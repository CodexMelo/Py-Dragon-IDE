# Novo arquivo
from PySide6.QtWidgets import (QPlainTextEdit, QWidget, QVBoxLayout, QMenu, 
                              QMessageBox, QFileDialog, QListWidget, QListWidgetItem, 
                              QTextEdit, QHBoxLayout, QLabel, QFrame, QApplication)
from PySide6.QtCore import Qt, QTimer, QRect, QRegularExpression, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import (QFont, QTextCursor, QSyntaxHighlighter, QTextCharFormat, 
                          QColor, QPainter, QPalette, QTextFormat, QPen, QLinearGradient)
from PySide6.QtGui import QTextDocument 
import os
import re
import importlib
import importlib.metadata
from collections import defaultdict

# Importar os componentes organizados
from editor.line_numbers import LineNumberArea
from editor.code_folding import CodeFoldingArea
from syntax.highlighters import HighlighterFactory
from syntax.syntax_manager import SyntaxHighlightingManager
from editor.CompletPronto import completer, quick_template, quick_snippet, get_available_templates, get_available_snippets

# ===== SISTEMA DE SUGESTÕES INTELIGENTE CORRIGIDO =====
class SmartSuggestionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            SmartSuggestionWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d30, stop:0.1 #252526, stop:1 #1e1e1e);
                border: 1px solid #464647;
                border-radius: 6px;
                padding: 2px;
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                font-family: 'Segoe UI', system-ui;
                font-size: 12px;
                color: #cccccc;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 3px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3c3c3c, stop:1 #2a2a2a);
                border: 1px solid #565656;
            }
            QListWidget::item:hover:!selected {
                background: #2a2d2e;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header compacto
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background: #323233;
                border-bottom: 1px solid #464647;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 4px 8px;
            }
            QLabel {
                color: #969696;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(4, 2, 4, 2)
        self.suggestion_count_label = QLabel("0 sugestões")
        self.header_layout.addWidget(self.suggestion_count_label)
        self.header_layout.addStretch()
        
        self.layout.addWidget(self.header_frame)
        
        # Lista de sugestões
        self.list_widget = QListWidget()
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.list_widget.setMinimumHeight(150)
        self.list_widget.setMaximumHeight(400)
        
        # Configurar ícones e cores para diferentes tipos
        self.type_colors = {
            'function': '#4EC9B0',
            'class': '#4EC9B0', 
            'method': '#DCDCAA',
            'property': '#9CDCFE',
            'variable': '#9CDCFE',
            'keyword': '#C586C0',
            'module': '#CE9178',
            'builtin': '#D7BA7D',
            'file': '#CE9178',
            'folder': '#569CD6',
            'image': '#C586C0',
            'template': '#4EC9B0',
            'snippet': '#D7BA7D'
        }
        
        self.layout.addWidget(self.list_widget)
        
        # Footer compacto
        self.footer_frame = QFrame()
        self.footer_frame.setStyleSheet("""
            QFrame {
                background: #252526;
                border-top: 1px solid #464647;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                padding: 3px 8px;
            }
            QLabel {
                color: #6A9955;
                font-size: 9px;
                font-style: italic;
            }
        """)
        self.footer_layout = QHBoxLayout(self.footer_frame)
        self.footer_layout.setContentsMargins(4, 1, 4, 1)
        self.hint_label = QLabel("↑↓ • Enter • Tab • Esc")
        self.footer_layout.addWidget(self.hint_label)
        
        self.layout.addWidget(self.footer_frame)
        
        self.enabled = True
        
    def show_completions(self, editor, suggestions, position):
        """Mostra sugestões com categorização"""
        if not suggestions or not self.enabled:
            self.hide()
            return
            
        self.list_widget.clear()
        
        # Categorizar sugestões
        categorized = self._categorize_suggestions(suggestions)
        
        # Adicionar por categoria
        for category, items in categorized.items():
            if items:
                # Header da categoria
                category_item = QListWidgetItem(f"▸ {category.upper()}")
                category_item.setFlags(Qt.NoItemFlags)
                category_item.setBackground(QColor(45, 45, 48))
                category_item.setForeground(QColor(150, 150, 150))
                row_height = self.list_widget.sizeHintForRow(0)
                category_item.setSizeHint(QSize(100, row_height))
                self.list_widget.addItem(category_item)
                
                # Itens da categoria
                for item_text, item_type in items:
                    list_item = QListWidgetItem(self._format_suggestion(item_text, item_type))
                    list_item.setData(Qt.UserRole, item_text)
                    list_item.setForeground(QColor(self.type_colors.get(item_type, '#CCCCCC')))
                    self.list_widget.addItem(list_item)
        
        # Atualizar contador
        total_items = sum(len(items) for items in categorized.values())
        self.suggestion_count_label.setText(f"{total_items} sugestões")
        
        # Posicionar e mostrar
        self.move(editor.mapToGlobal(position))
        self.adjustSize()
        
        # Limitar altura máxima
        max_height = min(editor.height() - 100, 600)
        if self.height() > max_height:
            self.setFixedHeight(max_height)
            
        self.show()
        self.list_widget.setFocus()
        
        # Selecionar primeiro item válido (pular headers)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() != Qt.NoItemFlags:
                self.list_widget.setCurrentRow(i)
                break

    def _categorize_suggestions(self, suggestions):
        """Categoriza sugestões por tipo - INCLUI TEMPLATES"""
        categories = {
            'templates': [],
            'snippets': [],
            'arquivos': [],
            'pastas': [],
            'funções': [],
            'classes': [],
            'métodos': [],
            'variáveis': [],
            'palavras-chave': [],
            'módulos': [],
            'built-ins': []
        }
        
        for suggestion in suggestions:
            # Detectar templates e snippets primeiro
            if suggestion.startswith('template:'):
                template_name = suggestion.replace('template:', '')
                categories['templates'].append((suggestion, 'template'))
                continue
            elif suggestion.startswith('snippet:'):
                snippet_name = suggestion.replace('snippet:', '')
                categories['snippets'].append((suggestion, 'snippet'))
                continue
                
            # Detectar se é arquivo (tem extensão e não é função/método)
            if '.' in suggestion and not suggestion.endswith('()'):
                ext = suggestion.split('.')[-1].lower()
                # Lista de extensões de arquivo comuns
                file_extensions = ['py', 'js', 'html', 'css', 'json', 'txt', 'md', 'xml', 
                                 'yml', 'yaml', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 
                                 'ico', 'pdf', 'doc', 'docx', 'csv', 'sql', 'java', 'cpp', 
                                 'c', 'h', 'php', 'rb', 'go', 'rs', 'swift', 'kt', 'ts']
                
                if ext in file_extensions:
                    # Verificar se não é um módulo Python (arquivo .py sem path)
                    if ext == 'py' and '/' not in suggestion and '\\' not in suggestion:
                        categories['módulos'].append((suggestion, 'module'))
                    else:
                        # Detectar tipo específico do arquivo
                        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'ico']:
                            categories['arquivos'].append((suggestion, 'image'))
                        else:
                            categories['arquivos'].append((suggestion, 'file'))
                    continue
            
            # Detectar se é pasta (não tem extensão, não termina com parênteses, não tem caracteres especiais de código)
            if (not '.' in suggestion and 
                not suggestion.endswith('()') and 
                not any(char in suggestion for char in '()[]{}:') and
                not ' ' in suggestion and
                not suggestion.lower() in ['def', 'class', 'if', 'else', 'for', 'while', 'import', 'from']):
                categories['pastas'].append((suggestion, 'folder'))
                continue
                
            clean_suggestion = suggestion.replace('()', '')
            
            # Detectar funções e métodos
            if suggestion.endswith('()'):
                if '.' in clean_suggestion:
                    # Método: classe.metodo()
                    categories['métodos'].append((suggestion, 'method'))
                else:
                    # Função: funcao()
                    categories['funções'].append((suggestion, 'function'))
            
            # Detectar classes (começam com letra maiúscula e não são pastas/arquivos)
            elif suggestion and suggestion[0].isupper() and not '.' in suggestion:
                categories['classes'].append((suggestion, 'class'))
            
            # Detectar palavras-chave
            elif any(keyword in suggestion.lower() for keyword in 
                    ['import ', 'from ', 'def ', 'class ', 'if ', 'else ', 'for ', 'while ', 
                     'return ', 'try:', 'except ', 'finally ', 'with ', 'as ', 'lambda ']):
                categories['palavras-chave'].append((suggestion, 'keyword'))
            
            # Detectar módulos (contém ponto mas não é arquivo)
            elif '.' in suggestion and not any(ext in suggestion for ext in file_extensions):
                categories['módulos'].append((suggestion, 'module'))
            
            # Detectar built-ins
            elif any(builtin == suggestion.lower() for builtin in 
                    ['print', 'len', 'str', 'list', 'dict', 'range', 'type', 'input', 
                     'open', 'sum', 'max', 'min', 'abs', 'all', 'any']):
                categories['built-ins'].append((suggestion, 'builtin'))
            
            # Variáveis (padrão snake_case ou camelCase)
            elif (re.match(r'^[a-z_][a-z0-9_]*$', suggestion) or 
                  re.match(r'^[a-z][a-z0-9]*([A-Z][a-z0-9]*)*$', suggestion)):
                categories['variáveis'].append((suggestion, 'variable'))
            
            # Fallback - adicionar como variável
            else:
                categories['variáveis'].append((suggestion, 'variable'))
                    
        # Remover categorias vazias
        return {k: v for k, v in categories.items() if v}
    
    def _format_suggestion(self, text, item_type):
        """Formata o texto da sugestão baseado no tipo - INCLUI TEMPLATES"""
        icons = {
            'function': 'ƒ',
            'class': 'Ⓒ', 
            'method': 'Ⓜ',
            'property': 'Ⓟ',
            'variable': 'Ⓥ',
            'keyword': 'Ⓚ',
            'module': 'Ⓛ',
            'builtin': 'Ⓑ',
            'file': '📄',
            'folder': '📁',
            'image': '🖼️',
            'template': '📋',
            'snippet': '⚡'
        }
        
        # Detectar se é template ou snippet
        if text.startswith('template:'):
            icon = icons.get('template', '📋')
            clean_text = text.replace('template:', '')
            return f"{icon} {clean_text} (template)"
        elif text.startswith('snippet:'):
            icon = icons.get('snippet', '⚡')
            clean_text = text.replace('snippet:', '')
            return f"{icon} {clean_text} (snippet)"
        else:
            icon = icons.get(item_type, '•')
            return f"{icon}  {text}"
    
    def get_selected_text(self):
        """Retorna o texto selecionado"""
        if self.list_widget.currentItem():
            return self.list_widget.currentItem().data(Qt.UserRole)
        return None
    
    def keyPressEvent(self, event):
        """Manipulação de teclas personalizada - VERSÃO CORRIGIDA"""
        key = event.key()
        text = event.text()
        
        # Apenas processar teclas de navegação e aceitação
        if key == Qt.Key_Escape:
            self.hide()
            event.accept()
        elif key in [Qt.Key_Return, Qt.Key_Enter]:
            self.accept()
            event.accept()
        elif key == Qt.Key_Tab:
            self.accept()
            event.accept()
        elif key == Qt.Key_Up:
            current = self.list_widget.currentRow()
            # Pular headers de categoria
            while current > 0:
                current -= 1
                if not self.list_widget.item(current).flags() == Qt.NoItemFlags:
                    self.list_widget.setCurrentRow(current)
                    break
            event.accept()
        elif key == Qt.Key_Down:
            current = self.list_widget.currentRow()
            # Pular headers de categoria
            while current < self.list_widget.count() - 1:
                current += 1
                if not self.list_widget.item(current).flags() == Qt.NoItemFlags:
                    self.list_widget.setCurrentRow(current)
                    break
            event.accept()
        else:
            # Para qualquer outra tecla, apenas fechar e permitir que o editor processe
            self.hide()
            event.ignore()  # Importante: não aceitar o evento para permitir que o editor o processe

    def accept(self):
        """Aceita a sugestão selecionada"""
        selected_text = self.get_selected_text()
        if selected_text and self.parent():
            self.parent().insert_completion(selected_text)
        self.hide()

# CLASSES AUXILIARES
class ScopeHeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_class = "Global"
        self.current_function = "Nenhuma"
        
    def update_scope(self, current_class, current_function):
        self.current_class = current_class
        self.current_function = current_function
        
    def show_scope(self):
        self.show()
        
    def hide_scope(self):
        self.hide()

class ScopeIndicatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class LinterWorker:
    def __init__(self, file_path, python_executable, project_path):
        self.file_path = file_path
        self.python_executable = python_executable
        self.project_path = project_path
        self._is_running = False
        
    def isRunning(self):
        return self._is_running
        
    def stop(self):
        self._is_running = False
        
    def start(self):
        self._is_running = True
        
    def finished(self):
        return None

# ===== EDITOR PRINCIPAL COM SISTEMA CORRIGIDO =====
class UnifiedCodeEditor(QPlainTextEdit):
    
    def __init__(self, text="", cursor_position=0, file_path="", project_path="", parent=None):
        super().__init__(parent)
        
        self.file_path = file_path
        self.project_path = project_path
        self.is_modified = False
        self.current_theme = "Dark Professional"
        
        # Configuração básica
        self.setPlainText(text)
        cursor = self.textCursor()
        cursor.setPosition(min(cursor_position, len(text)))
        self.setTextCursor(cursor)       
        
        # ===== CONFIGURAÇÕES BÁSICAS =====
        self.setup_basic_settings()
        
        # ===== SISTEMA DE NÚMEROS DE LINHA =====
        self.setup_line_numbers()
        
        # ===== SISTEMA DE FOLDING =====
        self.setup_code_folding()
        
        # ===== SISTEMA DE AUTOCOMPLETE INTELIGENTE =====
        self.setup_smart_autocomplete_system()
        
        # ===== SYNTAX HIGHLIGHTING =====
        self.setup_syntax_highlighting()
        
        # ===== SISTEMA DE INDICADORES VISUAIS =====
        self.setup_visual_indicators()
        
        # ===== SISTEMA LSP =====
        self.lsp_manager = None
        self.lsp_completions = []
        
        # ===== CONEXÕES DE SINAIS =====
        self.setup_signal_connections()
        
        # ===== CONFIGURAÇÕES FINAIS =====
        self.setup_final_settings()
        
        print(f"✅ Editor Unificado criado para: {file_path}")
        
        # Cache para melhor performance
        self.project_cache = None
        self.pip_packages = self._get_pip_packages()
        self.last_suggestions_update = 0
        self._typing_with_autocomplete = False

    def _get_pip_packages(self):
        """Coleta todos os pacotes pip instalados no ambiente."""
        try:
            return {dist.metadata['Name'] for dist in importlib.metadata.distributions()}
        except Exception as e:
            print(f"❌ Erro ao coletar pacotes pip: {e}")
            return set()

    def _scan_project_files(self):
        """Escaneia TODOS os arquivos do projeto para coletar definições"""
        if not self.project_path or not os.path.exists(self.project_path):
            return defaultdict(set)

        cache = defaultdict(set)
        try:
            for root, dirs, files in os.walk(self.project_path):
                # Ignorar pastas desnecessárias
                ignore_dirs = ['__pycache__', '.git', 'venv', '.vscode', '.idea', 'node_modules', 'dist', 'build']
                for ignore_dir in ignore_dirs:
                    if ignore_dir in dirs:
                        dirs.remove(ignore_dir)
                
                # Adicionar pastas
                for dir_name in dirs:
                    if not dir_name.startswith('.'):
                        cache['folders'].add(dir_name)
                
                # Adicionar arquivos
                for file in files:
                    if file.startswith('.'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.project_path)
                    
                    # Adicionar nome do arquivo
                    cache['files'].add(file)
                    
                    # Adicionar caminho relativo
                    cache['files'].add(rel_path.replace('\\', '/'))
                    
                    # Se for arquivo Python, extrair definições
                    if file.endswith('.py'):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()

                            # Extrai imports
                            imports = re.findall(r'^\s*(?:from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)|import\s+([a-zA-Z_][a-zA-Z0-9_]*))\s*', content, re.MULTILINE)
                            for imp in imports:
                                imp_name = imp[0] or imp[1]
                                cache['imports'].add(imp_name.split('.')[0])

                            # Extrai funções
                            functions = re.findall(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content, re.MULTILINE)
                            cache['functions'].update(functions)

                            # Extrai classes
                            classes = re.findall(r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?::|\()', content, re.MULTILINE)
                            cache['classes'].update(classes)

                            # Extrai variáveis
                            variables = re.findall(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=]', content, re.MULTILINE)
                            cache['variables'].update(variables)

                        except Exception as e:
                            print(f"❌ Erro ao escanear {file_path}: {e}")
            
            return cache
        except Exception as e:
            print(f"❌ Erro ao escanear projeto: {e}")
            return defaultdict(set)

    def get_project_definitions(self):
        """Retorna definições do projeto, usando cache se disponível."""
        if self.project_cache is None:
            self.project_cache = self._scan_project_files()
        return self.project_cache

    def setup_smart_autocomplete_system(self):
        """Configura sistema de autocomplete inteligente"""
        self.autocomplete_timer = QTimer(self)
        self.autocomplete_timer.setSingleShot(True)
        self.autocomplete_timer.timeout.connect(self.show_smart_autocomplete)
        
        # Usar o novo widget inteligente
        self.autocomplete_widget = SmartSuggestionWidget(self)
        
        # Timer para sugestões em tempo real
        self.realtime_suggestions_timer = QTimer(self)
        self.realtime_suggestions_timer.setSingleShot(True)
        self.realtime_suggestions_timer.timeout.connect(self.update_realtime_suggestions)
        
        self.last_key_pressed = None
        self.force_show_autocomplete = False

    def show_smart_autocomplete(self):
        """Mostra sugestões inteligentes"""
        if not self.autocomplete_widget.enabled or self._typing_with_autocomplete:
            return
            
        try:
            suggestions = self.get_enhanced_suggestions()
            if suggestions:
                cursor_rect = self.cursorRect()
                # Posicionar acima do cursor se estiver perto da parte inferior
                if cursor_rect.bottom() + 200 > self.height():
                    position = cursor_rect.topLeft() 
                else:
                    position = cursor_rect.bottomLeft()
                    
                self.autocomplete_widget.show_completions(self, suggestions, position)
        except Exception as e:
            print(f"❌ Erro no autocomplete inteligente: {e}")

    def update_realtime_suggestions(self):
        """Atualiza sugestões em tempo real enquanto digita"""
        if self.autocomplete_widget.isVisible() and not self._typing_with_autocomplete:
            suggestions = self.get_enhanced_suggestions()
            if suggestions:
                current_pos = self.cursorRect().bottomLeft()
                self.autocomplete_widget.show_completions(self, suggestions, current_pos)

    def get_enhanced_suggestions(self):
        """Sugestões melhoradas com categorização inteligente - INCLUI TEMPLATES"""
        try:
            cursor = self.textCursor()
            position = cursor.position()
            text_before = self.toPlainText()[:position]
            
            # Detectar contexto atual
            context = self._detect_context(text_before)
            
            # Obter sugestões baseadas no contexto
            if context == 'import':
                return self._get_import_suggestions()
            elif context == 'string_path':
                return self._get_path_suggestions(text_before)
            elif context == 'attribute':
                return self._get_attribute_suggestions(text_before)
            elif context == 'function_call':
                return self._get_function_suggestions()
            else:
                return self._get_general_suggestions_with_templates(text_before)
                
        except Exception as e:
            print(f"❌ Erro nas sugestões melhoradas: {e}")
            return self._get_fallback_suggestions()

    def _detect_context(self, text_before):
        """Detecta o contexto atual do código"""
        lines = text_before.split('\n')
        current_line = lines[-1] if lines else ""
        
        if re.match(r'^\s*(from|import)\s+', current_line):
            return 'import'
        elif re.search(r'[\'\"][^\'\"]*$', current_line) and any(keyword in current_line for keyword in ['open', 'open(', 'read', 'write', 'path', 'file']):
            return 'string_path'
        elif re.search(r'\.\w*$', current_line):
            return 'attribute'
        elif re.search(r'\w+\(.*\)$', current_line):
            return 'function_call'
        else:
            return 'general'

    def _get_import_suggestions(self):
        """Sugestões específicas para imports"""
        suggestions = set()
        
        # Módulos padrão do Python
        std_modules = [
            'os', 'sys', 're', 'json', 'datetime', 'time', 'math', 'random',
            'collections', 'itertools', 'functools', 'threading', 'multiprocessing',
            'subprocess', 'pathlib', 'shutil', 'glob', 'argparse', 'logging',
            'asyncio', 'concurrent', 'hashlib', 'hmac', 'secrets', 'base64',
            'struct', 'pickle', 'copy', 'pprint', 'textwrap', 'unicodedata',
            'string', 'difflib', 'typing', 'abc', 'atexit', 'contextlib',
            'dataclasses', 'enum', 'inspect', 'operator', 'statistics', 'decimal',
            'fractions', 'numbers', 'cmath', 'array', 'bisect', 'heapq', 'queue',
            'weakref', 'types', 'collections.abc', 'io', 'tempfile', 'fileinput',
            'fnmatch', 'linecache', 'tokenize', 'keyword', 'ast', 'symtable',
            'traceback', 'gc', 'site', 'sysconfig', 'warnings', 'builtins',
            'codecs', 'locale', 'gettext', 'readline', 'rlcompleter'
        ]
        suggestions.update(std_modules)
        
        # Módulos do projeto
        suggestions.update(self.get_project_modules())
        
        # Pacotes pip instalados
        suggestions.update(self.pip_packages)
        
        return sorted(list(suggestions))

    def _get_path_suggestions(self, text_before):
        """Sugestões para caminhos de arquivos"""
        suggestions = set()
        
        # Extrair o caminho parcial da string
        match = re.search(r'[\'\"]([^\'\"]*)$', text_before)
        if not match:
            return []
            
        partial_path = match.group(1)
        
        # Obter todos os arquivos e pastas do projeto
        project_defs = self.get_project_definitions()
        suggestions.update(project_defs['files'])
        suggestions.update(project_defs['folders'])
        
        # Filtrar por caminho parcial
        if partial_path:
            filtered = [s for s in suggestions if s.lower().startswith(partial_path.lower())]
            return sorted(filtered)
        else:
            return sorted(list(suggestions))

    def _get_attribute_suggestions(self, text_before):
        """Sugestões para acesso a atributos/métodos"""
        match = re.search(r'(\w+(?:\.\w+)*)\.(\w*)$', text_before)
        if not match:
            return []
            
        module_path = match.group(1)
        prefix = match.group(2)
        
        try:
            # Tentar importar dinamicamente
            parts = module_path.split('.')
            import sys
            sys.path.insert(0, self.project_path)
            
            module = importlib.import_module(parts[0])
            for part in parts[1:]:
                module = getattr(module, part)
                
            # Coletar atributos
            attributes = []
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue
                    
                attr = getattr(module, attr_name)
                if callable(attr):
                    if isinstance(attr, type):
                        attributes.append(attr_name)
                    else:
                        attributes.append(f"{attr_name}()")
                else:
                    attributes.append(attr_name)
                    
            # Filtrar por prefixo
            if prefix:
                filtered = [attr for attr in attributes if attr.lower().startswith(prefix.lower())]
                return sorted(filtered)
            else:
                return sorted(attributes)
                
        except (ImportError, AttributeError):
            return []

    def _get_function_suggestions(self):
        """Sugestões para chamadas de função"""
        suggestions = set()
        
        # Funções locais
        local_funcs = self.extract_local_definitions()
        suggestions.update([f for f in local_funcs if '()' in f])
        
        # Funções built-in
        builtin_funcs = [
            'print()', 'len()', 'str()', 'int()', 'float()', 'list()', 'dict()',
            'set()', 'tuple()', 'range()', 'type()', 'isinstance()', 'enumerate()',
            'zip()', 'map()', 'filter()', 'sorted()', 'reversed()', 'sum()', 'max()', 'min()',
            'abs()', 'all()', 'any()', 'ascii()', 'bin()', 'bool()', 'breakpoint()', 'bytearray()',
            'bytes()', 'callable()', 'chr()', 'classmethod()', 'compile()', 'complex()',
            'delattr()', 'dict()', 'dir()', 'divmod()', 'enumerate()', 'eval()', 'exec()',
            'filter()', 'float()', 'format()', 'frozenset()', 'getattr()', 'globals()',
            'hasattr()', 'hash()', 'help()', 'hex()', 'id()', 'input()', 'int()', 'isinstance()',
            'issubclass()', 'iter()', 'len()', 'list()', 'locals()', 'map()', 'max()', 'memoryview()',
            'min()', 'next()', 'object()', 'oct()', 'open()', 'ord()', 'pow()', 'print()', 'property()',
            'range()', 'repr()', 'reversed()', 'round()', 'set()', 'setattr()', 'slice()', 'sorted()',
            'staticmethod()', 'str()', 'sum()', 'super()', 'tuple()', 'type()', 'vars()', 'zip()'
        ]
        suggestions.update(builtin_funcs)
        
        return sorted(list(suggestions))

    def _get_general_suggestions_with_templates(self, text_before):
        """Sugestões gerais incluindo templates"""
        all_suggestions = set()
        
        # Sugestões normais
        all_suggestions.update(self.get_language_keywords())
        all_suggestions.update(self.extract_local_definitions())
        
        # Sugestões do projeto
        project_defs = self.get_project_definitions()
        all_suggestions.update(project_defs['imports'])
        all_suggestions.update([f + '()' for f in project_defs['functions']])
        all_suggestions.update(project_defs['classes'])
        all_suggestions.update(project_defs['variables'])
        all_suggestions.update([os.path.basename(f) for f in project_defs['files']])
        all_suggestions.update(project_defs['folders'])
        all_suggestions.update(self.pip_packages)
        all_suggestions.update([f"{b}()" for b in self.get_extended_builtins()])
        
        # Adicionar templates da linguagem atual
        try:
            language = self.get_language()
            templates = get_available_templates(language)
            snippets = get_available_snippets(language)
            
            # Adicionar templates com prefixo
            all_suggestions.update([f"template:{t}" for t in templates])
            all_suggestions.update([f"snippet:{s}" for s in snippets])
            
        except ImportError:
            print("❌ CompletPronto não disponível para templates")
        
        # Filtrar por prefixo atual
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        prefix = cursor.selectedText().strip().lower()
        
        if prefix:
            starting = [s for s in all_suggestions if s.lower().startswith(prefix)]
            containing = [s for s in all_suggestions if prefix in s.lower() and not s.lower().startswith(prefix)]
            
            # Ordenar por relevância (templates primeiro)
            def relevance_sort(s):
                if s.startswith('template:'): return 0
                elif s.startswith('snippet:'): return 1
                elif s in self.extract_local_definitions(): return 2
                elif s in self.get_language_keywords(): return 3
                elif s in [f"{b}()" for b in self.get_extended_builtins()]: return 4
                elif s in project_defs['imports']: return 5
                elif s in project_defs['classes']: return 6
                elif s in [f + '()' for f in project_defs['functions']]: return 7
                elif s in project_defs['variables']: return 8
                elif s in [os.path.basename(f) for f in project_defs['files']]: return 9
                elif s in project_defs['folders']: return 10
                else: return 11
                
            starting.sort(key=relevance_sort)
            containing.sort(key=relevance_sort)
            
            return starting + containing
        else:
            return sorted(list(all_suggestions))

    def get_extended_builtins(self):
        """Retorna uma lista maior de built-ins"""
        extended_builtins = [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray',
            'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex',
            'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec',
            'filter', 'float', 'format', 'frozenset', 'getattr', 'globals',
            'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview',
            'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property',
            'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
            'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip',
            '__import__'
        ]
        return extended_builtins

    def insert_completion(self, text):
        """Insere a sugestão selecionada de forma inteligente - COM SUPORTE A TEMPLATES"""
        # Verificar se é um template (começa com "template:")
        if text.startswith('template:'):
            self._insert_template_completion(text)
            return
            
        # Verificar se é um snippet (começa com "snippet:")  
        if text.startswith('snippet:'):
            self._insert_snippet_completion(text)
            return
            
        cursor = self.textCursor()
        position = cursor.position()
        text_before = self.toPlainText()[:position]
        
        # Detectar se estamos em uma string (caminho de arquivo)
        if re.search(r'[\'\"][^\'\"]*$', text_before):
            # Encontrar a string atual
            match = re.search(r'[\'\"]([^\'\"]*)$', text_before)
            if match:
                prefix_len = len(match.group(1))
                cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, prefix_len)
                cursor.insertText(text)
                return
        
        # Detectar se estamos após um ponto (atributo/método)
        match = re.search(r'(\w+(?:\.\w+)*)\.(\w*)$', text_before)
        if match:
            prefix_len = len(match.group(2))
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, prefix_len)
            cursor.insertText(text.replace('()', ''))
        else:
            # Substituir palavra atual
            cursor.select(QTextCursor.WordUnderCursor)
            cursor.insertText(text)
            
        # Se for uma função, posicionar cursor dentro dos parênteses
        if text.endswith('()'):
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)

    def _insert_template_completion(self, template_text):
        """Insere um template de código com placeholders inteligentes"""
        try:
            template_name = template_text.replace('template:', '')
            language = self.get_language()
            
            # Obter o template base
            template = quick_template(language, template_name)
            
            if not template:
                print(f"❌ Template não encontrado: {template_name}")
                return
                
            # Processar placeholders especiais
            template = self._process_template_placeholders(template, template_name)
            
            # Inserir o template
            cursor = self.textCursor()
            
            # Remover a palavra atual se houver
            cursor.select(QTextCursor.WordUnderCursor)
            cursor.removeSelectedText()
            
            # Inserir o template
            cursor.insertText(template)
            
            # Posicionar cursor no primeiro placeholder ou posição padrão
            self._position_cursor_after_template(template)
            
            print(f"✅ Template inserido: {template_name}")
            
        except ImportError:
            print("❌ CompletPronto não encontrado")
        except Exception as e:
            print(f"❌ Erro ao inserir template: {e}")

    def _insert_snippet_completion(self, snippet_text):
        """Insere um snippet de código"""
        try:
            snippet_name = snippet_text.replace('snippet:', '')
            language = self.get_language()
            
            # Obter o snippet
            snippet = quick_snippet(language, snippet_name)
            
            if not snippet:
                print(f"❌ Snippet não encontrado: {snippet_name}")
                return
                
            # Inserir o snippet
            cursor = self.textCursor()
            
            # Remover a palavra atual se houver
            cursor.select(QTextCursor.WordUnderCursor)
            cursor.removeSelectedText()
            
            cursor.insertText(snippet)
            
            print(f"✅ Snippet inserido: {snippet_name}")
            
        except ImportError:
            print("❌ CompletPronto não encontrado")
        except Exception as e:
            print(f"❌ Erro ao inserir snippet: {e}")

    def _process_template_placeholders(self, template, template_name):
        """Processa placeholders especiais no template"""
        import re
        
        # Mapeamento de valores padrão baseado no nome do template
        default_values = {
            # Python
            'for_loop': {'var': 'i', 'start': '0', 'end': '10'},
            'for_loop_list': {'item': 'item', 'list_name': 'my_list'},
            'function_def': {'function_name': 'my_function', 'parameters': '', 'docstring': ''},
            'class_def': {'class_name': 'MyClass', 'docstring': '', 'parameters': ''},
            'if_statement': {'condition': 'condition'},
            'while_loop': {'condition': 'condition'},
            
            # JavaScript
            'function_def': {'functionName': 'myFunction', 'parameters': ''},
            'arrow_function': {'functionName': 'myFunction', 'parameters': ''},
            'for_loop': {'var': 'i', 'start': '0', 'end': '10'},
            
            # HTML
            'html5_boilerplate': {'title': 'My Page', 'css_file': 'style.css', 'js_file': 'script.js'},
            'div': {'class': '', 'content': ''},
            'paragraph': {'class': '', 'content': 'Hello World'},
        }
        
        # Aplicar valores padrão
        defaults = default_values.get(template_name, {})
        for key, value in defaults.items():
            placeholder = '{' + key + '}'
            if placeholder in template:
                template = template.replace(placeholder, value)
        
        # Processar placeholders especiais
        template = template.replace('{cursor}', '')  # Remove marcador de cursor
        
        # Para placeholders não substituídos, deixar vazio
        template = re.sub(r'\{[^}]+\}', '', template)
        
        return template

    def _position_cursor_after_template(self, template):
        """Posiciona o cursor inteligentemente após inserir template"""
        cursor = self.textCursor()
        
        # Lógica para posicionar cursor baseada no template
        if 'def ' in template and '):' in template:
            # Para funções, posicionar após os parênteses na linha do docstring
            lines = template.split('\n')
            for i, line in enumerate(lines):
                if '):' in line and i + 1 < len(lines):
                    # Mover para linha após a definição da função
                    cursor.movePosition(QTextCursor.StartOfLine)
                    for _ in range(i + 1):
                        cursor.movePosition(QTextCursor.Down)
                    cursor.movePosition(QTextCursor.EndOfLine)
                    break
                    
        elif 'for ' in template and '):' in template:
            # Para loops, posicionar dentro do loop
            lines = template.split('\n')
            for i, line in enumerate(lines):
                if '):' in line and i + 1 < len(lines):
                    cursor.movePosition(QTextCursor.StartOfLine)
                    for _ in range(i + 1):
                        cursor.movePosition(QTextCursor.Down)
                    cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, 4)  # Indentação
                    break
                    
        elif 'class ' in template and '):' in template:
            # Para classes, posicionar no __init__ ou após a definição
            if '__init__' in template:
                init_pos = template.find('__init__')
                cursor.setPosition(cursor.position() + init_pos)
            else:
                lines = template.split('\n')
                for i, line in enumerate(lines):
                    if '):' in line and i + 1 < len(lines):
                        cursor.movePosition(QTextCursor.StartOfLine)
                        for _ in range(i + 1):
                            cursor.movePosition(QTextCursor.Down)
                        cursor.movePosition(QTextCursor.EndOfLine)
                        break
        
        self.setTextCursor(cursor)

    def _get_fallback_suggestions(self):
        """Sugestões de fallback melhoradas"""
        return [
            "print()", "def", "class", "if", "else", "for", "while", 
            "import", "from", "return", "True", "False", "None",
            "len()", "str()", "list()", "dict()", "range()", "type()"
        ]

    # ===== CORREÇÃO DE INDENTAÇÃO AUTOMÁTICA =====
    def _paste_with_formatting(self):
        """Cola e formata automaticamente APENAS o texto colado"""
        try:
            # Obter a posição atual do cursor ANTES de colar
            original_cursor = self.textCursor()
            original_position = original_cursor.position()
            
            # Colar o texto normalmente
            self.paste()
            
            # Obter a nova posição do cursor após colar
            new_cursor = self.textCursor()
            new_position = new_cursor.position()
            
            # Calcular o texto que foi colado (baseado na diferença de posição)
            # Isso é uma aproximação - vamos selecionar da posição original até a nova
            selection_cursor = QTextCursor(self.document())
            selection_cursor.setPosition(original_position)
            selection_cursor.setPosition(new_position, QTextCursor.KeepAnchor)
            
            # Aplicar formatação APENAS no texto selecionado (texto colado)
            self._fix_pasted_indentation(selection_cursor)
            
            print("✅ Apenas o texto colado foi formatado automaticamente")
            
        except Exception as e:
            print(f"❌ Erro ao formatar texto colado: {e}")
    
    def _format_pasted_text(self):
        """Formata o texto que foi colado com indentação correta"""
        try:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                # Se não há seleção, formata da posição atual para baixo
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            
            selected_text = cursor.selectedText()
            if not selected_text.strip():
                return
                
            # Corrige a indentação do texto selecionado
            self._fix_pasted_indentation(cursor)
            
        except Exception as e:
            print(f"❌ Erro ao formatar texto colado: {e}")

    def _fix_pasted_indentation(self, cursor):
        """Corrige a indentação APENAS do texto colado"""
        try:
            if not cursor.hasSelection():
                return
                
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()
            
            cursor.beginEditBlock()
            
            start_block = self.document().findBlock(start_pos)
            end_block = self.document().findBlock(end_pos)
            
            current_block = start_block
            fixed_blocks = []
            
            # Determinar indentação base da primeira linha do texto colado
            first_line_text = start_block.text()
            base_indent = len(first_line_text) - len(first_line_text.lstrip())
            
            while current_block.isValid() and current_block.position() <= end_block.position():
                line_text = current_block.text()
                
                # Para a primeira linha do texto colado, manter a indentação original
                if current_block == start_block:
                    fixed_line = line_text
                else:
                    # Para linhas subsequentes do texto colado, ajustar indentação relativa
                    current_indent = len(line_text) - len(line_text.lstrip())
                    stripped = line_text.lstrip()
                    
                    # Se a linha não vazia, aplicar indentação relativa
                    if stripped:
                        # Manter a diferença relativa de indentação
                        relative_indent = max(0, current_indent - base_indent)
                        fixed_line = ' ' * (base_indent + relative_indent) + stripped
                    else:
                        fixed_line = line_text
                        
                fixed_blocks.append(fixed_line)
                current_block = current_block.next()
            
            # Substituir APENAS o texto selecionado (texto colado)
            cursor.setPosition(start_block.position())
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            
            current_block = start_block.next()
            while current_block.isValid() and current_block.position() <= end_block.position():
                cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                current_block = current_block.next()
            
            cursor.insertText('\n'.join(fixed_blocks))
            cursor.endEditBlock()
            
        except Exception as e:
            print(f"❌ Erro ao corrigir indentação do texto colado: {e}")
            cursor.endEditBlock()
    
    # ===== CONFIGURAÇÕES BÁSICAS =====
    def setup_basic_settings(self):
        """Configurações básicas do editor"""
        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(40)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setUndoRedoEnabled(True)
        self.document().setModified(False)
        self.setViewportMargins(50, 0, 0, 0)

    def setup_line_numbers(self):
        """Configura sistema de números de linha"""
        self.line_number_area = LineNumberArea(self)
        self.line_number_width = 0
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)

    def setup_code_folding(self):
        """Configura sistema de folding de código"""
        self.folding_area = CodeFoldingArea(self)
        self.updateRequest.connect(self.update_folding_area)

    def setup_syntax_highlighting(self):
        """Configura syntax highlighting usando o sistema organizado"""
        try:
            if self.file_path:
                # Usar o HighlighterFactory dos imports organizados
                self.highlighter = HighlighterFactory.create_highlighter(self.file_path, self.document())
                print(f"✅ Syntax highlighting configurado para: {self.file_path}")
            else:
                self.highlighter = None
        except Exception as e:
            print(f"❌ Erro no syntax highlighting: {e}")
            self.highlighter = None

    def setup_visual_indicators(self):
        """Configura indicadores visuais"""
        self.highlight_current_line()
        self.setup_indentation_guides()
        self.setup_vertical_guideline()

    def setup_signal_connections(self):
        """Configura todas as conexões de sinais"""
        self.textChanged.connect(self.on_text_changed)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.textChanged.connect(self.on_text_changed_for_outline)
        self.textChanged.connect(self.on_text_changed_for_lsp)
        self.cursorPositionChanged.connect(self.on_cursor_changed_for_lsp)

    def setup_final_settings(self):
        """Configurações finais"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setup_line_spacing()

    def setup_line_spacing(self):
        """Configura espaçamento entre linhas"""
        try:
            self.document().setDocumentMargin(4)
            self.setStyleSheet("QPlainTextEdit { padding: 2px; }")
        except Exception as e:
            print(f"Erro ao configurar espaçamento: {e}")

    # ===== MÉTODOS DE NUMERAÇÃO DE LINHAS =====
    def line_number_area_width(self):
        """Calcula largura da área de números"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, new_block_count):
        """Atualiza largura da área de números"""
        self.line_number_width = self.line_number_area_width()
        self.setViewportMargins(self.line_number_width + 16, 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Atualiza área de números quando texto é rolado"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

    def line_number_area_paint_event(self, event):
        """Pinta os números de linha"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(30, 30, 40))
        
        font = self.font()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor(150, 150, 150))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0, int(top), 
                    self.line_number_area.width() - 5, 
                    self.fontMetrics().height(),
                    Qt.AlignRight, number
                )
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    # ===== MÉTODOS DE FOLDING =====
    def update_folding_area(self, rect, dy):
        """Atualiza área de folding quando texto é rolado"""
        if dy:
            self.folding_area.scroll(0, dy)
        else:
            self.folding_area.update(0, rect.y(), self.folding_area.width(), rect.height())

    def folding_area_paint_event(self, event):
        """Pinta a área de folding"""
        painter = QPainter(self.folding_area)
        painter.fillRect(event.rect(), QColor(30, 30, 40))
        
        block = self.firstVisibleBlock()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and re.match(r'^\s*(def|class)', block.text()):
                rect = QRect(0, int(top), 16, self.fontMetrics().height())
                painter.setPen(QColor(150, 150, 150))
                painter.drawText(rect, Qt.AlignCenter, "+")
            
            block = block.next()
            top += self.blockBoundingRect(block).height()

    def get_basic_suggestions(self):
        """Sugestões básicas de fallback"""
        suggestions = set()
        code = self.toPlainText()
        
        keywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
            "try", "while", "with", "yield"
        ]
        suggestions.update(keywords)
        
        builtins = [
            "abs", "all", "any", "ascii", "bin", "bool", "breakpoint", "bytearray",
            "bytes", "callable", "chr", "classmethod", "compile", "complex",
            "delattr", "dict", "dir", "divmod", "enumerate", "eval", "exec",
            "filter", "float", "format", "frozenset", "getattr", "globals",
            "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
            "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview",
            "min", "next", "object", "oct", "open", "ord", "pow", "print", "property",
            "range", "repr", "reversed", "round", "set", "setattr", "slice", "sorted",
            "staticmethod", "str", "sum", "super", "tuple", "type", "vars", "zip"
        ]
        suggestions.update([f"{b}()" for b in builtins])
        
        functions = re.findall(r'def\s+(\w+)', code)
        suggestions.update([f"{f}()" for f in functions])
        
        classes = re.findall(r'class\s+(\w+)', code)
        suggestions.update(classes)
        
        return suggestions

    def get_language_keywords(self):
        """Retorna palavras-chave específicas da linguagem"""
        language = self.get_language()
        
        keywords_map = {
            'python': [
                "False", "None", "True", "and", "as", "assert", "async", "await",
                "break", "class", "continue", "def", "del", "elif", "else", "except",
                "finally", "for", "from", "global", "if", "import", "in", "is",
                "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
                "try", "while", "with", "yield"
            ],
            'javascript': [
                "break", "case", "catch", "class", "const", "continue", "debugger",
                "default", "delete", "do", "else", "export", "extends", "finally",
                "for", "function", "if", "import", "in", "instanceof", "new",
                "return", "super", "switch", "this", "throw", "try", "typeof",
                "var", "void", "while", "with", "yield", "await"
            ],
            'html': [
                "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6", "a", "img",
                "ul", "ol", "li", "table", "tr", "td", "th", "form", "input", "button"
            ],
            'css': [
                "color", "background", "font", "margin", "padding", "border",
                "width", "height", "display", "position", "float", "clear"
            ]
        }
        
        return keywords_map.get(language, [])

    def extract_local_definitions(self):
        """Extrai definições locais do código atual"""
        definitions = set()
        try:
            code = self.toPlainText()
            functions = re.findall(r'def\s+(\w+)', code)
            definitions.update([f"{f}()" for f in functions])
            classes = re.findall(r'class\s+(\w+)', code)
            definitions.update(classes)
        except Exception as e:
            print(f"Erro extrair definições: {e}")
        return definitions

    def get_project_modules(self):
        """Obtém módulos do projeto atual"""
        modules = set()
        try:
            if not self.project_path or not os.path.exists(self.project_path):
                return modules
                
            for root, dirs, files in os.walk(self.project_path):
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if '.git' in dirs:
                    dirs.remove('.git')
                if 'venv' in dirs:
                    dirs.remove('venv')
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.project_path)
                        module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                        if module_name.endswith('.__init__'):
                            module_name = module_name[:-9]
                        modules.add(module_name)
        except Exception as e:
            print(f"Erro buscar módulos projeto: {e}")
        return modules

    def get_language(self):
        """Obtém a linguagem do arquivo atual"""
        if not self.file_path:
            return "python"
        
        extension = os.path.splitext(self.file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'html',
            '.txt': 'text',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.sql': 'sql',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.ts': 'typescript'
        }
        return language_map.get(extension, 'text')

    # ===== MÉTODOS VISUAIS =====
    def highlight_current_line(self):
        """Destaca a linha atual"""
        extra_selections = []
    
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(45, 45, 48, 60)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)

    # ===== LINHA VERTICAL DE ORIENTAÇÃO =====
    def setup_vertical_guideline(self):
        """Configura a linha vertical de orientação como no VS Code/PyCharm"""
        self.guideline_enabled = True
        self.guideline_position = 80
        self.guideline_color = QColor(60, 60, 80, 120)
        
        self.guideline_timer = QTimer(self)
        self.guideline_timer.setSingleShot(True)
        self.guideline_timer.timeout.connect(self.update_guideline)
        
        self.cursorPositionChanged.connect(self.schedule_guideline_update)
        self.textChanged.connect(self.schedule_guideline_update)
        self.updateRequest.connect(self.schedule_guideline_update)

    def schedule_guideline_update(self):
        """Agenda atualização da linha vertical"""
        if self.guideline_enabled:
            self.guideline_timer.start(50)

    def update_guideline(self):
        """Atualiza a linha vertical de orientação"""
        if not self.guideline_enabled:
            return
            
        try:
            self.viewport().update()
        except Exception as e:
            print(f"❌ Erro ao atualizar linha vertical: {e}")

    def paintEvent(self, event):
        """Sobrescreve o paintEvent para desenhar a linha vertical"""
        super().paintEvent(event)
        
        if self.guideline_enabled:
            self.draw_vertical_guideline(event)

    def draw_vertical_guideline(self, event):
        """Desenha a linha vertical diretamente no viewport"""
        try:
            painter = QPainter(self.viewport())
            painter.setPen(QPen(self.guideline_color, 1))
            
            char_width = self.fontMetrics().horizontalAdvance(' ')
            guideline_x = self.guideline_position * char_width
            
            viewport_width = self.viewport().width()
            if guideline_x > viewport_width:
                return
                
            painter.drawLine(guideline_x, 0, guideline_x, self.viewport().height())
            
        except Exception as e:
            print(f"❌ Erro ao desenhar linha vertical: {e}")

    def get_last_visible_block(self):
        """Método auxiliar para obter o último bloco visível"""
        try:
            viewport_rect = self.viewport().rect()
            bottom = viewport_rect.bottom()
            
            cursor = self.cursorForPosition(viewport_rect.bottomLeft())
            if cursor.isNull():
                return self.document().lastBlock()
            return cursor.block()
            
        except Exception as e:
            print(f"❌ Erro ao obter último bloco visível: {e}")
            return self.document().lastBlock()

    def set_guideline_position(self, position):
        """Define a posição da linha vertical (em caracteres)"""
        self.guideline_position = position
        self.update_guideline()

    def toggle_guideline(self):
        """Alterna a exibição da linha vertical"""
        self.guideline_enabled = not self.guideline_enabled
        if self.guideline_enabled:
            self.update_guideline()
        else:
            self.viewport().update()

    def clear_guideline(self):
        """Remove a linha vertical"""
        self.guideline_enabled = False
        self.viewport().update()

    # ===== MÉTODOS DE FORMATAÇÃO =====
    def fix_indentation(self):
        """Corrige indentação do código Python de forma inteligente"""
        try:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                return
                
            selected_text = cursor.selectedText()
            if not selected_text.strip():
                return
            
            cursor.beginEditBlock()
            
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()
            
            start_block = self.document().findBlock(start_pos)
            end_block = self.document().findBlock(end_pos)
            
            current_block = start_block
            fixed_blocks = []
            
            while current_block.isValid() and current_block.position() <= end_block.position():
                line_text = current_block.text()
                fixed_line = self._fix_line_indentation(line_text, current_block.blockNumber())
                fixed_blocks.append(fixed_line)
                current_block = current_block.next()
            
            cursor.setPosition(start_block.position())
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            
            current_block = start_block.next()
            while current_block.isValid() and current_block.position() <= end_block.position():
                cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                current_block = current_block.next()
            
            cursor.insertText('\n'.join(fixed_blocks))
            cursor.endEditBlock()
            
        except Exception as e:
            print(f"Erro ao corrigir indentação do texto colado: {e}")

    def _fix_line_indentation(self, line_text, line_number):
        """Corrige indentação de uma linha específica"""
        stripped = line_text.lstrip()
        current_indent = len(line_text) - len(stripped)
        
        if line_number > 0:
            prev_block = self.document().findBlockByNumber(line_number - 1)
            if prev_block.isValid():
                prev_line = prev_block.text().rstrip()
                
                if prev_line.endswith(':'):
                    return '    ' + stripped
                
                elif prev_line and not prev_line.startswith('#') and not prev_line.endswith(('pass', 'return', 'break')):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    if current_indent < prev_indent:
                        return ' ' * prev_indent + stripped
        
        return ' ' * current_indent + stripped

    def basic_fix_indentation(self):
        """Correção básica de indentação como fallback"""
        text = self.toPlainText()
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.lstrip()
            indent_level = (len(line) - len(stripped)) // 4
            fixed_line = '    ' * indent_level + stripped
            fixed_lines.append(fixed_line)
            
        self.setPlainText('\n'.join(fixed_lines))

    # ===== CORREÇÕES SOLICITADAS =====

    def select_all_occurrences(self):
        """Seleciona todas as ocorrências da palavra sob o cursor"""
        cursor = self.textCursor()
        
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        
        selected_text = cursor.selectedText().strip()
        if not selected_text:
            return
        
        self.clear_selections()
        
        document = self.document()
        extra_selections = []
        
        search_cursor = QTextCursor(document)
        search_cursor.movePosition(QTextCursor.Start)
        
        while True:
            search_cursor = document.find(selected_text, search_cursor)
            if search_cursor.isNull():
                break
                
            if self._is_whole_word(search_cursor, selected_text):
                selection = QTextEdit.ExtraSelection()
                selection.format.setBackground(QColor(100, 100, 200, 80))
                selection.format.setForeground(Qt.white)
                selection.cursor = QTextCursor(search_cursor)
                extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
        print(f"✅ Selecionadas {len(extra_selections)} ocorrências de '{selected_text}'")

    def _is_whole_word(self, cursor, word):
        """Verifica se a seleção é uma palavra completa"""
        cursor_pos = cursor.position()
        document = self.document()
        
        if cursor_pos > 0:
            prev_cursor = QTextCursor(cursor)
            prev_cursor.setPosition(cursor_pos - 1)
            prev_char = prev_cursor.selectedText()
            if prev_char and (prev_char.isalnum() or prev_char == '_'):
                return False
        
        next_pos = cursor_pos + len(word)
        if next_pos < document.characterCount():
            next_cursor = QTextCursor(cursor)
            next_cursor.setPosition(next_pos)
            next_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            next_char = next_cursor.selectedText()
            if next_char and (next_char.isalnum() or next_char == '_'):
                return False
        
        return True

    def clear_selections(self):
        """Limpa todas as seleções extras"""
        self.setExtraSelections([])

    # ===== KEYPRESS EVENT CORRIGIDO E NÃO TRAVANTE =====
    def keyPressEvent(self, event):
        """Manipulação de teclas melhorada - NÃO TRAVA MAIS"""
        try:
            key = event.key()
            modifiers = event.modifiers()
            text = event.text()
            
            # Se autocomplete está visível
            if self.autocomplete_widget.isVisible():
                # Teclas de navegação - processar no autocomplete
                if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab, Qt.Key_Escape]:
                    self.autocomplete_widget.keyPressEvent(event)
                    return
                # Teclas de texto - processar normalmente e atualizar autocomplete
                elif text and text.isprintable():
                    self._typing_with_autocomplete = True
                    super().keyPressEvent(event)
                    self.realtime_suggestions_timer.start(150)
                    self._typing_with_autocomplete = False
                    return
            
            # Atalhos personalizados
            if modifiers == Qt.ControlModifier and key == Qt.Key_Space:
                self.force_show_autocomplete = True
                self.show_smart_autocomplete()
                return
            elif modifiers == Qt.ControlModifier and key == Qt.Key_D:
                self.select_all_occurrences()
                return
            elif key == Qt.Key_Escape:
                self.clear_selections()
                if self.autocomplete_widget.isVisible():
                    self.autocomplete_widget.hide()
                return
            elif key in [Qt.Key_Tab, Qt.Key_Backtab]:
                if self._handle_indentation_key(event):
                    return
            elif modifiers == Qt.ControlModifier and key == Qt.Key_V:
                self._paste_with_formatting()
                return
            
            # Processar tecla normalmente
            super().keyPressEvent(event)
            
            # Atualizar sugestões para caracteres comuns (quando autocomplete não está visível)
            if (not self.autocomplete_widget.isVisible() and 
                text and text.isprintable() and 
                not modifiers and key not in [Qt.Key_Backspace, Qt.Key_Delete]):
                self.autocomplete_timer.start(300)
                
        except Exception as e:
            print(f"❌ Erro no keyPressEvent: {e}")
            super().keyPressEvent(event)

    def _handle_indentation_key(self, event):
        """Manipula Tab e Shift+Tab de forma correta"""
        key = event.key()
        cursor = self.textCursor()
        
        if key == Qt.Key_Tab and cursor.hasSelection():
            self._indent_selection()
            return True
        elif key == Qt.Key_Backtab and cursor.hasSelection():
            self._unindent_selection()
            return True
        elif key == Qt.Key_Tab and not cursor.hasSelection():
            cursor.insertText("    ")
            return True
            
        return False

    def _indent_selection(self):
        """Adiciona indentação à seleção"""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
            
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.beginEditBlock()
        
        start_block = self.document().findBlock(start)
        end_block = self.document().findBlock(end)
        
        current_block = start_block
        while current_block.isValid() and current_block.position() <= end_block.position():
            block_cursor = QTextCursor(current_block)
            block_cursor.movePosition(QTextCursor.StartOfLine)
            block_cursor.insertText("    ")
            current_block = current_block.next()
        
        cursor.endEditBlock()

    def _unindent_selection(self):
        """Remove indentação da seleção"""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
            
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.beginEditBlock()
        
        start_block = self.document().findBlock(start)
        end_block = self.document().findBlock(end)
        
        current_block = start_block
        while current_block.isValid() and current_block.position() <= end_block.position():
            line_text = current_block.text()
            leading_spaces = len(line_text) - len(line_text.lstrip())
            
            if leading_spaces >= 4:
                block_cursor = QTextCursor(current_block)
                block_cursor.movePosition(QTextCursor.StartOfLine)
                block_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
                block_cursor.removeSelectedText()
            elif leading_spaces > 0:
                block_cursor = QTextCursor(current_block)
                block_cursor.movePosition(QTextCursor.StartOfLine)
                block_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, leading_spaces)
                block_cursor.removeSelectedText()
            
            current_block = current_block.next()
        
        cursor.endEditBlock()

    # ===== GUIAS DE INDENTAÇÃO =====
    def setup_indentation_guides(self):
        """Configura linhas de orientação para indentação"""
        self.indentation_guides_enabled = True
        self.indentation_guide_color = QColor(60, 60, 70, 60)
        
        self.guide_timer = QTimer(self)
        self.guide_timer.setSingleShot(True)
        self.guide_timer.timeout.connect(self.update_indentation_guides)
        
        self.cursorPositionChanged.connect(self.schedule_guide_update)
        self.textChanged.connect(self.schedule_guide_update)

    def schedule_guide_update(self):
        """Agenda atualização das guias de indentação"""
        if self.indentation_guides_enabled:
            self.guide_timer.start(100)

    def update_indentation_guides(self):
        """Atualiza as linhas de orientação para indentação"""
        if not self.indentation_guides_enabled:
            return
        
        try:
            extra_selections = []
            document = self.document()
            
            tab_width = 4
            max_guides = 8
            
            first_visible_block = self.firstVisibleBlock()
            if not first_visible_block.isValid():
                return
                
            last_visible_block = self.get_last_visible_block()
            
            block = first_visible_block
            while block.isValid() and block.blockNumber() <= last_visible_block.blockNumber():
                line_text = block.text()
                indent_level = len(line_text) - len(line_text.lstrip())
                
                for level in range(1, max_guides + 1):
                    guide_pos = level * tab_width
                    
                    if guide_pos > indent_level and guide_pos < len(line_text):
                        selection = QTextEdit.ExtraSelection()
                        selection.format.setBackground(self.indentation_guide_color)
                        
                        guide_cursor = QTextCursor(block)
                        guide_cursor.setPosition(block.position() + guide_pos)
                        guide_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
                        selection.cursor = guide_cursor
                        
                        extra_selections.append(selection)
                
                block = block.next()
            
            current_selections = self.extraSelections()
            non_guide_selections = [sel for sel in current_selections 
                                   if sel.format.background().color() != self.indentation_guide_color]
            
            self.setExtraSelections(non_guide_selections + extra_selections)
            
        except Exception as e:
            print(f"❌ Erro ao atualizar guias de indentação: {e}")

    def toggle_indentation_guides(self):
        """Alterna a exibição das linhas de orientação"""
        self.indentation_guides_enabled = not self.indentation_guides_enabled
        if self.indentation_guides_enabled:
            self.update_indentation_guides()
        else:
            self.clear_indentation_guides()

    def clear_indentation_guides(self):
        """Remove todas as guias de indentação"""
        current_selections = self.extraSelections()
        non_guide_selections = [sel for sel in current_selections 
                               if sel.format.background().color() != self.indentation_guide_color]
        self.setExtraSelections(non_guide_selections)

    # ===== MÉTODOS DE CONTEXTO =====
    def show_context_menu(self, position):
        """Menu de contexto personalizado"""
        menu = QMenu(self)
        
        undo_action = menu.addAction("↶ Desfazer (Ctrl+Z)")
        undo_action.triggered.connect(self.undo)
        undo_action.setEnabled(self.document().isUndoAvailable())
        
        redo_action = menu.addAction("↷ Refazer (Ctrl+Y)")
        redo_action.triggered.connect(self.redo)
        redo_action.setEnabled(self.document().isRedoAvailable())

        menu.addSeparator()
        
        cut_action = menu.addAction("✂️ Recortar (Ctrl+X)")
        cut_action.triggered.connect(self.cut)
        cut_action.setEnabled(self.textCursor().hasSelection())
        
        copy_action = menu.addAction("📋 Copiar (Ctrl+C)")
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(self.textCursor().hasSelection())
        
        paste_action = menu.addAction("📝 Colar")
        paste_action.triggered.connect(self._paste_with_formatting)
        
        select_all_action = menu.addAction("🔲 Selecionar tudo (Ctrl+A)")
        select_all_action.triggered.connect(self.selectAll)
        
        menu.addSeparator()
        
        fix_indent_action = menu.addAction("📐 Corrigir indentação (Ctrl+I)")
        fix_indent_action.triggered.connect(self.fix_indentation)
        
        increase_indent_action = menu.addAction("➡️ Aumentar indentação (Tab)")
        increase_indent_action.triggered.connect(self._indent_selection)
        
        decrease_indent_action = menu.addAction("⬅️ Diminuir indentação (Shift+Tab)")
        decrease_indent_action.triggered.connect(self._unindent_selection)
        
        menu.addSeparator()
    
        select_similar_action = menu.addAction("🎯 Selecionar ocorrências (Ctrl+D)")
        select_similar_action.triggered.connect(self.select_all_occurrences)
    
        clear_selections_action = menu.addAction("🧹 Limpar seleções (Esc)")
        clear_selections_action.triggered.connect(self.clear_selections)
        
        toggle_guides_action = menu.addAction("📐 Alternar guias de indentação")
        toggle_guides_action.triggered.connect(self.toggle_indentation_guides)
        toggle_guides_action.setCheckable(True)
        toggle_guides_action.setChecked(self.indentation_guides_enabled)
        
        toggle_guideline_action = menu.addAction("📏 Alternar linha vertical")
        toggle_guideline_action.triggered.connect(self.toggle_guideline)
        toggle_guideline_action.setCheckable(True)
        toggle_guideline_action.setChecked(self.guideline_enabled)
        
        force_autocomplete_action = menu.addAction("🚀 Forçar sugestões (Ctrl+Space)")
        force_autocomplete_action.triggered.connect(lambda: self.show_smart_autocomplete())
    
        menu.exec(self.mapToGlobal(position))

    # ===== MÉTODOS UTILITÁRIOS =====
    def get_ide(self):
        """Encontra a instância do IDE pai"""
        parent = self.parent()
        while parent and not hasattr(parent, 'project_path'):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent

    def on_text_changed(self):
        """Quando texto é modificado"""
        self.is_modified = True
        current_char = self.get_char_before_cursor()
        if current_char in ['.', '_'] or current_char.isalnum():
            self.autocomplete_timer.start(300)

    def get_char_before_cursor(self):
        """Obtém caractere antes do cursor"""
        cursor = self.textCursor()
        if cursor.position() > 0:
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
            return cursor.selectedText()
        return ""

    def on_cursor_position_changed(self):
        """Quando posição do cursor muda"""
        self.highlight_current_line()
        self.update_status_info()

    def update_status_info(self):
        """Atualiza informações na barra de status"""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        
        ide = self.get_ide()
        if ide and hasattr(ide, 'cursor_info_label'):
            ide.cursor_info_label.setText(f"Linha: {line}, Coluna: {column}")

    def resizeEvent(self, event):
        """Redimensiona áreas de números e folding"""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.folding_area.setGeometry(QRect(cr.left(), cr.top(), 16, cr.height()))
        self.line_number_area.setGeometry(QRect(cr.left() + 16, cr.top(), self.line_number_width, cr.height()))

    # ===== MÉTODOS LSP =====
    def set_lsp_manager(self, lsp_manager):
        """Define gerenciador LSP"""
        self.lsp_manager = lsp_manager
        if self.file_path and lsp_manager:
            lsp_manager.open_document(self.file_path, self.toPlainText())

    def on_text_changed_for_lsp(self):
        """Notifica mudanças para LSP"""
        if self.lsp_manager and self.file_path:
            self.lsp_manager.update_document(self.file_path, self.toPlainText())

    def on_cursor_changed_for_lsp(self):
        """Processa mudanças do cursor para LSP"""
        pass

    def on_text_changed_for_outline(self):
        """Atualiza outline quando texto muda"""
        if hasattr(self, 'outline_timer'):
            self.outline_timer.stop()
        else:
            self.outline_timer = QTimer()
            self.outline_timer.setSingleShot(True)
            self.outline_timer.timeout.connect(self.update_outline)
        
        self.outline_timer.start(500)

    def update_outline(self):
        """Notifica o IDE para atualizar o outline"""
        ide = self.get_ide()
        if ide and hasattr(ide, 'outline_widget'):
            ide.outline_widget.refresh_outline()

# CLASSE EnhancedCodeEditor (herda tudo de UnifiedCodeEditor)
class EnhancedCodeEditor(UnifiedCodeEditor):
    def __init__(self, text="", cursor_position=0, file_path="", project_path="", parent=None):
        super().__init__(text, cursor_position, file_path, project_path, parent)
        
        self.highlighting_manager = None
        self.syntax_highlighter = None
        self.lsp_manager = None
        self.lsp_completions = []
        self.minimap = None
        
        self.setup_enhanced_connections()
        
        # Usar o SyntaxHighlightingManager organizado
        if file_path and hasattr(parent, 'syntax_highlighting_manager'):
            parent.syntax_highlighting_manager.setup_editor_highlighter(self, file_path)

    def setup_enhanced_connections(self):
        """Configura conexões específicas do EnhancedCodeEditor"""
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.textChanged.connect(self.on_text_changed)
        self.textChanged.connect(self._on_text_changed_for_lsp)
        self.cursorPositionChanged.connect(self._on_cursor_changed_for_lsp)

    def on_text_changed(self):
        """Quando o texto é alterado"""
        self.is_modified = True

    def _on_text_changed_for_lsp(self):
        """Notifica mudanças para LSP"""
        if (self.lsp_manager and self.file_path and 
            not self.file_path.endswith('.py')):
            return
            
        content = self.toPlainText()
        if self.lsp_manager and self.file_path:
            self.lsp_manager.update_document(self.file_path, content)

    def _on_cursor_changed_for_lsp(self):
        """Processa mudanças do cursor para LSP"""
        pass

# CLASSE EditorTab
class EditorTab(QWidget):
    def __init__(self, file_path=None, parent=None):
        super().__init__(parent)
        
        self.file_path = file_path
        self.scope_header = None
        self.setup_editor()
        self.setup_ui()
        self.setup_scope_header()
        self.setup_indicators()

    def setup_editor(self):
        self.editor = EnhancedCodeEditor(
            text="",
            cursor_position=0,
            file_path=self.file_path,
            project_path=getattr(self.get_ide(), 'project_path', ''),
            parent=self
        )
            
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setTabStopDistance(40)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Configurar syntax highlighting usando o sistema organizado
        if self.file_path and hasattr(self.get_ide(), 'syntax_highlighting_manager'):
            self.get_ide().syntax_highlighting_manager.setup_editor_highlighter(self.editor, self.file_path)
        
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor.setPlainText(content)
            except Exception as e:
                print(f"Erro ao carregar arquivo: {e}")

    def setup_ui(self):
        """Configura a interface do usuário"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        self.setLayout(layout)

    def setup_indicators(self):
        """Configura todos os indicadores visuais"""
        palette = self.editor.palette()
        palette.setColor(QPalette.Highlight, QColor("#569cd6"))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.editor.setPalette(palette)
        
        self.editor.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.editor.textChanged.connect(self.on_text_changed)

    def setup_scope_header(self):
        """Configura o header flutuante de escopo"""
        self.scope_header = ScopeHeaderWidget(self)
        
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.scope_header)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.editor)
        
        self.setLayout(main_layout)
        self.scope_header.hide()

    def on_cursor_position_changed(self):
        """Chamado quando o cursor se move"""
        try:
            cursor = self.editor.textCursor()
            line = cursor.blockNumber() + 1
            
            current_class = self.find_current_class(line)
            current_function = self.find_current_function(line)
            
            self.update_scope_header(current_class, current_function)
            
        except Exception as e:
            print(f"Erro na mudança de cursor: {e}")

    def update_scope_header(self, current_class, current_function):
        """Atualiza o header de escopo"""
        if not self.scope_header:
            return
            
        self.scope_header.update_scope(current_class, current_function)
        
        if current_class != "Global" or current_function != "Nenhuma":
            self.scope_header.show_scope()
        else:
            self.scope_header.hide_scope()

    def find_current_class(self, current_line):
        """Encontra a classe atual"""
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        current_class = "Global"
        for i in range(current_line - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                class_match = re.match(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if class_match:
                    current_class = class_match.group(1)
                    break
        return current_class

    def find_current_function(self, current_line):
        """Encontra a função atual"""
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        current_function = "Nenhuma"
        for i in range(current_line - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                func_match = re.match(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if func_match:
                    current_function = func_match.group(1)
                    break
                    
        return current_function

    def get_ide(self):
        """Encontra a instância do IDE pai"""
        parent = self.parent()
        while parent and not hasattr(parent, 'project_path'):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent

    def on_text_changed(self):
        """Quando texto é modificado"""
        self.is_modified = True

    def save_file(self):
        """Salva o arquivo"""
        if not self.file_path:
            return self.save_file_as()
            
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            return True
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
            return False
            
    def save_file_as(self):
        """Salva o arquivo com novo nome"""
        ide = self.get_ide()
        if not ide:
            return False
            
        new_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Como",
            getattr(ide, 'project_path', ''),
            "Todos os Arquivos (*.*)"
        )
        
        if new_path:
            self.file_path = new_path
            return self.save_file()
            
        return False

    def get_content(self):
        """Retorna o conteúdo do editor"""
        return self.editor.toPlainText()
        
    def set_content(self, content):
        """Define o conteúdo do editor"""
        self.editor.setPlainText(content)

    def get_current_editor(self):
        """Retorna o editor deste tab"""
        return self.editor