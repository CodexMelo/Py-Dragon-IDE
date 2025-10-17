from PySide6.QtWidgets import QDialog, QListWidget, QLineEdit
from core.plugin_system import PluginBase
import json


class SnippetManagerPlugin(PluginBase):
    """Gerenciador de snippets de código"""

    def __init__(self, ide_instance):
        super().__init__(ide_instance)
        self.info = PluginInfo(
            name="Snippet Manager",
            version="1.0.0",
            author="Py Dragon Team",
            description="Gerenciamento de snippets de código reutilizáveis"
        )
        self.snippets_file = os.path.join(
            os.path.expanduser("~"), ".py_dragon_snippets.json")
        self.snippets = self.load_snippets()

    def initialize(self):
        pass

    def shutdown(self):
        self.save_snippets()

    def load_snippets(self):
        """Carrega snippets do arquivo"""
        try:
            with open(self.snippets_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_snippets(self):
        """Salva snippets no arquivo"""
        try:
            with open(self.snippets_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.snippets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar snippets: {e}")

    def get_actions(self):
        actions = [
            QAction("💾 Salvar Snippet", self.ide),
            QAction(
                "📋 Gerenciar Snippets", self.ide)
        ]

        actions[0].triggered.connect(self.save_current_snippet)
        actions[1].triggered.connect(self.manage_snippets)

        return actions

    def save_current_snippet(self):
        """Salva o código selecionado como snippet"""
        editor = self.ide.get_current_editor()
        if not editor:
            return

        cursor = editor.textCursor()
        selected_text = cursor.selectedText()

        if not selected_text:
            QMessageBox.information(
                self.ide, "Snippet", "Selecione um texto para salvar como snippet")
            return

        name, ok = QInputDialog.getText(
            self.ide, "Salvar Snippet", "Nome do snippet:")
        if ok and name:
            self.snippets[name] = {
                'code': selected_text,
                'language': 'python',
                'created': time.time()
            }
            self.save_snippets()
            QMessageBox.information(
                self.ide, "Snippet", f"Snippet '{name}' salvo!")

    def manage_snippets(self):
        """Gerencia snippets salvos"""
        dialog = SnippetManagerDialog(self.ide, self.snippets)
        if dialog.exec():
            selected_snippet = dialog.get_selected_snippet()
            if selected_snippet:
                self.insert_snippet(
                    selected_snippet)

    def insert_snippet(self, snippet_name):
        """Insere um snippet no editor atual"""
        editor = self.ide.get_current_editor()
        if not editor or snippet_name not in self.snippets:
            return

        snippet = self.snippets[snippet_name]['code']
        cursor = editor.textCursor()
        cursor.insertText(snippet)



class SnippetManagerDialog(QDialog):
    def __init__(self, parent, snippets):
        super().__init__(parent)
        self.snippets = snippets
        self.selected_snippet = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Gerenciador de Snippets")
        self.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout()

        # Lista de snippets
        self.snippets_list = QListWidget()
        self.snippets_list.addItems(self.snippets.keys())
        layout.addWidget(self.snippets_list)

        # Preview
        layout.addWidget(QLabel("Preview:"))
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        layout.addWidget(self.preview_edit)

        self.snippets_list.currentItemChanged.connect(
            self.on_snippet_selected)

        # Botões
        btn_layout = QHBoxLayout()
        self.insert_btn = QPushButton("Inserir")
        self.insert_btn.clicked.connect(self.insert_snippet)
        btn_layout.addWidget(self.insert_btn)

        self.delete_btn = QPushButton("Excluir")
        self.delete_btn.clicked.connect(self.delete_snippet)
        btn_layout.addWidget(self.delete_btn)

        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def on_snippet_selected(self, current, previous):
        if current:
            snippet_name = current.text()
            self.preview_edit.setPlainText(
                self.snippets[snippet_name]['code'])

    def insert_snippet(self):
        current_item = self.snippets_list.currentItem()
        if current_item:
            self.selected_snippet = current_item.text()
            self.accept()

    def delete_snippet(self):
        current_item = self.snippets_list.currentItem()
        if current_item:
            name = current_item.text()
            reply = QMessageBox.question(
                self, "Confirmar", f"Excluir snippet '{name}'?")
            if reply == QMessageBox.Yes:
                del self.snippets[name]
                self.snippets_list.takeItem(
                    self.snippets_list.row(current_item))

    def get_selected_snippet(self):
        return self.selected_snippet
