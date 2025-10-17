from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QIcon, QFont


class FloatingAutoCompleteWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_editor = None
        self.enabled = True  # Novo: controle de estado
        
    def setup_ui(self):
        """Configura a interface do widget"""
        # Configurações de janela
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setMaximumHeight(200)
        self.setMaximumWidth(400)
        self.setFocusPolicy(Qt.NoFocus)
        
        # Estilo moderno similar ao VS Code
        self.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                font-family: 'Segoe UI', 'Consolas', monospace;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #2d2d30;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: white;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)
        
        # Conectar sinais
        self.itemDoubleClicked.connect(self.insert_completion)
            
    def show_completions(self, editor, suggestions, position=None):
        """Mostra sugestões na posição do cursor - VERSÃO CORRIGIDA"""
        if not self.enabled or not suggestions:
            self.hide()
            return
                
        self.current_editor = editor
        self.clear()
        
        # Limita a 25 sugestões
        suggestions = suggestions[:1000]
        
        # Adiciona sugestões
        for suggestion in suggestions:
            item = QListWidgetItem(suggestion)
            
            # Destaque visual baseado no tipo de sugestão
            if suggestion.endswith('()'):
                item.setForeground(QColor("#DCDCAA"))  # Amarelo para funções
            elif suggestion[0].isupper():
                item.setForeground(QColor("#4EC9B0"))  # Ciano para classes
            elif suggestion in ['import', 'from', 'def', 'class', 'if', 'for', 'while']:
                item.setForeground(QColor("#569CD6"))  # Azul para palavras-chave
            
            self.addItem(item)
        
        # Ajusta tamanho dinamicamente
        self.adjust_size(len(suggestions))
        
        # Posiciona o widget
        self.position_completion_widget(editor, position)
        
        # Mostra e seleciona primeiro item
        self.show()
        self.setCurrentRow(0)
        self.setFocus()

        
    def adjust_size(self, item_count):
            """Ajusta o tamanho do widget baseado no número de itens"""
            item_height = self.sizeHintForRow(0)
            visible_items = min(item_count, 15)  # Mostra até 15 itens visíveis
            
            height = item_height * visible_items + 4
            width = 500  # Largura aumentada para acomodar mais texto
            
            self.setFixedHeight(height)
            self.setFixedWidth(width)
        
    def position_completion_widget(self, editor, position=None):
        """Posiciona o widget próximo ao cursor - MÉTODO CORRIGIDO (nome alterado)"""
        if position:
            # Usa posição fornecida
            global_pos = editor.mapToGlobal(position)
        else:
            # Usa posição do cursor
            cursor_rect = editor.cursorRect()
            global_pos = editor.mapToGlobal(cursor_rect.bottomLeft())
        
        # Ajusta para não sair da tela
        screen = QApplication.primaryScreen().availableGeometry()
        
        # Verifica borda inferior
        if global_pos.y() + self.height() > screen.bottom():
            global_pos = editor.mapToGlobal(cursor_rect.topLeft())
            global_pos.setY(global_pos.y() - self.height())
            
        # Verifica borda direita
        if global_pos.x() + self.width() > screen.right():
            global_pos.setX(screen.right() - self.width())
            
        # Verifica borda esquerda
        if global_pos.x() < screen.left():
            global_pos.setX(screen.left())
            
        self.move(global_pos)

    def keyPressEvent(self, event):
        """Manipula teclas para navegação e inserção"""
        key = event.key()
        
        if key == Qt.Key_Escape:
            # Escape - fecha e desativa temporariamente
            self.hide()
            self.enabled = False
            event.accept()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            # Enter - insere completion
            self.insert_completion()
            event.accept()
        elif key == Qt.Key_Tab:
            # Tab - insere completion
            self.insert_completion()
            event.accept()
        elif key == Qt.Key_Up:
            # Seta para cima - navega
            if self.currentRow() == 0:
                self.setCurrentRow(self.count() - 1)
            else:
                self.setCurrentRow(self.currentRow() - 1)
            event.accept()
        elif key == Qt.Key_Down:
            # Seta para baixo - navega
            if self.currentRow() == self.count() - 1:
                self.setCurrentRow(0)
            else:
                self.setCurrentRow(self.currentRow() + 1)
            event.accept()
        else:
            # Outras teclas - repassa para o editor
            if self.current_editor:
                self.current_editor.keyPressEvent(event)
            self.hide()

            
    def insert_completion(self, item=None):
        """Insere a sugestão selecionada no editor"""
        if not self.current_editor:
            return
            
        if item is None:
            item = self.currentItem()
            
        if item:
            completion = item.text()
            cursor = self.current_editor.textCursor()
            
            # Remove a parte já digitada (se houver)
            current_line = cursor.block().text()
            cursor.select(QTextCursor.WordUnderCursor)
            current_word = cursor.selectedText()
            
            # Remove parênteses se já existirem em funções
            if completion.endswith('()') and current_word:
                # Se já tem parênteses, remove da completion
                if current_word + '()' == completion:
                    completion = current_word
                # Se está no meio do nome da função, insere só o nome
                elif current_word in completion:
                    completion = completion.replace('()', '')
            
            # Insere o texto
            if current_word:
                # Substitui a palavra atual
                cursor.insertText(completion)
            else:
                # Insere normalmente
                cursor.insertText(completion)
                
            # Foca no editor novamente
            self.current_editor.setFocus()
            
        self.hide()
            
    def get_icon(self, icon_type):
        """Retorna ícone baseado no tipo"""
        # Implementação simples sem ícones por enquanto
        return QIcon()
        
    def hideEvent(self, event):
        """Limpa referências quando escondido"""
        self.current_editor = None
        super().hideEvent(event)

    def set_enabled(self, enabled):
        """Ativa/desativa o autocomplete"""
        self.enabled = enabled
        if not enabled:
            self.hide()
    
    def toggle_enabled(self):
        """Alterna o estado do autocomplete"""
        self.enabled = not self.enabled
        if not self.enabled:
            self.hide()
        return self.enabled



class AutoCompleteWorker(QThread):
    def __init__(self, ide_instance):
        super().__init__()
        self.ide = ide_instance
        self._is_running = True
        self._mutex = threading.Lock()

    def stop(self):
        """Para o worker de forma segura"""
        with self._mutex:
             self._is_running = False
             self.quit()
             self.wait(2000)

    def run(self):
        """Loop principal do worker de autocomplete"""
        while self._is_running:
            try:
                # Aguarda por trabalho
                self.msleep(100)
                
                # Verifica se há editor atual
                editor = self.ide.get_current_editor()
                if not editor or not hasattr(editor, 'file_path'):
                    continue
                    
                # Obtém sugestões
                suggestions = self.get_suggestions_for_editor(editor)
                if suggestions:
                    self.suggestion_ready.emit(editor.file_path, suggestions)
                    
            except Exception as e:
                print(f"Erro no worker de autocomplete: {e}")

    # No método get_suggestions_for_editor do AutoCompleteWorker:
    def get_suggestions_for_editor(self, editor):
        """Obtém sugestões para o editor atual - AUMENTADO"""
        try:
            if not hasattr(self.ide, 'completer'):
                return []
                
            code = editor.toPlainText()
            cursor = editor.textCursor()
            cursor_position = cursor.position()
            
            suggestions = self.ide.completer.get_completions(
                code, 
                cursor_position,
                editor.file_path,
                self.ide.project_path if hasattr(self.ide, 'project_path') else ""
            )
            
            # AUMENTADO: Limita a 25 sugestões em vez de 15
            return suggestions[:100000]
            
        except Exception as e:
            print(f"Erro ao obter sugestões: {e}")
            return []


class HybridCompleter:
    """Completador híbrido focado em imports e arquivos - VERSÃO MELHORADA"""
    
    def __init__(self):
        self.import_completer = SmartImportCompleter()
        self._jedi_enabled = False
        
    def get_completions(self, text, cursor_position, file_path="", project_path=""):
        """Obtém sugestões focadas em imports e arquivos do projeto - VERSÃO MELHORADA"""
        try:
            # Usa apenas o analisador de imports
            suggestions = self.import_completer.get_import_completions(
                text, cursor_position, file_path, project_path
            )
            
            # Adiciona sugestões básicas se poucas sugestões
            if len(suggestions) < 50:  # AUMENTADO o limite
                basic = self._get_basic_suggestions(text)
                suggestions.extend([s for s in basic if s not in suggestions])
            
            # AUMENTADO: Retorna até 50 sugestões
            return suggestions[:50]
            
        except Exception as e:
            print(f"❌ Erro no completador: {e}")
            return self._get_fallback_suggestions()
    
    def _get_basic_suggestions(self, text):
        """Sugestões básicas de fallback - VERSÃO EXPANDIDA"""
        suggestions = [
            # Palavras-chave Python expandidas
            "print", "def", "class", "if", "else", "elif", "for", "while", "return", 
            "import", "from", "as", "try", "except", "finally", "with", 
            "lambda", "yield", "async", "await", "global", "nonlocal",
            "True", "False", "None", "and", "or", "not", "is", "in",
            "len", "str", "int", "float", "list", "dict", "set", "tuple",
            "range", "type", "isinstance", "issubclass", "hasattr", "getattr",
            "setattr", "delattr", "property", "staticmethod", "classmethod",
            "super", "self", "cls", "__init__", "__str__", "__repr__",
            "__name__", "__main__", "__file__", "__doc__", "__module__",
            
            # Funções comuns adicionais
            "sum", "max", "min", "abs", "round", "sorted", "reversed",
            "enumerate", "zip", "map", "filter", "any", "all", "dir",
            "vars", "locals", "globals", "help", "id", "hash", "callable",
            "issubclass", "iter", "next", "open", "input", "exit", "quit",
            
            # Módulos comuns
            "os", "sys", "json", "re", "datetime", "time", "math", "random",
            "subprocess", "shutil", "pathlib", "collections", "itertools",
            "functools", "typing", "logging", "argparse", "csv", "json"
        ]
        
        # Adiciona funções locais do texto atual
        if text:
            functions = re.findall(r'def\s+(\w+)', text)
            suggestions.extend([f"{f}()" for f in functions])
            
            classes = re.findall(r'class\s+(\w+)', text)
            suggestions.extend(classes)
            
            # Variáveis (nomes com mais de 2 caracteres)
            variables = re.findall(r'(\b[a-zA-Z_][a-zA-Z0-9_]{2,})\b\s*=', text)
            suggestions.extend(variables)
            
        return suggestions
    def _get_fallback_suggestions(self):
        """Sugestões de fallback mínimas e seguras"""
        return [
            "print", "def", "class", "if", "else", "for", "while", "import", 
            "from", "return", "True", "False", "None", "len", "str", "list", 
            "dict", "range", "type", "isinstance"
        ]

class UnifiedSuggestionSystem:
    """Sistema unificado e hierárquico de sugestões"""
    
    def __init__(self, editor=None):  # ✅ CORREÇÃO: Tornar editor opcional
        self.editor = editor
        self.cache = {}
        self.usage_stats = {} 
        
    def get_suggestions(self, code, cursor_position, file_path="", project_path=""):
        """Método principal unificado para obter todas as sugestões"""
        try:
            # Análise do contexto atual
            context = self._analyze_context(code, cursor_position, file_path)
            
            # Obtém sugestões hierárquicas
            suggestions = self._get_hierarchical_suggestions(context)
            
            # Aplica filtros e priorização
            filtered_suggestions = self._filter_and_prioritize(suggestions, context)
            
            return filtered_suggestions[:25]  # Limita a 25 sugestões
            show_autocomplete
        except Exception as e:
            print(f"❌ Erro no sistema unificado: {e}")
            return self._get_fallback_suggestions()
    
    def _analyze_context(self, code, cursor_position, file_path):
        """Analisa completamente o contexto do código"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        current_line = lines[current_line_index] if current_line_index < len(lines) else ""
        
        return {
            # Informações básicas
            'current_line': current_line.strip(),
            'current_word': self._get_current_word(code, cursor_position),
            'current_indent': len(current_line) - len(current_line.lstrip()),
            'file_extension': os.path.splitext(file_path or '')[1].lower(),
            
            # Contexto estrutural
            'inside_function': self._is_inside_function(code, cursor_position),
            'inside_class': self._is_inside_class(code, cursor_position),
            'function_name': self._get_current_function(code, cursor_position),
            'class_name': self._get_current_class(code, cursor_position),
            
            # Contexto sintático
            'after_import': any(keyword in current_line for keyword in ['import', 'from']),
            'after_dot': current_line.rstrip().endswith('.'),
            'after_def': 'def ' in current_line,
            'after_class': 'class ' in current_line,
            
            # Projeto
            'project_path': project_path,
            'file_path': file_path
        }
    
    def _get_hierarchical_suggestions(self, context):
        """Obtém sugestões hierárquicas baseadas no contexto"""
        suggestions = set()
        
        # Nível 1: Palavras-chave da linguagem
        suggestions.update(self._get_language_keywords(context))
        
        # Nível 2: Funções built-in
        suggestions.update(self._get_builtin_functions(context))
        
        # Nível 3: Definições locais do arquivo
        suggestions.update(self._get_local_definitions(context))
        
        # Nível 4: Sugestões contextuais
        suggestions.update(self._get_contextual_suggestions(context))
        
        # Nível 5: Módulos e imports
        suggestions.update(self._get_module_suggestions(context))
        
        # Nível 6: Completamento de código
        suggestions.update(self._get_code_completion_suggestions(context))
        
        return suggestions
    
    def _get_language_keywords(self, context):
        """Palavras-chave específicas da linguagem"""
        language = self._get_language_from_extension(context['file_extension'])
        
        keywords_map = {
            'python': [
                # Controle de fluxo
                "if", "else", "elif", "for", "while", "break", "continue",
                "return", "yield", "pass", "raise", "try", "except", "finally",
                
                # Definições
                "def", "class", "lambda",
                
                # Escopo
                "global", "nonlocal", "with", "as",
                
                # Importação
                "import", "from",
                
                # Operadores lógicos
                "and", "or", "not", "is", "in",
                
                # Valores especiais
                "True", "False", "None",
                
                # Assincronia
                "async", "await"
            ],
            'javascript': [
                "function", "var", "let", "const", "if", "else", "for", "while",
                "return", "class", "import", "export", "try", "catch", "finally"
            ],
            'html': ["div", "span", "p", "h1", "button", "input", "form", "table"],
            'css': [".class", "#id", "color", "font-size", "margin", "padding"]
        }
        
        return keywords_map.get(language, [])
    
    def _get_builtin_functions(self, context):
        """Funções built-in da linguagem"""
        language = self._get_language_from_extension(context['file_extension'])
        
        if language == 'python':
            return [
                # E/S e sistema
                "print()", "input()", "open()", "len()", "type()", "isinstance()",
                
                # Conversão de tipos
                "str()", "int()", "float()", "list()", "dict()", "set()", "tuple()",
                
                # Matemática
                "abs()", "sum()", "min()", "max()", "round()", "range()",
                
                # Iteração
                "enumerate()", "zip()", "map()", "filter()", "sorted()", "reversed()",
                
                # Objetos e atributos
                "getattr()", "setattr()", "hasattr()", "dir()", "vars()",
                
                # Arquivos e sistema
                "os.path.join()", "os.listdir()", "json.loads()", "json.dumps()"
            ]
        
        return []
    
    def _get_local_definitions(self, context):
        """Definições locais do arquivo atual"""
        definitions = set()
        
        if not context.get('file_path') or not os.path.exists(context['file_path']):
            return definitions
        
        try:
            with open(context['file_path'], 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Funções
            functions = re.findall(r'def\s+(\w+)', code)
            definitions.update([f"{f}()" for f in functions])
            
            # Classes
            classes = re.findall(r'class\s+(\w+)', code)
            definitions.update(classes)
            
            # Variáveis (nomes significativos)
            variables = re.findall(r'(\b[a-zA-Z_][a-zA-Z0-9_]{2,})\b\s*=', code)
            definitions.update(variables)
            
        except Exception as e:
            print(f"Erro ao extrair definições locais: {e}")
        
        return definitions
    
    def _get_contextual_suggestions(self, context):
        """Sugestões baseadas no contexto específico"""
        suggestions = set()
        current_line = context['current_line']
        
        # Após import/from
        if context['after_import']:
            suggestions.update(self._get_import_suggestions(context))
        
        # Após ponto (métodos/atributos)
        if context['after_dot']:
            suggestions.update(self._get_dot_suggestions(context))
        
        # Padrões específicos de linha
        patterns = {
            r'if\s*.*:': ['elif', 'else:'],
            r'for\s+.*\s+in\s+': ['range(', 'enumerate(', 'zip('],
            r'def\s+\w+\(\):': ['pass', 'return'],
            r'class\s+\w+': ['def __init__(self):', 'pass'],
            r'print\(': ['f"', 'end=" "', 'sep=" "'],
            r'return\s+': ['True', 'False', 'None']
        }
        
        for pattern, pattern_suggestions in patterns.items():
            if re.search(pattern, current_line):
                suggestions.update(pattern_suggestions)
        
        # Contexto de função/classe
        if context['inside_function']:
            suggestions.update(['return', 'yield', 'pass'])
        if context['inside_class']:
            suggestions.update(['self.', '__init__', '__str__'])
        
        return suggestions
    
    def _get_import_suggestions(self, context):
        """Sugestões para imports"""
        suggestions = set()
        
        # Módulos padrão Python
        stdlib_modules = [
            'os', 'sys', 'json', 're', 'datetime', 'math', 'random',
            'subprocess', 'shutil', 'glob', 'ast', 'inspect', 'importlib',
            'platform', 'time', 'pathlib', 'collections', 'itertools', 'functools',
            'typing', 'logging', 'unittest', 'threading', 'multiprocessing'
        ]
        suggestions.update(stdlib_modules)
        
        # Módulos do projeto
        if context.get('project_path'):
            project_modules = self._get_project_modules(context['project_path'])
            suggestions.update(project_modules)
        
        return suggestions
    
    def _get_dot_suggestions(self, context):
        """Sugestões após ponto (métodos/atributos)"""
        suggestions = set()
        
        # Métodos comuns de tipos básicos
        string_methods = ['.strip()', '.split()', '.join()', '.replace()', '.format()']
        list_methods = ['.append()', '.extend()', '.insert()', '.remove()', '.pop()']
        dict_methods = ['.keys()', '.values()', '.items()', '.get()', '.update()']
        
        suggestions.update(string_methods + list_methods + dict_methods)
        
        return suggestions
    
    def _get_module_suggestions(self, context):
        """Sugestões de módulos do projeto"""
        modules = set()
        
        if not context.get('project_path') or not os.path.exists(context['project_path']):
            return modules
            
        try:
            for root, dirs, files in os.walk(context['project_path']):
                # Ignora diretórios comuns
                ignore_dirs = {'__pycache__', '.git', 'venv', '.venv', 'node_modules'}
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        rel_path = os.path.relpath(os.path.join(root, file), context['project_path'])
                        module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                        
                        if module_name.endswith('.__init__'):
                            module_name = module_name[:-9]
                            
                        modules.add(module_name)
                        
        except Exception as e:
            print(f"Erro ao buscar módulos: {e}")
            
        return modules
    
    def _get_code_completion_suggestions(self, context):
        """Sugestões para completar estruturas de código"""
        suggestions = set()
        
        code_snippets = {
            'ifmain': 'if __name__ == "__main__": main()',
            'fori': 'for i in range():',
            'foritem': 'for item in :',
            'while': 'while :',
            'try': 'try:\n    \nexcept:',
            'class': 'class :',
            'function': 'def ():',
            'main': 'def main():\n    \n\nif __name__ == "__main__":\n    main()'
        }
        
        for key, snippet in code_snippets.items():
            suggestions.add(f"#{key}: {snippet}")
        
        return suggestions
    
    def _filter_and_prioritize(self, suggestions, context):
        """Filtra e prioriza sugestões baseadas no contexto"""
        current_word = context['current_word']
        all_suggestions = list(suggestions)
        
        if not current_word:
            # Sem filtro - retorna sugestões prioritárias primeiro
            return self._apply_priority_sorting(all_suggestions)
        
        # Com filtro - aplica matching inteligente
        exact_matches = [s for s in all_suggestions if s.lower().startswith(current_word.lower())]
        contains_matches = [s for s in all_suggestions if current_word.lower() in s.lower() and s not in exact_matches]
        
        # Combina e ordena
        result = exact_matches + contains_matches
        return self._apply_priority_sorting(result)
    
    def _apply_priority_sorting(self, suggestions):
        """Aplica ordenação por prioridade"""
        def priority_key(suggestion):
            if suggestion.endswith('()'):
                return 0  # Funções primeiro
            elif suggestion[0].isupper():
                return 1  # Classes
            elif suggestion.startswith('self.'):
                return 2  # Atributos/métodos
            elif suggestion in ['if', 'for', 'while', 'def', 'class']:
                return 3  # Palavras-chave estruturais
            else:
                return 4  # Outros
        
        return sorted(suggestions, key=priority_key)
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _get_language_from_extension(self, extension):
        """Determina linguagem baseada na extensão do arquivo"""
        language_map = {
            '.py': 'python', '.js': 'javascript', '.html': 'html', '.css': 'css',
            '.json': 'json', '.xml': 'html', '.txt': 'text', '.md': 'markdown',
            '.yml': 'yaml', '.yaml': 'yaml', '.sql': 'sql', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby'
        }
        return language_map.get(extension, 'text')
    
    def _get_current_word(self, code, cursor_position):
        """Extrai a palavra atual sendo digitada"""
        text_before = code[:cursor_position]
        word_chars = []
        
        for char in reversed(text_before):
            if char.isalnum() or char in ['_', '.']:
                word_chars.append(char)
            else:
                break
        
        return ''.join(reversed(word_chars)) if word_chars else ""
    
    def _is_inside_function(self, code, cursor_position):
        """Verifica se está dentro de uma função"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        current_indent = len(lines[current_line_index]) - len(lines[current_line_index].lstrip())
        
        for i in range(current_line_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                def_indent = len(lines[i]) - len(lines[i].lstrip())
                return current_indent > def_indent
            elif line and not line.startswith('#'):
                line_indent = len(lines[i]) - len(lines[i].lstrip())
                if line_indent < current_indent:
                    break
        
        return False
    
    def _is_inside_class(self, code, cursor_position):
        """Verifica se está dentro de uma classe"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        
        for i in range(current_line_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                return True
            elif line and not line.startswith('#') and not line.startswith('def '):
                break
        
        return False
    
    def _get_current_function(self, code, cursor_position):
        """Obtém o nome da função atual"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        
        for i in range(current_line_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                match = re.match(r'def\s+(\w+)', line)
                return match.group(1) if match else "Nenhuma"
        
        return "Nenhuma"
    
    def _get_current_class(self, code, cursor_position):
        """Obtém o nome da classe atual"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        
        for i in range(current_line_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                match = re.match(r'class\s+(\w+)', line)
                return match.group(1) if match else "Global"
        
        return "Global"
    
    def _get_fallback_suggestions(self):
        """Sugestões de fallback mínimas e seguras"""
        return [
            "print", "def", "class", "if", "else", "for", "while", "import", 
            "from", "return", "True", "False", "None", "len", "str", "list", 
            "dict", "range", "type", "isinstance"
        ]

        get_unified_suggestions