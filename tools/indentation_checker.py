from PySide6.QtGui import QTextBlockUserData
import re




class IndentationChecker:
    """Verificador de erros de indentação para Python"""

    def __init__(self):
        self.errors = []

    def check_code(self, code, filename="<string>"):
        """Verifica erros de indentação no código Python"""
        self.errors = []

        try:
            # Tenta compilar o código para detectar
            # erros de sintaxe
            compile(code, filename, 'exec')
        except IndentationError as e:
            self.add_indentation_error(e, code)
        except SyntaxError as e:
            if "unexpected indent" in str(
                    e) or "expected an indented block" in str(e):
                self.add_indentation_error(
                    e, code)

        return self.errors

    def add_indentation_error(self, error, code):
        """Adiciona erro de indentação à lista"""
        lines = code.split('\n')
        error_info = {
            'type': 'indentation',
            'message': str(error),
            'line': error.lineno or 1,
            'column': error.offset or 1,
            'suggestion': self.get_indentation_suggestion(error, lines)
        }
        self.errors.append(error_info)

    def get_indentation_suggestion(self, error, lines):
        """Sugere correção para erro de indentação"""
        error_msg = str(error).lower()

        if "unexpected indent" in error_msg:
            return "Remova a indentação extra nesta linha"
        elif "expected an indented block" in error_msg:
            return "Adicione indentação após os dois pontos (:)"
        elif "unindent does not match any outer indentation level" in error_msg:
            return "Ajuste a indentação para corresponder ao nível anterior"

        return "Verifique a indentação da linha"


# ===== CLASSES AUXILIARES =====
class ErrorData(QTextBlockUserData):
    def __init__(self, errors=None):
        super().__init__()
        self.errors = errors or []
