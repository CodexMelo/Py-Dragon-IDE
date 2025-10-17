from PySide6.QtWidgets import QDialog, QTextEdit, QPushButton
from core.plugin_system import PluginBase
import subprocess


class GitIntegrationPlugin(PluginBase):
    """Integração com Git"""

    def __init__(self, ide_instance):
        super().__init__(ide_instance)
        self.info = PluginInfo(
            name="Git Integration",
            version="1.0.0",
            author="Py Dragon Team",
            description="Integração com controle de versão Git"
        )

    def initialize(self):
        self.git_actions = []

    def shutdown(self):
        pass

    def get_actions(self):
        actions = [
            QAction("📊 Status Git", self.ide),
            QAction("🔄 Commit", self.ide),
            QAction("📤 Push", self.ide),
            QAction("📥 Pull", self.ide)
        ]

        actions[0].triggered.connect(self.show_git_status)
        actions[1].triggered.connect(self.show_commit_dialog)
        actions[2].triggered.connect(self.git_push)
        actions[3].triggered.connect(self.git_pull)

        return actions

    def show_git_status(self):
        """Mostra status do Git"""
        if not self.ide.project_path:
            QMessageBox.information(
                self.ide, "Git", "Nenhum projeto aberto")
            return

        try:
            result = subprocess.run(
                ["git", "status"],
                capture_output=True, text=True, cwd=self.ide.project_path
            )

            dialog = QDialog(self.ide)
            dialog.setWindowTitle("Status Git")
            dialog.setGeometry(300, 300, 600, 400)

            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setPlainText(
                result.stdout if result.returncode == 0 else result.stderr)
            layout.addWidget(text_edit)

            dialog.setLayout(layout)
            dialog.exec()

        except Exception as e:
            QMessageBox.warning(
                self.ide, "Erro Git", f"Erro ao executar git status: {str(e)}")

    def show_commit_dialog(self):
        """Mostra diálogo de commit"""
        dialog = GitCommitDialog(self.ide)
        if dialog.exec():
            message = dialog.get_commit_message()
            self.git_commit(message)

    def git_commit(self, message):
        """Executa commit Git"""
        try:
            commands = [
                ["git", "add", "."],
                ["git", "commit",
                 "-m", message]
            ]

            for cmd in commands:
                result = subprocess.run(
                    cmd, cwd=self.ide.project_path, capture_output=True, text=True)
                if result.returncode != 0:
                    QMessageBox.warning(
                        self.ide, "Erro Git", result.stderr)
                    return

            QMessageBox.information(
                self.ide, "Git", "Commit realizado com sucesso!")

        except Exception as e:
            QMessageBox.warning(
                self.ide, "Erro Git", f"Erro no commit: {str(e)}")

    def git_push(self):
        """Executa push Git"""
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=self.ide.project_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                QMessageBox.information(
                    self.ide, "Git", "Push realizado com sucesso!")
            else:
                QMessageBox.warning(
                    self.ide, "Erro Git", result.stderr)

        except Exception as e:
            QMessageBox.warning(
                self.ide, "Erro Git", f"Erro no push: {str(e)}")

    def git_pull(self):
        """Executa pull Git"""
        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=self.ide.project_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                QMessageBox.information(
                    self.ide, "Git", "Pull realizado com sucesso!")
            else:
                QMessageBox.warning(
                    self.ide, "Erro Git", result.stderr)

        except Exception as e:
            QMessageBox.warning(
                self.ide, "Erro Git", f"Erro no pull: {str(e)}")



class GitCommitDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Commit Git")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Mensagem do commit:"))
        self.message_edit = QTextEdit()
        layout.addWidget(self.message_edit)

        btn_layout = QHBoxLayout()
        self.commit_btn = QPushButton("Commit")
        self.commit_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.commit_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_commit_message(self):
        return self.message_edit.toPlainText().strip()
