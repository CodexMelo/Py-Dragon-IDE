# ===== CORREÇÃO DE ENCODING PARA WINDOWS =====
import os
import sys

# Forçar UTF-8 no Windows
if os.name == 'nt':
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr is not None:
        sys.stderr.reconfigure(encoding='utf-8')

    # Configurar environment para UTF-8
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
import ast
import glob



# ===== IMPORTS ADICIONAIS =====
import importlib
import importlib.util
import inspect
import json
import platform
import re
import shutil
import subprocess
import tempfile
import textwrap
import threading
import time
import traceback
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List
from urllib.request import urlretrieve

try:
    import jedi

    JEDI_AVAILABLE = True
except ImportError:
    JEDI_AVAILABLE = False
    print("Jedi não disponível - usando autocomplete básico")
from typing import Any, Dict, List, Set

from PySide6.QtCore import (
    QDir,
    QModelIndex,
    QProcess,
    QRegularExpression,
    QSize,
    QStringListModel,
    Qt,
    QThread,
    QTimer,
    QUrl,
    Signal as QSignal
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QFontDatabase,
    QGuiApplication,
    QKeyEvent,
    QPainter,
    QPalette,
    QShortcut,
    QSyntaxHighlighter,
    QTextBlockUserData,
    QTextCharFormat,
    QTextCursor,
    QTextOption, QKeySequence
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDockWidget,
    QFileDialog,
    QFileSystemModel,
    QFontDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSplitter,
    QStyledItemDelegate,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeView,
)
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QVBoxLayout as QVBoxLayoutDialog
from PySide6.QtWidgets import QWidget


@dataclass
class PluginInfo:
    name: str
    version: str
    author: str
    description: str
    enabled: bool = True


class PluginBase(ABC):
    """Classe base para todos os plugins"""

    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.info = PluginInfo(
            name="Plugin Base",
            version="1.0.0",
            author="Desconhecido",
            description="Plugin base"
        )

    @abstractmethod
    def initialize(self):
        """Inicializa o plugin"""
        pass

    @abstractmethod
    def shutdown(self):
        """Finaliza o plugin"""
        pass

    def get_actions(self) -> List[QAction]:
        """Retorna ações do plugin para a interface"""
        return []

    def get_menu_items(self) -> Dict[str, List[QAction]]:
        """Retorna itens de menu do plugin"""
        return {}

    def get_toolbar_items(self) -> List[QAction]:
        """Retorna itens para a toolbar"""
        return []


class PluginManager:
    """Gerenciador de plugins"""

    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.plugins: Dict[str, PluginBase] = {}
        self.plugins_dir = os.path.join(
            os.path.expanduser("~"), ".py_dragon_plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)

    def discover_plugins(self):
        """Descobre plugins disponíveis"""
        plugins = {}

        # Plugins internos
        internal_plugins = [
            CodeFormatterPlugin,
            GitIntegrationPlugin,
            CodeMetricsPlugin,
            SnippetManagerPlugin
        ]

        for plugin_class in internal_plugins:
            try:
                plugin = plugin_class(
                    self.ide)
                plugins[plugin.info.name] = plugin
            except Exception as e:
                print(
                    f"Erro ao carregar plugin interno {plugin_class.__name__}: {e}")

        # Plugins externos
        for file in os.listdir(self.plugins_dir):
            if file.endswith(
                    '.py') and not file.startswith('_'):
                try:
                    plugin_path = os.path.join(
                        self.plugins_dir, file)
                    spec = importlib.util.spec_from_file_location(
                        file[:-3], plugin_path)
                    module = importlib.util.module_from_spec(
                        spec)
                    spec.loader.exec_module(
                        module)

                    for attr_name in dir(
                            module):
                        attr = getattr(
                            module, attr_name)
                        if (inspect.isclass(attr) and
                                issubclass(attr, PluginBase) and
                                attr != PluginBase):
                            plugin = attr(
                                self.ide)
                            plugins[plugin.info.name] = plugin

                except Exception as e:
                    print(
                        f"Erro ao carregar plugin externo {file}: {e}")

        return plugins

    def load_plugins(self):
        """Carrega todos os plugins"""
        self.plugins = self.discover_plugins()

        for name, plugin in self.plugins.items():
            try:
                plugin.initialize()
                print(
                    f"✅ Plugin carregado: {name} v{plugin.info.version}")
            except Exception as e:
                print(
                    f"❌ Erro ao inicializar plugin {name}: {e}")

    def shutdown_plugins(self):
        """Finaliza todos os plugins de forma segura"""
        if not hasattr(self, 'plugins'):
            return

        for name, plugin in list(self.plugins.items()):
            try:
                if hasattr(
                        plugin, 'shutdown'):
                    plugin.shutdown()
                print(
                    f"✅ Plugin finalizado: {name}")
            except Exception as e:
                print(
                    f"❌ Erro ao finalizar plugin {name}: {e}")

        # Limpa dicionário
        self.plugins.clear()

    def get_plugin_actions(self):
        """Obtém todas as ações dos plugins"""
        actions = []
        for plugin in self.plugins.values():
            if plugin.info.enabled:
                actions.extend(
                    plugin.get_actions())
        return actions

    def install_plugin(self, plugin_path_or_url):
        """Instala um novo plugin"""
        try:
            if plugin_path_or_url.startswith(
                    'http'):
                # Download de URL
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix='.zip')
                urlretrieve(
                    plugin_path_or_url, temp_file.name)
                plugin_path = temp_file.name
            else:
                plugin_path = plugin_path_or_url

            # Extrai/instala o plugin
            if plugin_path.endswith('.zip'):
                with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                    zip_ref.extractall(
                        self.plugins_dir)
            elif plugin_path.endswith('.py'):
                shutil.copy(
                    plugin_path, self.plugins_dir)

            QMessageBox.information(
                self.ide, "Sucesso", "Plugin instalado com sucesso!")

        except Exception as e:
            QMessageBox.warning(
                self.ide, "Erro", f"Falha na instalação: {str(e)}")


# ===== PLUGINS INTERNOS =====

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


# ===== DIÁLOGOS PARA OS PLUGINS =====

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
        self.preview_edit.setFont(QFont("Consolas", 10))
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


class DeployDialog(QDialog):
    def __init__(self, parent, project_path):
        super().__init__(parent)
        self.project_path = project_path
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Configuração de Deploy")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        # Tipo de deploy
        layout.addWidget(QLabel("Tipo de deploy:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["zip", "git", "ftp"])
        layout.addWidget(self.type_combo)

        # Configurações específicas
        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout()
        self.config_widget.setLayout(self.config_layout)
        layout.addWidget(self.config_widget)

        self.type_combo.currentTextChanged.connect(
            self.update_config_fields)
        self.update_config_fields("zip")

        # Botões
        btn_layout = QHBoxLayout()
        self.deploy_btn = QPushButton("Deploy")
        self.deploy_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.deploy_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def update_config_fields(self, deploy_type):
        # Limpa campos anteriores
        for i in reversed(range(self.config_layout.count())):
            self.config_layout.itemAt(
                i).widget().setParent(None)

        if deploy_type == "zip":
            self.config_layout.addWidget(
                QLabel("Diretório de saída:"))
            self.output_dir = QLineEdit(
                os.path.dirname(self.project_path))
            self.config_layout.addWidget(
                self.output_dir)

        elif deploy_type == "git":
            self.config_layout.addWidget(
                QLabel("Repositório remoto:"))
            self.remote = QLineEdit("origin")
            self.config_layout.addWidget(
                self.remote)

            self.config_layout.addWidget(
                QLabel("Branch:"))
            self.branch = QLineEdit("main")
            self.config_layout.addWidget(
                self.branch)

            self.config_layout.addWidget(
                QLabel("Mensagem do commit:"))
            self.commit_message = QLineEdit(
                "Deploy automático")
            self.config_layout.addWidget(
                self.commit_message)

        elif deploy_type == "ftp":
            self.config_layout.addWidget(
                QLabel("Servidor FTP:"))
            self.ftp_server = QLineEdit()
            self.config_layout.addWidget(
                self.ftp_server)

            self.config_layout.addWidget(
                QLabel("Usuário:"))
            self.ftp_user = QLineEdit()
            self.config_layout.addWidget(
                self.ftp_user)

            self.config_layout.addWidget(
                QLabel("Senha:"))
            self.ftp_password = QLineEdit()
            self.ftp_password.setEchoMode(
                QLineEdit.Password)
            self.config_layout.addWidget(
                self.ftp_password)

    def get_deploy_config(self):
        deploy_type = self.type_combo.currentText()
        config = {'type': deploy_type}

        if deploy_type == "zip":
            config['output_dir'] = self.output_dir.text()
        elif deploy_type == "git":
            config['remote'] = self.remote.text()
            config['branch'] = self.branch.text()
            config['commit_message'] = self.commit_message.text(
            )
        elif deploy_type == "ftp":
            config['server'] = self.ftp_server.text()
            config['user'] = self.ftp_user.text()
            config['password'] = self.ftp_password.text()

        return config


##############

class ContextAwareCompleter:
    """Completador inteligente baseado em contexto"""

    def __init__(self):
        self.analyzer = CodeAnalyzer()

    def get_completions(
            self,
            code,
            cursor_position,
            file_path="",
            project_path=""):
        """Obtém sugestões baseadas no contexto"""
        analysis = self.analyzer.analyze_code(code, file_path)
        context = self.get_current_context(
            code, cursor_position)

        if context['type'] == 'import':
            return self.get_import_completions(
                context, analysis)
        elif context['type'] == 'attribute':
            return self.get_attribute_completions(
                context, analysis, project_path)
        else:
            return self.get_general_completions(
                analysis)

    def get_current_context(self, code, cursor_position):
        """Detecta contexto atual"""
        text_before = code[:cursor_position]
        current_line = text_before.split(
            '\n')[-1] if '\n' in text_before else text_before

        if 'import' in current_line:
            if 'from' in current_line:
                parts = current_line.split(
                    'import')
                if len(parts) > 1:
                    module = parts[0].replace(
                        'from', '').strip()
                    return {
                        'type': 'from_import', 'module': module}
            return {'type': 'import'}

        elif current_line.rstrip().endswith('.'):
            line_before_dot = current_line.rstrip()[
                :-1]
            parts = line_before_dot.split()
            if parts:
                return {
                    'type': 'attribute', 'object': parts[-1]}

        return {'type': 'general'}

    def get_import_completions(self, context, analysis):
        """Sugestões para imports"""
        suggestions = set()

        if context['type'] == 'import':
            common_modules = [
                'os', 'sys', 'json', 're', 'datetime', 'math', 'random']
            suggestions.update(common_modules)

        elif context['type'] == 'from_import':
            module = context['module']
            if module in analysis['imports']:
                suggestions.update(
                    analysis['imports'][module])

        return sorted(list(suggestions))

    def get_attribute_completions(self, context, analysis, project_path):
        """Sugestões para atributos (obj.metodo)"""
        obj_name = context['object']
        suggestions = set()

        # Métodos de classes locais
        if obj_name in analysis['symbols']['classes']:
            methods = analysis['symbols']['methods'].get(
                obj_name, set())
            suggestions.update(methods)

        # Métodos comuns baseados no nome
        common_methods = {
            'str': ['upper()', 'lower()', 'strip()', 'split()', 'replace()'],
            'list': ['append()', 'remove()', 'pop()', 'sort()', 'reverse()'],
            'dict': ['get()', 'keys()', 'values()', 'items()', 'update()'],
        }

        for pattern, methods in common_methods.items():
            if pattern in obj_name.lower():
                suggestions.update(
                    methods)

        # Tenta obter do cache de módulos
        try:
            cached = module_cache_manager.get_module_methods(
                obj_name, "", project_path)
            suggestions.update(cached)
        except:
            pass

        return sorted(list(suggestions))

    def get_general_completions(self, analysis):
        """Sugestões gerais"""
        suggestions = set()

        # Palavras-chave
        keywords = [
            "if", "else", "for", "while", "def", "class", "import", "from"]
        suggestions.update(keywords)

        # Símbolos locais
        suggestions.update(analysis['symbols']['functions'])
        suggestions.update(analysis['symbols']['classes'])
        suggestions.update(analysis['symbols']['variables'])

        # Módulos importados
        for module in analysis['imports']:
            suggestions.add(module)

        return sorted(list(suggestions))


class PythonVersionManager:
    """Gerenciador de versões Python instaladas e para download"""

    def __init__(self):
        self.installed_versions = []
        self.available_versions = []
        self.scan_installed_versions()

    def scan_installed_versions(self):
        """Detecta versões Python instaladas no sistema"""
        self.installed_versions = []

        # Locais comuns de instalação
        search_paths = []

        if platform.system() == "Windows":
            search_paths = [
                "C:\\Python*",
                "C:\\Program Files\\Python*",
                "C:\\Users\\*\\AppData\\Local\\Programs\\Python\\Python*"
            ]
        elif platform.system() == "Linux":
            search_paths = [
                "/usr/bin/python*",
                "/usr/local/bin/python*",
                "/opt/python*"
            ]
        elif platform.system() == "Darwin":  # macOS
            search_paths = [
                "/usr/local/bin/python*",
                "/opt/homebrew/bin/python*",
                "/Applications/Python*"
            ]

        # Busca por executáveis Python
        for path_pattern in search_paths:
            for python_path in glob.glob(
                    path_pattern):
                if os.path.isfile(python_path) and not python_path.endswith(
                        ('config', 'm')):
                    try:
                        result = subprocess.run(
                            [python_path, "--version"],
                            capture_output=True, text=True, timeout=2
                        )
                        if result.returncode == 0:
                            version = result.stdout.strip()
                            self.installed_versions.append({
                                'path': python_path,
                                'version': version,
                                'type': 'system'
                            })
                    except:
                        pass

        # Remove duplicatas
        seen = set()
        unique_versions = []
        for v in self.installed_versions:
            key = v['path']
            if key not in seen:
                seen.add(key)
                unique_versions.append(
                    v)

        self.installed_versions = unique_versions

    def get_available_versions(self):
        """Obtém versões disponíveis para download"""
        # Esta é uma implementação simplificada
        # Em produção, você faria web scraping do site oficial
        # do Python
        self.available_versions = [
            {'version': 'Python 3.12.0',
             'url': 'https://www.python.org/downloads/release/python-3120/'},
            {'version': 'Python 3.11.6',
             'url': 'https://www.python.org/downloads/release/python-3116/'},
            {'version': 'Python 3.10.12',
             'url': 'https://www.python.org/downloads/release/python-31012/'},
            {'version': 'Python 3.9.18',
             'url': 'https://www.python.org/downloads/release/python-3918/'},
        ]
        return self.available_versions

    def set_as_default(self, python_path):
        """Define uma versão Python como padrão no IDE"""
        try:
            # Verifica se é válido
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return python_path
        except:
            pass
        return None


class HybridCompleter:
    """Híbrido: Jedi + análise própria - CORRIGIDA"""

    def __init__(self):
        self.jedi_completer = JediCompleter() if JEDI_AVAILABLE else None
        self.context_completer = ContextAwareCompleter()

    def get_completions(
            self,
            text,
            cursor_position,
            file_path="",
            project_path=""):
        """Obtém sugestões baseadas no contexto - CORRIGIDA"""
        suggestions = set()

        # Tenta Jedi primeiro (mais preciso)
        if self.jedi_completer:
            try:
                # Calcula linha e coluna
                # para Jedi
                text_before = text[:cursor_position]
                line = text_before.count(
                    '\n') + 1
                column = len(
                    text_before.split('\n')[-1]) + 1

                jedi_suggestions = self.jedi_completer.get_completions(
                    text, (line, column), file_path)
                suggestions.update(
                    jedi_suggestions)
            except Exception as e:
                print(
                    f"Erro no Jedi: {e}")

        # Fallback para análise própria
        own_suggestions = self.context_completer.get_completions(
            text, cursor_position, file_path, project_path)
        suggestions.update(own_suggestions)

        return sorted(list(suggestions))[:15]


# ===== DIÁLOGO DO GESTOR DE VERSÕES =====

class PythonVersionDialog(QDialog):
    def __init__(self, version_manager, parent=None):
        super().__init__(parent)
        self.version_manager = version_manager
        self.setWindowTitle("🐍 Gerenciador de Versões Python")
        self.setGeometry(300, 300, 800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Abas
        tabs = QTabWidget()

        # Aba: Versões Instaladas
        installed_tab = QWidget()
        installed_layout = QVBoxLayout()

        # Lista de versões instaladas
        self.installed_list = QListWidget()
        self.refresh_installed_versions()
        installed_layout.addWidget(
            QLabel("Versões Python Instaladas:"))
        installed_layout.addWidget(self.installed_list)

        # Botões para versões instaladas
        installed_buttons = QHBoxLayout()
        self.set_default_btn = QPushButton(
            "Definir como Padrão")
        self.set_default_btn.clicked.connect(
            self.set_default_version)
        installed_buttons.addWidget(self.set_default_btn)

        self.refresh_btn = QPushButton("🔄 Atualizar Lista")
        self.refresh_btn.clicked.connect(
            self.refresh_installed_versions)
        installed_buttons.addWidget(self.refresh_btn)

        installed_layout.addLayout(installed_buttons)
        installed_tab.setLayout(installed_layout)

        # Aba: Download de Versões
        download_tab = QWidget()
        download_layout = QVBoxLayout()

        download_layout.addWidget(
            QLabel("Versões Disponíveis para Download:"))

        self.available_list = QListWidget()
        self.load_available_versions()
        download_layout.addWidget(self.available_list)

        download_buttons = QHBoxLayout()
        self.download_btn = QPushButton(
            "🌐 Abrir Página de Download")
        self.download_btn.clicked.connect(
            self.open_download_page)
        download_buttons.addWidget(self.download_btn)

        download_layout.addLayout(download_buttons)
        download_tab.setLayout(download_layout)

        tabs.addTab(installed_tab, "📥 Instaladas")
        tabs.addTab(download_tab, "🌐 Download")

        layout.addWidget(tabs)

        # Botões de ação
        button_layout = QHBoxLayout()
        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def refresh_installed_versions(self):
        """Atualiza lista de versões instaladas"""
        self.version_manager.scan_installed_versions()
        self.installed_list.clear()

        for version in self.version_manager.installed_versions:
            item_text = f"{version['version']} - {version['path']}"
            self.installed_list.addItem(item_text)

    def load_available_versions(self):
        """Carrega versões disponíveis para download"""
        versions = self.version_manager.get_available_versions()
        self.available_list.clear()

        for version in versions:
            self.available_list.addItem(
                version['version'])

    def set_default_version(self):
        """Define a versão selecionada como padrão"""
        current_item = self.installed_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Aviso", "Selecione uma versão Python!")
            return

        # Extrai o caminho do item
        item_text = current_item.text()
        path = item_text.split(" - ")[1]

        new_default = self.version_manager.set_as_default(path)
        if new_default:
            QMessageBox.information(
                self, "Sucesso", f"Python padrão definido para:\n{new_default}")
            if hasattr(
                    self.parent(), 'update_python_version'):
                self.parent().update_python_version(new_default)
        else:
            QMessageBox.warning(
                self, "Erro", "Não foi possível definir esta versão como padrão.")

    def open_download_page(self):
        """Abre página de download da versão selecionada"""
        current_item = self.available_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Aviso", "Selecione uma versão para download!")
            return

        version_name = current_item.text()
        versions = self.version_manager.get_available_versions()

        for version in versions:
            if version['version'] == version_name:
                import webbrowser
                webbrowser.open(
                    version['url'])
                QMessageBox.information(self, "Download",
                                        f"Abriu a página de download para {version_name}")
                break


# ===== LOCALIZADOR DE TEXTOS SIMILARES APRIMORADO =====

class AdvancedFindSimilarDialog(QDialog):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.current_match_index = 0
        self.all_matches = []
        self.setWindowTitle("🔍 Localizador de Textos Similares")
        self.setGeometry(400, 300, 700, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Controles de busca
        search_group = QGroupBox("Configurações de Busca")
        search_layout = QVBoxLayout()

        # Campo de busca
        search_field_layout = QHBoxLayout()
        search_field_layout.addWidget(
            QLabel("Texto para buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Digite o texto que deseja encontrar...")
        self.search_input.textChanged.connect(
            self.on_search_text_changed)
        search_field_layout.addWidget(self.search_input)
        search_layout.addLayout(search_field_layout)

        # Opções de busca
        options_layout = QHBoxLayout()

        self.case_sensitive = QCheckBox(
            "Diferenciar maiúsculas/minúsculas")
        options_layout.addWidget(self.case_sensitive)

        self.whole_word = QCheckBox("Palavra inteira")
        options_layout.addWidget(self.whole_word)

        self.regex_mode = QCheckBox("Usar expressões regulares")
        options_layout.addWidget(self.regex_mode)

        search_layout.addLayout(options_layout)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # Área de resultados
        results_group = QGroupBox("Resultados da Busca")
        results_layout = QVBoxLayout()

        # Contador de resultados
        self.results_count = QLabel(
            "Digite um texto para buscar...")
        results_layout.addWidget(self.results_count)

        # Lista de resultados
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(
            self.go_to_match)
        results_layout.addWidget(self.results_list)

        # Navegação
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Anterior")
        self.prev_btn.clicked.connect(self.previous_match)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Próximo ▶")
        self.next_btn.clicked.connect(self.next_match)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        self.select_all_btn = QPushButton("Selecionar Todos")
        self.select_all_btn.clicked.connect(
            self.select_all_matches)
        nav_layout.addWidget(self.select_all_btn)

        results_layout.addLayout(nav_layout)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Botões de ação
        button_layout = QHBoxLayout()

        self.replace_btn = QPushButton("Substituir Selecionado")
        self.replace_btn.clicked.connect(self.replace_current)
        self.replace_btn.setEnabled(False)
        button_layout.addWidget(self.replace_btn)

        self.replace_all_btn = QPushButton("Substituir Todos")
        self.replace_all_btn.clicked.connect(self.replace_all)
        self.replace_all_btn.setEnabled(False)
        button_layout.addWidget(self.replace_all_btn)

        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_search_text_changed(self):
        """Executa busca quando o texto muda"""
        search_text = self.search_input.text().strip()
        if len(search_text) >= 1:  # Busca a partir de 1 caractere
            self.perform_search()
        else:
            self.clear_results()

    def perform_search(self):
        """Executa a busca com as configurações atuais"""
        search_text = self.search_input.text().strip()
        if not search_text:
            return

        full_text = self.editor.toPlainText()
        self.all_matches = []
        self.current_match_index = 0

        # Prepara padrão de busca
        pattern = search_text
        flags = 0

        if self.case_sensitive.isChecked():
            flags = re.IGNORECASE if not self.case_sensitive.isChecked() else 0

        if self.whole_word.isChecked() and not self.regex_mode.isChecked():
            pattern = r'\b' + \
                      re.escape(search_text) + r'\b'
        elif not self.regex_mode.isChecked():
            pattern = re.escape(search_text)

        try:
            if self.regex_mode.isChecked():
                regex = re.compile(
                    pattern, flags)
            else:
                regex = re.compile(
                    pattern, flags)

            # Encontra todas as ocorrências
            for match in regex.finditer(full_text):
                start_pos = match.start()
                end_pos = match.end()

                # Encontra a linha
                line_start = full_text.rfind(
                    '\n', 0, start_pos) + 1
                line_end = full_text.find(
                    '\n', start_pos)
                if line_end == -1:
                    line_end = len(
                        full_text)

                line_text = full_text[line_start:line_end]
                line_num = full_text.count(
                    '\n', 0, line_start) + 1

                # Destaca o texto
                # encontrado na
                # visualização
                preview_start = max(
                    0, start_pos - line_start - 20)
                preview_end = min(
                    len(line_text), end_pos - line_start + 20)
                preview_text = line_text[preview_start:preview_end]

                # Adiciona ellipsis se
                # necessário
                if preview_start > 0:
                    preview_text = "..." + preview_text
                if preview_end < len(
                        line_text):
                    preview_text = preview_text + "..."

                self.all_matches.append({
                    'start': start_pos,
                    'end': end_pos,
                    'line': line_num,
                    'preview': preview_text,
                    'matched_text': match.group()
                })

            self.update_results_display()

        except re.error as e:
            self.results_count.setText(
                f"❌ Erro na expressão regular: {str(e)}")
            self.clear_results()

    def update_results_display(self):
        """Atualiza a exibição dos resultados"""
        self.results_list.clear()

        if not self.all_matches:
            self.results_count.setText(
                "Nenhum resultado encontrado")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.replace_btn.setEnabled(False)
            self.replace_all_btn.setEnabled(False)
            return

        # Preenche a lista
        for i, match in enumerate(self.all_matches):
            item_text = f"Linha {match['line']}: {match['preview']}"
            item = QListWidgetItem(item_text)
            if i == self.current_match_index:
                item.setBackground(
                    QColor(86, 156, 214))
                item.setForeground(
                    QColor(255, 255, 255))
            self.results_list.addItem(item)

        # Atualiza contador e navegação
        self.results_count.setText(
            f"Encontrados {len(self.all_matches)} resultados • Atual: {self.current_match_index + 1}")
        self.prev_btn.setEnabled(len(self.all_matches) > 1)
        self.next_btn.setEnabled(len(self.all_matches) > 1)
        self.replace_btn.setEnabled(True)
        self.replace_all_btn.setEnabled(True)

        # Rola para o item atual
        if self.all_matches:
            self.results_list.setCurrentRow(
                self.current_match_index)
            self.highlight_current_match()

    def highlight_current_match(self):
        """Destaca a ocorrência atual no editor"""
        if not self.all_matches or self.current_match_index >= len(
                self.all_matches):
            return

        match = self.all_matches[self.current_match_index]

        # Cria seleção no editor
        cursor = self.editor.textCursor()
        cursor.setPosition(match['start'])
        cursor.setPosition(match['end'], QTextCursor.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

        # Garante que a linha esteja visível
        self.editor.centerCursor()

    def next_match(self):
        """Vai para a próxima ocorrência"""
        if self.all_matches:
            self.current_match_index = (
                                               self.current_match_index + 1) % len(self.all_matches)
            self.update_results_display()

    def previous_match(self):
        """Vai para a ocorrência anterior"""
        if self.all_matches:
            self.current_match_index = (
                                               self.current_match_index - 1) % len(self.all_matches)
            self.update_results_display()

    def go_to_match(self, item):
        """Vai para a ocorrência clicada na lista"""
        row = self.results_list.row(item)
        if 0 <= row < len(self.all_matches):
            self.current_match_index = row
            self.update_results_display()

    def select_all_matches(self):
        """Seleciona todas as ocorrências no editor"""
        if not self.all_matches:
            return

        cursor = self.editor.textCursor()
        cursor.setPosition(self.all_matches[0]['start'])

        for match in self.all_matches[1:]:
            cursor.setPosition(
                match['start'], QTextCursor.KeepAnchor)

        cursor.setPosition(
            self.all_matches[-1]['end'], QTextCursor.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def replace_current(self):
        """Substitui a ocorrência atual"""
        if not self.all_matches or self.current_match_index >= len(
                self.all_matches):
            return

        new_text, ok = QInputDialog.getText(
            self, "Substituir", "Substituir por:")
        if ok and new_text is not None:
            match = self.all_matches[self.current_match_index]

            # Substitui no texto
            cursor = self.editor.textCursor()
            cursor.setPosition(match['start'])
            cursor.setPosition(
                match['end'], QTextCursor.KeepAnchor)
            cursor.insertText(new_text)

            # Atualiza a busca
            self.perform_search()

    def replace_all(self):
        """Substitui todas as ocorrências"""
        if not self.all_matches:
            return

        new_text, ok = QInputDialog.getText(
            self, "Substituir Todos", "Substituir por:")
        if ok and new_text is not None:
            # Ordena por posição (decrescente) para
            # evitar problemas com índices
            sorted_matches = sorted(
                self.all_matches, key=lambda x: x['start'], reverse=True)

            cursor = self.editor.textCursor()

            for match in sorted_matches:
                cursor.setPosition(
                    match['start'])
                cursor.setPosition(
                    match['end'], QTextCursor.KeepAnchor)
                cursor.insertText(
                    new_text)

            # Atualiza a busca
            self.perform_search()

    def clear_results(self):
        """Limpa os resultados"""
        self.all_matches = []
        self.current_match_index = 0
        self.results_list.clear()
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.replace_btn.setEnabled(False)
        self.replace_all_btn.setEnabled(False)


# ===== SISTEMA DE TEMAS FUNCIONAL =====

class ThemeManager:
    """Gerenciador de temas para o IDE"""

    def __init__(self):
        self.themes = {
            "Dark Professional": self.dark_professional_theme(),
            "Dark Blue": self.dark_blue_theme(),
            "Light Modern": self.light_modern_theme(),
            "Monokai": self.monokai_theme(),
            "Solarized Dark": self.solarized_dark_theme(),
            "Solarized Light": self.solarized_light_theme(),
        }
        self.current_theme = "Dark Professional"

    def dark_professional_theme(self):
        return {
            "name": "Dark Professional",
            "type": "dark",
            "colors": {
                "background": "#1e1e1e",
                "foreground": "#d4d4d4",
                "selection": "#264f78",
                "cursor": "#569cd6",
                "comment": "#6a9955",
                "string": "#ce9178",
                "number": "#b5cea8",
                "keyword": "#569cd6",
                "function": "#dcdcaa",
                "class": "#4ec9b0",
                "error": "#f44747",
                "warning": "#ffcc66",
                "info": "#9cdcfe"
            },
            "syntax": {
                "keyword": "#569cd6",
                "string": "#ce9178",
                "comment": "#6a9955",
                "number": "#b5cea8",
                "function": "#dcdcaa",
                "class": "#4ec9b0",
                "builtin": "#4ec9b0"
            }
        }

    def dark_blue_theme(self):
        return {
            "name": "Dark Blue",
            "type": "dark",
            "colors": {
                "background": "#0d1117",
                "foreground": "#c9d1d9",
                "selection": "#1c3b5a",
                "cursor": "#58a6ff",
                "comment": "#8b949e",
                "string": "#a5d6ff",
                "number": "#79c0ff",
                "keyword": "#ff7b72",
                "function": "#d2a8ff",
                "class": "#ffa657",
                "error": "#f85149",
                "warning": "#d29922",
                "info": "#a5d6ff"
            }
        }

    def light_modern_theme(self):
        return {
            "name": "Light Modern",
            "type": "light",
            "colors": {
                "background": "#ffffff",
                "foreground": "#24292e",
                "selection": "#0366d625",
                "cursor": "#0969da",
                "comment": "#6a737d",
                "string": "#032f62",
                "number": "#005cc5",
                "keyword": "#d73a49",
                "function": "#6f42c1",
                "class": "#22863a",
                "error": "#cb2431",
                "warning": "#f66a0a",
                "info": "#005cc5"
            }
        }

    def monokai_theme(self):
        return {
            "name": "Monokai",
            "type": "dark",
            "colors": {
                "background": "#272822",
                "foreground": "#f8f8f2",
                "selection": "#49483e",
                "cursor": "#f92672",
                "comment": "#75715e",
                "string": "#e6db74",
                "number": "#ae81ff",
                "keyword": "#f92672",
                "function": "#a6e22e",
                "class": "#a6e22e",
                "error": "#f44747",
                "warning": "#ffd700",
                "info": "#66d9ef"
            }
        }

    def solarized_dark_theme(self):
        return {
            "name": "Solarized Dark",
            "type": "dark",
            "colors": {
                "background": "#002b36",
                "foreground": "#839496",
                "selection": "#073642",
                "cursor": "#839496",
                "comment": "#586e75",
                "string": "#2aa198",
                "number": "#d33682",
                "keyword": "#859900",
                "function": "#b58900",
                "class": "#268bd2",
                "error": "#dc322f",
                "warning": "#cb4b16",
                "info": "#2aa198"
            }
        }

    def solarized_light_theme(self):
        return {
            "name": "Solarized Light",
            "type": "light",
            "colors": {
                "background": "#fdf6e3",
                "foreground": "#657b83",
                "selection": "#eee8d5",
                "cursor": "#657b83",
                "comment": "#93a1a1",
                "string": "#2aa198",
                "number": "#d33682",
                "keyword": "#859900",
                "function": "#b58900",
                "class": "#268bd2",
                "error": "#dc322f",
                "warning": "#cb4b16",
                "info": "#2aa198"
            }
        }

    def get_theme(self, theme_name):
        return self.themes.get(
            theme_name, self.themes["Dark Professional"])

    def get_theme_names(self):
        return list(self.themes.keys())


class ThemeDialog(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.current_theme = theme_manager.current_theme
        self.setWindowTitle("🎨 Gerenciador de Temas")
        self.setGeometry(400, 300, 800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()

        # Lista de temas
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Selecione um tema:"))

        self.theme_list = QListWidget()
        self.theme_list.addItems(
            self.theme_manager.get_theme_names())
        self.theme_list.currentItemChanged.connect(
            self.on_theme_selected)
        left_panel.addWidget(self.theme_list)

        # Pré-visualização
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Pré-visualização:"))

        self.preview_widget = QWidget()
        self.preview_widget.setMinimumSize(400, 300)
        self.preview_layout = QVBoxLayout(self.preview_widget)

        # Simula um editor na pré-visualização
        self.preview_editor = QPlainTextEdit()
        self.preview_editor.setPlainText("""# Exemplo de código Python
                                def hello_world():
                                                \"\"\"Função de exemplo\"\"\"
                                                name = "Mundo"
                                                number = 42
                                                # Saída: Olá, Mundo!
                                                print(f"Olá, {name}!")
                                                return number

                                class ExampleClass:
                                                def __init__(self):
                                                                self.value = 123

                                                def calculate(self, x):
                                                                return x * 2
                                """)
        self.preview_editor.setReadOnly(True)
        self.preview_layout.addWidget(self.preview_editor)

        right_panel.addWidget(self.preview_widget)

        # Informações do tema
        self.theme_info = QLabel()
        self.theme_info.setWordWrap(True)
        self.theme_info.setStyleSheet(
            "padding: 10px; border: 1px solid #ccc;")
        right_panel.addWidget(self.theme_info)

        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

        # Botões
        button_layout = QHBoxLayout()

        self.apply_btn = QPushButton("Aplicar Tema")
        self.apply_btn.clicked.connect(self.apply_theme)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)

        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Seleciona tema atual
        for i in range(self.theme_list.count()):
            if self.theme_list.item(
                    i).text() == self.current_theme:
                self.theme_list.setCurrentRow(
                    i)
                break

    def on_theme_selected(self, current, previous):
        """Quando um tema é selecionado na lista"""
        if current:
            theme_name = current.text()
            theme = self.theme_manager.get_theme(
                theme_name)
            self.apply_btn.setEnabled(
                theme_name != self.current_theme)
            self.update_preview(theme)
            self.update_theme_info(theme)

    def update_preview(self, theme):
        """Atualiza a pré-visualização com o tema selecionado"""
        colors = theme["colors"]

        # Aplica cores ao widget de pré-visualização
        style = f"""
                                                                                QPlainTextEdit {{
                                                                                                background-color: {colors['background']};
                                                                                                color: {
        colors['foreground']};
                                                                                                border: 1px solid #555;
                                                                                                font-family: 'Consolas', monospace;
                                                                                                font-size: 11px;
                                                                                }}
                                                                """
        self.preview_editor.setStyleSheet(style)

        # Aqui você aplicaria o syntax highlighting também
        # (simplificado para este exemplo)

    def update_theme_info(self, theme):
        """Atualiza informações do tema"""
        colors = theme["colors"]
        info_text = f"""
                                                                <h3>{theme['name']}</h3>
                                                                <p><b>Tipo:</b> {theme['type'].title()}</p>
                                                                <p><b>Cores principais:</b></p>
                                                                <table>
                                                                <tr><td>Fundo:</td><td style='background-color:{colors['background']}; color:{colors['foreground']};'>{colors['background']}</td></tr>
                                                                <tr><td>Texto:</td><td style='background-color:{colors['foreground']}; color:{colors['background']};'>{colors['foreground']}</td></tr>
                                                                <tr><td>Seleção:</td><td style='background-color:{colors['selection']}; color:{colors['foreground']};'>{colors['selection']}</td></tr>
                                                                </table>
                                                                """
        self.theme_info.setText(info_text)

    def apply_theme(self):
        """Aplica o tema selecionado"""
        current_item = self.theme_list.currentItem()
        if current_item:
            theme_name = current_item.text()
            self.theme_manager.current_theme = theme_name

            # Aplica o tema ao IDE pai
            if hasattr(self.parent(),
                       'apply_theme'):
                self.parent().apply_theme(theme_name)

            self.apply_btn.setEnabled(False)
            QMessageBox.information(
                self, "Tema Aplicado", f"Tema '{theme_name}' aplicado com sucesso!")


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
            self.definitions.add(
                f"{self.current_class}.{node.name}()")
        else:
            self.definitions.add(f"{node.name}()")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if self.current_class:
            self.definitions.add(
                f"{self.current_class}.{node.name}()")
        else:
            self.definitions.add(f"{node.name}()")
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.definitions.add(
                    target.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            self.definitions.add(module_name)
            self.imported_modules.add(module_name)
            self.import_statements.append(
                alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.definitions.add(node.module)
            self.imported_modules.add(node.module)
            self.import_statements.append(
                f"from {node.module} import ...")
        for alias in node.names:
            self.definitions.add(alias.name)
        self.generic_visit(node)
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
                module_name = alias.name.split('.')[
                    0]
                self.definitions.add(
                    module_name)
            self.generic_visit(node)
        except:
            pass

    def visit_ImportFrom(self, node):
        try:
            if node.module:
                self.definitions.add(
                    node.module)
            for alias in node.names:
                self.definitions.add(
                    alias.name)
            self.generic_visit(node)
        except:
            pass


class ClassRelationVisitor(ast.NodeVisitor):
    """Visitor para detectar relações entre classes e métodos"""

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
                self.methods[self.current_class] = set(
                )
            self.methods[self.current_class].add(
                node.name)
        self.generic_visit(node)


# ===== GERENCIADOR DE SINTAXE =====

class LanguageSyntaxManager:
    """Gerenciador de sintaxe para múltiplas linguagens"""

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

    def get_suggestions(
            self,
            language: str,
            context: str = "") -> List[str]:
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
            method_chains = syntax.get(
                'method_chains', {})
            common_modules = syntax.get(
                'common_modules', {})

            # Verifica se é um método chain
            # conhecido
            for base, methods in method_chains.items():
                if chain == base:
                    return [
                        f"{m}()" for m in methods]

            # Verifica se é um módulo conhecido
            for module, methods in common_modules.items():
                if chain == module:
                    return methods

        # Para JavaScript
        elif language == 'javascript':
            common_apis = syntax.get(
                'common_apis', {})
            for api, methods in common_apis.items():
                if chain == api:
                    return [
                        f"{m}()" for m in methods]

        return []


# Instância global
language_syntax_manager = LanguageSyntaxManager()


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

    def preload_all_project_modules(
            self, project_path: str, file_path: str = None):
        """PRELOAD AGRESSIVO: Carrega todos os módulos do projeto uma vez"""
        if self._preload_done or not project_path:
            return

        with self._cache_lock:
            self._preload_done = True
            print(
                "🔄 Preloading todos os módulos do projeto...")

            # Encontra todos os .py no projeto
            py_files = []
            for root, dirs, files in os.walk(
                    project_path):
                for file in files:
                    if file.endswith(
                            '.py') and not file.startswith('__'):
                        py_files.append(
                            os.path.join(root, file))

            # Carrega cada um
            for py_file in py_files:
                module_name = os.path.relpath(
                    py_file, project_path).replace(os.sep, '.').rstrip('.py')
                self.get_module_methods(
                    module_name, py_file, project_path)

            print("✅ Preload concluído!")

    def get_module_methods(
            self,
            module_name: str,
            file_path: str = None,
            project_path: str = None) -> Set[str]:
        """Obtém todos os métodos de um módulo com cache"""
        with self._cache_lock:
            cache_key = f"{module_name}:{file_path or ''}"

            # Verifica se precisa atualizar o cache
            current_time = time.time()
            last_scan = self._last_scan_time.get(
                cache_key, 0)

            if current_time - last_scan > self._scan_interval:
                self._update_module_cache(
                    module_name, file_path, project_path)
                self._last_scan_time[cache_key] = current_time

            methods = self._module_cache.get(
                cache_key, set())
            return {
                m if m.endswith('()') else f"{m}()" for m in methods}

    def _update_module_cache(
            self,
            module_name: str,
            file_path: str = None,
            project_path: str = None):
        """Atualiza o cache para um módulo específico"""
        cache_key = f"{module_name}:{file_path or ''}"
        methods = set()

        try:
            # Tenta carregar como módulo Python
            # padrão
            if module_name in sys.builtin_module_names:
                methods.update(
                    self._get_builtin_module_methods(module_name))

            # Tenta importar o módulo
            try:
                spec = importlib.util.find_spec(
                    module_name)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(
                        spec)
                    spec.loader.exec_module(
                        module)
                    methods.update(
                        self._get_module_attributes(module))
            except:
                pass

            # Procura módulos locais no projeto
            if project_path:
                local_methods = self._scan_local_module(
                    module_name, project_path, file_path)
                methods.update(
                    local_methods)

        except Exception as e:
            print(
                f"Erro ao atualizar cache para {module_name}: {e}")

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
                if not attr_name.startswith(
                        '_'):
                    attr = getattr(
                        module, attr_name)
                    if callable(
                            attr):
                        attrs.add(
                            f"{attr_name}()")
                    else:
                        attrs.add(
                            attr_name)
        except:
            pass
        return attrs

    def _scan_local_module(
            self,
            module_name: str,
            project_path: str,
            current_file: str = None) -> Set[str]:
        #        """Escaneia módulos locais no projeto"""
        methods = set()
        try:
            # Possíveis locais do módulo
            possible_paths = [
                os.path.join(
                    project_path, f"{module_name}.py"),
                os.path.join(
                    project_path, module_name, "__init__.py"),
            ]

            for module_path in possible_paths:
                if os.path.exists(
                        module_path):
                    module_methods = self._parse_python_file_robust(
                        module_path)
                    methods.update(
                        module_methods)
                    break

        except Exception as e:
            print(
                f"Erro ao escanear módulo local {module_name}: {e}")

        return methods

    def _parse_python_file_robust(self, file_path: str) -> Set[str]:
        #        """Analisa um arquivo Python com AST robusta"""
        methods = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = None
            try:
                tree = ast.parse(
                    content, mode='exec', filename=file_path)
            except (IndentationError, SyntaxError):
                # Fallback regex para
                # arquivos com problemas
                # de sintaxe
                return self._parse_with_regex(
                    content)

            # Visita AST
            visitor = SafeDefinitionVisitor()
            visitor.visit(tree)
            methods.update(visitor.definitions)

        except Exception as e:
            print(
                f"Erro ao analisar arquivo {file_path}: {e}")

        return methods

    def _parse_with_regex(self, content: str) -> Set[str]:
        #    """Fallback regex para análise de código"""
        methods = set()
        # Funções
        functions = re.findall(
            r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update([f"{f}()" for f in functions])
        # Classes
        classes = re.findall(
            r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update(classes)
        return methods


# Instância global do gerenciador de cache
module_cache_manager = ModuleCacheManager()


# ===== WORKERS EM BACKGROUND =====
class LinterWorker(QThread):
    finished = QSignal(dict, list)  # errors, messages  # <- Mudança aqui: Signal -> QSignal

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

    # ===== SETUP DO AUTOCOMPLETE =====
    # Worker para autocomplete (inicia se Jedi disponível)

class AutoCompleteWorker(QThread):
    suggestion_ready = QSignal(str, list)  # Emite sugestões

    def __init__(self, ide):
        super().__init__()
        self.ide = ide
        self.running = True

    def run(self):
        while self.running:
            if hasattr(self.ide, 'current_editor') and self.ide.current_editor and JEDI_AVAILABLE:
                # Usa Jedi para sugestões
                try:
                    source = self.ide.current_editor.toPlainText()
                    script = jedi.Script(source)
                    completions = script.complete(len(source) - 1)  # Corrige posição
                    suggestions = [comp.name for comp in completions[:10]]  # Top 10
                    self.suggestion_ready.emit(getattr(self.ide, 'current_file', ''), suggestions)
                except Exception as e:
                    print(f"❌ Erro Jedi: {e}")
                    self.suggestion_ready.emit(getattr(self.ide, 'current_file', ''), [])
            else:
                # Fallback básico (palavras comuns Python)
                fallback = ['print', 'len', 'str', 'int', 'list', 'dict', 'os', 'sys']
                self.suggestion_ready.emit(getattr(self.ide, 'current_file', ''), fallback)
            self.msleep(500)  # Checa a cada 500ms

    def stop(self):
        self.running = False
        self.quit()
        self.wait(1000)


# Métodos da classe IDE para autocomplete
def setup_autocomplete(self):
    """Configura o sistema de autocomplete na IDE"""
    # Worker para autocomplete (inicia se Jedi disponível)
    self.auto_complete_worker = AutoCompleteWorker(self)
    self.auto_complete_worker.suggestion_ready.connect(self.show_completions)
    self.auto_complete_worker.start()

    # Shortcut para autocomplete (Ctrl+Space)
    self.autocomplete_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
    self.autocomplete_shortcut.activated.connect(self.trigger_autocomplete)

    # Lista para mostrar sugestões (dock simples à direita)
    self.completion_list = QListWidget()
    self.completion_list.setVisible(False)
    self.completion_list.itemDoubleClicked.connect(self.insert_completion)
    
    self.completion_dock = QDockWidget("Completions", self)
    self.completion_dock.setWidget(self.completion_list)
    self.addDockWidget(Qt.RightDockWidgetArea, self.completion_dock)
    
    # Variáveis para controle do autocomplete
    self.last_suggestions = []
    self.current_completions = []


def insert_completion(self, item):
    """Insere a sugestão selecionada no editor"""
    if hasattr(self, 'current_editor') and self.current_editor:
        completion_text = item.text()
        cursor = self.current_editor.textCursor()
        cursor.insertText(completion_text)
        self.completion_list.setVisible(False)


def show_completions(self, file_path, suggestions):
    """Mostra lista de sugestões"""
    if not suggestions or not hasattr(self, 'current_editor') or not self.current_editor:
        self.completion_list.setVisible(False)
        return
    
    # Filtra sugestões duplicadas
    unique_suggestions = []
    seen = set()
    for sug in suggestions:
        if sug not in seen:
            unique_suggestions.append(sug)
            seen.add(sug)
    
    self.last_suggestions = unique_suggestions[:10]  # Limita a 10 sugestões
    self.completion_list.clear()
    
    for sug in self.last_suggestions:
        self.completion_list.addItem(sug)
    
    # Posiciona o dock perto do cursor
    if self.completion_list.count() > 0:
        self.completion_list.setVisible(True)
        self.completion_dock.raise_()
        self.completion_list.setFocus()


def trigger_autocomplete(self):
    """Dispara autocomplete manual"""
    if hasattr(self, 'current_editor') and self.current_editor:
        # Força uma atualização imediata das sugestões
        self.auto_complete_worker.run()
        
        # Mostra as sugestões mais recentes
        if self.last_suggestions:
            self.completion_list.clear()
            for sug in self.last_suggestions:
                self.completion_list.addItem(sug)
            self.completion_list.setVisible(True)
            self.completion_dock.raise_()


def get_enhanced_suggestions(self):
    """Usa sistema híbrido Jedi + análise própria"""
    return self.completer.get_completions(
        self.text,
        self.cursor_position,
        self.file_path,
        self.project_path
    )


def get_fallback_suggestions(self):
    """Fallback caso o novo sistema falhe"""
    suggestions = set()

    # Sugestões básicas
    keywords = [
        "if", "else", "for", "while", "def", "class", "import"]
    suggestions.update(keywords)

    # Tenta análise simples com regex
    functions = re.findall(
        r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', self.text)
    suggestions.update([f"{f}()" for f in functions])

    return sorted(list(suggestions))[:15]


def analyze_context(self, text_before_cursor, current_line):
    """Analisa o contexto atual - NOVO MÉTODO"""
    context = {'type': 'general'}

    # Verifica se está em import
    if 'import' in current_line:
        if 'from' in current_line:
            # from module import ...
            parts = current_line.split('import')
            if len(parts) > 1:
                module_part = parts[0].replace('from', '').strip()
                context = {'type': 'from_import', 'module': module_part}
        else:
            # import module
            context = {'type': 'import'}

    # Verifica se está acessando atributo (obj.)
    elif current_line.strip().endswith('.'):
        parts = current_line.split('.')
        if len(parts) >= 2:
            # Última palavra antes do ponto
            obj_name = parts[-2].split()[-1]
            context = {'type': 'attribute', 'object': obj_name}

    # Verifica se está em chamada de função
    elif '(' in current_line and not current_line.strip().endswith('('):
        context = {'type': 'function_call'}

    return context


def get_import_suggestions(self):
    """Sugestões para imports - APRIMORADO"""
    common_modules = [
        'os', 'sys', 'json', 're', 'datetime', 'math', 'random',
        'subprocess', 'shutil', 'glob', 'ast', 'inspect', 'importlib',
        'platform', 'time', 'pathlib', 'collections', 'itertools', 'functools',
        'typing', 'logging', 'unittest', 'pytest', 'numpy', 'pandas',
        'matplotlib', 'seaborn', 'tkinter', 'PySide6', 'threading', 'multiprocessing'
    ]
    return common_modules


def get_from_import_suggestions(self, module_name):
    """Sugestões para from module import - APRIMORADO COM HARDCODED"""
    suggestions = set()

    # HARDCODED para stdlib comuns (funciona sem import falhar)
    hardcoded_stdlib = {
        'tkinter': ['Tk', 'Button', 'Label', 'Entry', 'Canvas', 'Frame', 'filedialog', 'messagebox', 'simpledialog',
                    'colorchooser', 'commondialog', 'Toplevel', 'Menu', 'Checkbutton', 'Radiobutton', 'Scale',
                    'Scrollbar', 'Listbox', 'Text', 'Spinbox'],
        'threading': ['Thread', 'Lock', 'RLock', 'Condition', 'Semaphore', 'BoundedSemaphore', 'Event', 'Timer',
                      'Barrier', 'BrokenBarrierError', 'current_thread', 'main_thread', 'active_count', 'enumerate',
                      'settrace', 'setprofile'],
        'subprocess': ['Popen', 'PIPE', 'STDOUT', 'call', 'check_call', 'check_output', 'run', 'CalledProcessError',
                       'TimeoutExpired', 'CompletedProcess', 'DEVNULL'],
        'os': ['path', 'environ', 'getcwd', 'listdir', 'mkdir', 'remove', 'rename', 'system', 'walk', 'chdir',
               'getenv', 'makedirs', 'rmdir', 'scandir'],
        'sys': ['argv', 'path', 'exit', 'version', 'platform', 'modules', 'executable', 'stdin', 'stdout', 'stderr',
                'gettrace', 'settrace'],
        'json': ['loads', 'dumps', 'load', 'dump', 'JSONEncoder', 'JSONDecoder', 'JSONDecodeError'],
        're': ['search', 'match', 'findall', 'sub', 'compile', 'escape', 'IGNORECASE', 'MULTILINE', 'DOTALL'],
        'datetime': ['datetime', 'date', 'time', 'timedelta', 'now', 'today', 'strftime', 'strptime', 'tzinfo',
                     'timezone'],
        'math': ['sqrt', 'sin', 'cos', 'tan', 'pi', 'e', 'log', 'exp', 'ceil', 'floor', 'fabs', 'gcd'],
        'random': ['random', 'randint', 'choice', 'shuffle', 'uniform', 'seed', 'randrange', 'sample', 'choices'],
    }

    if module_name in hardcoded_stdlib:
        suggestions.update(hardcoded_stdlib[module_name])
        # Debug no console
        print(f"DEBUG: Sugestões hardcoded para '{module_name}': {list(suggestions)[:5]}...")
        return sorted(list(suggestions))

    try:
        # Tenta importar o módulo para obter seus atributos
        if module_name in sys.builtin_module_names:
            # Módulos built-in
            builtin_contents = {
                'os': ['path', 'environ', 'getcwd', 'listdir', 'mkdir', 'remove'],
                'sys': ['argv', 'path', 'exit', 'version', 'platform'],
                'json': ['loads', 'dumps', 'load', 'dump'],
                're': ['search', 'match', 'findall', 'sub', 'compile', 'IGNORECASE'],
                'datetime': ['datetime', 'date', 'time', 'timedelta', 'now', 'today']
            }
            if module_name in builtin_contents:
                suggestions.update(builtin_contents[module_name])
        else:
            # Tenta importar o módulo
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    suggestions.add(attr_name)
            # Debug
            print(f"DEBUG: Import de '{module_name}' OK, {len(suggestions)} sugestões.")
    except ImportError as e:
        # Debug
        print(f"DEBUG: Erro ao importar '{module_name}': {e} (usando hardcoded se disponível).")

    return sorted(list(suggestions))


def get_attribute_suggestions(self, obj_name):
    """Sugestões para atributos de objeto - APRIMORADO"""
    suggestions = set()

    # Métodos comuns baseados no tipo de objeto
    common_methods = {
        'str': ['upper', 'lower', 'strip', 'split', 'join', 'replace', 'find',
                'startswith', 'endswith', 'format', 'isalpha', 'isdigit'],
        'list': ['append', 'remove', 'pop', 'sort', 'reverse', 'index', 'count',
                 'extend', 'insert', 'clear', 'copy'],
        'dict': ['get', 'keys', 'values', 'items', 'update', 'pop', 'clear',
                 'copy', 'setdefault'],
        'set': ['add', 'remove', 'discard', 'union', 'intersection', 'difference'],
        # pandas
        'df': ['head', 'tail', 'describe', 'info', 'columns', 'shape', 'loc', 'iloc'],
    }

    # Verifica se é um objeto conhecido
    for obj_type, methods in common_methods.items():
        if obj_type in obj_name.lower():
            suggestions.update([f"{m}()" for m in methods])
            break

    # Se não encontrou, adiciona métodos genéricos
    if not suggestions:
        generic_methods = ['__str__', '__repr__', '__len__', '__getitem__',
                           '__setitem__', '__iter__', '__next__']
        suggestions.update([f"{m}()" for m in generic_methods])

    return suggestions


def get_function_suggestions(self):
    """Sugestões para chamadas de função - NOVO"""
    suggestions = set()

    # Adiciona funções built-in
    builtins = [
        'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
        'range', 'input', 'open', 'type', 'sum', 'min', 'max', 'abs', 'round',
        'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter', 'any', 'all',
        'isinstance', 'issubclass', 'hasattr', 'getattr', 'setattr'
    ]
    suggestions.update([f"{b}()" for b in builtins])

    return suggestions


def get_general_suggestions(self):
    """Sugestões gerais - COMPLETAMENTE REFEITO"""
    suggestions = set()

    # 1. Palavras-chave Python
    keywords = {
        "if", "else", "elif", "for", "while", "break", "continue", "pass", "return",
        "try", "except", "finally", "raise", "def", "class", "lambda", "global",
        "nonlocal", "import", "from", "as", "and", "or", "not", "in", "is",
        "True", "False", "None", "with", "yield", "assert", "del", "async", "await"
    }
    suggestions.update(keywords)

    # 2. Funções built-in
    builtins = [
        "print", "len", "str", "int", "float", "list", "dict", "set", "tuple",
        "range", "input", "open", "type", "sum", "min", "max", "abs", "round",
        "sorted", "reversed", "enumerate", "zip", "map", "filter", "any", "all",
        "bool", "chr", "ord", "dir", "help", "id", "isinstance", "issubclass",
        "getattr", "setattr", "hasattr", "vars", "locals", "globals", "exec", "eval"
    ]
    suggestions.update([f"{b}()" for b in builtins])

    # 3. Definições locais do arquivo atual
    local_defs = self.extract_local_definitions()
    suggestions.update(local_defs)

    # 4. Módulos importados
    imported_modules = self.extract_imported_modules()
    suggestions.update(imported_modules)

    return suggestions


def extract_local_definitions(self):
    """Extrai definições locais do código atual - APRIMORADO"""
    definitions = set()

    try:
        # Usa regex para encontrar definições rapidamente
        code = self.text

        # Funções
        func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        functions = re.findall(func_pattern, code)
        definitions.update([f"{f}()" for f in functions])

        # Classes
        class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        classes = re.findall(class_pattern, code)
        definitions.update(classes)

        # Variáveis (apenas as mais significativas)
        var_pattern = r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=\s]'
        var_matches = re.findall(var_pattern, code, re.MULTILINE)
        for _, var in var_matches:
            if len(var) > 2 and not var.startswith('_'):  # Filtra variáveis muito curtas e privadas
                definitions.add(var)

    except Exception as e:
        print(f"Erro ao extrair definições locais: {e}")

    return definitions


def extract_imported_modules(self):
    """Extrai módulos importados - APRIMORADO"""
    modules = set()

    try:
        code = self.text

        # Import simples: import module
        simple_imports = re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        modules.update(simple_imports)

        # Import from: from module import ...
        from_imports = re.findall(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', code)
        modules.update(from_imports)

        # Import com alias: import module as alias
        alias_imports = re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+as', code)
        modules.update(alias_imports)

    except Exception as e:
        print(f"Erro ao extrair módulos importados: {e}")

    return modules


def closeEvent(self, event):
    """Garante que o worker seja parado ao fechar a IDE"""
    if hasattr(self, 'auto_complete_worker'):
        self.auto_complete_worker.stop()
    super().closeEvent(event)

class DebugWorker(QThread):
    """Worker para execução de debug em thread separada"""
    output_received = QSignal(str)  # Mudança: Signal -> QSignal (importado como QSignal)
    finished = QSignal(int)  # return code

    def __init__(self, python_exec, file_path, project_path):
        super().__init__()
        self.python_exec = python_exec
        self.file_path = file_path
        self.project_path = project_path
        self.process = None
        self._is_running = True

    def stop(self):
        """Para a execução do debug"""
        self._is_running = False
        if self.process:
            self.process.terminate()
        self.terminate()

    def run(self):
        """Executa o debug em thread separada"""
        try:
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(
                self.handle_stdout)
            self.process.readyReadStandardError.connect(
                self.handle_stderr)
            self.process.finished.connect(
                self.on_finished)

            # Comando para debug interativo
            cmd = [
                self.python_exec, "-m", "pdb", self.file_path]

            self.process.start(cmd[0], cmd[1:])
            self.process.setWorkingDirectory(
                self.project_path or os.path.dirname(self.file_path))

            # Aguarda o processo terminar
            if self.process.waitForStarted():
                while self._is_running and self.process.state() == QProcess.Running:
                    self.msleep(
                        100)

        except Exception as e:
            self.output_received.emit(
                f"❌ Erro no debug: {str(e)}")

    def handle_stdout(self):
        """Processa saída padrão"""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        if data:
            self.output_received.emit(data)

    def handle_stderr(self):
        """Processa erro padrão"""
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        if data:
            self.output_received.emit(data)

    def on_finished(self, exit_code, exit_status):
        """Processa término do processo"""
        self.finished.emit(exit_code)

    def send_command(self, command):
        """Envia comando para o processo de debug"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.write(
                f"{command}\n".encode())

# ===== COMPONENTES DE INTERFACE =====

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(70)

    def update_line_numbers(self):
        self.update()

    def update_line_numbers_area(self, rect, dy):
        if dy:
            self.scroll(0, dy)
        else:
            self.update(
                0, rect.y(), self.width(), rect.height())
        if rect.contains(self.editor.viewport().rect()):
            self.update_line_numbers()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(20, 30, 48))
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.editor.blockBoundingGeometry(block).translated(
                self.editor.contentOffset()).top())
        bottom = top + \
                 int(self.editor.blockBoundingRect(block).height())
        font = self.editor.font()
        font.setPointSize(10)
        painter.setFont(font)
        font_metrics = self.editor.fontMetrics()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(
                    block_number + 1)
                painter.setPen(
                    QColor(150, 150, 150))
                painter.drawText(
                    0, top, 50, font_metrics.height(), Qt.AlignRight, number)

                # Draw vertical
                # separator
                painter.setPen(
                    QColor(100, 100, 100))
                painter.drawLine(
                    55, top, 55, bottom)

                # Draw red line for
                # errors
                data = block.userData()
                if isinstance(data, ErrorData) and any(
                        error['type'] == 'error' for error in data.errors):
                    painter.setPen(
                        QColor(255, 0, 0))
                    painter.drawLine(
                        60, top, 60, bottom)

            block = block.next()
            top = bottom
            bottom = top + \
                     int(self.editor.blockBoundingRect(
                         block).height())
            block_number += 1


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

    # ... restante do código permanece igual

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


class AutoCompleteWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setMaximumHeight(150)
        self.setMaximumWidth(400)
        self.current_editor = None

        # Estilo melhorado
        self.setStyleSheet("""
                                                                                QListWidget {
                                                                                                background-color: #2d2d30;
                                                                                                color: #d4d4d4;
                                                                                                border: 1px solid #3e3e42;
                                                                                                border-radius: 4px;
                                                                                                font-family: 'Consolas', monospace;
                                                                                                font-size: 11px;
                                                                                }
                                                                                QListWidget::item {
                                                                                                padding: 4px 8px;
                                                                                                border-bottom: 1px solid #3e3e42;
                                                                                }
                                                                                QListWidget::item:selected {
                                                                                                background-color: #569cd6;
                                                                                                color: white;
                                                                                }
                                                                                QListWidget::item:hover {
                                                                                                background-color: #3e3e42;
                                                                                }
                                                                """)

    def show_suggestions(self, editor, suggestions):
        self.current_editor = editor
        self.clear()

        if not suggestions:
            self.hide()
            return

        # Limita a 10 sugestões
        for suggestion in suggestions[:10]:
            self.addItem(suggestion)

        # Posiciona o widget corretamente
        cursor_rect = editor.cursorRect()
        pos = editor.mapToGlobal(cursor_rect.bottomLeft())

        # Ajusta para não sair da tela
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        if pos.y() + self.height() > screen_geometry.bottom():
            pos = editor.mapToGlobal(
                cursor_rect.topLeft())
            pos.setY(pos.y() - self.height())

        if pos.x() + self.width() > screen_geometry.right():
            pos.setX(
                screen_geometry.right() - self.width())

        self.move(pos)
        self.show()
        self.setCurrentRow(0)

    def keyPressEvent(self, event):
        if self.current_editor and self.isVisible():
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
                self.insert_current_completion()
                event.accept()
                return
            elif event.key() == Qt.Key_Escape:
                self.hide()
                event.accept()
                return

        super().keyPressEvent(event)

    def insert_current_completion(self):
        """Insere a sugestão atual no editor - CORRIGIDO"""
        if not self.current_editor or self.currentRow() < 0:
            return

        current_item = self.currentItem()
        if current_item:
            completion = current_item.text()

            cursor = self.current_editor.textCursor()

            # Encontra a palavra atual para
            # substituir
            cursor.select(
                QTextCursor.WordUnderCursor)
            current_word = cursor.selectedText()

            # Se estiver no meio de uma palavra,
            # move para o fim
            if not current_word:
                cursor.movePosition(
                    QTextCursor.StartOfWord)
                cursor.movePosition(
                    QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
                current_word = cursor.selectedText()

            # Remove seleção e insere o completion
            cursor.setPosition(
                cursor.selectionEnd())
            cursor.insertText(completion)

            self.hide()


class CodeEditor(QPlainTextEdit):
    def __init__(
            self,
            text,
            cursor_position,
            file_path,
            project_path,
            parent=None):
        super().__init__(parent)
        self.setPlainText(text)
        cursor = self.textCursor()
        cursor.setPosition(min(cursor_position, len(text)))
        self.setTextCursor(cursor)

        self.file_path = file_path
        self.project_path = project_path

        # Configurar tab
        self.configure_tab_stop()

        # Controle de estado do worker - CORRIGIDO
        self.auto_complete_worker = None
        self.is_worker_running = False

        # INICIALIZAÇÃO CORRIGIDA do autocomplete
        self.auto_complete_widget = AutoCompleteWidget(self)
        self.auto_complete_timer = QTimer(self)
        self.auto_complete_timer.setSingleShot(True)
        self.auto_complete_timer.timeout.connect(
            self.trigger_auto_complete)

        # REMOVER ESTA LINHA PROBLEMÁTICA:
        # s elf._cursor_info_timer = QTimer(self)

        # Adicionar timer correto:
        self._cursor_info_timer = QTimer(self)  # ✅ Nome correto
        self._cursor_info_timer.setSingleShot(True)
        self._cursor_info_timer.timeout.connect(
            self._update_cursor_info_debounced)

    def configure_tab_stop(self):
        """Configura o tamanho do tab baseado no tipo de arquivo"""
        font = QFont("Monospace", 12)
        self.setFont(font)
        font_metrics = self.fontMetrics()

        if self.file_path and self.file_path.endswith('.py'):
            tab_width = font_metrics.horizontalAdvance(
                ' ') * 4
        else:
            tab_width = font_metrics.horizontalAdvance(
                ' ') * 2

        self.setTabStopDistance(tab_width)

    def keyPressEvent(self, event: QKeyEvent):
        try:
            # Atalhos para forçar autocomplete
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space:
                self.force_auto_complete()
                event.accept()
                return

            # Fecha o autocomplete se Escape for
            # pressionado
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
                            self.auto_complete_widget.insert_completion(
                                current_item.text())
                        event.accept()
                        return
                    elif event.key() == Qt.Key_Up:
                        current_row = self.auto_complete_widget.currentRow()
                        self.auto_complete_widget.setCurrentRow(
                            max(0, current_row - 1))
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
            print(
                f"Erro crítico no keyPressEvent: {e}")
            super().keyPressEvent(event)

    def force_auto_complete(self):
        #  """Força autocomplete imediatamente"""
        if self.auto_complete_worker and self.auto_complete_worker.isRunning():
            self.auto_complete_worker.stop()
            self.auto_complete_worker.wait(10)

        self.trigger_auto_complete()

    def trigger_auto_complete(self):
        """Dispara autocomplete de forma segura - CORRIGIDO"""
        # Não dispara se estiver em string ou comentário
        if self.is_inside_string() or self.is_inside_comment():
            return

        # Para worker anterior se estiver rodando
        if self.auto_complete_worker and self.auto_complete_worker.isRunning():
            self.auto_complete_worker.stop()
            self.auto_complete_worker.wait(100)

        self.is_worker_running = True

        try:
            # Worker com tratamento de erro
            self.auto_complete_worker = AutoCompleteWorker(
                self.toPlainText(),
                self.textCursor().position(),
                self.file_path,
                self.project_path
            )
            self.auto_complete_worker.finished.connect(
                self.on_auto_complete_finished)
            self.auto_complete_worker.start()
        except Exception as e:
            print(f"Erro ao iniciar worker: {e}")
            self.is_worker_running = False

    def on_auto_complete_finished(self, suggestions):
        #  """Callback quando worker termina - CORRIGIDO"""
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
                indent_level = len(
                    line) - len(line.lstrip(' \t'))
                fixed_line = ' ' * \
                             (indent_level * 4) + \
                             line.lstrip(' \t')
                fixed_lines.append(
                    fixed_line)
            fixed_text = '\n'.join(fixed_lines)
            self.setPlainText(fixed_text)
            print(
                "Indentação corrigida automaticamente!")
        except Exception as e:
            print(
                f"Falha na correção de indent: {e}")

    def is_inside_string(self):
        """Verifica se está dentro de string de forma mais precisa"""
        cursor = self.textCursor()
        position = cursor.position()
        text = self.toPlainText()[:position]

        # Conta aspas não escapadas
        single_quotes = 0
        double_quotes = 0
        triple_single = 0
        triple_double = 0

        i = 0
        while i < len(text):
            if text[i] == "'":
                # Verifica se é triple
                # quote
                if i + \
                        2 < len(text) and text[i:i + 3] == "'''":
                    triple_single += 1
                    i += 2
                else:
                    single_quotes += 1
            elif text[i] == '"':
                # Verifica se é triple
                # quote
                if i + \
                        2 < len(text) and text[i:i + 3] == '"""':
                    triple_double += 1
                    i += 2
                else:
                    double_quotes += 1
            # Ignora próximo caractere (escape)
            elif text[i] == '\\':
                i += 1
            i += 1

        # Se está dentro de triple quotes
        if triple_single % 2 == 1 or triple_double % 2 == 1:
            return True

        # Se está dentro de quotes simples
        if single_quotes % 2 == 1:
            return True

        # Se está dentro de quotes duplas
        if double_quotes % 2 == 1:
            return True

        return False

    def is_inside_comment(self):
        """Verifica se está dentro de comentário - CORRIGIDO"""
        cursor = self.textCursor()
        position = cursor.position()
        text_before = self.toPlainText()[:position]

        # Divide em linhas e verifica a linha atual
        lines = text_before.split('\n')
        if not lines:
            return False

        current_line = lines[-1]

        # Remove strings para evitar falsos positivos
        line_without_strings = self.remove_strings_from_line(
            current_line)

        return '#' in line_without_strings

    def show_auto_complete(self, suggestions):
        """Mostra sugestões - CORRIGIDO"""
        if suggestions and self.hasFocus():
            self.auto_complete_widget.show_suggestions(
                self, suggestions)
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

    def on_text_changed(self):
        """Responde a mudanças de texto - CORRIGIDO"""
        try:
            cursor = self.textCursor()
            current_line = cursor.block().text()

            # Verifica contexto atual
            current_char = self.get_current_char()

            # Dispara autocomplete em situações
            # específicas
            trigger_chars = ['.', ' ', '(', '=']

            if (current_char in trigger_chars or
                    len(current_line.strip()) == 0 or
                    current_line.endswith((' ', 'def ', 'class ', 'import ', 'from '))):

                if not self.is_inside_comment() and not self.is_inside_string():
                    self.auto_complete_timer.start(
                        300)  # Reduzido para 300ms
        except Exception as e:
            print(f"Erro em on_text_changed: {e}")

    def get_current_char(self):
        """Obtém o caractere na posição atual do cursor"""
        cursor = self.textCursor()
        if cursor.position() > 0:
            cursor.movePosition(
                QTextCursor.Left, QTextCursor.KeepAnchor)
            return cursor.selectedText()
        return ""

    def on_cursor_changed(self):
        """Atualiza informações do cursor"""
        self.update_cursor_info()

    def on_cursor_position_changed(self):
        """Debounce para mudanças de cursor"""
        self.cursor_timer.start(100)  # 100ms debounce

    def on_cursor_changed_timeout(self):
        """Callback debounced para mudanças de cursor"""
        self.update_cursor_info()

    def remove_strings_from_line(self, line):
        """Remove trechos entre aspas para análise de comentários"""
        # Simples remoção de strings entre aspas simples e
        # duplas
        in_single_quote = False
        in_double_quote = False
        result = []
        i = 0

        while i < len(line):
            if line[i] == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif line[i] == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif not in_single_quote and not in_double_quote:
                result.append(line[i])
            i += 1

        return ''.join(result)

    def update_cursor_info(self):
        """Atualiza informações do cursor na statusbar com verificações de segurança"""
        try:
            # Verifica se há um editor ativo
            editor = self.get_current_editor()
            if not editor:
                return

            # Verifica se os componentes da UI
            # existem
            if not hasattr(
                    self, 'cursor_info_label') or not self.cursor_info_label:
                return

            # Obtém posição do cursor
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1

            # Atualiza o label
            self.cursor_info_label.setText(
                f"Linha: {line}, Coluna: {column}")

        except Exception as e:
            print(
                f"Erro em update_cursor_info: {e}")
            # Não propaga a exceção para não quebrar
            # a aplicação

    def _update_cursor_info_debounced(self):
        """Versão debounced do update_cursor_info"""
        self.update_cursor_info()

    def on_cursor_position_changed(self):
        """Debounce para mudanças de cursor"""
        self._cursor_info_timer.start(100)


class JediCompleter:
    """Usa Jedi para autocomplete profissional"""

    def __init__(self):
        self.script = None

    def get_completions(self, code, cursor_position, file_path=""):
        if not JEDI_AVAILABLE:
            return []

        try:
            self.script = jedi.Script(
                code=code,
                path=file_path,
                project=jedi.Project(path=os.path.dirname(
                    file_path) if file_path else ".")
            )

            completions = self.script.complete(
                line=cursor_position[0], column=cursor_position[1])

            suggestions = []
            for completion in completions:
                name = completion.name
                if completion.type == 'function':
                    name += '()'
                suggestions.append(name)

            # Limita a 20 sugestões
            return suggestions[:20]

        except Exception as e:
            print(f"Erro no Jedi: {e}")
            return []


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

        # Passar todos os parâmetros obrigatórios
        self.editor = CodeEditor(
            text=initial_text,
            cursor_position=0,
            file_path=file_path,
            project_path=self.get_project_path()
        )

        # Garantir que o tab seja 4 espaços
        font = QFont("Monospace", 12)
        self.editor.setFont(font)
        font_metrics = self.editor.fontMetrics()
        tab_width = font_metrics.horizontalAdvance(' ') * 4
        self.editor.setTabStopDistance(tab_width)

        # Use o MultiLanguageHighlighter
        self.highlighter = MultiLanguageHighlighter(
            self.editor.document())
        if file_path:
            self.highlighter.set_language(file_path)

        self.editor.setWordWrapMode(QTextOption.NoWrap)

        # Linting
        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.timeout.connect(self.start_linting)
        self.is_linting = False
        self.pending_lint = False

        self.linter_worker = None
        self.last_lint_content = initial_text

        # Connect signals
        self.editor.textChanged.connect(self.schedule_linting)
        self.editor.cursorPositionChanged.connect(
            self.update_line_numbers)
        self.editor.verticalScrollBar().valueChanged.connect(self.update_line_numbers)

        # Line number area
        self.line_number_area = LineNumberArea(self.editor)
        layout.addWidget(self.editor)
        self.setLayout(layout)

        self.update_line_numbers()

        # Set viewport margins to shift text to the right
        self.editor.setViewportMargins(
            self.line_number_area.width() + 10, 0, 0, 0)

    def get_project_path(self):
        """Obtém o caminho do projeto do IDE pai"""
        ide = self.get_ide()
        return ide.project_path if ide else ""

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.line_number_area.setGeometry(
            0, 0, self.line_number_area.width(), self.height())

    def update_line_numbers(self):
        self.line_number_area.update_line_numbers()

    def schedule_linting(self):
        """Schedule linting com debounce melhorado"""
        current_content = self.editor.toPlainText()

        if (current_content != self.last_lint_content and
                self.file_path and
                self.file_path.endswith('.py')):

            if self.is_linting:
                self.pending_lint = True
            else:
                self.lint_timer.start(
                    2000)

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
        self.linter_worker.finished.connect(
            self.on_linting_finished)
        self.linter_worker.start()

    def on_linting_finished(self, errors, lint_messages):
        """Finaliza linting e verifica se precisa relintar"""
        self.is_linting = False

        if self.pending_lint:
            self.pending_lint = False
            self.schedule_linting()

        # Apply errors to document
        doc = self.editor.document()
        block_count = doc.blockCount()

        # Clear previous errors from all blocks
        for i in range(block_count):
            block = doc.findBlockByLineNumber(i)
            if block.isValid():
                block.setUserData(
                    ErrorData([]))

        # Apply new errors
        for line_num, line_errors in errors.items():
            if line_num < block_count:
                block = doc.findBlockByLineNumber(
                    line_num)
                if block.isValid():
                    data = ErrorData(
                        line_errors)
                    block.setUserData(
                        data)

        # Update problems list
        ide = self.get_ide()
        if ide and ide.problems_list:
            ide.problems_list.clear()
            for msg in lint_messages:
                item = QListWidgetItem(
                    msg)

                # Extract line number
                # safely
                line_num = '0'
                if 'Line' in msg and ':' in msg:
                    try:
                        line_part = msg.split('Line')[1].split(':')[
                            0].strip()
                        line_num = line_part
                    except:
                        pass

                data = {
                    'file': self.file_path,
                    'line': line_num,
                    'type': 'error' if 'error' in msg.lower() else 'warning'
                }
                item.setData(
                    Qt.UserRole, data)
                ide.problems_list.addItem(
                    item)

        # Also update lint_text for additional info
        if ide and ide.lint_text:
            if lint_messages:
                ide.lint_text.setPlainText(
                    '\n'.join(lint_messages))
            else:
                ide.lint_text.setPlainText(
                    "No lint issues found.")

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
            painter.drawText(
                option.rect.x() + 5, option.rect.bottom() - 5, "●")


class FontSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Font")
        self.layout = QVBoxLayoutDialog(self)
        self.label = QLabel("Choose a font:")
        self.layout.addWidget(self.label)
        self.font_combo = QComboBox()
        self.available_fonts = QFontDatabase.families()
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
            # Exemplo simples: cria um ZIP ou use
            # subprocess para PyInstaller
            output_dir = os.path.join(
                self.project_path, "dist")
            os.makedirs(output_dir, exist_ok=True)

            # Comando exemplo com PyInstaller
            # (ajuste conforme necessário)
            pyinstaller_cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--distpath", output_dir,
                os.path.join(
                    self.project_path, self.main_file)
            ]
            result = subprocess.run(
                pyinstaller_cmd, cwd=self.project_path, capture_output=True, text=True)

            if result.returncode == 0:
                QMessageBox.information(
                    self, "Sucesso", f"Projeto empacotado em {output_dir}!")
            else:
                QMessageBox.warning(
                    self, "Erro", f"Falha no empacotamento:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao empacotar: {str(e)}")

        self.accept()


class ProgressDialog(QDialog):
    """Diálogo de progresso para mostrar o carregamento"""

    def __init__(
            self,
            parent=None,
            title="Carregando",
            message="Carregando módulos..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 150)
        self.setModal(True)
        self.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        layout = QVBoxLayout()

        # Ícone e título
        title_layout = QHBoxLayout()
        self.icon_label = QLabel("🔄")
        self.icon_label.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(self.icon_label)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #569cd6;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Mensagem
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet(
            "color: #cccccc; margin: 10px 0;")
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
        self.counter_label.setStyleSheet(
            "color: #9cdcfe; font-size: 12px;")
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
            self.counter_label.setText(
                f"{current}/{total} módulos carregados")

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
        title_label = QLabel(
            "Digite o nome e selecione a extensão:")
        title_label.setStyleSheet(
            "font-weight: bold; color: #569cd6; margin-bottom: 5px;")
        layout.addWidget(title_label)

        # Campo Nome
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nome:"))
        self.name_edit = QLineEdit("novo_arquivo")
        self.name_edit.setPlaceholderText("Ex: meu_script")
        self.name_edit.textChanged.connect(
            self.update_create_button)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Campo Extensão (ComboBox com índice/ícones visuais)
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("Extensão:"))
        self.ext_combo = QComboBox()
        extensions = [
            ("Python (.py)", ".py"),
            ("JavaScript (.js)", ".js"),
            ("HTML (.html)", ".html"),
            ("CSS (.css)", ".css"),
            ("JSON (.json)", ".json"),
            ("Texto (.txt)", ".txt"),
            ("Sem extensão", "")
        ]
        for display, ext in extensions:
            self.ext_combo.addItem(display, ext)
        self.ext_combo.setCurrentIndex(0)
        ext_layout.addWidget(self.ext_combo)
        layout.addLayout(ext_layout)

        # Botões
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("Criar")
        self.create_btn.clicked.connect(self.accept)
        self.create_btn.setStyleSheet(
            "background-color: #569cd6; color: white; padding: 8px;")
        self.create_btn.setEnabled(False)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            "background-color: #d84f4f; color: white; padding: 8px;")

        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_file_name(self):
        """Retorna nome completo (nome + extensão)"""
        try:
            name = self.name_edit.text().strip()
            if not name:
                return None

            import re
            name = re.sub(
                r'[<>:"/\\|?*]', '_', name)

            ext = self.ext_combo.currentData()

            if ext and isinstance(
                    ext, str) and ext.strip():
                if not ext.startswith(
                        '.'):
                    ext = '.' + ext
                return name + ext
            else:
                return name

        except Exception as e:
            print(
                f"Erro ao obter nome do arquivo: {e}")
            return None

    def update_create_button(self):
        """Habilita botão se nome não vazio"""
        try:
            text = self.name_edit.text().strip()
            is_valid = bool(
                text) and not text.isspace()
            self.create_btn.setEnabled(is_valid)
        except Exception as e:
            print(f"Erro ao atualizar botão: {e}")
            self.create_btn.setEnabled(False)


class LoadingWidget(QWidget):
    """Widget de carregamento para o autocomplete"""

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
        self.loading_label.setStyleSheet(
            "color: #9cdcfe; font-size: 10px;")
        self.loading_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.loading_label)
        self.setLayout(layout)
        self.hide()


class StatusBarProgress(QWidget):
    """Widget de progresso para a barra de status"""

    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.text_label.setStyleSheet(
            "color: #9cdcfe; font-size: 12px;")
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
        """Atualiza o progresso"""
        self.progress_bar.setValue(value)
        if message:
            self.text_label.setText(message)

    def show_loading(self, message="Carregando..."):
        """Mostra o widget de carregamento"""
        self.icon_label.setText("🔄")
        self.text_label.setText(message)
        self.progress_bar.setValue(0)
        self.show()

    def show_success(self, message="Concluído!"):
        """Mostra sucesso"""
        self.icon_label.setText("✅")
        self.text_label.setText(message)
        self.progress_bar.setValue(100)
        QTimer.singleShot(2000, self.hide)

    def show_error(self, message="Erro!"):
        """Mostra erro"""
        self.icon_label.setText("❌")
        self.text_label.setText(message)
        self.progress_bar.setValue(0)
        QTimer.singleShot(3000, self.hide)


class TerminalTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Monospace", 10))
        self.setStyleSheet(
            "background-color: #1e1e1e; color: #ffffff;")
        self._shell_process = None

    def set_shell_process(self, process):
        """Define o processo do shell"""
        self._shell_process = process

    def append_output(self, data):
        """Adiciona texto ao terminal"""
        try:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)

            # Preserva a posição do input
            current_text = self.toPlainText()
            if current_text.endswith(">>> "):
                # Remove o prompt
                # temporariamente
                self.setPlainText(
                    current_text[:-4] + data + "\n>>> ")
            else:
                cursor.insertText(
                    data + "\n>>> ")

            # Move cursor para após o prompt
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
        except Exception as e:
            print(f"Erro em append_output: {e}")

    def keyPressEvent(self, event):
        """Handle terminal input"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.execute_command()
        else:
            super().keyPressEvent(event)

    def execute_command(self):
        """Executa comando no shell"""
        if not self._shell_process:
            return

        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        command = cursor.selectedText().strip()

        if command and not command.endswith(">>>"):
            # Remove prompt se existir
            if command.startswith(">>> "):
                command = command[4:]

            if command:  # Só envia se não estiver vazio
                self._shell_process.write(
                    f"{command}\n".encode())

        # Adiciona novo prompt
        self.appendPlainText(">>> ")

    def restart_shell(self):
        """Reinicia o shell de forma segura"""
        try:
            ide = self.get_ide()
            if ide:
                # Para processo anterior
                # de forma segura
                if self._shell_process:
                    if self._shell_process.state() == QProcess.Running:
                        self._shell_process.terminate()
                        self._shell_process.waitForFinished(
                            1000)
                    self._shell_process = None

                # Cria novo processo
                ide.shell_process = QProcess(
                    ide)
                ide.shell_process.readyReadStandardOutput.connect(
                    ide.handle_terminal_output)
                ide.shell_process.readyReadStandardError.connect(
                    ide.handle_terminal_error)

                if os.name == 'nt':
                    ide.shell_process.start(
                        "cmd.exe")
                else:
                    ide.shell_process.start(
                        "/bin/bash", ["-i"])

                # Atualiza referência
                self._shell_process = ide.shell_process

                if ide.project_path:
                    ide.activate_project()

                self.append_output(
                    "\nShell reiniciado\n>>> ")

        except Exception as e:
            self.append_output(
                f"\nErro ao reiniciar shell: {str(e)}")


class DebugTerminal(TerminalTextEdit):
    """Terminal especializado para debug"""

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
        self.clear()
        self.append_output(
            f"🐛 Iniciando debug: {os.path.basename(file_path)}\n")
        self.append_output(
            "Comandos: n(next), s(step), c(continue), q(quit), l(list), p(print), b(break)\n")
        self.append_output("-" * 50 + "\n")

        self.debug_worker = DebugWorker(
            python_exec, file_path, project_path)
        self.debug_worker.output_received.connect(
            self.append_output)
        self.debug_worker.finished.connect(
            self.on_debug_finished)
        self.debug_worker.start()

        self.input_start = len(self.toPlainText())

    def on_debug_finished(self, exit_code):
        self.append_output(
            f"\n🔚 Sessão de debug finalizada (código: {exit_code})\n")
        self.debug_worker = None

    def execute_command(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        command_line = cursor.selectedText().strip()

        if command_line and self.debug_worker:
            clean_command = command_line.strip()
            if clean_command in self.debug_commands:
                full_command = self.debug_commands[clean_command]
                self.append_output(
                    f"Executando: {full_command}\n")
                self.debug_worker.send_command(
                    full_command)
            else:
                self.debug_worker.send_command(
                    clean_command)

            self.append_output("\n(Pdb) ")
        else:
            self.append_output("\n(Pdb) ")

    def keyPressEvent(self, event: QKeyEvent):
        if self.debug_worker and event.key(
        ) in [Qt.Key_Return, Qt.Key_Enter]:
            self.execute_command()
            event.accept()
            return

        if self.debug_worker and event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_N:
                self.debug_worker.send_command(
                    "next")
                self.append_output(
                    "\nnext\n")
                event.accept()
                return
            elif event.key() == Qt.Key_S:
                self.debug_worker.send_command(
                    "step")
                self.append_output(
                    "\nstep\n")
                event.accept()
                return
            elif event.key() == Qt.Key_C:
                self.debug_worker.send_command(
                    "continue")
                self.append_output(
                    "\ncontinue\n")
                event.accept()
                return
            elif event.key() == Qt.Key_Q:
                self.debug_worker.send_command(
                    "quit")
                self.append_output(
                    "\nquit\n")
                event.accept()
                return

        super().keyPressEvent(event)

    def stop_debug(self):
        if self.debug_worker:
            self.debug_worker.stop()
            self.debug_worker.wait(1000)
            self.append_output(
                "\n⏹️ Debug interrompido\n")


# gereciador de pacotes
# gereciador de pacotes
class PackageManagerThread(QThread):
    output_signal = QSignal(str)  # Mudança: Signal -> QSignal (importado como QSignal)
    finished_signal = QSignal(bool, str)
    progress_signal = QSignal(str)

    def __init__(self, command, package_name="", version=""):
        super().__init__()
        self.command = command
        self.package_name = package_name
        self.version = version

    def run(self):
        try:
            if self.command == "list":
                self.progress_signal.emit("Listando pacotes instalados...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "list", "--format=json"],
                    capture_output=True, text=True, encoding='utf-8', timeout=30
                )
                self.output_signal.emit(result.stdout)

            elif self.command == "search":
                self.progress_signal.emit(f"Buscando pacote: {self.package_name}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "search", self.package_name],
                    capture_output=True, text=True, encoding='utf-8', timeout=30
                )
                self.output_signal.emit(result.stdout)

            elif self.command == "install":
                package_spec = self.package_name
                if self.version:
                    package_spec = f"{self.package_name}=={self.version}"

                self.progress_signal.emit(f"Instalando {package_spec}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package_spec],
                    capture_output=True, text=True, encoding='utf-8', timeout=120
                )
                if result.returncode == 0:
                    self.finished_signal.emit(True, f"Pacote {package_spec} instalado com sucesso!")
                else:
                    self.finished_signal.emit(False, f"Erro ao instalar: {result.stderr}")

            elif self.command == "uninstall":
                self.progress_signal.emit(f"Desinstalando {self.package_name}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", self.package_name],
                    capture_output=True, text=True, encoding='utf-8', timeout=60
                )
                if result.returncode == 0:
                    self.finished_signal.emit(True, f"Pacote {self.package_name} desinstalado com sucesso!")
                else:
                    self.finished_signal.emit(False, f"Erro ao desinstalar: {result.stderr}")

            elif self.command == "upgrade":
                self.progress_signal.emit(f"Atualizando {self.package_name}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", self.package_name],
                    capture_output=True, text=True, encoding='utf-8', timeout=120
                )
                if result.returncode == 0:
                    self.finished_signal.emit(True, f"Pacote {self.package_name} atualizado com sucesso!")
                else:
                    self.finished_signal.emit(False, f"Erro ao atualizar: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.finished_signal.emit(False, "Timeout: A operação demorou muito.")
        except Exception as e:
            self.finished_signal.emit(False, f"Erro: {str(e)}")

class PackageManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Gerenciador de Pacotes Python")
        self.setGeometry(200, 200, 900, 700)
        self.setup_ui()
        self.refresh_packages()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Controles superiores
        top_group = QGroupBox("Gerenciar Pacotes")
        top_layout = QVBoxLayout()

        # Busca e instalação
        install_layout = QHBoxLayout()
        self.package_input = QLineEdit()
        self.package_input.setPlaceholderText("Nome do pacote...")
        self.package_input.returnPressed.connect(self.search_package)
        install_layout.addWidget(self.package_input)

        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("Versão (opcional)")
        self.version_input.setFixedWidth(100)
        install_layout.addWidget(self.version_input)

        self.search_btn = QPushButton("🔍 Buscar")
        self.search_btn.clicked.connect(self.search_package)
        install_layout.addWidget(self.search_btn)

        self.install_btn = QPushButton("📥 Instalar")
        self.install_btn.clicked.connect(self.install_package)
        install_layout.addWidget(self.install_btn)

        top_layout.addLayout(install_layout)

        # Botões de ação
        action_layout = QHBoxLayout()

        self.uninstall_btn = QPushButton("🗑️ Desinstalar")
        self.uninstall_btn.clicked.connect(self.uninstall_package)
        action_layout.addWidget(self.uninstall_btn)

        self.upgrade_btn = QPushButton("🔄 Atualizar")
        self.upgrade_btn.clicked.connect(self.upgrade_package)
        action_layout.addWidget(self.upgrade_btn)

        self.refresh_btn = QPushButton("🔄 Atualizar Lista")
        self.refresh_btn.clicked.connect(self.refresh_packages)
        action_layout.addWidget(self.refresh_btn)

        top_layout.addLayout(action_layout)
        top_group.setLayout(top_layout)
        layout.addWidget(top_group)

        # Lista de pacotes
        packages_group = QGroupBox("Pacotes Instalados")
        packages_layout = QVBoxLayout()

        # Filtro
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filtrar pacotes...")
        self.filter_input.textChanged.connect(self.filter_packages)
        filter_layout.addWidget(self.filter_input)
        packages_layout.addLayout(filter_layout)

        self.packages_list = QListWidget()
        self.packages_list.itemDoubleClicked.connect(self.package_selected)
        self.packages_list.setAlternatingRowColors(True)
        packages_layout.addWidget(self.packages_list)

        # Informações do pacote
        self.package_info = QLabel("Selecione um pacote para ver informações")
        self.package_info.setWordWrap(True)
        self.package_info.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        packages_layout.addWidget(self.package_info)

        packages_group.setLayout(packages_layout)
        layout.addWidget(packages_group)

        # Área de output
        output_group = QGroupBox("Log de Operações")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(150)
        output_layout.addWidget(self.output_text)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        output_layout.addWidget(self.progress_bar)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        self.setLayout(layout)

    def refresh_packages(self):
        """Atualiza lista de pacotes"""
        self.progress_bar.setVisible(True)
        self.output_text.append("🔄 Atualizando lista de pacotes...")

        self.thread = PackageManagerThread("list")
        self.thread.output_signal.connect(self.update_packages_list)
        self.thread.finished_signal.connect(self.on_operation_finished)
        self.thread.progress_signal.connect(self.update_progress_text)
        self.thread.start()

    def update_packages_list(self, output):
        """Atualiza a lista de pacotes com a saída do pip"""
        try:
            packages = json.loads(output)
            self.all_packages = packages
            self.filter_packages()
        except json.JSONDecodeError:
            self.output_text.append("❌ Erro ao analisar lista de pacotes")

    def filter_packages(self):
        """Filtra pacotes baseado no texto do filtro"""
        if not hasattr(self, 'all_packages'):
            return

        filter_text = self.filter_input.text().lower()
        self.packages_list.clear()

        for package in self.all_packages:
            name = package['name'].lower()
            version = package['version'].lower()

            if filter_text in name or filter_text in version:
                item_text = f"{package['name']} ({package['version']})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, package)
                self.packages_list.addItem(item)

    def search_package(self):
        """Busca pacote no PyPI"""
        package_name = self.package_input.text().strip()
        if not package_name:
            QMessageBox.warning(self, "Aviso", "Digite o nome do pacote!")
            return

        self.output_text.append(f"🔍 Buscando pacote: {package_name}")
        self.progress_bar.setVisible(True)

        self.thread = PackageManagerThread("search", package_name)
        self.thread.output_signal.connect(self.show_search_results)
        self.thread.finished_signal.connect(self.on_operation_finished)
        self.thread.progress_signal.connect(self.update_progress_text)
        self.thread.start()

    def show_search_results(self, output):
        """Mostra resultados da busca"""
        self.output_text.append("Resultados da busca:\n" + output)

    def install_package(self, package_name):
        """Instala um pacote Python"""
        try:
            # CORREÇÃO: Use self.output_text local, não output_tabs (que é do IDE)
            self.output_text.appendPlainText(f"📦 Instalando {package_name}...\n")

            # CORREÇÃO: Chame get_python_executable do parent (IDE)
            python_exec = self.parent().get_python_executable() if self.parent() else sys.executable

            result = subprocess.run(
                [python_exec, "-m", "pip", "install", package_name],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stdout:
                self.output_text.appendPlainText(result.stdout)
            if result.stderr:
                self.output_text.appendPlainText(result.stderr)

            if result.returncode == 0:
                self.output_text.appendPlainText(f"\n✅ {package_name} instalado com sucesso!")
            else:
                self.output_text.appendPlainText(f"\n❌ Falha na instalação de {package_name}")

        except Exception as e:
            self.output_text.appendPlainText(f"💥 Erro na instalação: {str(e)}")

    def uninstall_package(self):
        """Desinstala pacote selecionado"""
        current_item = self.packages_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione um pacote da lista!")
            return

        package_data = current_item.data(Qt.UserRole)
        package_name = package_data['name']

        reply = QMessageBox.question(
            self, "Confirmar",
            f"Desinstalar o pacote {package_name}?"
        )
        if reply == QMessageBox.Yes:
            self.output_text.append(f"🗑️ Desinstalando {package_name}")
            self.thread = PackageManagerThread("uninstall", package_name)
            self.thread.finished_signal.connect(self.on_operation_finished)
            self.thread.progress_signal.connect(self.update_progress_text)
            self.thread.start()

    def upgrade_package(self):
        """Atualiza pacote selecionado"""
        current_item = self.packages_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione um pacote da lista!")
            return

        package_data = current_item.data(Qt.UserRole)
        package_name = package_data['name']

        self.output_text.append(f"🔄 Atualizando {package_name}")
        self.thread = PackageManagerThread("upgrade", package_name)
        self.thread.finished_signal.connect(self.on_operation_finished)
        self.thread.progress_signal.connect(self.update_progress_text)
        self.thread.start()

    def package_selected(self, item):
        """Quando um pacote é selecionado na lista"""
        package_data = item.data(Qt.UserRole)
        self.package_input.setText(package_data['name'])

        info_text = f"<b>{package_data['name']}</b> (v{package_data['version']})"
        self.package_info.setText(info_text)

    def on_operation_finished(self, success, message):
        """Quando uma operação é finalizada"""
        self.progress_bar.setVisible(False)

        if success:
            self.output_text.append("✅ " + message)
            self.refresh_packages()  # Atualiza lista após operação
        else:
            self.output_text.append("❌ " + message)

    def update_progress_text(self, message):
        """Atualiza texto de progresso"""
        self.output_text.append("➡️ " + message)

class FindFilesDialog(QDialog):
    def __init__(self, workspace_path, parent=None):
        super().__init__(parent)
        self.workspace_path = workspace_path
        self.setWindowTitle("Buscar Arquivos por Nome")
        self.setGeometry(300, 300, 700, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Controles de busca
        search_layout = QHBoxLayout()
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Digite parte do nome do arquivo...")
        self.filename_input.textChanged.connect(self.search_files)
        search_layout.addWidget(QLabel("Nome do arquivo:"))
        search_layout.addWidget(self.filename_input)

        layout.addLayout(search_layout)

        # Lista de resultados
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(QLabel("Arquivos Encontrados:"))
        layout.addWidget(self.results_list)

        self.setLayout(layout)

    def search_files(self):
        search_text = self.filename_input.text().strip().lower()
        self.results_list.clear()

        if not search_text:
            return

        for root, dirs, files in os.walk(self.workspace_path):
            for file in files:
                if search_text in file.lower():
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, self.workspace_path)
                    self.results_list.addItem(relative_path)

    def open_file(self, item):
        """Abre o arquivo selecionado no IDE pai"""
        file_path = os.path.join(self.workspace_path, item.text())
        if os.path.exists(file_path):
            # Emitir sinal ou chamar método para abrir o arquivo
            if hasattr(self.parent(), 'open_file'):
                self.parent().open_file(file_path)
            self.close()
        else:
            print(f"Arquivo não encontrado: {file_path}")  # Log para debug

class SymbolCollector(ast.NodeVisitor):
    """Coletor de símbolos via AST - COMPLETA"""

    def __init__(self):
        super().__init__()
        self.imported_modules = {}
        self.local_symbols = {
            'functions': set(), 'classes': set(), 'variables': set(), 'methods': {}
        }
        self.class_hierarchy = {}
        self.current_class = None

    def visit_Import(self, node):
        for alias in node.names:
            self.imported_modules[alias.name] = []
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            imports = [
                alias.name for alias in node.names]
            self.imported_modules[node.module] = imports
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.local_symbols['classes'].add(node.name)
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        if self.current_class:
            if self.current_class not in self.local_symbols['methods']:
                self.local_symbols['methods'][self.current_class] = set(
                )
            self.local_symbols['methods'][self.current_class].add(
                f"{node.name}()")
        else:
            self.local_symbols['functions'].add(
                f"{node.name}()")
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_symbols['variables'].add(
                    target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        # Captura nomes de variáveis em expressões
        if isinstance(node.ctx, ast.Store):
            self.local_symbols['variables'].add(
                node.id)
        self.generic_visit(node)


class CodeAnalyzer:
    """Analisador de código para autocomplete inteligente"""

    def __init__(self):
        self.imported_modules = {}
        self.local_symbols = {}

    def analyze_code(self, code, file_path="<string>"):
        """Analisa código e extrai símbolos"""
        try:
            tree = ast.parse(
                code, filename=file_path)
            collector = SymbolCollector()
            collector.visit(tree)

            return {
                'imports': collector.imported_modules,
                'symbols': collector.local_symbols,
                'classes': collector.class_hierarchy
            }
        except:
            return self.analyze_with_regex(code)

    def analyze_with_regex(self, code):
        """Fallback com regex"""
        imports = {}
        # Detecta imports com regex
        import_pattern = r'(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(import_pattern, code)
        for module in matches:
            imports[module] = []

        return {
            'imports': imports,
            'symbols': {'functions': set(), 'classes': set(), 'variables': set(), 'methods': {}},
            'classes': {}
        }


class FindSimilarDialog(QDialog):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("🔍 Encontrar Textos Similares")
        self.setGeometry(300, 300, 600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Controles de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Digite o texto para buscar similares...")
        self.search_input.textChanged.connect(self.find_similar)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)

        self.case_sensitive = QCheckBox(
            "Diferenciar maiúsc/minúsc")
        search_layout.addWidget(self.case_sensitive)

        self.whole_word = QCheckBox("Palavra inteira")
        search_layout.addWidget(self.whole_word)

        layout.addLayout(search_layout)

        # Lista de resultados
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(
            self.go_to_match)
        layout.addWidget(
            QLabel("Textos Similares Encontrados:"))
        layout.addWidget(self.results_list)

        # Estatísticas
        self.stats_label = QLabel("Nenhuma busca realizada")
        layout.addWidget(self.stats_label)

        # Botões
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Selecionar Todos")
        self.select_all_btn.clicked.connect(
            self.select_all_matches)
        button_layout.addWidget(self.select_all_btn)

        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def find_similar(self):
        search_text = self.search_input.text().strip()
        if not search_text:
            self.results_list.clear()
            self.stats_label.setText(
                "Nenhuma busca realizada")
            return

        # Obter todo o texto do editor
        full_text = self.editor.toPlainText()
        lines = full_text.split('\n')

        self.results_list.clear()
        matches_count = 0

        # Preparar padrão de busca
        pattern = search_text
        if self.whole_word.isChecked():
            pattern = r'\b' + \
                      re.escape(search_text) + r'\b'
        else:
            pattern = re.escape(search_text)

        flags = 0 if self.case_sensitive.isChecked() else re.IGNORECASE

        try:
            regex = re.compile(pattern, flags)

            # Buscar em cada linha
            for line_num, line in enumerate(
                    lines, 1):
                line_matches = list(
                    regex.finditer(line))
                for match in line_matches:
                    start_pos = match.start()
                    end_pos = match.end()
                    matched_text = line[max(
                        0, start_pos - 10):end_pos + 10].replace('\n', ' ')

                    item_text = f"Linha {line_num}: ...{matched_text}..."
                    self.results_list.addItem(
                        item_text)
                    matches_count += 1

            self.stats_label.setText(
                f"Encontrados {matches_count} resultados similares")

        except re.error as e:
            self.stats_label.setText(
                f"Erro no padrão de busca: {str(e)}")

    def go_to_match(self, item):
        # Extrair número da linha do item selecionado
        text = item.text()
        line_match = re.search(r'Linha (\d+):', text)
        if line_match:
            line_num = int(
                line_match.group(1)) - 1  # Converter para índice 0-based

            # Mover cursor para a linha
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.Start)
            for _ in range(line_num):
                cursor.movePosition(
                    cursor.Down)

            self.editor.setTextCursor(cursor)
            self.editor.setFocus()
            self.close()

    def select_all_matches(self):
        search_text = self.search_input.text().strip()
        if not search_text:
            return

        # Preparar seleção múltipla
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.Start)

        # Preparar padrão de busca
        pattern = search_text
        if self.whole_word.isChecked():
            pattern = r'\b' + \
                      re.escape(search_text) + r'\b'
        else:
            pattern = re.escape(search_text)

        flags = 0 if self.case_sensitive.isChecked() else re.IGNORECASE

        try:
            regex = re.compile(pattern, flags)
            full_text = self.editor.toPlainText()

            # Encontrar todas as ocorrências
            matches = list(
                regex.finditer(full_text))
            if matches:
                # Selecionar a primeira
                # ocorrência
                first_match = matches[0]
                cursor.setPosition(
                    first_match.start())
                cursor.setPosition(
                    first_match.end(), cursor.KeepAnchor)
                self.editor.setTextCursor(
                    cursor)

                QMessageBox.information(self, "Seleção",
                                        f"{len(matches)} ocorrências encontradas. Primeira selecionada.")

        except re.error as e:
            QMessageBox.warning(
                self, "Erro", f"Erro no padrão de busca: {str(e)}")


# ===== CLASSE PRINCIPAL IDE =====
class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self._initialize_variables()
        self.setup_managers()
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
		
        # Inicializar plugins APÓS a UI estar completamente
        # configurada
        QTimer.singleShot(100, self.setup_plugin_system)

        # Configuração global de exceções
        sys.excepthook = self.exception_hook

    def exception_hook(self, exctype, value, tb):
        """Captura exceções globais"""
        print("ERRO GLOBAL:", exctype, value)
        traceback.print_exception(exctype, value, tb)
        sys.__excepthook__(exctype, value, tb)

    def setup_plugin_system(self):
        """Inicializa o sistema de plugins de forma segura"""
        try:
            self.plugin_manager = PluginManager(
                self)
            self.plugin_manager.load_plugins()
            self.integrate_plugins()
            print(
                "🔌 Sistema de plugins inicializado com sucesso")
        except Exception as e:
            print(
                f"❌ Erro ao inicializar plugins: {e}")

    def setup_managers(self):
        """Inicializa os novos gerenciadores"""
        self.python_version_manager = PythonVersionManager()
        self.theme_manager = ThemeManager()
        self.indentation_checker = IndentationChecker()
        self.language_config = LanguageConfig()
        self.language_syntax_manager = LanguageSyntaxManager()

        # Gerenciador de cache global
        global module_cache_manager
        module_cache_manager = ModuleCacheManager()

    def _initialize_variables(self):
        """INICIALIZAÇÃO SEGURA: Define TODAS as variáveis com valores padrão"""
        self.current_file = ""
        self.project_path = ""
        self.python_path = sys.executable
        self.venv_path = ""
        self.current_font = "Consolas"
        self.clipboard_path = ""
        self.is_cut = False

        # Inicializar processos como None
        self.shell_process = None
        self.debug_process = None
        self.current_process = None

        # Workers
        self.linter_worker = None
        self.auto_complete_worker = None
        self.debug_worker = None

        # Estado
        self.is_linting = False
        self.pending_lint = False
        self.last_lint_content = ""

        # UI components - inicializar como None
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

        self.file_info_label = None
        self.cursor_info_label = None
        self.project_info_label = None
        self.status_progress = None

    def setup_ui(self):
        self.setWindowTitle("Py Dragon Studio IDE")
        self.setGeometry(100, 100, 1400, 900)

        self.set_dark_theme_optimized()

        self.setup_central_widget()
        self.setup_docks()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()

        self.start_shell()
        self.check_python_version()

    def setup_central_widget(self):
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
        self.setup_left_dock()
        self.setup_right_dock()
        self.setup_bottom_dock()

    def setup_left_dock(self):
        left_dock = QDockWidget("Explorer", self)
        left_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        left_dock.setMaximumWidth(300)

        left_tabs = QTabWidget()
        left_tabs.setTabPosition(QTabWidget.West)

        self.setup_file_explorer(left_tabs)
        self.setup_problems_widget(left_tabs)

        left_dock.setWidget(left_tabs)
        self.addDockWidget(Qt.LeftDockWidgetArea, left_dock)

    def setup_file_explorer(self, parent_tabs):
        explorer_widget = QWidget()
        explorer_layout = QVBoxLayout(explorer_widget)

        explorer_toolbar = QToolBar()
        explorer_toolbar.setIconSize(QSize(16, 16))

        self.refresh_explorer_btn = QAction("🔄", self)
        self.new_file_btn = QAction("📄", self)
        self.new_folder_btn = QAction("📁", self)

        explorer_toolbar.addAction(self.refresh_explorer_btn)
        explorer_toolbar.addAction(self.new_file_btn)
        explorer_toolbar.addAction(self.new_folder_btn)

        explorer_layout.addWidget(explorer_toolbar)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.homePath())

        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(
            self.file_model.index(QDir.homePath()))
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(15)
        self.file_tree.setSortingEnabled(True)

        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)

        explorer_layout.addWidget(self.file_tree)

        parent_tabs.addTab(explorer_widget, "📁 Explorer")

    def setup_problems_widget(self, parent_tabs):
        problems_widget = QWidget()
        problems_layout = QVBoxLayout(problems_widget)

        problems_toolbar = QToolBar()
        problems_toolbar.setIconSize(QSize(16, 16))

        self.clear_problems_btn = QAction("🗑️", self)
        self.run_lint_btn = QAction("🔍", self)

        problems_toolbar.addAction(self.clear_problems_btn)
        problems_toolbar.addAction(self.run_lint_btn)

        problems_layout.addWidget(problems_toolbar)

        self.problems_list = QListWidget()
        self.problems_list.setAlternatingRowColors(True)
        self.problems_list.setItemDelegate(ProblemsDelegate())

        problems_layout.addWidget(self.problems_list)

        parent_tabs.addTab(problems_widget, "⚠️ Problems")

    def setup_right_dock(self):
        right_dock = QDockWidget("Minimap", self)
        right_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        right_dock.setMaximumWidth(200)

        self.minimap = Minimap()
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
        bottom_dock = QDockWidget("Output", self)
        bottom_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

        self.output_tabs = QTabWidget()
        self.output_tabs.setTabPosition(QTabWidget.North)

        self.setup_terminal_tab()
        self.setup_output_tab()
        self.setup_debug_tab()
        self.setup_errors_tab()
        self.setup_lint_tab()

        bottom_dock.setWidget(self.output_tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, bottom_dock)

    def setup_terminal_tab(self):
        self.terminal_text = TerminalTextEdit(self)
        self.terminal_text.setFont(QFont(self.current_font, 10))
        self.terminal_text.setStyleSheet("""
                                                QPlainTextEdit {
                                                                background-color: #1e1e1e;
                                                                color: #d4d4d4;
                                                                border: none;
                                                                font-family: 'Consolas', monospace;
                                                }
                                """)
        self.output_tabs.addTab(
            self.terminal_text, "💻 Terminal")

    def setup_output_tab(self):
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
        self.debug_text = DebugTerminal(self)
        self.debug_text.setFont(QFont(self.current_font, 10))
        self.output_tabs.addTab(self.debug_text, "🐛 Debug")

    def setup_errors_tab(self):
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
        menubar = self.menuBar()

        file_menu = menubar.addMenu("📁 Arquivo")
        self.setup_file_menu(file_menu)

        edit_menu = menubar.addMenu("✏️ Editar")
        self.setup_edit_menu(edit_menu)

        view_menu = menubar.addMenu("👁️ Visualizar")
        self.setup_view_menu(view_menu)

        run_menu = menubar.addMenu("🚀 Executar")
        self.setup_run_menu(run_menu)

        project_menu = menubar.addMenu("📦 Projeto")
        self.setup_project_menu(project_menu)

        tools_menu = menubar.addMenu("🛠️ Ferramentas")
        self.setup_tools_menu(tools_menu)

        help_menu = menubar.addMenu("❓ Ajuda")
        self.setup_help_menu(help_menu)

    def setup_tools_menu(self, tools_menu):
        """Configura o menu de ferramentas com as novas funcionalidades"""

        # Gestor de Versões Python
        python_versions_action = QAction(
            "🐍 Gerenciador de Versões Python", self)
        python_versions_action.triggered.connect(
            self.open_python_version_manager)
        tools_menu.addAction(python_versions_action)

        # Localizador de Textos Similares Aprimorado
        find_similar_action = QAction(
            "🔍 Localizador de Textos Similares", self)
        find_similar_action.setShortcut("Ctrl+Shift+F")
        find_similar_action.triggered.connect(
            self.open_advanced_find_similar)
        tools_menu.addAction(find_similar_action)

        # Gerenciador de Pacotes
        package_action = QAction(
            "📦 Gerenciador de Pacotes Python", self)
        package_action.setShortcut("Ctrl+Shift+P")
        package_action.triggered.connect(
            self.open_package_manager)
        tools_menu.addAction(package_action)

        # Gerenciador de Temas
        theme_action = QAction("🎨 Gerenciador de Temas", self)
        theme_action.triggered.connect(self.open_theme_manager)
        tools_menu.addAction(theme_action)

        tools_menu.addSeparator()

        # GERENCIADOR DE PLUGINS
        plugin_manager_action = QAction(
            "🔌 Gerenciador de Plugins", self)
        plugin_manager_action.triggered.connect(
            self.show_plugin_manager)
        tools_menu.addAction(plugin_manager_action)

        tools_menu.addSeparator()

        # Outras ferramentas existentes
        manage_packages_action = QAction(
            "🔧 Gerenciar Pacotes", self)
        manage_packages_action.triggered.connect(
            self.manage_packages)
        tools_menu.addAction(manage_packages_action)

        select_python_action = QAction(
            "🐍 Selecionar Python", self)
        select_python_action.triggered.connect(
            self.select_python_version)
        tools_menu.addAction(select_python_action)

        format_action = QAction("📐 Formatar Código", self)
        format_action.setShortcut("Ctrl+Shift+L")
        format_action.triggered.connect(self.format_code)
        tools_menu.addAction(format_action)

        settings_action = QAction("⚙️ Configurações", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

    def show_plugin_manager(self):
        """Mostra gerenciador de plugins"""
        QMessageBox.information(self, "Gerenciador de Plugins",
                                "Sistema de plugins em desenvolvimento!\n\n"
                                "Em breve você poderá instalar e gerenciar plugins.")

    def open_python_version_manager(self):
        """Abre o gerenciador de versões Python"""
        dialog = PythonVersionDialog(
            self.python_version_manager, self)
        dialog.exec()

    def open_advanced_find_similar(self):
        """Abre o localizador de textos similares aprimorado"""
        editor = self.get_current_editor()
        if editor:
            dialog = AdvancedFindSimilarDialog(
                editor, self)
            dialog.exec()
        else:
            QMessageBox.warning(
                self, "Aviso", "Nenhum editor ativo!")

    def open_package_manager(self):
        """Abre o gerenciador de pacotes Python"""
        dialog = PackageManagerDialog(self)
        dialog.exec()

    def open_find_similar(self):
        """Abre a busca de textos similares"""
        current_editor = self.get_current_editor()
        if current_editor:
            dialog = FindSimilarDialog(
                current_editor, self)
            dialog.exec()
        else:
            QMessageBox.warning(
                self, "Aviso", "Nenhum editor ativo!")

    def open_find_files(self):
        """Abre a busca de arquivos por nome"""
        if hasattr(self, 'project_path') and self.project_path:
            dialog = FindFilesDialog(
                self.project_path, self)
            dialog.exec()
        else:
            QMessageBox.warning(
                self, "Aviso", "Nenhum projeto aberto!")

    def open_theme_manager(self):
        """Abre o gerenciador de temas"""
        dialog = ThemeDialog(self.theme_manager, self)
        dialog.exec()

    def integrate_plugins(self):
        """Integra plugins na interface do IDE"""
        # Por enquanto, apenas log
        print("🔌 Sistema de plugins inicializado")

        # Adiciona ações dos plugins (quando existirem)
        plugin_actions = self.plugin_manager.get_plugin_actions()

        if plugin_actions:
            # Adiciona ao menu Ferramentas
            tools_menu = None
            for action in self.menuBar().actions():
                if action.text() == "🛠️ Ferramentas":
                    tools_menu = action.menu()
                    break

            if tools_menu:
                tools_menu.addSeparator()
                for action in plugin_actions:
                    tools_menu.addAction(
                        action)

    def setup_file_menu(self, menu):
        actions = [
            ("📄 Novo Arquivo", "Ctrl+N", self.new_file),
            ("📁 Novo Projeto", "Ctrl+Shift+N",
             self.create_project),
            ("📂 Abrir Arquivo", "Ctrl+O", self.open_file),
            ("📂 Abrir Projeto",
             "Ctrl+Shift+O", self.set_project),
            ("💾 Salvar", "Ctrl+S", self.save_file),
            ("💾 Salvar Como", "Ctrl+Shift+S",
             self.save_file_as),
            ("🔒 Salvar Tudo", "Ctrl+Alt+S",
             self.save_all_files),
            ("---", None, None),
            ("🚪 Sair", "Ctrl+Q", self.close)
        ]

        self.create_menu_actions(menu, actions)

    def apply_theme(self, theme_name):
        """Aplica um tema ao IDE"""
        theme = self.theme_manager.get_theme(theme_name)
        colors = theme["colors"]

        # Aplica o tema à interface
        self.apply_theme_to_ui(theme)

        # Aplica syntax highlighting aos editores
        self.apply_syntax_theme(theme)

        print(f"Tema '{theme_name}' aplicado!")

    def apply_theme_to_ui(self, theme):
        """Aplica o tema à interface do usuário"""
        colors = theme["colors"]

        palette = QPalette()

        if theme["type"] == "dark":
            # Configuração para tema escuro
            palette.setColor(
                QPalette.Window, QColor(colors["background"]))
            palette.setColor(
                QPalette.WindowText, QColor(
                    colors["foreground"]))
            palette.setColor(
                QPalette.Base, QColor(colors["background"]))
            palette.setColor(
                QPalette.AlternateBase, QColor(
                    colors["selection"]))
            palette.setColor(
                QPalette.ToolTipBase, QColor(
                    colors["background"]))
            palette.setColor(
                QPalette.ToolTipText, QColor(
                    colors["foreground"]))
            palette.setColor(
                QPalette.Text, QColor(colors["foreground"]))
            palette.setColor(
                QPalette.Button, QColor(colors["background"]))
            palette.setColor(
                QPalette.ButtonText, QColor(
                    colors["foreground"]))
            palette.setColor(
                QPalette.BrightText, Qt.red)
            palette.setColor(
                QPalette.Link, QColor(colors["info"]))
            palette.setColor(
                QPalette.Highlight, QColor(
                    colors["selection"]))
            palette.setColor(
                QPalette.HighlightedText, QColor(
                    colors["foreground"]))
        else:
            # Configuração para tema claro
            palette.setColor(
                QPalette.Window, QColor(colors["background"]))
            palette.setColor(
                QPalette.WindowText, QColor(
                    colors["foreground"]))
            palette.setColor(
                QPalette.Base, Qt.white)
            palette.setColor(
                QPalette.AlternateBase, QColor(
                    colors["selection"]))
            palette.setColor(
                QPalette.ToolTipBase, Qt.white)
            palette.setColor(
                QPalette.ToolTipText, Qt.black)
            palette.setColor(
                QPalette.Text, Qt.black)
            palette.setColor(
                QPalette.Button, QColor(colors["background"]))
            palette.setColor(
                QPalette.ButtonText, Qt.black)
            palette.setColor(
                QPalette.BrightText, Qt.red)
            palette.setColor(
                QPalette.Link, QColor(colors["info"]))
            palette.setColor(
                QPalette.Highlight, QColor(
                    colors["selection"]))
            palette.setColor(
                QPalette.HighlightedText, Qt.white)

        QApplication.setPalette(palette)

    def apply_syntax_theme(self, theme):
        """Aplica o tema de syntax highlighting a todos os editores"""
        # Esta função precisaria ser integrada com seu sistema de syntax highlighting
        # Para este exemplo, vamos apenas atualizar os editores
        # abertos
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, EditorTab):
                # Aqui você atualizaria
                # o highlighter com as
                # novas cores
                pass

    def check_indentation_errors(self):
        """Verifica erros de indentação no arquivo atual"""
        editor = self.get_current_editor()
        if not editor or not hasattr(
                editor, 'file_path') or not editor.file_path.endswith('.py'):
            return

        code = editor.toPlainText()
        errors = self.indentation_checker.check_code(
            code, editor.file_path)

        if errors:
            self.show_indentation_errors(errors)
        else:
            self.statusBar().showMessage("✅ Nenhum erro de indentação encontrado", 3000)

    def show_indentation_errors(self, errors):
        """Mostra erros de indentação na lista de problemas"""
        # Limpa problemas anteriores de indentação
        for i in range(self.problems_list.count() - 1, -1, -1):
            item = self.problems_list.item(i)
            data = item.data(Qt.UserRole)
            if data and data.get(
                    'type') == 'indentation':
                self.problems_list.takeItem(
                    i)

        # Adiciona novos erros
        for error in errors:
            item_text = f"Linha {error['line']}: {error['message']} - {error['suggestion']}"
            item = QListWidgetItem(item_text)

            # Define ícone de erro
            # Vermelho para erros
            item.setForeground(QColor(255, 0, 0))

            data = {
                'file': getattr(self.get_current_editor(), 'file_path', ''),
                'line': error['line'],
                'type': 'indentation',
                'message': error['message']
            }
            item.setData(Qt.UserRole, data)

            self.problems_list.addItem(item)

        self.statusBar().showMessage(
            f"❌ Encontrados {len(errors)} erro(s) de indentação", 5000)

    def setup_edit_menu(self, menu):
        actions = [
            ("↶ Desfazer", "Ctrl+Z", self.undo),
            ("↷ Refazer", "Ctrl+Y", self.redo),
            ("---", None, None),
            ("✂️ Recortar", "Ctrl+X", self.cut),
            ("📋 Copiar", "Ctrl+C", self.copy),
            ("📝 Colar", "Ctrl+V", self.paste),
            ("---", None, None),
            ("🔍 Buscar", "Ctrl+F",
             self.show_find_dialog),
            ("🔄 Substituir", "Ctrl+H",
             self.show_replace_dialog),
            ("---", None, None),
            ("🎯 Auto-completar", "Ctrl+Space",
             self.force_auto_complete_current),
            ("📐 Corrigir Indentação", "Ctrl+I",
             self.fix_indentation_current)
        ]

        self.create_menu_actions(menu, actions)

    def schedule_linting(self):
        """Agenda verificação de código incluindo indentação"""
        editor = self.get_current_editor()
        if not editor:
            return

        current_content = editor.toPlainText()

        if (current_content != self.last_lint_content and
                hasattr(editor, 'file_path') and
                editor.file_path and
                editor.file_path.endswith('.py')):

            if self.is_linting:
                self.pending_lint = True
            else:
                # Usa QTimer para
                # linting
                QTimer.singleShot(
                    2000, self.run_linter)

            # Verifica indentação imediatamente
            # (mais rápido)
            self.check_indentation_errors()

    def setup_view_menu(self, menu):
        actions = [
            ("📊 Layout Dividido",
             "Ctrl+\\", self.split_view),
            ("🔍 Zoom In", "Ctrl+=", self.zoom_in),
            ("🔍 Zoom Out", "Ctrl+-", self.zoom_out),
            ("🔍 Zoom Reset", "Ctrl+0", self.zoom_reset),
            ("---", None, None),
            ("👁️ Mostrar/Ocultar Explorer",
             "Ctrl+Shift+E", self.toggle_explorer),
            ("👁️ Mostrar/Ocultar Terminal",
             "Ctrl+`", self.toggle_terminal),
            ("👁️ Mostrar/Ocultar Minimap",
             "Ctrl+Shift+M", self.toggle_minimap),
            ("---", None, None),
            ("🎨 Tema Escuro", None,
             lambda: self.set_dark_theme_optimized()),
            ("🎨 Tema Claro", None,
             lambda: self.set_light_theme()),
            ("🔤 Fonte...", None, self.show_font_dialog)
        ]

        self.create_menu_actions(menu, actions)

    def setup_run_menu(self, menu):
        actions = [
            ("▶️ Executar", "F5", self.run_code),
            ("🐛 Debug", "F6", self.debug_code),
            ("⏸️ Pausar", "F7", self.pause_execution),
            ("⏹️ Parar", "F8", self.stop_execution),
            ("---", None, None),
            ("🧪 Executar Testes",
             "Ctrl+T", self.run_tests),
            ("📊 Coverage", "Ctrl+Shift+T",
             self.run_coverage)
        ]

        self.create_menu_actions(menu, actions)

    def setup_project_menu(self, menu):
        actions = [
            ("📦 Novo Projeto", None,
             self.create_project),
            ("📂 Abrir Projeto", None, self.set_project),
            ("🔧 Configurar Projeto", None,
             self.configure_project),
            ("---", None, None),
            ("🐍 Criar Virtualenv",
             None, self.create_venv),
            ("📚 Instalar Dependências", None,
             self.install_dependencies),
            ("---", None, None),
            ("📦 Empacotar", None, self.package_project),
            ("🚀 Deploy", None, self.deploy_project)
        ]

        self.create_menu_actions(menu, actions)

    def setup_help_menu(self, menu):
        actions = [
            ("📚 Documentação", "F1",
             self.show_documentation),
            ("🐛 Reportar Bug", None, self.report_bug),
            ("💡 Sugerir Feature", None,
             self.suggest_feature),
            ("---", None, None),
            ("ℹ️ Sobre", None, self.show_about)
        ]

        self.create_menu_actions(menu, actions)

    def create_menu_actions(self, menu, actions):
        for text, shortcut, callback in actions:
            if text == "---":
                menu.addSeparator()
            else:
                action = QAction(
                    text, self)
                if shortcut:
                    action.setShortcut(
                        shortcut)
                if callback:
                    action.triggered.connect(
                        callback)
                menu.addAction(action)

    def setup_toolbar(self):
        toolbar = QToolBar("Ferramentas Principais")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(True)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        actions = [
            ("📄", "Novo Arquivo",
             "Ctrl+N", self.new_file),
            ("📂", "Abrir Arquivo",
             "Ctrl+O", self.open_file),
            ("💾", "Salvar", "Ctrl+S", self.save_file),
            ("---", None, None, None),
            ("↶", "Desfazer", "Ctrl+Z", self.undo),
            ("↷", "Refazer", "Ctrl+Y", self.redo),
            ("---", None, None, None),
            ("▶️", "Executar", "F5", self.run_code),
            ("🐛", "Debug", "F6", self.debug_code),
            ("---", None, None, None),
            ("🔍", "Buscar", "Ctrl+F",
             self.show_find_dialog),
            ("🎯", "Auto-completar", "Ctrl+Space",
             self.force_auto_complete_current)
        ]

        for icon, text, shortcut, callback in actions:
            if icon == "---":
                toolbar.addSeparator()
            else:
                action = QAction(
                    icon, self)
                action.setText(text)
                action.setToolTip(text)
                if shortcut:
                    action.setShortcut(
                        shortcut)
                if callback:
                    action.triggered.connect(
                        callback)
                toolbar.addAction(
                    action)

        self.addToolBar(toolbar)

    def setup_statusbar(self):
        status_bar = self.statusBar()

        self.file_info_label = QLabel("Sem arquivo")
        status_bar.addWidget(self.file_info_label)

        self.cursor_info_label = QLabel("Linha: 1, Coluna: 1")
        status_bar.addPermanentWidget(self.cursor_info_label)

        self.project_info_label = QLabel("Sem projeto")
        status_bar.addPermanentWidget(self.project_info_label)

        self.status_progress = StatusBarProgress()
        status_bar.addPermanentWidget(self.status_progress)

    def setup_connections(self):
        self.file_tree.doubleClicked.connect(
            self.open_from_tree)
        self.file_tree.setContextMenuPolicy(
            Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(
            self.show_explorer_context_menu)

        self.problems_list.itemClicked.connect(
            self.jump_to_error)

        self.tab_widget.tabCloseRequested.connect(
            self.close_tab)
        self.tab_widget.currentChanged.connect(
            self.on_tab_changed)

        self.refresh_explorer_btn.triggered.connect(
            self.refresh_explorer)
        self.new_file_btn.triggered.connect(
            self.create_new_file_in_explorer)
        self.new_folder_btn.triggered.connect(
            self.create_new_folder_in_explorer)
        self.clear_problems_btn.triggered.connect(
            self.clear_problems)
        self.run_lint_btn.triggered.connect(self.run_linter)
        self.tab_widget.currentChanged.connect(
            self.update_cursor_info)

    def update_cursor_info(self):
        """Atualiza informações do cursor na statusbar"""
        editor = self.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1
            self.cursor_info_label.setText(
                f"Linha: {line}, Coluna: {column}")

            # Atualiza também as informações do
            # arquivo
            if hasattr(
                    editor, 'file_path') and editor.file_path:
                self.update_file_info(
                    editor.file_path)

    def setup_shortcuts(self):
        QShortcut(
            "Ctrl+Tab",
            self).activated.connect(
            self.next_tab)
        QShortcut(
            "Ctrl+Shift+Tab",
            self).activated.connect(
            self.previous_tab)

        QShortcut(
            "Ctrl+P",
            self).activated.connect(
            self.show_command_palette)

    def set_dark_theme_optimized(self):
        palette = QPalette()

        dark_bg = QColor(30, 30, 30)
        darker_bg = QColor(20, 20, 20)
        light_text = QColor(220, 220, 220)
        highlight = QColor(86, 156, 214)
        highlight_text = QColor(255, 255, 255)

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
        palette.setColor(
            QPalette.HighlightedText, highlight_text)

        QApplication.setPalette(palette)
        QApplication.setStyle("Fusion")

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

    def new_file(self):
        """Cria um novo arquivo usando o diálogo especializado"""
        dialog = NewFileDialog(self)
        if dialog.exec():
            file_name = dialog.get_file_name()
            if file_name:
                # Cria editor vazio
                editor = QPlainTextEdit()
                editor.setFont(
                    QFont(self.current_font, 12))

                # Adiciona à aba
                index = self.tab_widget.addTab(
                    editor, f"📄 {file_name}")
                self.tab_widget.setCurrentIndex(
                    index)

                # Armazena caminho
                # temporário
                editor.file_path = None
                editor.is_new_file = True
                editor.file_name = file_name

                editor.setFocus()
                self.update_file_info(
                    None)

    def open_file(self, file_path=None):
        """Abre um arquivo usando o EditorTab aprimorado"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Abrir Arquivo",
                self.project_path or QDir.homePath(),
                "Arquivos de Código (*.py *.js *.html *.css *.json *.xml *.txt *.md *.yml *.yaml *.sql *.java *.cpp *.c *.cs *.php *.rb *.go *.rs *.swift *.kt *.ts);;Todos os Arquivos (*.*)"
            )

        if file_path:
            try:
                # Verifica se já está
                # aberto
                for i in range(
                        self.tab_widget.count()):
                    widget = self.tab_widget.widget(
                        i)
                    if hasattr(
                            widget, 'file_path') and widget.file_path == file_path:
                        self.tab_widget.setCurrentIndex(
                            i)
                        return

                # Cria nova aba com
                # EditorTab
                editor_tab = EditorTab(
                    file_path=file_path, parent=self.tab_widget)
                index = self.tab_widget.addTab(
                    editor_tab, os.path.basename(file_path))
                self.tab_widget.setCurrentIndex(
                    index)

                self.update_file_info(
                    file_path)
                self.statusBar().showMessage(
                    f"✅ Arquivo aberto: {os.path.basename(file_path)}", 3000)

            except Exception as e:
                QMessageBox.warning(
                    self, "Erro", f"Não foi possível abrir o arquivo:\n{str(e)}")

    def save_file(self):
        """Salva o arquivo atual"""
        current_widget = self.tab_widget.currentWidget()

        if isinstance(current_widget, EditorTab):
            editor = current_widget.editor
            if hasattr(
                    editor, 'file_path') and editor.file_path:
                try:
                    with open(editor.file_path, 'w', encoding='utf-8') as f:
                        f.write(
                            editor.toPlainText())
                    self.statusBar().showMessage(
                        f"✅ Arquivo salvo: {os.path.basename(editor.file_path)}", 3000)
                except Exception as e:
                    QMessageBox.warning(
                        self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
            else:
                self.save_file_as()
        else:
            QMessageBox.information(
                self, "Informação", "Nenhum arquivo para salvar.")

    def save_file_as(self):
        """Salva o arquivo atual com novo nome"""
        current_widget = self.tab_widget.currentWidget()

        if isinstance(current_widget, EditorTab):
            editor = current_widget.editor
            new_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Como",
                self.project_path or QDir.homePath(),
                "Todos os Arquivos (*.*)"
            )

            if new_path:
                try:
                    with open(new_path, 'w', encoding='utf-8') as f:
                        f.write(
                            editor.toPlainText())

                    # Atualiza
                    # a aba
                    editor.file_path = new_path
                    index = self.tab_widget.currentIndex()
                    self.tab_widget.setTabText(
                        index, os.path.basename(new_path))

                    self.update_file_info(
                        new_path)
                    self.statusBar().showMessage(
                        f"✅ Arquivo salvo como: {os.path.basename(new_path)}", 3000)

                except Exception as e:
                    QMessageBox.warning(
                        self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")

    def save_all_files(self):
        """Salva todos os arquivos abertos"""
        for i in range(self.tab_widget.count()):
            self.tab_widget.setCurrentIndex(i)
            self.save_file()

    def run_code(self):
        """Executa o código atual com melhorias visuais"""
        current_widget = self.tab_widget.currentWidget()

        if not current_widget or not hasattr(
                current_widget, 'file_path'):
            QMessageBox.information(
                self, "Informação", "Nenhum arquivo para executar.")
            return

        file_path = current_widget.file_path
        if not file_path or not file_path.endswith('.py'):
            QMessageBox.information(
                self, "Informação", "Apenas arquivos Python podem ser executados.")
            return

        try:
            # Salva o arquivo primeiro
            self.save_file()

            # Limpa output anterior
            self.output_text.clear()

            # Mostra que está executando
            self.output_tabs.setCurrentWidget(
                self.output_text)
            self.output_text.appendPlainText(
                f"🚀 Executando: {os.path.basename(file_path)}")
            self.output_text.appendPlainText(
                "=" * 50 + "\n")

            # Executa o código
            python_exec = self.get_python_executable()

            # Configura o processo para capturar
            # saída em tempo real
            self.current_process = QProcess(self)
            self.current_process.setProcessChannelMode(
                QProcess.MergedChannels)

            def handle_output():
                data = self.current_process.readAll().data().decode('utf-8', errors='ignore')
                if data:
                    self.output_text.appendPlainText(
                        data)

            def handle_finished(
                    exit_code, exit_status):
                if exit_code == 0:
                    self.output_text.appendPlainText(
                        f"\n✅ Execução concluída com sucesso!")
                else:
                    self.output_text.appendPlainText(
                        f"\n❌ Execução falhou (código: {exit_code})")

            self.current_process.readyRead.connect(
                handle_output)
            self.current_process.finished.connect(
                handle_finished)

            # Define o diretório de trabalho
            working_dir = self.project_path or os.path.dirname(
                file_path)
            self.current_process.setWorkingDirectory(
                working_dir)

            # Inicia o processo
            self.current_process.start(
                python_exec, [file_path])

            if not self.current_process.waitForStarted(
                    5000):
                self.output_text.appendPlainText(
                    "❌ Erro: Não foi possível iniciar o processo Python")
                return

        except Exception as e:
            self.output_text.appendPlainText(
                f"💥 Erro na execução: {str(e)}")

    def debug_code(self):
        """Executa o código em modo debug com terminal especializado"""
        current_widget = self.tab_widget.currentWidget()

        if not current_widget or not hasattr(
                current_widget, 'file_path'):
            QMessageBox.information(
                self, "Informação", "Nenhum arquivo para depurar.")
            return

        file_path = current_widget.file_path

        try:
            # Salva o arquivo primeiro
            self.save_file()

            # Remove aba de debug existente
            for i in range(
                    self.output_tabs.count()):
                if self.output_tabs.tabText(
                        i) == "🐛 Debug Console":
                    self.output_tabs.removeTab(
                        i)
                    break

            # Cria novo terminal de debug
            debug_terminal = DebugTerminal()
            debug_index = self.output_tabs.addTab(
                debug_terminal, "🐛 Debug Console")
            self.output_tabs.setCurrentIndex(
                debug_index)

            # Inicia o debug
            debug_terminal.start_debug(
                self.get_python_executable(),
                file_path,
                self.project_path or os.path.dirname(
                    file_path)
            )

        except Exception as e:
            self.debug_text.setPlainText(
                f"❌ Erro no debug: {str(e)}")
            self.output_tabs.setCurrentWidget(
                self.debug_text)

    def close_tab(self, index):
        """Fecha uma aba com confirmação se não salvo"""
        widget = self.tab_widget.widget(index)

        if isinstance(widget, EditorTab):
            editor = widget.editor
            # Verifica se há mudanças não salvas
            if hasattr(
                    editor, 'is_modified') and editor.is_modified:
                reply = QMessageBox.question(
                    self,
                    "Arquivo não salvo",
                    f"Deseja salvar as alterações em {os.path.basename(editor.file_path) if editor.file_path else 'novo arquivo'}?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )

                if reply == QMessageBox.Save:
                    self.save_file()
                elif reply == QMessageBox.Cancel:
                    return

        self.tab_widget.removeTab(index)

    def on_tab_changed(self, index):
        """Atualiza a interface quando a aba muda"""
        if index >= 0:
            widget = self.tab_widget.widget(index)
            if isinstance(
                    widget, EditorTab) and hasattr(
                widget.editor, 'file_path') and widget.editor.file_path:
                self.update_file_info(
                    widget.editor.file_path)

                # Atualiza minimap
                self.minimap.setPlainText(
                    widget.editor.toPlainText())
            else:
                self.update_file_info(
                    None)
                self.minimap.clear()

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
        """Mostra diálogo de busca aprimorado"""
        editor = self.get_current_editor()
        if not editor:
            return

        find_text, ok = QInputDialog.getText(
            self,
            "Buscar",
            "Texto para buscar:",
            text=editor.textCursor().selectedText()
        )

        if ok and find_text:
            # Implementação de busca simples
            cursor = editor.textCursor()
            document = editor.document()

            # Busca a partir da posição atual
            cursor = document.find(
                find_text, cursor)
            if not cursor.isNull():
                editor.setTextCursor(
                    cursor)
                editor.setFocus()
            else:
                # Busca do início se não
                # encontrou
                cursor = document.find(
                    find_text, 0)
                if not cursor.isNull():
                    editor.setTextCursor(
                        cursor)
                    editor.setFocus()
                else:
                    QMessageBox.information(
                        self, "Buscar", "Texto não encontrado.")

    def show_replace_dialog(self):
        """Mostra diálogo de substituir aprimorado"""
        editor = self.get_current_editor()
        if not editor:
            return

        find_text, ok1 = QInputDialog.getText(
            self,
            "Substituir",
            "Texto para buscar:",
            text=editor.textCursor().selectedText()
        )

        if ok1 and find_text:
            replace_text, ok2 = QInputDialog.getText(
                self,
                "Substituir",
                "Substituir por:"
            )

            if ok2:
                text = editor.toPlainText()
                new_text = text.replace(
                    find_text, replace_text)
                editor.setPlainText(
                    new_text)

    def force_auto_complete_current(self):
        """Força auto-completar no editor atual"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'force_auto_complete'):
            editor.force_auto_complete()

    def fix_indentation_current(self):
        """Corrige indentação no editor atual"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'fix_indentation'):
            editor.fix_indentation()

    # ===== MÉTODOS DE PROJETO =====

    def create_project(self):
        """Cria um novo projeto com estrutura completa"""
        project_name, ok = QInputDialog.getText(
            self,
            "Novo Projeto",
            "Nome do projeto:",
            text="meu_projeto"
        )

        if not ok or not project_name:
            return

        project_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta para o Projeto",
            QDir.homePath()
        )

        if not project_path:
            return

        project_full_path = os.path.join(
            project_path, project_name)

        try:
            # Cria estrutura de diretórios
            dirs = [
                project_full_path,
                os.path.join(
                    project_full_path, "src"),
                os.path.join(
                    project_full_path, "tests"),
                os.path.join(
                    project_full_path, "docs"),
                os.path.join(
                    project_full_path, "data")
            ]

            for dir_path in dirs:
                os.makedirs(
                    dir_path, exist_ok=True)

            # Arquivo principal
            main_file = os.path.join(
                project_full_path, "main.py")
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(f'''"""
{project_name}
"""

def main():
                """Função principal do projeto."""
                print("Hello World!")

if __name__ == "__main__":
                main()
''')

            # README
            readme_file = os.path.join(
                project_full_path, "README.md")
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(
                    f"# {project_name}\n\nProjeto criado com Py Dragon Studio IDE\n")

            # requirements.txt
            requirements_file = os.path.join(
                project_full_path, "requirements.txt")
            with open(requirements_file, 'w', encoding='utf-8') as f:
                f.write(
                    "# Dependências do projeto\n")

            # .gitignore
            gitignore_file = os.path.join(
                project_full_path, ".gitignore")
            with open(gitignore_file, 'w', encoding='utf-8') as f:
                f.write("""# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtualenv
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""")

            self.set_project(project_full_path)
            self.open_file(main_file)

            QMessageBox.information(
                self, "Sucesso", f"Projeto '{project_name}' criado com sucesso!")

        except Exception as e:
            QMessageBox.warning(
                self, "Erro", f"Não foi possível criar o projeto:\n{str(e)}")

    def set_project(self, project_path=None):
        """Define o projeto atual com atualizações completas"""
        if not project_path:
            project_path = QFileDialog.getExistingDirectory(
                self,
                "Selecionar Projeto",
                self.project_path or QDir.homePath()
            )

        if project_path:
            self.project_path = project_path
            self.project_info_label.setText(
                f"📦 {os.path.basename(project_path)}")

            # Atualiza explorador
            self.refresh_explorer()

            # Ativa no terminal
            self.activate_project()

            # Preload de módulos em background
            threading.Thread(target=module_cache_manager.preload_all_project_modules,
                             args=(project_path,), daemon=True).start()

            self.statusBar().showMessage(
                f"✅ Projeto carregado: {project_path}", 3000)

    def configure_project(self):
        """Configura o projeto - placeholder para funcionalidade futura"""
        if not self.project_path:
            QMessageBox.information(
                self, "Informação", "Nenhum projeto aberto.")
            return

        QMessageBox.information(self, "Configurar Projeto",
                                f"Configurações do projeto: {os.path.basename(self.project_path)}\n\n"
                                "Esta funcionalidade está em desenvolvimento.")

    def create_venv(self):
        """Cria virtualenv para o projeto"""
        if not self.project_path:
            QMessageBox.information(
                self, "Informação", "Nenhum projeto aberto.")
            return

        venv_name = "venv"
        venv_path = os.path.join(self.project_path, venv_name)

        try:
            # Mostra progresso
            progress = ProgressDialog(
                self, "Criando Virtualenv", "Criando ambiente virtual...")
            progress.show()

            # Usa o Python atual para criar o venv
            result = subprocess.run([sys.executable, "-m", "venv", venv_path],
                                    capture_output=True, text=True)

            progress.close()

            if result.returncode == 0:
                self.venv_path = venv_path
                self.activate_project()
                QMessageBox.information(
                    self, "Sucesso", f"Virtualenv criado em: {venv_path}")
            else:
                QMessageBox.warning(
                    self, "Erro", f"Não foi criar o virtualenv:\n{result.stderr}")

        except Exception as e:
            QMessageBox.warning(
                self, "Erro", f"Não foi criar o virtualenv:\n{str(e)}")

    def install_dependencies(self):
        """Instala dependências do projeto"""
        if not self.project_path:
            return

        requirements_file = os.path.join(
            self.project_path, "requirements.txt")
        if not os.path.exists(requirements_file):
            # Cria arquivo requirements.txt vazio
            try:
                with open(requirements_file, 'w', encoding='utf-8') as f:
                    f.write(
                        "# Adicione suas dependências aqui\n")
            except:
                pass

        package, ok = QInputDialog.getText(
            self,
            "Instalar Pacote",
            "Nome do pacote (deixe vazio para instalar requirements.txt):"
        )

        if ok:
            try:
                python_exec = self.get_python_executable()

                if package:
                    cmd = [
                        python_exec, "-m", "pip", "install", package]
                else:
                    cmd = [
                        python_exec, "-m", "pip", "install", "-r", "requirements.txt"]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                self.output_tabs.setCurrentWidget(
                    self.output_text)
                self.output_text.clear()

                if package:
                    self.output_text.appendPlainText(
                        f"📦 Instalando {package}...\n")
                else:
                    self.output_text.appendPlainText(
                        "📦 Instalando dependências do requirements.txt...\n")

                self.output_text.appendPlainText(
                    "-" * 50 + "\n")

                if result.stdout:
                    self.output_text.appendPlainText(
                        result.stdout)
                if result.stderr:
                    self.output_text.appendPlainText(
                        result.stderr)

                if result.returncode == 0:
                    self.output_text.appendPlainText(
                        "\n✅ Instalação concluída com sucesso!")
                else:
                    self.output_text.appendPlainText(
                        f"\n❌ Falha na instalação (código: {result.returncode})")

            except Exception as e:
                self.output_text.appendPlainText(
                    f"💥 Erro: {str(e)}")

    def package_project(self):
        """Empacota o projeto"""
        if not self.project_path:
            QMessageBox.information(
                self, "Informação", "Nenhum projeto aberto.")
            return

        # Encontra arquivo principal
        main_files = [
            os.path.join(
                self.project_path, "main.py"),
            os.path.join(
                self.project_path, "app.py"),
            os.path.join(
                self.project_path, "src", "main.py"),
        ]

        main_file = None
        for file in main_files:
            if os.path.exists(file):
                main_file = os.path.basename(
                    file)
                break

        if not main_file:
            # Pede ao usuário para selecionar
            main_file, ok = QInputDialog.getText(
                self,
                "Empacotar Projeto",
                "Arquivo principal:",
                text="main.py"
            )
            if not ok or not main_file:
                return

        dialog = PackageDialog(
            self, self.project_path, main_file)
        dialog.exec()

    def deploy_project(self):
        """Implementa deploy automático do projeto"""
        if not self.project_path:
            QMessageBox.information(
                self, "Informação", "Nenhum projeto aberto.")
            return

        try:
            # Diálogo de configuração de deploy
            dialog = DeployDialog(
                self, self.project_path)
            if dialog.exec():
                deploy_config = dialog.get_deploy_config()

                self.output_tabs.setCurrentWidget(
                    self.output_text)
                self.output_text.clear()
                self.output_text.appendPlainText(
                    "🚀 Iniciando deploy...\n")
                self.output_text.appendPlainText(
                    "=" * 50 + "\n")

                # Executa deploy baseado
                # na configuração
                if deploy_config['type'] == 'zip':
                    self.deploy_as_zip(
                        deploy_config)
                elif deploy_config['type'] == 'git':
                    self.deploy_via_git(
                        deploy_config)
                elif deploy_config['type'] == 'ftp':
                    self.deploy_via_ftp(
                        deploy_config)
                else:
                    self.output_text.appendPlainText(
                        "❌ Tipo de deploy não suportado")

        except Exception as e:
            QMessageBox.warning(
                self, "Erro", f"Falha no deploy: {str(e)}")

    def deploy_via_ftp(self, config):
        """Deploy via FTP (implementação básica)"""
        self.output_text.appendPlainText(
            "⚠️ Deploy FTP em desenvolvimento...")
        # Implementação completa precisaria de biblioteca ftplib

    def deploy_via_git(self, config):
        """Deploy via Git"""
        try:
            # Verifica se é um repositório Git
            if not os.path.exists(
                    os.path.join(self.project_path, '.git')):
                self.output_text.appendPlainText(
                    "❌ Não é um repositório Git")
                return

            commands = [
                ["git", "add", "."],
                ["git",
                 "commit",
                 "-m",
                 config.get('commit_message',
                            'Deploy automático')],
                ["git", "push", config.get(
                    'remote', 'origin'), config.get('branch', 'main')]
            ]

            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                self.output_text.appendPlainText(
                    f"Comando: {' '.join(cmd)}")

                if result.stdout:
                    self.output_text.appendPlainText(
                        result.stdout)
                if result.stderr:
                    self.output_text.appendPlainText(
                        result.stderr)

                if result.returncode != 0:
                    self.output_text.appendPlainText(
                        f"❌ Falha no comando: {' '.join(cmd)}")
                    return

            self.output_text.appendPlainText(
                "✅ Deploy via Git concluído!")

        except Exception as e:
            self.output_text.appendPlainText(
                f"❌ Erro no deploy Git: {str(e)}")

    def deploy_as_zip(self, config):
        """Cria arquivo ZIP do projeto"""
        try:
            zip_path = os.path.join(
                config['output_dir'], f"{os.path.basename(self.project_path)}.zip")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(
                        self.project_path):
                    # Filtra
                    # arquivos
                    # e
                    # diretórios
                    if '__pycache__' in dirs:
                        dirs.remove(
                            '__pycache__')
                    if '.git' in dirs:
                        dirs.remove(
                            '.git')

                    for file in files:
                        if not file.endswith(
                                ('.pyc', '.tmp')):
                            file_path = os.path.join(
                                root, file)
                            arcname = os.path.relpath(
                                file_path, self.project_path)
                            zipf.write(
                                file_path, arcname)

            self.output_text.appendPlainText(
                f"✅ Projeto compactado: {zip_path}")
            self.output_text.appendPlainText(
                f"📦 Tamanho: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")

        except Exception as e:
            self.output_text.appendPlainText(
                f"❌ Erro ao criar ZIP: {str(e)}")

    # ===== MÉTODOS AUXILIARES =====

    def update_file_info(self, file_path):
        """Atualiza informações do arquivo na statusbar"""
        if file_path and os.path.exists(file_path):
            try:
                size = os.path.getsize(
                    file_path)
                size_str = f"{size} bytes" if size < 1024 else f"{size / 1024:.1f} KB"

                # Detecta encoding
                try:
                    with open(file_path, 'rb') as f:
                        raw = f.read()
                    encoding = "UTF-8"
                except:
                    encoding = "Desconhecido"

                file_name = os.path.basename(
                    file_path)
                self.file_info_label.setText(
                    f"📄 {file_name} ({size_str}, {encoding})")

                # Atualiza informações
                # do cursor
                editor = self.get_current_editor()
                if editor:
                    cursor = editor.textCursor()
                    line = cursor.blockNumber() + 1
                    column = cursor.columnNumber() + 1
                    self.cursor_info_label.setText(
                        f"Linha: {line}, Coluna: {column}")

            except Exception as e:
                self.file_info_label.setText(
                    "📄 Informações indisponíveis")
        else:
            self.file_info_label.setText(
                "📄 Sem arquivo")
            self.cursor_info_label.setText(
                "Linha: 1, Coluna: 1")

    def refresh_explorer(self):
        """Atualiza o explorador de arquivos"""
        if self.project_path and self.file_model:
            self.file_model.setRootPath(
                self.project_path)
            self.file_tree.setRootIndex(
                self.file_model.index(self.project_path))
        elif self.file_model:
            self.file_model.setRootPath(
                QDir.homePath())
            self.file_tree.setRootIndex(
                self.file_model.index(QDir.homePath()))

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
            menu.addAction(
                "📄 Abrir", lambda: self.open_file(file_path))
            menu.addAction(
                "📋 Copiar Caminho", lambda: self.copy_file_path(file_path))
            menu.addSeparator()
            menu.addAction(
                "🗑️ Excluir", lambda: self.delete_file(file_path))
        else:
            menu.addAction(
                "📂 Abrir Pasta", lambda: self.set_project(file_path))
            menu.addAction(
                "📄 Novo Arquivo", lambda: self.create_new_file_in_explorer(file_path))
            menu.addAction(
                "📁 Nova Pasta", lambda: self.create_new_folder_in_explorer(file_path))
            menu.addSeparator()
            menu.addAction(
                "🗑️ Excluir", lambda: self.delete_folder(file_path))

        menu.exec(
            self.file_tree.viewport().mapToGlobal(position))

    def create_new_file_in_explorer(self, parent_path=None):
        """Cria novo arquivo no explorador"""
        if not parent_path:
            current_index = self.file_tree.currentIndex()
            if current_index.isValid():
                parent_path = self.file_model.filePath(
                    current_index)
                if not os.path.isdir(
                        parent_path):
                    parent_path = os.path.dirname(
                        parent_path)
            else:
                parent_path = self.project_path or QDir.homePath()

        dialog = NewFileDialog(self)
        if dialog.exec():
            file_name = dialog.get_file_name()
            if file_name:
                file_path = os.path.join(
                    parent_path, file_name)
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(
                            '# Novo arquivo\n')
                    self.refresh_explorer()
                    self.open_file(
                        file_path)
                except Exception as e:
                    QMessageBox.warning(
                        self, "Erro", f"Não foi possível criar o arquivo:\n{str(e)}")

    def create_new_folder_in_explorer(self, parent_path=None):
        """Cria nova pasta no explorador"""
        if not parent_path:
            current_index = self.file_tree.currentIndex()
            if current_index.isValid():
                parent_path = self.file_model.filePath(
                    current_index)
                if not os.path.isdir(
                        parent_path):
                    parent_path = os.path.dirname(
                        parent_path)
            else:
                parent_path = self.project_path or QDir.homePath()

        folder_name, ok = QInputDialog.getText(
            self,
            "Nova Pasta",
            "Nome da pasta:",
            text="nova_pasta"
        )

        if ok and folder_name:
            new_folder_path = os.path.join(
                parent_path, folder_name)
            try:
                os.makedirs(
                    new_folder_path, exist_ok=True)
                self.refresh_explorer()
            except Exception as e:
                QMessageBox.warning(
                    self, "Erro", f"Não foi possível criar a pasta:\n{str(e)}")

    def copy_file_path(self, file_path):
        """Copia caminho do arquivo para área de transferência"""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(file_path)
        self.statusBar().showMessage("✅ Caminho copiado para área de transferência", 2000)

    def delete_file(self, file_path):
        """Exclui arquivo com confirmação"""
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir '{os.path.basename(file_path)}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                self.refresh_explorer()
                self.statusBar().showMessage(
                    f"✅ Arquivo excluído: {os.path.basename(file_path)}", 3000)
            except Exception as e:
                QMessageBox.warning(
                    self, "Erro", f"Não foi possível excluir o arquivo:\n{str(e)}")

    def delete_folder(self, folder_path):
        """Exclui pasta com confirmação"""
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a pasta '{os.path.basename(folder_path)}' e todo seu conteúdo?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                shutil.rmtree(
                    folder_path)
                self.refresh_explorer()
                self.statusBar().showMessage(
                    f"✅ Pasta excluída: {os.path.basename(folder_path)}", 3000)
            except Exception as e:
                QMessageBox.warning(
                    self, "Erro", f"Não foi possível excluir a pasta:\n{str(e)}")

    def jump_to_error(self, item):
        """Salta para a linha do erro na lista de problemas"""
        data = item.data(Qt.UserRole)
        if data:
            file_path = data.get('file')
            line_str = data.get('line', '0')

            try:
                # Converte para índice
                # 0-based
                line_num = int(
                    line_str) - 1

                # Encontra a aba do
                # arquivo
                for i in range(
                        self.tab_widget.count()):
                    widget = self.tab_widget.widget(
                        i)
                    if isinstance(
                            widget, EditorTab) and widget.file_path == file_path:
                        self.tab_widget.setCurrentIndex(
                            i)

                        # Move
                        # cursor
                        # para
                        # a
                        # linha
                        editor = widget.editor
                        cursor = editor.textCursor()
                        document = editor.document()

                        block = document.findBlockByLineNumber(
                            line_num)
                        if block.isValid():
                            cursor.setPosition(
                                block.position())
                            editor.setTextCursor(
                                cursor)
                            editor.setFocus()
                            editor.centerCursor()
                        break

            except ValueError:
                QMessageBox.warning(
                    self, "Erro", f"Número de linha inválido: {line_str}")

    def clear_problems(self):
        """Limpa a lista de problemas"""
        self.problems_list.clear()

    def run_linter(self):
        """Executa o linter no arquivo atual"""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(
                current_widget,
                EditorTab) and current_widget.file_path and current_widget.file_path.endswith('.py'):
            # Força o linting
            current_widget.start_linting()
        else:
            QMessageBox.information(
                self, "Informação", "Apenas arquivos Python podem ser analisados.")

    # ===== MÉTODOS DE TERMINAL =====

    def start_shell(self):
        """Inicia o processo do shell de forma segura"""
        try:
            # Limpa processo anterior
            if hasattr(self, 'shell_process') and self.shell_process:
                if self.shell_process.state() == QProcess.Running:
                    self.shell_process.terminate()
                    if not self.shell_process.waitForFinished(1000):
                        self.shell_process.kill()
                self.shell_process = None

            self.shell_process = QProcess(self)
            self.shell_process.readyReadStandardOutput.connect(self.handle_terminal_output)
            self.shell_process.readyReadStandardError.connect(self.handle_terminal_error)

            # Configura o working directory
            if self.project_path:
                self.shell_process.setWorkingDirectory(self.project_path)

            if os.name == 'nt':
                self.shell_process.start("cmd.exe")
            else:
                self.shell_process.start("/bin/bash", ["-i"])

            # Espera o processo iniciar
            if not self.shell_process.waitForStarted(5000):
                print("❌ Não foi possível iniciar o shell")
                return

            # Configura o terminal
            if hasattr(self, 'terminal_text') and self.terminal_text:
                # Limpa o terminal
                self.terminal_text.clear()
                self.terminal_text.setPlainText(">>> ")
                self.terminal_text.input_start = 4

                # Configura referência segura
                if hasattr(self.terminal_text, 'set_shell_process'):
                    self.terminal_text.set_shell_process(self.shell_process)

            print("✅ Terminal iniciado com sucesso")

            # Ativa o projeto após um delay curto para o shell inicializar
            if self.project_path:
                QTimer.singleShot(500, self.activate_project)

        except Exception as e:
            print(f"❌ Erro ao iniciar terminal: {str(e)}")

    def activate_project(self):
        """Ativa o projeto no terminal"""
        try:
            if (not hasattr(self, 'shell_process') or not self.shell_process
                    or self.shell_process.state() != QProcess.Running):
                print("ℹ️ Shell não está rodando, pulando ativação de projeto")
                return

            if self.project_path:
                if os.name == 'nt':
                    cd_command = f'cd /d "{self.project_path}" && '
                else:
                    cd_command = f'cd "{self.project_path}" && '

                self.shell_process.write(cd_command.encode('utf-8'))

                # Ativa virtualenv se existir
                if hasattr(self, 'venv_path') and self.venv_path and os.path.exists(self.venv_path):
                    if os.name == 'nt':
                        activate_cmd = f'call "{os.path.join(self.venv_path, "Scripts", "activate.bat")}"\n'
                    else:
                        activate_cmd = f'source "{os.path.join(self.venv_path, "bin", "activate")}"\n'

                    self.shell_process.write(activate_cmd.encode('utf-8'))

                print("✅ Projeto ativado no terminal")
            else:
                print("ℹ️ Nenhum projeto aberto para ativar")

        except Exception as e:
            print(f"❌ Erro ao ativar projeto no terminal: {str(e)}")

    def handle_terminal_output(self):
        """Processa saída do terminal com tratamento robusto"""
        try:
            if (not hasattr(self, 'shell_process') or not self.shell_process or
                    not hasattr(self, 'terminal_text') or not self.terminal_text):
                return

            data = self.shell_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if not data:
                return

            # Adiciona output sem bagunçar o prompt/input atual
            current_text = self.terminal_text.toPlainText()
            input_pos = getattr(self.terminal_text, 'input_start', 0)
            if len(current_text) > input_pos:
                # Insere no final do input atual
                new_text = current_text[:input_pos] + data
                self.terminal_text.setPlainText(new_text)
            else:
                self.terminal_text.appendPlainText(data)

            # Move cursor para o final do input
            cursor = self.terminal_text.textCursor()
            cursor.setPosition(len(self.terminal_text.toPlainText()))
            self.terminal_text.setTextCursor(cursor)
            self.terminal_text.ensureCursorVisible()

        except Exception as e:
            print(f"❌ Erro em handle_terminal_output: {e}")

    def handle_terminal_error(self):
        """Processa erro do terminal"""
        try:
            if (not hasattr(self, 'shell_process') or not self.shell_process or
                    not hasattr(self, 'terminal_text') or not self.terminal_text):
                return

            data = self.shell_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if data:
                # Marca erro em vermelho (simples append com prefixo)
                error_text = f"\n[ERRO] {data}"
                current_text = self.terminal_text.toPlainText()
                input_pos = getattr(self.terminal_text, 'input_start', 0)
                if len(current_text) > input_pos:
                    new_text = current_text[:input_pos] + error_text
                    self.terminal_text.setPlainText(new_text)
                else:
                    self.terminal_text.appendPlainText(error_text)

        except Exception as e:
            print(f"❌ Erro em handle_terminal_error: {e}")

    def activate_project(self):

        """Ativa dir do projeto e venv se for Python"""
        try:
            if not hasattr(self,
                           'shell_process') or not self.shell_process or self.shell_process.state() != QProcess.Running:
                print("ℹ️ Shell não rodando")
                return

            import os, platform
            system = platform.system()
            if not hasattr(self, 'project_path') or not self.project_path:
                print("ℹ️ Nenhum projeto aberto")
                return

            # Verifica se é projeto Python (tem .py no dir raiz)
            is_python_project = any(f.endswith('.py') for f in os.listdir(self.project_path))
            if not is_python_project:
                print("ℹ️ Não é projeto Python, pulando venv")
                # Só CD
                cd_cmd = f'cd /d "{self.project_path}"' if system == "Windows" else f'cd "{self.project_path}"'
                self.shell_process.write((cd_cmd + "\n").encode('utf-8'))
                return

            # CD primeiro
            cd_cmd = f'cd /d "{self.project_path}" & echo 📁 Projeto Python ativado: {self.project_path}' if system == "Windows" else f'cd "{self.project_path}" && echo "📁 Projeto Python ativado: {self.project_path}"'
            self.shell_process.write(cd_cmd.encode('utf-8'))

            # Detecta e ativa venv (pastas comuns)
            venv_paths = ['venv', '.venv', 'env', 'virtualenv']  # Adicionei 'virtualenv' opcional
            venv_found = None
            for v in venv_paths:
                vpath = os.path.join(self.project_path, v)
                if os.path.isdir(vpath):
                    venv_found = vpath
                    break

            if venv_found:
                v_name = os.path.basename(venv_found)  # Nome da pasta
                if system == "Windows":
                    activate_cmd = f'& call "{os.path.join(venv_found, "Scripts", "activate.bat")}" & echo 🐍 Venv ativado: {v_name} & echo %VIRTUAL_ENV%'
                else:
                    activate_cmd = f'&& source "{os.path.join(venv_found, "bin", "activate")}" && echo "🐍 Venv ativado: {v_name}" && echo $VIRTUAL_ENV'
                self.shell_process.write((activate_cmd + "\n").encode('utf-8'))
                print(f"✅ Venv ativado: {venv_found}")
            else:
                # CORREÇÃO: Use string normal + encode('utf-8') para Unicode
                no_venv_msg = 'echo ⚠️ Nenhum venv encontrado – use "python -m venv venv"\n'
                self.shell_process.write(no_venv_msg.encode('utf-8'))
                print("ℹ️ Sem venv no projeto")

        except Exception as e:
            print(f"❌ Erro ativar projeto: {e}")

    def get_python_executable(self):

        """Obtém o executável Python"""
    
        if self.venv_path and os.path.exists(self.venv_path):
            if os.name == 'nt':
                return os.path.join(
                    self.venv_path, "Scripts", "python.exe")
            else:
                return os.path.join(
                    self.venv_path, "bin", "python")
        return sys.executable

    def check_python_version(self):
        """Verifica e exibe a versão do Python"""
        try:
            result = subprocess.run([self.get_python_executable(), "--version"],
                                    capture_output=True, text=True)
            version = result.stdout.strip()
            self.statusBar().showMessage(
                f"🐍 {version}", 5000)
        except:
            self.statusBar().showMessage("❌ Não foi possível detectar Python", 5000)

    # ===== MÉTODOS DE VISUALIZAÇÃO =====

    def split_view(self):
        """Divide a visualização em horizontal"""
        if isinstance(self.centralWidget(), QSplitter):
            return

        splitter = QSplitter(Qt.Horizontal)

        # Cria novo tab widget para a direita
        right_tab_widget = QTabWidget()
        right_tab_widget.setTabsClosable(True)
        right_tab_widget.setMovable(True)

        # Move a aba atual para a direita (opcional)
        # current_index = self.tab_widget.currentIndex()
        # if current_index >= 0:
        #     widget = self.tab_widget.widget(current_index)
        #     self.tab_widget.removeTab(current_index)
        # right_tab_widget.addTab(widget,
        # self.tab_widget.tabText(current_index))

        splitter.addWidget(self.tab_widget)
        splitter.addWidget(right_tab_widget)

        splitter.setSizes([700, 300])
        self.setCentralWidget(splitter)

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
                dock.setVisible(
                    not dock.isVisible())
                break

    def toggle_terminal(self):
        """Mostra/esconde o dock do terminal e inicia shell se preciso"""
        # Encontra o dock "Output"
        dock_found = False
        for dock in self.findChildren(QDockWidget):
            if dock.windowTitle() == "Output":
                dock.setVisible(not dock.isVisible())
                dock_found = True
                # Se mostrou e shell não rodando, inicia
                if dock.isVisible() and not hasattr(self,
                                                    'terminal_process_started') or not self.terminal_process_started:
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(300, self.start_shell)  # Delay para UI
                break
        if not dock_found:
            print("⚠️ Dock 'Output' não encontrado – verifique setup")
            # Fallback: mostra o dock se existir
            if hasattr(self, 'terminal_dock'):
                self.terminal_dock.setVisible(not self.terminal_dock.isVisible())

    def toggle_minimap(self):
        """Alterna visibilidade do minimap"""
        for dock in self.findChildren(QDockWidget):
            if dock.windowTitle() == "Minimap":
                dock.setVisible(
                    not dock.isVisible())
                break

    def show_font_dialog(self):
        """Mostra diálogo para selecionar fonte"""
        font, ok = QFontDialog.getFont()
        if ok:
            self.current_font = font.family()
            # Aplica a fonte a todos os editores
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(
                    i)
                if isinstance(
                        widget, EditorTab):
                    widget.editor.setFont(
                        font)

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
        QMessageBox.information(self, "Gerenciar Pacotes",
                                "Esta funcionalidade está em desenvolvimento.\n\n"
                                "Use o terminal para gerenciar pacotes:\n"
                                "• pip install <pacote>\n"
                                "• pip uninstall <pacote>\n"
                                "• pip list")

    def select_python_version(self):
        """Seleciona versão do Python"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Executável Python",
            "/usr/bin" if os.name != 'nt' else "C:\\",
            "Executável Python (python python.exe)"
        )

        if file_path:
            # Verifica se é um Python válido
            try:
                result = subprocess.run([file_path, "--version"],
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    self.python_path = file_path
                    self.venv_path = None  # Reseta virtualenv
                    self.statusBar().showMessage(
                        f"🐍 Python definido: {result.stdout.strip()}", 3000)
                else:
                    QMessageBox.warning(
                        self, "Erro", "Executável Python inválido.")
            except Exception as e:
                QMessageBox.warning(
                    self, "Erro", f"Erro ao verificar Python: {str(e)}")

    def format_code(self):
        """Formata o código atual"""
        editor = self.get_current_editor()
        if not editor or not hasattr(
                editor, 'file_path') or not editor.file_path.endswith('.py'):
            QMessageBox.information(
                self, "Informação", "Apenas arquivos Python podem ser formatados.")
            return

        try:
            # Usa autopep8 para formatação
            python_exec = self.get_python_executable()
            result = subprocess.run(
                [python_exec, "-m", "autopep8",
                 "-", "--aggressive"],
                input=editor.toPlainText().encode('utf-8'),
                capture_output=True,
                text=False
            )

            if result.returncode == 0:
                formatted_code = result.stdout.decode(
                    'utf-8')
                editor.setPlainText(
                    formatted_code)
                self.statusBar().showMessage("✅ Código formatado com sucesso!", 3000)
            else:
                QMessageBox.warning(
                    self, "Erro", "Falha ao formatar código. Instale autopep8: pip install autopep8")

        except Exception as e:
            QMessageBox.warning(
                self, "Erro", f"Erro ao formatar código: {str(e)}")

    def show_settings(self):
        """Mostra configurações"""
        QMessageBox.information(self, "Configurações",
                                "Painel de configurações em desenvolvimento.\n\n"
                                "Configurações atuais:\n"
                                f"• Python: {self.get_python_executable()}\n"
                                f"• Projeto: {self.project_path or 'Nenhum'}\n"
                                f"• Virtualenv: {self.venv_path or 'Nenhum'}")

    # ===== MÉTODOS DE AJUDA =====

    def show_documentation(self):
        """Mostra documentação"""
        QMessageBox.information(self, "Documentação",
                                "Py Dragon Studio IDE\n\n"
                                "📖 **Atalhos Principais:**\n"
                                "• Ctrl+N - Novo arquivo\n"
                                "• Ctrl+O - Abrir arquivo\n"
                                "• Ctrl+S - Salvar\n"
                                "• Ctrl+Shift+S - Salvar como\n"
                                "• Ctrl+Space - Auto-completar\n"
                                "• F5 - Executar código\n"
                                "• F6 - Debug\n"
                                "• Ctrl+F - Buscar\n"
                                "• Ctrl+H - Substituir\n\n"
                                "🚀 **Funcionalidades:**\n"
                                "• Syntax highlighting multi-linguagem\n"
                                "• Auto-complete inteligente\n"
                                "• Terminal integrado\n"
                                "• Debug integrado\n"
                                "• Gerenciamento de projetos\n"
                                "• Virtualenv integrado")

    def report_bug(self):
        """Reporta bug"""
        QMessageBox.information(self, "Reportar Bug",
                                "🐛 **Encontrou um bug?**\n\n"
                                "Por favor, reporte em:\n"
                                "https://github.com/seu-usuario/py-dragon-studio/issues\n\n"
                                "Inclua:\n"
                                "• Descrição do problema\n"
                                "• Passos para reproduzir\n"
                                "• Screenshots (se aplicável)\n"
                                "• Sua configuração (SO, Python)")

    def suggest_feature(self):
        """Sugere nova funcionalidade"""
        QMessageBox.information(self, "Sugerir Funcionalidade",
                                "💡 **Tem uma ideia para melhorar o IDE?**\n\n"
                                "Envie sua sugestão em:\n"
                                "https://github.com/seu-usuario/py-dragon-studio/issues\n\n"
                                "Adoramos ouvir suas ideias!")

    # No método show_about, substitua:
    def show_about(self):
        """Mostra informações sobre o aplicativo"""
        QMessageBox.about(self, "Sobre Py Dragon Studio IDE",
                          f"<h2>Py Dragon Studio IDE</h2>"
                          f"<p><b>Versão:</b> 1.0.0</p>"
                          f"<p><b>Python:</b> {sys.version}</p>"
                          f"<p><b>Plataforma:</b> {platform.system()} {platform.release()}</p>"
                          f"<p><b>Arquitetura:</b> {platform.architecture()[0]}</p>"
                          f"<hr>"
                          f"<p>Um IDE Python moderno com foco em produtividade e experiência do desenvolvedor.</p>"
                          f"<p>Desenvolvido com PySide6</p>")  # Removido o ❤️

    # ===== MÉTODOS DE NAVEGAÇÃO =====

    def get_current_editor(self):
        """Obtém o editor atual de forma mais robusta"""
        try:
            current_widget = self.tab_widget.currentWidget()
            if isinstance(
                    current_widget, EditorTab):
                return current_widget.editor
            elif hasattr(current_widget, 'editor'):
                return current_widget.editor
            return None
        except Exception as e:
            print(
                f"Erro em get_current_editor: {e}")
            return None

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
            "Novo Arquivo", "Abrir Arquivo", "Salvar", "Salvar Tudo",
            "Executar", "Debug", "Buscar", "Substituir",
            "Terminal", "Explorer", "Problemas", "Minimap"
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
            elif command == "Salvar Tudo":
                self.save_all_files()
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
            elif command == "Problemas":
                # Foca na lista de
                # problemas
                for dock in self.findChildren(
                        QDockWidget):
                    if dock.windowTitle() == "Explorer":
                        left_tabs = dock.widget()
                        if isinstance(
                                left_tabs, QTabWidget):
                            left_tabs.setCurrentIndex(
                                1)  # Problems tab
                        break
            elif command == "Minimap":
                self.toggle_minimap()

    def pause_execution(self):
        """Pausa a execução atual"""
        try:
            # Para processos em execução
            if hasattr(
                    self, 'current_process') and self.current_process:
                if self.current_process.state() == QProcess.Running:
                    self.current_process.kill()
                    self.output_text.appendPlainText(
                        "⏸️ Execução pausada")
                else:
                    self.output_text.appendPlainText(
                        "ℹ️ Nenhum processo em execução")
            else:
                self.output_text.appendPlainText(
                    "ℹ️ Nenhum processo para pausar")

        except Exception as e:
            self.output_text.appendPlainText(
                f"❌ Erro ao pausar execução: {str(e)}")

    def stop_execution(self):
        """Para completamente a execução"""
        try:
            # Para todos os processos relacionados
            processes = [
                getattr(
                    self, 'current_process', None),
                getattr(
                    self, 'shell_process', None),
                getattr(
                    self, 'debug_process', None)
            ]

            stopped = False
            for proc in processes:
                if proc and proc.state() == QProcess.Running:
                    proc.terminate()
                    if not proc.waitForFinished(
                            1000):
                        proc.kill()
                    stopped = True

            if stopped:
                self.output_text.appendPlainText(
                    "⏹️ Todas as execuções paradas")
            else:
                self.output_text.appendPlainText(
                    "ℹ️ Nenhuma execução em andamento")

        except Exception as e:
            self.output_text.appendPlainText(
                f"❌ Erro ao parar execução: {str(e)}")

    def run_tests(self):
        """Executa testes do projeto de forma robusta"""
        if not self.project_path:
            QMessageBox.information(
                self, "Informação", "Nenhum projeto aberto.")
            return

        try:
            self.output_tabs.setCurrentWidget(
                self.output_text)
            self.output_text.clear()
            self.output_text.appendPlainText(
                "🧪 Executando testes...\n")
            self.output_text.appendPlainText(
                "=" * 50 + "\n")

            python_exec = self.get_python_executable()

            # Tenta diferentes frameworks de teste
            test_commands = [
                [python_exec, "-m",
                 "pytest", "-v"],
                [python_exec, "-m", "unittest",
                 "discover", "-v"],
                [python_exec, "-m",
                 "doctest", "**/*.py"]
            ]

            success = False
            for cmd in test_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=self.project_path,
                        timeout=30
                    )

                    self.output_text.appendPlainText(
                        f"Comando: {' '.join(cmd)}\n")

                    if result.stdout:
                        self.output_text.appendPlainText(
                            result.stdout)
                    if result.stderr and "Error" in result.stderr:
                        self.output_text.appendPlainText(
                            f"Erros:\n{result.stderr}")

                    if result.returncode == 0:
                        self.output_text.appendPlainText(
                            f"\n✅ Testes executados com sucesso usando {cmd[2]}!")
                        success = True
                        break
                    else:
                        self.output_text.appendPlainText(
                            f"\n❌ {cmd[2]} falhou, tentando próximo...\n")
                        self.output_text.appendPlainText(
                            "-" * 30 + "\n")

                except subprocess.TimeoutExpired:
                    self.output_text.appendPlainText(
                        f"⏰ Timeout no comando: {' '.join(cmd)}\n")
                except Exception as e:
                    self.output_text.appendPlainText(
                        f"⚠️ Erro com {cmd[2]}: {str(e)}\n")

            if not success:
                self.output_text.appendPlainText(
                    "\n❌ Não foi possível executar testes com nenhum framework conhecido.")
                self.output_text.appendPlainText(
                    "Frameworks suportados: pytest, unittest, doctest")

        except Exception as e:
            self.output_text.appendPlainText(
                f"💥 Erro inesperado: {str(e)}")

    def run_coverage(self):
        """Executa análise de cobertura de código completa"""
        if not self.project_path:
            QMessageBox.information(
                self, "Informação", "Nenhum projeto aberto.")
            return

        try:
            python_exec = self.get_python_executable()

            # Verifica se coverage está instalado
            try:
                subprocess.run([python_exec, "-m", "coverage", "--version"],
                               capture_output=True, check=True)
            except:
                reply = QMessageBox.question(
                    self,
                    "Coverage não instalado",
                    "O pacote 'coverage' não está instalado. Deseja instalar agora?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    self.install_package(
                        "coverage")
                else:
                    return

            self.output_tabs.setCurrentWidget(
                self.output_text)
            self.output_text.clear()
            self.output_text.appendPlainText(
                "📊 Executando análise de cobertura...\n")
            self.output_text.appendPlainText(
                "=" * 50 + "\n")

            # Executa cobertura com pytest
            result = subprocess.run(
                [python_exec, "-m", "coverage",
                 "run", "-m", "pytest"],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=60
            )

            if result.stdout:
                self.output_text.appendPlainText(
                    "Saída dos testes:\n")
                self.output_text.appendPlainText(
                    result.stdout)

            if result.stderr:
                self.output_text.appendPlainText(
                    "Erros:\n")
                self.output_text.appendPlainText(
                    result.stderr)

            # Gera relatório
            if result.returncode in [
                0, 1]:  # 0 = sucesso, 1 = testes falharam mas cobertura funciona
                # Relatório no terminal
                report_result = subprocess.run(
                    [python_exec, "-m",
                     "coverage", "report"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                self.output_text.appendPlainText(
                    "\n" + "=" * 50 + "\n")
                self.output_text.appendPlainText(
                    "RELATÓRIO DE COBERTURA:\n")
                self.output_text.appendPlainText(
                    "=" * 50 + "\n")

                if report_result.stdout:
                    self.output_text.appendPlainText(
                        report_result.stdout)

                # Relatório HTML
                html_result = subprocess.run(
                    [python_exec, "-m",
                     "coverage", "html"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                if html_result.returncode == 0:
                    html_path = os.path.join(
                        self.project_path, 'htmlcov', 'index.html')
                    self.output_text.appendPlainText(
                        f"\n📁 Relatório HTML: {html_path}")

                    # Botão
                    # para
                    # abrir
                    # relatório
                    open_report_btn = QPushButton(
                        "Abrir Relatório HTML")
                    open_report_btn.clicked.connect(
                        lambda: self.open_html_report(html_path))

                    # Adiciona
                    # botão
                    # ao
                    # output
                    # (precisa
                    # de
                    # layout
                    # especial)
                    self.output_text.appendPlainText(
                        "\n[Clique aqui para abrir o relatório HTML]")

                # Relatório XML (para
                # CI/CD)
                xml_result = subprocess.run(
                    [python_exec, "-m",
                     "coverage", "xml"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                if xml_result.returncode == 0:
                    self.output_text.appendPlainText(
                        "📊 Relatório XML gerado: coverage.xml")

            else:
                self.output_text.appendPlainText(
                    "❌ Falha na execução da cobertura")

        except subprocess.TimeoutExpired:
            self.output_text.appendPlainText(
                "⏰ Timeout na análise de cobertura")
        except Exception as e:
            self.output_text.appendPlainText(
                f"💥 Erro na cobertura: {str(e)}")

    def install_package(self, package_name):
        """Instala um pacote Python"""
        try:
            python_exec = self.get_python_executable()

            self.output_tabs.setCurrentWidget(
                self.output_text)
            self.output_text.appendPlainText(
                f"📦 Instalando {package_name}...\n")

            result = subprocess.run(
                [python_exec, "-m", "pip",
                 "install", package_name],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stdout:
                self.output_text.appendPlainText(
                    result.stdout)
            if result.stderr:
                self.output_text.appendPlainText(
                    result.stderr)

            if result.returncode == 0:
                self.output_text.appendPlainText(
                    f"\n✅ {package_name} instalado com sucesso!")
            else:
                self.output_text.appendPlainText(
                    f"\n❌ Falha na instalação de {package_name}")

        except Exception as e:
            self.output_text.appendPlainText(
                f"💥 Erro na instalação: {str(e)}")

    def open_html_report(self, html_path):
        """Abre relatório HTML no navegador padrão"""
        try:
            import webbrowser
            webbrowser.open(f"file://{html_path}")
        except Exception as e:
            QMessageBox.warning(
                self, "Erro", f"Não foi possível abrir o relatório: {str(e)}")

    def closeEvent(self, event):
        """Lida com o fechamento da aplicação"""
        # Para todos os processos
        self.stop_execution()

        # Finaliza plugins
        if hasattr(self, 'plugin_manager'):
            self.plugin_manager.shutdown_plugins()

        # Para workers em execução
        if hasattr(
                self, 'linter_worker') and self.linter_worker:
            self.linter_worker.stop()
        if hasattr(
                self, 'auto_complete_worker') and self.auto_complete_worker:
            self.auto_complete_worker.stop()
        if hasattr(self, 'debug_worker') and self.debug_worker:
            self.debug_worker.stop()

        event.accept()

    def start_shell(self):
        """Inicia o processo do shell de forma segura, adaptado por OS"""
        try:
            # Limpa processo anterior (se existir)
            if hasattr(self, 'shell_process') and self.shell_process:
                self.stop_process(self.shell_process)

            self.shell_process = QProcess(self)
            self.shell_process.readyReadStandardOutput.connect(self.handle_terminal_output)
            self.shell_process.readyReadStandardError.connect(self.handle_terminal_error)
            self.shell_process.finished.connect(lambda: print("ℹ️ Shell finalizado"))

            # Configura working directory do projeto
            if self.project_path:
                self.shell_process.setWorkingDirectory(self.project_path)
                print(f"📁 Working dir: {self.project_path}")

            # Comando por OS (intuitivo: detecta automático)
            system = platform.system()
            if system == "Windows":
                self.shell_process.start("cmd.exe", ["/K", "echo Bem-vindo ao Py Dragon Terminal!"])
                prompt = "C:\\> "
            elif system == "Darwin":  # macOS
                self.shell_process.start("/bin/zsh")  # Ou mude para "/bin/bash" se preferir
                prompt = "% "
            else:  # Linux
                self.shell_process.start("/bin/bash", ["-i"])
                prompt = "$ "

            # Espera iniciar (timeout 5s)
            if not self.shell_process.waitForStarted(5000):
                print("❌ Shell não iniciou!")
                if hasattr(self, 'terminal_text'):
                    self.terminal_text.appendPlainText("❌ Erro: Verifique permissões do shell.")
                return

            self.terminal_process_started = True
            print(f"✅ Terminal rodando em {system}! Prompt: {prompt}")

            # Configura o texto do terminal (prompt inicial)
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.clear()
                self.terminal_text.setPlainText(prompt)
                self.terminal_text.input_start = len(prompt)  # <- Marca onde digitar começa
                cursor = self.terminal_text.textCursor()
                cursor.setPosition(len(prompt))  # Cursor no final
                self.terminal_text.setTextCursor(cursor)
                self.terminal_text.ensureCursorVisible()

            # Ativa projeto após delay (para shell estabilizar)
            if self.project_path:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(1000, self.activate_project)

        except Exception as e:
            print(f"❌ Erro no terminal ({platform.system()}): {str(e)}")
            if hasattr(self, 'terminal_text'):
                self.terminal_text.appendPlainText(f"❌ Erro: {str(e)}")

    def stop_process(self, process):

        """Para um processo de forma segura"""

        if process and process.state() == QProcess.Running:
            process.terminate()
            if not process.waitForFinished(1000):
                process.kill()
                process.waitForFinished(1000)

    def terminal_key_press(self, event):
        """Captura teclas no terminal: Enter envia comando, Backspace protege prompt"""
        if not hasattr(self,
                       'shell_process') or not self.shell_process or self.shell_process.state() != QProcess.Running:
            event.ignore()  # Ignora se shell parado
            return

        cursor = self.terminal_text.textCursor()
        pos = cursor.position()
        if pos < self.terminal_text.input_start:
            event.ignore()  # Não edita histórico
            return

        from PySide6.QtCore import Qt
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Envia comando ao shell
            command = self.terminal_text.toPlainText()[self.terminal_text.input_start:].strip()
            if command:  # Só se não vazio
                self.shell_process.write((command + "\n").encode('utf-8'))
                print(f"📤 Enviado: {command}")  # Log no console
                # Nova linha para output
                self.terminal_text.appendPlainText("")
                self.terminal_text.input_start = self.terminal_text.textCursor().position()
                # Adiciona novo prompt
                prompt = self.get_prompt()
                self.terminal_text.insertPlainText(prompt)
                self.terminal_text.input_start += len(prompt)
            event.accept()
        elif event.key() == Qt.Key_Backspace and pos == self.terminal_text.input_start:
            event.ignore()  # Protege prompt
        else:
            event.accept()  # Permite digitar

    def get_prompt(self):
        """Prompt simples por OS"""
        import platform
        system = platform.system()
        if system == "Windows":
            return "C:\\> "
        elif system == "Darwin":
            return "% "
        else:
            return "$ "


def handle_terminal_output(self):
    """Processa saída do terminal com tratamento robusto"""
    try:
        if (not hasattr(self, 'shell_process') or not self.shell_process or
                not hasattr(self, 'terminal_text') or not self.terminal_text):
            return

        data = self.shell_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        if not data:
            return

        # Usa appendPlainText como fallback seguro
        current_text = self.terminal_text.toPlainText()

        # Remove o prompt temporariamente se existir
        if current_text.endswith(">>> "):
            new_text = current_text[:-4] + data
            self.terminal_text.setPlainText(new_text + ">>> ")
        else:
            self.terminal_text.appendPlainText(data)

        # Move cursor para o final
        cursor = self.terminal_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.terminal_text.setTextCursor(cursor)
        self.terminal_text.ensureCursorVisible()

    except Exception as e:
        print(f"❌ Erro em handle_terminal_output: {e}")


def handle_terminal_error(self):
    """Processa erro do terminal"""
    try:
        if (not hasattr(self, 'shell_process') or not self.shell_process or
                not hasattr(self, 'terminal_text') or not self.terminal_text):
            return

        data = self.shell_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        if data:
            # Adiciona marcação de erro
            error_text = f"[ERRO] {data}"
            current_text = self.terminal_text.toPlainText()

            if current_text.endswith(">>> "):
                self.terminal_text.setPlainText(current_text[:-4] + error_text + ">>> ")
            else:
                self.terminal_text.appendPlainText(error_text)

    except Exception as e:
        print(f"❌ Erro em handle_terminal_error: {e}")



class SingleApplication:
    def __init__(self, app_id):
        self.app = QApplication(sys.argv)
        self.app_id = app_id
        self.server = None
        self.socket = QLocalSocket()

    def is_running(self):
        self.socket.connectToServer(self.app_id)
        if self.socket.waitForConnected(500):
            self.socket.disconnectFromServer()
            return True
        return False

    def run(self):
        if self.is_running():
            print("Aplicação já está em execução!")
            return False

        # Criar servidor local
        self.server = QLocalServer()
        self.server.listen(self.app_id)
        return True


if __name__ == "__main__":
    # Configurar encoding de forma segura
    try:
        if os.name == 'nt' and hasattr(sys.stdout, 'reconfigure') and sys.stdout is not None:
            sys.stdout.reconfigure(encoding='utf-8')
        if os.name == 'nt' and hasattr(sys.stderr, 'reconfigure') and sys.stderr is not None:
            sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        # Fallback seguro se reconfigure não estiver disponível
        pass

    try:
        # Verificar se já está rodando
        single_app = SingleApplication("py_dragon_studio_ide")
        if not single_app.run():
            sys.exit(1)

        app = single_app.app
        app.setApplicationName("Py Dragon Studio IDE")
        app.setApplicationVersion("1.0.0")

        window = IDE()
        window.show()

        exit_code = app.exec()
        
        # Limpar servidor ao sair
        if single_app.server:
            single_app.server.close()
            
        sys.exit(exit_code)

    except Exception as e:
        print(f"Erro crítico: {e}")
        # Mensagem de erro simples sem emojis
        QMessageBox.critical(None, "Erro", f"Erro ao inicializar: {str(e)}")
        sys.exit(1)

