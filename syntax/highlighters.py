from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PySide6.QtCore import QRegExp


class SimplePythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter simplificado para Python"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Paleta de cores básica
        self.colors = {
            'keyword': QColor("#569CD6"),
            'string': QColor("#CE9178"), 
            'comment': QColor("#6A9955"),
            'number': QColor("#B5CEA8"),
            'function': QColor("#DCDCAA"),
            'class': QColor("#4EC9B0")
        }
        
        self.highlighting_rules = []
        self.setup_rules()
    
    def setup_rules(self):
        """Configura regras básicas de syntax highlighting"""
        
        # Palavras-chave Python
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors['keyword'])
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
            "try", "while", "with", "yield"
        ]
        
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors['string'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format)
        )
        
        # Comentários
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors['comment'])
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(
            (QRegularExpression(r'#.*'), comment_format)
        )
        
        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors['number'])
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format)
        )
    
    def highlightBlock(self, text):
        """Aplica o syntax highlighting ao bloco de texto"""
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)



class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter para Python"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Paleta de cores estilo PyCharm
        self.colors = {
            'keyword': QColor("#CC7832"),      # Laranja
            'string': QColor("#6A8759"),       # Verde escuro
            'comment': QColor("#808080"),      # Cinza
            'number': QColor("#6897BB"),       # Azul claro
            'function': QColor("#FFC66D"),     # Amarelo
            'class': QColor("#FFC66D"),        # Amarelo
            'builtin': QColor("#CC7832"),      # Laranja
            'self': QColor("#94558D"),         # Roxo
            'decorator': QColor("#BBB529"),    # Amarelo esverdeado
        }
        
        self.highlighting_rules = []
        self.setup_rules()
    
    def setup_rules(self):
        """Configura as regras de syntax highlighting"""
        
        # Palavras-chave Python
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors['keyword'])
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
            "try", "while", "with", "yield"
        ]
        
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Funções e classes
        function_format = QTextCharFormat()
        function_format.setForeground(self.colors['function'])
        function_format.setFontWeight(QFont.Bold)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)'), function_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)'), function_format)
        )
        
        # Chamadas de função
        call_format = QTextCharFormat()
        call_format.setForeground(self.colors['function'])
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[A-Za-z_][a-zA-Z0-9_]*\s*(?=\()'), call_format)
        )
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors['string'])
        
        # Strings simples
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format)
        )
        
        # Strings multi-linha
        self.highlighting_rules.append(
            (QRegularExpression(r'"""(?!"").*?"""', QRegularExpression.DotMatchesEverythingOption), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'''(?!'').*?'''", QRegularExpression.DotMatchesEverythingOption), string_format)
        )
        
        # Comentários
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors['comment'])
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(
            (QRegularExpression(r'#.*'), comment_format)
        )
        
        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors['number'])
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'\b0[xX][0-9a-fA-F]+\b'), number_format)
        )
        
        # Self/cls
        self_format = QTextCharFormat()
        self_format.setForeground(self.colors['self'])
        self.highlighting_rules.append(
            (QRegularExpression(r'\b(self|cls)\b'), self_format)
        )
        
        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(self.colors['decorator'])
        self.highlighting_rules.append(
            (QRegularExpression(r'@[a-zA-Z_][a-zA-Z0-9_]*'), decorator_format)
        )
    
    def highlightBlock(self, text):
        """Aplica o syntax highlighting ao bloco de texto"""
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class AdvancedSyntaxHighlighter(QSyntaxHighlighter):
    """Sistema avançado de syntax highlighting para múltiplas linguagens"""
    
    def __init__(self, document, language="python"):
        super().__init__(document)
        self.language = language
        self.highlighting_rules = []
        self.setup_theme()
        self.setup_rules()
        
    def setup_theme(self):
        """Configura o tema de cores para syntax highlighting"""
        self.colors = {
            # Cores baseadas no tema Dark Professional
            'keyword': QColor("#569CD6"),      # Azul - palavras-chave
            'string': QColor("#CE9178"),       # Laranja claro - strings
            'comment': QColor("#6A9955"),      # Verde - comentários
            'number': QColor("#B5CEA8"),       # Verde claro - números
            'function': QColor("#DCDCAA"),     # Amarelo - funções
            'class': QColor("#4EC9B0"),        # Ciano - classes
            'builtin': QColor("#4FC1FF"),      # Azul claro - built-ins
            'decorator': QColor("#BBB529"),    # Amarelo esverdeado - decorators
            'operator': QColor("#D4D4D4"),     # Cinza claro - operadores
            'error': QColor("#F44747"),        # Vermelho - erros
            'warning': QColor("#FFCC66"),      # Laranja - avisos
            'type': QColor("#4EC9B0"),         # Ciano - tipos
            'constant': QColor("#569CD6"),     # Azul - constantes
            'attribute': QColor("#9CDCFE"),    # Azul claro - atributos
            'parameter': QColor("#9CDCFE"),    # Azul claro - parâmetros
            'docstring': QColor("#6A9955"),    # Verde - docstrings
        }
        
    def setup_rules(self):
        """Configura regras de highlighting baseadas na linguagem"""
        if self.language == "python":
            self.setup_python_rules()
        elif self.language == "javascript":
            self.setup_javascript_rules()
        elif self.language == "html":
            self.setup_html_rules()
        elif self.language == "css":
            self.setup_css_rules()
        elif self.language == "json":
            self.setup_json_rules()
        else:
            self.setup_generic_rules()
    
    def setup_python_rules(self):
        """Regras específicas para Python"""
        
        # Palavras-chave Python
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors['keyword'])
        keyword_format.setFontWeight(QFont.Bold)
        
        python_keywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
            "try", "while", "with", "yield"
        ]
        
        for keyword in python_keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Funções built-in
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(self.colors['builtin'])
        
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
        
        for builtin in builtins:
            pattern = QRegularExpression(r'\b' + builtin + r'\b')
            self.highlighting_rules.append((pattern, builtin_format))
        
        # Definições de função
        function_format = QTextCharFormat()
        function_format.setForeground(self.colors['function'])
        function_format.setFontWeight(QFont.Bold)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)'), function_format)
        )
        
        # Definições de classe
        class_format = QTextCharFormat()
        class_format.setForeground(self.colors['class'])
        class_format.setFontWeight(QFont.Bold)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)'), class_format)
        )
        
        # Chamadas de função
        call_format = QTextCharFormat()
        call_format.setForeground(self.colors['function'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()'), call_format)
        )
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors['string'])
        
        # Strings simples
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format)
        )
        
        # f-strings
        fstring_format = QTextCharFormat()
        fstring_format.setForeground(QColor("#D7BA7D"))
        self.highlighting_rules.append(
            (QRegularExpression(r'f"[^"]*"'), fstring_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"f'[^']*'"), fstring_format)
        )
        
        # Docstrings
        docstring_format = QTextCharFormat()
        docstring_format.setForeground(self.colors['docstring'])
        docstring_format.setFontItalic(True)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"""(?!"").*?"""', QRegularExpression.DotMatchesEverythingOption), docstring_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'''(?!'').*?'''", QRegularExpression.DotMatchesEverythingOption), docstring_format)
        )
        
        # Comentários
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors['comment'])
        comment_format.setFontItalic(True)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'#.*'), comment_format)
        )
        
        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors['number'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\b'), number_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.[0-9]+\b'), number_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'\b0[xX][0-9a-fA-F]+\b'), number_format)
        )
        
        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(self.colors['decorator'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'@[a-zA-Z_][a-zA-Z0-9_\.]*'), decorator_format)
        )
        
        # Self/cls
        self_format = QTextCharFormat()
        self_format.setForeground(self.colors['parameter'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\b(self|cls)\b'), self_format)
        )
        
        # Operadores
        operator_format = QTextCharFormat()
        operator_format.setForeground(self.colors['operator'])
        
        operators = [
            r'=', r'==', r'!=', r'<', r'<=', r'>', r'>=', r'\+', r'-', r'\*',
            r'/', r'//', r'%', r'\*\*', r'\+=', r'-=', r'\*=', r'/=', r'%=',
            r'\^', r'\|', r'&', r'~', r'>>', r'<<'
        ]
        
        for op in operators:
            pattern = QRegularExpression(op)
            self.highlighting_rules.append((pattern, operator_format))
    
    def setup_javascript_rules(self):
        """Regras específicas para JavaScript"""
        # Palavras-chave JavaScript
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors['keyword'])
        keyword_format.setFontWeight(QFont.Bold)
        
        js_keywords = [
            "break", "case", "catch", "class", "const", "continue", "debugger",
            "default", "delete", "do", "else", "export", "extends", "finally",
            "for", "function", "if", "import", "in", "instanceof", "new",
            "return", "super", "switch", "this", "throw", "try", "typeof",
            "var", "void", "while", "with", "yield", "await", "enum", "implements",
            "interface", "let", "package", "private", "protected", "public", "static"
        ]
        
        for keyword in js_keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Strings e comentários (similar ao Python)
        self.setup_common_rules()
    
    def setup_html_rules(self):
        """Regras específicas para HTML"""
        # Tags HTML
        tag_format = QTextCharFormat()
        tag_format.setForeground(self.colors['keyword'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'</?[a-zA-Z][^>]*>'), tag_format)
        )
        
        # Atributos
        attribute_format = QTextCharFormat()
        attribute_format.setForeground(self.colors['attribute'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[a-zA-Z-]+(?=\=)'), attribute_format)
        )
        
        # Strings e comentários
        self.setup_common_rules()
    
    def setup_css_rules(self):
        """Regras específicas para CSS"""
        # Propriedades CSS
        property_format = QTextCharFormat()
        property_format.setForeground(self.colors['attribute'])
        
        css_properties = [
            "color", "background", "font", "margin", "padding", "border",
            "width", "height", "display", "position", "float", "clear"
        ]
        
        for prop in css_properties:
            pattern = QRegularExpression(r'\b' + prop + r'\b')
            self.highlighting_rules.append((pattern, property_format))
        
        # Strings e comentários
        self.setup_common_rules()
    
    def setup_json_rules(self):
        """Regras específicas para JSON"""
        # Chaves JSON
        key_format = QTextCharFormat()
        key_format.setForeground(self.colors['attribute'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"(?=\s*:)'), key_format)
        )
        
        # Strings e números
        self.setup_common_rules()
    
    def setup_common_rules(self):
        """Regras comuns para todas as linguagens"""
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors['string'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"'), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^']*'"), string_format)
        )
        
        # Comentários de linha
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors['comment'])
        comment_format.setFontItalic(True)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'//.*'), comment_format)
        )
        
        # Comentários de bloco
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), comment_format)
        )
        
        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors['number'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\b'), number_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.[0-9]+\b'), number_format)
        )
    
    def setup_generic_rules(self):
        """Regras genéricas para linguagens não específicas"""
        self.setup_common_rules()
    
    def highlightBlock(self, text):
        """Aplica o syntax highlighting ao bloco de texto"""
        # Aplica todas as regras de highlighting
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        
        # Destaque de parênteses/colchetes/chaves correspondentes
        self.highlight_matching_brackets(text)
    
    def highlight_matching_brackets(self, text):
        """Destaca pares de parênteses/colchetes/chaves correspondentes - CORRIGIDO"""
        try:
            # Método simplificado e seguro
            brackets = [
                ('(', ')'), ('[', ']'), ('{', '}')
            ]
            
            # Apenas destaca brackets básicos sem lógica complexa de cursor
            bracket_format = QTextCharFormat()
            bracket_format.setBackground(QColor(86, 156, 214, 80))
            bracket_format.setForeground(QColor(255, 255, 255))
            
            for open_bracket, close_bracket in brackets:
                # Destaca brackets abertos
                open_pos = 0
                while open_pos < len(text):
                    open_pos = text.find(open_bracket, open_pos)
                    if open_pos == -1:
                        break
                    self.setFormat(open_pos, 1, bracket_format)
                    open_pos += 1
                
                # Destaca brackets fechados
                close_pos = 0
                while close_pos < len(text):
                    close_pos = text.find(close_bracket, close_pos)
                    if close_pos == -1:
                        break
                    self.setFormat(close_pos, 1, bracket_format)
                    close_pos += 1
                    
        except Exception as e:
            # Ignora erros no highlight de brackets
            pass
    
    def highlight_matching_bracket(self, bracket, matching_bracket, position, text):
        """Destaca um bracket e seu correspondente"""
        bracket_format = QTextCharFormat()
        bracket_format.setBackground(QColor(86, 156, 214, 80))  # Azul translúcido
        bracket_format.setForeground(QColor(255, 255, 255))
        
        # Destaca o bracket atual
        self.setFormat(position, 1, bracket_format)
        
        # Encontra e destaca o bracket correspondente
        if bracket in ['(', '[', '{']:
            # Busca para frente
            count = 1
            for i in range(position + 1, len(text)):
                if text[i] == bracket:
                    count += 1
                elif text[i] == matching_bracket:
                    count -= 1
                    if count == 0:
                        self.setFormat(i, 1, bracket_format)
                        break
        else:
            # Busca para trás
            count = 1
            for i in range(position - 1, -1, -1):
                if text[i] == bracket:
                    count += 1
                elif text[i] == matching_bracket:
                    count -= 1
                    if count == 0:
                        self.setFormat(i, 1, bracket_format)
                        break



class MultiLanguageHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_config = LanguageConfig()
        self.current_language = 'Text'
        self.highlighting_rules = []
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6a9955"))
        self.error_format = QTextCharFormat()
        self.error_format.setBackground(QColor(255, 0, 0, 128))
        self.warning_format = QTextCharFormat()
        self.warning_format.setBackground(
            QColor(255, 255, 0, 128))

    def setup_python_rules_pycharm_style(self):
        """Configura regras de highlight no estilo PyCharm"""

        # Paleta de cores PyCharm-like
        colors = {
            'keyword': '#CC7832',  # Laranja
            'string': '#6A8759',  # Verde escuro
            'comment': '#808080',  # Cinza
            'number': '#6897BB',  # Azul claro
            'function': '#FFC66D',  # Amarelo
            'class': '#FFC66D',  # Amarelo
            'builtin': '#CC7832',  # Laranja
            'self': '#94558D',  # Roxo
            'decorator': '#BBB529',  # Amarelo esverdeado
        }

        # Keywords (mais visíveis)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(colors['keyword']))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
            "try", "while", "with", "yield"
        ]

        for word in keywords:
            pattern = QRegularExpression(
                r'\b' + word + r'\b')
            self.highlighting_rules.append(
                (pattern, keyword_format))

        # Funções (mais destacadas)
        function_format = QTextCharFormat()
        function_format.setForeground(
            QColor(colors['function']))
        function_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)'), function_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)'), function_format))

        # Chamadas de função
        call_format = QTextCharFormat()
        call_format.setForeground(QColor(colors['function']))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[A-Za-z_][a-zA-Z0-9_]*\s*(?=\()'), call_format))

        # Strings (mais legíveis)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(colors['string']))
        self.highlighting_rules.append(
            (QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'.*?'"), string_format))

        # Strings multi-linha
        self.highlighting_rules.append(
            (QRegularExpression(r'"""(?!"").*?"""', QRegularExpression.DotMatchesEverythingOption), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'''(?!'').*?'''", QRegularExpression.DotMatchesEverythingOption), string_format))

        # Comentários (mais suaves)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(colors['comment']))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(
            (QRegularExpression(r'#.*'), comment_format))

        # Números (mais destacados)
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(colors['number']))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b0[xX][0-9a-fA-F]+\b'), number_format))

        # Self/cls (destaque especial)
        self_format = QTextCharFormat()
        self_format.setForeground(QColor(colors['self']))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b(self|cls)\b'), self_format))

        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(
            QColor(colors['decorator']))
        self.highlighting_rules.append(
            (QRegularExpression(r'@[a-zA-Z_][a-zA-Z0-9_]*'), decorator_format))

    def set_language(self, file_path):
        self.current_language = self.language_config.get_language_from_extension(
            file_path)
        self.setup_highlighting_rules()


    def setup_highlighting_rules(self):
        self.highlighting_rules = []
        if self.current_language == 'Python':
            self.setup_python_rules()
        elif self.current_language == 'JavaScript':
            self.setup_javascript_rules()
        elif self.current_language == 'HTML':
            self.setup_html_rules()
        elif self.current_language == 'CSS':
            self.setup_css_rules()
        elif self.current_language == 'JSON':
            self.setup_json_rules()
        elif self.current_language == 'SQL':
            self.setup_sql_rules()
        elif self.current_language == 'Java':
            self.setup_java_rules()
        elif self.current_language == 'C++' or self.current_language == 'C':
            self.setup_cpp_rules()
        elif self.current_language == 'C#':
            self.setup_csharp_rules()
        elif self.current_language == 'PHP':
            self.setup_php_rules()
        elif self.current_language == 'Ruby':
            self.setup_ruby_rules()
        elif self.current_language == 'Go':
            self.setup_go_rules()
        elif self.current_language == 'Rust':
            self.setup_rust_rules()
        elif self.current_language == 'Swift':
            self.setup_swift_rules()
        elif self.current_language == 'Kotlin':
            self.setup_kotlin_rules()
        elif self.current_language == 'XML':
            self.setup_xml_rules()
        elif self.current_language == 'Markdown':
            self.setup_markdown_rules()
        elif self.current_language == 'YAML':
            self.setup_yaml_rules()
        else:
            self.setup_basic_rules()

    def setup_python_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "if", "else", "elif", "for", "while", "break", "continue", "pass", "return",
            "try", "except", "finally", "raise", "def", "class", "lambda", "global",
            "nonlocal", "import", "from", "as", "and", "or", "not", "in", "is",
            "True", "False", "None"
        ]
        for word in keywords:
            pattern = QRegularExpression(
                r'\b' + word + r'\b')
            self.highlighting_rules.append(
                (pattern, keyword_format))

        # Built-in functions
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#4ec9b0"))
        builtins = [
            "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes", "callable",
            "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod",
            "enumerate", "eval", "exec", "filter", "float", "format", "frozenset", "getattr",
            "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
            "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min",
            "next", "object", "oct", "open", "ord", "pow", "print", "property", "range",
            "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod",
            "str", "sum", "super", "tuple", "type", "vars", "zip", "__import__"
        ]
        for builtin in builtins:
            pattern = QRegularExpression(
                r'\b' + builtin + r'\b')
            self.highlighting_rules.append(
                (pattern, builtin_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\bdef\s+[a-zA-Z_][a-zA-Z0-9_]*'), function_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[A-Za-z_][a-zA-Z0-9_]*\s*(?=\()'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append(
            (QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'.*?'"), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'"""(?!"").*?"""', QRegularExpression.DotMatchesEverythingOption), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'''(?!'').*?'''", QRegularExpression.DotMatchesEverythingOption), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'(f|r)?".*?"'), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'(f|r)?\'.*?\''), string_format))

        # Comments
        self.highlighting_rules.append(
            (QRegularExpression(r'#.*'), self.comment_format))
        docstring_format = QTextCharFormat()
        docstring_format.setForeground(QColor("#808080"))
        self.highlighting_rules.append(
            (QRegularExpression(r'"""[^"]*"""'), docstring_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'''[^']*'''"), docstring_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b0[xX][0-9a-fA-F]+\b'), number_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b0[bB][01]+\b'), number_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b0[oO][0-7]+\b'), number_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+j\b'), number_format))

        # Self and cls
        self_format = QTextCharFormat()
        self_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b(self|cls)\b'), self_format))

    # Implementações para outras linguagens (abreviadas para brevidade, mas
    # completas na versão final)
    def setup_javascript_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "function", "var", "let", "const", "if", "else", "for", "while",
            "do", "switch", "case", "break", "continue", "return", "try",
            "catch", "finally", "throw", "new", "delete", "typeof", "instanceof",
            "this", "true", "false", "null", "undefined", "async", "await", "export", "import"
        ]
        for word in keywords:
            pattern = QRegularExpression(
                r'\b' + word + r'\b')
            self.highlighting_rules.append(
                (pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append(
            (QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'.*?'"), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'`.*?`', QRegularExpression.DotMatchesEverythingOption), string_format))

        # Comments
        self.highlighting_rules.append(
            (QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_html_rules(self):
        # Tags
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#569cd6"))
        self.highlighting_rules.append(
            (QRegularExpression(r'</?[a-zA-Z][^>]*>'), tag_format))

        # Attributes
        attribute_format = QTextCharFormat()
        attribute_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[a-zA-Z-]+(?=\=)'), attribute_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^']*'"), string_format))

        # Comments
        self.highlighting_rules.append(
            (QRegularExpression(r'<!--.*?-->', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

    def setup_css_rules(self):
        # Properties
        property_format = QTextCharFormat()
        property_format.setForeground(QColor("#9cdcfe"))
        properties = [
            "color", "background", "font", "margin", "padding", "border",
            "width", "height", "display", "position", "float", "clear", "text-align",
            "font-size", "font-family", "line-height", "z-index", "opacity"
        ]
        for prop in properties:
            pattern = QRegularExpression(
                r'\b' + prop + r'\b')
            self.highlighting_rules.append(
                (pattern, property_format))

        # Selectors
        selector_format = QTextCharFormat()
        selector_format.setForeground(QColor("#d7ba7d"))
        self.highlighting_rules.append(
            (QRegularExpression(r'[.#]?[a-zA-Z][^{]*{'), selector_format))

        # Values
        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append(
            (QRegularExpression(r':[^;]*;'), value_format))

        # Comments
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

    def setup_json_rules(self):
        # Keys
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"(?=\s*:)'), key_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"'), string_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b(true|false|null)\b'), keyword_format))

    def setup_sql_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE",
            "ALTER", "DROP", "TABLE", "DATABASE", "INDEX", "VIEW", "JOIN",
            "INNER", "LEFT", "RIGHT", "OUTER", "ON", "AND", "OR", "NOT",
            "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET", "VALUES",
            "SET", "INTO", "AS", "IS", "NULL", "LIKE", "IN", "BETWEEN", "UNION"
        ]
        for word in keywords:
            pattern = QRegularExpression(
                r'\b' + word + r'\b', QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append(
                (pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        functions = [
            "COUNT",
            "SUM",
            "AVG",
            "MAX",
            "MIN",
            "UPPER",
            "LOWER",
            "CONCAT",
            "SUBSTRING"]
        for func in functions:
            pattern = QRegularExpression(
                r'\b' + func + r'\b', QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append(
                (pattern, function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append(
            (QRegularExpression(r"'.*?'"), string_format))

        # Comments
        self.highlighting_rules.append(
            (QRegularExpression(r'--.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

    # Adicione as outras setups de forma similar... (setup_java_rules,
    # setup_cpp_rules, etc.) para completar

    def setup_basic_rules(self):
        # Strings básicas para linguagens não específicas
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^']*'"), string_format))

        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(
                    match.capturedStart(), match.capturedLength(), format)

        # Aplica highlights de erro/aviso
        data = self.currentBlockUserData()
        if isinstance(data, ErrorData) and data.errors:
            for error in data.errors:
                if error['type'] == 'error':
                    self.setFormat(
                        0, len(text), self.error_format)
                elif error['type'] == 'warning':
                    self.setFormat(
                        0, len(text), self.warning_format)

