from PySide6.QtWidgets import QDialog, QTreeWidget
from core.plugin_system import PluginBase
import ast



class CodeMetricsPlugin(PluginBase):
    """Plugin de métricas de código"""

    def __init__(self, ide_instance):
        super().__init__(ide_instance)
        self.info = PluginInfo(
            name="Code Metrics",
            version="1.0.0",
            author="Py Dragon Team",
            description="Análise de métricas e qualidade de código"
        )

    def initialize(self):
        pass

    def shutdown(self):
        pass

    def get_actions(self):
        action = QAction("📈 Métricas de Código", self.ide)
        action.triggered.connect(self.analyze_metrics)
        return [action]

    def analyze_metrics(self):
        """Analisa métricas do código atual"""
        editor = self.ide.get_current_editor()
        if not editor:
            return

        code = editor.toPlainText()
        metrics = self.calculate_metrics(code)

        dialog = MetricsDialog(self.ide, metrics)
        dialog.exec()

    def calculate_metrics(self, code):
        """Calcula métricas do código"""
        lines = code.split('\n')

        metrics = {
            'Linhas totais': len(lines),
            'Linhas de código': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            'Linhas em branco': len([l for l in lines if not l.strip()]),
            'Comentários': len([l for l in lines if l.strip().startswith('#')]),
            'Funções': len(re.findall(r'def\s+(\w+)', code)),
            'Classes': len(re.findall(r'class\s+(\w+)', code)),
            'Complexidade': self.calculate_complexity(code)
        }

        return metrics

    def calculate_complexity(self, code):
        """Calcula complexidade ciclomática simples"""
        complexity = 1  # Base

        # Conta estruturas de decisão
        patterns = [
            r'\bif\b', r'\belif\b', r'\belse\b',
            r'\bfor\b', r'\bwhile\b',
            r'\band\b', r'\bor\b',
            r'case', r'default'
        ]

        for pattern in patterns:
            complexity += len(re.findall(pattern, code))

        return complexity


class MetricsDialog(QDialog):
    def __init__(self, parent, metrics):
        super().__init__(parent)
        self.metrics = metrics
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Métricas de Código")
        self.setGeometry(300, 300, 300, 400)

        layout = QVBoxLayout()

        table = QTableWidget()
        table.setRowCount(len(self.metrics))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Métrica", "Valor"])

        for i, (key, value) in enumerate(self.metrics.items()):
            table.setItem(
                i, 0, QTableWidgetItem(key))
            table.setItem(
                i, 1, QTableWidgetItem(str(value)))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
