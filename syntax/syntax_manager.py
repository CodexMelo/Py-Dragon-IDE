from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *  # ✅ CORREÇÃO: Adicionar este import
from typing import Dict, Any
import os
from syntax.highlighters import HighlighterFactory

class SyntaxHighlightingManager:
    
    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.highlighters = {}
        self.current_language = "python"
        self.language_syntax_manager = LanguageSyntaxManager()  # ✅ CORREÇÃO: Criar instância
        
    def setup_editor_highlighter(self, editor, file_path):
        """Configura syntax highlighting para um editor baseado no arquivo"""
        if not file_path:
            return
            
        language = self.detect_language(file_path)
        self.current_language = language
        
        # Remove highlighter anterior se existir
        if editor in self.highlighters:
            self.highlighters[editor].setDocument(None)
            
        # ✅ CORREÇÃO: Usar HighlighterFactory importada no topo
        try:
            highlighter = HighlighterFactory.create_highlighter(file_path, editor.document())
            self.highlighters[editor] = highlighter
            print(f"✅ Highlighter criado para: {language}")
            
        except Exception as e:
            print(f"⚠️ Erro ao criar highlighter: {e}, usando fallback")
            # Fallback: criar highlighter básico
            highlighter = self._create_basic_highlighter(language, editor.document())
            self.highlighters[editor] = highlighter
        
        # Aplica configurações adicionais
        self.apply_editor_settings(editor)
    
    def _create_basic_highlighter(self, language, document):
        """Cria um highlighter básico como fallback"""
        from PySide6.QtGui import QSyntaxHighlighter
        
        class BasicHighlighter(QSyntaxHighlighter):
            def __init__(self, parent=None):
                super().__init__(parent)
                
            def highlightBlock(self, text):
                # Implementação básica - sem highlighting
                pass
        
        return BasicHighlighter(document)
    
    def detect_language(self, file_path):
        """Detecta a linguagem baseada na extensão do arquivo"""
        extension = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.htm': 'html',
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
            '.h': 'c',
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
    
    def apply_editor_settings(self, editor):
        """Aplica configurações visuais adicionais ao editor"""
        # Configura fonte monoespaçada para melhor alinhamento
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        editor.setFont(font)
        
        # Configura tabulação
        editor.setTabStopDistance(40)  # 4 espaços equivalentes
        
        # Configura quebra de linha
        editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Configura cores de seleção
        palette = editor.palette()
        palette.setColor(QPalette.Highlight, QColor(86, 156, 214))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        editor.setPalette(palette)
    
    def update_theme(self, theme_colors):
        """Atualiza as cores do syntax highlighting baseado no tema"""
        for highlighter in self.highlighters.values():
            if hasattr(highlighter, 'colors'):
                highlighter.colors.update(theme_colors)
                # Recarrega as regras com as novas cores
                if hasattr(highlighter, 'highlighting_rules'):
                    highlighter.highlighting_rules.clear()
                if hasattr(highlighter, 'setup_rules'):
                    highlighter.setup_rules()
                # Força rehighlight de todo o documento
                highlighter.rehighlight()
    
    def clear_highlighter(self, editor):
        """Remove o highlighter de um editor"""
        if editor in self.highlighters:
            self.highlighters[editor].setDocument(None)
            del self.highlighters[editor]


class LanguageSyntaxManager:

    def __init__(self):
        self.syntax_data = {}
        self.syntax_path = os.path.join(
        os.path.expanduser("~"), ".py_dragon_syntax")
        self.load_all_syntax()

    def load_all_syntax(self):
        """Carrega todos os arquivos de sintaxe"""
        languages = {
            'python': self._get_python_syntax(),
            'javascript': self._get_javascript_syntax(),
            'html': self._get_html_syntax(),
            'css': self._get_css_syntax(),
            'sql': self._get_sql_syntax(),
            'java': self._get_java_syntax(),
            'cpp': self._get_cpp_syntax(),
            'csharp': self._get_csharp_syntax(),
            'php': self._get_php_syntax(),
            'ruby': self._get_ruby_syntax(),
            'go': self._get_go_syntax(),
            'rust': self._get_rust_syntax(),
            'swift': self._get_swift_syntax(),
                'kotlin': self._get_kotlin_syntax(),
            'typescript': self._get_typescript_syntax(),
            'yaml': self._get_yaml_syntax(),
            'xml': self._get_xml_syntax(),
            'markdown': self._get_markdown_syntax()
        }

        for lang, syntax in languages.items():
            self.syntax_data[lang] = syntax

    def _get_python_syntax(self) -> Dict[str, Any]:
        return {
            "name": "Python",
            "extensions": [".py", ".pyw", ".pyi"],
            "keywords": [
                "False", "None", "True", "and", "as", "assert", "async", "await",
                "break", "class", "continue", "def", "del", "elif", "else", "except",
                "finally", "for", "from", "global", "if", "import", "in", "is",
                "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
                "try", "while", "with", "yield"
            ],
            "builtin_functions": [
                "abs()", "all()", "any()", "ascii()", "bin()", "bool()", "breakpoint()",
                "bytearray()", "bytes()", "callable()", "chr()", "classmethod()",
                "compile()", "complex()", "delattr()", "dict()", "dir()", "divmod()",
                "enumerate()", "eval()", "exec()", "filter()", "float()", "format()",
                "frozenset()", "getattr()", "globals()", "hasattr()", "hash()",
                "help()", "hex()", "id()", "input()", "int()", "isinstance()",
                "issubclass()", "iter()", "len()", "list()", "locals()", "map()",
                "max()", "memoryview()", "min()", "next()", "object()", "oct()",
                "open()", "ord()", "pow()", "print()", "property()", "range()",
                "repr()", "reversed()", "round()", "set()", "setattr()", "slice()",
                "sorted()", "staticmethod()", "str()", "sum()", "super()", "tuple()",
                "type()", "vars()", "zip()", "__import__()"
            ],
            "builtin_types": [
                "int", "float", "str", "bool", "list", "dict", "tuple", "set",
                "frozenset", "complex", "bytes", "bytearray", "memoryview", "range"
            ],
            "common_modules": {
                "os": ["path", "mkdir", "remove", "listdir", "getcwd", "chdir"],
                "sys": ["argv", "path", "exit", "version", "platform"],
                "json": ["loads", "dumps", "load", "dump"],
                "re": ["search", "match", "findall", "sub", "compile", "IGNORECASE"],
                "datetime": ["datetime", "date", "time", "timedelta", "now", "today"],
                "math": ["sqrt", "sin", "cos", "tan", "pi", "e", "log", "exp"],
                "random": ["random", "randint", "choice", "shuffle", "seed"],
                "subprocess": ["run", "call", "Popen", "check_output"],
                "shutil": ["copy", "move", "rmtree", "which", "copytree"],
                "glob": ["glob", "iglob"],
                "ast": ["parse", "walk", "NodeVisitor", "literal_eval"],
                "inspect": ["getsource", "signature", "getmembers", "isfunction"]
            },
            "method_chains": {
                "str": ["upper", "lower", "strip", "split", "join", "replace", "find"],
                "list": ["append", "remove", "pop", "sort", "reverse", "index", "count"],
                "dict": ["get", "keys", "values", "items", "update", "pop", "clear"],
                "set": ["add", "remove", "discard", "union", "intersection", "difference"],
                "file": ["read", "write", "close", "readline", "readlines", "seek"]
            }
        }

    def _get_javascript_syntax(self) -> Dict[str, Any]:
        return {
            "name": "JavaScript",
            "extensions": [".js", ".jsx", ".mjs", ".cjs"],
            "keywords": [
                "break", "case", "catch", "class", "const", "continue", "debugger",
                "default", "delete", "do", "else", "export", "extends", "finally",
                "for", "function", "if", "import", "in", "instanceof", "new",
                "return", "super", "switch", "this", "throw", "try", "typeof",
                "var", "void", "while", "with", "yield", "await", "enum", "implements",
                "interface", "let", "package", "private", "protected", "public", "static"
            ],
            "builtin_objects": [
                "Array", "Date", "eval", "function", "hasOwnProperty", "Infinity",
                "isFinite", "isNaN", "isPrototypeOf", "length", "Math", "NaN",
                "name", "Number", "Object", "prototype", "String", "toString",
                "undefined", "valueOf"
            ],
            "global_functions": [
                "decodeURI()", "decodeURIComponent()", "encodeURI()", "encodeURIComponent()",
                "eval()", "isFinite()", "isNaN()", "parseFloat()", "parseInt()"
            ],
            "common_apis": {
                "console": ["log", "error", "warn", "info", "debug", "table"],
                "Math": ["abs", "ceil", "floor", "round", "max", "min", "pow", "random"],
                "Array": ["from", "isArray", "of", "concat", "every", "filter", "find",
                          "findIndex", "forEach", "includes", "indexOf", "join", "map",
                          "pop", "push", "reduce", "reverse", "shift", "slice", "some",
                          "sort", "splice", "unshift"],
                "String": ["fromCharCode", "fromCodePoint", "raw", "charAt", "charCodeAt",
                           "concat", "endsWith", "includes", "indexOf", "lastIndexOf",
                           "localeCompare", "match", "normalize", "padEnd", "padStart",
                           "repeat", "replace", "search", "slice", "split", "startsWith",
                           "substr", "substring", "toLowerCase", "toUpperCase", "trim"]
            }
        }

    def _get_html_syntax(self) -> Dict[str, Any]:
        return {
            "name": "HTML",
            "extensions": [".html", ".htm", ".xhtml"],
            "tags": [
                "html", "head", "title", "body", "div", "span", "p", "h1", "h2", "h3",
                "h4", "h5", "h6", "a", "img", "ul", "ol", "li", "table", "tr", "td",
                "th", "form", "input", "button", "textarea", "select", "option",
                "label", "script", "style", "link", "meta", "header", "footer",
                "nav", "section", "article", "aside", "main", "figure", "figcaption"
            ],
            "attributes": {
                "global": ["id", "class", "style", "title", "lang", "dir", "accesskey", "tabindex"],
                "a": ["href", "target", "download", "rel"],
                "img": ["src", "alt", "width", "height", "loading"],
                "form": ["action", "method", "enctype", "target"],
                "input": ["type", "name", "value", "placeholder", "required", "disabled",
                          "readonly", "maxlength", "min", "max", "step"],
                "button": ["type", "name", "value", "disabled"],
                "textarea": ["name", "rows", "cols", "placeholder", "required", "disabled"],
                "select": ["name", "multiple", "required", "disabled"],
                "option": ["value", "selected", "disabled"],
                "label": ["for"],
                "link": ["rel", "href", "type", "media"],
                "script": ["src", "type", "async", "defer"],
                "style": ["type", "media"],
                "meta": ["name", "content", "charset", "http-equiv"]
            }
        }

    def _get_css_syntax(self) -> Dict[str, Any]:
        return {
            "name": "CSS",
            "extensions": [".css", ".scss", ".sass", ".less"],
            "properties": [
                "color", "background-color", "background-image", "background-repeat",
                "background-position", "background-size", "font-family", "font-size",
                "font-weight", "font-style", "text-align", "text-decoration",
                "text-transform", "line-height", "letter-spacing", "width", "height",
                "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
                "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
                "border", "border-width", "border-style", "border-color", "border-radius",
                "display", "position", "top", "right", "bottom", "left", "float", "clear",
                "overflow", "visibility", "opacity", "z-index", "flex", "flex-direction",
                "flex-wrap", "justify-content", "align-items", "align-content", "grid",
                "grid-template-columns", "grid-template-rows", "grid-gap", "transition",
                "animation", "transform", "box-shadow", "text-shadow"
            ],
            "values": {
                "color": ["red", "blue", "green", "black", "white", "transparent", "#", "rgb(", "rgba("],
                "size": ["px", "em", "rem", "%", "vh", "vw", "vmin", "vmax"],
                "display": ["block", "inline", "inline-block", "flex", "grid", "none"],
                "position": ["static", "relative", "absolute", "fixed", "sticky"],
                "font-weight": ["normal", "bold", "bolder", "lighter", "100", "200", "300", "400", "500", "600", "700",
                                "800", "900"]
            }
        }

    def _get_sql_syntax(self) -> Dict[str, Any]:
        return {
            "name": "SQL",
            "extensions": [".sql", ".ddl", ".dml"],
            "keywords": [
                "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE",
                "ALTER", "DROP", "TABLE", "DATABASE", "INDEX", "VIEW", "JOIN",
                "INNER", "LEFT", "RIGHT", "OUTER", "ON", "AND", "OR", "NOT",
                "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET", "VALUES",
                "SET", "INTO", "AS", "IS", "NULL", "LIKE", "IN", "BETWEEN", "UNION",
                "DISTINCT", "ALL", "EXISTS", "CASE", "WHEN", "THEN", "ELSE", "END"
            ],
            "functions": {
                "aggregate": ["COUNT", "SUM", "AVG", "MAX", "MIN", "GROUP_CONCAT"],
                "string": ["CONCAT", "SUBSTRING", "LENGTH", "UPPER", "LOWER", "TRIM", "REPLACE"],
                "numeric": ["ABS", "ROUND", "CEIL", "FLOOR", "MOD", "POWER", "SQRT"],
                "date": ["NOW", "CURDATE", "CURTIME", "DATE", "TIME", "YEAR", "MONTH", "DAY"]
            }
        }

    def _get_java_syntax(self) -> Dict[str, Any]:
        return {
            "name": "Java",
            "extensions": [".java", ".jav"],
            "keywords": [
                "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
                "class", "const", "continue", "default", "do", "double", "else", "enum",
                "extends", "final", "finally", "float", "for", "goto", "if", "implements",
                "import", "instanceof", "int", "interface", "long", "native", "new",
                "package", "private", "protected", "public", "return", "short", "static",
                "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
                "transient", "try", "void", "volatile", "while"
            ],
            "common_classes": {
                "System": ["out", "in", "err", "exit", "currentTimeMillis"],
                "String": ["length", "charAt", "substring", "equals", "indexOf", "toLowerCase", "toUpperCase"],
                "Math": ["abs", "sqrt", "pow", "max", "min", "random"],
                "ArrayList": ["add", "get", "remove", "size", "clear"],
                "HashMap": ["put", "get", "remove", "containsKey", "keySet"]
            }
        }

    def _get_cpp_syntax(self) -> Dict[str, Any]:
        return {
            "name": "C++",
            "extensions": [".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh"],
            "keywords": [
                "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
                "bool", "break", "case", "catch", "char", "char8_t", "char16_t", "char32_t",
                "class", "compl", "concept", "const", "consteval", "constexpr", "const_cast",
                "continue", "co_await", "co_return", "co_yield", "decltype", "default",
                "delete", "do", "double", "dynamic_cast", "else", "enum", "explicit",
                "export", "extern", "false", "float", "for", "friend", "goto", "if",
                "inline", "int", "long", "mutable", "namespace", "new", "noexcept", "not",
                "not_eq", "nullptr", "operator", "or", "or_eq", "private", "protected",
                "public", "register", "reinterpret_cast", "requires", "return", "short",
                "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
                "switch", "template", "this", "thread_local", "throw", "true", "try",
                "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual",
                "void", "volatile", "wchar_t", "while", "xor", "xor_eq"
            ],
            "common_headers": {
                "iostream": ["cin", "cout", "cerr", "endl"],
                "vector": ["push_back", "pop_back", "size", "empty", "clear"],
                "string": ["length", "substr", "find", "replace", "c_str"],
                "algorithm": ["sort", "find", "reverse", "count", "max_element"]
            }
        }

    def _get_csharp_syntax(self) -> Dict[str, Any]:
        return {
            "name": "C#",
            "extensions": [".cs"],
            "keywords": [
                "abstract", "as", "base", "bool", "break", "byte", "case", "catch", "char",
                "checked", "class", "const", "continue", "decimal", "default", "delegate",
                "do", "double", "else", "enum", "event", "explicit", "extern", "false",
                "finally", "fixed", "float", "for", "foreach", "goto", "if", "implicit",
                "in", "int", "interface", "internal", "is", "lock", "long", "namespace",
                "new", "null", "object", "operator", "out", "override", "params", "private",
                "protected", "public", "readonly", "ref", "return", "sbyte", "sealed",
                "short", "sizeof", "stackalloc", "static", "string", "struct", "switch",
                "this", "throw", "true", "try", "typeof", "uint", "ulong", "unchecked",
                "unsafe", "ushort", "using", "virtual", "void", "volatile", "while"
            ],
            "common_classes": {
                "Console": ["WriteLine", "Write", "ReadLine", "Read"],
                "String": ["Length", "Substring", "ToLower", "ToUpper", "Split", "Replace"],
                "Math": ["Abs", "Sqrt", "Pow", "Max", "Min", "Round"],
                "List": ["Add", "Remove", "Count", "Clear", "Contains"],
                "Dictionary": ["Add", "Remove", "ContainsKey", "Keys", "Values"]
            }
        }

    def _get_php_syntax(self) -> Dict[str, Any]:
        return {
            "name": "PHP",
            "extensions": [".php", ".phtml", ".php3", ".php4", ".php5", ".php7", ".phps"],
            "keywords": [
                "__halt_compiler", "abstract", "and", "array", "as", "break", "callable",
                "case", "catch", "class", "clone", "const", "continue", "declare", "default",
                "die", "do", "echo", "else", "elseif", "empty", "enddeclare", "endfor",
                "endforeach", "endif", "endswitch", "endwhile", "eval", "exit", "extends",
                "final", "finally", "fn", "for", "foreach", "function", "global", "goto",
                "if", "implements", "include", "include_once", "instanceof", "insteadof",
                "interface", "isset", "list", "match", "namespace", "new", "or", "print",
                "private", "protected", "public", "require", "require_once", "return",
                "static", "switch", "throw", "trait", "try", "unset", "use", "var", "while",
                "xor", "yield"
            ],
            "superglobals": [
                "$GLOBALS", "$_SERVER", "$_GET", "$_POST", "$_FILES", "$_REQUEST",
                "$_SESSION", "$_ENV", "$_COOKIE"
            ],
            "common_functions": {
                "string": ["strlen", "substr", "strpos", "str_replace", "trim", "explode", "implode"],
                "array": ["count", "array_push", "array_pop", "array_merge", "in_array", "array_keys"],
                "file": ["file_get_contents", "file_put_contents", "fopen", "fclose", "fwrite"]
            }
        }

    def _get_ruby_syntax(self) -> Dict[str, Any]:
        return {
            "name": "Ruby",
            "extensions": [".rb", ".rbw", ".rake", ".gemspec"],
            "keywords": [
                "BEGIN", "END", "alias", "and", "begin", "break", "case", "class",
                "def", "defined?", "do", "else", "elsif", "end", "ensure", "false",
                "for", "if", "in", "module", "next", "nil", "not", "or", "redo",
                "rescue", "retry", "return", "self", "super", "then", "true",
                "undef", "unless", "until", "when", "while", "yield"
            ],
            "common_methods": {
                "String": ["length", "upcase", "downcase", "strip", "split", "gsub"],
                "Array": ["push", "pop", "length", "each", "map", "select"],
                "Hash": ["keys", "values", "each", "merge", "delete"],
                "File": ["read", "write", "open", "close", "exists?"]
            }
        }

    def _get_go_syntax(self) -> Dict[str, Any]:
        return {
            "name": "Go",
            "extensions": [".go"],
            "keywords": [
                "break", "default", "func", "interface", "select", "case", "defer",
                "go", "map", "struct", "chan", "else", "goto", "package", "switch",
                "const", "fallthrough", "if", "range", "type", "continue", "for",
                "import", "return", "var"
            ],
            "builtin_functions": [
                "append", "cap", "close", "complex", "copy", "delete", "imag",
                "len", "make", "new", "panic", "print", "println", "real", "recover"
            ],
            "common_packages": {
                "fmt": ["Println", "Printf", "Sprintf", "Scan", "Scanf"],
                "strings": ["Contains", "HasPrefix", "HasSuffix", "Join", "Split", "ToLower", "ToUpper"],
                "os": ["Getenv", "Setenv", "Exit", "Getwd", "Chdir"]
            }
        }

    def _get_rust_syntax(self) -> Dict[str, Any]:
        return {
            "name": "Rust",
            "extensions": [".rs", ".rlib"],
            "keywords": [
                "as", "break", "const", "continue", "crate", "else", "enum", "extern",
                "false", "fn", "for", "if", "impl", "in", "let", "loop", "match", "mod",
                "move", "mut", "pub", "ref", "return", "self", "Self", "static", "struct",
                "super", "true", "trait", "type", "unsafe", "use", "where", "while",
                "async", "await", "dyn", "abstract", "become", "box", "do", "final",
                "macro", "override", "priv", "typeof", "unsized", "virtual", "yield"
            ],
            "common_modules": {
                "std::io": ["stdin", "stdout", "stderr", "Read", "Write"],
                "std::vec::Vec": ["push", "pop", "len", "is_empty", "contains"],
                "std::string::String": ["from", "as_str", "push_str", "len", "is_empty"]
            }
        }

    def _get_swift_syntax(self) -> Dict[str, Any]:
        return {
            "name": "Swift",
            "extensions": [".swift"],
            "keywords": [
                "associatedtype", "class", "deinit", "enum", "extension", "fileprivate",
                "func", "import", "init", "inout", "internal", "let", "open", "operator",
                "private", "protocol", "public", "static", "struct", "subscript",
                "typealias", "var", "break", "case", "continue", "default", "defer",
                "do", "else", "fallthrough", "for", "guard", "if", "in", "repeat",
                "return", "switch", "where", "while", "as", "catch", "false", "is",
                "nil", "rethrows", "super", "self", "Self", "throw", "throws", "true",
                "try", "try?"
            ],
            "common_types": {
                "String": ["count", "isEmpty", "hasPrefix", "hasSuffix", "lowercased", "uppercased"],
                "Array": ["append", "remove", "count", "isEmpty", "contains"],
                "Dictionary": ["updateValue", "removeValue", "count", "isEmpty", "keys"]
            }
        }

    def _get_kotlin_syntax(self) -> Dict[str, Any]:
        return {
            "name": "Kotlin",
            "extensions": [".kt", ".kts"],
            "keywords": [
                "as", "as?", "break", "class", "continue", "do", "else", "false",
                "for", "fun", "if", "in", "!in", "interface", "is", "!is", "null",
                "object", "package", "return", "super", "this", "throw", "true",
                "try", "typealias", "val", "var", "when", "while", "by", "catch",
                "constructor", "delegate", "dynamic", "field", "file", "finally",
                "get", "import", "init", "param", "property", "receiver", "set",
                "setparam", "where", "actual", "abstract", "annotation", "companion",
                "const", "crossinline", "data", "enum", "expect", "external",
                "final", "infix", "inline", "inner", "internal", "lateinit",
                "noinline", "open", "operator", "out", "override", "private",
                "protected", "public", "reified", "sealed", "suspend", "tailrec",
                "vararg", "it"
            ],
            "common_functions": [
                "println", "print", "readLine", "listOf", "mutableListOf",
                "mapOf", "mutableMapOf", "setOf", "mutableSetOf"
            ]
        }

    def _get_typescript_syntax(self) -> Dict[str, Any]:
        return {
            "name": "TypeScript",
            "extensions": [".ts", ".tsx"],
            "keywords": [
                "break", "case", "catch", "class", "const", "continue", "debugger",
                "default", "delete", "do", "else", "enum", "export", "extends",
                "false", "finally", "for", "function", "if", "import", "in",
                "instanceof", "new", "null", "return", "super", "switch", "this",
                "throw", "true", "try", "typeof", "var", "void", "while", "with",
                "as", "implements", "interface", "let", "package", "private",
                "protected", "public", "static", "yield", "any", "boolean", "constructor",
                "declare", "get", "module", "require", "number", "set", "string",
                "symbol", "type", "from", "of", "async", "await", "namespace",
                "keyof", "readonly", "infer", "unique", "unknown", "never", "override"
            ],
            "types": [
                "number", "string", "boolean", "any", "void", "null", "undefined",
                "never", "object", "unknown", "Array", "Promise", "Date", "RegExp",
                "Error", "Map", "Set", "WeakMap", "WeakSet"
            ]
        }

    def _get_yaml_syntax(self) -> Dict[str, Any]:
        return {
            "name": "YAML",
            "extensions": [".yaml", ".yml"],
            "keywords": [
                "true", "false", "null", "yes", "no", "on", "off",
                "YAML", "yaml", "TAB", "SPACE", "---", "..."
            ],
            "directives": [
                "%YAML", "%TAG"
            ],
            "common_keys": [
                "name", "version", "description", "author", "license",
                "dependencies", "devDependencies", "scripts", "main",
                "exports", "imports", "type", "engines", "os", "cpu"
            ]
        }

    def _get_xml_syntax(self) -> Dict[str, Any]:
        return {
            "name": "XML",
            "extensions": [".xml", ".xsd", ".xsl", ".xslt", ".svg"],
            "keywords": [
                "<?xml", "<!--", "-->", "<![CDATA[", "]]>", "<!DOCTYPE"
            ],
            "common_elements": {
                "xml": ["version", "encoding", "standalone"],
                "xsd": ["schema", "element", "complexType", "simpleType", "sequence", "attribute"],
                "xsl": ["stylesheet", "template", "apply-templates", "value-of", "for-each"]
            }
        }

    def _get_markdown_syntax(self) -> Dict[str, Any]:
        return {
            "name": "Markdown",
            "extensions": [".md", ".markdown"],
            "elements": [
                "#", "##", "###", "####", "#####", "######",  # Headers
                "**", "__", "*", "_",  # Bold/Italic
                "~~",  # Strikethrough
                "`", "```",  # Code
                ">",  # Blockquote
                "-", "*", "+",  # List
                "1.", "2.", "3.",  # Ordered list
                # Links
                "[", "]", "(", ")",
                "!",  # Images
                "|", "---",  # Tables
                "---", "***", "___"  # Horizontal rules
            ]
        }

    
    def get_suggestions(self):
        """Obtém sugestões de autocomplete de forma unificada"""
        try:
            # Usa o completador do IDE se disponível
            if hasattr(self, 'ide') and hasattr(self.ide, 'completer'):
                code = self.toPlainText()
                cursor_position = self.textCursor().position()
                
                suggestions = self.ide.completer.get_completions(
                    code, 
                    cursor_position,
                    self.file_path,
                    getattr(self.ide, 'project_path', "")
                )
                
                if suggestions:
                    return suggestions[:10000]  # Limita a 15 sugestões
            
            # Fallback para sugestões básicas
            return self.get_basic_suggestions()
            
        except Exception as e:
            print(f"Erro ao obter sugestões: {e}")
            return self.get_basic_suggestions()

    def get_basic_suggestions(self):
        """Sugestões básicas de fallback - MÉTODO SEGURO"""
        suggestions = set()
        
        try:
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
            
            # Análise do código atual
            code = self.toPlainText()
            
            # Funções locais
            functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
            suggestions.update([f"{f}()" for f in functions])
            
            # Classes locais
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
            suggestions.update(classes)
            
        except Exception as e:
            print(f"Erro sugestões básicas: {e}")
        
        return suggestions
