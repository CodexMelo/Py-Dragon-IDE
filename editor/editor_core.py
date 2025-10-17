from PySide6.QtWidgets import (QPlainTextEdit, QWidget, QVBoxLayout, QMenu, 
                              QMessageBox, QFileDialog, QListWidget, QListWidgetItem,QTextEdit)
from PySide6.QtCore import Qt, QTimer, QRect, QRegularExpression
from PySide6.QtGui import (QFont, QTextCursor, QSyntaxHighlighter, QTextCharFormat, 
                          QColor, QPainter, QPalette, QTextFormat)
import os
import re
from editor.line_numbers import LineNumberArea
from editor.code_folding import CodeFoldingArea
from syntax.highlighters import HighlighterFactory


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
        
        # ===== SISTEMA DE AUTOCOMPLETE =====
        self.setup_autocomplete_system()
        
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

    def get_suggestions(self, code, cursor_position, file_path="", project_path=""):
        """Método principal unificado para obter todas as sugestões"""
        try:
            context = self._analyze_context(code, cursor_position, file_path)
            suggestions = self._get_hierarchical_suggestions(context)
            filtered_suggestions = self._filter_and_prioritize(suggestions, context)
            return filtered_suggestions[:25]
        except Exception as e:
            print(f"❌ Erro no sistema unificado: {e}")
            return []  # CORREÇÃO: Retornar lista vazia

    def _analyze_context(self, code, cursor_position, file_path):
        """Analisa o contexto atual para sugestões"""
        return {
            'code': code,
            'cursor_position': cursor_position,
            'file_path': file_path,
            'current_line': self._get_current_line(code, cursor_position),
            'previous_char': self._get_previous_char(code, cursor_position)
        }

    def _get_current_line(self, code, cursor_position):
        """Obtém a linha atual do cursor"""
        lines = code.split('\n')
        current_line_num = 0
        chars_count = 0
        
        for i, line in enumerate(lines):
            chars_count += len(line) + 1  # +1 para o \n
            if chars_count >= cursor_position:
                current_line_num = i
                break
        
        return lines[current_line_num] if current_line_num < len(lines) else ""

    def _get_previous_char(self, code, cursor_position):
        """Obtém o caractere anterior ao cursor"""
        if cursor_position > 0 and cursor_position <= len(code):
            return code[cursor_position - 1]
        return ""

    def _get_hierarchical_suggestions(self, context):
        """Obtém sugestões hierárquicas baseadas no contexto"""
        suggestions = set()
        
        # Adiciona palavras-chave da linguagem
        suggestions.update(self._get_language_keywords())
        
        # Adiciona definições locais
        suggestions.update(self._extract_local_definitions())
        
        # Adiciona módulos do projeto
        suggestions.update(self._get_project_modules())
        
        return list(suggestions)

    def _filter_and_prioritize(self, suggestions, context):
        """Filtra e prioriza sugestões baseadas no contexto"""
        if not suggestions:
            return []
        
        # Filtra por caractere atual se disponível
        current_char = context.get('previous_char', '')
        if current_char and current_char.isalpha():
            filtered = [s for s in suggestions if s.lower().startswith(current_char.lower())]
            if filtered:
                return filtered
        
        return sorted(suggestions)

    def setup_autocomplete_system(self):
        """Configura sistema completo de autocomplete - VERSÃO CORRIGIDA"""
        # Timer para autocomplete automático
        self.autocomplete_timer = QTimer(self)
        self.autocomplete_timer.setSingleShot(True)
        self.autocomplete_timer.timeout.connect(self.show_autocomplete)
        
        # Widget de autocomplete flutuante
        try:
            from .autocomplete import FloatingAutoCompleteWidget
            self.autocomplete_widget = FloatingAutoCompleteWidget(self)
        except ImportError:
            # Fallback se não conseguir importar
            class BasicAutoCompleteWidget:
                def __init__(self, parent):
                    self.parent = parent
                    self.enabled = True
                
                def show_completions(self, editor, suggestions, position=None):
                    if suggestions:
                        print(f"📝 Autocomplete: {len(suggestions)} sugestões")
                
                def hide(self):
                    pass
                
                def isVisible(self):
                    return False
                    
                def set_enabled(self, enabled):
                    self.enabled = enabled
            
            self.autocomplete_widget = BasicAutoCompleteWidget(self)
        
        # Completador inteligente
        try:
            from .autocomplete import UnifiedSuggestionSystem
            self.completer = UnifiedSuggestionSystem()
        except ImportError:
            # Fallback básico
            class BasicCompleter:
                def get_completions(self, text, cursor_position, file_path="", project_path=""):
                    return ["print", "def", "class", "if", "else", "for", "while"]
            
            self.completer = BasicCompleter()
        
        # Variáveis de controle
        self.last_key_pressed = None
        self.force_show_autocomplete = False
        
        print("✅ Sistema de autocomplete configurado")

    def _get_fallback_suggestions(self):
        """Sugestões de fallback mínimas e seguras"""
        return [
            "print", "def", "class", "if", "else", "for", "while", "import", 
            "from", "return", "True", "False", "None", "len", "str", "list", 
            "dict", "range", "type", "isinstance"
        ]

    def setup_basic_settings(self):
        """Configurações básicas do editor"""
        # Fonte e tabulação
        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(40)  # 4 espaços
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Habilitar undo/redo
        self.setUndoRedoEnabled(True)
        self.document().setModified(False)
        
        # Configurar margens
        self.setViewportMargins(50, 0, 0, 0)

    def setup_line_numbers(self):
        """Configura sistema de números de linha"""
        self.line_number_area = LineNumberArea(self)
        self.line_number_width = 0
        
        # Conectar sinais para atualizar números
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)

    def get_enhanced_suggestions(self):
        """Obtém sugestões melhoradas de forma unificada"""
        suggestions = set()
        
        try:
            # 1. Palavras-chave da linguagem atual
            language_keywords = self.get_language_keywords()
            suggestions.update(language_keywords)
            
            # 2. Definições locais do arquivo
            local_definitions = self.extract_local_definitions()
            suggestions.update(local_definitions)
            
            # 3. Módulos do projeto (se disponível)
            if hasattr(self, 'project_path') and self.project_path:
                project_modules = self.get_project_modules()
                suggestions.update(project_modules)
                
            # 4. Sugestões do sistema de autocomplete base
            base_suggestions = self.get_suggestions_for_autocomplete()
            if base_suggestions:
                suggestions.update(base_suggestions)
            
            # 5. Remove duplicatas e limita resultados
            unique_suggestions = sorted(list(suggestions))
            return unique_suggestions[:25]  # CORREÇÃO: 25 em vez de 10000
            
        except Exception as e:
            print(f"❌ Erro no enhanced suggestions: {e}")
            return self._get_fallback_suggestions()

    def get_suggestions_for_autocomplete(self):
        """Obtém sugestões básicas para autocomplete"""
        return self.get_basic_suggestions()

    def setup_code_folding(self):
        """Configura sistema de folding de código"""
        self.folding_area = CodeFoldingArea(self)
        
        # Conectar sinal para atualizar folding
        self.updateRequest.connect(self.update_folding_area)

    def show_autocomplete(self):
        """Mostra sugestões de autocomplete - VERSÃO FINAL CORRIGIDA"""
        if not self.autocomplete_widget.enabled:
            return
            
        try:
            # Usa o sistema unificado de sugestões
            suggestions = self.get_unified_suggestions()
            
            if suggestions:
                cursor_rect = self.cursorRect()
                self.autocomplete_widget.show_completions(self, suggestions, cursor_rect.bottomLeft())
                
        except Exception as e:
            print(f"❌ Erro crítico no autocomplete: {e}")
            # Tenta fallback básico em caso de erro crítico
            try:
                basic_suggestions = self._get_fallback_suggestions()
                if basic_suggestions:
                    cursor_rect = self.cursorRect()
                    self.autocomplete_widget.show_completions(self, basic_suggestions, cursor_rect.bottomLeft())
            except Exception as e2:
                print(f"❌ Erro até no fallback: {e2}")
                
    # No seu método setup_syntax_highlighting()
    def setup_syntax_highlighting(self):
        """Configura syntax highlighting - VERSÃO CORRIGIDA DEFINITIVA"""
        try:
            # Sistema básico que sempre funciona
            if self.file_path and self.file_path.endswith('.py'):
                from syntax.highlighters import PythonHighlighter
                self.highlighter = PythonHighlighter(self.document())
                print("✅ Highlighter Python carregado")
            elif self.file_path and self.file_path.endswith('.js'):
                from syntax.highlighters import JavaScriptHighlighter
                self.highlighter = JavaScriptHighlighter(self.document())
                print("✅ Highlighter JavaScript carregado")
            elif self.file_path and self.file_path.endswith(('.html', '.htm')):
                from syntax.highlighters import HTMLHighlighter
                self.highlighter = HTMLHighlighter(self.document())
                print("✅ Highlighter HTML carregado")
            elif self.file_path and self.file_path.endswith('.css'):
                from syntax.highlighters import CSSHighlighter
                self.highlighter = CSSHighlighter(self.document())
                print("✅ Highlighter CSS carregado")
            elif self.file_path and self.file_path.endswith('.json'):
                from syntax.highlighters import JSONHighlighter
                self.highlighter = JSONHighlighter(self.document())
                print("✅ Highlighter JSON carregado")
            else:
                # Para outras linguagens, usa highlighter genérico
                from syntax.highlighters import TextHighlighter
                self.highlighter = TextHighlighter(self.document())
                print("✅ Highlighter genérico carregado")
                
        except Exception as e:
            print(f"❌ Erro no syntax highlighting: {e}")
        # Fallback absoluto - nenhum highlighter
            self.highlighter = None
    def setup_visual_indicators(self):
        """Configura indicadores visuais"""
        # Highlight da linha atual
        self.highlight_current_line()
    
    def setup_signal_connections(self):
        """Configura todas as conexões de sinais"""
        # Sinais básicos
        self.textChanged.connect(self.on_text_changed)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        
        # Sinais para funcionalidades avançadas
        self.textChanged.connect(self.on_text_changed_for_outline)
        self.textChanged.connect(self.on_text_changed_for_lsp)
        self.cursorPositionChanged.connect(self.on_cursor_changed_for_lsp)

    def setup_final_settings(self):
        """Configurações finais"""
        # Menu de contexto
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Espaçamento entre linhas
        self.setup_line_spacing()

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
        self.setViewportMargins(self.line_number_width + 16, 0, 0, 0)  # +16 para folding

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

    # ===== MÉTODOS DE AUTOCOMPLETE =====
    
    def on_text_changed(self):
        """Quando texto é modificado"""
        self.is_modified = True
        
        # Dispara autocomplete
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

    def _get_language_keywords(self):
        """Retorna palavras-chave específicas da linguagem - MÉTODO ADICIONADO"""
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

    def _extract_local_definitions(self):
        """Extrai definições locais do código atual - MÉTODO ADICIONADO"""
        definitions = set()
        try:
            code = self.toPlainText()
            
            # Funções
            functions = re.findall(r'def\s+(\w+)', code)
            definitions.update([f"{f}()" for f in functions])
            
            # Classes
            classes = re.findall(r'class\s+(\w+)', code)
            definitions.update(classes)
            
            # Variáveis (nomes com mais de 2 caracteres)
            variables = re.findall(r'(\b[a-zA-Z_][a-zA-Z0-9_]{2,})\b\s*=', code)
            definitions.update(variables)
            
        except Exception as e:
            print(f"Erro extrair definições: {e}")
        
        return definitions

    def get_current_word(self, text_before):
        """Extrai a palavra atual sendo digitada"""
        try:
            # Encontra o início da palavra atual
            word_chars = []
            for char in reversed(text_before):
                if char.isalnum() or char in ['_', '.']:
                    word_chars.append(char)
                else:
                    break
            
            return ''.join(reversed(word_chars)) if word_chars else ""
        except:
            return ""
    
    def _get_project_modules(self):
        """Método auxiliar para compatibilidade"""
        return self.get_project_modules()
        
    def get_basic_suggestions(self):
        """Sugestões básicas de fallback"""
        suggestions = set()
        code = self.toPlainText()
        
        # Palavras-chave Python
        keywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
            "try", "while", "with", "yield"
        ]
        suggestions.update(keywords)
        
        # Funções built-in
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
        
        # Definições locais
        functions = re.findall(r'def\s+(\w+)', code)
        suggestions.update([f"{f}()" for f in functions])
        
        classes = re.findall(r'class\s+(\w+)', code)
        suggestions.update(classes)
        
        return suggestions

    # ===== MÉTODOS DE SYNTAX HIGHLIGHTING =====
    
    def detect_language(self):
        """Detecta linguagem baseada na extensão do arquivo"""
        if not self.file_path:
            return "python"
        
        extension = os.path.splitext(self.file_path)[1].lower()
        language_map = {
            '.py': 'python', '.js': 'javascript', '.html': 'html', '.css': 'css',
            '.json': 'json', '.xml': 'html', '.txt': 'text', '.md': 'markdown',
            '.yml': 'yaml', '.yaml': 'yaml', '.sql': 'sql', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby',
            '.go': 'go', '.rs': 'rust', '.swift': 'swift', '.kt': 'kotlin', '.ts': 'typescript'
        }
        return language_map.get(extension, 'text')

    # ===== MÉTODOS VISUAIS =====
    
    def highlight_current_line(self):
        """Destaca a linha atual"""
        extra_selections = []
    
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()  # ✅ CORREÇÃO: Use QTextEdit.ExtraSelection
            line_color = QColor(45, 45, 48, 60)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)

    def setup_line_spacing(self):
        """Configura espaçamento entre linhas"""
        try:
            self.document().setDocumentMargin(4)
            self.setStyleSheet("QPlainTextEdit { padding: 2px; }")
        except Exception as e:
            print(f"Erro ao configurar espaçamento: {e}")

    # ===== MÉTODOS DE FORMATAÇÃO =====
    
    def fix_indentation(self):
        """Corrige indentação do código Python de forma inteligente"""
        try:
            cursor = self.textCursor()
            cursor.beginEditBlock()
            
            # Salva posição do cursor
            original_position = cursor.position()
            
            text = self.toPlainText()
            lines = text.split('\n')
            fixed_lines = []
            indent_stack = [0]  # Pilha de níveis de indentação
            
            for i, line in enumerate(lines):
                stripped = line.lstrip()
                current_indent = len(line) - len(stripped)
                
                # Remove indentação antiga
                clean_line = stripped
                
                # Calcula indentação correta baseada no contexto
                if i > 0:
                    prev_line = lines[i-1].rstrip()
                    
                    # Diminui indentação após blocos que terminam
                    if (prev_line.endswith('pass') or 
                        prev_line.endswith('return') or
                        prev_line.endswith('break') or
                        prev_line.endswith('continue')):
                        if indent_stack and current_indent <= indent_stack[-1]:
                            indent_stack.pop()
                    
                    # Aumenta indentação após dois pontos
                    if prev_line.endswith(':'):
                        new_indent = (len(prev_line) - len(prev_line.lstrip())) + 4
                        indent_stack.append(new_indent)
                
                # Aplica indentação atual da pilha
                current_indent_level = indent_stack[-1] if indent_stack else 0
                fixed_line = (' ' * current_indent_level) + clean_line
                fixed_lines.append(fixed_line)
            
            # Aplica texto corrigido
            new_text = '\n'.join(fixed_lines)
            self.setPlainText(new_text)
            
            # Restaura posição do cursor aproximadamente
            new_cursor = self.textCursor()
            new_cursor.setPosition(min(original_position, len(new_text)))
            self.setTextCursor(new_cursor)
            
            cursor.endEditBlock()
            
        except Exception as e:
            print(f"Erro ao corrigir indentação: {e}")
            # Fallback básico
            self.basic_fix_indentation()

    def basic_fix_indentation(self):
        """Correção básica de indentação como fallback"""
        text = self.toPlainText()
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.lstrip()
            # Converte tabs para 4 espaços e mantém indentação existente
            indent_level = (len(line) - len(stripped)) // 4
            fixed_line = '    ' * indent_level + stripped
            fixed_lines.append(fixed_line)
            
        self.setPlainText('\n'.join(fixed_lines))   

    def clean_trailing_whitespace(self):
        """Remove espaços em branco no final das linhas"""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        block = self.document().firstBlock()
        while block.isValid():
            text = block.text()
            stripped = text.rstrip()
            if text != stripped:
                cursor.setPosition(block.position())
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cursor.insertText(stripped)
            block = block.next()
        
        cursor.endEditBlock()

    # ===== MÉTODOS DE NAVEGAÇÃO =====
    def get_python_block_structure(self):
        """Analisa a estrutura de blocos do código Python"""
        text = self.toPlainText()
        lines = text.split('\n')
        structure = []
        indent_stack = [0]
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            # Detecta início de blocos
            if stripped.endswith(':'):
                block_type = self.detect_block_type(stripped)
                structure.append({
                    'line': i + 1,
                    'type': block_type,
                    'name': self.extract_block_name(stripped, block_type),
                    'indent': current_indent,
                    'end_line': None  # Será preenchido depois
                })
                
                # Adiciona novo nível de indentação
                indent_stack.append(current_indent + 4)
        
        return structure

    def detect_block_type(self, line):
        """Detecta o tipo de bloco Python"""
        line_clean = line.strip()
        
        if line_clean.startswith('class '):
            return 'class'
        elif line_clean.startswith('def '):
            return 'function'
        elif line_clean.startswith('async def '):
            return 'async_function'
        elif line_clean.startswith('if '):
            return 'if'
        elif line_clean.startswith('for '):
            return 'for'
        elif line_clean.startswith('while '):
            return 'while'
        elif line_clean.startswith('with '):
            return 'with'
        elif line_clean.startswith('try:'):
            return 'try'
        elif line_clean.startswith('except'):
            return 'except'
        else:
            return 'block'

    def extract_block_name(self, line, block_type):
        """Extrai o nome do bloco"""
        if block_type == 'class':
            return line.split('class ')[1].split('(')[0].split(':')[0].strip()
        elif block_type in ['function', 'async_function']:
            return line.split('def ')[1].split('(')[0].strip()
        else:
            return line.split(':')[0].strip()
    def goto_line(self, line_number):
        """Vai para uma linha específica"""
        if line_number < 1:
            return
                
        document = self.document()
        block = document.findBlockByLineNumber(line_number - 1)
            
        if block.isValid():
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)
            self.centerCursor()

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
        # Implementar hover information se desejado
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

    # ===== MÉTODOS DE CONTEXTO E TECLADO =====
    
    def show_context_menu(self, position):
        """Menu de contexto personalizado com opções de indentação"""
        menu = QMenu(self)
        
        # Ações de edição
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
        
        paste_action = menu.addAction("📝 Colar (Ctrl+V)")
        paste_action.triggered.connect(self.paste)
        
        select_all_action = menu.addAction("🔲 Selecionar tudo (Ctrl+A)")
        select_all_action.triggered.connect(self.selectAll())
        
        menu.addSeparator()
        
        # Ações específicas do editor - NOVAS OPÇÕES
        fix_indent_action = menu.addAction("📐 Corrigir indentação (Ctrl+I)")
        fix_indent_action.triggered.connect(self.fix_indentation)
        
        increase_indent_action = menu.addAction("➡️ Aumentar indentação (Tab)")
        increase_indent_action.triggered.connect(self.increase_indentation)
        
        decrease_indent_action = menu.addAction("⬅️ Diminuir indentação (Shift+Tab)")
        decrease_indent_action.triggered.connect(self.decrease_indentation)
        
        auto_complete_action = menu.addAction("🎯 Auto-completar (Ctrl+Space)")
        auto_complete_action.triggered.connect(self.show_autocomplete)
        
        menu.exec(self.mapToGlobal(position))

    def increase_indentation(self):
        """Aumenta indentação da seleção ou linha atual"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.auto_indent_selection()
        else:
            cursor.insertText("    ")

    def trigger_autocomplete(self):
        """Dispara o autocomplete após digitação - VERSÃO SIMPLIFICADA"""
        if not self.autocomplete_widget.enabled:
            return
            
        try:
            # Obtém sugestões unificadas
            suggestions = self.get_unified_suggestions()
            
            if suggestions:
                cursor_rect = self.cursorRect()
                self.autocomplete_widget.show_completions(self, suggestions, cursor_rect.bottomLeft())
                        
        except Exception as e:
            print(f"Erro no trigger_autocomplete: {e}")

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

    def get_filtered_suggestions(self, current_char):
        """Obtém sugestões filtradas pela letra inicial"""
        all_suggestions = self.get_suggestions_for_autocomplete()
        
        if not current_char or len(current_char) != 1:
            return all_suggestions
            
        # Filtra sugestões que começam com a letra (case insensitive)
        filtered = [s for s in all_suggestions if s.lower().startswith(current_char.lower())]
        
        # Se não encontrou sugestões específicas, mostra todas
        if not filtered and current_char.isalpha():
            return all_suggestions
            
        return filtered
    
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
        
        # Área de folding (esquerda)
        self.folding_area.setGeometry(
            QRect(cr.left(), cr.top(), 16, cr.height())
        )
        
        # Área de números de linha (ao lado do folding)
        self.line_number_area.setGeometry(
            QRect(cr.left() + 16, cr.top(), self.line_number_width, cr.height())
        )

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
        """Extrai definições locais do código atual - MÉTODO SEGURO"""
        definitions = set()
        try:
            code = self.toPlainText()
            
            # Funções
            functions = re.findall(r'def\s+(\w+)', code)
            definitions.update([f"{f}()" for f in functions])
            
            # Classes
            classes = re.findall(r'class\s+(\w+)', code)
            definitions.update(classes)
            
        except Exception as e:
            print(f"Erro extrair definições: {e}")
        
        return definitions

    def get_project_modules(self):
        """Obtém módulos do projeto atual - MÉTODO SEGURO"""
        modules = set()
        try:
            if not self.project_path or not os.path.exists(self.project_path):
                return modules
                
            # Busca por arquivos Python no projeto
            for root, dirs, files in os.walk(self.project_path):
                # Ignora diretórios comuns
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if '.git' in dirs:
                    dirs.remove('.git')
                if 'venv' in dirs:
                    dirs.remove('venv')
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        # Calcula nome do módulo
                        rel_path = os.path.relpath(os.path.join(root, file), self.project_path)
                        module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                        
                        # Remove __init__ do final se for pacote
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
    
    def get_unified_suggestions(self):
        """Sistema unificado de sugestões - VERSÃO CORRIGIDA"""
        try:
            # Usa o completador do IDE se disponível
            ide = self.get_ide()
            if ide and hasattr(ide, 'completer'):
                code = self.toPlainText()
                cursor_position = self.textCursor().position()
                
                suggestions = ide.completer.get_completions(
                    code, 
                    cursor_position,
                    self.file_path,
                    getattr(ide, 'project_path', "")
                )
                
                if suggestions:
                    return suggestions[:25]  # Limita a 25 sugestões
            
            # Fallback para sistema interno
            return self.get_enhanced_suggestions()
            
        except Exception as e:
            print(f"❌ Erro no unified suggestions: {e}")
            return self._get_fallback_suggestions()

    # Substitua o método keyPressEvent existente:

    def keyPressEvent(self, event):
            try:
                key = event.key()
                modifiers = event.modifiers()
                text = event.text()
            
            # Captura a tecla pressionada
                self.last_key_pressed = key
            
            # Ctrl+Space - Força autocomplete
                if modifiers == Qt.ControlModifier and key == Qt.Key_Space:
                    self.force_show_autocomplete = True
                    self.show_autocomplete()
                    event.accept()
                    return
                
            # Ctrl+I - Corrige indentação
                elif modifiers == Qt.ControlModifier and key == Qt.Key_I:
                    self.fix_indentation()
                    event.accept()
                    return  
                
            # Tab com Shift - diminui indentação
                elif modifiers == Qt.ShiftModifier and key == Qt.Key_Tab:
                    self.decrease_indentation()
                    event.accept()
                    return
                
            # Tab normal - aumenta indentação
                elif key == Qt.Key_Tab:
                    if self.handle_indentation(event):
                        event.accept()
                        return
                    
            # Enter - indentação inteligente
                elif key in [Qt.Key_Return, Qt.Key_Enter]:
                    if self.handle_indentation(event):
                        event.accept()
                        return
                    
            # Escape - desativa autocomplete temporariamente
                elif key == Qt.Key_Escape:
                    if self.autocomplete_widget.isVisible():
                        self.autocomplete_widget.hide()
                        event.accept()
                        return
                # Se autocomplete não está visível, reativa para próxima letra
                    self.autocomplete_widget.set_enabled(True)
                
            # Letras e caracteres que devem ativar autocomplete
                elif (len(text) == 1 and 
                    (text.isalpha() or text in ['.', '_']) and 
                    self.autocomplete_widget.enabled):
                
                # Processa a tecla normalmente primeiro
                    super().keyPressEvent(event)
                
                # CORREÇÃO: Usar o método correto
                    QTimer.singleShot(50, self.trigger_autocomplete)
                    return
                
            # Enter/Tab com autocomplete visível
                elif key in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab]:
                    if self.autocomplete_widget.isVisible():
                        self.autocomplete_widget.insert_completion()
                        event.accept()
                        return
                    
            # Teclas normais
                super().keyPressEvent(event)
            
            # Para outras teclas, esconde o autocomplete
                if self.autocomplete_widget.isVisible():
                    self.autocomplete_widget.hide()
            
            except Exception as e:
                print(f"Erro no keyPressEvent: {e}")
                super().keyPressEvent(event)


    def handle_indentation(self, event):
            try:
                key = event.key()
                cursor = self.textCursor()
                current_block = cursor.block()
                current_text = current_block.text()
                cursor_position = cursor.positionInBlock()
            
            # Tab - aumenta indentação
                if key == Qt.Key_Tab and not cursor.hasSelection():
                # Se está no início da linha ou em espaço em branco, insere tab
                    if cursor_position <= len(current_text) - len(current_text.lstrip()):
                        cursor.insertText("    ")
                        return True
                    else:
                    # Tab normal
                        cursor.insertText("    ")
                        return True
                    
            # Shift+Tab - diminui indentação
                elif key == Qt.Key_Backtab:
                    self.decrease_indentation()
                    return True
                
            # Enter - mantém indentação automaticamente
                elif key in [Qt.Key_Return, Qt.Key_Enter]:
                    return self.handle_enter_key()
                
            except Exception as e:
                print(f"Erro na indentação: {e}")
        
                return False

    def handle_enter_key(self):
        
            cursor = self.textCursor()
            current_block = cursor.block()
            current_text = current_block.text()
        
        # Calcula indentação atual
            indent_level = len(current_text) - len(current_text.lstrip())
            current_indent = " " * indent_level
        
        # Verifica contexto para indentação adicional
            additional_indent = self.get_additional_indent(current_text.rstrip())
        
            cursor.insertText("\n" + current_indent + additional_indent)
            return True
    def decrease_indentation(self):
        cursor = self.textCursor()
        current_block = cursor.block()
        current_text = current_block.text()
        
        # Encontra espaços iniciais para remover
        leading_spaces = len(current_text) - len(current_text.lstrip())
        if leading_spaces >= 4:
            # Remove 4 espaços
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
            cursor.removeSelectedText()
        elif leading_spaces > 0:
            # Remove todos os espaços restantes
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, leading_spaces)
        cursor.removeSelectedText()
    def get_additional_indent(self, line_text):
        """Determina indentação adicional baseada no contexto Python"""
        try:
            if not line_text:
                return ""
                
            line_clean = line_text.rstrip()
            
            # Casos que precisam de indentação adicional
            if any(line_clean.endswith(suffix) for suffix in [':', '(', '[', '{']):
                return "    "  # 4 espaços
            
            # Casos especiais para Python
            python_keywords = ['def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ']
            if any(line_clean.startswith(keyword) for keyword in python_keywords):
                return "    "
            
            return ""
        except Exception as e:
            print(f"Erro ao determinar indentação adicional: {e}")
            return ""
    
	

    def auto_indent_selection(self):
        """Aplica indentação automática à seleção"""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.beginEditBlock()
        
        # Itera pelas linhas selecionadas
        temp_cursor = QTextCursor(cursor)
        temp_cursor.setPosition(start)
        temp_cursor.movePosition(QTextCursor.StartOfLine)
        
        while temp_cursor.position() <= end:
            block = temp_cursor.block()
            if block.isValid():
                line_text = block.text()
                # Adiciona 4 espaços no início
                temp_cursor.movePosition(QTextCursor.StartOfLine)
                temp_cursor.insertText("    " + line_text.lstrip())
                temp_cursor.movePosition(QTextCursor.Down)
                temp_cursor.movePosition(QTextCursor.StartOfLine)
            else:
                break
        
        cursor.endEditBlock()











# ... (o restante do código para EnhancedCodeEditor e EditorTab permanece similar)
class EnhancedCodeEditor(UnifiedCodeEditor):
    def __init__(self, text="", cursor_position=0, file_path="", project_path="", parent=None):
        super().__init__(text, cursor_position, file_path, project_path, parent)
        
        # Configurações específicas do EnhancedCodeEditor
        self.highlighting_manager = None
        self.syntax_highlighter = None
       
        self.lsp_manager = None
        self.lsp_completions = []
        self.minimap = None
        
        # Configurar conexões específicas
        self.setup_enhanced_connections()
        
        # Configurar syntax highlighting se houver arquivo
        if file_path and hasattr(parent, 'syntax_highlighting_manager'):
            parent.syntax_highlighting_manager.setup_editor_highlighter(self, file_path)

    def setup_enhanced_connections(self):
        """Configura conexões de sinais específicas do EnhancedCodeEditor"""
        # Conectar sinais para syntax highlighting e indicadores
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.textChanged.connect(self.on_text_changed)
        
        # Conectar sinais para LSP
        self.textChanged.connect(self._on_text_changed_for_lsp)
        self.cursorPositionChanged.connect(self._on_cursor_changed_for_lsp)

   

    def on_text_changed(self):
        """Quando o texto é alterado"""
        self.is_modified = True

    def update_status_info(self):
        """Atualiza informações na barra de status"""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        
        # Encontra o IDE pai para atualizar a statusbar
        parent = self.parent()
        while parent and not hasattr(parent, 'statusBar'):
            parent = parent.parent()
            
        if parent and hasattr(parent, 'cursor_info_label'):
            parent.cursor_info_label.setText(f"Linha: {line}, Coluna: {column}")

    def set_highlighter(self, highlighter):
        """Define o syntax highlighter para este editor"""
        self.syntax_highlighter = highlighter

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

    # ===== MÉTODOS LSP AVANÇADOS =====
    
    def set_lsp_manager(self, lsp_manager):
        """Define o gerenciador LSP"""
        self.lsp_manager = lsp_manager
        
        # Notificar abertura do documento
        if self.file_path and lsp_manager:
            lsp_manager.open_document(self.file_path, self.toPlainText())
    
    def _on_text_changed_for_lsp(self):
        """Notifica mudanças para LSP"""
        if (self.lsp_manager and self.file_path and 
            not self.file_path.endswith('.py')):
            return
            
        content = self.toPlainText()
        if self.lsp_manager and self.file_path:
            self.lsp_manager.update_document(self.file_path, content)
    
    def _on_cursor_changed_for_lsp(self):
        """Processa mudanças do cursor para LSP (hover, etc)"""
        # Implementar hover information se desejado
        pass
    
    def get_lsp_suggestions(self):
        """Obtém sugestões via LSP"""
        if not self.lsp_manager or not self.file_path:
            return []
        
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        
        # Usar callback assíncrono
        def handle_completions(response):
            if response and 'result' in response:
                items = response['result']
                if isinstance(items, list):
                    self.lsp_completions = self._process_lsp_completions(items)
                elif isinstance(items, dict) and 'items' in items:
                    self.lsp_completions = self._process_lsp_completions(items['items'])
        
        self.lsp_manager.get_completions(self.file_path, line, column, handle_completions)
        return self.lsp_completions
    
    def _process_lsp_completions(self, items):
        """Processa itens de completion do LSP"""
        completions = []
        
        for item in items:
            if isinstance(item, dict):
                label = item.get('label', '')
                detail = item.get('detail', '')
                kind = item.get('kind', 0)
                
                # Formatar baseado no tipo
                completion_text = self._format_completion_item(label, detail, kind)
                if completion_text:
                    completions.append(completion_text)
        
        return completions
    
    def _format_completion_item(self, label, detail, kind):
        """Formata item de completion baseado no tipo"""
        # Mapear tipos LSP para representação visual
        kind_map = {
            2: f"🔹 {label}",  # Method
            3: f"🔸 {label}",  # Function  
            4: f"🗂️ {label}",  # Constructor
            5: f"📊 {label}",  # Field
            6: f"📁 {label}",  # Variable
            7: f"🏛️ {label}",  # Class
            8: f"📚 {label}",  # Interface
            9: f"📦 {label}",  # Module
            10: f"🏷️ {label}", # Property
            11: f"🔤 {label}", # Unit
            12: f"💎 {label}", # Value
            13: f"📝 {label}", # Enum
            14: f"🔑 {label}", # Keyword
            15: f"🎨 {label}", # Color
            16: f"📄 {label}", # File
            17: f"🔗 {label}", # Reference
        }
        
        return kind_map.get(kind, label)

    # ===== MÉTODOS MINIMAP =====
    
    def set_minimap(self, minimap):
        """Define o minimap associado a este editor"""
        self.minimap = minimap
        if self.minimap:
            self.minimap.set_main_editor(self)

    # ===== MÉTODOS DE AUTOCOMPLETE MELHORADOS =====
    
    


    def _get_fallback_suggestions(self):
        """Sugestões de fallback mínimas e seguras"""
        return [
            "print", "def", "class", "if", "else", "for", "while", "import", 
            "from", "return", "True", "False", "None", "len", "str", "list", 
            "dict", "range", "type", "isinstance"
        ]

    def get_unified_suggestions(self):
        """Sistema unificado de sugestões - VERSÃO CORRIGIDA"""
        try:
            # Usa o completador do IDE se disponível
            ide = self.get_ide()
            if ide and hasattr(ide, 'completer'):
                code = self.toPlainText()
                cursor_position = self.textCursor().position()
                
                suggestions = ide.completer.get_completions(
                    code, 
                    cursor_position,
                    self.file_path,
                    getattr(ide, 'project_path', "")
                )
                
                if suggestions:
                    return suggestions[:25]  # Limita a 25 sugestões
            
            # Fallback para sistema interno
            return self.get_enhanced_suggestions()
            
        except Exception as e:
            print(f"❌ Erro no unified suggestions: {e}")
            return self._get_fallback_suggestions()



    # ===== MÉTODOS DE FORMATAÇÃO AVANÇADA =====
    
    def format_code(self):
        """Formata o código automaticamente baseado na linguagem"""
        language = self.get_language()
        
        if language == 'python':
            self.format_python_code()
        elif language == 'html':
            self.format_html_code()
        elif language == 'css':
            self.format_css_code()
        elif language == 'javascript':
            self.format_javascript_code()
        else:
            # Formatação genérica
            self.fix_indentation()
            self.clean_trailing_whitespace()
    
    def format_python_code(self):
        """Formata código Python usando autopep8 ou formatação básica"""
        try:
            code = self.toPlainText()
            
            # Tenta usar autopep8 primeiro
            try:
                import autopep8
                formatted_code = autopep8.fix_code(code)
                self.setPlainText(formatted_code)
                return
            except ImportError:
                print("autopep8 não encontrado, usando formatação básica")
            
            # Fallback para formatação básica
            self.fix_indentation()
            self.clean_trailing_whitespace()
            
        except Exception as e:
            print(f"Erro ao formatar código Python: {e}")
            # Fallback absoluto
            self.fix_indentation()
    
    def format_html_code(self):
        """Formata código HTML (placeholder)"""
        self.fix_indentation()
        self.clean_trailing_whitespace()
    
    def format_css_code(self):
        """Formata código CSS (placeholder)"""
        self.fix_indentation()
        self.clean_trailing_whitespace()
    
    def format_javascript_code(self):
        """Formata código JavaScript (placeholder)"""
        self.fix_indentation()
        self.clean_trailing_whitespace()

    def clean_trailing_whitespace(self):
        """Remove espaços em branco no final das linhas"""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        # Itera por todas as linhas
        block = self.document().firstBlock()
        while block.isValid():
            text = block.text()
            stripped = text.rstrip()
            if text != stripped:
                cursor.setPosition(block.position())
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cursor.insertText(stripped)
            block = block.next()
        
        cursor.endEditBlock()

    # ===== MÉTODOS DE NAVEGAÇÃO AVANÇADA =====
    
    def goto_line(self, line_number):
        """Vai para uma linha específica"""
        if line_number < 1:
            return
            
        document = self.document()
        block = document.findBlockByLineNumber(line_number - 1)
        
        if block.isValid():
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)
            self.centerCursor()
    
    def find_next(self, text, case_sensitive=False, whole_word=False):
        """Encontra próxima ocorrência do texto"""
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords
            
        cursor = self.textCursor()
        found = self.document().find(text, cursor, flags)
        
        if not found.isNull():
            self.setTextCursor(found)
            return True
        else:
            # Busca do início
            cursor.setPosition(0)
            found = self.document().find(text, cursor, flags)
            if not found.isNull():
                self.setTextCursor(found)
                return True
        
        return False

    def replace_text(self, find_text, replace_text, replace_all=False):
        """Substitui texto no editor"""
        cursor = self.textCursor()
        
        if replace_all:
            # Substitui todas as ocorrências
            cursor.beginEditBlock()
            cursor.movePosition(QTextCursor.Start)
            
            while True:
                found = self.document().find(find_text, cursor)
                if found.isNull():
                    break
                found.insertText(replace_text)
                cursor = found
            
            cursor.endEditBlock()
        else:
            # Substitui apenas a seleção atual
            if cursor.hasSelection() and cursor.selectedText() == find_text:
                cursor.insertText(replace_text)

    # ===== MÉTODOS DE DIAGNÓSTICO =====
    
    def get_editor_info(self):
        """Retorna informações sobre o editor"""
        return {
            'type': 'EnhancedCodeEditor',
            'file_path': self.file_path,
            'language': self.get_language(),
            'line_count': self.blockCount(),
            'has_lsp': self.lsp_manager is not None,
            'has_minimap': self.minimap is not None,
            'has_syntax_highlighting': self.syntax_highlighter is not None
        }




class EditorTab(QWidget):

    def __init__(self, file_path=None, parent=None):
        super().__init__(parent)
        
        self.file_path = file_path
        self.scope_header = None
        self.setup_editor()
        self.setup_ui()
        self.setup_scope_header()
        self.setup_indicators()
        self.editor.cursorPositionChanged.connect(self.update_scope_indicator)

    # No EditorTab.setup_editor():
    def setup_editor(self):
        self.editor = EnhancedCodeEditor(
            text="",
            cursor_position=0,
            file_path=self.file_path,
            project_path=getattr(self.get_ide(), 'project_path', ''),
            parent=self
        )
            
        # Configurações básicas do editor
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setTabStopDistance(40)  # 4 espaços equivalente
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Configurar highlight de sintaxe
        if self.file_path and self.file_path.endswith('.py'):
            self.highlighter = PythonHighlighter(self.editor.document())
        
        # Carregar conteúdo do arquivo se existir
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
        # Destacar linha atual de forma mais visível
        palette = self.editor.palette()
        palette.setColor(QPalette.Highlight, QColor("#569cd6"))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.editor.setPalette(palette)
        
        # Conectar sinais para indicadores em tempo real
        self.editor.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.editor.textChanged.connect(self.on_text_changed)

    def setup_linting(self):
        """Configura o sistema de linting"""
        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.timeout.connect(self.start_linting)
        self.is_linting = False
        self.pending_lint = False
        self.linter_worker = None
        self.last_lint_content = self.editor.toPlainText()

        # Conectar sinal de texto alterado para linting
        self.editor.textChanged.connect(self.schedule_linting)
    def update_scope_header(self, current_class, current_function):
        """Atualiza o header de escopo de forma inteligente"""
        if not self.scope_header:
            return
            
        # Sempre atualiza os dados
        self.scope_header.update_scope(current_class, current_function)
        
        # Mostra/oculta baseado na relevância
        if current_class != "Global" or current_function != "Nenhuma":
            self.scope_header.show_scope()
        else:
            self.scope_header.hide_scope()
    def on_cursor_position_changed(self):
        """Chamado quando o cursor se move - ATUALIZADO"""
        try:
            cursor = self.editor.textCursor()
            line = cursor.blockNumber() + 1
            
            # Atualiza informações de escopo
            current_class = self.find_current_class(line)
            current_function = self.find_current_function(line)
            
            # Atualiza header de escopo
            self.update_scope_header(current_class, current_function)
            
            # Remove a chamada problemática
            # self.update_scope_indicator()  # REMOVER ESTA LINHA
            
        except Exception as e:
            print(f"Erro na mudança de cursor: {e}")

            

    def update_line_column_info(self, line, column):
        """Atualiza informações de linha e coluna"""
        ide = self.get_ide()
        if ide and hasattr(ide, 'cursor_info_label'):
            ide.cursor_info_label.setText(f"Linha: {line}, Coluna: {column}")
        
    def on_text_changed(self):
        """Quando texto é modificado - VERSÃO MAIS SENSÍVEL"""
        self.is_modified = True
        
        # Dispara autocomplete mais rapidamente para letras únicas
        current_char = self.get_char_before_cursor()
        if current_char.isalpha() and len(current_char) == 1:
            self.autocomplete_timer.start(100)  # Reduzido para 100ms
        elif current_char in ['.', '_'] or current_char.isalnum():
            self.autocomplete_timer.start(300)

    def setup_scope_header(self):
        """Configura o header flutuante de escopo"""
        self.scope_header = ScopeHeaderWidget(self)
        
        # Posiciona no topo do editor
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.scope_header)
        
        # Layout principal que inclui header e editor
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.editor)
        
        self.setLayout(main_layout)
        
        # Inicialmente oculto - só mostra quando relevante
        self.scope_header.hide()
    def setup_scope_indicator(self):
        """Configura o indicador de escopo"""
        self.scope_indicator = ScopeIndicatorWidget()
        
        # Adiciona ao layout do editor
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scope_indicator)
        main_layout.addWidget(self.editor)
        
        # Substitui o layout atual
        if self.layout():
            QWidget().setLayout(self.layout())
        self.setLayout(main_layout)       

    def find_current_class(self, current_line):
        """Encontra a classe atual baseada na posição do cursor"""
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
                    get_unified_suggestions
        return current_class

    def find_current_function(self, current_line):
        """Encontra a função atual baseada na posição do cursor"""
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


    def setup_navigation_panel(self):
        """Configura painel de navegação lateral"""
        # Criar um widget lateral com a estrutura do código
        self.nav_panel = QListWidget()
        self.nav_panel.itemClicked.connect(self.navigate_to_item)
        
        # Layout principal
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.nav_panel, 1)
        main_layout.addWidget(self.editor, 4)
        
        # Aplicar layout
        if self.layout():
            # Se já tem layout, limpar e adicionar novo
            QWidget().setLayout(self.layout())
        self.setLayout(main_layout)
        
        # Atualizar painel inicialmente
        self.update_navigation_panel()

    def update_navigation_panel(self):
        """Atualiza o painel de navegação com a estrutura do código"""
        if not hasattr(self, 'nav_panel'):
            return
            
        self.nav_panel.clear()
        text = self.editor.toPlainText()
        
        for i, line in enumerate(text.split('\n')):
            line = line.strip()
            if line.startswith('class '):
                class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                item = QListWidgetItem(f"📦 {class_name}")
                item.setData(Qt.UserRole, i)
                self.nav_panel.addItem(item)
            elif line.startswith('def '):
                func_name = line.split('def ')[1].split('(')[0].strip()
                item = QListWidgetItem(f"  📋 {func_name}")
                item.setData(Qt.UserRole, i)
                self.nav_panel.addItem(item)

    def navigate_to_item(self, item):
        """Navega para o item clicado no painel de navegação"""
        line_number = item.data(Qt.UserRole)
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.Down)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def highlight_current_scope(self, current_line):
        """Destaca o escopo atual (classe/função) - implementação simplificada"""
        # Em QPlainTextEdit, podemos usar seleção temporária
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        
        # Apenas para demonstração - em produção você implementaria
        # um sistema mais sofisticado de highlight
        pass

    def find_current_scope(self, current_line):
        """Encontra o escopo atual baseado na indentação"""
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        if current_line > len(lines):
            return None, None
            
        # Encontrar linha de início do escopo (class/def)
        start_line = current_line - 1
        for i in range(current_line - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith(('class ', 'def ')) and not line.startswith('#'):
                start_line = i
                break
        
        # Encontrar fim do escopo baseado na indentação
        if start_line < len(lines):
            start_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
            end_line = start_line
            
            for i in range(start_line + 1, len(lines)):
                line = lines[i]
                if line.strip():  # Linha não vazia
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= start_indent and not line.strip().startswith('#'):
                        break
                end_line = i
                
            return start_line, end_line
            
        return None, None

    # ===== MÉTODOS DE LINTING =====
    
    def schedule_linting(self):
        """Schedule linting com debounce melhorado"""
        current_content = self.editor.toPlainText()

        if (current_content != self.last_lint_content and
                self.file_path and
                self.file_path.endswith('.py')):

            if self.is_linting:
                self.pending_lint = True
            else:
                self.lint_timer.start(2000)

    def start_linting(self):
        """Start linting com controle de estado"""
        if self.is_linting:
            return

        self.is_linting = True

        ide = self.get_ide()
        if not ide:
            return

        # Stop previous worker if running
        if self.linter_worker and self.linter_worker.isRunning():
            self.linter_worker.stop()

        # Save file and update last content
        try:
            current_content = self.editor.toPlainText()
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
            self.last_lint_content = current_content
        except Exception:
            return

        # Start new worker
        self.linter_worker = LinterWorker(
            self.file_path,
            ide.get_python_executable(),
            ide.project_path
        )
        self.linter_worker.finished.connect(self.on_linting_finished)
        self.linter_worker.start()

    def on_linting_finished(self, errors, lint_messages):
        """Finaliza linting e verifica se precisa relintar"""
        self.is_linting = False

        if self.pending_lint:
            self.pending_lint = False
            self.schedule_linting()

        # Aplicar erros (implementação simplificada)
        print(f"Linting finished: {len(lint_messages)} messages")

        # Update problems list no IDE pai
        ide = self.get_ide()
        if ide and hasattr(ide, 'problems_list'):
            ide.problems_list.clear()
            for msg in lint_messages:
                item = QListWidgetItem(msg)
                ide.problems_list.addItem(item)

    def get_ide(self):
        """Find and return the parent IDE instance"""
        parent = self.parent()
        while parent and not hasattr(parent, 'project_path'):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent

    # ===== MÉTODOS DE ARQUIVO =====
    
    def save_file(self):
        """Salva o arquivo"""
        if not self.file_path:
            return self.save_file_as()
            
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.last_lint_content = self.editor.toPlainText()
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
            getattr(ide, 'project_path', '') or QDir.homePath(),
            "Todos os Arquivos (*.*)"
        )
        
        if new_path:
            self.file_path = new_path
            result = self.save_file()
            
            if result and ide:
                self.update_tab_title()
            return result
            
        return False
        
    def update_tab_title(self):
        """Atualiza o título da aba"""
        ide = self.get_ide()
        if not ide or not hasattr(ide, 'tab_widget'):
            return
            
        index = ide.tab_widget.indexOf(self)
        if index >= 0:
            base_name = os.path.basename(self.file_path) if self.file_path else "Novo Arquivo"
            ide.tab_widget.setTabText(index, base_name)
            
    def is_modified(self):
        """Verifica se o arquivo foi modificado"""
        current_content = self.editor.toPlainText()
        return current_content != self.last_lint_content
        
    def get_content(self):
        """Retorna o conteúdo do editor"""
        return self.editor.toPlainText()
        
    def set_content(self, content):
        """Define o conteúdo do editor"""
        self.editor.setPlainText(content)

    def get_current_editor(self):
        """Retorna o editor deste tab"""
        return self.editor



