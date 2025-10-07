from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox
from PySide6.QtCore import QTimer
from core.plugin_system import PluginBase
import autopep8



class CodeFormatterPlugin(PluginBase):
    """Plugin de formatação de código avançada"""

    def __init__(self, ide_instance):
        super().__init__(ide_instance)
        self.info = PluginInfo(
            name="Code Formatter",
            version="1.1.0",
            author="Py Dragon Team",
            description="Formatação automática de código com múltiplos formatadores"
        )

    def initialize(self):
        self.formatters = {
            'Python': self.format_python,
            'JavaScript': self.format_javascript,
            'HTML': self.format_html,
            'CSS': self.format_css
        }

    def shutdown(self):
        pass

    def get_actions(self):
        format_action = QAction(
            "🚀 Formatador Avançado", self.ide)
        format_action.triggered.connect(self.show_format_dialog)
        return [format_action]

    def get_menu_items(self):
        return {
            "Ferramentas": self.get_actions()
        }

    def show_format_dialog(self):
        """Mostra diálogo de formatação avançada"""
        dialog = FormatDialog(self.ide, self.formatters)
        dialog.exec()

    def format_python(self, code):
        """Formata código Python"""
        try:
            # Tenta black primeiro
            result = subprocess.run(
                [sys.executable, "-m",
                 "black", "--code", code],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout

            # Fallback para autopep8
            result = subprocess.run(
                [sys.executable, "-m",
                 "autopep8", "-"],
                input=code, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout

            return code
        except:
            return code

    def format_javascript(self, code):
        """Formata código JavaScript (placeholder)"""
        # Implementação com prettier ou similar
        return code

    def format_html(self, code):
        """Formata HTML (placeholder)"""
        return code

    def format_css(self, code):
        """Formata CSS (placeholder)"""
        return code



class FormatDialog(QDialog):
    def __init__(self, parent, formatters):
        super().__init__(parent)
        self.formatters = formatters
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Formatador de Código")
        self.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout()

        # Seletor de formatador
        layout.addWidget(QLabel("Selecione o formatador:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.formatters.keys())
        layout.addWidget(self.format_combo)

        # Preview
        layout.addWidget(QLabel("Pré-visualização:"))
        self.preview_edit = QTextEdit()
        self.preview_edit.setFont(QFont("Consolas", 1010))
        layout.addWidget(self.preview_edit)

        # Botões
        btn_layout = QHBoxLayout()
        self.format_btn = QPushButton("Formatar")
        self.format_btn.clicked.connect(self.format_code)
        btn_layout.addWidget(self.format_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def format_code(self):
        formatter_name = self.format_combo.currentText()
        formatter = self.formatters[formatter_name]

        current_editor = self.parent().get_current_editor()
        if current_editor:
            code = current_editor.toPlainText()
            formatted = formatter(code)
            self.preview_edit.setPlainText(
                formatted)
