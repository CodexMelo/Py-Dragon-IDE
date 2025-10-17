from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont



class BaseHighlighter(QSyntaxHighlighter):
    """Classe base para todos os highlighters"""
    
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        self.setup_theme()
        self.setup_rules()
    
    def setup_theme(self):
        """Configura o tema de cores padrão"""
        self.colors = {
            'keyword': QColor("#569CD6"),
            'string': QColor("#CE9178"),
            'comment': QColor("#6A9955"),
            'number': QColor("#B5CEA8"),
            'function': QColor("#DCDCAA"),
            'class': QColor("#4EC9B0"),
            'builtin': QColor("#4FC1FF"),
            'decorator': QColor("#BBB529"),
            'operator': QColor("#D4D4D4"),
            'type': QColor("#4EC9B0"),
            'constant': QColor("#569CD6"),
            'attribute': QColor("#9CDCFE"),
            'parameter': QColor("#9CDCFE"),
        }
    
    def setup_rules(self):
        """Método abstrato - deve ser implementado pelas subclasses"""
        raise NotImplementedError("Subclasses devem implementar setup_rules()")
    
    def highlightBlock(self, text):
        """Aplica o syntax highlighting ao bloco de texto"""
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class PythonHighlighter(BaseHighlighter):
    """Syntax Highlighter dedicado para Python"""
    
    def setup_rules(self):
        self.setup_python_rules()
    
    def setup_python_rules(self):
        """Configura regras específicas para Python"""
        
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
            pattern = QRegularExpression(f"\\b{keyword}\\b")
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
            pattern = QRegularExpression(f"\\b{builtin}\\b")
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
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors['string'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format)
        )
        
        # Docstrings
        docstring_format = QTextCharFormat()
        docstring_format.setForeground(self.colors['comment'])
        docstring_format.setFontItalic(True)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'""".*?"""', QRegularExpression.DotMatchesEverythingOption), docstring_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'''.*?'''", QRegularExpression.DotMatchesEverythingOption), docstring_format)
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


class JavaScriptHighlighter(BaseHighlighter):
    """Syntax Highlighter dedicado para JavaScript"""
    
    def setup_rules(self):
        self.setup_javascript_rules()
    
    def setup_javascript_rules(self):
        """Configura regras específicas para JavaScript"""
        
        # Palavras-chave JavaScript
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors['keyword'])
        keyword_format.setFontWeight(QFont.Bold)
        
        js_keywords = [
            "break", "case", "catch", "class", "const", "continue", "debugger",
            "default", "delete", "do", "else", "export", "extends", "finally",
            "for", "function", "if", "import", "in", "instanceof", "new",
            "return", "super", "switch", "this", "throw", "try", "typeof",
            "var", "void", "while", "with", "yield", "await", "let", "static"
        ]
        
        for keyword in js_keywords:
            pattern = QRegularExpression(f"\\b{keyword}\\b")
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Funções
        function_format = QTextCharFormat()
        function_format.setForeground(self.colors['function'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\bfunction\s+([a-zA-Z_][a-zA-Z0-9_]*)'), function_format)
        )
        
        # Classes
        class_format = QTextCharFormat()
        class_format.setForeground(self.colors['class'])
        class_format.setFontWeight(QFont.Bold)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)'), class_format)
        )
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors['string'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'`[^`\\]*(\\.[^`\\]*)*`'), string_format)
        )
        
        # Comentários
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors['comment'])
        comment_format.setFontItalic(True)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'//.*'), comment_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), comment_format)
        )
        
        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors['number'])
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\b'), number_format)
        )


class HTMLHighlighter(BaseHighlighter):
    """Syntax Highlighter dedicado para HTML"""
    
    def setup_rules(self):
        self.setup_html_rules()
    
    def setup_html_rules(self):
        """Configura regras específicas para HTML"""
        
        # Tags HTML
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#569CD6"))
        tag_format.setFontWeight(QFont.Bold)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'</?[a-zA-Z][^>]*>'), tag_format)
        )
        
        # Atributos
        attribute_format = QTextCharFormat()
        attribute_format.setForeground(QColor("#9CDCFE"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[a-zA-Z-]+(?=\=)'), attribute_format)
        )
        
        # Strings (valores de atributos)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"'), string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'[^']*'"), string_format)
        )
        
        # Comentários HTML
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'<!--.*?-->', QRegularExpression.DotMatchesEverythingOption), comment_format)
        )


class CSSHighlighter(BaseHighlighter):
    """Syntax Highlighter dedicado para CSS"""
    
    def setup_rules(self):
        self.setup_css_rules()
    
    def setup_css_rules(self):
        """Configura regras específicas para CSS"""
        
        # Propriedades CSS
        property_format = QTextCharFormat()
        property_format.setForeground(QColor("#9CDCFE"))
        
        css_properties = [
            "color", "background", "font", "margin", "padding", "border",
            "width", "height", "display", "position", "float", "clear",
            "text-align", "font-size", "font-family", "line-height"
        ]
        
        for prop in css_properties:
            pattern = QRegularExpression(f"\\b{prop}\\b")
            self.highlighting_rules.append((pattern, property_format))
        
        # Seletores
        selector_format = QTextCharFormat()
        selector_format.setForeground(QColor("#D7BA7D"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r'[.#]?[a-zA-Z-][^{]*\{'), selector_format)
        )
        
        # Valores
        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#CE9178"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r':[^;]*;'), value_format)
        )
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"'), string_format)
        )
        
        # Comentários
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)
        
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), comment_format)
        )


class JSONHighlighter(BaseHighlighter):
    """Syntax Highlighter dedicado para JSON"""
    
    def setup_rules(self):
        self.setup_json_rules()
    
    def setup_json_rules(self):
        """Configura regras específicas para JSON"""
        
        # Chaves
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#9CDCFE"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"(?=\s*:)'), key_format)
        )
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"'), string_format)
        )
        
        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\b'), number_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[0-9]+\.[0-9]+\b'), number_format)
        )
        
        # Palavras reservadas
        reserved_format = QTextCharFormat()
        reserved_format.setForeground(QColor("#569CD6"))
        
        reserved_words = ["true", "false", "null"]
        for word in reserved_words:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, reserved_format))


class JavaHighlighter(BaseHighlighter):
    """Syntax Highlighter dedicado para Java"""
    
    def setup_rules(self):
        self.setup_java_rules()
    
    def setup_java_rules(self):
        """Configura regras específicas para Java"""
        
        # Palavras-chave Java
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors['keyword'])
        keyword_format.setFontWeight(QFont.Bold)
        
        java_keywords = [
            "abstract", "assert", "boolean", "break", "byte", "case", "catch",
            "char", "class", "const", "continue", "default", "do", "double",
            "else", "enum", "extends", "final", "finally", "float", "for",
            "goto", "if", "implements", "import", "instanceof", "int", "interface",
            "long", "native", "new", "package", "private", "protected", "public",
            "return", "short", "static", "strictfp", "super", "switch",
            "synchronized", "this", "throw", "throws", "transient", "try",
            "void", "volatile", "while"
        ]
        
        for keyword in java_keywords:
            pattern = QRegularExpression(f"\\b{keyword}\\b")
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Tipos
        type_format = QTextCharFormat()
        type_format.setForeground(self.colors['type'])
        
        types = ["String", "Integer", "Double", "Float", "Boolean", "Object"]
        for type_name in types:
            pattern = QRegularExpression(f"\\b{type_name}\\b")
            self.highlighting_rules.append((pattern, type_format))
        
        # Strings e comentários (usando regras comuns)
        self.setup_common_rules()


class CppHighlighter(BaseHighlighter):
    """Syntax Highlighter dedicado para C++"""
    
    def setup_rules(self):
        self.setup_cpp_rules()
    
    def setup_cpp_rules(self):
        """Configura regras específicas para C++"""
        
        # Palavras-chave C++
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors['keyword'])
        keyword_format.setFontWeight(QFont.Bold)
        
        cpp_keywords = [
            "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel", "atomic_commit",
            "atomic_noexcept", "auto", "bitand", "bitor", "bool", "break", "case", "catch",
            "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept", "const",
            "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await",
            "co_return", "co_yield", "decltype", "default", "delete", "do", "double",
            "dynamic_cast", "else", "enum", "explicit", "export", "extern", "false", "float",
            "for", "friend", "goto", "if", "inline", "int", "long", "mutable", "namespace",
            "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq",
            "private", "protected", "public", "reflexpr", "register", "reinterpret_cast",
            "requires", "return", "short", "signed", "sizeof", "static", "static_assert",
            "static_cast", "struct", "switch", "synchronized", "template", "this",
            "thread_local", "throw", "true", "try", "typedef", "typeid", "typename",
            "union", "unsigned", "using", "virtual", "void", "volatile", "wchar_t",
            "while", "xor", "xor_eq"
        ]
        
        for keyword in cpp_keywords:
            pattern = QRegularExpression(f"\\b{keyword}\\b")
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Strings e comentários
        self.setup_common_rules()


class PHPHighlighter(BaseHighlighter):
    """Syntax Highlighter dedicado para PHP"""
    
    def setup_rules(self):
        self.setup_php_rules()
    
    def setup_php_rules(self):
        """Configura regras específicas para PHP"""
        
        # Palavras-chave PHP
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors['keyword'])
        keyword_format.setFontWeight(QFont.Bold)
        
        php_keywords = [
            "__halt_compiler", "abstract", "and", "array", "as", "break", "callable",
            "case", "catch", "class", "clone", "const", "continue", "declare", "default",
            "die", "do", "echo", "else", "elseif", "empty", "enddeclare", "endfor",
            "endforeach", "endif", "endswitch", "endwhile", "eval", "exit", "extends",
            "final", "finally", "fn", "for", "foreach", "function", "global", "goto",
            "if", "implements", "include", "include_once", "instanceof", "insteadof",
            "interface", "isset", "list", "match", "namespace", "new", "or", "print",
            "private", "protected", "public", "require", "require_once", "return",
            "static", "switch", "throw", "trait", "try", "unset", "use", "var",
            "while", "xor", "yield"
        ]
        
        for keyword in php_keywords:
            pattern = QRegularExpression(f"\\b{keyword}\\b")
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Variáveis PHP ($)
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor("#9CDCFE"))
        
        self.highlighting_rules.append(
            (QRegularExpression(r'\$[a-zA-Z_][a-zA-Z0-9_]*'), variable_format)
        )
        
        # Strings e comentários
        self.setup_common_rules()


class TextHighlighter(BaseHighlighter):
    """Highlighter genérico para texto simples"""
    
    def setup_rules(self):
        # Apenas regras básicas para texto
        self.setup_basic_rules()


# Métodos auxiliares para regras comuns
def setup_common_rules(self):
    """Configura regras comuns para várias linguagens"""
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

def setup_basic_rules(self):
    """Configura regras básicas para linguagens não suportadas"""
    # Apenas strings e números básicos
    string_format = QTextCharFormat()
    string_format.setForeground(self.colors['string'])
    
    self.highlighting_rules.append(
        (QRegularExpression(r'"[^"]*"'), string_format)
    )
    
    number_format = QTextCharFormat()
    number_format.setForeground(self.colors['number'])
    
    self.highlighting_rules.append(
        (QRegularExpression(r'\b[0-9]+\b'), number_format)
    )

# Adiciona os métodos auxiliares às classes
BaseHighlighter.setup_common_rules = setup_common_rules
BaseHighlighter.setup_basic_rules = setup_basic_rules


# Fábrica de Highlighters
class HighlighterFactory:
    """Fábrica para criar highlighters baseados na extensão do arquivo"""
    
    @staticmethod
    def create_highlighter(file_path, document):
        """Cria o highlighter apropriado baseado na extensão do arquivo"""
        if not file_path:
            return TextHighlighter(document)
        
        extension = file_path.lower().split('.')[-1] if '.' in file_path else ''
        
        highlighter_map = {
            'py': PythonHighlighter,
            'js': JavaScriptHighlighter,
            'html': HTMLHighlighter,
            'htm': HTMLHighlighter,
            'css': CSSHighlighter,
            'json': JSONHighlighter,
            'java': JavaHighlighter,
            'cpp': CppHighlighter,
            'c': CppHighlighter,
            'h': CppHighlighter,
            'php': PHPHighlighter,
            'txt': TextHighlighter,
            'md': TextHighlighter,
        }
        
        highlighter_class = highlighter_map.get(extension, TextHighlighter)
        return highlighter_class(document)
    
    @staticmethod
    def get_supported_languages():
        """Retorna lista de linguagens suportadas"""
        return {
            'Python': ['.py'],
            'JavaScript': ['.js'],
            'HTML': ['.html', '.htm'],
            'CSS': ['.css'],
            'JSON': ['.json'],
            'Java': ['.java'],
            'C/C++': ['.cpp', '.c', '.h'],
            'PHP': ['.php'],
            'Text': ['.txt', '.md']
        }