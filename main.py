import os
import subprocess
import shutil
import glob
import json
import inspect
import importlib.util
import ast
import platform
import sys
import time
import re
import traceback
import textwrap
import threading
from typing import Dict, Set, List, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QPlainTextEdit,
    QFileSystemModel, QTreeView, QTabWidget, QToolBar,
    QFileDialog, QInputDialog, QMessageBox, QComboBox,
    QMenu, QSplitter, QVBoxLayout, QWidget, QListWidget, QListWidgetItem,
    QStyledItemDelegate, QDialog, QVBoxLayout as QVBoxLayoutDialog, QLabel, QPushButton,
    QCompleter, QProgressBar, QHBoxLayout, QLineEdit
)
from PySide6.QtGui import (
    QAction, QPalette, QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextCursor,
    QKeyEvent, QTextBlockUserData, QTextOption, QPainter, QFontDatabase, QGuiApplication, QShortcut
)
from PySide6.QtCore import Qt, QDir, QRegularExpression, QProcess, QTimer, QModelIndex, QThread, Signal, \
    QStringListModel, QSize


# ===== CLASSES AUXILIARES =====

class ErrorData(QTextBlockUserData):
    def __init__(self, errors=None):
        super().__init__()
        self.errors = errors or []


class LanguageConfig:
    def __init__(self):
        self.supported_languages = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.sql': 'SQL',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.md': 'Markdown',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.txt': 'Text'
        }

    def get_language_from_extension(self, file_path):
        if not file_path:
            return 'Text'
        _, ext = os.path.splitext(file_path)
        return self.supported_languages.get(ext.lower(), 'Text')


# ===== VISITORS PARA ANÁLISE AST =====

class DefinitionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.definitions = set()
        self.imported_modules = set()
        self.current_class = None
        self.import_statements = []

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.definitions.add(node.name)
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class:
            self.definitions.add(f"{self.current_class}.{node.name}()")
        else:
            self.definitions.add(f"{node.name}()")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if self.current_class:
            self.definitions.add(f"{self.current_class}.{node.name}()")
        else:
            self.definitions.add(f"{node.name}()")
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.definitions.add(target.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            self.definitions.add(module_name)
            self.imported_modules.add(module_name)
            self.import_statements.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.definitions.add(node.module)
            self.imported_modules.add(node.module)
            self.import_statements.append(f"from {node.module} import ...")
        for alias in node.names:
            self.definitions.add(alias.name)
        self.generic_visit(node)


class SafeDefinitionVisitor(ast.NodeVisitor):
    """Visitor AST seguro com tratamento de erros"""

    def __init__(self):
        self.definitions = set()

    def visit_ClassDef(self, node):
        try:
            self.definitions.add(node.name)
            self.generic_visit(node)
        except:
            pass

    def visit_FunctionDef(self, node):
        try:
            self.definitions.add(f"{node.name}()")
            self.generic_visit(node)
        except:
            pass

    def visit_Import(self, node):
        try:
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                self.definitions.add(module_name)
            self.generic_visit(node)
        except:
            pass

    def visit_ImportFrom(self, node):
        try:
            if node.module:
                self.definitions.add(node.module)
            for alias in node.names:
                self.definitions.add(alias.name)
            self.generic_visit(node)
        except:
            pass


# ===== GERENCIADOR DE SINTAXE =====

class LanguageSyntaxManager:
    """Gerenciador de sintaxe para múltiplas linguagens"""

    def __init__(self):
        self.syntax_data = {}
        self.syntax_path = os.path.join(os.path.expanduser("~"), ".py_dragon_syntax")
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
            ]
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
            ]
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
                "[", "]", "(", ")",  # Links
                "!",  # Images
                "|", "---",  # Tables
                "---", "***", "___"  # Horizontal rules
            ]
        }

    def get_suggestions(self, language: str, context: str = "") -> List[str]:
        """Obtém sugestões baseadas na linguagem e contexto"""
        if language not in self.syntax_data:
            return []

        syntax = self.syntax_data[language]
        suggestions = []

        # Adiciona keywords
        suggestions.extend(syntax.get('keywords', []))

        # Adiciona funções built-in
        suggestions.extend(syntax.get('builtin_functions', []))
        suggestions.extend(syntax.get('builtin_objects', []))
        suggestions.extend(syntax.get('global_functions', []))

        # Adiciona tags HTML
        suggestions.extend(syntax.get('tags', []))

        # Adiciona propriedades CSS
        suggestions.extend(syntax.get('properties', []))

        return sorted(list(set(suggestions)))

    def get_chain_suggestions(self, language: str, chain: str) -> List[str]:
        """Obtém sugestões para cadeias (obj.metodo)"""
        if language not in self.syntax_data:
            return []

        syntax = self.syntax_data[language]

        # Para Python
        if language == 'python':
            method_chains = syntax.get('method_chains', {})
            common_modules = syntax.get('common_modules', {})

            # Verifica se é um método chain conhecido
            for base, methods in method_chains.items():
                if chain == base:
                    return [f"{m}()" for m in methods]

            # Verifica se é um módulo conhecido
            for module, methods in common_modules.items():
                if chain == module:
                    return methods

        return []


# Instância global
language_syntax_manager = LanguageSyntaxManager()


# CONTINUAÇÃO DO CÓDIGO... (o restante permanece igual)

# ===== SISTEMA DE CACHE DE MÓDULOS =====

class ModuleCacheManager:
    """Gerenciador de cache para módulos e métodos"""

    def __init__(self):
        self._cache_lock = threading.RLock()
        self._module_cache: Dict[str, Dict[str, Any]] = {}
        self._project_modules: Dict[str, Set[str]] = {}
        self._last_scan_time: Dict[str, float] = {}
        self._scan_interval = 5.0
        self._chain_cache: Dict[str, Set[str]] = {}
        self._preload_done = False

    def preload_all_project_modules(self, project_path: str, file_path: str = None):
        """PRELOAD AGRESSIVO: Carrega todos os módulos do projeto uma vez"""
        if self._preload_done or not project_path:
            return

        with self._cache_lock:
            self._preload_done = True
            print("🔄 Preloading todos os módulos do projeto...")

            # Encontra todos os .py no projeto
            py_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        py_files.append(os.path.join(root, file))

            # Carrega cada um
            for py_file in py_files:
                module_name = os.path.relpath(py_file, project_path).replace(os.sep, '.').rstrip('.py')
                self.get_module_methods(module_name, py_file, project_path)

            print("✅ Preload concluído!")

    def get_module_methods(self, module_name: str, file_path: str = None, project_path: str = None) -> Set[str]:
        """Obtém todos os métodos de um módulo com cache"""
        with self._cache_lock:
            cache_key = f"{module_name}:{file_path or ''}"

            # Verifica se precisa atualizar o cache
            current_time = time.time()
            last_scan = self._last_scan_time.get(cache_key, 0)

            if current_time - last_scan > self._scan_interval:
                self._update_module_cache(module_name, file_path, project_path)
                self._last_scan_time[cache_key] = current_time

            methods = self._module_cache.get(cache_key, set())
            return {m if m.endswith('()') else f"{m}()" for m in methods}

    def _update_module_cache(self, module_name: str, file_path: str = None, project_path: str = None):
        """Atualiza o cache para um módulo específico"""
        cache_key = f"{module_name}:{file_path or ''}"
        methods = set()

        try:
            # Tenta carregar como módulo Python padrão
            if module_name in sys.builtin_module_names:
                methods.update(self._get_builtin_module_methods(module_name))

            # Tenta importar o módulo
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    methods.update(self._get_module_attributes(module))
            except:
                pass

            # Procura módulos locais no projeto
            if project_path:
                local_methods = self._scan_local_module(module_name, project_path, file_path)
                methods.update(local_methods)

        except Exception as e:
            print(f"Erro ao atualizar cache para {module_name}: {e}")

        self._module_cache[cache_key] = methods

    def _get_builtin_module_methods(self, module_name: str) -> Set[str]:
        """Métodos para módulos built-in"""
        builtin_methods = {
            'os': ['path.join()', 'path.exists()', 'path.dirname()', 'path.basename()', 'mkdir()', 'listdir()',
                   'getcwd()', 'chdir()'],
            'sys': ['argv', 'path', 'exit()', 'version', 'platform', 'modules', 'executable'],
            'json': ['loads()', 'dumps()', 'load()', 'dump()'],
            're': ['search()', 'match()', 'findall()', 'sub()', 'compile()', 'IGNORECASE', 'MULTILINE'],
            'datetime': ['datetime', 'date', 'time', 'timedelta', 'now()', 'today()', 'strftime()'],
            'math': ['sqrt()', 'sin()', 'cos()', 'pi', 'e', 'log()', 'ceil()', 'floor()'],
            'random': ['random()', 'randint()', 'choice()', 'shuffle()', 'uniform()', 'seed()']
        }
        return set(builtin_methods.get(module_name, []))

    def _get_module_attributes(self, module) -> Set[str]:
        """Extrai atributos de um módulo importado"""
        attrs = set()
        try:
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    attr = getattr(module, attr_name)
                    if callable(attr):
                        attrs.add(f"{attr_name}()")
                    else:
                        attrs.add(attr_name)
        except:
            pass
        return attrs

    def _scan_local_module(self, module_name: str, project_path: str, current_file: str = None) -> Set[str]:
        """Escaneia módulos locais no projeto"""
        methods = set()
        try:
            # Possíveis locais do módulo
            possible_paths = [
                os.path.join(project_path, f"{module_name}.py"),
                os.path.join(project_path, module_name, "__init__.py"),
            ]

            for module_path in possible_paths:
                if os.path.exists(module_path):
                    module_methods = self._parse_python_file_robust(module_path)
                    methods.update(module_methods)
                    break

        except Exception as e:
            print(f"Erro ao escanear módulo local {module_name}: {e}")

        return methods

    def _parse_python_file_robust(self, file_path: str) -> Set[str]:
        """Analisa um arquivo Python com AST robusta"""
        methods = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = None
            try:
                tree = ast.parse(content, mode='exec', filename=file_path)
            except (IndentationError, SyntaxError):
                # Fallback regex para arquivos com problemas de sintaxe
                return self._parse_with_regex(content)

            # Visita AST
            visitor = SafeDefinitionVisitor()
            visitor.visit(tree)
            methods.update(visitor.definitions)

        except Exception as e:
            print(f"Erro ao analisar arquivo {file_path}: {e}")

        return methods

    def _parse_with_regex(self, content: str) -> Set[str]:
        """Fallback regex para análise de código"""
        methods = set()
        # Funções
        functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update([f"{f}()" for f in functions])
        # Classes
        classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update(classes)
        return methods


# Instância global do gerenciador de cache
module_cache_manager = ModuleCacheManager()


# ===== WORKERS EM BACKGROUND =====

class LinterWorker(QThread):
    finished = Signal(dict, list)  # errors, messages

    def __init__(self, file_path, python_exec, project_path):
        super().__init__()
        self.file_path = file_path
        self.python_exec = python_exec
        self.project_path = project_path
        self._is_running = True

    def stop(self):
        self._is_running = False
        self.terminate()

    def run(self):
        if not self._is_running or not self.file_path:
            return

        errors = {}
        lint_messages = []

        try:
            # Try pylint first with corrected enables
            pylint_cmd = [
                self.python_exec, '-m', 'pylint',
                '--output-format=json',
                '--reports=n',
                '--disable=all',
                '--enable=E,W,fatal',
                self.file_path
            ]

            cwd = self.project_path if self.project_path else os.path.dirname(self.file_path)
            result = subprocess.run(
                pylint_cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                timeout=5
            )

            if result.returncode in [0, 1, 2, 4, 8, 16, 32] and result.stdout.strip():
                try:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if not self._is_running:
                            return
                        if line.strip():
                            try:
                                issue = json.loads(line.strip())
                                if 'line' in issue and issue['line'] > 0:
                                    line_num = issue['line'] - 1
                                    msg = issue.get('message', 'No message')
                                    symbol = issue.get('symbol', 'unknown')
                                    msg_type = issue.get('type', 'warning')
                                    error_type = 'error' if msg_type == 'error' else 'warning'

                                    if line_num not in errors:
                                        errors[line_num] = []
                                    errors[line_num].append({
                                        'type': error_type,
                                        'msg': msg,
                                        'symbol': symbol
                                    })
                                    lint_messages.append(f"Line {issue['line']}: {msg} ({symbol})")
                            except json.JSONDecodeError:
                                continue
                except json.JSONDecodeError:
                    pass

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        if self._is_running:
            self.finished.emit(errors, lint_messages)


class AutoCompleteWorker(QThread):
    finished = Signal(list)  # suggestions
    progress = Signal(str)  # progress update
    loading_state = Signal(bool)  # True=loading, False=done

    def __init__(self, text, cursor_position, file_path, project_path, selected_text=""):
        super().__init__()
        self.text = text
        self.cursor_position = cursor_position
        self.file_path = file_path
        self.project_path = project_path
        self.selected_text = selected_text
        self._is_running = True
        self._keyword_cache = None
        self._builtin_cache = None
        self._module_cache = {}

    def stop(self):
        self._is_running = False
        self.terminate()

    def run(self):
        if not self._is_running:
            return

        try:
            self.loading_state.emit(True)
            self.progress.emit("🔍 Analisando código...")

            suggestions = self.get_instant_suggestions()

            if self._is_running:
                self.progress.emit("✅ Sugestões carregadas!")
                self.loading_state.emit(False)
                self.finished.emit(suggestions)

        except Exception as e:
            if self._is_running:
                self.progress.emit(f"❌ Erro: {str(e)}")
                self.loading_state.emit(False)
                self.finished.emit([])

    def get_instant_suggestions(self):
        """Sugestões instantâneas com suporte multi-linguagem"""
        suggestions = set()
        language = self.detect_language()

        # 1. Sugestões da sintaxe da linguagem
        syntax_suggestions = language_syntax_manager.get_suggestions(language)
        suggestions.update(syntax_suggestions)

        # 2. Para Python, usa o cache manager
        if language == 'python':
            # Palavras-chave com cache
            if self._keyword_cache is None:
                self._keyword_cache = self.get_all_keywords()
            suggestions.update(self._keyword_cache)

            # Built-ins com cache
            if self._builtin_cache is None:
                self._builtin_cache = self.get_all_builtins()
            suggestions.update(self._builtin_cache)

            # Análise local
            self.progress.emit("📝 Analisando definições locais...")
            local_defs = self.get_local_definitions_instant()
            suggestions.update(local_defs)

        return sorted(list(suggestions))[:20]

    def detect_language(self) -> str:
        """Detecta a linguagem baseada na extensão do arquivo"""
        if not self.file_path:
            return 'python'

        ext = os.path.splitext(self.file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript',
            '.html': 'html', '.htm': 'html',
            '.css': 'css', '.scss': 'css', '.sass': 'css',
            '.sql': 'sql',
            '.java': 'java',
            '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp', '.h': 'cpp', '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin', '.kts': 'kotlin',
            '.ts': 'typescript', '.tsx': 'typescript',
            '.yaml': 'yaml', '.yml': 'yaml',
            '.xml': 'xml',
            '.md': 'markdown'
        }
        return language_map.get(ext, 'python')

    def get_local_definitions_instant(self):
        """Extrai definições locais instantaneamente com regex"""
        definitions = set()
        func_matches = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', self.text)
        class_matches = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', self.text)
        definitions.update([f"{f}()" for f in func_matches])
        definitions.update(class_matches)
        return definitions

    def get_all_keywords(self):
        """Todas palavras-chave Python"""
        return {
            "if", "else", "elif", "for", "while", "break", "continue", "pass", "return",
            "try", "except", "finally", "raise", "def", "class", "lambda", "global",
            "nonlocal", "import", "from", "as", "and", "or", "not", "in", "is",
            "True", "False", "None", "with", "yield", "assert", "del", "async", "await"
        }

    def get_all_builtins(self):
        """Built-ins mais comuns"""
        return {
            "print", "len", "str", "int", "float", "list", "dict", "set", "tuple",
            "range", "input", "open", "type", "sum", "min", "max", "abs", "round",
            "sorted", "reversed", "enumerate", "zip", "map", "filter", "any", "all",
            "bool", "chr", "ord", "dir", "help", "id", "isinstance", "issubclass",
            "getattr", "setattr", "hasattr", "vars", "locals", "globals"
        }


# ===== COMPONENTES DE INTERFACE =====

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(70)

    def update_line_numbers(self):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(20, 30, 48))
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + int(self.editor.blockBoundingRect(block).height())
        font = self.editor.font()
        font.setPointSize(10)
        painter.setFont(font)
        font_metrics = self.editor.fontMetrics()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(150, 150, 150))
                painter.drawText(0, top, 50, font_metrics.height(), Qt.AlignRight, number)

                # Draw vertical separator
                painter.setPen(QColor(100, 100, 100))
                painter.drawLine(55, top, 55, bottom)

                # Draw red line for errors
                data = block.userData()
                if isinstance(data, ErrorData) and any(error['type'] == 'error' for error in data.errors):
                    painter.setPen(QColor(255, 0, 0))
                    painter.drawLine(60, top, 60, bottom)

            block = block.next()
            top = bottom
            bottom = top + int(self.editor.blockBoundingRect(block).height())
            block_number += 1


class MultiLanguageHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_config = LanguageConfig()
        self.current_language = 'Text'
        self.highlighting_rules = []
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6a9955"))

    def set_language(self, file_path):
        self.current_language = self.language_config.get_language_from_extension(file_path)
        self.setup_highlighting_rules()

    def setup_highlighting_rules(self):
        self.highlighting_rules = []
        if self.current_language == 'Python':
            self.setup_python_rules()
        elif self.current_language == 'JavaScript':
            self.setup_javascript_rules()
        # ... (outros setup_*_rules)

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
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'#.*'), self.comment_format))

    def setup_javascript_rules(self):
        # Similar ao setup_python_rules mas para JavaScript
        pass

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        # Aplica highlights de erro/aviso
        data = self.currentBlockUserData()
        if isinstance(data, ErrorData) and data.errors:
            for error in data.errors:
                if error['type'] == 'error':
                    error_format = QTextCharFormat()
                    error_format.setBackground(QColor(255, 0, 0, 128))
                    self.setFormat(0, len(text), error_format)


class AutoCompleteWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip)
        self.setMaximumHeight(120)
        self.setMaximumWidth(300)
        self.current_editor = None

    def show_suggestions(self, editor, suggestions):
        self.current_editor = editor
        self.clear()

        if not suggestions:
            self.hide()
            return

        for suggestion in suggestions[:8]:
            self.addItem(suggestion)

        cursor_rect = editor.cursorRect()
        pos = editor.mapToGlobal(cursor_rect.bottomLeft())
        self.move(pos)
        self.show()
        self.setCurrentRow(0)
        self.setFocus()

    def insert_completion(self, completion):
        if not self.current_editor:
            return
        cursor = self.current_editor.textCursor()
        cursor.insertText(completion)
        self.hide()


# ===== EDITOR PRINCIPAL =====

class CodeEditor(QPlainTextEdit):
    def __init__(self, text, cursor_position, file_path, project_path, parent=None):
        super().__init__(parent)
        super().__init__(parent)
        self.setPlainText(text)
        cursor = self.textCursor()
        cursor.setPosition(min(cursor_position, len(text)))
        self.setTextCursor(cursor)

        self.file_path = file_path
        self.project_path = project_path

        # Configurar tab
        self.configure_tab_stop()
          # 🔧 CORREÇÃO: Controle de estado do worker
        self.auto_complete_worker = None
        self.worker_lock = threading.Lock()  # Lock para evitar race conditions
        self.is_worker_running = False
        # Inicializar componentes de autocomplete
        self.auto_complete_widget = AutoCompleteWidget(self)
        self.auto_complete_timer = QTimer(self)
        self.auto_complete_timer.setSingleShot(True)
        self.auto_complete_timer.timeout.connect(self.trigger_auto_complete)
        
        # Configurações visuais
        self.setFont(QFont("Monospace", 12))
        self.setWordWrapMode(QTextOption.NoWrap)

        # Cache para melhor performance
        self.last_suggestions = []
        self.last_word = ""

    def configure_tab_stop(self):
        """Configura o tamanho do tab baseado no tipo de arquivo"""
        font = QFont("Monospace", 12)
        self.setFont(font)
        font_metrics = self.fontMetrics()

        if self.file_path and self.file_path.endswith('.py'):
            tab_width = font_metrics.horizontalAdvance(' ') * 4
        else:
            tab_width = font_metrics.horizontalAdvance(' ') * 2

        self.setTabStopDistance(tab_width)

    def keyPressEvent(self, event: QKeyEvent):
        try:
            # Atalhos para forçar autocomplete
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space:
                self.force_auto_complete()
                event.accept()
                return

            # Fecha o autocomplete se Escape for pressionado
            if event.key() == Qt.Key_Escape and self.auto_complete_widget.isVisible():
                self.auto_complete_widget.hide()
                event.accept()
                return

            # Navega no autocomplete com setas
            if self.auto_complete_widget.isVisible():
                if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Return, Qt.Key_Enter):
                    if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                        current_item = self.auto_complete_widget.currentItem()
                        if current_item:
                            self.auto_complete_widget.insert_completion(current_item.text())
                        event.accept()
                        return
                    elif event.key() == Qt.Key_Up:
                        current_row = self.auto_complete_widget.currentRow()
                        self.auto_complete_widget.setCurrentRow(max(0, current_row - 1))
                        event.accept()
                        return
                    elif event.key() == Qt.Key_Down:
                        current_row = self.auto_complete_widget.currentRow()
                        self.auto_complete_widget.setCurrentRow(
                            min(self.auto_complete_widget.count() - 1, current_row + 1))
                        event.accept()
                        return

            super().keyPressEvent(event)

        except Exception as e:
            print(f"Erro crítico no keyPressEvent: {e}")
            super().keyPressEvent(event)

    def force_auto_complete(self):
        """Força autocomplete imediatamente"""
        if self.auto_complete_worker and self.auto_complete_worker.isRunning():
            self.auto_complete_worker.stop()
            self.auto_complete_worker.wait(10)

        self.trigger_auto_complete()

    def trigger_auto_complete(self):
        """Dispara autocomplete com controle de concorrência"""
        try:
            with self.worker_lock:
                # 🔧 CORREÇÃO: Verifica se já existe worker rodando
                if self.is_worker_running:
                    return  # Já tem um worker ativo, ignora
                
                # Para worker anterior de forma segura
                if self.auto_complete_worker and self.auto_complete_worker.isRunning():
                    self.auto_complete_worker.stop()
                    self.auto_complete_worker.wait(500)  # 🔧 Aumenta timeout
                
                # Marca como rodando ANTES de criar novo worker
                self.is_worker_running = True
                
                # Cria novo worker
                self.auto_complete_worker = AutoCompleteWorker(...)
                self.auto_complete_worker.finished.connect(self.on_auto_complete_finished)
                self.auto_complete_worker.start()
                
        except Exception as e:
            print(f"Erro no trigger_auto_complete: {e}")
            self.is_worker_running = False

    def on_auto_complete_finished(self, suggestions):
        """Callback quando worker termina"""
        with self.worker_lock:
            self.is_worker_running = False
        self.show_auto_complete(suggestions)

    def fix_indentation(self):
        """Auto-corrige indentação inconsistente no texto atual"""
        try:
            text = self.toPlainText()
            # Dedent e reindent com 4 espaços
            dedented = textwrap.dedent(text)
            lines = dedented.splitlines()
            fixed_lines = []
            for line in lines:
                indent_level = len(line) - len(line.lstrip(' \t'))
                fixed_line = ' ' * (indent_level * 4) + line.lstrip(' \t')
                fixed_lines.append(fixed_line)
            fixed_text = '\n'.join(fixed_lines)
            self.setPlainText(fixed_text)
            print("Indentação corrigida automaticamente!")
        except Exception as e:
            print(f"Falha na correção de indent: {e}")

    # CONTINUA... (O restante do código permanece similar mas bem organizado)
    def is_inside_string(self, text, position):
        """Verifica se está dentro de string de forma otimizada - MELHORADO"""
        # Conta quotes não escapados
        single_count = 0
        double_count = 0
        for i, char in enumerate(text[:position]):
            if char == "'" and (i == 0 or text[i-1] != '\\'):
                single_count += 1
            elif char == '"' and (i == 0 or text[i-1] != '\\'):
                double_count += 1
        return (single_count % 2 == 1) or (double_count % 2 == 1)

    def is_inside_comment(self, current_line):
        """Verifica se está em comentário - CORREÇÃO DEFINITIVA"""
        if not current_line or not current_line.strip():
            return False

        try:
            # CORREÇÃO: Verifica simplesmente se há '#' em qualquer parte da linha
            # Não precisa splitar ou acessar índices
            return '#' in current_line
        except Exception:
            return False

    def show_auto_complete(self, suggestions):
        """Mostra sugestões instantaneamente"""
        if suggestions:
            self.auto_complete_widget.show_suggestions(self, suggestions)
            # Cache das sugestões para reutilização
            self.last_suggestions = suggestions
        else:
            self.auto_complete_widget.hide()

    def insert_completion(self, completion):
        """Insere completion rapidamente"""
        cursor = self.textCursor()

        if cursor.hasSelection():
            cursor.removeSelectedText()

        cursor.insertText(completion)
        self.auto_complete_widget.hide()
class ErrorData(QTextBlockUserData):
    def __init__(self, errors=None):
        super().__init__()
        self.errors = errors or []




class LanguageSyntaxManager:
    """Gerenciador de sintaxe para múltiplas linguagens - CORRIGIDO JSON"""

    def __init__(self):
        self.syntax_data = {}
        # Usa diretório temporário para evitar problemas de permissão
        self.syntax_path = os.path.join(os.path.expanduser("~"), ".py_dragon_syntax")
        self.load_all_syntax()

    def load_all_syntax(self):
        """Carrega todos os arquivos de sintaxe - CORRIGIDO"""
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
            # Não salva mais automaticamente para evitar erros
            # self._save_syntax_file(lang, syntax)

    def _save_syntax_file(self, language: str, syntax: Dict):
        """Salva arquivo de sintaxe se necessário - CORRIGIDO"""
        try:
            os.makedirs(self.syntax_path, exist_ok=True)
            filepath = os.path.join(self.syntax_path, f"{language}.json")

            # Converte sets para lists para serialização
            serializable_syntax = self._make_serializable(syntax)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_syntax, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Não foi possível salvar sintaxe {language}: {e}")

    def _make_serializable(self, obj):
        """Converte sets para lists para serialização JSON"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        else:
            return obj

    # CORREÇÃO: Método Kotlin com lista em vez de set
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
            "common_functions": [  # CORRIGIDO: lista em vez de set
                "println", "print", "readLine", "listOf", "mutableListOf",
                "mapOf", "mutableMapOf", "setOf", "mutableSetOf"
            ]
        }

    # CORREÇÃO: Método TypeScript com lista em vez de set
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
            "types": [  # CORRIGIDO: lista em vez de set
                "number", "string", "boolean", "any", "void", "null", "undefined",
                "never", "object", "unknown", "Array", "Promise", "Date", "RegExp",
                "Error", "Map", "Set", "WeakMap", "WeakSet"
            ]
        }

    # ... outros métodos permanecem iguais (já usam listas) ...

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
            "common_functions": {
                "println", "print", "readLine", "listOf", "mutableListOf",
                "mapOf", "mutableMapOf", "setOf", "mutableSetOf"
            }
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
                "[", "]", "(", ")",  # Links
                "!",  # Images
                "|", "---",  # Tables
                "---", "***", "___"  # Horizontal rules
            ]
        }

    # MÉTODOS DE ACESSO (mantidos iguais)
    def get_suggestions(self, language: str, context: str = "") -> List[str]:
        """Obtém sugestões baseadas na linguagem e contexto"""
        if language not in self.syntax_data:
            return []

        syntax = self.syntax_data[language]
        suggestions = []

        # Adiciona keywords
        suggestions.extend(syntax.get('keywords', []))

        # Adiciona funções built-in
        suggestions.extend(syntax.get('builtin_functions', []))
        suggestions.extend(syntax.get('builtin_objects', []))
        suggestions.extend(syntax.get('global_functions', []))

        # Adiciona tags HTML
        suggestions.extend(syntax.get('tags', []))

        # Adiciona propriedades CSS
        suggestions.extend(syntax.get('properties', []))

        return sorted(list(set(suggestions)))

    def get_chain_suggestions(self, language: str, chain: str) -> List[str]:
        """Obtém sugestões para cadeias (obj.metodo)"""
        if language not in self.syntax_data:
            return []

        syntax = self.syntax_data[language]

        # Para Python
        if language == 'python':
            method_chains = syntax.get('method_chains', {})
            common_modules = syntax.get('common_modules', {})

            # Verifica se é um método chain conhecido
            for base, methods in method_chains.items():
                if chain == base:
                    return [f"{m}()" for m in methods]

            # Verifica se é um módulo conhecido
            for module, methods in common_modules.items():
                if chain == module:
                    return methods

        # Para JavaScript
        elif language == 'javascript':
            common_apis = syntax.get('common_apis', {})
            for api, methods in common_apis.items():
                if chain == api:
                    return [f"{m}()" for m in methods]

        return []


# Instância global - AGORA FUNCIONANDO
language_syntax_manager = LanguageSyntaxManager()


class LanguageConfig:
    def __init__(self):
        self.supported_languages = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.sql': 'SQL',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.md': 'Markdown',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.txt': 'Text'
        }

    def get_language_from_extension(self, file_path):
        if not file_path:
            return 'Text'
        _, ext = os.path.splitext(file_path)
        return self.supported_languages.get(ext.lower(), 'Text')

class MultiLanguageHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_config = LanguageConfig()
        self.current_language = 'Text'
        self.highlighting_rules = []
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6a9955"))

    def set_language(self, file_path):
        self.current_language = self.language_config.get_language_from_extension(file_path)
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
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

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
            pattern = QRegularExpression(r'\b' + builtin + r'\b')
            self.highlighting_rules.append((pattern, builtin_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\bdef\s+[a-zA-Z_][a-zA-Z0-9_]*'), function_format))
        self.highlighting_rules.append((QRegularExpression(r'\b[A-Za-z_][a-zA-Z0-9_]*\s*(?=\()'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'"""(?!"").*?"""', QRegularExpression.DotMatchesEverythingOption), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r"'''(?!'').*?'''", QRegularExpression.DotMatchesEverythingOption), string_format))
        self.highlighting_rules.append((QRegularExpression(r'(f|r)?".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r'(f|r)?\'.*?\''), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'#.*'), self.comment_format))
        docstring_format = QTextCharFormat()
        docstring_format.setForeground(QColor("#808080"))
        self.highlighting_rules.append((QRegularExpression(r'"""[^"]*"""'), docstring_format))
        self.highlighting_rules.append((QRegularExpression(r"'''[^']*'''"), docstring_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))
        self.highlighting_rules.append((QRegularExpression(r'\b0[xX][0-9a-fA-F]+\b'), number_format))
        self.highlighting_rules.append((QRegularExpression(r'\b0[bB][01]+\b'), number_format))
        self.highlighting_rules.append((QRegularExpression(r'\b0[oO][0-7]+\b'), number_format))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+j\b'), number_format))

        # Self and cls
        self_format = QTextCharFormat()
        self_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append((QRegularExpression(r'\b(self|cls)\b'), self_format))

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
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'`.*?`', QRegularExpression.DotMatchesEverythingOption), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_html_rules(self):
        # Tags
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#569cd6"))
        self.highlighting_rules.append((QRegularExpression(r'</?[a-zA-Z][^>]*>'), tag_format))

        # Attributes
        attribute_format = QTextCharFormat()
        attribute_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append((QRegularExpression(r'\b[a-zA-Z-]+(?=\=)'), attribute_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), string_format))

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
            pattern = QRegularExpression(r'\b' + prop + r'\b')
            self.highlighting_rules.append((pattern, property_format))

        # Selectors
        selector_format = QTextCharFormat()
        selector_format.setForeground(QColor("#d7ba7d"))
        self.highlighting_rules.append((QRegularExpression(r'[.#]?[a-zA-Z][^{]*{'), selector_format))

        # Values
        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r':[^;]*;'), value_format))

        # Comments
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

    def setup_json_rules(self):
        # Keys
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"(?=\s*:)'), key_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        self.highlighting_rules.append((QRegularExpression(r'\b(true|false|null)\b'), keyword_format))

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
            pattern = QRegularExpression(r'\b' + word + r'\b', QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "UPPER", "LOWER", "CONCAT", "SUBSTRING"]
        for func in functions:
            pattern = QRegularExpression(r'\b' + func + r'\b', QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((pattern, function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'--.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

    def setup_java_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
            "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float",
            "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native",
            "new", "package", "private", "protected", "public", "return", "short", "static", "strictfp",
            "super", "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void",
            "volatile", "while", "true", "false", "null"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\b[A-Za-z_][A-Za-z0-9_]*(?=\()'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_cpp_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum",
            "extern", "float", "for", "goto", "if", "inline", "int", "long", "namespace", "new", "private",
            "protected", "public", "register", "return", "short", "signed", "sizeof", "static", "struct",
            "switch", "template", "this", "throw", "try", "typedef", "union", "unsigned", "virtual", "void",
            "volatile", "while", "class", "true", "false", "nullptr"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"R\".*?\""), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_csharp_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "abstract", "as", "base", "bool", "break", "byte", "case", "catch", "char", "checked", "class",
            "const", "continue", "decimal", "default", "delegate", "do", "double", "else", "enum", "event",
            "explicit", "extern", "false", "finally", "fixed", "float", "for", "foreach", "goto", "if", "implicit",
            "in", "int", "interface", "internal", "is", "lock", "long", "namespace", "new", "null", "object",
            "operator", "out", "override", "params", "private", "protected", "public", "readonly", "ref",
            "return", "sbyte", "sealed", "short", "sizeof", "stackalloc", "static", "string", "struct", "switch",
            "this", "throw", "true", "try", "typeof", "uint", "ulong", "unchecked", "unsafe", "ushort", "using",
            "virtual", "void", "volatile", "while"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r'@".*?"'), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_php_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "abstract", "and", "array", "as", "break", "callable", "case", "catch", "class", "clone", "const",
            "continue", "declare", "default", "die", "do", "echo", "else", "elseif", "empty", "enddeclare",
            "endfor", "endforeach", "endif", "endswitch", "endwhile", "eval", "exit", "extends", "final",
            "finally", "for", "foreach", "function", "global", "goto", "if", "implements", "include", "include_once",
            "instanceof", "insteadof", "interface", "isset", "list", "namespace", "new", "or", "print", "private",
            "protected", "public", "require", "require_once", "return", "static", "switch", "throw", "trait",
            "try", "unset", "use", "var", "while", "xor", "yield", "true", "false", "null"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append((QRegularExpression(r'#.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

    def setup_ruby_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "begin", "break", "case", "class", "def", "do", "else", "elsif", "end", "ensure",
            "false", "for", "if", "in", "module", "nil", "not", "or", "redo", "rescue",
            "retry", "return", "self", "super", "then", "true", "unless", "until", "when",
            "while", "yield", "alias", "and", "BEGIN", "defined?", "END", "next", "raise",
            "require", "rescue", "attr", "attr_accessor", "attr_reader", "attr_writer"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions/Methods
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\bdef\s+[a-zA-Z_][a-zA-Z0-9_]*'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), string_format))
        self.highlighting_rules.append((QRegularExpression(r'%[qQw]{[^}]*}'), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'#.*'), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_go_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "break", "default", "func", "interface", "select", "case", "defer", "go", "map", "struct",
            "chan", "else", "goto", "package", "switch", "const", "fallthrough", "if", "range", "type",
            "continue", "for", "import", "return", "var", "true", "false", "nil"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\bfunc\s+[a-zA-Z_][a-zA-Z0-9_]*'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"`[^`]*`"), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_rust_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "as", "break", "const", "continue", "crate", "else", "enum", "extern", "false", "fn", "for",
            "if", "impl", "in", "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return",
            "self", "Self", "static", "struct", "super", "true", "trait", "type", "unsafe", "use",
            "where", "while", "dyn", "abstract", "become", "box", "do", "final", "macro", "override",
            "priv", "typeof", "unsized", "virtual", "yield"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\bfn\s+[a-zA-Z_][a-zA-Z0-9_]*'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'r"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_swift_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "associatedtype", "class", "deinit", "enum", "extension", "fileprivate", "func", "import", "init",
            "inout", "internal", "let", "open", "operator", "private", "protocol", "public", "static",
            "struct", "subscript", "typealias", "var", "break", "case", "continue", "default", "defer",
            "do", "else", "fallthrough", "for", "guard", "if", "in", "repeat", "return", "switch", "where",
            "while", "as", "catch", "false", "is", "nil", "rethrows", "super", "self", "Self", "throw",
            "throws", "true", "try", "try?"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\bfunc\s+[a-zA-Z_][a-zA-Z0-9_]*'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_kotlin_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = [
            "abstract", "annotation", "as", "break", "by", "catch", "class", "companion", "const", "constructor",
            "continue", "data", "do", "else", "enum", "expect", "external", "false", "final", "finally",
            "for", "fun", "if", "import", "in", "inline", "inner", "interface", "internal", "is", "lateinit",
            "lazy", "native", "null", "object", "open", "operator", "out", "override", "package", "private",
            "property", "protected", "public", "receiver", "reified", "return", "sealed", "self", "super",
            "suspend", "tailrec", "this", "throw", "true", "try", "typealias", "typeof", "val", "var",
            "when", "where", "while"
        ]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\bfun\s+[a-zA-Z_][a-zA-Z0-9_]*'), function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'''[^''']*'''"), string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def setup_xml_rules(self):
        # Tags
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#569cd6"))
        self.highlighting_rules.append((QRegularExpression(r'</?[a-zA-Z][^>]*>'), tag_format))

        # Attributes
        attribute_format = QTextCharFormat()
        attribute_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append((QRegularExpression(r'\b[a-zA-Z-]+(?=\s*=)'), attribute_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), string_format))

        # Comments
        self.highlighting_rules.append(
            (QRegularExpression(r'<!--.*?-->', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

    def setup_markdown_rules(self):
        # Headers
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#569cd6"))
        for level in range(1, 7):
            self.highlighting_rules.append((QRegularExpression(rf'^{"#" * level}\s+'), header_format))

        # Bold/Italic
        bold_format = QTextCharFormat()
        bold_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((QRegularExpression(r'\*\*.*?\*\*'), bold_format))
        self.highlighting_rules.append((QRegularExpression(r'__.*?__'), bold_format))

        italic_format = QTextCharFormat()
        italic_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'\*.*?\*'), italic_format))
        self.highlighting_rules.append((QRegularExpression(r'_.*?_'), italic_format))

        # Code
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'`(.*?)`'), code_format))
        self.highlighting_rules.append(
            (QRegularExpression(r'```[\s\S]*?```', QRegularExpression.DotMatchesEverythingOption), code_format))

    def setup_yaml_rules(self):
        # Keys
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#9cdcfe"))
        self.highlighting_rules.append((QRegularExpression(r'^[a-zA-Z0-9_-]+:'), key_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), string_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'#.*'), self.comment_format))

    def setup_basic_rules(self):
        # Strings básicas para linguagens não específicas
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), string_format))

        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((QRegularExpression(r'\b[0-9]+\.?[0-9]*\b'), number_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        # Aplica highlights de erro/aviso
        data = self.currentBlockUserData()
        if isinstance(data, ErrorData) and data.errors:
            for error in data.errors:
                if error['type'] == 'error':
                    error_format = QTextCharFormat()
                    error_format.setBackground(QColor(255, 0, 0, 128))
                    self.setFormat(0, len(text), error_format)
                elif error['type'] == 'warning':
                    warning_format = QTextCharFormat()
                    warning_format.setBackground(QColor(255, 255, 0, 128))
                    self.setFormat(0, len(text), warning_format)

class EditorTab(QWidget):
    def __init__(self, file_path=None, parent=None):
        super().__init__(parent)

	
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.file_path = file_path
        
        # Obter conteúdo do arquivo se existir
        initial_text = ""
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    initial_text = f.read()
            except Exception:
                initial_text = ""

        # CORREÇÃO: Passar todos os parâmetros obrigatórios
        self.editor = CodeEditor(
            text=initial_text,
            cursor_position=0,
            file_path=file_path,
            project_path=self.get_project_path()
        )

        # CORREÇÃO ADICIONAL: Garantir que o tab seja 4 espaços
        font = QFont("Monospace", 12)
        self.editor.setFont(font)
        font_metrics = self.editor.fontMetrics()
        tab_width = font_metrics.horizontalAdvance(' ') * 4  # 4 espaços
        self.editor.setTabStopDistance(tab_width)

        # Use o MultiLanguageHighlighter em vez do PythonHighlighter
        self.highlighter = MultiLanguageHighlighter(self.editor.document())
        if file_path:
            self.highlighter.set_language(file_path)

        self.editor.setWordWrapMode(QTextOption.NoWrap)

        # Resto do código permanece igual...
        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.timeout.connect(self.start_linting)
        self.is_linting = False
        self.pending_lint = False

        self.linter_worker = None
        self.last_lint_content = initial_text

        # Connect signals
        self.editor.textChanged.connect(self.schedule_linting)
        self.editor.cursorPositionChanged.connect(self.update_line_numbers)
        self.editor.verticalScrollBar().valueChanged.connect(self.update_line_numbers)

        # Line number area
        self.line_number_area = LineNumberArea(self.editor)
        layout.addWidget(self.editor)
        self.setLayout(layout)

        self.update_line_numbers()

        # Set viewport margins to shift text to the right
        self.editor.setViewportMargins(self.line_number_area.width() + 10, 0, 0, 0)

    def get_project_path(self):
        """Obtém o caminho do projeto do IDE pai"""
        ide = self.get_ide()
        return ide.project_path if ide else ""

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.line_number_area.setGeometry(0, 0, self.line_number_area.width(), self.height())

    def update_line_numbers(self):
        self.line_number_area.update_line_numbers()

    def schedule_linting(self):
        """Schedule linting com debounce melhorado"""
        current_content = self.editor.toPlainText()
        
        # 🔧 CORREÇÃO: Só agenda se conteúdo mudou E não está lintando
        if (current_content != self.last_lint_content and 
            self.file_path and 
            self.file_path.endswith('.py')):
            
            if self.is_linting:
                self.pending_lint = True  # Marca que precisa relintar depois
            else:
                self.lint_timer.start(2000)  # Debounce de 2 segundos


    def start_linting(self):
        """Start linting com controle de estado"""
        if self.is_linting:
            return  # 🔧 CORREÇÃO: Já está rodando
            
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
    
    # 🔧 CORREÇÃO: Verifica se há lint pendente
    if self.pending_lint:
        self.pending_lint = False
        self.schedule_linting()  # Agenda novo lint se necessário

    # Apply errors to document
    doc = self.editor.document()
    block_count = doc.blockCount()

    # Clear previous errors from all blocks
    for i in range(block_count):
        block = doc.findBlockByLineNumber(i)
        if block.isValid():
            block.setUserData(ErrorData([]))

    # Apply new errors
    for line_num, line_errors in errors.items():
        if line_num < block_count:
            block = doc.findBlockByLineNumber(line_num)
            if block.isValid():
                data = ErrorData(line_errors)
                block.setUserData(data)

    # CORREÇÃO: Obter a instância do IDE de forma segura
    ide = self.get_ide()
    if not ide:
        return

    # Update problems list
    if ide.problems_list:
        ide.problems_list.clear()
        for msg in lint_messages:
            item = QListWidgetItem(msg)

            # Extract line number safely
            line_num = '0'
            if 'Line' in msg and ':' in msg:
                try:
                    line_part = msg.split('Line')[1].split(':')[0].strip()
                    line_num = line_part
                except:
                    pass

            data = {
                'file': self.file_path,
                'line': line_num,
                'type': 'error' if 'error' in msg.lower() else 'warning'
            }
            item.setData(Qt.UserRole, data)
            ide.problems_list.addItem(item)

    # Also update lint_text for additional info
    if ide.lint_text:
        if lint_messages:
            ide.lint_text.setPlainText('\n'.join(lint_messages))
        else:
            ide.lint_text.setPlainText("No lint issues found.")

    # Rehighlight with new errors
    self.highlighter.rehighlight()

    def get_ide(self):
        """Find and return the parent IDE instance"""
        parent = self.parent()
        while parent and not isinstance(parent, IDE):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent

    def rehighlight(self):
        self.highlighter.rehighlight()



class LinterWorker(QThread):

    finished = Signal(dict, list)  # errors, messages

    def __init__(self, file_path, python_exec, project_path):
        super().__init__()
        self.file_path = file_path
        self.python_exec = python_exec
        self.project_path = project_path
        self._is_running = True

    def stop(self):
        self._is_running = False
        self.terminate()

    def run(self):
        if not self._is_running or not self.file_path:
            return

        errors = {}
        lint_messages = []

        try:
            # Try pylint first with corrected enables
            pylint_cmd = [
                self.python_exec, '-m', 'pylint',
                '--output-format=json',
                '--reports=n',  # No reports
                '--disable=all',
                '--enable=E,W,fatal',
                self.file_path
            ]

            cwd = self.project_path if self.project_path else os.path.dirname(self.file_path)
            result = subprocess.run(
                pylint_cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                timeout=5  # Reduced timeout
            )

            if result.returncode in [0, 1, 2, 4, 8, 16, 32] and result.stdout.strip():
                try:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if not self._is_running:
                            return
                        if line.strip():
                            try:
                                issue = json.loads(line.strip())
                                if 'line' in issue and issue['line'] > 0:
                                    line_num = issue['line'] - 1
                                    msg = issue.get('message', 'No message')
                                    symbol = issue.get('symbol', 'unknown')
                                    msg_type = issue.get('type', 'warning')
                                    error_type = 'error' if msg_type == 'error' else 'warning'

                                    if line_num not in errors:
                                        errors[line_num] = []
                                    errors[line_num].append({
                                        'type': error_type,
                                        'msg': msg,
                                        'symbol': symbol
                                    })
                                    lint_messages.append(f"Line {issue['line']}: {msg} ({symbol})")
                            except json.JSONDecodeError:
                                continue
                except json.JSONDecodeError:
                    pass  # Silently ignore JSON errors

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Silently fail - we don't want to spam messages for missing linters
            pass

        if self._is_running:
            self.finished.emit(errors, lint_messages)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(70)  # Increased width for better alignment

    def update_line_numbers(self):
        self.update()

    def update_line_numbers_area(self, rect, dy):
        if dy:
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())
        if rect.contains(self.editor.viewport().rect()):
            self.update_line_numbers()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(20, 30, 48))  # Match dark theme
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + int(self.editor.blockBoundingRect(block).height())
        font = self.editor.font()
        font.setPointSize(10)
        painter.setFont(font)
        font_metrics = self.editor.fontMetrics()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(150, 150, 150))  # Light gray for line numbers
                painter.drawText(0, top, 50, font_metrics.height(), Qt.AlignRight, number)

                # Draw vertical separator
                painter.setPen(QColor(100, 100, 100))  # Gray vertical line
                painter.drawLine(55, top, 55, bottom)

                # Draw red line for errors
                data = block.userData()
                if isinstance(data, ErrorData) and any(error['type'] == 'error' for error in data.errors):
                    painter.setPen(QColor(255, 0, 0))  # Red line for errors
                    painter.drawLine(60, top, 60, bottom)

            block = block.next()
            top = bottom
            bottom = top + int(self.editor.blockBoundingRect(block).height())
            block_number += 1

class FontSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Font")
        self.layout = QVBoxLayoutDialog(self)
        self.label = QLabel("Choose a font:")
        self.layout.addWidget(self.label)
        self.font_combo = QComboBox()
        self.available_fonts = QFontDatabase.families()  # Use static method to avoid deprecation warning
        self.font_combo.addItems(self.available_fonts)
        self.layout.addWidget(self.font_combo)
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.accept)
        self.layout.addWidget(self.apply_button)
        self.setLayout(self.layout)

    def get_selected_font(self):
        return self.font_combo.currentText()
class PackageDialog(QDialog):
    def __init__(self, parent, project_path, main_file):
        super().__init__(parent)
        self.project_path = project_path
        self.main_file = main_file
        self.setWindowTitle("Empacotar Projeto")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout(self)

        info_label = QLabel(f"Projeto: {os.path.basename(project_path)}\n"
                            f"Arquivo principal: {main_file}\n\n"
                            "Deseja empacotar como executável?")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        btn_layout = QHBoxLayout()
        self.yes_btn = QPushButton("Sim, Empacotar")
        self.yes_btn.clicked.connect(self.package_project)
        self.no_btn = QPushButton("Cancelar")
        self.no_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.yes_btn)
        btn_layout.addWidget(self.no_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def package_project(self):
        """Simula o empacotamento (expanda para PyInstaller real)"""
        try:
            # Exemplo simples: cria um ZIP ou use subprocess para PyInstaller
            output_dir = os.path.join(self.project_path, "dist")
            os.makedirs(output_dir, exist_ok=True)

            # Comando exemplo com PyInstaller (ajuste conforme necessário)
            pyinstaller_cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--distpath", output_dir,
                os.path.join(self.project_path, self.main_file)
            ]
            result = subprocess.run(pyinstaller_cmd, cwd=self.project_path, capture_output=True, text=True)

            if result.returncode == 0:
                QMessageBox.information(self, "Sucesso", f"Projeto empacotado em {output_dir}!")
            else:
                QMessageBox.warning(self, "Erro", f"Falha no empacotamento:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao empacotar: {str(e)}")

        self.accept()
class ProgressDialog(QDialog):
    """Diálogo de progresso para mostrar o carregamento"""

    def __init__(self, parent=None, title="Carregando", message="Carregando módulos..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 150)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        layout = QVBoxLayout()

        # Ícone e título
        title_layout = QHBoxLayout()
        self.icon_label = QLabel("🔄")
        self.icon_label.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(self.icon_label)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #569cd6;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Mensagem
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("color: #cccccc; margin: 10px 0;")
        layout.addWidget(self.message_label)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3c3c3c;
                border-radius: 5px;
                background-color: #1e1e1e;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #569cd6;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Contador
        self.counter_label = QLabel("0/0 módulos carregados")
        self.counter_label.setStyleSheet("color: #9cdcfe; font-size: 12px;")
        layout.addWidget(self.counter_label)

        # Botão cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #d84f4f;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e06c6c;
            }
        """)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def update_progress(self, value, message="", current=0, total=0):
        """Atualiza o progresso"""
        self.progress_bar.setValue(value)
        if message:
            self.message_label.setText(message)
        if total > 0:
            self.counter_label.setText(f"{current}/{total} módulos carregados")

    def set_icon(self, icon):
        """Muda o ícone"""
        self.icon_label.setText(icon)
class NewFileDialog(QDialog):
    """Diálogo intuitivo para novo arquivo: nome + seletor de extensão"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📄 Novo Arquivo")
        self.setFixedSize(400, 150)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Título
        title_label = QLabel("Digite o nome e selecione a extensão:")
        title_label.setStyleSheet("font-weight: bold; color: #569cd6; margin-bottom: 5px;")
        layout.addWidget(title_label)

        # Campo Nome
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nome:"))
        self.name_edit = QLineEdit("novo_arquivo")
        self.name_edit.setPlaceholderText("Ex: meu_script")
        self.name_edit.textChanged.connect(self.update_create_button)  # Habilita botão dinamicamente
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Campo Extensão (ComboBox com índice/ícones visuais)
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("Extensão:"))
        self.ext_combo = QComboBox()
        # Opções comuns com display amigável (texto + extensão)
        extensions = [
            ("Python (.py)", ".py"),
            ("JavaScript (.js)", ".js"),
            ("HTML (.html)", ".html"),
            ("CSS (.css)", ".css"),
            ("JSON (.json)", ".json"),
            ("Texto (.txt)", ".txt"),
            ("Sem extensão", "")  # Opção para arquivos sem ext.
        ]
        for display, ext in extensions:
            self.ext_combo.addItem(display, ext)  # User data = extensão real
        self.ext_combo.setCurrentIndex(0)  # Default: Python
        ext_layout.addWidget(self.ext_combo)
        layout.addLayout(ext_layout)

        # Botões
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("Criar")
        self.create_btn.clicked.connect(self.accept)
        self.create_btn.setStyleSheet("background-color: #569cd6; color: white; padding: 8px;")
        self.create_btn.setEnabled(False)  # Desabilitado até nome válido

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background-color: #d84f4f; color: white; padding: 8px;")

        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_file_name(self):
        """Retorna nome completo (nome + extensão) - VERSÃO MAIS ROBUSTA"""
        try:
            name = self.name_edit.text().strip()
            if not name:
                return None
            
            # CORREÇÃO: Remove caracteres inválidos para nome de arquivo
            import re
            name = re.sub(r'[<>:"/\\|?*]', '_', name)
            
            ext = self.ext_combo.currentData()  # Extensão real (user data)
            
            # CORREÇÃO: Verifica se ext não é None e é string válida
            if ext and isinstance(ext, str) and ext.strip():
                # Garante que a extensão comece com ponto
                if not ext.startswith('.'):
                    ext = '.' + ext
                return name + ext
            else:
                return name
                
        except Exception as e:
            print(f"Erro ao obter nome do arquivo: {e}")
            return None

    def update_create_button(self):
        """Habilita botão se nome não vazio"""
        try:
            text = self.name_edit.text().strip()
            # CORREÇÃO: Também verifica se o nome não contém apenas espaços
            is_valid = bool(text) and not text.isspace()
            self.create_btn.setEnabled(is_valid)
        except Exception as e:
            print(f"Erro ao atualizar botão: {e}")
            self.create_btn.setEnabled(False)

class LoadingWidget(QWidget):
  #  """Widget de carregamento para o autocomplete"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2d2d30;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #569cd6;
                border-radius: 3px;
            }
        """)

        # Texto de carregamento
        self.loading_label = QLabel("🔄 Carregando sugestões...")
        self.loading_label.setStyleSheet("color: #9cdcfe; font-size: 10px;")
        self.loading_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.loading_label)
        self.setLayout(layout)
        self.hide()

class ModuleCacheManager:
#    """Gerenciador de cache para módulos e métodos - MELHORADO COM CACHING DE CADEIAS E PRELOAD"""

    def __init__(self):
        self._cache_lock = threading.RLock()
        self._module_cache: Dict[str, Dict[str, Any]] = {}  # Cache principal: módulo -> {método: sub-métodos}
        self._project_modules: Dict[str, Set[str]] = {}
        self._last_scan_time: Dict[str, float] = {}
        self._scan_interval = 5.0  # Aumentado para 5s para reduzir scans frequentes
        self._chain_cache: Dict[str, Set[str]] = {}
        self._preload_done = False  # CORREÇÃO: Adicionado atributo faltante

    def preload_all_project_modules(self, project_path: str, file_path: str = None):
     #   """PRELOAD AGRESSIVO: Carrega todos os módulos do projeto uma vez"""
        if self._preload_done or not project_path:
            return

        with self._cache_lock:
            self._preload_done = True
            print("🔄 Preloading todos os módulos do projeto... (pode demorar)")

            # Encontra todos os .py no projeto
            py_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        py_files.append(os.path.join(root, file))

            # Carrega cada um
            for py_file in py_files:
                module_name = os.path.relpath(py_file, project_path).replace(os.sep, '.').rstrip('.py')
                self.get_module_methods(module_name, py_file, project_path)  # Força scan

            print("✅ Preload concluído!")

    def get_module_methods(self, module_name: str, file_path: str = None, project_path: str = None) -> Set[str]:
     #   """Obtém todos os métodos de um módulo com cache - VERSÃO OTIMIZADA"""
        with self._cache_lock:
            try:
                if not module_name or not isinstance(module_name, str):
                    return set()
                    
                cache_key = f"{module_name}:{file_path or ''}"
                format_cache_key = f"formatted:{cache_key}"

                # Verifica se precisa atualizar o cache
                current_time = time.time()
                last_scan = self._last_scan_time.get(cache_key, 0)

                if current_time - last_scan > self._scan_interval:
                    self._update_module_cache(module_name, file_path, project_path)
                    self._last_scan_time[cache_key] = current_time
                    # Limpa cache de formatação quando atualiza
                    if format_cache_key in self._module_cache:
                        del self._module_cache[format_cache_key]

                # Verifica se já tem a versão formatada em cache
                if format_cache_key in self._module_cache:
                    return self._module_cache[format_cache_key].copy()

                methods = self._module_cache.get(cache_key, set())
                
                # Formata métodos
                formatted_methods = {m if m.endswith('()') else f"{m}()" for m in methods if m}
                
                # Cache da versão formatada
                self._module_cache[format_cache_key] = formatted_methods.copy()
                
                return formatted_methods
                
            except Exception as e:
                print(f"Erro em get_module_methods para {module_name}: {e}")
                return set()

    def get_chain_methods(self, chain: str, file_path: str = None, project_path: str = None) -> Set[str]:
    #    """NOVO: Obtém métodos para uma cadeia como 'obj.method'"""
        cache_key = f"chain:{chain}:{file_path or ''}"
        if cache_key in self._chain_cache:
            return self._chain_cache[cache_key]

        # Extrai base module e subpath
        parts = chain.split('.')
        base_module = parts[0]
        sub_path = '.'.join(parts[1:])

        base_methods = self.get_module_methods(base_module, file_path, project_path)
        sub_methods = set()

        for method in base_methods:
            method_name = method.rstrip('()')
            if method_name == sub_path:
                # Encontrou o sub-método, adiciona seus filhos
                full_method_key = f"{base_module}.{method_name}"
                sub_methods.update(self._get_sub_methods(full_method_key, file_path, project_path))

        self._chain_cache[cache_key] = sub_methods
        return sub_methods

    def _get_sub_methods(self, full_method: str, file_path: str = None, project_path: str = None) -> Set[str]:
    #    """Extrai sub-métodos de um método/classe específico"""
        subs = set()
        # Para simplificação, usa padrões comuns ou análise AST mais profunda
        # Expansão futura: análise de retornos de funções para inferir tipos
        common_subs = {
            'list': ['append()', 'remove()', 'pop()', 'sort()', 'reverse()', 'index()', 'count()'],
            'dict': ['get()', 'keys()', 'values()', 'items()', 'update()', 'pop()', 'clear()'],
            'str': ['upper()', 'lower()', 'strip()', 'split()', 'join()', 'replace()', 'find()', 'startswith()'],
            'int': ['bit_length()', '__str__()', 'abs()'],
            # Adicione mais baseados em inferência
        }
        base_name = full_method.split('.')[-1].rstrip('()')
        for key, methods in common_subs.items():
            if key in base_name.lower():
                subs.update(methods)
                break
        return subs

    def _update_module_cache(self, module_name: str, file_path: str = None, project_path: str = None):
     #   """Atualiza o cache para um módulo específico - MELHORADO COM AST ROBUSTA"""
        cache_key = f"{module_name}:{file_path or ''}"
        methods = set()

        try:
            # Tenta carregar como módulo Python padrão
            if module_name in sys.builtin_module_names:
                methods.update(self._get_builtin_module_methods(module_name))

            # Tenta importar o módulo
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    methods.update(self._get_module_attributes(module))
            except:
                pass

            # Procura módulos locais no projeto
            if project_path:
                local_methods = self._scan_local_module(module_name, project_path, file_path)
                methods.update(local_methods)

            # Procura no arquivo atual
            if file_path and os.path.exists(file_path):
                current_file_methods = self._scan_file_for_imports(file_path, module_name)
                methods.update(current_file_methods)

            # Adiciona métodos comuns baseados no nome do módulo
            common_methods = self._get_common_module_methods(module_name)
            methods.update(common_methods)

        except Exception as e:
            print(f"Erro ao atualizar cache para {module_name}: {e}")

        self._module_cache[cache_key] = methods

    def _get_builtin_module_methods(self, module_name: str) -> Set[str]:
     #  """Métodos para módulos built-in - EXPANDIDO"""
        builtin_methods = {
            'os': ['path.join()', 'path.exists()', 'path.dirname()', 'path.basename()', 'mkdir()', 'listdir()', 'getcwd()', 'chdir()', 'remove()', 'rename()', 'system()', 'environ'],
            'sys': ['argv', 'path', 'exit()', 'version', 'platform', 'modules', 'executable'],
            'json': ['loads()', 'dumps()', 'load()', 'dump()'],
            're': ['search()', 'match()', 'findall()', 'sub()', 'compile()', 'IGNORECASE', 'MULTILINE'],
            'datetime': ['datetime', 'date', 'time', 'timedelta', 'now()', 'today()', 'strftime()'],
            'math': ['sqrt()', 'sin()', 'cos()', 'pi', 'e', 'log()', 'ceil()', 'floor()', 'radians()'],
            'random': ['random()', 'randint()', 'choice()', 'shuffle()', 'uniform()', 'seed()'],
            'subprocess': ['run()', 'call()', 'Popen()', 'check_output()', 'DEVNULL', 'PIPE'],
            'shutil': ['copy()', 'move()', 'rmtree()', 'which()', 'copytree()', 'make_archive()'],
            'glob': ['glob()', 'iglob()'],
            'ast': ['parse()', 'walk()', 'NodeVisitor', 'literal_eval()'],
            'inspect': ['getsource()', 'signature()', 'getmembers()', 'isfunction()', 'isclass()'],
            'importlib': ['import_module()', 'util', 'reload()'],
            'platform': ['system()', 'version()', 'machine()', 'python_version()'],
            'time': ['sleep()', 'time()', 'ctime()', 'strftime()', 'localtime()'],
            'pathlib': ['Path()', 'PurePath()'],
            'collections': ['deque()', 'Counter()', 'defaultdict()', 'namedtuple()', 'OrderedDict()'],
            'itertools': ['chain()', 'cycle()', 'combinations()', 'permutations()', 'product()'],
            'functools': ['partial()', 'reduce()', 'wraps()', 'lru_cache()'],
            'threading': ['Thread()', 'Lock()', 'Event()', 'Timer()'],
            'multiprocessing': ['Process()', 'Pool()', 'Queue()', 'Manager()'],
            'tkinter': ['Tk()', 'Button()', 'Label()', 'Entry()', 'Text()', 'filedialog', 'messagebox'],
            'PySide6': ['QtWidgets', 'QtCore', 'QtGui'],
            'PySide6.QtWidgets': ['QApplication()', 'QMainWindow()', 'QPushButton()', 'QLabel()'],
            'PySide6.QtCore': ['Qt', 'QTimer()', 'Signal()', 'Slot()'],
            'PySide6.QtGui': ['QPalette()', 'QColor()', 'QFont()']
        }
        return set(builtin_methods.get(module_name, []))

    def _get_module_attributes(self, module) -> Set[str]:
    #    """Extrai atributos de um módulo importado - MELHORADO PARA SUB-ATRIOS"""
        attrs = set()
        try:
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    attr = getattr(module, attr_name)
                    if callable(attr):
                        attrs.add(f"{attr_name}()")
                        # NOVO: Se é callable, tenta extrair sub-métodos se possível
                        if hasattr(attr, '__doc__') and 'class' in str(type(attr)).lower():
                            subs = self._extract_class_methods(attr)
                            for sub in subs:
                                attrs.add(f"{attr_name}.{sub}")
                    else:
                        attrs.add(attr_name)
        except:
            pass
        return attrs

    def _extract_class_methods(self, cls) -> Set[str]:
     #   """Extrai métodos de uma classe dinamicamente"""
        subs = set()
        for sub_name in dir(cls):
            if not sub_name.startswith('_') and callable(getattr(cls, sub_name)):
                subs.add(f"{sub_name}()")
        return subs

    def _scan_local_module(self, module_name: str, project_path: str, current_file: str = None) -> Set[str]:
     #   """Escaneia módulos locais no projeto - MELHORADO COM AST ROBUSTA"""
        methods = set()

        try:
            # Possíveis locais do módulo
            possible_paths = [
                os.path.join(project_path, f"{module_name}.py"),
                os.path.join(project_path, module_name, "__init__.py"),
                os.path.join(project_path, "src", f"{module_name}.py"),
                os.path.join(project_path, "lib", f"{module_name}.py"),
            ]

            # Se temos um arquivo atual, procura no mesmo diretório
            if current_file:
                current_dir = os.path.dirname(current_file)
                possible_paths.extend([
                    os.path.join(current_dir, f"{module_name}.py"),
                    os.path.join(current_dir, module_name, "__init__.py"),
                ])

            for module_path in possible_paths:
                if os.path.exists(module_path):
                    module_methods = self._parse_python_file_robust(module_path)
                    methods.update(module_methods)
                    break

            # Procura por imports relativos
            if current_file and '.' in module_name:
                relative_methods = self._handle_relative_imports(module_name, current_file, project_path)
                methods.update(relative_methods)

        except Exception as e:
            print(f"Erro ao escanear módulo local {module_name}: {e}")

        return methods

    def _parse_python_file_robust(self, file_path: str) -> Set[str]:
     #   """Analisa um arquivo Python com AST robusta - CORRIGIDO PARA ERROS DE INDENT"""
        methods = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Tenta AST com modo 'exec' e ignore erros de indent
            tree = None
            try:
                tree = ast.parse(content, mode='exec', filename=file_path)
            except (IndentationError, SyntaxError) as e:
                # Corrige indentação básica antes de parse - MELHORADO
                lines = content.splitlines()
                fixed_lines = []
                current_indent = 0
                for line_num, line in enumerate(lines, 1):
                    stripped = line.lstrip()
                    if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try ', 'except ', 'else:', 'elif ')):
                        # Detecta novo bloco
                        current_indent = len(line) - len(stripped)
                    elif not stripped:
                        # Linha vazia mantém indent
                        fixed_lines.append(' ' * current_indent)
                        continue
                    else:
                        # Ajusta indent se inconsistente
                        actual_indent = len(line) - len(stripped)
                        if actual_indent % 4 != 0:  # Assume 4 spaces
                            fixed_lines.append(' ' * (current_indent + (actual_indent % 4)))
                        else:
                            fixed_lines.append(line)
                    fixed_lines.append(' ' * current_indent + stripped if not line.startswith(' ' * current_indent) else line)
                fixed_content = '\n'.join(fixed_lines)
                try:
                    tree = ast.parse(fixed_content, mode='exec', filename=file_path)
                    print(f"Indentação corrigida com sucesso para {file_path}")
                except Exception as fix_e:
                    print(f"Correção de indent falhou para {file_path}: {fix_e}")
                    return self._parse_with_regex(content)
            except Exception as parse_e:
                print(f"AST ainda falhou para {file_path}: {parse_e}")
                # Fallback regex melhorado
                return self._parse_with_regex(content)

            # Visita AST
            visitor = DefinitionVisitor()
            visitor.visit(tree)
            methods.update(visitor.definitions)

        except Exception as e:
            print(f"Erro ao analisar arquivo {file_path}: {e}")
            # Fallback global
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                methods.update(self._parse_with_regex(content))
            except:
                pass

        return methods

    def _parse_with_regex(self, content: str) -> Set[str]:
#        """Fallback regex melhorado para defs, classes e assigns"""
        methods = set()
        # Funções
        functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update([f"{f}()" for f in functions])
        # Classes
        classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update(classes)
        # Atribuições de vars
        var_matches = re.findall(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=', content, re.MULTILINE)
        for indent, var in var_matches:
            if len(var) > 2 and not var.startswith('_'):
                methods.add(var)
        return methods

    def _scan_file_for_imports(self, file_path: str, target_module: str) -> Set[str]:
       # """Escaneia um arquivo específico para imports relacionados - MELHORADO COM AST ROBUSTA"""
        methods = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Análise AST robusta
            tree = None
            try:
                tree = ast.parse(content, mode='exec', filename=file_path)
            except (IndentationError, SyntaxError, Exception) as e:
                print(f"AST falhou para {file_path} (usando regex fallback): {e}")
                methods.update(self._find_imports_regex(content, target_module))
                return methods

            visitor = DefinitionVisitor()
            visitor.visit(tree)

            # Filtra imports relacionados ao target
            for imp in visitor.import_statements:
                if target_module in imp:
                    # Encontra usos
                    usage_methods = self._find_module_usage(content, target_module)
                    methods.update(usage_methods)

            # Adiciona defs locais
            methods.update(visitor.definitions)

        except Exception as e:
            print(f"Erro ao escanear imports em {file_path}: {e}")
            methods.update(self._find_imports_regex(content, target_module))

        return methods

    def _find_imports_regex(self, content: str, target_module: str) -> Set[str]:
      #  """Fallback regex para encontrar imports e métodos relacionados - MELHORADO"""
        methods = set()
        # Regex para imports
        import_patterns = [
            rf'import\s+{re.escape(target_module)}(\s+as\s+([a-zA-Z_][a-zA-Z0-9_]*))?',
            rf'from\s+{re.escape(target_module)}\s+import\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    for item in match:
                        if item and item not in ['', ' ']:
                            methods.add(item)
                else:
                    if match and match not in ['', ' ']:
                        methods.add(match)
        # Usos
        methods.update(self._find_module_usage(content, target_module))
        return methods

    def _find_module_usage(self, content: str, module_name: str, alias: str = None) -> Set[str]:
     #   """Encontra usos de um módulo no código - MELHORADO PARA CADEIAS"""
        methods = set()
        used_name = alias or module_name

        # Métodos: modulo.metodo(args)
        pattern = rf'{re.escape(used_name)}\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        matches = re.findall(pattern, content)
        methods.update([f"{match}()" for match in matches])

        # Atributos: modulo.attr
        attr_pattern = rf'{re.escape(used_name)}\.([a-zA-Z_][a-zA-Z0-9_]*)(?![a-zA-Z0-9_])'
        attr_matches = re.findall(attr_pattern, content)
        methods.update(attr_matches)

        # NOVO: Cadeias como modulo.method.submethod
        chain_pattern = rf'{re.escape(used_name)}\.([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
        chain_matches = re.findall(chain_pattern, content)
        for base, sub in chain_matches:
            methods.add(f"{base}.{sub}()")

        return methods

    def _handle_relative_imports(self, module_name: str, current_file: str, project_path: str) -> Set[str]:
#        """Lida com imports relativos - MELHORADO"""
        methods = set()

        try:
            current_dir = os.path.dirname(current_file)
            relative_parts = module_name.split('.')

            if relative_parts[0] == '':
                relative_parts = relative_parts[1:]
                base_path = current_dir
            else:
                base_path = project_path

            abs_path = os.path.join(base_path, *relative_parts[:-1])
            target_module = relative_parts[-1]

            module_files = [
                os.path.join(abs_path, f"{target_module}.py"),
                os.path.join(abs_path, target_module, "__init__.py")
            ]

            for module_file in module_files:
                if os.path.exists(module_file):
                    module_methods = self._parse_python_file_robust(module_file)
                    methods.update(module_methods)
                    break

        except Exception as e:
            print(f"Erro com import relativo {module_name}: {e}")

        return methods

    def _get_common_module_methods(self, module_name: str) -> Set[str]:
#        """Métodos comuns baseados em padrões de nomes de módulos"""
        common_patterns = {
            'utils': ['helper()', 'utility()', 'format()', 'validate()', 'parse()'],
            'config': ['load()', 'save()', 'get()', 'set()', 'update()'],
            'database': ['connect()', 'query()', 'insert()', 'update()', 'delete()', 'commit()'],
            'api': ['request()', 'get()', 'post()', 'put()', 'delete()', 'authenticate()'],
            'handler': ['handle()', 'process()', 'execute()', 'run()'],
            'manager': ['create()', 'read()', 'update()', 'delete()', 'list()', 'find()'],
            'service': ['execute()', 'process()', 'handle()', 'run()']
        }

        for pattern, methods in common_patterns.items():
            if pattern in module_name.lower():
                return set(methods)

        return set()

    def clear_cache(self, module_name: str = None):
     #   """Limpa o cache, opcionalmente para um módulo específico"""
        with self._cache_lock:
            if module_name:
                keys_to_remove = [k for k in self._module_cache.keys() if k.startswith(module_name)]
                for key in keys_to_remove:
                    self._module_cache.pop(key, None)
                    self._last_scan_time.pop(key, None)
                self._chain_cache.clear()
            else:
                self._module_cache.clear()
                self._last_scan_time.clear()
                self._chain_cache.clear()
            self._preload_done = False

    def force_rescan(self, module_name: str, file_path: str = None):
   #     """Força uma reanálise do módulo"""
        cache_key = f"{module_name}:{file_path or ''}"
        self._last_scan_time.pop(cache_key, None)
        self._module_cache.pop(cache_key, None)
        self._chain_cache.clear()  # Limpa chains relacionadas

class AutoCompleteWorker(QThread):
    finished = Signal(list)  # suggestions
    progress = Signal(str)  # progress update
    loading_state = Signal(bool)  # True=loading, False=done

    def __init__(self, text, cursor_position, file_path, project_path, selected_text=""):
        super().__init__()
        self.text = text
        self.cursor_position = cursor_position
        self.file_path = file_path
        self.project_path = project_path
        self.selected_text = selected_text
        self._is_running = True
        # Cache para melhor performance
        self._keyword_cache = None
        self._builtin_cache = None
        self._module_cache = {}  # Cache para módulos

    def stop(self):
        self._is_running = False
        self.terminate()

    def run(self):
        if not self._is_running:
            return

        try:
            # Emite sinal de carregamento
            self.loading_state.emit(True)
            self.progress.emit("🔍 Analisando código...")

            # Preload se não feito
            module_cache_manager.preload_all_project_modules(self.project_path, self.file_path)

            # Resposta ultra-rápida com cache
            suggestions = self.get_instant_suggestions()

            if self._is_running:
                self.progress.emit("✅ Sugestões carregadas!")
                self.loading_state.emit(False)
                self.finished.emit(suggestions)

        except Exception as e:
            if self._is_running:
                self.progress.emit(f"❌ Erro: {str(e)}")
                self.loading_state.emit(False)
                self.finished.emit([])

    def get_instant_suggestions(self):
    #    """Sugestões instantâneas com suporte multi-linguagem"""
        suggestions = set()

        # Determina a linguagem atual
        language = self.detect_language()

        # 1. Sugestões da sintaxe da linguagem
        syntax_suggestions = language_syntax_manager.get_suggestions(language)
        suggestions.update(syntax_suggestions)

        # 2. Contexto básico
        lines = self.text[:self.cursor_position].split('\n')
        current_line = lines[-1] if lines else ""
        current_word = self.get_current_word_fast(current_line)

        # 3. Para Python, usa o cache manager
        if language == 'python':
            # Palavras-chave com cache
            if self._keyword_cache is None:
                self._keyword_cache = self.get_all_keywords()
            suggestions.update(self._keyword_cache)

            # Built-ins com cache
            if self._builtin_cache is None:
                self._builtin_cache = self.get_all_builtins()
            suggestions.update(self._builtin_cache)

            # Análise local
            self.progress.emit("📝 Analisando definições locais...")
            local_defs = self.get_local_definitions_instant()
            suggestions.update(local_defs)

            # Módulos importados
            self.progress.emit("📦 Analisando imports...")
            module_suggestions = self.get_module_suggestions_fast(current_word)
            suggestions.update(module_suggestions)

        # 4. Para outras linguagens, usa sintaxe específica
        else:
            self.progress.emit(f"🔍 Analisando {language}...")
            lang_specific = self.get_language_specific_suggestions(language, current_word)
            suggestions.update(lang_specific)

        # 5. Filtro por palavra atual
        if current_word:
            if '.' in current_word:
                # Cadeia: usa syntax manager
                chain_base = current_word.rsplit('.', 1)[0]
                chain_methods = language_syntax_manager.get_chain_suggestions(language, chain_base)
                filtered = [s for s in chain_methods if s.lower().startswith(current_word.lower().rsplit('.', 1)[1])]
                suggestions.update(filtered)
            else:
                filtered = [s for s in suggestions if s.lower().startswith(current_word.lower())]
                suggestions = set(filtered)

        return sorted(list(suggestions))[:20]

    def detect_language(self) -> str:
    #    """Detecta a linguagem baseada na extensão do arquivo"""
        if not self.file_path:
            return 'python'  # default

        ext = os.path.splitext(self.file_path)[1].lower()

        language_map = {
            '.py': 'python',
            '.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript',
            '.html': 'html', '.htm': 'html',
            '.css': 'css', '.scss': 'css', '.sass': 'css',
            '.sql': 'sql',
            '.java': 'java',
            '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp', '.h': 'cpp', '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin', '.kts': 'kotlin',
            '.ts': 'typescript', '.tsx': 'typescript',
            '.yaml': 'yaml', '.yml': 'yaml',
            '.xml': 'xml',
            '.md': 'markdown'
        }

        return language_map.get(ext, 'python')

    def get_language_specific_suggestions(self, language: str, current_word: str) -> Set[str]:
       # """Sugestões específicas para cada linguagem"""
        suggestions = set()

        if language == 'html':
            # Sugere tags e atributos baseados no contexto
            if current_word.startswith('<'):
                suggestions.update(language_syntax_manager.syntax_data['html']['tags'])
            elif '=' in current_line:
                suggestions.update(language_syntax_manager.syntax_data['html']['attributes'].get('global', []))

        elif language == 'css':
            # Sugere propriedades e valores
            if current_line.strip().endswith(':'):
                suggestions.update(language_syntax_manager.syntax_data['css']['values'].get('color', []))
                suggestions.update(language_syntax_manager.syntax_data['css']['values'].get('size', []))
            else:
                suggestions.update(language_syntax_manager.syntax_data['css']['properties'])

        elif language == 'javascript':
            # Sugere APIs globais e métodos
            suggestions.update(language_syntax_manager.syntax_data['javascript']['global_functions'])

        return suggestions

    def get_module_suggestions_fast(self, current_word: str = ""):
       # """Sugestões de módulos importados com cache - CORRIGIDO"""
        suggestions = set()

        try:
            # Analisa imports no código
            imports = self.parse_imports_fast()

            for module_name in imports:
                # Usa o cache manager para obter métodos
                self.progress.emit(f"📚 Carregando {module_name}...")
                module_methods = module_cache_manager.get_module_methods(
                    module_name,
                    self.file_path,
                    self.project_path
                )
                suggestions.update(module_methods)

                # Também adiciona o próprio nome do módulo
                suggestions.add(module_name)

                # Se current_word tem ., sugere chains - CORREÇÃO: verificação segura
                if '.' in current_word and current_word.startswith(module_name + '.'):
                    chain = current_word.split('.', 1)[0]
                    try:
                        chain_methods = module_cache_manager.get_chain_methods(chain, self.file_path, self.project_path)
                        suggestions.update(chain_methods)
                    except Exception as e:
                        print(f"Erro em chain methods para {chain}: {e}")
                        # Fallback: métodos comuns baseados no padrão
                        fallback_methods = self._get_fallback_chain_methods(chain)
                        suggestions.update(fallback_methods)

        except Exception as e:
            print(f"Erro em get_module_suggestions_fast: {e}")

        return suggestions

    def _get_fallback_chain_methods(self, chain: str) -> Set[str]:
#        """Fallback para quando o chain method falha"""
        common_chains = {
            'os.path': ['join()', 'exists()', 'dirname()', 'basename()', 'abspath()'],
            'sys.path': ['append()', 'insert()', 'remove()'],
            'json.dumps': ['encode()'],
            'json.loads': ['decode()'],
            're.compile': ['match()', 'search()', 'findall()', 'sub()'],
            'datetime.datetime': ['now()', 'today()', 'strftime()', 'strptime()'],
        }
        return set(common_chains.get(chain, []))

    def parse_imports_fast(self):
     #   """Analisa imports de forma rápida com regex - VERSÃO MAIS ROBUSTA"""
        imports = set()

        try:
            # CORREÇÃO: Garante que self.text é string e remove None
            text_content = str(self.text) if self.text is not None else ""

            # Padrões regex para imports
            import_patterns = [
                r'import\s+([a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import',
                r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, text_content)
                for match in matches:
                    if isinstance(match, tuple):
                        for item in match:
                            # CORREÇÃO: Filtra melhor os resultados
                            if (item and 
                                isinstance(item, str) and 
                                item.strip() and 
                                item not in ['', ' ', '.']):
                                clean_item = item.strip()
                                # Adiciona apenas o primeiro componente para módulos aninhados
                                if '.' in clean_item:
                                    base_module = clean_item.split('.')[0]
                                    imports.add(base_module)
                                else:
                                    imports.add(clean_item)
                    else:
                        # CORREÇÃO: Tratamento para match único
                        if (match and 
                            isinstance(match, str) and 
                            match.strip() and 
                            match not in ['', ' ', '.']):
                            clean_match = match.strip()
                            if '.' in clean_match:
                                base_module = clean_match.split('.')[0]
                                imports.add(base_module)
                            else:
                                imports.add(clean_match)

            # CORREÇÃO: Remove duplicatas e módulos vazios
            imports = {imp for imp in imports if imp and not imp.isspace()}

        except Exception as e:
            print(f"Erro ao analisar imports: {e}")
            imports = set()

        return imports

    def get_current_word_fast(self, current_line):
    #    """Extrai palavra atual de forma ultra-rápida - CORRIGIDO"""
        if not current_line or not current_line.strip():
            return ""

        # CORREÇÃO: Garante que current_line é string
        current_line_str = str(current_line)
        
        # Busca reversa simples para palavra completa incluindo chains
        line = current_line_str[:current_line_str.rfind(' ')+1 if ' ' in current_line_str else len(current_line_str)].rstrip()

        # Extrai a última palavra ou chain antes do cursor
        words = re.split(r'[\s\(\)\[\]\{\}]', line)
        if words:
            last_word = words[-1].rstrip() if words[-1] else ""
            if last_word and last_word.endswith('.'):
                # Para "os." retorna "os." para sugerir métodos
                return last_word
            return last_word
        return ""

    def get_selected_suggestions_fast(self, selected_text):
    #    """Sugestões rápidas para texto selecionado"""
        selected_clean = selected_text.strip()
        suggestions = []

        if not selected_clean:
            return suggestions

        # Resposta instantânea baseada no tipo
        if selected_clean.replace('.', '').replace('-', '').isdigit():
            # Número
            suggestions = [
                f"abs({selected_clean})",
                f"round({selected_clean})",
                f"str({selected_clean})",
                f"int({selected_clean})",
            ]
        elif selected_clean.startswith(('"', "'")):
            # String
            suggestions = [
                f"len({selected_clean})",
                f"str({selected_clean})",
                f"{selected_clean}.upper()",
                f"{selected_clean}.lower()",
                f"{selected_clean}.strip()",
                f"{selected_clean}.split()",
            ]
        elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', selected_clean):
            # Variável/função
            suggestions = [
                f"len({selected_clean})",
                f"str({selected_clean})",
                f"int({selected_clean})",
                f"float({selected_clean})",
                f"print({selected_clean})",
                f"type({selected_clean})",
            ]

        return suggestions[:8]

    def get_local_definitions_instant(self):
      #  """Extrai definições locais instantaneamente com regex - MELHORADO"""
        definitions = set()

        # Regex ultra-rápidas para funções e classes
        func_matches = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', self.text)
        class_matches = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', self.text)
        var_matches = re.findall(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=', self.text, re.MULTILINE)

        definitions.update([f"{f}()" for f in func_matches])
        definitions.update(class_matches)

        # Filtra variáveis para evitar muito ruído
        for _, var in var_matches:
            if len(var) > 2 and not var.startswith('_'):  # Filtra variáveis muito curtas e privadas
                definitions.add(var)

        return definitions

    def get_all_keywords(self):
#        """Todas palavras-chave Python"""
        return {
            "if", "else", "elif", "for", "while", "break", "continue", "pass", "return",
            "try", "except", "finally", "raise", "def", "class", "lambda", "global",
            "nonlocal", "import", "from", "as", "and", "or", "not", "in", "is",
            "True", "False", "None", "with", "yield", "assert", "del", "async", "await"
        }

    def get_all_builtins(self):
   #     """Built-ins mais comuns"""
        return {
            "print", "len", "str", "int", "float", "list", "dict", "set", "tuple",
            "range", "input", "open", "type", "sum", "min", "max", "abs", "round",
            "sorted", "reversed", "enumerate", "zip", "map", "filter", "any", "all",
            "bool", "chr", "ord", "dir", "help", "id", "isinstance", "issubclass",
            "getattr", "setattr", "hasattr", "vars", "locals", "globals"
        }

    def get_import_suggestions(self):
        #"""Sugestões para imports"""
        common_modules = [
            'os', 'sys', 'json', 'tkinter', 're', 'datetime', 'math', 'random',
            'subprocess', 'shutil', 'glob', 'ast', 'inspect', 'importlib',
            'platform', 'time', 'pathlib', 'collections', 'itertools', 'functools'
        ]
        return common_modules

    def get_context_suggestions(self, current_line, current_word):
        #"""Sugestões baseadas no contexto - MELHORADO PARA CADEIAS"""
        suggestions = set()
        # Sugestões comuns baseadas em palavra atual
        context_map = {
            'if': ['else', 'elif'],
            'for': ['in', 'range', 'enumerate'],
            'def': ['pass', 'return'],
            'class': ['def', 'pass'],
            'import': ['os', 'sys', 'json'],
            '.': ['append()', 'get()', 'upper()', 'lower()']  # Comum após ponto
        }
        for key, vals in context_map.items():
            if key in current_word.lower():
                suggestions.update(vals)
        return suggestions

# Instância global do gerenciador de cache
module_cache_manager = ModuleCacheManager()


class DefinitionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.definitions = set()
        self.imported_modules = set()
        self.current_class = None
        self.import_statements = []  # Armazena imports para análise posterior

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.definitions.add(node.name)
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class:
            self.definitions.add(f"{self.current_class}.{node.name}()")
        else:
            self.definitions.add(f"{node.name}()")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if self.current_class:
            self.definitions.add(f"{self.current_class}.{node.name}()")
        else:
            self.definitions.add(f"{node.name}()")
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.definitions.add(target.id)
            elif isinstance(target, ast.Attribute):
                self.definitions.add(f"{target.value.id}.{target.attr}" if isinstance(target.value, ast.Name) else target.attr)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            self.definitions.add(node.target.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            self.definitions.add(module_name)
            self.imported_modules.add(module_name)
            self.import_statements.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.definitions.add(node.module)
            self.imported_modules.add(node.module)
            self.import_statements.append(f"from {node.module} import ...")
        for alias in node.names:
            self.definitions.add(alias.name)
        self.generic_visit(node)


class ErrorData(QTextBlockUserData):
    def __init__(self, errors=None):
        super().__init__()
        self.errors = errors or []








class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(70)  # Increased width for better alignment

    def update_line_numbers(self):
        self.update()

    def update_line_numbers_area(self, rect, dy):
        if dy:
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())
        if rect.contains(self.editor.viewport().rect()):
            self.update_line_numbers()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(20, 30, 48))  # Match dark theme
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + int(self.editor.blockBoundingRect(block).height())
        font = self.editor.font()
        font.setPointSize(10)
        painter.setFont(font)
        font_metrics = self.editor.fontMetrics()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(150, 150, 150))  # Light gray for line numbers
                painter.drawText(0, top, 50, font_metrics.height(), Qt.AlignRight, number)

                # Draw vertical separator
                painter.setPen(QColor(100, 100, 100))  # Gray vertical line
                painter.drawLine(55, top, 55, bottom)

                # Draw red line for errors
                data = block.userData()
                if isinstance(data, ErrorData) and any(error['type'] == 'error' for error in data.errors):
                    painter.setPen(QColor(255, 0, 0))  # Red line for errors
                    painter.drawLine(60, top, 60, bottom)

            block = block.next()
            top = bottom
            bottom = top + int(self.editor.blockBoundingRect(block).height())
            block_number += 1


class AutoCompleteWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip)
        self.setMaximumHeight(120)  # Reduzido para ser menos intrusivo
        self.setMaximumWidth(300)
        self.current_editor = None

        # Estilo otimizado para performance
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def show_suggestions(self, editor, suggestions):
        self.current_editor = editor
        self.clear()

        if not suggestions:
            self.hide()
            return

        # Adiciona sugestões rapidamente
        for suggestion in suggestions[:8]:  # Apenas 8 sugestões para resposta rápida
            self.addItem(suggestion)

        # Posicionamento otimizado
        cursor_rect = editor.cursorRect()
        pos = editor.mapToGlobal(cursor_rect.bottomLeft())
        self.move(pos)
        self.show()
        self.setCurrentRow(0)  # Seleciona primeiro item
        self.setFocus()

    def insert_completion(self, completion):
        if not self.current_editor:
            return

        cursor = self.current_editor.textCursor()
        cursor.insertText(completion)
        self.hide()




class LinterWorker(QThread):
    finished = Signal(dict, list)  # errors, messages

    def __init__(self, file_path, python_exec, project_path):
        super().__init__()
        self.file_path = file_path
        self.python_exec = python_exec
        self.project_path = project_path
        self._is_running = True

    def stop(self):
        self._is_running = False
        self.terminate()

    def run(self):
        if not self._is_running or not self.file_path:
            return

        errors = {}
        lint_messages = []

        try:
            # Try pylint first with corrected enables
            pylint_cmd = [
                self.python_exec, '-m', 'pylint',
                '--output-format=json',
                '--reports=n',  # No reports
                '--disable=all',
                '--enable=E,W,fatal',
                self.file_path
            ]

            cwd = self.project_path if self.project_path else os.path.dirname(self.file_path)
            result = subprocess.run(
                pylint_cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                timeout=5  # Reduced timeout
            )

            if result.returncode in [0, 1, 2, 4, 8, 16, 32] and result.stdout.strip():
                try:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if not self._is_running:
                            return
                        if line.strip():
                            try:
                                issue = json.loads(line.strip())
                                if 'line' in issue and issue['line'] > 0:
                                    line_num = issue['line'] - 1
                                    msg = issue.get('message', 'No message')
                                    symbol = issue.get('symbol', 'unknown')
                                    msg_type = issue.get('type', 'warning')
                                    error_type = 'error' if msg_type == 'error' else 'warning'

                                    if line_num not in errors:
                                        errors[line_num] = []
                                    errors[line_num].append({
                                        'type': error_type,
                                        'msg': msg,
                                        'symbol': symbol
                                    })
                                    lint_messages.append(f"Line {issue['line']}: {msg} ({symbol})")
                            except json.JSONDecodeError:
                                continue
                except json.JSONDecodeError:
                    pass  # Silently ignore JSON errors

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Silently fail - we don't want to spam messages for missing linters
            pass

        if self._is_running:
            self.finished.emit(errors, lint_messages)




class Minimap(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Monospace", 4))
        self.setWordWrapMode(QTextOption.NoWrap)


class ProblemsDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        super().paint(painter, option, index)
        data = index.data(Qt.UserRole)
        if data:
            error_type = data.get('type', 'info')
            color = QColor("red") if error_type == 'error' else QColor("yellow") if error_type == 'warning' else QColor(
                "blue")
            painter.setPen(color)
            painter.drawText(option.rect.x() + 5, option.rect.bottom() - 5, "●")




class TerminalTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_start = 0
        self.setFont(QFont("Monospace", 10))
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        # Histórico de comandos
        self.history = []
        self.history_index = -1

        # Configurar prompt inicial
        self.setPlainText(">>> ")
        self.input_start = 4  # Posição após ">>> "

        # Mover cursor para o final
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

    def append_output(self, output):
      #  """Adiciona saída ao terminal - MÉTODO ADICIONADO"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.insertPlainText(output)

        # Atualiza input_start
        self.input_start = len(self.toPlainText())

        # Move cursor para o final
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

        # Rola para baixo
        self.ensureCursorVisible()

    def keyPressEvent(self, event: QKeyEvent):
        cursor = self.textCursor()
        cursor_position = cursor.position()

        # Impede edição antes do input_start
        if cursor_position < self.input_start and event.key() not in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Up,
                                                                      Qt.Key_Down]:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            event.accept()
            return

        # Enter - executa comando
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.execute_command()
            event.accept()
            return

        # Setas para navegar no histórico
        elif event.key() == Qt.Key_Up:
            self.navigate_history(-1)
            event.accept()
            return
        elif event.key() == Qt.Key_Down:
            self.navigate_history(1)
            event.accept()
            return

        # Ctrl+C - interrompe processo
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self.interrupt_process()
            event.accept()
            return

        # Ctrl+L - limpa terminal
        elif event.key() == Qt.Key_L and event.modifiers() == Qt.ControlModifier:
            self.clear_terminal()
            event.accept()
            return

        # Backspace - impede apagar o prompt
        elif event.key() == Qt.Key_Backspace:
            if cursor_position > self.input_start:
                super().keyPressEvent(event)
            event.accept()
            return

        # Delete - impede apagar o prompt
        elif event.key() == Qt.Key_Delete:
            if cursor_position >= self.input_start:
                super().keyPressEvent(event)
            event.accept()
            return

        # Teclas normais - apenas se estiver após o prompt
        elif cursor_position >= self.input_start:
            super().keyPressEvent(event)

        else:
            # Move para o final se tentar digitar antes do prompt
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)

    def execute_command(self):
      #  """Executa o comando atual"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        command_line = cursor.selectedText().strip()

        # Remove o prompt se existir
        if command_line.startswith(">>> "):
            command = command_line[4:]
        else:
            command = command_line

        if command:
            # Adiciona ao histórico
            self.history.append(command)
            self.history_index = len(self.history)

            # Executa o comando
            self.run_command(command)

        # Novo prompt
        self.append_output("\n>>> ")

    def run_command(self, command):
       # """Executa um comando no shell"""
        try:
            ide = self.get_ide()
            if ide and ide.shell_process:
                # Envia o comando para o processo do shell
                ide.shell_process.write(f"{command}\n".encode())
        except Exception as e:
            self.append_output(f"\nErro: {str(e)}")

    def navigate_history(self, direction):
       # """Navega pelo histórico de comandos"""
        if not self.history:
            return

        new_index = self.history_index + direction

        if 0 <= new_index < len(self.history):
            self.history_index = new_index
            self.replace_current_line(self.history[self.history_index])
        elif new_index == len(self.history):
            self.history_index = new_index
            self.replace_current_line("")

    def replace_current_line(self, text):
      #  """Substitui a linha atual por novo texto"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.insertText(f">>> {text}")

        # Move cursor para o final
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.input_start = len(self.toPlainText()) - len(text)

    def interrupt_process(self):
  #      """Interrompe o processo atual (Ctrl+C)"""
        try:
            ide = self.get_ide()
            if ide and ide.shell_process:
                # Envia sinal de interrupção
                if os.name == 'nt':  # Windows
                    ide.shell_process.kill()
                else:  # Linux/Mac
                    ide.shell_process.terminate()

                self.append_output("\n^C")
                # Reinicia o shell
                self.restart_shell()
        except Exception as e:
            self.append_output(f"\nErro ao interromper: {str(e)}")

    def clear_terminal(self):
      #  """Limpa o terminal (Ctrl+L)"""
        self.clear()
        self.setPlainText(">>> ")
        self.input_start = 4
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

    def restart_shell(self):
    #    """Reinicia o processo do shell"""
        try:
            ide = self.get_ide()
            if ide:
                # Para processo atual
                if ide.shell_process and ide.shell_process.state() == QProcess.Running:
                    ide.shell_process.terminate()
                    ide.shell_process.waitForFinished(1000)

                # Inicia novo processo
                ide.shell_process = QProcess(ide)
                ide.shell_process.readyReadStandardOutput.connect(ide.handle_terminal_output)
                ide.shell_process.readyReadStandardError.connect(ide.handle_terminal_error)

                if os.name == 'nt':  # Windows
                    ide.shell_process.start("cmd.exe")
                else:  # Linux/Mac
                    ide.shell_process.start("/bin/bash", ["-i"])

                # Configura diretório do projeto se existir
                if ide.project_path:
                    ide.activate_project()

                self.append_output("\nShell reiniciado\n>>> ")

        except Exception as e:
            self.append_output(f"\nErro ao reiniciar shell: {str(e)}")

    def get_ide(self):
      #  """Encontra a instância do IDE pai"""
        parent = self.parent()
        while parent and not isinstance(parent, IDE):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent


# Classe PackageDialog adicionada para corrigir o erro




class StatusBarProgress(QWidget):
   # """Widget de progresso para a barra de status - CORRIGIDO"""

    def __init__(self, parent=None):
        super().__init__(parent)  # CORREÇÃO: Chamar __init__ da classe base
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        # Ícone
        self.icon_label = QLabel("🔄")
        self.icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.icon_label)

        # Texto
        self.text_label = QLabel("Carregando...")
        self.text_label.setStyleSheet("color: #9cdcfe; font-size: 12px;")
        layout.addWidget(self.text_label)

        # Barra de progresso pequena
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QProgressBar::chunk {
                background-color: #569cd6;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Botão fechar
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d84f4f;
                color: white;
                border-radius: 2px;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)
        self.hide()

    def update_progress(self, value, message=""):
       # """Atualiza o progresso"""
        self.progress_bar.setValue(value)
        if message:
            self.text_label.setText(message)

    def show_loading(self, message="Carregando..."):
    #    """Mostra o widget de carregamento"""
        self.icon_label.setText("🔄")
        self.text_label.setText(message)
        self.progress_bar.setValue(0)
        self.show()

    def show_success(self, message="Concluído!"):
       # """Mostra sucesso"""
        self.icon_label.setText("✅")
        self.text_label.setText(message)
        self.progress_bar.setValue(100)
        QTimer.singleShot(2000, self.hide)  # Esconde após 2 segundos

    def show_error(self, message="Erro!"):
       # """Mostra erro"""
        self.icon_label.setText("❌")
        self.text_label.setText(message)
        self.progress_bar.setValue(0)
        QTimer.singleShot(3000, self.hide)  # Esconde após 3 segundos


# NOVO: Visitor para relações de classe
class ClassRelationVisitor(ast.NodeVisitor):
   # """Visitor para detectar relações entre classes e métodos"""

    def __init__(self):
        self.classes = set()
        self.methods = {}
        self.current_class = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.classes.add(node.name)
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class:
            if self.current_class not in self.methods:
                self.methods[self.current_class] = set()
            self.methods[self.current_class].add(node.name)
        self.generic_visit(node)


class SafeDefinitionVisitor(ast.NodeVisitor):
    #"""Visitor AST seguro com tratamento de erros"""

    def __init__(self):
        self.definitions = set()

    def visit_ClassDef(self, node):
        try:
            self.definitions.add(node.name)
            self.generic_visit(node)
        except:
            pass

    def visit_FunctionDef(self, node):
        try:
            self.definitions.add(f"{node.name}()")
            self.generic_visit(node)
        except:
            pass

    def visit_Import(self, node):
        try:
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                self.definitions.add(module_name)
            self.generic_visit(node)
        except:
            pass

    def visit_ImportFrom(self, node):
        try:
            if node.module:
                self.definitions.add(node.module)
            for alias in node.names:
                self.definitions.add(alias.name)
            self.generic_visit(node)
        except:
            pass


# ===== SISTEMA DE DEBUG CORRIGIDO =====

class DebugWorker(QThread):
   # """Worker para execução de debug em thread separada"""
    output_received = Signal(str)
    finished = Signal(int)  # return code

    def __init__(self, python_exec, file_path, project_path):
        super().__init__()
        self.python_exec = python_exec
        self.file_path = file_path
        self.project_path = project_path
        self.process = None
        self._is_running = True

    def stop(self):
     #   """Para a execução do debug"""
        self._is_running = False
        if self.process:
            self.process.terminate()
        self.terminate()

    def run(self):
#        """Executa o debug em thread separada"""
        try:
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.on_finished)

            # Comando para debug interativo
            cmd = [self.python_exec, "-m", "pdb", self.file_path]

            self.process.start(cmd[0], cmd[1:])
            self.process.setWorkingDirectory(self.project_path or os.path.dirname(self.file_path))

            # Aguarda o processo terminar
            if self.process.waitForStarted():
                while self._is_running and self.process.state() == QProcess.Running:
                    self.msleep(100)

        except Exception as e:
            self.output_received.emit(f"❌ Erro no debug: {str(e)}")

    def handle_stdout(self):
 #       """Processa saída padrão"""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        if data:
            self.output_received.emit(data)

    def handle_stderr(self):
     #   """Processa erro padrão"""
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        if data:
            self.output_received.emit(data)

    def on_finished(self, exit_code, exit_status):
#        """Processa término do processo"""
        self.finished.emit(exit_code)

    def send_command(self, command):
    #    """Envia comando para o processo de debug"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.write(f"{command}\n".encode())


class DebugTerminal(TerminalTextEdit):
#    """Terminal especializado para debug"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.debug_worker = None
        self.setStyleSheet("""
            DebugTerminal {
                background-color: #1e1e1e;
                color: #ce9178;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)

        # Comandos específicos do debug
        self.debug_commands = {
            'n': 'next', 's': 'step', 'c': 'continue', 'q': 'quit',
            'l': 'list', 'p': 'print', 'pp': 'pprint', 'w': 'where',
            'b': 'break', 'cl': 'clear', 'r': 'return'
        }

    def start_debug(self, python_exec, file_path, project_path):
     #   """Inicia sessão de debug"""
        self.clear()
        self.append_output(f"🐛 Iniciando debug: {os.path.basename(file_path)}\n")
        self.append_output("Comandos: n(next), s(step), c(continue), q(quit), l(list), p(print), b(break)\n")
        self.append_output("-" * 50 + "\n")

        self.debug_worker = DebugWorker(python_exec, file_path, project_path)
        self.debug_worker.output_received.connect(self.append_output)
        self.debug_worker.finished.connect(self.on_debug_finished)
        self.debug_worker.start()

        self.input_start = len(self.toPlainText())

    def on_debug_finished(self, exit_code):
    #    """Processa término do debug"""
        self.append_output(f"\n🔚 Sessão de debug finalizada (código: {exit_code})\n")
        self.debug_worker = None

    def execute_command(self):
#        """Executa comando no debug"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        command_line = cursor.selectedText().strip()

        if command_line and self.debug_worker:
            # Processa comandos abreviados
            clean_command = command_line.strip()
            if clean_command in self.debug_commands:
                full_command = self.debug_commands[clean_command]
                self.append_output(f"Executando: {full_command}\n")
                self.debug_worker.send_command(full_command)
            else:
                self.debug_worker.send_command(clean_command)

            # Novo prompt
            self.append_output("\n(Pdb) ")
        else:
            self.append_output("\n(Pdb) ")

    def keyPressEvent(self, event: QKeyEvent):
    #    """Override para comandos de debug"""
        if self.debug_worker and event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.execute_command()
            event.accept()
            return

        # Atalhos para comandos comuns de debug
        if self.debug_worker and event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_N:  # Ctrl+N - next
                self.debug_worker.send_command("next")
                self.append_output("\nnext\n")
                event.accept()
                return
            elif event.key() == Qt.Key_S:  # Ctrl+S - step
                self.debug_worker.send_command("step")
                self.append_output("\nstep\n")
                event.accept()
                return
            elif event.key() == Qt.Key_C:  # Ctrl+C - continue
                self.debug_worker.send_command("continue")
                self.append_output("\ncontinue\n")
                event.accept()
                return
            elif event.key() == Qt.Key_Q:  # Ctrl+Q - quit
                self.debug_worker.send_command("quit")
                self.append_output("\nquit\n")
                event.accept()
                return

        super().keyPressEvent(event)

    def stop_debug(self):
      #  """Para a sessão de debug"""
        if self.debug_worker:
            self.debug_worker.stop()
            self.debug_worker.wait(1000)
            self.append_output("\n⏹️ Debug interrompido\n")

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 🔧 CORREÇÃO CRÍTICA: Inicializar TODAS as variáveis ANTES de setup_ui()
        self._initialize_variables()
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()

        # Configuração global de exceções
        def exception_hook(exctype, value, tb):
            print("ERRO GLOBAL:", exctype, value)
            traceback.print_exception(exctype, value, tb)
            sys.__excepthook__(exctype, value, tb)
        sys.excepthook = exception_hook

    def _initialize_variables(self):
        """🔧 INICIALIZAÇÃO SEGURA: Define TODAS as variáveis com valores padrão"""
        # Variáveis de estado - CORREÇÃO: Nunca deixar como None se serão usadas em strings
        self.current_file = ""  # Em vez de None
        self.project_path = ""  # Em vez de None
        self.python_path = sys.executable
        self.venv_path = ""  # Em vez de None
        self.current_font = "Consolas"
        self.clipboard_path = ""  # Em vez de None
        self.is_cut = False

        # Componentes da UI - CORREÇÃO: Inicializar antes de usar
        self.problems_list = None
        self.file_model = None
        self.file_tree = None
        self.tab_widget = None
        self.output_tabs = None
        self.terminal_text = None
        self.output_text = None
        self.debug_text = None
        self.errors_text = None
        self.lint_text = None
        self.minimap = None
        
        # Barra de status
        self.file_info_label = None
        self.cursor_info_label = None
        self.project_info_label = None
        self.status_progress = None
        
        # Processos - CORREÇÃO: Inicializar antes de start_shell()
        self.shell_process = None
        self.debug_process = None
        self.process_lock = threading.Lock()

    def setup_ui(self):
        """Configura a interface do usuário de forma otimizada"""
        self.setWindowTitle("Py Dragon Studio IDE")
        self.setGeometry(100, 100, 1400, 900)

        # 🔧 CORREÇÃO: NÃO redefinir variáveis aqui - usar as já inicializadas
        # As variáveis já foram inicializadas em _initialize_variables()

        # Tema escuro otimizado
        self.set_dark_theme_optimized()

        # Layout principal
        self.setup_central_widget()
        self.setup_docks()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()

        # Inicialização de componentes
        self.start_shell()
        self.check_python_version()

    def setup_central_widget(self):
        """Configura o widget central com tabs"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2d2d30;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 2px solid #569cd6;
            }
            QTabBar::tab:hover {
                background-color: #383838;
            }
        """)

        self.setCentralWidget(self.tab_widget)

    def setup_docks(self):
        """Configura os docks de forma organizada"""
        # Dock esquerdo - Explorer e Problems
        self.setup_left_dock()

        # Dock direito - Minimap
        self.setup_right_dock()

        # Dock inferior - Output e Terminal
        self.setup_bottom_dock()

    def setup_left_dock(self):
        """Configura o dock esquerdo com Explorer e Problems"""
        left_dock = QDockWidget("Explorer", self)
        left_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        left_dock.setMaximumWidth(300)

        # Container para múltiplas abas no dock esquerdo
        left_tabs = QTabWidget()
        left_tabs.setTabPosition(QTabWidget.West)

        # File Explorer
        self.setup_file_explorer(left_tabs)

        # Problems List
        self.setup_problems_widget(left_tabs)

        left_dock.setWidget(left_tabs)
        self.addDockWidget(Qt.LeftDockWidgetArea, left_dock)

    def setup_file_explorer(self, parent_tabs):
        """Configura o explorador de arquivos"""
        explorer_widget = QWidget()
        explorer_layout = QVBoxLayout(explorer_widget)

        # Barra de ferramentas do explorer
        explorer_toolbar = QToolBar()
        explorer_toolbar.setIconSize(QSize(16, 16))

        # Botões do explorer
        self.refresh_explorer_btn = QAction("🔄", self)
        self.new_file_btn = QAction("📄", self)
        self.new_folder_btn = QAction("📁", self)

        explorer_toolbar.addAction(self.refresh_explorer_btn)
        explorer_toolbar.addAction(self.new_file_btn)
        explorer_toolbar.addAction(self.new_folder_btn)

        explorer_layout.addWidget(explorer_toolbar)

        # Modelo de arquivos
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.homePath())

        # Tree view
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(QDir.homePath()))
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(15)
        self.file_tree.setSortingEnabled(True)

        # Ocultar colunas desnecessárias
        self.file_tree.hideColumn(1)  # Tamanho
        self.file_tree.hideColumn(2)  # Tipo
        self.file_tree.hideColumn(3)  # Data modificação

        explorer_layout.addWidget(self.file_tree)

        parent_tabs.addTab(explorer_widget, "📁 Explorer")

    def setup_problems_widget(self, parent_tabs):
        """Configura a lista de problemas"""
        problems_widget = QWidget()
        problems_layout = QVBoxLayout(problems_widget)

        # Barra de ferramentas dos problemas
        problems_toolbar = QToolBar()
        problems_toolbar.setIconSize(QSize(16, 16))

        self.clear_problems_btn = QAction("🗑️", self)
        self.run_lint_btn = QAction("🔍", self)

        problems_toolbar.addAction(self.clear_problems_btn)
        problems_toolbar.addAction(self.run_lint_btn)

        problems_layout.addWidget(problems_toolbar)

        # Lista de problemas
        self.problems_list = QListWidget()
        self.problems_list.setAlternatingRowColors(True)

        problems_layout.addWidget(self.problems_list)

        parent_tabs.addTab(problems_widget, "⚠️ Problems")

    def setup_right_dock(self):
        """Configura o dock direito com minimap"""
        right_dock = QDockWidget("Minimap", self)
        right_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        right_dock.setMaximumWidth(200)

        self.minimap = QPlainTextEdit()
        self.minimap.setReadOnly(True)
        self.minimap.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #569cd6;
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 2px;
            }
        """)

        right_dock.setWidget(self.minimap)
        self.addDockWidget(Qt.RightDockWidgetArea, right_dock)

    def setup_bottom_dock(self):
        """Configura o dock inferior com múltiplas abas"""
        bottom_dock = QDockWidget("Output", self)
        bottom_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

        self.output_tabs = QTabWidget()
        self.output_tabs.setTabPosition(QTabWidget.North)

        # Terminal
        self.setup_terminal_tab()

        # Output
        self.setup_output_tab()

        # Debug
        self.setup_debug_tab()

        # Errors
        self.setup_errors_tab()

        # Lint
        self.setup_lint_tab()

        bottom_dock.setWidget(self.output_tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, bottom_dock)

    def setup_terminal_tab(self):
        """Configura a aba do terminal"""
        self.terminal_text = QPlainTextEdit()
        self.terminal_text.setReadOnly(True)
        self.terminal_text.setFont(QFont(self.current_font, 10))
        self.terminal_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        self.output_tabs.addTab(self.terminal_text, "💻 Terminal")

    def setup_output_tab(self):
        """Configura a aba de output"""
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont(self.current_font, 10))
        self.output_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        self.output_tabs.addTab(self.output_text, "📤 Output")

    def setup_debug_tab(self):
        """Configura a aba de debug"""
        self.debug_text = QPlainTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFont(QFont(self.current_font, 10))
        self.debug_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ce9178;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        self.output_tabs.addTab(self.debug_text, "🐛 Debug")

    def setup_errors_tab(self):
        """Configura a aba de erros"""
        self.errors_text = QPlainTextEdit()
        self.errors_text.setReadOnly(True)
        self.errors_text.setFont(QFont(self.current_font, 10))
        self.errors_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #f44747;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        self.output_tabs.addTab(self.errors_text, "❌ Errors")

    def setup_lint_tab(self):
        """Configura a aba de lint"""
        self.lint_text = QPlainTextEdit()
        self.lint_text.setReadOnly(True)
        self.lint_text.setFont(QFont(self.current_font, 10))
        self.lint_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffcc66;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        self.output_tabs.addTab(self.lint_text, "📋 Lint")

    def setup_menu(self):
        """Configura o menu principal otimizado"""
        menubar = self.menuBar()

        # Menu Arquivo
        file_menu = menubar.addMenu("📁 Arquivo")
        self.setup_file_menu(file_menu)

        # Menu Editar
        edit_menu = menubar.addMenu("✏️ Editar")
        self.setup_edit_menu(edit_menu)

        # Menu Visualizar
        view_menu = menubar.addMenu("👁️ Visualizar")
        self.setup_view_menu(view_menu)

        # Menu Executar
        run_menu = menubar.addMenu("🚀 Executar")
        self.setup_run_menu(run_menu)

        # Menu Projeto
        project_menu = menubar.addMenu("📦 Projeto")
        self.setup_project_menu(project_menu)

        # Menu Ferramentas
        tools_menu = menubar.addMenu("🛠️ Ferramentas")
        self.setup_tools_menu(tools_menu)

        # Menu Ajuda
        help_menu = menubar.addMenu("❓ Ajuda")
        self.setup_help_menu(help_menu)

    def setup_file_menu(self, menu):
        """Configura o menu Arquivo"""
        actions = [
            ("📄 Novo Arquivo", "Ctrl+N", self.new_file),
            ("📁 Novo Projeto", "Ctrl+Shift+N", self.create_project),
            ("📂 Abrir Arquivo", "Ctrl+O", self.open_file),
            ("📂 Abrir Projeto", "Ctrl+Shift+O", self.set_project),
            ("💾 Salvar", "Ctrl+S", self.save_file),
            ("💾 Salvar Como", "Ctrl+Shift+S", self.save_file_as),
            ("🔒 Salvar Tudo", "Ctrl+Alt+S", self.save_all_files),
            ("---", None, None),
            ("🚪 Sair", "Ctrl+Q", self.close)
        ]

        self.create_menu_actions(menu, actions)

    def setup_edit_menu(self, menu):
        """Configura o menu Editar"""
        actions = [
            ("↶ Desfazer", "Ctrl+Z", self.undo),
            ("↷ Refazer", "Ctrl+Y", self.redo),
            ("---", None, None),
            ("✂️ Recortar", "Ctrl+X", self.cut),
            ("📋 Copiar", "Ctrl+C", self.copy),
            ("📝 Colar", "Ctrl+V", self.paste),
            ("---", None, None),
            ("🔍 Buscar", "Ctrl+F", self.show_find_dialog),
            ("🔄 Substituir", "Ctrl+H", self.show_replace_dialog),
            ("---", None, None),
            ("🎯 Auto-completar", "Ctrl+Space", self.force_auto_complete_current),
            ("📐 Corrigir Indentação", "Ctrl+I", self.fix_indentation_current)
        ]

        self.create_menu_actions(menu, actions)

    def setup_view_menu(self, menu):
        """Configura o menu Visualizar"""
        actions = [
            ("📊 Layout Dividido", "Ctrl+\\", self.split_view),
            ("🔍 Zoom In", "Ctrl+=", self.zoom_in),
            ("🔍 Zoom Out", "Ctrl+-", self.zoom_out),
            ("🔍 Zoom Reset", "Ctrl+0", self.zoom_reset),
            ("---", None, None),
            ("👁️ Mostrar/Ocultar Explorer", "Ctrl+Shift+E", self.toggle_explorer),
            ("👁️ Mostrar/Ocultar Terminal", "Ctrl+`", self.toggle_terminal),
            ("👁️ Mostrar/Ocultar Minimap", "Ctrl+Shift+M", self.toggle_minimap),
            ("---", None, None),
            ("🎨 Tema Escuro", None, lambda: self.set_dark_theme_optimized()),
            ("🎨 Tema Claro", None, lambda: self.set_light_theme()),
            ("🔤 Fonte...", None, self.show_font_dialog)
        ]

        self.create_menu_actions(menu, actions)

    def setup_run_menu(self, menu):
        """Configura o menu Executar"""
        actions = [
            ("▶️ Executar", "F5", self.run_code),
            ("🐛 Debug", "F6", self.debug_code),
            ("⏸️ Pausar", "F7", self.pause_execution),
            ("⏹️ Parar", "F8", self.stop_execution),
            ("---", None, None),
            ("🧪 Executar Testes", "Ctrl+T", self.run_tests),
            ("📊 Coverage", "Ctrl+Shift+T", self.run_coverage)
        ]

        self.create_menu_actions(menu, actions)

    def setup_project_menu(self, menu):
        """Configura o menu Projeto"""
        actions = [
            ("📦 Novo Projeto", None, self.create_project),
            ("📂 Abrir Projeto", None, self.set_project),
            ("🔧 Configurar Projeto", None, self.configure_project),
            ("---", None, None),
            ("🐍 Criar Virtualenv", None, self.create_venv),
            ("📚 Instalar Dependências", None, self.install_dependencies),
            ("---", None, None),
            ("📦 Empacotar", None, self.package_project),
            ("🚀 Deploy", None, self.deploy_project)
        ]

        self.create_menu_actions(menu, actions)

    def setup_tools_menu(self, menu):
        """Configura o menu Ferramentas"""
        actions = [
            ("🔧 Gerenciar Pacotes", None, self.manage_packages),
            ("🐍 Selecionar Python", None, self.select_python_version),
            ("🔍 Linter", None, self.run_linter),
            ("📐 Formatar Código", "Ctrl+Shift+F", self.format_code),
            ("---", None, None),
            ("⚙️ Configurações", "Ctrl+,", self.show_settings)
        ]

        self.create_menu_actions(menu, actions)

    def setup_help_menu(self, menu):
        """Configura o menu Ajuda"""
        actions = [
            ("📚 Documentação", "F1", self.show_documentation),
            ("🐛 Reportar Bug", None, self.report_bug),
            ("💡 Sugerir Feature", None, self.suggest_feature),
            ("---", None, None),
            ("ℹ️ Sobre", None, self.show_about)
        ]

        self.create_menu_actions(menu, actions)

    def create_menu_actions(self, menu, actions):
        """Cria ações de menu a partir de uma lista"""
        for text, shortcut, callback in actions:
            if text == "---":
                menu.addSeparator()
            else:
                action = QAction(text, self)
                if shortcut:
                    action.setShortcut(shortcut)
                if callback:
                    action.triggered.connect(callback)
                menu.addAction(action)

    def setup_toolbar(self):
        """Configura a toolbar principal"""
        toolbar = QToolBar("Ferramentas Principais")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(True)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Ações da toolbar
        actions = [
            ("📄 Novo Arquivo", "Novo Arquivo", "Ctrl+N", self.new_file),
            ("📂 Abrir Arquivo", "Abrir Arquivo", "Ctrl+O", self.open_file),
            ("💾 Salvar", "Salvar", "Ctrl+S", self.save_file),
            ("---", None, None, None),
            ("↶ Desfazer", "Desfazer", "Ctrl+Z", self.undo),
            ("↷ Refazer", "Refazer", "Ctrl+Y", self.redo),
            ("---", None, None, None),
            ("▶️ Executar", "Executar", "F5", self.run_code),
            ("🐛 Debug", "Debug", "F6", self.debug_code),
            ("---", None, None, None),
            ("🔍 Buscar", "Buscar", "Ctrl+F", self.show_find_dialog),
            ("🎯 Auto-completar", "Auto-completar", "Ctrl+Space", self.force_auto_complete_current)
        ]

        for icon, text, shortcut, callback in actions:
            if icon == "---":
                toolbar.addSeparator()
            else:
                action = QAction(icon, self)
                action.setText(text)
                action.setToolTip(text)
                if shortcut:
                    action.setShortcut(shortcut)
                if callback:
                    action.triggered.connect(callback)
                toolbar.addAction(action)

        self.addToolBar(toolbar)

    def setup_statusbar(self):
        """Configura a barra de status otimizada"""
        status_bar = self.statusBar()

        # Informações do arquivo
        self.file_info_label = QLabel("Sem arquivo")
        status_bar.addWidget(self.file_info_label)

        # Informações do cursor
        self.cursor_info_label = QLabel("Linha: 1, Coluna: 1")
        status_bar.addPermanentWidget(self.cursor_info_label)

        # Informações do projeto
        self.project_info_label = QLabel("Sem projeto")
        status_bar.addPermanentWidget(self.project_info_label)

        # Progresso
        self.status_progress = QLabel("✅")
        status_bar.addPermanentWidget(self.status_progress)

    def setup_connections(self):
        """Configura as conexões de sinais"""
        # Conexões do explorador de arquivos
        self.file_tree.doubleClicked.connect(self.open_from_tree)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_explorer_context_menu)

        # Conexões dos problemas
        self.problems_list.itemClicked.connect(self.jump_to_error)

        # Conexões das abas
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Conexões dos botões
        self.refresh_explorer_btn.triggered.connect(self.refresh_explorer)
        self.new_file_btn.triggered.connect(self.create_new_file_in_explorer)
        self.new_folder_btn.triggered.connect(self.create_new_folder_in_explorer)
        self.clear_problems_btn.triggered.connect(self.clear_problems)
        self.run_lint_btn.triggered.connect(self.run_linter)

    def setup_shortcuts(self):
        """Configura atalhos de teclado globais"""
        # Navegação entre abas
        QShortcut("Ctrl+Tab", self).activated.connect(self.next_tab)
        QShortcut("Ctrl+Shift+Tab", self).activated.connect(self.previous_tab)

        # Comandos rápidos
        QShortcut("Ctrl+P", self).activated.connect(self.show_command_palette)

    def set_dark_theme_optimized(self):
        """Tema escuro otimizado para programação"""
        palette = QPalette()

        # Cores base
        dark_bg = QColor(30, 30, 30)
        darker_bg = QColor(20, 20, 20)
        light_text = QColor(220, 220, 220)
        highlight = QColor(86, 156, 214)
        highlight_text = QColor(255, 255, 255)

        # Configuração da paleta
        palette.setColor(QPalette.Window, dark_bg)
        palette.setColor(QPalette.WindowText, light_text)
        palette.setColor(QPalette.Base, darker_bg)
        palette.setColor(QPalette.AlternateBase, dark_bg)
        palette.setColor(QPalette.ToolTipBase, dark_bg)
        palette.setColor(QPalette.ToolTipText, light_text)
        palette.setColor(QPalette.Text, light_text)
        palette.setColor(QPalette.Button, dark_bg)
        palette.setColor(QPalette.ButtonText, light_text)
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, highlight)
        palette.setColor(QPalette.Highlight, highlight)
        palette.setColor(QPalette.HighlightedText, highlight_text)

        QApplication.setPalette(palette)
        QApplication.setStyle("Fusion")

        # CSS adicional para componentes específicos
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QMenuBar {
                background-color: #2d2d30;
                color: #cccccc;
                border: none;
            }
            QMenuBar::item:selected {
                background-color: #3e3e42;
            }
            QMenu {
                background-color: #2d2d30;
                color: #cccccc;
                border: 1px solid #3e3e42;
            }
            QMenu::item:selected {
                background-color: #3e3e42;
            }
            QToolBar {
                background-color: #2d2d30;
                border: none;
                spacing: 3px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #3e3e42;
                border: 1px solid #505050;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QDockWidget::title {
                background-color: #2d2d30;
                padding: 4px 8px;
                text-align: left;
                font-weight: bold;
            }
        """)

    # ===== MÉTODOS PRINCIPAIS =====

    def new_file(self):
        """Cria um novo arquivo"""
        editor = QPlainTextEdit()
        editor.setFont(QFont(self.current_font, 12))
        index = self.tab_widget.addTab(editor, "📄 novo_arquivo.py")
        self.tab_widget.setCurrentIndex(index)
        editor.setFocus()

    def open_file(self, file_path=None):
        """Abre um arquivo"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Abrir Arquivo",
                self.project_path or QDir.homePath(),
                "Arquivos de Código (*.py *.js *.html *.css *.json *.xml *.txt);;Todos os Arquivos (*.*)"
            )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                editor = QPlainTextEdit()
                editor.setPlainText(content)
                editor.setFont(QFont(self.current_font, 12))
                
                index = self.tab_widget.addTab(editor, os.path.basename(file_path))
                self.tab_widget.setCurrentIndex(index)
                
                # Armazena o caminho do arquivo
                editor.file_path = file_path
                
                self.update_file_info(file_path)

            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo:\n{str(e)}")

    def save_file(self):
        """Salva o arquivo atual"""
        editor = self.get_current_editor()
        if not editor or not hasattr(editor, 'file_path'):
            self.save_file_as()
            return

        file_path = editor.file_path
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())

            self.statusBar().showMessage(f"✅ Arquivo salvo: {os.path.basename(file_path)}", 3000)

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")

    def save_file_as(self):
        """Salva o arquivo atual com novo nome"""
        editor = self.get_current_editor()
        if not editor:
            return

        new_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Como",
            self.project_path or QDir.homePath(),
            "Arquivos Python (*.py);;Todos os Arquivos (*.*)"
        )

        if new_path:
            try:
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(editor.toPlainText())

                # Atualiza a aba
                editor.file_path = new_path
                index = self.tab_widget.currentIndex()
                self.tab_widget.setTabText(index, os.path.basename(new_path))

                self.update_file_info(new_path)
                self.statusBar().showMessage(f"✅ Arquivo salvo como: {os.path.basename(new_path)}", 3000)

            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")

    def save_all_files(self):
        """Salva todos os arquivos abertos"""
        for i in range(self.tab_widget.count()):
            self.tab_widget.setCurrentIndex(i)
            self.save_file()

    def run_code(self):
        """Executa o código atual"""
        editor = self.get_current_editor()
        if not editor or not hasattr(editor, 'file_path'):
            QMessageBox.information(self, "Informação", "Nenhum arquivo para executar.")
            return

        file_path = editor.file_path
        if not file_path.endswith('.py'):
            QMessageBox.information(self, "Informação", "Apenas arquivos Python podem ser executados.")
            return

        try:
            # Limpa output anterior
            self.output_text.clear()

            # Mostra que está executando
            self.output_tabs.setCurrentWidget(self.output_text)
            self.output_text.appendPlainText(f"🚀 Executando: {os.path.basename(file_path)}\n{'-' * 50}")

            # Executa o código
            python_exec = self.get_python_executable()
            result = subprocess.run(
                [python_exec, file_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path or os.path.dirname(file_path)
            )

            # Mostra resultados
            if result.stdout:
                self.output_text.appendPlainText("📤 SAÍDA:")
                self.output_text.appendPlainText(result.stdout)

            if result.stderr:
                self.output_text.appendPlainText("❌ ERROS:")
                self.output_text.appendPlainText(result.stderr)

            if result.returncode == 0:
                self.output_text.appendPlainText(f"\n✅ Execução concluída com sucesso!")
            else:
                self.output_text.appendPlainText(f"\n❌ Execução falhou (código: {result.returncode})")

        except subprocess.TimeoutExpired:
            self.output_text.appendPlainText("⏰ Timeout: A execução demorou muito.")
        except Exception as e:
            self.output_text.appendPlainText(f"💥 Erro na execução: {str(e)}")

    def debug_code(self):
        """Executa o código em modo debug"""
        editor = self.get_current_editor()
        if not editor or not hasattr(editor, 'file_path'):
            QMessageBox.information(self, "Informação", "Nenhum arquivo para depurar.")
            return

        file_path = editor.file_path
        try:
            self.debug_text.clear()
            self.output_tabs.setCurrentWidget(self.debug_text)

            python_exec = self.get_python_executable()
            result = subprocess.run(
                [python_exec, "-m", "pdb", file_path],
                capture_output=True,
                text=True,
                cwd=self.project_path or os.path.dirname(file_path)
            )

            stdout_str = result.stdout or ''
            stderr_str = result.stderr or ''
            self.debug_text.setPlainText(stdout_str + stderr_str)

        except Exception as e:
            error_msg = f"Erro no debug: {str(e)}"
            self.debug_text.setPlainText(error_msg)

    def get_current_editor(self):
        """Obtém o editor atual"""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, QPlainTextEdit):
            return current_widget
        return None

    def close_tab(self, index):
        """Fecha uma aba"""
        self.tab_widget.removeTab(index)

    def on_tab_changed(self, index):
        """Atualiza a interface quando a aba muda"""
        if index >= 0:
            editor = self.tab_widget.widget(index)
            if hasattr(editor, 'file_path') and editor.file_path:
                self.update_file_info(editor.file_path)
            else:
                self.update_file_info(None)

    # ===== MÉTODOS DE EDIÇÃO =====

    def undo(self):
        """Desfaz a última ação"""
        editor = self.get_current_editor()
        if editor:
            editor.undo()

    def redo(self):
        """Refaz a última ação"""
        editor = self.get_current_editor()
        if editor:
            editor.redo()

    def cut(self):
        """Recorta texto selecionado"""
        editor = self.get_current_editor()
        if editor:
            editor.cut()

    def copy(self):
        """Copia texto selecionado"""
        editor = self.get_current_editor()
        if editor:
            editor.copy()

    def paste(self):
        """Cola texto da área de transferência"""
        editor = self.get_current_editor()
        if editor:
            editor.paste()

    def show_find_dialog(self):
        """Mostra diálogo de busca"""
        editor = self.get_current_editor()
        if not editor:
            return

        find_text, ok = QInputDialog.getText(
            self,
            "Buscar",
            "Texto para buscar:"
        )

        if ok and find_text:
            cursor = editor.textCursor()
            document = editor.document()

            # Busca a partir da posição atual
            cursor = document.find(find_text, cursor)
            if not cursor.isNull():
                editor.setTextCursor(cursor)
            else:
                QMessageBox.information(self, "Buscar", "Texto não encontrado.")

    def show_replace_dialog(self):
        """Mostra diálogo de substituir"""
        editor = self.get_current_editor()
        if not editor:
            return

        find_text, ok1 = QInputDialog.getText(
            self,
            "Substituir",
            "Texto para buscar:"
        )

        if ok1 and find_text:
            replace_text, ok2 = QInputDialog.getText(
                self,
                "Substituir",
                "Substituir por:"
            )

            if ok2:
                text = editor.toPlainText()
                new_text = text.replace(find_text, replace_text)
                editor.setPlainText(new_text)

    def force_auto_complete_current(self):
        """Força auto-completar no editor atual"""
        # Implementação básica - pode ser expandida
        pass

    def fix_indentation_current(self):
        """Corrige indentação no editor atual"""
        editor = self.get_current_editor()
        if editor:
            text = editor.toPlainText()
            # Implementação básica de correção de indentação
            lines = text.split('\n')
            fixed_lines = []
            for line in lines:
                # Remove espaços em branco desnecessários no final
                fixed_lines.append(line.rstrip())
            editor.setPlainText('\n'.join(fixed_lines))

    # ===== MÉTODOS DE PROJETO =====

    def create_project(self):
        """Cria um novo projeto"""
        project_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta para o Projeto",
            QDir.homePath()
        )

        if project_path:
            project_name = os.path.basename(project_path)

            # Cria estrutura básica
            try:
                # Arquivo principal
                main_file = os.path.join(project_path, "main.py")
                with open(main_file, 'w', encoding='utf-8') as f:
                    f.write(f'''# Projeto: {project_name}

def main():
    """Função principal"""
    print("Hello World!")

if __name__ == "__main__":
    main()
''')

                # README
                readme_file = os.path.join(project_path, "README.md")
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {project_name}\n\nProjeto criado com Py Dragon Studio IDE\n")

                self.set_project(project_path)
                self.open_file(main_file)

                QMessageBox.information(self, "Sucesso", f"Projeto '{project_name}' criado com sucesso!")

            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível criar o projeto:\n{str(e)}")

    def set_project(self, project_path=None):
        """Define o projeto atual"""
        if not project_path:
            project_path = QFileDialog.getExistingDirectory(
                self,
                "Selecionar Projeto",
                self.project_path or QDir.homePath()
            )

        if project_path:
            self.project_path = project_path
            self.project_info_label.setText(f"📦 {os.path.basename(project_path)}")

            # Atualiza explorador
            self.refresh_explorer()

            # Ativa no terminal
            self.activate_project()

            self.statusBar().showMessage(f"✅ Projeto carregado: {project_path}", 3000)

    def configure_project(self):
        """Configura o projeto"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        QMessageBox.information(self, "Configurar Projeto", 
                               f"Configurações do projeto: {os.path.basename(self.project_path)}")

    def create_venv(self):
        """Cria virtualenv para o projeto"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        venv_name = "venv"
        venv_path = os.path.join(self.project_path, venv_name)

        try:
            # Usa o Python atual para criar o venv
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
            self.venv_path = venv_path
            self.activate_project()
            QMessageBox.information(self, "Sucesso", f"Virtualenv criado em: {venv_path}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi criar o virtualenv:\n{str(e)}")

    def install_dependencies(self):
        """Instala dependências do projeto"""
        if not self.project_path:
            return

        requirements_file = os.path.join(self.project_path, "requirements.txt")
        if not os.path.exists(requirements_file):
            QMessageBox.information(self, "Informação", "Arquivo requirements.txt não encontrado.")
            return

        try:
            python_exec = self.get_python_executable()
            result = subprocess.run(
                [python_exec, "-m", "pip", "install", "-r", requirements_file],
                capture_output=True,
                text=True,
                cwd=self.project_path
            )

            self.output_tabs.setCurrentWidget(self.output_text)
            self.output_text.clear()
            self.output_text.appendPlainText("📦 Instalando dependências...\n")

            if result.stdout:
                self.output_text.appendPlainText(result.stdout)
            if result.stderr:
                self.output_text.appendPlainText(result.stderr)

            if result.returncode == 0:
                self.output_text.appendPlainText("\n✅ Dependências instaladas com sucesso!")
            else:
                self.output_text.appendPlainText(f"\n❌ Falha na instalação (código: {result.returncode})")

        except Exception as e:
            self.output_text.appendPlainText(f"💥 Erro: {str(e)}")

    def package_project(self):
        """Empacota o projeto"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        QMessageBox.information(self, "Empacotar", "Funcionalidade de empacotamento em desenvolvimento.")

    def deploy_project(self):
        """Faz deploy do projeto"""
        QMessageBox.information(self, "Informação", "Funcionalidade de deploy em desenvolvimento.")

    # ===== MÉTODOS AUXILIARES =====

    def update_file_info(self, file_path):
        """Atualiza informações do arquivo na statusbar"""
        if file_path and os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path)
                size_str = f"{size} bytes" if size < 1024 else f"{size / 1024:.1f} KB"
                file_name = os.path.basename(file_path)
                self.file_info_label.setText(f"📄 {file_name} ({size_str})")
            except Exception as e:
                self.file_info_label.setText("📄 Informações indisponíveis")
        else:
            self.file_info_label.setText("📄 Sem arquivo")

    def refresh_explorer(self):
        """Atualiza o explorador de arquivos"""
        if self.project_path and self.file_model:
            self.file_model.setRootPath(self.project_path)
            self.file_tree.setRootIndex(self.file_model.index(self.project_path))
        elif self.file_model:
            self.file_model.setRootPath(QDir.homePath())
            self.file_tree.setRootIndex(self.file_model.index(QDir.homePath()))

    def open_from_tree(self, index):
        """Abre arquivo a partir do explorador"""
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.open_file(file_path)

    def show_explorer_context_menu(self, position):
        """Mostra menu de contexto no explorador"""
        index = self.file_tree.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        file_path = self.file_model.filePath(index)
        
        if os.path.isfile(file_path):
            menu.addAction("📄 Abrir", lambda: self.open_file(file_path))
        else:
            menu.addAction("📂 Abrir Pasta", lambda: self.set_project(file_path))
        
        menu.exec_(self.file_tree.viewport().mapToGlobal(position))

    def create_new_file_in_explorer(self):
        """Cria novo arquivo no explorador"""
        current_index = self.file_tree.currentIndex()
        if current_index.isValid():
            parent_path = self.file_model.filePath(current_index)
            if not os.path.isdir(parent_path):
                parent_path = os.path.dirname(parent_path)
        else:
            parent_path = self.project_path or QDir.homePath()

        file_name, ok = QInputDialog.getText(
            self,
            "Novo Arquivo",
            "Nome do arquivo:",
            text="novo_arquivo.py"
        )

        if ok and file_name:
            file_path = os.path.join(parent_path, file_name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('# Novo arquivo\n')
                self.refresh_explorer()
                self.open_file(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível criar o arquivo:\n{str(e)}")

    def create_new_folder_in_explorer(self):
        """Cria nova pasta no explorador"""
        current_index = self.file_tree.currentIndex()
        if current_index.isValid():
            parent_path = self.file_model.filePath(current_index)
            if not os.path.isdir(parent_path):
                parent_path = os.path.dirname(parent_path)
        else:
            parent_path = self.project_path or QDir.homePath()

        folder_name, ok = QInputDialog.getText(
            self,
            "Nova Pasta",
            "Nome da pasta:",
            text="nova_pasta"
        )

        if ok and folder_name:
            new_folder_path = os.path.join(parent_path, folder_name)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                self.refresh_explorer()
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível criar a pasta:\n{str(e)}")

    def jump_to_error(self, item):
        """Salta para a linha do erro na lista de problemas"""
        # Implementação básica
        pass

    def clear_problems(self):
        """Limpa a lista de problemas"""
        self.problems_list.clear()

    def run_linter(self):
        """Executa o linter no arquivo atual"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'file_path') and editor.file_path.endswith('.py'):
            self.lint_text.clear()
            self.output_tabs.setCurrentWidget(self.lint_text)
            self.lint_text.setPlainText("🔍 Analisando código...\n\nLinter em desenvolvimento.")
        else:
            QMessageBox.information(self, "Informação", "Apenas arquivos Python podem ser analisados.")

    # ===== MÉTODOS DE TERMINAL =====

    def start_shell(self):
        """Inicia o processo do shell"""
        try:
            self.shell_process = QProcess(self)
            self.shell_process.readyReadStandardOutput.connect(self.handle_terminal_output)
            self.shell_process.readyReadStandardError.connect(self.handle_terminal_error)

            if os.name == 'nt':  # Windows
                self.shell_process.start("cmd.exe")
            else:  # Linux/Mac
                self.shell_process.start("/bin/bash", ["-i"])

            if self.project_path:
                self.activate_project()

        except Exception as e:
            self.terminal_text.appendPlainText(f"❌ Erro ao iniciar terminal: {str(e)}\n")

    def handle_terminal_output(self):
        """Processa saída do terminal"""
        data = self.shell_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.terminal_text.appendPlainText(data)

    def handle_terminal_error(self):
        """Processa erro do terminal"""
        data = self.shell_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.terminal_text.appendPlainText(data)

    def activate_project(self):
        """Ativa o projeto no terminal"""
        if self.project_path and self.shell_process and self.shell_process.state() == QProcess.Running:
            cd_command = f"cd \"{self.project_path}\"\n"
            self.shell_process.write(cd_command.encode())

    def get_python_executable(self):
        """Obtém o executável Python"""
        if self.venv_path and os.path.exists(self.venv_path):
            if os.name == 'nt':  # Windows
                return os.path.join(self.venv_path, "Scripts", "python.exe")
            else:  # Linux/Mac
                return os.path.join(self.venv_path, "bin", "python")
        return sys.executable

    def check_python_version(self):
        """Verifica e exibe a versão do Python"""
        try:
            result = subprocess.run([self.get_python_executable(), "--version"],
                                    capture_output=True, text=True)
            version = result.stdout.strip()
            self.statusBar().showMessage(f"🐍 {version}", 5000)
        except:
            self.statusBar().showMessage("❌ Não foi possível detectar Python", 5000)

    # ===== MÉTODOS DE VISUALIZAÇÃO =====

    def split_view(self):
        """Divide a visualização"""
        QMessageBox.information(self, "Layout Dividido", "Funcionalidade em desenvolvimento.")

    def zoom_in(self):
        """Aumenta o zoom"""
        editor = self.get_current_editor()
        if editor:
            font = editor.font()
            size = font.pointSize()
            font.setPointSize(min(size + 1, 24))
            editor.setFont(font)

    def zoom_out(self):
        """Diminui o zoom"""
        editor = self.get_current_editor()
        if editor:
            font = editor.font()
            size = font.pointSize()
            font.setPointSize(max(size - 1, 8))
            editor.setFont(font)

    def zoom_reset(self):
        """Reseta o zoom"""
        editor = self.get_current_editor()
        if editor:
            font = editor.font()
            font.setPointSize(12)
            editor.setFont(font)

    def toggle_explorer(self):
        """Alterna visibilidade do explorer"""
        for dock in self.findChildren(QDockWidget):
            if dock.windowTitle() == "Explorer":
                dock.setVisible(not dock.isVisible())
                break

    def toggle_terminal(self):
        """Alterna visibilidade do terminal"""
        for dock in self.findChildren(QDockWidget):
            if dock.windowTitle() == "Output":
                dock.setVisible(not dock.isVisible())
                break

    def toggle_minimap(self):
        """Alterna visibilidade do minimap"""
        for dock in self.findChildren(QDockWidget):
            if dock.windowTitle() == "Minimap":
                dock.setVisible(not dock.isVisible())
                break

    def show_font_dialog(self):
        """Mostra diálogo para selecionar fonte"""
        font, ok = QFontDialog.getFont()
        if ok:
            self.current_font = font.family()
            # Aplica a fonte a todos os editores
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                if isinstance(editor, QPlainTextEdit):
                    editor.setFont(font)

    def set_light_theme(self):
        """Define tema claro"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        QApplication.setPalette(palette)

    # ===== MÉTODOS DE FERRAMENTAS =====

    def manage_packages(self):
        """Gerencia pacotes Python"""
        QMessageBox.information(self, "Gerenciar Pacotes", "Funcionalidade em desenvolvimento.")

    def select_python_version(self):
        """Seleciona versão do Python"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Executável Python",
            "/usr/bin" if os.name != 'nt' else "C:\\",
            "Executável Python (python python.exe)"
        )

        if file_path:
            self.python_path = file_path
            self.statusBar().showMessage(f"🐍 Python definido: {file_path}", 3000)

    def format_code(self):
        """Formata o código atual"""
        editor = self.get_current_editor()
        if not editor or not hasattr(editor, 'file_path') or not editor.file_path.endswith('.py'):
            QMessageBox.information(self, "Informação", "Apenas arquivos Python podem ser formatados.")
            return

        QMessageBox.information(self, "Formatar Código", "Funcionalidade em desenvolvimento.")

    def show_settings(self):
        """Mostra configurações"""
        QMessageBox.information(self, "Configurações", "Painel de configurações em desenvolvimento.")

    # ===== MÉTODOS DE AJUDA =====

    def show_documentation(self):
        """Mostra documentação"""
        QMessageBox.information(self, "Documentação",
                                "Py Dragon Studio IDE\n\n"
                                "Atalhos:\n"
                                "Ctrl+N - Novo arquivo\n"
                                "Ctrl+O - Abrir arquivo\n"
                                "Ctrl+S - Salvar\n"
                                "F5 - Executar\n"
                                "Ctrl+Space - Auto-completar")

    def report_bug(self):
        """Reporta bug"""
        QMessageBox.information(self, "Reportar Bug",
                                "Encontrou um bug?\n\n"
                                "Por favor, reporte em:\n"
                                "https://github.com/seu-usuario/py-dragon-studio/issues")

    def suggest_feature(self):
        """Sugere nova funcionalidade"""
        QMessageBox.information(self, "Sugerir Funcionalidade",
                                "Tem uma ideia para melhorar o IDE?\n\n"
                                "Envie sua sugestão em:\n"
                                "https://github.com/seu-usuario/py-dragon-studio/issues")

    def show_about(self):
        """Mostra informações sobre o aplicativo"""
        QMessageBox.about(self, "Sobre Py Dragon Studio IDE",
                          f"Py Dragon Studio IDE\n\n"
                          f"Versão: 1.0.0\n"
                          f"Python: {sys.version}\n"
                          f"Plataforma: {platform.system()}\n\n"
                          f"Um IDE Python moderno com foco em produtividade.")

    # ===== MÉTODOS DE NAVEGAÇÃO =====

    def next_tab(self):
        """Navega para a próxima aba"""
        current = self.tab_widget.currentIndex()
        next_index = (current + 1) % self.tab_widget.count()
        self.tab_widget.setCurrentIndex(next_index)

    def previous_tab(self):
        """Navega para a aba anterior"""
        current = self.tab_widget.currentIndex()
        previous_index = (current - 1) % self.tab_widget.count()
        self.tab_widget.setCurrentIndex(previous_index)

    def show_command_palette(self):
        """Mostra palette de comandos"""
        commands = [
            "Novo Arquivo", "Abrir Arquivo", "Salvar", "Executar",
            "Debug", "Buscar", "Substituir", "Terminal", "Explorer"
        ]

        command, ok = QInputDialog.getItem(
            self,
            "Palette de Comandos",
            "Digite ou selecione um comando:",
            commands,
            0,
            True
        )

        if ok and command:
            if command == "Novo Arquivo":
                self.new_file()
            elif command == "Abrir Arquivo":
                self.open_file()
            elif command == "Salvar":
                self.save_file()
            elif command == "Executar":
                self.run_code()
            elif command == "Debug":
                self.debug_code()
            elif command == "Buscar":
                self.show_find_dialog()
            elif command == "Substituir":
                self.show_replace_dialog()
            elif command == "Terminal":
                self.toggle_terminal()
            elif command == "Explorer":
                self.toggle_explorer()

    # ===== MÉTODOS DE EXECUÇÃO =====

    def pause_execution(self):
        """Pausa execução"""
        self.statusBar().showMessage("⏸️ Execução pausada", 2000)

    def stop_execution(self):
        """Para execução"""
        self.statusBar().showMessage("⏹️ Execução parada", 2000)

    def run_tests(self):
        """Executa testes"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        self.output_tabs.setCurrentWidget(self.output_text)
        self.output_text.clear()
        self.output_text.appendPlainText("🧪 Executando testes...\n\nFuncionalidade em desenvolvimento.")



    def run_coverage(self):
    #    """Executa coverage"""
        if not self.project_path:
            return

        try:
            python_exec = self.get_python_executable()
            result = subprocess.run(
                [python_exec, "-m", "coverage", "run", "-m", "pytest"],
                capture_output=True,
                text=True,
                cwd=self.project_path
            )

            self.output_tabs.setCurrentWidget(self.output_text)
            self.output_text.clear()
            self.output_text.appendPlainText("📊 Gerando coverage...\n")

            if result.returncode == 0:
                # Mostra report
                report_result = subprocess.run(
                    [python_exec, "-m", "coverage", "report"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                if report_result.stdout:
                    self.output_text.appendPlainText(report_result.stdout)
            else:
                self.output_text.appendPlainText("❌ Erro no coverage")

        except Exception as e:
            self.output_text.appendPlainText(f"❌ Erro: {str(e)}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IDE()
    window.show()
    sys.exit(app.exec())
   