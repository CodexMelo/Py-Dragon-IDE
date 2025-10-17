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
import logging
import threading
import time
import traceback
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List
from urllib.request import urlretrieve
# ===== LSP CLIENT IMPLEMENTATION =====
from threading import Thread
from queue import Queue, Empty

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
    Signal,QRect,QPoint
)
from PySide6.QtGui import (
    QAction,
    QColor,QIcon,
    QFont,
    QFontDatabase,
    QGuiApplication,
    QKeyEvent,QTextFormat,
    QPainter,
    QPalette,
    QShortcut,
    QSyntaxHighlighter,
    QTextBlockUserData,
    QTextCharFormat,
    QTextCursor,
    QTextOption, QKeySequence,QTextDocument)
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
    QListWidget,QTreeWidgetItem,QTreeWidget,
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
    QTreeView,QVBoxLayout,QWidget,QTableWidget, QTableWidgetItem, QVBoxLayout as QVBoxLayoutDialog,QFrame

)



 


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

class OutlineWidget(QWidget):
    """Widget que mostra a estrutura do código (classes e funções) igual ao VS Code"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ide = parent
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        self.refresh_btn = QAction("🔄", self)
        self.refresh_btn.setToolTip("Atualizar outline")
        self.refresh_btn.triggered.connect(self.refresh_outline)
        
        self.collapse_btn = QAction("📁", self)
        self.collapse_btn.setToolTip("Recolher tudo")
        self.collapse_btn.triggered.connect(self.collapse_all)
        
        self.expand_btn = QAction("📂", self)
        self.expand_btn.setToolTip("Expandir tudo")
        self.expand_btn.triggered.connect(self.expand_all)
        
        toolbar.addAction(self.refresh_btn)
        toolbar.addAction(self.collapse_btn)
        toolbar.addAction(self.expand_btn)
        
        layout.addWidget(toolbar)
        
        # Tree widget para mostrar a estrutura
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(12)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Estilo do tree widget
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px 2px;
                border: 1px solid transparent;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)
        
        layout.addWidget(self.tree_widget)
        
    def refresh_outline(self):
        """Atualiza o outline baseado no editor atual"""
        editor = self.ide.get_current_editor()
        if not editor:
            self.tree_widget.clear()
            return
            
        content = editor.toPlainText()
        self.parse_content(content)
        
    def parse_content(self, content):
        """Analisa o conteúdo e extrai classes e funções de forma mais robusta"""
        self.tree_widget.clear()
        
        try:
            lines = content.split('\n')
            current_class = None
            class_item = None
            current_indent = 0
            
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                    
                # Calcula indentação atual
                indent = len(line) - len(line.lstrip())
                
                # Detecta classes
                class_match = re.match(r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped_line)
                if class_match:
                    class_name = class_match.group(1)
                    current_class = class_name
                    class_item = QTreeWidgetItem(self.tree_widget)
                    class_item.setText(0, f"📦 {class_name}")
                    class_item.setData(0, Qt.UserRole, {"type": "class", "line": line_num})
                    class_item.setExpanded(True)
                    current_indent = indent
                    continue
                
                # Detecta funções (apenas no nível correto de indentação)
                func_match = re.match(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped_line)
                if func_match:
                    func_name = func_match.group(1)
                    
                    if current_class and indent > current_indent:
                        # Método dentro de classe
                        func_item = QTreeWidgetItem(class_item)
                        func_item.setText(0, f"🔧 {func_name}()")
                        func_item.setData(0, Qt.UserRole, {"type": "method", "line": line_num, "class": current_class})
                    else:
                        # Função global
                        func_item = QTreeWidgetItem(self.tree_widget)
                        func_item.setText(0, f"📋 {func_name}()")
                        func_item.setData(0, Qt.UserRole, {"type": "function", "line": line_num})
                        current_class = None  # Reset da classe atual
                        
        except Exception as e:
            print(f"Erro ao analisar outline: {e}")
            
    def on_item_double_clicked(self, item, column):
        """Navega para a linha quando um item é clicado"""
        data = item.data(0, Qt.UserRole)
        if data and 'line' in data:
            self.ide.navigate_to_line(data['line'])
            
    def collapse_all(self):
        """Recolhe todos os itens"""
        self.tree_widget.collapseAll()
        
    def expand_all(self):
        """Expande todos os itens"""
        self.tree_widget.expandAll()
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
class ProjectImportAnalyzer:
    """Analisa imports e arquivos do projeto para autocomplete"""
    
    def __init__(self):
        self.project_files_cache = {}
        self.import_cache = {}
        self.last_scan_time = 0
        
    def scan_project_files(self, project_path):
        """Escaneia todos os arquivos Python do projeto"""
        if not project_path or not os.path.exists(project_path):
            return {}
            
        current_time = time.time()
        # Recarrega cache a cada 30 segundos
        if (project_path in self.project_files_cache and 
            current_time - self.last_scan_time < 30):
            return self.project_files_cache[project_path]
            
        python_files = {}
        
        try:
            # Busca arquivos .py em todo o projeto
            for root, dirs, files in os.walk(project_path):
                # Ignora diretórios comuns
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if '.git' in dirs:
                    dirs.remove('.git')
                if 'venv' in dirs:
                    dirs.remove('venv')
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, project_path)
                        module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                        
                        # Extrai definições do arquivo
                        definitions = self._extract_file_definitions(full_path)
                        python_files[module_name] = {
                            'path': full_path,
                            'definitions': definitions,
                            'name': file[:-3]  # Remove .py
                        }
                        
        except Exception as e:
            print(f"⚠️ Erro ao escanear projeto: {e}")
            
        self.project_files_cache[project_path] = python_files
        self.last_scan_time = current_time
        return python_files
    
    def _extract_file_definitions(self, file_path):
        """Extrai funções, classes e variáveis de um arquivo"""
        definitions = {
            'functions': set(),
            'classes': set(), 
            'variables': set(),
            'imports': set()
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Análise com regex (fallback se AST falhar)
            functions = re.findall(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
            classes = re.findall(r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
            imports = re.findall(r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
            from_imports = re.findall(r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', content, re.MULTILINE)
            
            definitions['functions'].update([f"{f}()" for f in functions])
            definitions['classes'].update(classes)
            definitions['imports'].update(imports)
            definitions['imports'].update(from_imports)
            
            # Tenta análise AST para mais precisão
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        definitions['functions'].add(f"{node.name}()")
                    elif isinstance(node, ast.ClassDef):
                        definitions['classes'].add(node.name)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            definitions['imports'].add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        definitions['imports'].add(node.module)
            except:
                pass  # Usa apenas regex se AST falhar
                
        except Exception as e:
            print(f"⚠️ Erro ao analisar {file_path}: {e}")
            
        return definitions
    
    def get_import_suggestions(self, project_path, current_file=""):
        """Sugere módulos para import"""
        suggestions = set()
        
        # Módulos padrão do Python
        stdlib_modules = [
            'os', 'sys', 'json', 're', 'datetime', 'math', 'random',
            'subprocess', 'shutil', 'glob', 'ast', 'inspect', 'importlib',
            'platform', 'time', 'pathlib', 'collections', 'itertools', 'functools',
            'typing', 'logging', 'unittest', 'threading', 'multiprocessing'
        ]
        suggestions.update(stdlib_modules)
        
        # Módulos do projeto
        if project_path:
            project_files = self.scan_project_files(project_path)
            suggestions.update(project_files.keys())
            
            # Também adiciona nomes de arquivos sem extensão
            for module_info in project_files.values():
                suggestions.add(module_info['name'])
        
        return sorted(list(suggestions))
    
    def get_from_import_suggestions(self, project_path, module_name, current_file=""):
        """Sugere o que importar de um módulo específico"""
        suggestions = set()
        
        # Verifica se é um módulo do projeto
        project_files = self.scan_project_files(project_path) if project_path else {}
        
        if module_name in project_files:
            # É um módulo local - usa definições do arquivo
            definitions = project_files[module_name]['definitions']
            suggestions.update(definitions['functions'])
            suggestions.update(definitions['classes'])
            suggestions.update(definitions['imports'])
        else:
            # É um módulo externo ou stdlib - usa mapeamento hardcoded
            stdlib_contents = self._get_stdlib_contents(module_name)
            suggestions.update(stdlib_contents)
        
        return sorted(list(suggestions))
    
    def _get_stdlib_contents(self, module_name):
        """Conteúdo hardcoded de módulos stdlib comuns"""
        stdlib_map = {
            'os': ['path', 'environ', 'getcwd', 'listdir', 'mkdir', 'remove', 'rename', 
                   'system', 'walk', 'chdir', 'getenv', 'makedirs', 'rmdir'],
            'sys': ['argv', 'path', 'exit', 'version', 'platform', 'modules', 'executable'],
            'json': ['loads', 'dumps', 'load', 'dump', 'JSONEncoder', 'JSONDecoder'],
            're': ['search', 'match', 'findall', 'sub', 'compile', 'escape', 'IGNORECASE'],
            'datetime': ['datetime', 'date', 'time', 'timedelta', 'now', 'today'],
            'math': ['sqrt', 'sin', 'cos', 'tan', 'pi', 'e', 'log', 'exp', 'ceil', 'floor'],
            'random': ['random', 'randint', 'choice', 'shuffle', 'uniform', 'seed'],
            'subprocess': ['run', 'call', 'check_output', 'Popen', 'PIPE', 'STDOUT'],
            'pathlib': ['Path', 'PurePath', 'WindowsPath', 'PosixPath'],
            'collections': ['deque', 'Counter', 'OrderedDict', 'defaultdict', 'namedtuple'],
            'typing': ['List', 'Dict', 'Set', 'Tuple', 'Any', 'Union', 'Optional']
        }
        return stdlib_map.get(module_name, [])

class SmartImportCompleter:
    """Completador inteligente para imports e arquivos do projeto"""
    
    def __init__(self):
        self.analyzer = ProjectImportAnalyzer()
        self.last_context = {}
        
    def get_import_completions(self, code, cursor_position, file_path="", project_path=""):
        """Obtém sugestões específicas para contexto de import"""
        context = self._analyze_import_context(code, cursor_position)
        self.last_context = context
        
        if context['type'] == 'import':
            return self.analyzer.get_import_suggestions(project_path, file_path)
            
        elif context['type'] == 'from_import':
            return self.analyzer.get_from_import_suggestions(
                project_path, context['module'], file_path)
                
        elif context['type'] == 'project_file':
            return self._get_project_file_suggestions(project_path)
            
        else:
            return self._get_general_suggestions(code, project_path, file_path)
    
    def _analyze_import_context(self, code, cursor_position):
        """Analisa o contexto atual para determinar tipo de sugestão"""
        text_before = code[:cursor_position]
        current_line = text_before.split('\n')[-1] if '\n' in text_before else text_before
        
        # Verifica se está em import
        if 'import' in current_line:
            if 'from' in current_line:
                # from module import ...
                parts = current_line.split('import')
                if len(parts) > 1:
                    module_part = parts[0].replace('from', '').strip()
                    return {'type': 'from_import', 'module': module_part}
                else:
                    module_part = current_line.replace('from', '').strip()
                    return {'type': 'from_import', 'module': module_part}
            else:
                # import module
                return {'type': 'import'}
        
        # Verifica se está digitando caminho de arquivo
        elif any(keyword in current_line for keyword in ['open(', 'Path(', 'with open']):
            if any(quote in current_line for quote in ['"', "'"]):
                return {'type': 'project_file'}
        
        # Contexto geral
        return {'type': 'general'}
    
    def _get_project_file_suggestions(self, project_path):
        """Sugere arquivos do projeto"""
        suggestions = set()
        
        if not project_path:
            return list(suggestions)
            
        try:
            # Busca arquivos comuns
            patterns = ['*.py', '*.txt', '*.json', '*.xml', '*.html', '*.css', '*.js']
            
            for pattern in patterns:
                for file_path in glob.glob(os.path.join(project_path, '**', pattern), recursive=True):
                    if '__pycache__' not in file_path and '.git' not in file_path:
                        rel_path = os.path.relpath(file_path, project_path)
                        suggestions.add(f"'{rel_path}'")
                        
        except Exception as e:
            print(f"⚠️ Erro ao buscar arquivos: {e}")
            
        return sorted(list(suggestions))
    
    def _get_general_suggestions(self, code, project_path, file_path):
        """Sugestões gerais incluindo definições locais"""
        suggestions = set()
        
        # Palavras-chave Python
        keywords = [
            "if", "else", "elif", "for", "while", "def", "class", "import", "from",
            "return", "print", "len", "str", "list", "dict", "True", "False", "None"
        ]
        suggestions.update(keywords)
        
        # Definições do arquivo atual
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                suggestions.update([f"{f}()" for f in functions])
                
                classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                suggestions.update(classes)
                
            except:
                pass
        
        # Módulos do projeto
        if project_path:
            project_files = self.analyzer.scan_project_files(project_path)
            suggestions.update(project_files.keys())
        
        return sorted(list(suggestions))

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
class CodeFoldingArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setMouseTracking(True)
        self.setFixedWidth(16)
        
    def sizeHint(self):
        return QSize(16, 0)
        
    def paintEvent(self, event):
        """Pinta os indicadores de folding - VERSÃO CORRIGIDA"""
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
                
            # Preenche o fundo com cor mais suave
            painter.fillRect(event.rect(), QColor(40, 40, 45))
            
            block = self.editor.firstVisibleBlock()
            block_number = block.blockNumber()
            top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            bottom = top + self.editor.blockBoundingRect(block).height()
            
            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    # Desenha o indicador de folding se a linha for dobrável
                    if self.is_block_foldable(block):
                        rect = QRect(4, int(top) + 4, 8, 8)  # Indicador menor
                        
                        # Cor do indicador mais suave
                        painter.setPen(QColor(120, 120, 120))
                        painter.setBrush(QColor(60, 60, 65))
                        painter.drawRect(rect)
                        
                        # Sinal de + ou -
                        painter.setPen(QColor(180, 180, 180))
                        painter.drawLine(rect.left() + 2, rect.center().y(), rect.right() - 2, rect.center().y())
                        
                        # Só desenha a linha vertical se não estiver dobrado
                        if not self.is_block_folded(block):
                            painter.drawLine(rect.center().x(), rect.top() + 2, rect.center().x(), rect.bottom() - 2)
                
                block = block.next()
                top = bottom
                bottom = top + self.editor.blockBoundingRect(block).height()
                block_number += 1
                
        except Exception as e:
            print(f"Erro no paintEvent do folding: {e}")

    def is_block_foldable(self, block):
        """Verifica se um bloco pode ser dobrado - MAIS PRECISO"""
        try:
            text = block.text().strip()
            
            # Apenas linhas que realmente iniciam estruturas de bloco
            return (text.startswith('class ') or 
                    text.startswith('def ') or 
                    text.startswith('async def') or
                    (text.startswith('if ') and text.endswith(':')) or
                    (text.startswith('for ') and text.endswith(':')) or
                    (text.startswith('while ') and text.endswith(':')) or
                    (text.startswith('with ') and text.endswith(':')) or
                    text == 'try:' or
                    (text.startswith('elif ') and text.endswith(':')) or
                    text == 'else:' or
                    text == 'except:' or
                    text == 'finally:')
        except:
            return False

    def is_block_folded(self, block):
        """Verifica se um bloco está dobrado - MÉTODO ADICIONADO"""
        try:
            user_data = block.userData()
            if user_data and hasattr(user_data, 'is_folded'):
                return user_data.is_folded()
            return False
        except:
            return False

    def mousePressEvent(self, event):
        """Manipula clique nos indicadores de folding - CORRIGIDO"""
        if event.button() == Qt.LeftButton:
            # Encontra o bloco clicado - CORREÇÃO PARA PySide6
            block = self.editor.firstVisibleBlock()
            top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            bottom = top + self.editor.blockBoundingRect(block).height()
            
            while block.isValid():
                # PySide6 usa position() em vez de pos()
                if (event.position().y() >= top and event.position().y() <= bottom and 
                    self.is_block_foldable(block)):
                    self.toggle_fold(block)
                    break
                
                block = block.next()
                top = bottom
                bottom = top + self.editor.blockBoundingRect(block).height()

    def toggle_fold(self, block):
        """Alterna o estado de folding de um bloco - CORRIGIDO"""
        if not self.is_block_foldable(block):
            return
            
        try:
            # Obtém ou cria dados do usuário para o bloco
            user_data = block.userData()
            if not user_data or not hasattr(user_data, 'set_folded'):
                # Cria novos dados de folding se não existirem
                user_data = FoldData()
                block.setUserData(user_data)
            
            # Alterna estado
            currently_folded = self.is_block_folded(block)
            user_data.set_folded(not currently_folded)
            
            # Aplica o folding
            self.apply_folding(block, not currently_folded)
            
            # Atualiza a visualização
            self.update()
            self.editor.viewport().update()
            
        except Exception as e:
            print(f"Erro ao alternar folding: {e}")

    def apply_folding(self, start_block, fold):
        """Aplica folding a partir de um bloco - VERSÃO MELHORADA"""
        try:
            start_text = start_block.text()
            start_indent = len(start_text) - len(start_text.lstrip())
            current_block = start_block.next()
            
            blocks_to_fold = []
            
            while current_block.isValid():
                current_text = current_block.text()
                if not current_text.strip():  # Linha vazia
                    current_block = current_block.next()
                    continue
                    
                current_indent = len(current_text) - len(current_text.lstrip())
                
                # Se a indentação for menor ou igual, para
                if current_indent <= start_indent:
                    break
                    
                # Marca bloco para ser dobrado
                blocks_to_fold.append(current_block)
                current_block = current_block.next()
            
            # Aplica folding a todos os blocos de uma vez
            for block in blocks_to_fold:
                block.setVisible(not fold)
                
        except Exception as e:
            print(f"Erro ao aplicar folding: {e}")
class FoldData(QTextBlockUserData):
    
    def __init__(self):
        super().__init__()
        self._folded = False
        self._fold_level = 0
    
    def is_folded(self):
        return self._folded
    
    def set_folded(self, folded):
        self._folded = folded
    
    def get_fold_level(self):
        return self._fold_level
    
    def set_fold_level(self, level):
        self._fold_level = level
            

class AutoCompleteWorker(QThread):
    def __init__(self, ide_instance):
        super().__init__()
        self.ide = ide_instance
        self._is_running = True
        self._mutex = threading.Lock()

    def stop(self):
        """Para o worker de forma segura"""
        with self._mutex:
             self._is_running = False
             self.quit()
             self.wait(2000)

    def run(self):
        """Loop principal do worker de autocomplete"""
        while self._is_running:
            try:
                # Aguarda por trabalho
                self.msleep(100)
                
                # Verifica se há editor atual
                editor = self.ide.get_current_editor()
                if not editor or not hasattr(editor, 'file_path'):
                    continue
                    
                # Obtém sugestões
                suggestions = self.get_suggestions_for_editor(editor)
                if suggestions:
                    self.suggestion_ready.emit(editor.file_path, suggestions)
                    
            except Exception as e:
                print(f"Erro no worker de autocomplete: {e}")

    # No método get_suggestions_for_editor do AutoCompleteWorker:
    def get_suggestions_for_editor(self, editor):
        """Obtém sugestões para o editor atual - AUMENTADO"""
        try:
            if not hasattr(self.ide, 'completer'):
                return []
                
            code = editor.toPlainText()
            cursor = editor.textCursor()
            cursor_position = cursor.position()
            
            suggestions = self.ide.completer.get_completions(
                code, 
                cursor_position,
                editor.file_path,
                self.ide.project_path if hasattr(self.ide, 'project_path') else ""
            )
            
            # AUMENTADO: Limita a 25 sugestões em vez de 15
            return suggestions[:100000]
            
        except Exception as e:
            print(f"Erro ao obter sugestões: {e}")
            return []


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


# ===== SISTEMA DE AUTOCOMPLETE FLUTUANTE =====
class ScopeHeaderWidget(QWidget):
    """Widget que mostra o escopo atual (classe/função)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_class = "Global"
        self.current_function = "Nenhuma"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.scope_label = QLabel()
        self.scope_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                color: #9cdcfe;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        
        layout.addWidget(self.scope_label)
        self.setLayout(layout)
        self.update_display()
        
    def update_scope(self, current_class, current_function):
        """Atualiza o escopo atual"""
        self.current_class = current_class
        self.current_function = current_function
        self.update_display()
        
    def update_display(self):
        """Atualiza o display do escopo"""
        text_parts = []
        if self.current_class != "Global":
            text_parts.append(f"📦 {self.current_class}")
        if self.current_function != "Nenhuma":
            text_parts.append(f"📋 {self.current_function}")
            
        if text_parts:
            self.scope_label.setText(" → ".join(text_parts))
        else:
            self.scope_label.setText("🌍 Global")
            
    def show_scope(self):
        """Mostra o widget de escopo"""
        self.show()
        
    def hide_scope(self):
        """Esconde o widget de escopo"""
        self.hide()

        CodeFoldingArea
class FloatingAutoCompleteWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_editor = None
        self.enabled = True  # Novo: controle de estado
        
    def setup_ui(self):
        """Configura a interface do widget"""
        # Configurações de janela
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setMaximumHeight(200)
        self.setMaximumWidth(400)
        self.setFocusPolicy(Qt.NoFocus)
        
        # Estilo moderno similar ao VS Code
        self.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                font-family: 'Segoe UI', 'Consolas', monospace;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #2d2d30;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: white;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)
        
        # Conectar sinais
        self.itemDoubleClicked.connect(self.insert_completion)
            
    def show_completions(self, editor, suggestions, position=None):
        """Mostra sugestões na posição do cursor - VERSÃO CORRIGIDA"""
        if not self.enabled or not suggestions:
            self.hide()
            return
                
        self.current_editor = editor
        self.clear()
        
        # Limita a 25 sugestões
        suggestions = suggestions[:1000]
        
        # Adiciona sugestões
        for suggestion in suggestions:
            item = QListWidgetItem(suggestion)
            
            # Destaque visual baseado no tipo de sugestão
            if suggestion.endswith('()'):
                item.setForeground(QColor("#DCDCAA"))  # Amarelo para funções
            elif suggestion[0].isupper():
                item.setForeground(QColor("#4EC9B0"))  # Ciano para classes
            elif suggestion in ['import', 'from', 'def', 'class', 'if', 'for', 'while']:
                item.setForeground(QColor("#569CD6"))  # Azul para palavras-chave
            
            self.addItem(item)
        
        # Ajusta tamanho dinamicamente
        self.adjust_size(len(suggestions))
        
        # Posiciona o widget
        self.position_completion_widget(editor, position)
        
        # Mostra e seleciona primeiro item
        self.show()
        self.setCurrentRow(0)
        self.setFocus()

        
    def adjust_size(self, item_count):
            """Ajusta o tamanho do widget baseado no número de itens"""
            item_height = self.sizeHintForRow(0)
            visible_items = min(item_count, 15)  # Mostra até 15 itens visíveis
            
            height = item_height * visible_items + 4
            width = 500  # Largura aumentada para acomodar mais texto
            
            self.setFixedHeight(height)
            self.setFixedWidth(width)
        
    def position_completion_widget(self, editor, position=None):
        """Posiciona o widget próximo ao cursor - MÉTODO CORRIGIDO (nome alterado)"""
        if position:
            # Usa posição fornecida
            global_pos = editor.mapToGlobal(position)
        else:
            # Usa posição do cursor
            cursor_rect = editor.cursorRect()
            global_pos = editor.mapToGlobal(cursor_rect.bottomLeft())
        
        # Ajusta para não sair da tela
        screen = QApplication.primaryScreen().availableGeometry()
        
        # Verifica borda inferior
        if global_pos.y() + self.height() > screen.bottom():
            global_pos = editor.mapToGlobal(cursor_rect.topLeft())
            global_pos.setY(global_pos.y() - self.height())
            
        # Verifica borda direita
        if global_pos.x() + self.width() > screen.right():
            global_pos.setX(screen.right() - self.width())
            
        # Verifica borda esquerda
        if global_pos.x() < screen.left():
            global_pos.setX(screen.left())
            
        self.move(global_pos)

    def keyPressEvent(self, event):
        """Manipula teclas para navegação e inserção"""
        key = event.key()
        
        if key == Qt.Key_Escape:
            # Escape - fecha e desativa temporariamente
            self.hide()
            self.enabled = False
            event.accept()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            # Enter - insere completion
            self.insert_completion()
            event.accept()
        elif key == Qt.Key_Tab:
            # Tab - insere completion
            self.insert_completion()
            event.accept()
        elif key == Qt.Key_Up:
            # Seta para cima - navega
            if self.currentRow() == 0:
                self.setCurrentRow(self.count() - 1)
            else:
                self.setCurrentRow(self.currentRow() - 1)
            event.accept()
        elif key == Qt.Key_Down:
            # Seta para baixo - navega
            if self.currentRow() == self.count() - 1:
                self.setCurrentRow(0)
            else:
                self.setCurrentRow(self.currentRow() + 1)
            event.accept()
        else:
            # Outras teclas - repassa para o editor
            if self.current_editor:
                self.current_editor.keyPressEvent(event)
            self.hide()

            
    def insert_completion(self, item=None):
        """Insere a sugestão selecionada no editor"""
        if not self.current_editor:
            return
            
        if item is None:
            item = self.currentItem()
            
        if item:
            completion = item.text()
            cursor = self.current_editor.textCursor()
            
            # Remove a parte já digitada (se houver)
            current_line = cursor.block().text()
            cursor.select(QTextCursor.WordUnderCursor)
            current_word = cursor.selectedText()
            
            # Remove parênteses se já existirem em funções
            if completion.endswith('()') and current_word:
                # Se já tem parênteses, remove da completion
                if current_word + '()' == completion:
                    completion = current_word
                # Se está no meio do nome da função, insere só o nome
                elif current_word in completion:
                    completion = completion.replace('()', '')
            
            # Insere o texto
            if current_word:
                # Substitui a palavra atual
                cursor.insertText(completion)
            else:
                # Insere normalmente
                cursor.insertText(completion)
                
            # Foca no editor novamente
            self.current_editor.setFocus()
            
        self.hide()
            
    def get_icon(self, icon_type):
        """Retorna ícone baseado no tipo"""
        # Implementação simples sem ícones por enquanto
        return QIcon()
        
    def hideEvent(self, event):
        """Limpa referências quando escondido"""
        self.current_editor = None
        super().hideEvent(event)

    def set_enabled(self, enabled):
        """Ativa/desativa o autocomplete"""
        self.enabled = enabled
        if not enabled:
            self.hide()
    
    def toggle_enabled(self):
        """Alterna o estado do autocomplete"""
        self.enabled = not self.enabled
        if not self.enabled:
            self.hide()
        return self.enabled

class FoldData(QTextBlockUserData):
    """Classe personalizada para armazenar dados de folding"""
    
    def __init__(self):
        super().__init__()
        self._folded = False
        self._fold_level = 0
    
    def is_folded(self):
        return self._folded
    
    def set_folded(self, folded):
        self._folded = folded
    
    def get_fold_level(self):
        return self._fold_level
    
    def set_fold_level(self, level):
        self._fold_level = level     
class CodeFoldingArea(QWidget):    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setMouseTracking(True)
        self.setFixedWidth(16)
        
    def sizeHint(self):
        return QSize(16, 0)
        
    def paintEvent(self, event):
        """Pinta os indicadores de folding - VERSÃO CORRIGIDA"""
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
                
            # Preenche o fundo com cor mais suave
            painter.fillRect(event.rect(), QColor(40, 40, 45))
            
            block = self.editor.firstVisibleBlock()
            block_number = block.blockNumber()
            top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            bottom = top + self.editor.blockBoundingRect(block).height()
            
            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    # Desenha o indicador de folding se a linha for dobrável
                    if self.is_block_foldable(block):
                        rect = QRect(4, int(top) + 4, 8, 8)  # Indicador menor
                        
                        # Cor do indicador mais suave
                        painter.setPen(QColor(120, 120, 120))
                        painter.setBrush(QColor(60, 60, 65))
                        painter.drawRect(rect)
                        
                        # Sinal de + ou -
                        painter.setPen(QColor(180, 180, 180))
                        painter.drawLine(rect.left() + 2, rect.center().y(), rect.right() - 2, rect.center().y())
                        
                        # Só desenha a linha vertical se não estiver dobrado
                        if not self.is_block_folded(block):
                            painter.drawLine(rect.center().x(), rect.top() + 2, rect.center().x(), rect.bottom() - 2)
                
                block = block.next()
                top = bottom
                bottom = top + self.editor.blockBoundingRect(block).height()
                block_number += 1
                
        except Exception as e:
            print(f"Erro no paintEvent do folding: {e}")

    def is_block_foldable(self, block):
        """Verifica se um bloco pode ser dobrado - MAIS PRECISO"""
        try:
            text = block.text().strip()
            
            # Apenas linhas que realmente iniciam estruturas de bloco
            return (text.startswith('class ') or 
                    text.startswith('def ') or 
                    text.startswith('async def') or
                    (text.startswith('if ') and text.endswith(':')) or
                    (text.startswith('for ') and text.endswith(':')) or
                    (text.startswith('while ') and text.endswith(':')) or
                    (text.startswith('with ') and text.endswith(':')) or
                    text == 'try:' or
                    (text.startswith('elif ') and text.endswith(':')) or
                    text == 'else:' or
                    text == 'except:' or
                    text == 'finally:')
        except:
            return False

    def is_block_folded(self, block):
        """Verifica se um bloco está dobrado - MÉTODO CORRIGIDO"""
        try:
            user_data = block.userData()
            if user_data and isinstance(user_data, FoldData):
                return user_data.is_folded()
            return False
        except:
            return False

    def mousePressEvent(self, event):
        """Manipula clique nos indicadores de folding - CORRIGIDO"""
        if event.button() == Qt.LeftButton:
            # Encontra o bloco clicado - CORREÇÃO APLICADA AQUI
            block = self.editor.firstVisibleBlock()
            top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            bottom = top + self.editor.blockBoundingRect(block).height()
            
            while block.isValid():
                # SUBSTITUÍDO: event.pos() por event.position()
                if (event.position().y() >= top and event.position().y() <= bottom and 
                    self.is_block_foldable(block)):
                    self.toggle_fold(block)
                    break
                
                block = block.next()
                top = bottom
                bottom = top + self.editor.blockBoundingRect(block).height()

    def toggle_fold(self, block):
        """Alterna o estado de folding de um bloco - CORRIGIDO"""
        if not self.is_block_foldable(block):
            return
            
        try:
            # Obtém ou cria dados do usuário para o bloco
            user_data = block.userData()
            if not user_data or not isinstance(user_data, FoldData):
                # Cria novos dados de folding
                user_data = FoldData()
                block.setUserData(user_data)
            
            # Alterna estado
            currently_folded = user_data.is_folded()
            user_data.set_folded(not currently_folded)
            
            # Aplica o folding
            self.apply_folding(block, not currently_folded)
            
            # Atualiza a visualização
            self.update()
            self.editor.viewport().update()
            
        except Exception as e:
            print(f"Erro ao alternar folding: {e}")

    def apply_folding(self, start_block, fold):
        """Aplica folding a partir de um bloco - VERSÃO MELHORADA"""
        try:
            start_text = start_block.text()
            start_indent = len(start_text) - len(start_text.lstrip())
            current_block = start_block.next()
            
            blocks_to_fold = []
            
            while current_block.isValid():
                current_text = current_block.text()
                if not current_text.strip():  # Linha vazia
                    current_block = current_block.next()
                    continue
                    
                current_indent = len(current_text) - len(current_text.lstrip())
                
                # Se a indentação for menor ou igual, para
                if current_indent <= start_indent:
                    break
                    
                # Marca bloco para ser dobrado
                blocks_to_fold.append(current_block)
                current_block = current_block.next()
            
            # Aplica folding a todos os blocos de uma vez
            for block in blocks_to_fold:
                block.setVisible(not fold)
                
        except Exception as e:
            print(f"Erro ao aplicar folding: {e}")

class ScopeIndicatorWidget(QWidget):
    """Widget que mostra a classe/função atual como no VS Code"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_class = "Global"
        self.current_function = "Nenhuma"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.scope_label = QLabel()
        self.scope_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                color: #9cdcfe;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        
        layout.addWidget(self.scope_label)
        self.setLayout(layout)
        self.update_display()
        
    def update_scope(self, current_class, current_function):
        """Atualiza o escopo atual"""
        self.current_class = current_class
        self.current_function = current_function
        self.update_display()
        
    def update_display(self):
        """Atualiza o display do escopo"""
        text_parts = []
        if self.current_class != "Global":
            text_parts.append(f"📦 {self.current_class}")
        if self.current_function != "Nenhuma":
            text_parts.append(f"📋 {self.current_function}")
            
        if text_parts:
            self.scope_label.setText(" → ".join(text_parts))
        else:
            self.scope_label.setText("🌍 Global")




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
    """Completador híbrido focado em imports e arquivos - VERSÃO MELHORADA"""
    
    def __init__(self):
        self.import_completer = SmartImportCompleter()
        self._jedi_enabled = False
        
    def get_completions(self, text, cursor_position, file_path="", project_path=""):
        """Obtém sugestões focadas em imports e arquivos do projeto - VERSÃO MELHORADA"""
        try:
            # Usa apenas o analisador de imports
            suggestions = self.import_completer.get_import_completions(
                text, cursor_position, file_path, project_path
            )
            
            # Adiciona sugestões básicas se poucas sugestões
            if len(suggestions) < 50:  # AUMENTADO o limite
                basic = self._get_basic_suggestions(text)
                suggestions.extend([s for s in basic if s not in suggestions])
            
            # AUMENTADO: Retorna até 50 sugestões
            return suggestions[:50]
            
        except Exception as e:
            print(f"❌ Erro no completador: {e}")
            return self._get_fallback_suggestions()
    
    def _get_basic_suggestions(self, text):
        """Sugestões básicas de fallback - VERSÃO EXPANDIDA"""
        suggestions = [
            # Palavras-chave Python expandidas
            "print", "def", "class", "if", "else", "elif", "for", "while", "return", 
            "import", "from", "as", "try", "except", "finally", "with", 
            "lambda", "yield", "async", "await", "global", "nonlocal",
            "True", "False", "None", "and", "or", "not", "is", "in",
            "len", "str", "int", "float", "list", "dict", "set", "tuple",
            "range", "type", "isinstance", "issubclass", "hasattr", "getattr",
            "setattr", "delattr", "property", "staticmethod", "classmethod",
            "super", "self", "cls", "__init__", "__str__", "__repr__",
            "__name__", "__main__", "__file__", "__doc__", "__module__",
            
            # Funções comuns adicionais
            "sum", "max", "min", "abs", "round", "sorted", "reversed",
            "enumerate", "zip", "map", "filter", "any", "all", "dir",
            "vars", "locals", "globals", "help", "id", "hash", "callable",
            "issubclass", "iter", "next", "open", "input", "exit", "quit",
            
            # Módulos comuns
            "os", "sys", "json", "re", "datetime", "time", "math", "random",
            "subprocess", "shutil", "pathlib", "collections", "itertools",
            "functools", "typing", "logging", "argparse", "csv", "json"
        ]
        
        # Adiciona funções locais do texto atual
        if text:
            functions = re.findall(r'def\s+(\w+)', text)
            suggestions.extend([f"{f}()" for f in functions])
            
            classes = re.findall(r'class\s+(\w+)', text)
            suggestions.extend(classes)
            
            # Variáveis (nomes com mais de 2 caracteres)
            variables = re.findall(r'(\b[a-zA-Z_][a-zA-Z0-9_]{2,})\b\s*=', text)
            suggestions.extend(variables)
            
        return suggestions
    def _get_fallback_suggestions(self):
        """Sugestões de fallback mínimas e seguras"""
        return [
            "print", "def", "class", "if", "else", "for", "while", "import", 
            "from", "return", "True", "False", "None", "len", "str", "list", 
            "dict", "range", "type", "isinstance"
        ]

    
# ===== DIÁLOGO DO GESTOR DE VERSÕES =====
class LSPClient:
    """Cliente LSP para python-lsp-server (pylsp) - VERSÃO CORRIGIDA"""
    
    def __init__(self, workspace_path=None):
        self.workspace_path = workspace_path or os.getcwd()
        self.process = None
        self.seq_num = 0
        self.pending_requests = {}
        self.message_queue = Queue()
        self.initialized = False
        self.capabilities = {}
        
        # Configurar logging
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Configura sistema de logging para LSP"""
        logger = logging.getLogger('LSPClient')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def start_server(self):
        """Inicia o servidor LSP - VERSÃO CORRIGIDA"""
        try:
            self.logger.info("🔄 Iniciando python-lsp-server...")
            
            # Verificar se pylsp está instalado
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pylsp", "--help"], 
                    capture_output=True, 
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, result.args)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                self.logger.error("❌ python-lsp-server não encontrado. Instale com: pip install python-lsp-server")
                return False

            # Iniciar processo CORRETAMENTE
            self.process = subprocess.Popen(
                [sys.executable, "-m", "pylsp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                universal_newlines=False  # Mudar para False para lidar com bytes
            )
            
            # Iniciar threads para leitura
            self._start_reader_threads()
            
            # Inicializar LSP
            return self._initialize()
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao iniciar LSP server: {e}")
            return False

    def _start_reader_threads(self):
        """Inicia threads para ler stdout e stderr - VERSÃO CORRIGIDA"""
        def read_stdout():
            buffer = b""
            while self.process and self.process.poll() is None:
                try:
                    # Ler dados binários
                    data = self.process.stdout.read(1)
                    if data:
                        buffer += data
                        if buffer.endswith(b'\r\n\r\n'):
                            # Processar mensagem completa
                            try:
                                message = buffer.decode('utf-8').strip()
                                if message:
                                    self._process_message(message)
                            except UnicodeDecodeError:
                                self.logger.error("❌ Erro decodificando mensagem UTF-8")
                            buffer = b""
                    elif not data and buffer:
                        # Tentar processar buffer residual
                        try:
                            message = buffer.decode('utf-8').strip()
                            if message:
                                self._process_message(message)
                        except UnicodeDecodeError:
                            pass
                        buffer = b""
                except Exception as e:
                    self.logger.error(f"Erro lendo stdout: {e}")
                    break

        def read_stderr():
            while self.process and self.process.poll() is None:
                try:
                    line = self.process.stderr.readline()
                    if line:
                        self.logger.warning(f"LSP stderr: {line.strip()}")
                except Exception as e:
                    self.logger.error(f"Erro lendo stderr: {e}")
                    break

        Thread(target=read_stdout, daemon=True).start()
        Thread(target=read_stderr, daemon=True).start()

    def _process_message(self, message):
        """Processa mensagens do servidor LSP - VERSÃO CORRIGIDA"""
        try:
            if not message.strip():
                return
                
            # Extrair conteúdo JSON (pular headers LSP)
            if message.startswith('Content-Length:'):
                lines = message.split('\r\n')
                for line in lines:
                    if line and not line.startswith('Content-Length:') and not line.startswith('Content-Type:'):
                        try:
                            data = json.loads(line)
                            self._handle_json_message(data)
                        except json.JSONDecodeError:
                            continue
            else:
                # Tentar processar como JSON direto
                try:
                    data = json.loads(message)
                    self._handle_json_message(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"❌ Erro decodificando JSON: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Erro processando mensagem: {e}")

    def _handle_json_message(self, data):
        """Manipula mensagem JSON do LSP"""
        self.logger.debug(f"📨 Mensagem recebida: {data.get('method', 'Unknown')}")
        
        # Processar resposta para requisições pendentes
        if 'id' in data:
            request_id = data['id']
            if request_id in self.pending_requests:
                callback = self.pending_requests.pop(request_id)
                if callback:
                    callback(data)
        
        # Processar notificações
        elif 'method' in data:
            self._handle_notification(data)

    def _handle_notification(self, data):
        """Manipula notificações do servidor"""
        method = data.get('method')
        params = data.get('params', {})
        
        if method == 'textDocument/publishDiagnostics':
            self._handle_diagnostics(params)
        elif method == 'window/showMessage':
            self._handle_show_message(params)
        elif method == 'telemetry/event':
            self.logger.debug(f"Telemetria: {params}")

    def _handle_diagnostics(self, params):
        """Manipula diagnósticos (erros, avisos)"""
        uri = params.get('uri', '')
        diagnostics = params.get('diagnostics', [])
        
        # Converter URI para caminho de arquivo
        file_path = self._uri_to_path(uri)
        
        self.logger.info(f"🔍 Diagnósticos para {file_path}: {len(diagnostics)} problemas")
        
        # Emitir sinais ou processar diagnósticos
        for diagnostic in diagnostics:
            self._process_diagnostic(file_path, diagnostic)

    def _process_diagnostic(self, file_path, diagnostic):
        """Processa um diagnóstico individual"""
        try:
            range_info = diagnostic.get('range', {})
            start = range_info.get('start', {})
            line = start.get('line', 0) + 1  # LSP usa 0-based, IDE usa 1-based
            character = start.get('character', 0) + 1
            
            severity = diagnostic.get('severity', 1)
            message = diagnostic.get('message', '')
            source = diagnostic.get('source', 'pylsp')
            code = diagnostic.get('code', '')
            
            # Mapear severidade
            severity_map = {
                1: 'ERROR',
                2: 'WARNING', 
                3: 'INFO',
                4: 'HINT'
            }
            severity_str = severity_map.get(severity, 'INFO')
            
            self.logger.debug(f"📋 {severity_str} em {file_path}:{line}:{character} - {message}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro processando diagnóstico: {e}")

    def _handle_show_message(self, params):
        """Manipula mensagens do servidor"""
        message_type = params.get('type', 3)
        message = params.get('message', '')
        
        type_map = {
            1: 'ERROR',
            2: 'WARNING',
            3: 'INFO',
            4: 'LOG'
        }
        
        log_level = type_map.get(message_type, 'INFO')
        self.logger.info(f"💬 LSP {log_level}: {message}")

    def _initialize(self):
        """Inicializa conexão com servidor LSP"""
        initialize_params = {
            "processId": os.getpid(),
            "rootPath": self.workspace_path,
            "rootUri": self._path_to_uri(self.workspace_path),
            "capabilities": {
                "workspace": {
                    "configuration": True,
                    "workspaceFolders": True
                },
                "textDocument": {
                    "completion": {
                        "completionItem": {
                            "snippetSupport": True
                        }
                    },
                    "hover": {
                        "contentFormat": ["plaintext", "markdown"]
                    },
                    "signatureHelp": {
                        "signatureInformation": {
                            "parameterInformation": {
                                "labelOffsetSupport": True
                            }
                        }
                    }
                }
            },
            "workspaceFolders": [
                {
                    "uri": self._path_to_uri(self.workspace_path),
                    "name": os.path.basename(self.workspace_path)
                }
            ]
        }
        
        response = self.send_request("initialize", initialize_params)
        if response and not response.get('error'):
            self.capabilities = response.get('result', {}).get('capabilities', {})
            self.initialized = True
            
            # Enviar notificação initialized
            self.send_notification("initialized", {})
            
            self.logger.info("✅ LSP inicializado com sucesso")
            return True
        
        self.logger.error("❌ Falha na inicialização do LSP")
        return False

    def send_request(self, method, params, callback=None):
        """Envia requisição para servidor LSP - VERSÃO CORRIGIDA"""
        if not self.process:
            return None
            
        self.seq_num += 1
        request_id = self.seq_num
        
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        # Registrar callback se fornecido
        if callback:
            self.pending_requests[request_id] = callback
        
        try:
            json_message = json.dumps(message, ensure_ascii=False)
            content = f"Content-Length: {len(json_message.encode('utf-8'))}\r\n\r\n{json_message}"
            
            # Escrever bytes no stdin
            self.process.stdin.write(content.encode('utf-8'))
            self.process.stdin.flush()
            
            self.logger.debug(f"📤 Requisição enviada: {method}")
            
            # Para requisições síncronas, aguardar resposta
            if not callback:
                return self._wait_for_response(request_id)
                
        except Exception as e:
            self.logger.error(f"❌ Erro enviando requisição: {e}")
            if request_id in self.pending_requests:
                self.pending_requests.pop(request_id)
        
        return None

    def _wait_for_response(self, request_id, timeout=10):
        """Aguarda resposta para requisição síncrona"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Verificar se resposta chegou
            if request_id not in self.pending_requests:
                return None
            
            time.sleep(0.1)
        
        self.logger.warning(f"⏰ Timeout esperando resposta para requisição {request_id}")
        return None

    def send_notification(self, method, params):
        """Envia notificação para servidor LSP - VERSÃO CORRIGIDA"""
        if not self.process:
            return
            
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        try:
            json_message = json.dumps(message, ensure_ascii=False)
            content = f"Content-Length: {len(json_message.encode('utf-8'))}\r\n\r\n{json_message}"
            
            # Escrever bytes no stdin
            self.process.stdin.write(content.encode('utf-8'))
            self.process.stdin.flush()
            
            self.logger.debug(f"📤 Notificação enviada: {method}")
        except Exception as e:
            self.logger.error(f"❌ Erro enviando notificação: {e}")

    def did_open(self, file_path, text, language_id="python"):
        """Notifica que arquivo foi aberto"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": text
            }
        }
        self.send_notification("textDocument/didOpen", params)

    def did_change(self, file_path, text, version=1):
        """Notifica que arquivo foi modificado"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri,
                "version": version
            },
            "contentChanges": [
                {
                    "text": text
                }
            ]
        }
        self.send_notification("textDocument/didChange", params)

    def did_close(self, file_path):
        """Notifica que arquivo foi fechado"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            }
        }
        self.send_notification("textDocument/didClose", params)

    def get_completions(self, file_path, line, character, callback=None):
        """Obtém sugestões de autocomplete"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            },
            "position": {
                "line": line - 1,  # Converter para 0-based
                "character": character - 1
            },
            "context": {
                "triggerKind": 1  # Invoked
            }
        }
        
        return self.send_request("textDocument/completion", params, callback)

    def get_hover(self, file_path, line, character, callback=None):
        """Obtém informação de hover"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            },
            "position": {
                "line": line - 1,
                "character": character - 1
            }
        }
        
        return self.send_request("textDocument/hover", params, callback)

    def get_signature_help(self, file_path, line, character, callback=None):
        """Obtém ajuda de assinatura"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            },
            "position": {
                "line": line - 1,
                "character": character - 1
            }
        }
        
        return self.send_request("textDocument/signatureHelp", params, callback)

    def get_document_symbols(self, file_path, callback=None):
        """Obtém símbolos do documento"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            }
        }
        
        return self.send_request("textDocument/documentSymbol", params, callback)

    def format_document(self, file_path, callback=None):
        """Formata documento"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            },
            "options": {
                "tabSize": 4,
                "insertSpaces": True
            }
        }
        
        return self.send_request("textDocument/formatting", params, callback)

    def _path_to_uri(self, path):
        """Converte caminho para URI de forma robusta"""
        try:
            if not path:
                return ""
                
            # Obter caminho absoluto
            abs_path = os.path.abspath(path)
            
            # Normalizar para formato URI
            if os.name == 'nt':  # Windows
                # Remover drive letter colon e substituir backslashes
                normalized_path = abs_path.replace('\\', '/')
                # Se tiver drive letter (ex: C:/), formatar corretamente
                if ':' in normalized_path:
                    # Formato: file:///C:/Users/...
                    return f"file:///{normalized_path}"
                else:
                    return f"file:///{normalized_path}"
            else:  # Linux/Mac
                # Formato: file:///home/user/...
                return f"file://{abs_path}"
                
        except Exception as e:
            self.logger.error(f"❌ Erro convertendo path para URI: {e}")
            # Fallback seguro
            return f"file://{os.path.abspath(path or '')}"

    def _uri_to_path(self, uri):
        """Converte URI para caminho de forma robusta"""
        try:
            if not uri or not uri.startswith('file://'):
                return uri or ""
                
            path = uri[7:]  # Remove 'file://'
            
            if os.name == 'nt':  # Windows
                # Remover barra inicial se existir: /C:/ → C:/
                if path.startswith('/') and len(path) > 2 and path[2] == ':':
                    path = path[1:]
                return path.replace('/', '\\')
            else:  # Linux/Mac
                return path
                
        except Exception as e:
            self.logger.error(f"❌ Erro convertendo URI para path: {e}")
            return uri.replace('file://', '') if uri else ""


    def shutdown(self):
        """Desliga servidor LSP"""
        if self.initialized:
            self.send_request("shutdown", {})
            self.send_notification("exit", {})
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                    self.process.wait(timeout=2)
                except:
                    pass
            
        self.initialized = False
        self.logger.info("🔚 LSP client finalizado")


class LSPManager:
    """Gerenciador LSP para o IDE"""
    
    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.lsp_client = None
        self.workspace_path = None
        self.open_documents = {}
        
    def initialize(self, workspace_path):
        """Inicializa LSP para workspace"""
        try:
            self.workspace_path = workspace_path
            self.lsp_client = LSPClient(workspace_path)
            
            if self.lsp_client.start_server():
                if hasattr(self.ide, 'statusBar'):
                    self.ide.statusBar().showMessage("✅ LSP inicializado com sucesso", 3000)
                return True
            else:
                if hasattr(self.ide, 'statusBar'):
                    self.ide.statusBar().showMessage("❌ Falha ao inicializar LSP", 3000)
                return False
                
        except Exception as e:
            print(f"❌ Erro inicializando LSP: {e}")
            return False
    
    def open_document(self, file_path, content):
        """Abre documento no LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            self.lsp_client.did_open(file_path, content)
            self.open_documents[file_path] = content
    
    def update_document(self, file_path, content):
        """Atualiza documento no LSP"""
        if (self.lsp_client and self.lsp_client.initialized and 
            file_path in self.open_documents):
            
            version = self.open_documents.get(f"{file_path}_version", 1) + 1
            self.lsp_client.did_change(file_path, content, version)
            self.open_documents[file_path] = content
            self.open_documents[f"{file_path}_version"] = version
    
    def close_document(self, file_path):
        """Fecha documento no LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            self.lsp_client.did_close(file_path)
            if file_path in self.open_documents:
                del self.open_documents[file_path]
    
    def get_completions(self, file_path, line, column, callback=None):
        """Obtém completions via LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            return self.lsp_client.get_completions(file_path, line, column, callback)
        return None
    
    def get_hover_info(self, file_path, line, column, callback=None):
        """Obtém informação de hover via LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            return self.lsp_client.get_hover(file_path, line, column, callback)
        return None
    
    def format_document(self, file_path, callback=None):
        """Formata documento via LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            return self.lsp_client.format_document(file_path, callback)
        return None
    
    def shutdown(self):
        """Finaliza LSP"""
        if self.lsp_client:
            self.lsp_client.shutdown()


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
            
# ===== CLASSE EDITORTAB =====
# ===== CLASSE EDITORTAB CORRIGIDA =====
class EditorTab(QWidget):

    def __init__(self, file_path=None, parent=None):
        super().__init__(parent)
        
        self.file_path = file_path
        self.scope_header = None
        self.setup_editor()
        self.setup_ui()
        self.setup_scope_header()
        self.setup_indicators()
        self.editor.cursorPositionChanged.connect(self.update_scope_indicator)

    # No EditorTab.setup_editor():
    def setup_editor(self):
        self.editor = EnhancedCodeEditor(
            text="",
            cursor_position=0,
            file_path=self.file_path,
            project_path=getattr(self.get_ide(), 'project_path', ''),
            parent=self
        )
            
        # Configurações básicas do editor
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setTabStopDistance(40)  # 4 espaços equivalente
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Configurar highlight de sintaxe
        if self.file_path and self.file_path.endswith('.py'):
            self.highlighter = PythonHighlighter(self.editor.document())
        
        # Carregar conteúdo do arquivo se existir
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor.setPlainText(content)
            except Exception as e:
                print(f"Erro ao carregar arquivo: {e}")

    def setup_ui(self):
        """Configura a interface do usuário"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        self.setLayout(layout)

    def setup_indicators(self):
        """Configura todos os indicadores visuais"""
        # Destacar linha atual de forma mais visível
        palette = self.editor.palette()
        palette.setColor(QPalette.Highlight, QColor("#569cd6"))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.editor.setPalette(palette)
        
        # Conectar sinais para indicadores em tempo real
        self.editor.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.editor.textChanged.connect(self.on_text_changed)

    def setup_linting(self):
        """Configura o sistema de linting"""
        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.timeout.connect(self.start_linting)
        self.is_linting = False
        self.pending_lint = False
        self.linter_worker = None
        self.last_lint_content = self.editor.toPlainText()

        # Conectar sinal de texto alterado para linting
        self.editor.textChanged.connect(self.schedule_linting)
    def update_scope_header(self, current_class, current_function):
        """Atualiza o header de escopo de forma inteligente"""
        if not self.scope_header:
            return
            
        # Sempre atualiza os dados
        self.scope_header.update_scope(current_class, current_function)
        
        # Mostra/oculta baseado na relevância
        if current_class != "Global" or current_function != "Nenhuma":
            self.scope_header.show_scope()
        else:
            self.scope_header.hide_scope()
    def on_cursor_position_changed(self):
        """Chamado quando o cursor se move - ATUALIZADO"""
        try:
            cursor = self.editor.textCursor()
            line = cursor.blockNumber() + 1
            
            # Atualiza informações de escopo
            current_class = self.find_current_class(line)
            current_function = self.find_current_function(line)
            
            # Atualiza header de escopo
            self.update_scope_header(current_class, current_function)
            
            # Remove a chamada problemática
            # self.update_scope_indicator()  # REMOVER ESTA LINHA
            
        except Exception as e:
            print(f"Erro na mudança de cursor: {e}")

            

    def update_line_column_info(self, line, column):
        """Atualiza informações de linha e coluna"""
        ide = self.get_ide()
        if ide and hasattr(ide, 'cursor_info_label'):
            ide.cursor_info_label.setText(f"Linha: {line}, Coluna: {column}")
        
    def on_text_changed(self):
        """Quando texto é modificado - VERSÃO MAIS SENSÍVEL"""
        self.is_modified = True
        
        # Dispara autocomplete mais rapidamente para letras únicas
        current_char = self.get_char_before_cursor()
        if current_char.isalpha() and len(current_char) == 1:
            self.autocomplete_timer.start(100)  # Reduzido para 100ms
        elif current_char in ['.', '_'] or current_char.isalnum():
            self.autocomplete_timer.start(300)

    def setup_scope_header(self):
        """Configura o header flutuante de escopo"""
        self.scope_header = ScopeHeaderWidget(self)
        
        # Posiciona no topo do editor
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.scope_header)
        
        # Layout principal que inclui header e editor
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.editor)
        
        self.setLayout(main_layout)
        
        # Inicialmente oculto - só mostra quando relevante
        self.scope_header.hide()
    def setup_scope_indicator(self):
        """Configura o indicador de escopo"""
        self.scope_indicator = ScopeIndicatorWidget()
        
        # Adiciona ao layout do editor
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scope_indicator)
        main_layout.addWidget(self.editor)
        
        # Substitui o layout atual
        if self.layout():
            QWidget().setLayout(self.layout())
        self.setLayout(main_layout)       

    def find_current_class(self, current_line):
        """Encontra a classe atual baseada na posição do cursor"""
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        current_class = "Global"
        for i in range(current_line - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                class_match = re.match(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if class_match:
                    current_class = class_match.group(1)
                    break
                    get_unified_suggestions
        return current_class

    def find_current_function(self, current_line):
        """Encontra a função atual baseada na posição do cursor"""
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        current_function = "Nenhuma"
        for i in range(current_line - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                func_match = re.match(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if func_match:
                    current_function = func_match.group(1)
                    break
                    
        return current_function


    def setup_navigation_panel(self):
        """Configura painel de navegação lateral"""
        # Criar um widget lateral com a estrutura do código
        self.nav_panel = QListWidget()
        self.nav_panel.itemClicked.connect(self.navigate_to_item)
        
        # Layout principal
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.nav_panel, 1)
        main_layout.addWidget(self.editor, 4)
        
        # Aplicar layout
        if self.layout():
            # Se já tem layout, limpar e adicionar novo
            QWidget().setLayout(self.layout())
        self.setLayout(main_layout)
        
        # Atualizar painel inicialmente
        self.update_navigation_panel()

    def update_navigation_panel(self):
        """Atualiza o painel de navegação com a estrutura do código"""
        if not hasattr(self, 'nav_panel'):
            return
            
        self.nav_panel.clear()
        text = self.editor.toPlainText()
        
        for i, line in enumerate(text.split('\n')):
            line = line.strip()
            if line.startswith('class '):
                class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                item = QListWidgetItem(f"📦 {class_name}")
                item.setData(Qt.UserRole, i)
                self.nav_panel.addItem(item)
            elif line.startswith('def '):
                func_name = line.split('def ')[1].split('(')[0].strip()
                item = QListWidgetItem(f"  📋 {func_name}")
                item.setData(Qt.UserRole, i)
                self.nav_panel.addItem(item)

    def navigate_to_item(self, item):
        """Navega para o item clicado no painel de navegação"""
        line_number = item.data(Qt.UserRole)
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.Down)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def highlight_current_scope(self, current_line):
        """Destaca o escopo atual (classe/função) - implementação simplificada"""
        # Em QPlainTextEdit, podemos usar seleção temporária
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        
        # Apenas para demonstração - em produção você implementaria
        # um sistema mais sofisticado de highlight
        pass

    def find_current_scope(self, current_line):
        """Encontra o escopo atual baseado na indentação"""
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        if current_line > len(lines):
            return None, None
            
        # Encontrar linha de início do escopo (class/def)
        start_line = current_line - 1
        for i in range(current_line - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith(('class ', 'def ')) and not line.startswith('#'):
                start_line = i
                break
        
        # Encontrar fim do escopo baseado na indentação
        if start_line < len(lines):
            start_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
            end_line = start_line
            
            for i in range(start_line + 1, len(lines)):
                line = lines[i]
                if line.strip():  # Linha não vazia
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= start_indent and not line.strip().startswith('#'):
                        break
                end_line = i
                
            return start_line, end_line
            
        return None, None

    # ===== MÉTODOS DE LINTING =====
    
    def schedule_linting(self):
        """Schedule linting com debounce melhorado"""
        current_content = self.editor.toPlainText()

        if (current_content != self.last_lint_content and
                self.file_path and
                self.file_path.endswith('.py')):

            if self.is_linting:
                self.pending_lint = True
            else:
                self.lint_timer.start(2000)

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
        self.linter_worker.finished.connect(self.on_linting_finished)
        self.linter_worker.start()

    def on_linting_finished(self, errors, lint_messages):
        """Finaliza linting e verifica se precisa relintar"""
        self.is_linting = False

        if self.pending_lint:
            self.pending_lint = False
            self.schedule_linting()

        # Aplicar erros (implementação simplificada)
        print(f"Linting finished: {len(lint_messages)} messages")

        # Update problems list no IDE pai
        ide = self.get_ide()
        if ide and hasattr(ide, 'problems_list'):
            ide.problems_list.clear()
            for msg in lint_messages:
                item = QListWidgetItem(msg)
                ide.problems_list.addItem(item)

    def get_ide(self):
        """Find and return the parent IDE instance"""
        parent = self.parent()
        while parent and not hasattr(parent, 'project_path'):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent

    # ===== MÉTODOS DE ARQUIVO =====
    
    def save_file(self):
        """Salva o arquivo"""
        if not self.file_path:
            return self.save_file_as()
            
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.last_lint_content = self.editor.toPlainText()
            return True
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
            return False
            
    def save_file_as(self):
        """Salva o arquivo com novo nome"""
        ide = self.get_ide()
        if not ide:
            return False
            
        new_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Como",
            getattr(ide, 'project_path', '') or QDir.homePath(),
            "Todos os Arquivos (*.*)"
        )
        
        if new_path:
            self.file_path = new_path
            result = self.save_file()
            
            if result and ide:
                self.update_tab_title()
            return result
            
        return False
        
    def update_tab_title(self):
        """Atualiza o título da aba"""
        ide = self.get_ide()
        if not ide or not hasattr(ide, 'tab_widget'):
            return
            
        index = ide.tab_widget.indexOf(self)
        if index >= 0:
            base_name = os.path.basename(self.file_path) if self.file_path else "Novo Arquivo"
            ide.tab_widget.setTabText(index, base_name)
            
    def is_modified(self):
        """Verifica se o arquivo foi modificado"""
        current_content = self.editor.toPlainText()
        return current_content != self.last_lint_content
        
    def get_content(self):
        """Retorna o conteúdo do editor"""
        return self.editor.toPlainText()
        
    def set_content(self, content):
        """Define o conteúdo do editor"""
        self.editor.setPlainText(content)

    def get_current_editor(self):
        """Retorna o editor deste tab"""
        return self.editor


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        return QSize(self.editor.line_number_width, 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

class UnifiedCodeEditor(QPlainTextEdit):
    
    def __init__(self, text="", cursor_position=0, file_path="", project_path="", parent=None):
        super().__init__(parent)
        
        self.file_path = file_path
        self.project_path = project_path
        self.is_modified = False
        self.current_theme = "Dark Professional"
        
        # Configuração básica
        self.setPlainText(text)
        cursor = self.textCursor()
        cursor.setPosition(min(cursor_position, len(text)))
        self.setTextCursor(cursor)       
        
        # ===== CONFIGURAÇÕES BÁSICAS =====
        self.setup_basic_settings()
        
        # ===== SISTEMA DE NÚMEROS DE LINHA =====
        self.setup_line_numbers()
        
        # ===== SISTEMA DE FOLDING =====
        self.setup_code_folding()
        
        # ===== SISTEMA DE AUTOCOMPLETE =====
        self.setup_autocomplete_system()
        
        # ===== SYNTAX HIGHLIGHTING =====
        self.setup_syntax_highlighting()
        
        # ===== SISTEMA DE INDICADORES VISUAIS =====
        self.setup_visual_indicators()
        
        # ===== SISTEMA LSP =====
        self.lsp_manager = None
        self.lsp_completions = []
        
        # ===== CONEXÕES DE SINAIS =====
        self.setup_signal_connections()
        
        # ===== CONFIGURAÇÕES FINAIS =====
        self.setup_final_settings()
        
        print(f"✅ Editor Unificado criado para: {file_path}")
    def get_suggestions(self, code, cursor_position, file_path="", project_path=""):
        """Método principal unificado para obter todas as sugestões"""
        try:
            context = self._analyze_context(code, cursor_position, file_path)
            suggestions = self._get_hierarchical_suggestions(context)
            filtered_suggestions = self._filter_and_prioritize(suggestions, context)
            return filtered_suggestions[:25]  # ← APENAS ESTE RETURN
        except Exception as e:
            print(f"❌ Erro no sistema unificado: {e}")
            return self
    
    def setup_autocomplete_system(self):
        """Configura sistema completo de autocomplete"""
        # Timer para autocomplete automático
        self.autocomplete_timer = QTimer(self)
        self.autocomplete_timer.setSingleShot(True)
        self.autocomplete_timer.timeout.connect(self.show_autocomplete)
        
        # Widget de autocomplete flutuante
        self.autocomplete_widget = FloatingAutoCompleteWidget()
        
        # Completador inteligente
        self.completer = HybridCompleter()
        
        # Variáveis de controle
        self.last_key_pressed = None
        self.force_show_autocomplete = False
        
        print("✅ Sistema de autocomplete configurado")
    def _get_fallback_suggestions(self):
        """Sugestões de fallback mínimas e seguras"""
        return [
            "print", "def", "class", "if", "else", "for", "while", "import", 
            "from", "return", "True", "False", "None", "len", "str", "list", 
            "dict", "range", "type", "isinstance"
        ]
        # REMOVER: get_unified_suggestions  # ← SE HOUVER ESTA LINHA, REMOVER
        
    
    def setup_basic_settings(self):
        """Configurações básicas do editor"""
        # Fonte e tabulação
        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(40)  # 4 espaços
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Habilitar undo/redo
        self.setUndoRedoEnabled(True)
        self.document().setModified(False)
        
        # Configurar margens
        self.setViewportMargins(50, 0, 0, 0)

    def setup_line_numbers(self):
        """Configura sistema de números de linha"""
        self.line_number_area = LineNumberArea(self)
        self.line_number_width = 0
        
        # Conectar sinais para atualizar números
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)
    def get_enhanced_suggestions(self):
        """Obtém sugestões melhoradas de forma unificada"""
        suggestions = set()
        
        try:
            # 1. Palavras-chave da linguagem atual
            language_keywords = self.get_language_keywords()
            suggestions.update(language_keywords)
            
            # 2. Definições locais do arquivo
            local_definitions = self.extract_local_definitions()
            suggestions.update(local_definitions)
            
            # 3. Módulos do projeto (se disponível)
            if hasattr(self, 'project_path') and self.project_path:
                project_modules = self.get_project_modules()
                suggestions.update(project_modules)
                
            # 4. Sugestões do sistema de autocomplete base
            base_suggestions = self.get_suggestions_for_autocomplete()
            if base_suggestions:
                suggestions.update(base_suggestions)
            
            # 5. Remove duplicatas e limita resultados
            unique_suggestions = sorted(list(suggestions))
            return unique_suggestions[:10000]  # Limita a 25 sugestões
            
        except Exception as e:
            print(f"❌ Erro no enhanced suggestions: {e}")
            return self._get_fallback_suggestions()
    def setup_code_folding(self):
        """Configura sistema de folding de código"""
        self.folding_area = CodeFoldingArea(self)
        
        # Conectar sinal para atualizar folding
        self.updateRequest.connect(self.update_folding_area)

    def show_autocomplete(self):
        """Mostra sugestões de autocomplete - VERSÃO FINAL CORRIGIDA"""
        if not self.autocomplete_widget.enabled:
            return
            
        try:
            # Usa o sistema unificado de sugestões
            suggestions = self.get_unified_suggestions()  # JÁ CORRETO
            
            if suggestions:
                cursor_rect = self.cursorRect()
                self.autocomplete_widget.show_completions(self, suggestions, cursor_rect.bottomLeft())
                
        except Exception as e:
            print(f"❌ Erro crítico no autocomplete: {e}")
            # Tenta fallback básico em caso de erro crítico
            try:
                basic_suggestions = self._get_fallback_suggestions()
                if basic_suggestions:
                    cursor_rect = self.cursorRect()
                    self.autocomplete_widget.show_completions(self, basic_suggestions, cursor_rect.bottomLeft())
            except Exception as e2:
                print(f"❌ Erro até no fallback: {e2}")
                
    def setup_syntax_highlighting(self):
            """Configura syntax highlighting"""
            if self.file_path and self.file_path.endswith('.py'):
                self.highlighter = PythonHighlighter(self.document())
            else:
                # Highlighter genérico para outras linguagens
                language = self.detect_language()
                self.highlighter = AdvancedSyntaxHighlighter(self.document(), language)                

    def setup_visual_indicators(self):
        """Configura indicadores visuais"""
        self.code_indicators = CodeIndicators(self)
        
        # Highlight da linha atual
        self.highlight_current_line()
    
    def setup_signal_connections(self):
        """Configura todas as conexões de sinais"""
        # Sinais básicos
        self.textChanged.connect(self.on_text_changed)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.selectionChanged.connect(self.on_selection_changed)
        
        # Sinais para funcionalidades avançadas
        self.textChanged.connect(self.on_text_changed_for_outline)
        self.textChanged.connect(self.on_text_changed_for_lsp)
        self.cursorPositionChanged.connect(self.on_cursor_changed_for_lsp)

    def setup_final_settings(self):
        """Configurações finais"""
        # Menu de contexto
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Espaçamento entre linhas
        self.setup_line_spacing()

    # ===== MÉTODOS DE NUMERAÇÃO DE LINHAS =====
    
    def line_number_area_width(self):
        """Calcula largura da área de números"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, new_block_count):
        """Atualiza largura da área de números"""
        self.line_number_width = self.line_number_area_width()
        self.setViewportMargins(self.line_number_width + 16, 0, 0, 0)  # +16 para folding

    def update_line_number_area(self, rect, dy):
        """Atualiza área de números quando texto é rolado"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

    def line_number_area_paint_event(self, event):
        """Pinta os números de linha"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(30, 30, 40))
        
        font = self.font()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor(150, 150, 150))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0, int(top), 
                    self.line_number_area.width() - 5, 
                    self.fontMetrics().height(),
                    Qt.AlignRight, number
                )
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    # ===== MÉTODOS DE FOLDING =====
    
    def update_folding_area(self, rect, dy):
        """Atualiza área de folding quando texto é rolado"""
        if dy:
            self.folding_area.scroll(0, dy)
        else:
            self.folding_area.update(0, rect.y(), self.folding_area.width(), rect.height())

    # ===== MÉTODOS DE AUTOCOMPLETE =====
    
    def on_text_changed(self):
        """Quando texto é modificado"""
        self.is_modified = True
        
        # Dispara autocomplete
        current_char = self.get_char_before_cursor()
        if current_char in ['.', '_'] or current_char.isalnum():
            self.autocomplete_timer.start(300)

    def get_char_before_cursor(self):
        """Obtém caractere antes do cursor"""
        cursor = self.textCursor()
        if cursor.position() > 0:
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
            return cursor.selectedText()
        return ""
    
    
    
            

    def _get_language_keywords(self):
        """Retorna palavras-chave específicas da linguagem - MÉTODO ADICIONADO"""
        language = self.get_language()
        
        keywords_map = {
            'python': [
                "False", "None", "True", "and", "as", "assert", "async", "await",
                "break", "class", "continue", "def", "del", "elif", "else", "except",
                "finally", "for", "from", "global", "if", "import", "in", "is",
                "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
                "try", "while", "with", "yield"
            ],
            'javascript': [
                "break", "case", "catch", "class", "const", "continue", "debugger",
                "default", "delete", "do", "else", "export", "extends", "finally",
                "for", "function", "if", "import", "in", "instanceof", "new",
                "return", "super", "switch", "this", "throw", "try", "typeof",
                "var", "void", "while", "with", "yield", "await"
            ],
            'html': [
                "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6", "a", "img",
                "ul", "ol", "li", "table", "tr", "td", "th", "form", "input", "button"
            ],
            'css': [
                "color", "background", "font", "margin", "padding", "border",
                "width", "height", "display", "position", "float", "clear"
            ]
        }
        
        return keywords_map.get(language, [])
    def _extract_local_definitions(self):
        """Extrai definições locais do código atual - MÉTODO ADICIONADO"""
        definitions = set()
        try:
            code = self.toPlainText()
            
            # Funções
            functions = re.findall(r'def\s+(\w+)', code)
            definitions.update([f"{f}()" for f in functions])
            
            # Classes
            classes = re.findall(r'class\s+(\w+)', code)
            definitions.update(classes)
            
            # Variáveis (nomes com mais de 2 caracteres)
            variables = re.findall(r'(\b[a-zA-Z_][a-zA-Z0-9_]{2,})\b\s*=', code)
            definitions.update(variables)
            
        except Exception as e:
            print(f"Erro extrair definições: {e}")
        
        return definitions

    def get_current_word(self, text_before):
        """Extrai a palavra atual sendo digitada"""
        try:
            # Encontra o início da palavra atual
            word_chars = []
            for char in reversed(text_before):
                if char.isalnum() or char in ['_', '.']:
                    word_chars.append(char)
                else:
                    break
            
            return ''.join(reversed(word_chars)) if word_chars else ""
        except:
            return ""
    
    def _get_project_modules(self):
        """Método auxiliar para compatibilidade"""
        return self.get_project_modules()
        
    def get_basic_suggestions(self):
        """Sugestões básicas de fallback"""
        suggestions = set()
        code = self.toPlainText()
        
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
        
        # Definições locais
        functions = re.findall(r'def\s+(\w+)', code)
        suggestions.update([f"{f}()" for f in functions])
        
        classes = re.findall(r'class\s+(\w+)', code)
        suggestions.update(classes)
        
        return suggestions

    # ===== MÉTODOS DE SYNTAX HIGHLIGHTING =====
    
    def detect_language(self):
        """Detecta linguagem baseada na extensão do arquivo"""
        if not self.file_path:
            return "python"
        
        extension = os.path.splitext(self.file_path)[1].lower()
        language_map = {
            '.py': 'python', '.js': 'javascript', '.html': 'html', '.css': 'css',
            '.json': 'json', '.xml': 'html', '.txt': 'text', '.md': 'markdown',
            '.yml': 'yaml', '.yaml': 'yaml', '.sql': 'sql', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby',
            '.go': 'go', '.rs': 'rust', '.swift': 'swift', '.kt': 'kotlin', '.ts': 'typescript'
        }
        return language_map.get(extension, 'text')

    # ===== MÉTODOS VISUAIS =====
    
    def highlight_current_line(self):
        """Destaca a linha atual"""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(45, 45, 48, 60)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)

    def setup_line_spacing(self):
        """Configura espaçamento entre linhas"""
        try:
            self.document().setDocumentMargin(4)
            self.setStyleSheet("QPlainTextEdit { padding: 2px; }")
        except Exception as e:
            print(f"Erro ao configurar espaçamento: {e}")

    # ===== MÉTODOS DE FORMATAÇÃO =====
    
    def fix_indentation(self):
        """Corrige indentação do código"""
        try:
            text = self.toPlainText()
            lines = text.split('\n')
            fixed_lines = []
            
            for line in lines:
                stripped = line.lstrip()
                indent_level = (len(line) - len(stripped)) // 4
                fixed_line = '    ' * indent_level + stripped
                fixed_lines.append(fixed_line)
                
            self.setPlainText('\n'.join(fixed_lines))
            
        except Exception as e:
            print(f"Erro ao corrigir indentação: {e}")

    def clean_trailing_whitespace(self):
        """Remove espaços em branco no final das linhas"""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        block = self.document().firstBlock()
        while block.isValid():
            text = block.text()
            stripped = text.rstrip()
            if text != stripped:
                cursor.setPosition(block.position())
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cursor.insertText(stripped)
            block = block.next()
        
        cursor.endEditBlock()

    # ===== MÉTODOS DE NAVEGAÇÃO =====
    
    def goto_line(self, line_number):
        """Vai para uma linha específica"""
        if line_number < 1:
            return
            
        document = self.document()
        block = document.findBlockByLineNumber(line_number - 1)
        
        if block.isValid():
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)
            self.centerCursor()

    # ===== MÉTODOS LSP =====
    
    def set_lsp_manager(self, lsp_manager):
        """Define gerenciador LSP"""
        self.lsp_manager = lsp_manager
        
        if self.file_path and lsp_manager:
            lsp_manager.open_document(self.file_path, self.toPlainText())

    def on_text_changed_for_lsp(self):
        """Notifica mudanças para LSP"""
        if self.lsp_manager and self.file_path:
            self.lsp_manager.update_document(self.file_path, self.toPlainText())

    def on_cursor_changed_for_lsp(self):
        """Processa mudanças do cursor para LSP"""
        # Implementar hover information se desejado
        pass
    def show_autocomplete(self):
        """Mostra sugestões de autocomplete - VERSÃO CORRIGIDA"""
        if not self.autocomplete_widget.enabled:
            return
            
        try:
            # Usa o sistema unificado de sugestões
            suggestions = self.get_unified_suggestions()
            
            if suggestions:
                cursor_rect = self.cursorRect()
                self.autocomplete_widget.show_completions(self, suggestions, cursor_rect.bottomLeft())
                    
        except Exception as e:
            print(f"❌ Erro crítico no autocomplete: {e}")
            # Tenta fallback básico em caso de erro crítico
            try:
                basic_suggestions = self._get_fallback_suggestions()
                if basic_suggestions:
                    cursor_rect = self.cursorRect()
                    self.autocomplete_widget.show_completions(self, basic_suggestions, cursor_rect.bottomLeft())
            except Exception as e2:
                print(f"❌ Erro até no fallback: {e2}")
        
        
    def on_text_changed_for_outline(self):
        """Atualiza outline quando texto muda"""
        if hasattr(self, 'outline_timer'):
            self.outline_timer.stop()
        else:
            self.outline_timer = QTimer()
            self.outline_timer.setSingleShot(True)
            self.outline_timer.timeout.connect(self.update_outline)
        
        self.outline_timer.start(500)

    def update_outline(self):
        """Notifica o IDE para atualizar o outline"""
        ide = self.get_ide()
        if ide and hasattr(ide, 'outline_widget'):
            ide.outline_widget.refresh_outline()

    # ===== MÉTODOS DE CONTEXTO E TECLADO =====
    
    def show_context_menu(self, position):
        """Menu de contexto personalizado"""
        menu = QMenu(self)
        
        # Ações de edição
        undo_action = menu.addAction("↶ Desfazer (Ctrl+Z)")
        undo_action.triggered.connect(self.undo)
        undo_action.setEnabled(self.document().isUndoAvailable())
        
        redo_action = menu.addAction("↷ Refazer (Ctrl+Y)")
        redo_action.triggered.connect(self.redo)
        redo_action.setEnabled(self.document().isRedoAvailable())


        
        menu.addSeparator()
        
        cut_action = menu.addAction("✂️ Recortar (Ctrl+X)")
        cut_action.triggered.connect(self.cut)
        cut_action.setEnabled(self.textCursor().hasSelection())
        
        copy_action = menu.addAction("📋 Copiar (Ctrl+C)")
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(self.textCursor().hasSelection())
        
        paste_action = menu.addAction("📝 Colar (Ctrl+V)")
        paste_action.triggered.connect(self.paste)
        
        select_all_action = menu.addAction("🔲 Selecionar tudo (Ctrl+A)")
        select_all_action.triggered.connect(self.selectAll)
        
        menu.addSeparator()
        
        # Ações específicas do editor
        fix_indent_action = menu.addAction("📐 Corrigir indentação")
        fix_indent_action.triggered.connect(self.fix_indentation)
        
        auto_complete_action = menu.addAction("🎯 Auto-completar (Ctrl+Space)")
        auto_complete_action.triggered.connect(self.show_autocomplete)
        
        menu.exec(self.mapToGlobal(position))

   
    def trigger_autocomplete(self):
        """Dispara o autocomplete após digitação - VERSÃO SIMPLIFICADA"""
        if not self.autocomplete_widget.enabled:
            return
            
        try:
            # Obtém sugestões unificadas
            suggestions = self.get_unified_suggestions()
            
            if suggestions:
                cursor_rect = self.cursorRect()
                self.autocomplete_widget.show_completions(self, suggestions, cursor_rect.bottomLeft())
                        
        except Exception as e:
            print(f"Erro no trigger_autocomplete: {e}")

    # ===== MÉTODOS UTILITÁRIOS =====

    def get_ide(self):
        """Encontra a instância do IDE pai"""
        parent = self.parent()
        while parent and not hasattr(parent, 'project_path'):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent
    def get_filtered_suggestions(self, current_char):
        """Obtém sugestões filtradas pela letra inicial"""
        all_suggestions = self.get_suggestions_for_autocomplete()
        
        if not current_char or len(current_char) != 1:
            return all_suggestions
            
        # Filtra sugestões que começam com a letra (case insensitive)
        filtered = [s for s in all_suggestions if s.lower().startswith(current_char.lower())]
        
        # Se não encontrou sugestões específicas, mostra todas
        if not filtered and current_char.isalpha():
            return all_suggestions
            
        return filtered
    
    def on_cursor_position_changed(self):
        """Quando posição do cursor muda"""
        self.highlight_current_line()
        self.update_status_info()

    def on_selection_changed(self):
        """Quando seleção muda"""
        if hasattr(self, 'code_indicators'):
            self.code_indicators.highlight_matching_words()

    def update_status_info(self):
        """Atualiza informações na barra de status"""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        
        ide = self.get_ide()
        if ide and hasattr(ide, 'cursor_info_label'):
            ide.cursor_info_label.setText(f"Linha: {line}, Coluna: {column}")

    def resizeEvent(self, event):
        """Redimensiona áreas de números e folding"""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        
        # Área de folding (esquerda)
        self.folding_area.setGeometry(
            QRect(cr.left(), cr.top(), 16, cr.height())
        )
        
        # Área de números de linha (ao lado do folding)
        self.line_number_area.setGeometry(
            QRect(cr.left() + 16, cr.top(), self.line_number_width, cr.height())
        )
    def get_language_keywords(self):
        """Retorna palavras-chave específicas da linguagem"""
        language = self.get_language()
        
        keywords_map = {
            'python': [
                "False", "None", "True", "and", "as", "assert", "async", "await",
                "break", "class", "continue", "def", "del", "elif", "else", "except",
                "finally", "for", "from", "global", "if", "import", "in", "is",
                "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
                "try", "while", "with", "yield"
            ],
            'javascript': [
                "break", "case", "catch", "class", "const", "continue", "debugger",
                "default", "delete", "do", "else", "export", "extends", "finally",
                "for", "function", "if", "import", "in", "instanceof", "new",
                "return", "super", "switch", "this", "throw", "try", "typeof",
                "var", "void", "while", "with", "yield", "await"
            ],
            'html': [
                "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6", "a", "img",
                "ul", "ol", "li", "table", "tr", "td", "th", "form", "input", "button"
            ],
            'css': [
                "color", "background", "font", "margin", "padding", "border",
                "width", "height", "display", "position", "float", "clear"
            ]
        }
        
        return keywords_map.get(language, [])

    def extract_local_definitions(self):
        """Extrai definições locais do código atual - MÉTODO SEGURO"""
        definitions = set()
        try:
            code = self.toPlainText()
            
            # Funções
            functions = re.findall(r'def\s+(\w+)', code)
            definitions.update([f"{f}()" for f in functions])
            
            # Classes
            classes = re.findall(r'class\s+(\w+)', code)
            definitions.update(classes)
            
        except Exception as e:
            print(f"Erro extrair definições: {e}")
        
        return definitions
    def get_project_modules(self):
            """Obtém módulos do projeto atual - MÉTODO SEGURO"""
            modules = set()
            try:
                if not self.project_path or not os.path.exists(self.project_path):
                    return modules
                    
                # Busca por arquivos Python no projeto
                for root, dirs, files in os.walk(self.project_path):
                    # Ignora diretórios comuns
                    if '__pycache__' in dirs:
                        dirs.remove('__pycache__')
                    if '.git' in dirs:
                        dirs.remove('.git')
                    if 'venv' in dirs:
                        dirs.remove('venv')
                    
                    for file in files:
                        if file.endswith('.py') and not file.startswith('__'):
                            # Calcula nome do módulo
                            rel_path = os.path.relpath(os.path.join(root, file), self.project_path)
                            module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                            
                            # Remove __init__ do final se for pacote
                            if module_name.endswith('.__init__'):
                                module_name = module_name[:-9]
                                
                            modules.add(module_name)
                            
            except Exception as e:
                print(f"Erro buscar módulos projeto: {e}")
                
            return modules
    def get_language(self):
        """Obtém a linguagem do arquivo atual"""
        if not self.file_path:
            return "python"
        
        extension = os.path.splitext(self.file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.html': 'html',
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
    
    def keyPressEvent(self, event):
        """Manipula eventos de teclado unificados"""
        try:
            key = event.key()
            modifiers = event.modifiers()
            text = event.text()
            
            # Captura a tecla pressionada
            self.last_key_pressed = key
            
            # Ctrl+Space - Força autocomplete
            if modifiers == Qt.ControlModifier and key == Qt.Key_Space:
                self.force_show_autocomplete = True
                self.show_autocomplete()
                event.accept()
                return
                
            # Ctrl+I - Corrige indentação
            elif modifiers == Qt.ControlModifier and key == Qt.Key_I:
                self.fix_indentation()
                event.accept()
                return  
                
            # Escape - desativa autocomplete temporariamente
            elif key == Qt.Key_Escape:
                if self.autocomplete_widget.isVisible():
                    self.autocomplete_widget.hide()
                    event.accept()
                    return
                # Se autocomplete não está visível, reativa para próxima letra
                self.autocomplete_widget.set_enabled(True)
                
            # Letras e caracteres que devem ativar autocomplete
            elif (len(text) == 1 and 
                (text.isalpha() or text in ['.', '_']) and 
                self.autocomplete_widget.enabled):
                
                # Processa a tecla normalmente primeiro
                super().keyPressEvent(event)
                
                # CORREÇÃO: Usar o método correto
                QTimer.singleShot(50, self.trigger_autocomplete)
                return
                
            # Enter/Tab com autocomplete visível
            elif key in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab]:
                if self.autocomplete_widget.isVisible():
                    self.autocomplete_widget.insert_completion()
                    event.accept()
                    return
                    
            # Teclas normais
            super().keyPressEvent(event)
            
            # Para outras teclas, esconde o autocomplete
            if self.autocomplete_widget.isVisible():
                self.autocomplete_widget.hide()
            
        except Exception as e:
            print(f"Erro no keyPressEvent: {e}")
            super().keyPressEvent(event)
class UnifiedSuggestionSystem:
    """Sistema unificado e hierárquico de sugestões"""
    
    def __init__(self, editor):
        self.editor = editor
        self.cache = {}
        self.usage_stats = {}  # Estatísticas de uso para priorização
        
    def get_suggestions(self, code, cursor_position, file_path="", project_path=""):
        """Método principal unificado para obter todas as sugestões"""
        try:
            # Análise do contexto atual
            context = self._analyze_context(code, cursor_position, file_path)
            
            # Obtém sugestões hierárquicas
            suggestions = self._get_hierarchical_suggestions(context)
            
            # Aplica filtros e priorização
            filtered_suggestions = self._filter_and_prioritize(suggestions, context)
            
            return filtered_suggestions[:25]  # Limita a 25 sugestões
            show_autocomplete
        except Exception as e:
            print(f"❌ Erro no sistema unificado: {e}")
            return self._get_fallback_suggestions()
    
    def _analyze_context(self, code, cursor_position, file_path):
        """Analisa completamente o contexto do código"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        current_line = lines[current_line_index] if current_line_index < len(lines) else ""
        
        return {
            # Informações básicas
            'current_line': current_line.strip(),
            'current_word': self._get_current_word(code, cursor_position),
            'current_indent': len(current_line) - len(current_line.lstrip()),
            'file_extension': os.path.splitext(file_path or '')[1].lower(),
            
            # Contexto estrutural
            'inside_function': self._is_inside_function(code, cursor_position),
            'inside_class': self._is_inside_class(code, cursor_position),
            'function_name': self._get_current_function(code, cursor_position),
            'class_name': self._get_current_class(code, cursor_position),
            
            # Contexto sintático
            'after_import': any(keyword in current_line for keyword in ['import', 'from']),
            'after_dot': current_line.rstrip().endswith('.'),
            'after_def': 'def ' in current_line,
            'after_class': 'class ' in current_line,
            
            # Projeto
            'project_path': project_path,
            'file_path': file_path
        }
    
    def _get_hierarchical_suggestions(self, context):
        """Obtém sugestões hierárquicas baseadas no contexto"""
        suggestions = set()
        
        # Nível 1: Palavras-chave da linguagem
        suggestions.update(self._get_language_keywords(context))
        
        # Nível 2: Funções built-in
        suggestions.update(self._get_builtin_functions(context))
        
        # Nível 3: Definições locais do arquivo
        suggestions.update(self._get_local_definitions(context))
        
        # Nível 4: Sugestões contextuais
        suggestions.update(self._get_contextual_suggestions(context))
        
        # Nível 5: Módulos e imports
        suggestions.update(self._get_module_suggestions(context))
        
        # Nível 6: Completamento de código
        suggestions.update(self._get_code_completion_suggestions(context))
        
        return suggestions
    
    def _get_language_keywords(self, context):
        """Palavras-chave específicas da linguagem"""
        language = self._get_language_from_extension(context['file_extension'])
        
        keywords_map = {
            'python': [
                # Controle de fluxo
                "if", "else", "elif", "for", "while", "break", "continue",
                "return", "yield", "pass", "raise", "try", "except", "finally",
                
                # Definições
                "def", "class", "lambda",
                
                # Escopo
                "global", "nonlocal", "with", "as",
                
                # Importação
                "import", "from",
                
                # Operadores lógicos
                "and", "or", "not", "is", "in",
                
                # Valores especiais
                "True", "False", "None",
                
                # Assincronia
                "async", "await"
            ],
            'javascript': [
                "function", "var", "let", "const", "if", "else", "for", "while",
                "return", "class", "import", "export", "try", "catch", "finally"
            ],
            'html': ["div", "span", "p", "h1", "button", "input", "form", "table"],
            'css': [".class", "#id", "color", "font-size", "margin", "padding"]
        }
        
        return keywords_map.get(language, [])
    
    def _get_builtin_functions(self, context):
        """Funções built-in da linguagem"""
        language = self._get_language_from_extension(context['file_extension'])
        
        if language == 'python':
            return [
                # E/S e sistema
                "print()", "input()", "open()", "len()", "type()", "isinstance()",
                
                # Conversão de tipos
                "str()", "int()", "float()", "list()", "dict()", "set()", "tuple()",
                
                # Matemática
                "abs()", "sum()", "min()", "max()", "round()", "range()",
                
                # Iteração
                "enumerate()", "zip()", "map()", "filter()", "sorted()", "reversed()",
                
                # Objetos e atributos
                "getattr()", "setattr()", "hasattr()", "dir()", "vars()",
                
                # Arquivos e sistema
                "os.path.join()", "os.listdir()", "json.loads()", "json.dumps()"
            ]
        
        return []
    
    def _get_local_definitions(self, context):
        """Definições locais do arquivo atual"""
        definitions = set()
        
        if not context.get('file_path') or not os.path.exists(context['file_path']):
            return definitions
        
        try:
            with open(context['file_path'], 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Funções
            functions = re.findall(r'def\s+(\w+)', code)
            definitions.update([f"{f}()" for f in functions])
            
            # Classes
            classes = re.findall(r'class\s+(\w+)', code)
            definitions.update(classes)
            
            # Variáveis (nomes significativos)
            variables = re.findall(r'(\b[a-zA-Z_][a-zA-Z0-9_]{2,})\b\s*=', code)
            definitions.update(variables)
            
        except Exception as e:
            print(f"Erro ao extrair definições locais: {e}")
        
        return definitions
    
    def _get_contextual_suggestions(self, context):
        """Sugestões baseadas no contexto específico"""
        suggestions = set()
        current_line = context['current_line']
        
        # Após import/from
        if context['after_import']:
            suggestions.update(self._get_import_suggestions(context))
        
        # Após ponto (métodos/atributos)
        if context['after_dot']:
            suggestions.update(self._get_dot_suggestions(context))
        
        # Padrões específicos de linha
        patterns = {
            r'if\s*.*:': ['elif', 'else:'],
            r'for\s+.*\s+in\s+': ['range(', 'enumerate(', 'zip('],
            r'def\s+\w+\(\):': ['pass', 'return'],
            r'class\s+\w+': ['def __init__(self):', 'pass'],
            r'print\(': ['f"', 'end=" "', 'sep=" "'],
            r'return\s+': ['True', 'False', 'None']
        }
        
        for pattern, pattern_suggestions in patterns.items():
            if re.search(pattern, current_line):
                suggestions.update(pattern_suggestions)
        
        # Contexto de função/classe
        if context['inside_function']:
            suggestions.update(['return', 'yield', 'pass'])
        if context['inside_class']:
            suggestions.update(['self.', '__init__', '__str__'])
        
        return suggestions
    
    def _get_import_suggestions(self, context):
        """Sugestões para imports"""
        suggestions = set()
        
        # Módulos padrão Python
        stdlib_modules = [
            'os', 'sys', 'json', 're', 'datetime', 'math', 'random',
            'subprocess', 'shutil', 'glob', 'ast', 'inspect', 'importlib',
            'platform', 'time', 'pathlib', 'collections', 'itertools', 'functools',
            'typing', 'logging', 'unittest', 'threading', 'multiprocessing'
        ]
        suggestions.update(stdlib_modules)
        
        # Módulos do projeto
        if context.get('project_path'):
            project_modules = self._get_project_modules(context['project_path'])
            suggestions.update(project_modules)
        
        return suggestions
    
    def _get_dot_suggestions(self, context):
        """Sugestões após ponto (métodos/atributos)"""
        suggestions = set()
        
        # Métodos comuns de tipos básicos
        string_methods = ['.strip()', '.split()', '.join()', '.replace()', '.format()']
        list_methods = ['.append()', '.extend()', '.insert()', '.remove()', '.pop()']
        dict_methods = ['.keys()', '.values()', '.items()', '.get()', '.update()']
        
        suggestions.update(string_methods + list_methods + dict_methods)
        
        return suggestions
    
    def _get_module_suggestions(self, context):
        """Sugestões de módulos do projeto"""
        modules = set()
        
        if not context.get('project_path') or not os.path.exists(context['project_path']):
            return modules
            
        try:
            for root, dirs, files in os.walk(context['project_path']):
                # Ignora diretórios comuns
                ignore_dirs = {'__pycache__', '.git', 'venv', '.venv', 'node_modules'}
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        rel_path = os.path.relpath(os.path.join(root, file), context['project_path'])
                        module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                        
                        if module_name.endswith('.__init__'):
                            module_name = module_name[:-9]
                            
                        modules.add(module_name)
                        
        except Exception as e:
            print(f"Erro ao buscar módulos: {e}")
            
        return modules
    
    def _get_code_completion_suggestions(self, context):
        """Sugestões para completar estruturas de código"""
        suggestions = set()
        
        code_snippets = {
            'ifmain': 'if __name__ == "__main__": main()',
            'fori': 'for i in range():',
            'foritem': 'for item in :',
            'while': 'while :',
            'try': 'try:\n    \nexcept:',
            'class': 'class :',
            'function': 'def ():',
            'main': 'def main():\n    \n\nif __name__ == "__main__":\n    main()'
        }
        
        for key, snippet in code_snippets.items():
            suggestions.add(f"#{key}: {snippet}")
        
        return suggestions
    
    def _filter_and_prioritize(self, suggestions, context):
        """Filtra e prioriza sugestões baseadas no contexto"""
        current_word = context['current_word']
        all_suggestions = list(suggestions)
        
        if not current_word:
            # Sem filtro - retorna sugestões prioritárias primeiro
            return self._apply_priority_sorting(all_suggestions)
        
        # Com filtro - aplica matching inteligente
        exact_matches = [s for s in all_suggestions if s.lower().startswith(current_word.lower())]
        contains_matches = [s for s in all_suggestions if current_word.lower() in s.lower() and s not in exact_matches]
        
        # Combina e ordena
        result = exact_matches + contains_matches
        return self._apply_priority_sorting(result)
    
    def _apply_priority_sorting(self, suggestions):
        """Aplica ordenação por prioridade"""
        def priority_key(suggestion):
            if suggestion.endswith('()'):
                return 0  # Funções primeiro
            elif suggestion[0].isupper():
                return 1  # Classes
            elif suggestion.startswith('self.'):
                return 2  # Atributos/métodos
            elif suggestion in ['if', 'for', 'while', 'def', 'class']:
                return 3  # Palavras-chave estruturais
            else:
                return 4  # Outros
        
        return sorted(suggestions, key=priority_key)
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _get_language_from_extension(self, extension):
        """Determina linguagem baseada na extensão do arquivo"""
        language_map = {
            '.py': 'python', '.js': 'javascript', '.html': 'html', '.css': 'css',
            '.json': 'json', '.xml': 'html', '.txt': 'text', '.md': 'markdown',
            '.yml': 'yaml', '.yaml': 'yaml', '.sql': 'sql', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby'
        }
        return language_map.get(extension, 'text')
    
    def _get_current_word(self, code, cursor_position):
        """Extrai a palavra atual sendo digitada"""
        text_before = code[:cursor_position]
        word_chars = []
        
        for char in reversed(text_before):
            if char.isalnum() or char in ['_', '.']:
                word_chars.append(char)
            else:
                break
        
        return ''.join(reversed(word_chars)) if word_chars else ""
    
    def _is_inside_function(self, code, cursor_position):
        """Verifica se está dentro de uma função"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        current_indent = len(lines[current_line_index]) - len(lines[current_line_index].lstrip())
        
        for i in range(current_line_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                def_indent = len(lines[i]) - len(lines[i].lstrip())
                return current_indent > def_indent
            elif line and not line.startswith('#'):
                line_indent = len(lines[i]) - len(lines[i].lstrip())
                if line_indent < current_indent:
                    break
        
        return False
    
    def _is_inside_class(self, code, cursor_position):
        """Verifica se está dentro de uma classe"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        
        for i in range(current_line_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                return True
            elif line and not line.startswith('#') and not line.startswith('def '):
                break
        
        return False
    
    def _get_current_function(self, code, cursor_position):
        """Obtém o nome da função atual"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        
        for i in range(current_line_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                match = re.match(r'def\s+(\w+)', line)
                return match.group(1) if match else "Nenhuma"
        
        return "Nenhuma"
    
    def _get_current_class(self, code, cursor_position):
        """Obtém o nome da classe atual"""
        lines = code.split('\n')
        current_line_index = code[:cursor_position].count('\n')
        
        for i in range(current_line_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                match = re.match(r'class\s+(\w+)', line)
                return match.group(1) if match else "Global"
        
        return "Global"
    
    def _get_fallback_suggestions(self):
        """Sugestões de fallback mínimas e seguras"""
        return [
            "print", "def", "class", "if", "else", "for", "while", "import", 
            "from", "return", "True", "False", "None", "len", "str", "list", 
            "dict", "range", "type", "isinstance"
        ]

        get_unified_suggestions
class EnhancedCodeEditor(UnifiedCodeEditor):
    def __init__(self, text="", cursor_position=0, file_path="", project_path="", parent=None):
        super().__init__(text, cursor_position, file_path, project_path, parent)
        
        # Configurações específicas do EnhancedCodeEditor
        self.highlighting_manager = None
        self.syntax_highlighter = None
        self.code_indicators = CodeIndicators(self)
        self.lsp_manager = None
        self.lsp_completions = []
        self.minimap = None
        
        # Configurar conexões específicas
        self.setup_enhanced_connections()
        
        # Configurar syntax highlighting se houver arquivo
        if file_path and hasattr(parent, 'syntax_highlighting_manager'):
            parent.syntax_highlighting_manager.setup_editor_highlighter(self, file_path)

    def setup_enhanced_connections(self):
        """Configura conexões de sinais específicas do EnhancedCodeEditor"""
        # Conectar sinais para syntax highlighting e indicadores
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.selectionChanged.connect(self.on_selection_changed)
        self.textChanged.connect(self.on_text_changed)
        
        # Conectar sinais para LSP
        self.textChanged.connect(self._on_text_changed_for_lsp)
        self.cursorPositionChanged.connect(self._on_cursor_changed_for_lsp)

   

    def on_cursor_position_changed(self):
        """Quando a posição do cursor muda"""
        if hasattr(self, 'code_indicators'):
            self.code_indicators.highlight_current_line()
        
        # Atualiza informações na barra de status se possível
        self.update_status_info()

    def on_selection_changed(self):
        """Quando a seleção muda"""
        if hasattr(self, 'code_indicators'):
            self.code_indicators.highlight_matching_words()

    def on_text_changed(self):
        """Quando o texto é alterado"""
        self.is_modified = True

    def update_status_info(self):
        """Atualiza informações na barra de status"""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        
        # Encontra o IDE pai para atualizar a statusbar
        parent = self.parent()
        while parent and not hasattr(parent, 'statusBar'):
            parent = parent.parent()
            
        if parent and hasattr(parent, 'cursor_info_label'):
            parent.cursor_info_label.setText(f"Linha: {line}, Coluna: {column}")

    def set_highlighter(self, highlighter):
        """Define o syntax highlighter para este editor"""
        self.syntax_highlighter = highlighter

    def get_language(self):
        """Obtém a linguagem do arquivo atual"""
        if not self.file_path:
            return "python"
        
        extension = os.path.splitext(self.file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.html': 'html',
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

    # ===== MÉTODOS LSP AVANÇADOS =====
    
    def set_lsp_manager(self, lsp_manager):
        """Define o gerenciador LSP"""
        self.lsp_manager = lsp_manager
        
        # Notificar abertura do documento
        if self.file_path and lsp_manager:
            lsp_manager.open_document(self.file_path, self.toPlainText())
    
    def _on_text_changed_for_lsp(self):
        """Notifica mudanças para LSP"""
        if (self.lsp_manager and self.file_path and 
            not self.file_path.endswith('.py')):
            return
            
        content = self.toPlainText()
        if self.lsp_manager and self.file_path:
            self.lsp_manager.update_document(self.file_path, content)
    
    def _on_cursor_changed_for_lsp(self):
        """Processa mudanças do cursor para LSP (hover, etc)"""
        # Implementar hover information se desejado
        pass
    
    def get_lsp_suggestions(self):
        """Obtém sugestões via LSP"""
        if not self.lsp_manager or not self.file_path:
            return []
        
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        
        # Usar callback assíncrono
        def handle_completions(response):
            if response and 'result' in response:
                items = response['result']
                if isinstance(items, list):
                    self.lsp_completions = self._process_lsp_completions(items)
                elif isinstance(items, dict) and 'items' in items:
                    self.lsp_completions = self._process_lsp_completions(items['items'])
        
        self.lsp_manager.get_completions(self.file_path, line, column, handle_completions)
        return self.lsp_completions
    
    def _process_lsp_completions(self, items):
        """Processa itens de completion do LSP"""
        completions = []
        
        for item in items:
            if isinstance(item, dict):
                label = item.get('label', '')
                detail = item.get('detail', '')
                kind = item.get('kind', 0)
                
                # Formatar baseado no tipo
                completion_text = self._format_completion_item(label, detail, kind)
                if completion_text:
                    completions.append(completion_text)
        
        return completions
    
    def _format_completion_item(self, label, detail, kind):
        """Formata item de completion baseado no tipo"""
        # Mapear tipos LSP para representação visual
        kind_map = {
            2: f"🔹 {label}",  # Method
            3: f"🔸 {label}",  # Function  
            4: f"🗂️ {label}",  # Constructor
            5: f"📊 {label}",  # Field
            6: f"📁 {label}",  # Variable
            7: f"🏛️ {label}",  # Class
            8: f"📚 {label}",  # Interface
            9: f"📦 {label}",  # Module
            10: f"🏷️ {label}", # Property
            11: f"🔤 {label}", # Unit
            12: f"💎 {label}", # Value
            13: f"📝 {label}", # Enum
            14: f"🔑 {label}", # Keyword
            15: f"🎨 {label}", # Color
            16: f"📄 {label}", # File
            17: f"🔗 {label}", # Reference
        }
        
        return kind_map.get(kind, label)

    # ===== MÉTODOS MINIMAP =====
    
    def set_minimap(self, minimap):
        """Define o minimap associado a este editor"""
        self.minimap = minimap
        if self.minimap:
            self.minimap.set_main_editor(self)

    # ===== MÉTODOS DE AUTOCOMPLETE MELHORADOS =====
    
    


    def _get_fallback_suggestions(self):
        """Sugestões de fallback mínimas e seguras"""
        return [
            "print", "def", "class", "if", "else", "for", "while", "import", 
            "from", "return", "True", "False", "None", "len", "str", "list", 
            "dict", "range", "type", "isinstance"
        ]

    def get_unified_suggestions(self):
        """Sistema unificado de sugestões - CORREÇÃO DO MÉTODO AUSENTE"""
        try:
            # Usa o completador do IDE se disponível
            ide = self.get_ide()
            if ide and hasattr(ide, 'completer'):
                code = self.toPlainText()
                cursor_position = self.textCursor().position()
                
                suggestions = ide.completer.get_completions(
                    code, 
                    cursor_position,
                    self.file_path,
                    getattr(ide, 'project_path', "")
                )
                
                if suggestions:
                    return suggestions[:25]  # Limita a 25 sugestões
            
            # Fallback para sistema interno
            return self.get_enhanced_suggestions()
            
        except Exception as e:
            print(f"❌ Erro no unified suggestions: {e}")
            return self._get_fallback_suggestions()



    # ===== MÉTODOS DE FORMATAÇÃO AVANÇADA =====
    
    def format_code(self):
        """Formata o código automaticamente baseado na linguagem"""
        language = self.get_language()
        
        if language == 'python':
            self.format_python_code()
        elif language == 'html':
            self.format_html_code()
        elif language == 'css':
            self.format_css_code()
        elif language == 'javascript':
            self.format_javascript_code()
        else:
            # Formatação genérica
            self.fix_indentation()
            self.clean_trailing_whitespace()
    
    def format_python_code(self):
        """Formata código Python usando autopep8 ou formatação básica"""
        try:
            code = self.toPlainText()
            
            # Tenta usar autopep8 primeiro
            try:
                import autopep8
                formatted_code = autopep8.fix_code(code)
                self.setPlainText(formatted_code)
                return
            except ImportError:
                print("autopep8 não encontrado, usando formatação básica")
            
            # Fallback para formatação básica
            self.fix_indentation()
            self.clean_trailing_whitespace()
            
        except Exception as e:
            print(f"Erro ao formatar código Python: {e}")
            # Fallback absoluto
            self.fix_indentation()
    
    def format_html_code(self):
        """Formata código HTML (placeholder)"""
        self.fix_indentation()
        self.clean_trailing_whitespace()
    
    def format_css_code(self):
        """Formata código CSS (placeholder)"""
        self.fix_indentation()
        self.clean_trailing_whitespace()
    
    def format_javascript_code(self):
        """Formata código JavaScript (placeholder)"""
        self.fix_indentation()
        self.clean_trailing_whitespace()

    def clean_trailing_whitespace(self):
        """Remove espaços em branco no final das linhas"""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        # Itera por todas as linhas
        block = self.document().firstBlock()
        while block.isValid():
            text = block.text()
            stripped = text.rstrip()
            if text != stripped:
                cursor.setPosition(block.position())
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cursor.insertText(stripped)
            block = block.next()
        
        cursor.endEditBlock()

    # ===== MÉTODOS DE NAVEGAÇÃO AVANÇADA =====
    
    def goto_line(self, line_number):
        """Vai para uma linha específica"""
        if line_number < 1:
            return
            
        document = self.document()
        block = document.findBlockByLineNumber(line_number - 1)
        
        if block.isValid():
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)
            self.centerCursor()
    
    def find_next(self, text, case_sensitive=False, whole_word=False):
        """Encontra próxima ocorrência do texto"""
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords
            
        cursor = self.textCursor()
        found = self.document().find(text, cursor, flags)
        
        if not found.isNull():
            self.setTextCursor(found)
            return True
        else:
            # Busca do início
            cursor.setPosition(0)
            found = self.document().find(text, cursor, flags)
            if not found.isNull():
                self.setTextCursor(found)
                return True
        
        return False

    def replace_text(self, find_text, replace_text, replace_all=False):
        """Substitui texto no editor"""
        cursor = self.textCursor()
        
        if replace_all:
            # Substitui todas as ocorrências
            cursor.beginEditBlock()
            cursor.movePosition(QTextCursor.Start)
            
            while True:
                found = self.document().find(find_text, cursor)
                if found.isNull():
                    break
                found.insertText(replace_text)
                cursor = found
            
            cursor.endEditBlock()
        else:
            # Substitui apenas a seleção atual
            if cursor.hasSelection() and cursor.selectedText() == find_text:
                cursor.insertText(replace_text)

    # ===== MÉTODOS DE DIAGNÓSTICO =====
    
    def get_editor_info(self):
        """Retorna informações sobre o editor"""
        return {
            'type': 'EnhancedCodeEditor',
            'file_path': self.file_path,
            'language': self.get_language(),
            'line_count': self.blockCount(),
            'has_lsp': self.lsp_manager is not None,
            'has_minimap': self.minimap is not None,
            'has_syntax_highlighting': self.syntax_highlighter is not None
        }



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

    def apply_theme(self, theme_name):
        """Aplica um tema ao IDE (ATUALIZADO)"""
        theme = self.theme_manager.get_theme(theme_name)
        colors = theme["colors"]

        # Aplica o tema à interface
        self.apply_theme_to_ui(theme)

        # Aplica syntax highlighting aos editores
        self.apply_syntax_theme(theme)
        
        # Atualiza minimap
        self.update_minimap_theme()

        print(f"Tema '{theme_name}' aplicado!")


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
UnifiedCodeEditor

class SyntaxHighlightingManager:
    """Gerenciador de syntax highlighting para o IDE"""
    
    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.highlighters = {}
        self.current_language = "python"
        
    def setup_editor_highlighter(self, editor, file_path):
        """Configura syntax highlighting para um editor baseado no arquivo"""
        if not file_path:
            return
            
        language = self.detect_language(file_path)
        self.current_language = language
        
        # Remove highlighter anterior se existir
        if editor in self.highlighters:
            self.highlighters[editor].setDocument(None)
            
        # Cria novo highlighter
        highlighter = AdvancedSyntaxHighlighter(editor.document(), language)
        self.highlighters[editor] = highlighter
        
        # Aplica configurações adicionais
        self.apply_editor_settings(editor)
        
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
                highlighter.highlighting_rules.clear()
                highlighter.setup_rules()
                # Força rehighlight de todo o documento
                highlighter.rehighlight()
    
    def clear_highlighter(self, editor):
        """Remove o highlighter de um editor"""
        if editor in self.highlighters:
            self.highlighters[editor].setDocument(None)
            del self.highlighters[editor]
class CodeIndicators:
    """Sistema de indicadores visuais para o editor de código"""
    
    def __init__(self, editor):
        self.editor = editor
        self.setup_indicators()
        
    def setup_indicators(self):
        """Configura todos os indicadores visuais"""
        self.setup_line_highlight()
        self.setup_indentation_guides()
        self.setup_current_scope_highlight()
        self.setup_error_indicators()
        
    def setup_line_highlight(self):
        """Configura destaque da linha atual"""
        # Isso será conectado ao sinal cursorPositionChanged
        pass
    
    def setup_indentation_guides(self):
        """Configura guias de indentação"""
        # Guias de indentação são desenhados no paintEvent
        pass
    
    def setup_current_scope_highlight(self):
        """Configura destaque do escopo atual"""
        pass
    
    def setup_error_indicators(self):
        """Configura indicadores de erro"""
        pass
    
    def highlight_current_line(self):
        """Destaca a linha atual do cursor - CORRIGIDO"""
        try:
            extra_selections = []
            
            if not self.editor.isReadOnly():
                selection = QTextEdit.ExtraSelection()
                line_color = QColor(45, 45, 48)
                selection.format.setBackground(line_color)
                
                # CORREÇÃO: Usar a constante correta do Qt
                selection.format.setProperty(QTextFormat.FullWidthSelection, True)
                
                selection.cursor = self.editor.textCursor()
                selection.cursor.clearSelection()
                extra_selections.append(selection)
            
            self.editor.setExtraSelections(extra_selections)
        except Exception as e:
            print(f"Erro no highlight da linha: {e}")
    
    def highlight_matching_words(self):
        """Destaca palavras idênticas à seleção atual"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            if len(selected_text) > 1 and selected_text.isalnum():
                self.highlight_all_occurrences(selected_text)
    
    def highlight_all_occurrences(self, text):
        """Destaca todas as ocorrências de um texto"""
        extra_selections = []
        cursor = self.editor.textCursor()
        document = self.editor.document()
        
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(86, 156, 214, 50))  # Azul translúcido
        
        # Busca todas as ocorrências
        search_cursor = QTextCursor(document)
        while not search_cursor.isNull() and not search_cursor.atEnd():
            search_cursor = document.find(text, search_cursor)
            if not search_cursor.isNull():
                selection = QTextEdit.ExtraSelection()
                selection.format = highlight_format
                selection.cursor = search_cursor
                extra_selections.append(selection)
        
        self.editor.setExtraSelections(extra_selections)






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
                # Ignora diretórios comuns
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if '.git' in dirs:
                    dirs.remove('.git')
                if 'venv' in dirs:
                    dirs.remove('venv')
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        py_files.append(os.path.join(root, file))

            # Carrega cada um
            for py_file in py_files:
                try:
                    # Calcula nome do módulo relativo
                    rel_path = os.path.relpath(py_file, project_path)
                    module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                    
                    # Remove __init__ do final se for pacote
                    if module_name.endswith('.__init__'):
                        module_name = module_name[:-9]
                    
                    self.get_module_methods(module_name, py_file, project_path)
                except Exception as e:
                    print(f"⚠️ Erro ao preload {py_file}: {e}")

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
            except Exception as e:
                # Fallback para análise estática
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
                   'getcwd()', 'chdir()', 'remove()', 'rename()', 'system()', 'walk()'],
            'sys': ['argv', 'path', 'exit()', 'version', 'platform', 'modules', 'executable', 'stdin', 'stdout', 'stderr'],
            'json': ['loads()', 'dumps()', 'load()', 'dump()', 'JSONEncoder', 'JSONDecoder'],
            're': ['search()', 'match()', 'findall()', 'sub()', 'compile()', 'IGNORECASE', 'MULTILINE', 'DOTALL'],
            'datetime': ['datetime', 'date', 'time', 'timedelta', 'now()', 'today()', 'strftime()', 'strptime()'],
            'math': ['sqrt()', 'sin()', 'cos()', 'tan()', 'pi', 'e', 'log()', 'exp()', 'ceil()', 'floor()'],
            'random': ['random()', 'randint()', 'choice()', 'shuffle()', 'uniform()', 'seed()', 'sample()'],
            'pathlib': ['Path', 'PurePath', 'exists()', 'is_file()', 'is_dir()', 'name', 'stem', 'suffix'],
            'collections': ['deque', 'Counter', 'OrderedDict', 'defaultdict', 'namedtuple'],
            'itertools': ['chain', 'cycle', 'repeat', 'count', 'groupby', 'combinations', 'permutations'],
            'functools': ['partial', 'reduce', 'wraps', 'lru_cache'],
            'typing': ['List', 'Dict', 'Set', 'Tuple', 'Any', 'Union', 'Optional', 'Callable']
        }
        return set(builtin_methods.get(module_name, []))

    def _get_module_attributes(self, module) -> Set[str]:
        """Extrai atributos de um módulo importado"""
        attrs = set()
        try:
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    try:
                        attr = getattr(module, attr_name)
                        if callable(attr):
                            attrs.add(f"{attr_name}()")
                        else:
                            attrs.add(attr_name)
                    except (AttributeError, Exception):
                        # Ignora atributos que não podem ser acessados
                        pass
        except Exception:
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
                os.path.join(project_path, module_name.replace('.', os.sep) + ".py"),
                os.path.join(project_path, module_name.replace('.', os.sep), "__init__.py")
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
        
        # Imports para sugestões
        imports = re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update(imports)
        
        # From imports
        from_imports = re.findall(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', content)
        methods.update(from_imports)
        
        # Constantes (MAIÚSCULAS)
        constants = re.findall(r'^([A-Z_][A-Z0-9_]*)\s*=', content, re.MULTILINE)
        methods.update(constants)

        return methods

    def clear_cache(self):
        """Limpa todo o cache"""
        with self._cache_lock:
            self._module_cache.clear()
            self._project_modules.clear()
            self._last_scan_time.clear()
            self._chain_cache.clear()
            self._preload_done = False

    def get_cached_modules_count(self) -> int:
        """Retorna número de módulos em cache"""
        with self._cache_lock:
            return len(self._module_cache)

    def get_cache_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o cache"""
        with self._cache_lock:
            return {
                'total_modules': len(self._module_cache),
                'preload_done': self._preload_done,
                'project_modules': len(self._project_modules),
                'chain_cache_size': len(self._chain_cache)
            }



# Instância global do gerenciador de cache
module_cache_manager = ModuleCacheManager()

class LinterWorker(QThread):
    """Worker para execução de linter em background"""
    finished = Signal(dict, list)
    
    def __init__(self, file_path, python_exec, project_path):
        super().__init__()
        self.file_path = file_path
        self.python_exec = python_exec
        self.project_path = project_path
        self._is_running = True
        self._mutex = threading.Lock()

    def stop(self):
        """Para a thread de forma segura"""
        with self._mutex:
            self._is_running = False
        self.quit()
        self.wait(2000)

    def run(self):
        """Executa análise de linting em thread separada"""
        if not self._is_running or not self.file_path:
            return

        errors = {}
        lint_messages = []

        try:
            # Tenta pylint primeiro com enables corrigidos
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

            # Verifica se deve continuar
            with self._mutex:
                if not self._is_running:
                    return

            if result.returncode in [0, 1, 2, 4, 8, 16, 32] and result.stdout.strip():
                try:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        # Verifica se deve continuar a cada linha
                        with self._mutex:
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

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Linter error: {e}")

        # Verifica final antes de emitir
        with self._mutex:
            if self._is_running:
                self.finished.emit(errors, lint_messages)

class DebugWorker(QThread):
    """Worker para execução de debug em thread separada"""
    output_received = Signal(str)
    finished = Signal(int)
    error_occurred = Signal(str)

    def __init__(self, python_exec, file_path, project_path):
        super().__init__()
        self.python_exec = python_exec
        self.file_path = file_path
        self.project_path = project_path
        self.process = None
        self._is_running = True
        self._mutex = threading.Lock()
        self._command_queue = Queue()

    def stop(self):
        """Para a execução do debug de forma segura"""
        with self._mutex:
            self._is_running = False
            
        if self.process:
            try:
                self.process.terminate()
                if not self.process.waitForFinished(1000):
                    self.process.kill()
            except Exception as e:
                print(f"Erro ao parar processo: {e}")
                
        self.quit()
        self.wait(2000)

    def run(self):
        """Executa o debug em thread separada"""
        try:
            with self._mutex:
                if not self._is_running:
                    return
                    
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.on_finished)
            self.process.errorOccurred.connect(self.on_error)

            # Comando para debug interativo
            cmd = [self.python_exec, "-m", "pdb", self.file_path]

            # Define working directory
            working_dir = self.project_path or os.path.dirname(self.file_path)
            self.process.setWorkingDirectory(working_dir)

            # Define variáveis de ambiente se necessário
            env = QProcessEnvironment.systemEnvironment()
            self.process.setProcessEnvironment(env)

            self.output_received.emit(f"🚀 Iniciando debug: {os.path.basename(self.file_path)}")
            self.output_received.emit(f"📁 Diretório: {working_dir}")
            self.output_received.emit(f"🐍 Python: {self.python_exec}")
            self.output_received.emit("-" * 50)

            self.process.start(cmd[0], cmd[1:])

            # Aguarda o processo iniciar
            if not self.process.waitForStarted(5000):
                self.error_occurred.emit("❌ Falha ao iniciar processo de debug")
                return

            # Loop principal para processar comandos
            while True:
                with self._mutex:
                    if not self._is_running:
                        break
                    if self.process.state() != QProcess.Running:
                        break

                # Processa comandos da fila
                try:
                    command = self._command_queue.get_nowait()
                    if command:
                        self.process.write(f"{command}\n".encode('utf-8'))
                except Empty:
                    pass

                self.msleep(50)

        except Exception as e:
            error_msg = f"❌ Erro no debug: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.output_received.emit(error_msg)

    def handle_stdout(self):
        """Processa saída padrão"""
        with self._mutex:
            if not self._is_running:
                return
                
        try:
            data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if data.strip():
                self.output_received.emit(data)
        except Exception as e:
            print(f"Erro ao processar stdout: {e}")

    def handle_stderr(self):
        """Processa erro padrão"""
        with self._mutex:
            if not self._is_running:
                return
                
        try:
            data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if data.strip():
                # Marca como erro
                error_text = f"[ERRO] {data}"
                self.output_received.emit(error_text)
        except Exception as e:
            print(f"Erro ao processar stderr: {e}")

    def on_finished(self, exit_code, exit_status):
        """Processa término do processo"""
        with self._mutex:
            if self._is_running:
                self.output_received.emit(f"\n🔚 Processo de debug finalizado (código: {exit_code})")
                self.finished.emit(exit_code)

    def on_error(self, error):
        """Processa erro do processo"""
        error_msg = f"❌ Erro no processo: {error.name()}"
        self.error_occurred.emit(error_msg)
        self.output_received.emit(error_msg)

    def send_command(self, command):
        """Envia comando para o processo de debug"""
        with self._mutex:
            if not self._is_running or not self.process or self.process.state() != QProcess.Running:
                return False
                
        try:
            # Adiciona quebra de linha se necessário
            if not command.endswith('\n'):
                command += '\n'
                
            self._command_queue.put(command)
            return True
        except Exception as e:
            print(f"Erro ao enviar comando: {e}")
            return False

    def get_state(self):
        """Retorna o estado atual do worker"""
        with self._mutex:
            if not self._is_running:
                return "stopped"
            if not self.process:
                return "not_started"
            return "running" if self.process.state() == QProcess.Running else "finished"

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        return QSize(self.editor.line_number_width, 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

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

   # def paintEvent(self, event):
    #    painter = QPainter(self)
     #   painter.fillRect(event.rect(), QColor(20, 30, 48))
      #  block = self.editor.firstVisibleBlock()
      #  block_number = block.blockNumber()
     #   top = int(
    #        self.editor.blockBoundingGeometry(block).translated(
    #            self.editor.contentOffset()).top())
    #    bottom = top + \
    #             int(self.editor.blockBoundingRect(block).height())
    #    font = self.editor.font()
    #    font.setPointSize(10)
    #    painter.setFont(font)
    #    font_metrics = self.editor.fontMetrics()

     #   while block.isValid() and top <= event.rect().bottom():
     #       if block.isVisible() and bottom >= event.rect().top():
     #           number = str(
     #               block_number + 1)
     #           painter.setPen(
     #               QColor(150, 150, 150))
     #           painter.drawText(
     #              0, top, 50, font_metrics.height(), Qt.AlignRight, number)

                # Draw vertical
                # separator
      #          painter.setPen(
      #              QColor(100, 100, 100))
      #          painter.drawLine(
              #      55, top, 55, bottom)

                # Draw red line for
                # errors
       #         data = block.userData()
       #         if isinstance(data, ErrorData) and any(
       #                 error['type'] == 'error' for error in data.errors):
       #             painter.setPen(
       #                 QColor(255, 0, 0))
       #             painter.drawLine(
        #                60, top, 60, bottom)

         #   block = block.next()
         #   top = bottom
         #   bottom = top + \
          #           int(self.editor.blockBoundingRect(
          #               block).height())
          #  block_number += 1

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


class AutoCompleteWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setMaximumHeight(150)
        self.setMaximumWidth(300)
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
        
        # Conectar eventos de teclado
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Filtra eventos de teclado para o widget de autocomplete"""
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
                self.insert_current_completion()
                return True
            elif event.key() == Qt.Key_Escape:
                self.hide()
                return True
        return super().eventFilter(obj, event)

    def show_suggestions(self, editor, suggestions):
        """Mostra sugestões na posição do cursor"""
        self.current_editor = editor
        self.clear()

        if not suggestions:
            self.hide()
            return

        # Adiciona sugestões
        for suggestion in suggestions[:1000]:  # Limita a 15 sugestões
            self.addItem(suggestion)

        # Ajusta o tamanho
        self.adjustSize()

        # Posiciona o widget
        cursor_rect = editor.cursorRect()
        pos = editor.mapToGlobal(cursor_rect.bottomLeft())

        # Ajusta para não sair da tela
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        if pos.y() + self.height() > screen_geometry.bottom():
            pos = editor.mapToGlobal(cursor_rect.topLeft())
            pos.setY(pos.y() - self.height())

        if pos.x() + self.width() > screen_geometry.right():
            pos.setX(screen_geometry.right() - self.width())

        self.move(pos)
        self.show()
        self.setCurrentRow(0)

    def insert_current_completion(self):
        """Insere a sugestão atual no editor"""
        if not self.current_editor or self.currentRow() < 0:
            return

        current_item = self.currentItem()
        if current_item:
            completion = current_item.text()
            self.current_editor.insert_completion(completion)

class Minimap(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_editor = None
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setFrameShape(QFrame.NoFrame)
        
        # Configuração de fonte muito pequena para o minimap
        self.setFont(QFont("Monospace", 2))
        self.setWordWrapMode(QTextOption.NoWrap)
        
        # Cores do minimap (tema escuro)
        self.setStyleSheet("""
            Minimap {
                background-color: #1e1e1e;
                color: #858585;
                border: none;
                border-left: 1px solid #2d2d30;
            }
        """)
        
        # Área de visão atual (retângulo que mostra a região visível)
        self.viewport_rect = QRect()
        self.viewport_rect_color = QColor(100, 100, 100, 100)
        
        # Conectar eventos
        self.verticalScrollBar().valueChanged.connect(self.update_viewport_position)
        
    def set_main_editor(self, editor):
        """Define o editor principal que o minimap irá espelhar"""
        self.main_editor = editor
        if self.main_editor:
            # Conectar sinais do editor principal
            self.main_editor.verticalScrollBar().valueChanged.connect(self.update_from_main_editor)
            self.main_editor.textChanged.connect(self.update_minimap_content)
            
            # Atualizar conteúdo inicial
            self.update_minimap_content()
            
    def update_minimap_content(self):
        """Atualiza o conteúdo do minimap baseado no editor principal"""
        if not self.main_editor:
            return
            
        # Obter texto do editor principal
        main_text = self.main_editor.toPlainText()
        
        # Processar texto para o minimap (reduzir linhas muito longas)
        processed_lines = []
        lines = main_text.split('\n')
        
        for line in lines:
            if len(line) > 150:  # Limitar linhas muito longas
                processed_line = line[:147] + "..."
            else:
                processed_line = line
            processed_lines.append(processed_line)
            
        self.setPlainText('\n'.join(processed_lines))
        
        # Atualizar a posição do viewport
        self.update_viewport_position()
        
    def update_from_main_editor(self):
        """Atualiza o minimap quando o editor principal é rolado"""
        self.update_viewport_position()
        
    def update_viewport_position(self):
        """Atualiza a posição do retângulo de viewport - CORRIGIDO"""
        if not self.main_editor:
            return
            
        # Calcular proporções
        main_doc = self.main_editor.document()
        minimap_doc = self.document()
        
        if main_doc.lineCount() == 0 or minimap_doc.lineCount() == 0:
            return
            
        # Obter a região visível atual do editor principal
        main_scrollbar = self.main_editor.verticalScrollBar()
        main_max = main_scrollbar.maximum()
        main_value = main_scrollbar.value()
        
        # Calcular a proporção de rolagem
        if main_max > 0:
            scroll_ratio = main_value / main_max
        else:
            scroll_ratio = 0
            
        # Calcular altura visível proporcional
        minimap_height = self.height()
        main_visible_ratio = self.main_editor.viewport().height() / main_doc.size().height()
        viewport_height = max(minimap_height * main_visible_ratio, 20)  # Altura mínima
        
        # Calcular posição do viewport no minimap
        available_height = minimap_height - viewport_height
        viewport_top = scroll_ratio * available_height
        
        # Atualizar o retângulo do viewport
        self.viewport_rect = QRect(0, int(viewport_top), self.width(), int(viewport_height))
        self.viewport_rect_color = QColor(86, 156, 214, 80)  # Azul translúcido
        
        self.viewport().update()
        
    def paintEvent(self, event):
        """Evento de pintura personalizado para desenhar o viewport - CORRIGIDO"""
        super().paintEvent(event)
        
        # Desenhar o retângulo do viewport
        if self.viewport_rect.isValid():
            painter = QPainter(self.viewport())
            painter.fillRect(self.viewport_rect, self.viewport_rect_color)
            
            # Borda do viewport
            painter.setPen(QColor(86, 156, 214))
            painter.drawRect(self.viewport_rect)
            
    def resizeEvent(self, event):
        """Atualiza quando o minimap é redimensionado"""
        super().resizeEvent(event)
        self.update_viewport_position()
        
    def mousePressEvent(self, event):
        """Navega para a posição clicada no minimap - CORRIGIDO"""
        if event.button() == Qt.LeftButton and self.main_editor:
            self.navigate_to_click_position(event.pos())
            
    def mouseMoveEvent(self, event):
        """Permite arrastar o viewport - CORRIGIDO"""
        if event.buttons() & Qt.LeftButton and self.main_editor:
            self.navigate_to_click_position(event.pos())
            
    def wheelEvent(self, event):
        """Rola o editor principal quando roda no minimap"""
        if self.main_editor:
            # Encaminhar evento de roda para o editor principal
            self.main_editor.wheelEvent(event)
            
    def navigate_to_click_position(self, pos):
        """Navega para a posição clicada no minimap - CORRIGIDO"""
        if not self.main_editor:
            return
            
        # Calcular a posição proporcional no editor principal
        click_y = pos.y()
        minimap_height = self.height()
        
        if minimap_height <= 0:
            return
            
        click_ratio = click_y / minimap_height
        
        # Calcular nova posição de rolagem no editor principal
        main_scrollbar = self.main_editor.verticalScrollBar()
        main_max = main_scrollbar.maximum()
        new_scroll_value = int(click_ratio * main_max)
        
        # Aplicar a nova posição de rolagem
        main_scrollbar.setValue(new_scroll_value)

    def clear(self):
        """Limpa o conteúdo do minimap"""
        self.setPlainText("")


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
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        self._shell_process = None
        self._input_start = 0
        self._is_waiting_output = False
        self._command_history = []
        self._history_index = -1
        self._current_command = ""

    def set_shell_process(self, process):
        """Define o processo do shell"""
        self._shell_process = process
        self._setup_initial_prompt()

    def _setup_initial_prompt(self):
        """Configura prompt inicial"""
        self.clear()
        initial_text = "Py Dragon Terminal - Digite 'help' para ajuda\n"
        self.setPlainText(initial_text)
        self._add_prompt()
        self._move_cursor_to_end()

    def _add_prompt(self):
        """Adiciona novo prompt"""
        prompt = self._get_prompt()
        self.insertPlainText(prompt)
        self._input_start = len(self.toPlainText())
        self._move_cursor_to_end()

    def _get_prompt(self):
        """Retorna o prompt baseado no OS"""
        if os.name == 'nt':
            return "C:\\> "
        else:
            return "$ "

    def _move_cursor_to_end(self):
        """Move cursor para o final"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

    def append_output(self, data):
        """Adiciona saída do terminal - CORRIGIDO"""
        try:
            if not data.strip():
                return

            # Filtra códigos ANSI
            from re import sub
            cleaned_data = sub(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\][0-9;].*?\x07', '', data)
            
            if not cleaned_data.strip():
                return

            cursor = self.textCursor()
            current_pos = cursor.position()
            
            # Se estiver digitando, move para o final antes de adicionar output
            if current_pos < len(self.toPlainText()):
                self._move_cursor_to_end()
                cursor = self.textCursor()

            # Adiciona quebra de linha se necessário
            current_text = self.toPlainText()
            if current_text and not current_text.endswith('\n'):
                self.insertPlainText('\n')

            # Insere a saída LIMPA
            self.insertPlainText(cleaned_data.strip())
            
            # Novo prompt
            self.insertPlainText("\n")
            self._add_prompt()
            
            self._is_waiting_output = False

        except Exception as e:
            print(f"Erro em append_output: {e}")

    def keyPressEvent(self, event):
        """Handle de teclas - COMPLETAMENTE CORRIGIDO"""
        try:
            # Enter - executa comando
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if not self._is_waiting_output:
                    self._execute_command()
                event.accept()
                return
                
            # Backspace - protege prompt
            elif event.key() == Qt.Key_Backspace:
                cursor = self.textCursor()
                if cursor.position() <= self._input_start:
                    event.accept()
                    return
                else:
                    super().keyPressEvent(event)
                    
            # Setas para cima/baixo - histórico
            elif event.key() == Qt.Key_Up:
                self._navigate_history(-1)
                event.accept()
                return
            elif event.key() == Qt.Key_Down:
                self._navigate_history(1)
                event.accept()
                return
                
            # Setas esquerda/direita - protegem prompt
            elif event.key() in (Qt.Key_Left, Qt.Key_Right):
                cursor = self.textCursor()
                if event.key() == Qt.Key_Left and cursor.position() <= self._input_start:
                    event.accept()
                    return
                elif event.key() == Qt.Key_Right and cursor.position() < self._input_start:
                    event.accept()
                    return
                else:
                    super().keyPressEvent(event)

            # Ctrl+C - interrompe comando atual
            elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
                if self._shell_process and self._shell_process.state() == QProcess.Running:
                    self._shell_process.kill()
                    self.insertPlainText("^C\n")
                    self._add_prompt()
                event.accept()
                return
                
            # Ctrl+L - limpa terminal
            elif event.key() == Qt.Key_L and event.modifiers() == Qt.ControlModifier:
                self.clear()
                self._add_prompt()
                event.accept()
                return

            # Teclas normais
            else:
                super().keyPressEvent(event)
            
        except Exception as e:
            print(f"Erro no keyPressEvent: {e}")

    def _navigate_history(self, direction):
        """Navega pelo histórico de comandos"""
        if not self._command_history:
            return
            
        if self._history_index == -1:
            self._current_command = self._get_current_input()
            
        self._history_index += direction
        
        # Limita o índice ao histórico
        if self._history_index < 0:
            self._history_index = 0
        elif self._history_index >= len(self._command_history):
            self._history_index = len(self._command_history) - 1
            
        # Substitui o comando atual
        self._replace_current_input(self._command_history[self._history_index])

    def _get_current_input(self):
        """Obtém o texto atual do input"""
        full_text = self.toPlainText()
        return full_text[self._input_start:].strip()

    def _replace_current_input(self, new_text):
        """Substitui o texto atual do input"""
        cursor = self.textCursor()
        cursor.setPosition(self._input_start)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(new_text)
        self._move_cursor_to_end()

    def _execute_command(self):
        """Executa comando no shell - CORRIGIDO"""
        try:
            if not self._shell_process or self._shell_process.state() != QProcess.Running:
                self.insertPlainText("\n❌ Shell não está rodando\n")
                self._add_prompt()
                return

            # Obtém comando atual
            command = self._get_current_input()
            
            if command:
                # Adiciona ao histórico
                if command not in self._command_history:
                    self._command_history.append(command)
                self._history_index = -1
                
                # Envia comando
                self._shell_process.write(f"{command}\n".encode('utf-8'))
                self._is_waiting_output = True
                
                # Move para nova linha (o output será adicionado pelo append_output)
                self.insertPlainText("\n")
                
            else:
                # Comando vazio, apenas novo prompt
                self.insertPlainText("\n")
                self._add_prompt()
                
        except Exception as e:
            self.insertPlainText(f"\n❌ Erro ao executar comando: {e}\n")
            self._add_prompt()

    def restart_shell(self):
        """Reinicia o shell de forma segura"""
        try:
            # Para processo anterior
            if self._shell_process:
                if self._shell_process.state() == QProcess.Running:
                    self._shell_process.terminate()
                    self._shell_process.waitForFinished(1000)
                self._shell_process = None

            # Obtém referência do IDE
            ide = self.get_ide()
            if not ide:
                return

            # Cria novo processo
            ide.shell_process = QProcess(ide)
            ide.shell_process.readyReadStandardOutput.connect(ide.handle_terminal_output)
            ide.shell_process.readyReadStandardError.connect(ide.handle_terminal_error)

            # Comando baseado no OS
            if os.name == 'nt':
                ide.shell_process.start("cmd.exe")
            else:
                ide.shell_process.start("/bin/bash", ["-i"])

            # Atualiza referência
            self._shell_process = ide.shell_process
            
            # Configura prompt inicial após um delay
            QTimer.singleShot(500, self._setup_initial_prompt)

        except Exception as e:
            print(f"Erro ao reiniciar shell: {e}")

    def get_ide(self):
        """Encontra a instância do IDE pai"""
        parent = self.parent()
        while parent and not hasattr(parent, 'project_path'):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent

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

    def keyPressEvent(self, event):
        """Manipula eventos de teclado incluindo folding"""
        # Atalhos para folding
        if event.modifiers() == Qt.AltModifier:
            if event.key() == Qt.Key_Right:
                self.expand_all_folds()
                event.accept()
                return
            elif event.key() == Qt.Key_Left:
                self.collapse_all_folds()
                event.accept()
                return
        
        # Atalho para toggle folding (Alt+L)
        elif event.modifiers() == Qt.AltModifier and event.key() == Qt.Key_L:
            cursor = self.textCursor()
            block = cursor.block()
            if self.folding_area.is_block_foldable(block):
                self.folding_area.toggle_fold(block)
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
    """Thread para gerenciar operações de pacotes em background"""
    
    output_signal = Signal(str)
    finished_signal = Signal(bool, str)
    progress_signal = Signal(str)

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

            elif self.command == "show":
                self.progress_signal.emit(f"Obtendo informações do pacote {self.package_name}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", self.package_name],
                    capture_output=True, text=True, encoding='utf-8', timeout=30
                )
                if result.returncode == 0:
                    self.output_signal.emit(result.stdout)
                else:
                    self.output_signal.emit(f"Erro ao obter informações: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.finished_signal.emit(False, "Timeout: A operação demorou muito.")
        except Exception as e:
            self.finished_signal.emit(False, f"Erro: {str(e)}")
            

class PackageManagerDialog(QDialog):
    """Diálogo completo para gerenciamento de pacotes Python"""
    
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

        self.info_btn = QPushButton("📋 Informações")
        self.info_btn.clicked.connect(self.show_package_info)
        action_layout.addWidget(self.info_btn)

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
        """Atualiza lista de pacotes instalados"""
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

    def install_package(self):
        """Instala um pacote"""
        package_name = self.package_input.text().strip()
        version = self.version_input.text().strip()

        if not package_name:
            QMessageBox.warning(self, "Aviso", "Digite o nome do pacote!")
            return

        self.output_text.append(f"📥 Instalando {package_name}...")
        self.progress_bar.setVisible(True)

        self.thread = PackageManagerThread("install", package_name, version)
        self.thread.finished_signal.connect(self.on_operation_finished)
        self.thread.progress_signal.connect(self.update_progress_text)
        self.thread.start()

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

    def show_package_info(self):
        """Mostra informações detalhadas do pacote"""
        current_item = self.packages_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione um pacote da lista!")
            return

        package_data = current_item.data(Qt.UserRole)
        package_name = package_data['name']

        self.output_text.append(f"📋 Obtendo informações de {package_name}...")
        self.thread = PackageManagerThread("show", package_name)
        self.thread.output_signal.connect(self.show_package_details)
        self.thread.progress_signal.connect(self.update_progress_text)
        self.thread.start()

    def show_package_details(self, output):
        """Mostra informações detalhadas do pacote"""
        self.output_text.append(f"Informações do pacote:\n{output}")

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
        """Analisa código e extrai símbolos - VERSÃO SIMPLIFICADA"""
        try:
            # Análise básica com regex
            imports = {}
            functions = set()
            classes = set()
            variables = set()
            
            # Detecta imports
            import_pattern = r'(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            import_matches = re.findall(import_pattern, code)
            for module in import_matches:
                imports[module] = []
            
            # Detecta funções
            func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            func_matches = re.findall(func_pattern, code)
            functions.update([f"{f}()" for f in func_matches])
            
            # Detecta classes
            class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            class_matches = re.findall(class_pattern, code)
            classes.update(class_matches)
            
            return {
                'imports': imports,
                'symbols': {
                    'functions': functions,
                    'classes': classes,
                    'variables': variables,
                    'methods': {}
                },
                'classes': {}
            }
        except Exception as e:
            print(f"Erro na análise: {e}")
            return {
                'imports': {},
                'symbols': {'functions': set(), 'classes': set(), 'variables': set(), 'methods': {}},
                'classes': {}
            }

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

# ===== CORREÇÃO DO ERRO CRÍTICO =====

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # INICIALIZAR ATRIBUTOS PRIMEIRO
        self._initialize_variables()
        
        # DEPOIS configurar a UI
        self.setup_managers()
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        
        # Configurar sistemas avançados
        self.setup_lsp_system()
        self.setup_syntax_highlighting_system()
        self.setup_autocomplete()
        
        # Configurar exceções globais
        sys.excepthook = self.exception_hook
        
        # Inicializar sistemas com delay para garantir estabilidade
        QTimer.singleShot(100, self.setup_autocomplete)
        QTimer.singleShot(200, self.setup_plugin_system)
        QTimer.singleShot(500, self.setup_autocomplete_system)
        QTimer.singleShot(100, self.setup_undo_redo_system)
        
        # Configurações de debug
        self.debug_mode = False
        self.debug_process = None
        self.current_debug_file = None
        
        # Parse de argumentos de linha de comando
        self.parse_command_line_args()
        
        # CORREÇÃO: setup_indicators deve vir ANTES do setup_scope_header
        self.setup_indicators()

        # CORREÇÃO: Removida a chamada problemática para setup_undo_redo_connections
        # que tentava acessar self.editor que não existe ainda
        
        # Configurar scope header com delay para garantir que a UI está pronta
        QTimer.singleShot(100, self.setup_scope_header)
    def setup_undo_redo_system(self):
        """Configura o sistema de undo/redo de forma completa"""
        try:
            # Conectar sinais para atualizar estado dos botões
            self.update_undo_redo_actions()
            
            # Conectar mudança de aba para atualizar undo/redo
            self.tab_widget.currentChanged.connect(self.update_undo_redo_actions)
            
            print("✅ Sistema undo/redo configurado")
        except Exception as e:
            print(f"❌ Erro ao configurar undo/redo: {e}")
    def setup_scope_header(self):
        """Configura o header de escopo (classe/função atual) - NOVO MÉTODO"""
        # Este método será implementado para mostrar o escopo atual
        # Por enquanto, vamos apenas criar um placeholder
        try:
            # Inicializar variáveis de escopo
            self.current_class = "Global"
            self.current_function = "Nenhuma"
            
            # Conectar sinais para atualizar escopo
            self.tab_widget.currentChanged.connect(self.update_scope_display)
            
            print("✅ Header de escopo configurado")
        except Exception as e:
            print(f"⚠️ Erro ao configurar header de escopo: {e}")

    def update_scope_display(self, index):
        """Atualiza o display do escopo quando a aba muda - NOVO MÉTODO"""
        try:
            if index >= 0:
                widget = self.tab_widget.widget(index)
                if hasattr(widget, 'editor'):
                    # Conectar ao sinal de mudança de cursor do editor
                    widget.editor.cursorPositionChanged.connect(
                        lambda: self.update_scope_from_editor(widget.editor)
                    )
                    # Atualizar imediatamente
                    self.update_scope_from_editor(widget.editor)
        except Exception as e:
            print(f"Erro ao atualizar display de escopo: {e}")

    def update_scope_from_editor(self, editor):
        """Atualiza o escopo baseado na posição do cursor - NOVO MÉTODO"""
        try:
            if not editor:
                return
                
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            text = editor.toPlainText()
            lines = text.split('\n')
            
            # Encontrar classe atual
            current_class = "Global"
            for i in range(line - 1, -1, -1):
                if i < len(lines):
                    line_text = lines[i].strip()
                    if line_text.startswith('class '):
                        class_match = re.match(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line_text)
                        if class_match:
                            current_class = class_match.group(1)
                            break
            
            # Encontrar função atual
            current_function = "Nenhuma"
            for i in range(line - 1, -1, -1):
                if i < len(lines):
                    line_text = lines[i].strip()
                    if line_text.startswith('def '):
                        func_match = re.match(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line_text)
                        if func_match:
                            current_function = func_match.group(1)
                            break
            
            self.current_class = current_class
            self.current_function = current_function
            
            # Atualizar na statusbar
            self.update_scope_in_statusbar()
            
        except Exception as e:
            print(f"Erro ao atualizar escopo do editor: {e}")

    def update_scope_in_statusbar(self):
        """Atualiza as informações de escopo na statusbar - NOVO MÉTODO"""
        try:
            scope_text = f"Escopo: {self.current_class}"
            if self.current_function != "Nenhuma":
                scope_text += f".{self.current_function}()"
            
            # Atualizar o label de escopo na statusbar
            if hasattr(self, 'scope_info_label'):
                self.scope_info_label.setText(scope_text)
                
        except Exception as e:
            print(f"Erro ao atualizar escopo na statusbar: {e}")

    
    def setup_undo_redo_connections(self):
        """Configura conexões para undo/redo - VERSÃO SEGURA"""
        # CORREÇÃO: Este método será chamado apenas quando um editor estiver disponível
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'document'):
            try:
                editor.document().undoAvailable.connect(self.update_undo_action)
                editor.document().redoAvailable.connect(self.update_redo_action)
                print("✅ Conexões undo/redo configuradas")
            except Exception as e:
                print(f"⚠️ Erro ao configurar undo/redo: {e}")
    
    def update_undo_action(self, available):
        """Atualiza estado da ação desfazer"""
        # Pode ser usado para atualizar UI se necessário
        pass
    
    def update_redo_action(self, available):
        """Atualiza estado da ação refazer"""
        # Pode ser u
    def debug_code(self):
        """Executa o código em modo debug - VERSÃO CORRIGIDA"""
        try:
            current_widget = self.tab_widget.currentWidget()
            if not current_widget or not hasattr(current_widget, 'file_path'):
                QMessageBox.information(self, "Informação", "Nenhum arquivo para depurar.")
                return

            file_path = current_widget.file_path
            if not file_path or not file_path.endswith('.py'):
                QMessageBox.information(self, "Informação", "Apenas arquivos Python podem ser depurados.")
                return

            # Salva o arquivo primeiro
            self.save_file()

            # Limpa e prepara a aba de debug
            self.output_tabs.setCurrentWidget(self.debug_text)
            self.debug_text.clear()
            
            # Para qualquer debug anterior
            if self.debug_process and self.debug_process.state() == QProcess.Running:
                self.debug_process.kill()
                self.debug_process.waitForFinished(1000)

            # Cria novo processo de debug
            self.debug_process = QProcess(self)
            self.debug_process.readyReadStandardOutput.connect(self.handle_debug_output)
            self.debug_process.readyReadStandardError.connect(self.handle_debug_error)
            self.debug_process.finished.connect(self.handle_debug_finished)

            # Configura o comando
            python_exec = self.get_python_executable()
            cmd = [python_exec, "-u", "-m", "pdb", file_path]
            
            # Define working directory
            working_dir = self.project_path or os.path.dirname(file_path)
            self.debug_process.setWorkingDirectory(working_dir)

            self.debug_text.appendPlainText(f"🐛 Iniciando debug: {os.path.basename(file_path)}")
            self.debug_text.appendPlainText(f"📁 Diretório: {working_dir}")
            self.debug_text.appendPlainText(f"🐍 Python: {python_exec}")
            self.debug_text.appendPlainText("-" * 50)
            self.debug_text.appendPlainText("Comandos disponíveis:")
            self.debug_text.appendPlainText("n (next) - Próxima linha")
            self.debug_text.appendPlainText("s (step) - Entrar na função") 
            self.debug_text.appendPlainText("c (continue) - Continuar até breakpoint")
            self.debug_text.appendPlainText("l (list) - Mostrar código ao redor")
            self.debug_text.appendPlainText("p <expr> - Imprimir expressão")
            self.debug_text.appendPlainText("q (quit) - Sair do debug")
            self.debug_text.appendPlainText("-" * 50)
            self.debug_text.appendPlainText("(Pdb) ")

            # Inicia o processo
            self.debug_process.start(cmd[0], cmd[1:])
            self.debug_mode = True
            self.current_debug_file = file_path

            if not self.debug_process.waitForStarted(5000):
                self.debug_text.appendPlainText("❌ Falha ao iniciar processo de debug")
                self.debug_mode = False
                return

        except Exception as e:
            self.debug_text.appendPlainText(f"❌ Erro no debug: {str(e)}")
            self.debug_mode = False
    def get_current_editor(self):
        """Obtém o editor atual de forma robusta - VERSÃO CORRIGIDA"""
        try:
            # CORREÇÃO: Verifica se o tab_widget existe e tem abas
            if not hasattr(self, 'tab_widget') or self.tab_widget.count() == 0:
                return None
                
            current_widget = self.tab_widget.currentWidget()
            if current_widget:
                # Se for um EditorTab, retorna o editor interno
                if hasattr(current_widget, 'editor'):
                    return current_widget.editor
                # Se for diretamente um editor, retorna ele mesmo
                elif isinstance(current_widget, (QPlainTextEdit, UnifiedCodeEditor)):
                    return current_widget
            return None
        except Exception as e:
            print(f"❌ Erro em get_current_editor: {e}")
            return None

    def on_tab_changed(self, index):
        """Atualiza a interface quando a aba muda - VERSÃO CORRIGIDA"""
        try:
            if index >= 0:
                widget = self.tab_widget.widget(index)
                if hasattr(widget, 'file_path') and widget.file_path:
                    self.update_file_info(widget.file_path)
                    
                    # Atualiza syntax highlighting se necessário
                    if hasattr(widget, 'editor') and hasattr(self, 'syntax_highlighting_manager'):
                        self.syntax_highlighting_manager.setup_editor_highlighter(widget.editor, widget.file_path)

                    # Conectar ao minimap
                    if hasattr(self, 'minimap_widget'):
                        self.minimap_widget.set_main_editor(widget.editor)
                        
                    # ATUALIZA O OUTLINE automaticamente
                    if hasattr(self, 'outline_widget'):
                        self.outline_widget.refresh_outline()
                        
                    # CORREÇÃO: Configurar conexões undo/redo quando uma aba é selecionada
                    QTimer.singleShot(100, self.setup_undo_redo_connections)
                    
                else:
                    self.update_file_info(None)
                    # Limpar minimap se não há editor válido
                    if hasattr(self, 'minimap_widget'):
                        self.minimap_widget.clear()
                        
                    # Limpa o outline
                    if hasattr(self, 'outline_widget'):
                        self.outline_widget.tree_widget.clear()
                        
        except Exception as e:
            print(f"❌ Erro em on_tab_changed: {e}")

    def handle_debug_output(self):
        """Processa saída do debug"""
        try:
            if self.debug_process and self.debug_mode:
                data = self.debug_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
                if data:
                    self.debug_text.appendPlainText(data)
        except Exception as e:
            print(f"Erro ao processar output do debug: {e}")
    def handle_debug_finished(self, exit_code, exit_status):
        """Processa término do debug"""
        self.debug_text.appendPlainText(f"\n🔚 Debug finalizado (código: {exit_code})")
        self.debug_mode = False
        self.current_debug_file = None

    def send_debug_command(self, command):
        """Envia comando para o processo de debug"""
        try:
            if (self.debug_process and self.debug_mode and 
                self.debug_process.state() == QProcess.Running):
                self.debug_process.write(f"{command}\n".encode('utf-8'))
                return True
        except Exception as e:
            print(f"Erro ao enviar comando de debug: {e}")
        return False       

    def handle_debug_error(self):
        """Processa erro do debug"""
        try:
            if self.debug_process and self.debug_mode:
                data = self.debug_process.readAllStandardError().data().decode('utf-8', errors='ignore')
                if data:
                    self.debug_text.appendPlainText(f"[ERRO] {data}")
        except Exception as e:
            print(f"Erro ao processar erro do debug: {e}")        
    def setup_autocomplete_system(self):
        """Configura sistema de autocomplete completo"""
        try:
            # Inicializa o completador
            self.completer = HybridCompleter()
            
            # Shortcut global para autocomplete
            QShortcut(QKeySequence("Ctrl+Space"), self).activated.connect(
                self.trigger_global_autocomplete)
                
            print("✅ Sistema de autocomplete inicializado")
            
        except Exception as e:
            print(f"❌ Erro no setup do autocomplete: {e}")
            
    
    def setup_syntax_highlighting_system(self):
        """Configura o sistema de syntax highlighting"""
        self.syntax_highlighting_manager = SyntaxHighlightingManager(self)

    def parse_command_line_args(self):
        """NOVO: Processa --project e --python se launcher iniciar sem socket"""
        import sys
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        project = None
        python_ver = None
        for i, arg in enumerate(args):
            if arg == "--project" and i + 1 < len(args):
                project = args[i + 1]
            elif arg == "--python" and i + 1 < len(args):
                python_ver = args[i + 1]
        if project:
            QTimer.singleShot(1000, lambda: self.set_project(project))  # Delay para UI carregar
    def _initialize_variables(self):
            """INICIALIZAÇÃO SEGURA: Define TODAS as variáveis com valores padrão"""
            # Variáveis básicas
            self.current_file = ""
            self.project_path = ""
            self.python_path = sys.executable
            self.venv_path = ""
            self.current_font = "Consolas"
            self.clipboard_path = ""
            self.is_cut = False
            self.file_path = ""  # Inicializar file_path vazio
            
            # CORREÇÃO: Inicializar editor como None
            self.editor = None
            
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
            
            # CORREÇÃO: Inicializar atributos de escopo
            self.current_class = "Global"
            self.current_function = "Nenhuma"
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
            self.syntax_highlighting_manager = SyntaxHighlightingManager(self)


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
        """Configura widget central com splitter para editor e minimap - CORRIGIDO"""
        # Criar splitter horizontal
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Área do editor principal
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
        
        # Área do minimap NOVO - substituindo o antigo
        self.minimap_widget = Minimap()
        self.minimap_widget.setMaximumWidth(150)
        self.minimap_widget.setMinimumWidth(80)
        
        # Adicionar widgets ao splitter
        self.main_splitter.addWidget(self.tab_widget)
        self.main_splitter.addWidget(self.minimap_widget)
        
        # Configurar proporções (editor maior, minimap menor)
        self.main_splitter.setSizes([800, 150])
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 0)
        
        self.setCentralWidget(self.main_splitter)


    def setup_docks(self):
        self.setup_left_dock()
        #self.setup_right_dock()
        self.setup_bottom_dock()

    def setup_left_dock(self):
        left_dock = QDockWidget("Explorer", self)
        left_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        left_dock.setMaximumWidth(300)

        left_tabs = QTabWidget()
        left_tabs.setTabPosition(QTabWidget.West)

        self.setup_file_explorer(left_tabs)
        self.setup_outline_widget(left_tabs)  # NOVO: Adiciona o Outline
        self.setup_problems_widget(left_tabs)

        left_dock.setWidget(left_tabs)
        self.addDockWidget(Qt.LeftDockWidgetArea, left_dock)

    def setup_outline_widget(self, parent_tabs):
        """Configura o widget de outline (Classes/Funções)"""
        self.outline_widget = OutlineWidget(self)
        parent_tabs.addTab(self.outline_widget, "📊 Outline")

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
        package_action = QAction("📦 Gerenciador de Pacotes Python", self)
        package_action.setShortcut("Ctrl+Shift+P")
        package_action.triggered.connect(self.open_package_manager)
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
        """Abre o localizador de textos similares aprimorado - CORRIGIDO"""
        try:
            # Obtém o editor atual de forma robusta
            current_widget = self.tab_widget.currentWidget()
            
            if current_widget and hasattr(current_widget, 'editor'):
                editor = current_widget.editor
                dialog = AdvancedFindSimilarDialog(editor, self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Aviso", 
                                "Nenhum editor ativo!\n\n"
                                "Abra ou crie um arquivo primeiro para usar o localizador de textos similares.")
                
        except Exception as e:
            print(f"Erro ao abrir localizador de textos similares: {e}")
            QMessageBox.warning(self, "Erro", 
                            f"Não foi possível abrir o localizador de textos similares:\n{str(e)}")

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
        """Aplica o tema de syntax highlighting a todos os editores (ATUALIZADO)"""
        if hasattr(self, 'syntax_highlighting_manager'):
            # Converte cores do tema para o formato do highlighter
            theme_colors = {
                'keyword': QColor(theme["colors"].get("keyword", "#569CD6")),
                'string': QColor(theme["colors"].get("string", "#CE9178")),
                'comment': QColor(theme["colors"].get("comment", "#6A9955")),
                'number': QColor(theme["colors"].get("number", "#B5CEA8")),
                'function': QColor(theme["colors"].get("function", "#DCDCAA")),
                'class': QColor(theme["colors"].get("class", "#4EC9B0")),
                'builtin': QColor(theme["colors"].get("builtin", "#4FC1FF")),
                'decorator': QColor(theme["colors"].get("decorator", "#BBB529")),
            }
            
            self.syntax_highlighting_manager.update_theme(theme_colors)

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

    # No método setup_view_menu da classe IDE, adicione:

    def setup_view_menu(self, menu):
        actions = [
            # ... ações existentes ...
            ("📊 Layout Dividido", "Ctrl+\\", self.split_view),
            ("🔍 Zoom In", "Ctrl+=", self.zoom_in),
            ("🔍 Zoom Out", "Ctrl+-", self.zoom_out),
            ("🔍 Zoom Reset", "Ctrl+0", self.zoom_reset),
            ("---", None, None),
            
            # NOVOS: Controles de Folding
            ("📁 Dobrar Tudo", "Alt+Left", self.collapse_all_folds),
            ("📂 Expandir Tudo", "Alt+Right", self.expand_all_folds),
            ("📄 Alternar Dobra", "Alt+L", self.toggle_fold),
            ("---", None, None),
            
            ("👁️ Mostrar/Ocultar Explorer", "Ctrl+Shift+E", self.toggle_explorer),
            ("👁️ Mostrar/Ocultar Terminal", "Ctrl+`", self.toggle_terminal),
            ("👁️ Mostrar/Ocultar Minimap", "Ctrl+Shift+M", self.toggle_minimap),
            ("📊 Mostrar/Ocultar Outline", "Ctrl+Shift+O", self.toggle_outline),
            ("---", None, None),
            ("🎨 Tema Escuro", None, lambda: self.set_dark_theme_optimized()),
            ("🎨 Tema Claro", None, lambda: self.set_light_theme()),
            ("🔤 Fonte...", None, self.show_font_dialog)
        ]

        self.create_menu_actions(menu, actions)

    def collapse_all_folds(self):
        """Dobra todas as seções do editor atual"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'collapse_all_folds'):
            editor.collapse_all_folds()

    def expand_all_folds(self):
        """Expande todas as seções do editor atual"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'expand_all_folds'):
            editor.expand_all_folds()

    def toggle_fold(self):
        """Alterna a dobra na linha atual"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'folding_area'):
            cursor = editor.textCursor()
            block = cursor.block()
            editor.folding_area.toggle_fold(block)
    def toggle_outline(self):
        """Alterna a visibilidade do Outline"""
        for dock in self.findChildren(QDockWidget):
            if dock.windowTitle() == "Explorer":
                left_tabs = dock.widget()
                if isinstance(left_tabs, QTabWidget):
                    # Encontra e foca no Outline
                    for i in range(left_tabs.count()):
                        if left_tabs.tabText(i) == "📊 Outline":
                            left_tabs.setCurrentIndex(i)
                            break
                break
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
            ("📄", "Novo Arquivo", "Ctrl+N", self.new_file),
            ("📂", "Abrir Arquivo", "Ctrl+O", self.open_file),
            ("💾", "Salvar", "Ctrl+S", self.save_file),
            ("---", None, None, None),
            ("↶", "Desfazer", "Ctrl+Z", self.undo),
            ("↷", "Refazer", "Ctrl+Y", self.redo),
            ("---", None, None, None),
            ("▶️", "Executar", "F5", self.run_code),
            ("🐛", "Debug", "F6", self.debug_code),
            ("---", None, None, None),
            ("🔍", "Buscar", "Ctrl+F", self.show_find_dialog),
            ("🎯", "Auto-completar", "Ctrl+Space", self.force_auto_complete_current),
            ("📊", "Números de Linha", "Ctrl+Shift+L", self.toggle_line_numbers),
            ("🎯", "Destaque Linha Atual", "Ctrl+Shift+H", self.toggle_current_line_highlight),
            ("🗑️", "Limpar Indicadores", "Ctrl+Shift+C", self.clear_indicators),
            ("---", None, None, None),
        ]

        # CÓDIGO CORRIGIDO - Verifica o número de elementos em cada ação
        for action_data in actions:
            if len(action_data) == 4:
                icon, text, shortcut, callback = action_data
            elif len(action_data) == 3:
                # Se tiver apenas 3 elementos, assume que o callback é None
                icon, text, shortcut = action_data
                callback = None
            else:
                print(f"Ação com formato inválido: {action_data}")
                continue

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
        status_bar = self.statusBar()

        self.file_info_label = QLabel("Sem arquivo")
        status_bar.addWidget(self.file_info_label)

        # NOVA LABEL: Informações de escopo (classe/função atual)
        self.scope_info_label = QLabel("Escopo: Global")
        status_bar.addWidget(self.scope_info_label)

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
    def toggle_line_numbers(self):
        """Alterna a visibilidade dos números de linha"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'line_number_area'):
            editor.line_number_area.setVisible(not editor.line_number_area.isVisible())
            # Atualiza a margem
            editor.update_line_number_area_width(0)
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
        """Configura atalhos globais - VERSÃO CORRIGIDA"""
        
        # Atalhos básicos de edição (agora funcionarão globalmente)
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self).activated.connect(self.redo)
        QShortcut(QKeySequence("Ctrl+X"), self).activated.connect(self.cut)
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self.copy)
        QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(self.paste)
        QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(self.select_all)
        
        # Outros atalhos existentes...
        QShortcut("Ctrl+Tab", self).activated.connect(self.next_tab)
        QShortcut("Ctrl+Shift+Tab", self).activated.connect(self.previous_tab)
        QShortcut("Ctrl+P", self).activated.connect(self.show_command_palette)
        
        # Atalhos para folding
        QShortcut("Alt+Left", self).activated.connect(self.collapse_all_folds)
        QShortcut("Alt+Right", self).activated.connect(self.expand_all_folds)
        QShortcut("Alt+L", self).activated.connect(self.toggle_fold)
        
        QShortcut("Ctrl+Shift+M", self).activated.connect(self.toggle_minimap)
        QShortcut("Ctrl+L", self).activated.connect(self.toggle_line_numbers)
        QShortcut("Ctrl+Shift+O", self).activated.connect(self.focus_outline)
        QShortcut("Ctrl+Shift+H", self).activated.connect(self.toggle_current_line_highlight)
        QShortcut("Ctrl+Shift+C", self).activated.connect(self.clear_indicators)

    def select_all(self):
        """Seleciona todo o texto no editor atual"""
        editor = self.get_current_editor()
        if editor:
            editor.selectAll()

    def focus_outline(self):
        """Foca no widget de Outline"""
        if hasattr(self, 'outline_widget'):
            # Encontra o dock do explorer
            for dock in self.findChildren(QDockWidget):
                if dock.windowTitle() == "Explorer":
                    left_tabs = dock.widget()
                    if isinstance(left_tabs, QTabWidget):
                        # Encontra o índice da aba do Outline
                        for i in range(left_tabs.count()):
                            if left_tabs.tabText(i) == "📊 Outline":
                                left_tabs.setCurrentIndex(i)
                                self.outline_widget.tree_widget.setFocus()
                                break
                    break
                
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
        """Cria um novo arquivo - VERSÃO CORRIGIDA"""
        dialog = NewFileDialog(self)
        if dialog.exec():
            file_name = dialog.get_file_name()
            if file_name:
                # Cria editor CORRETO
                self.setup_editor_connections(editor)

                editor = UnifiedCodeEditor(
                    text="",
                    cursor_position=0,
                    file_path=None,
                    project_path=self.project_path,
                    parent=self
                )
                
                # Configurar para aceitar atalhos
                editor.setFocusPolicy(Qt.StrongFocus)

                # Cria widget de aba
                editor_tab = QWidget()
                layout = QVBoxLayout(editor_tab)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(editor)
                editor_tab.file_path = None
                editor_tab.editor = editor
                editor_tab.is_new_file = True
                editor_tab.file_name = file_name

                # Adiciona à aba
                index = self.tab_widget.addTab(editor_tab, f"📄 {file_name}")
                self.tab_widget.setCurrentIndex(index)

                editor.setFocus()
                self.update_file_info(None)

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
        """Salva o arquivo atual - VERSÃO CORRIGIDA"""
        try:
            current_widget = self.tab_widget.currentWidget()
            if not current_widget:
                QMessageBox.information(self, "Informação", "Nenhum arquivo para salvar.")
                return False

            # Verifica se é um EditorTab
            if hasattr(current_widget, 'editor'):
                editor = current_widget.editor
                file_path = getattr(current_widget, 'file_path', None)
                
                if file_path:
                    # Salva no arquivo existente
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(editor.toPlainText())
                    
                    # Marca como não modificado
                    editor.document().setModified(False)
                    
                    # Atualiza título da aba
                    index = self.tab_widget.currentIndex()
                    tab_text = self.tab_widget.tabText(index)
                    if tab_text.endswith(' *'):
                        self.tab_widget.setTabText(index, tab_text[:-2])
                    
                    self.statusBar().showMessage(f"✅ Arquivo salvo: {os.path.basename(file_path)}", 3000)
                    return True
                else:
                    # Arquivo novo - usa Salvar Como
                    return self.save_file_as()
            else:
                QMessageBox.information(self, "Informação", "Tipo de editor não suportado.")
                return False
                
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
            return False

    def save_file_as(self):
        """Salva o arquivo atual com novo nome - VERSÃO CORRIGIDA"""
        try:
            current_widget = self.tab_widget.currentWidget()
            if not current_widget:
                return False

            if hasattr(current_widget, 'editor'):
                editor = current_widget.editor
                
                new_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Salvar Como",
                    self.project_path or QDir.homePath(),
                    "Todos os Arquivos (*.*)"
                )

                if new_path:
                    with open(new_path, 'w', encoding='utf-8') as f:
                        f.write(editor.toPlainText())

                    # Atualiza informações do arquivo
                    current_widget.file_path = new_path
                    
                    # Atualiza título da aba
                    index = self.tab_widget.currentIndex()
                    self.tab_widget.setTabText(index, os.path.basename(new_path))
                    
                    # Marca como não modificado
                    editor.document().setModified(False)
                    
                    self.update_file_info(new_path)
                    self.statusBar().showMessage(f"✅ Arquivo salvo como: {os.path.basename(new_path)}", 3000)
                    return True
                    
            return False
            
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
            return False

    def save_all_files(self):
        """Salva todos os arquivos abertos - VERSÃO CORRIGIDA"""
        saved_count = 0
        total_count = self.tab_widget.count()
        
        for i in range(total_count):
            self.tab_widget.setCurrentIndex(i)
            if self.save_file():
                saved_count += 1
        
        if saved_count == total_count:
            self.statusBar().showMessage(f"✅ Todos os {saved_count} arquivos salvos", 3000)
        else:
            self.statusBar().showMessage(f"⚠️ {saved_count} de {total_count} arquivos salvos", 3000)

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
    def update_undo_redo_actions(self):
        """Atualiza estado das ações undo/redo na toolbar/menu"""
        try:
            editor = self.get_current_editor()
            undo_available = False
            redo_available = False
            
            if editor and hasattr(editor, 'document'):
                undo_available = editor.document().isUndoAvailable()
                redo_available = editor.document().isRedoAvailable()
            
            # Atualizar ações na toolbar se existirem
            # Você pode adicionar referências às suas ações aqui
            setup_editor_connections
        except Exception as e:
            print(f"Erro ao atualizar ações undo/redo: {e}")
    
        # ===== MÉTODOS DE EDIÇÃO =====
    def undo(self):
        """Desfaz a última ação - VERSÃO CORRIGIDA"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'document'):
            try:
                if editor.document().isUndoAvailable():
                    editor.undo()
                    self.statusBar().showMessage("↶ Ação desfeita", 2000)
                    self.update_undo_redo_actions()  # Atualizar estado dos botões
                else:
                    self.statusBar().showMessage("ℹ️ Nada para desfazer", 2000)
            except Exception as e:
                print(f"Erro ao desfazer: {e}")

    def redo(self):
        """Refaz a última ação - VERSÃO CORRIGIDA"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'document'):
            try:
                if editor.document().isRedoAvailable():
                    editor.redo()
                    self.statusBar().showMessage("↷ Ação refeita", 2000)
                    self.update_undo_redo_actions()  # Atualizar estado dos botões
                else:
                    self.statusBar().showMessage("ℹ️ Nada para refazer", 2000)
            except Exception as e:
                print(f"Erro ao refazer: {e}")

    def cut(self):
        """Recorta texto selecionado - VERSÃO CORRIGIDA"""
        editor = self.get_current_editor()
        if editor:
            try:
                editor.cut()
                self.statusBar().showMessage("✂️ Texto recortado", 2000)
            except Exception as e:
                print(f"Erro ao recortar: {e}")

    def copy(self):
        """Copia texto selecionado - VERSÃO CORRIGIDA"""
        editor = self.get_current_editor()
        if editor:
            try:
                editor.copy()
                self.statusBar().showMessage("📋 Texto copiado", 2000)
            except Exception as e:
                print(f"Erro ao copiar: {e}")

    def paste(self):
        """Cola texto da área de transferência - VERSÃO CORRIGIDA"""
        editor = self.get_current_editor()
        if editor:
            try:
                editor.paste()
                self.statusBar().showMessage("📝 Texto colado", 2000)
            except Exception as e:
                print(f"Erro ao colar: {e}")
    def show_find_dialog(self):
        """Mostra diálogo de busca - VERSÃO CORRIGIDA"""
        editor = self.get_current_editor()
        if not editor:
            QMessageBox.information(self, "Informação", "Nenhum editor ativo.")
            return

        # Diálogo de busca simples mas funcional
        find_text, ok = QInputDialog.getText(
            self,
            "Buscar",
            "Texto para buscar:",
            text=editor.textCursor().selectedText() or ""
        )

        if ok and find_text:
            self.find_in_editor(editor, find_text)

    def find_in_editor(self, editor, find_text, backward=False):
        """Busca texto no editor - VERSÃO CORRIGIDA"""
        try:
            cursor = editor.textCursor()
            document = editor.document()
            
            # Define opções de busca
            options = QTextDocument.FindFlag(0)
            if backward:
                options = QTextDocument.FindBackward
            
            # Realiza a busca
            found_cursor = document.find(find_text, cursor, options)
            
            if found_cursor.isNull():
                # Se não encontrou, busca do início/fim
                if backward:
                    cursor.movePosition(QTextCursor.End)
                else:
                    cursor.movePosition(QTextCursor.Start)
                    
                found_cursor = document.find(find_text, cursor, options)
            
            if not found_cursor.isNull():
                editor.setTextCursor(found_cursor)
                editor.setFocus()
                return True
            else:
                QMessageBox.information(self, "Buscar", "Texto não encontrado.")
                return False
                
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro na busca: {str(e)}")
            return False
                
    def setup_editor_connections(self, editor):
        """Configura conexões para detectar modificações e undo/redo"""
        if editor and hasattr(editor, 'document'):
            try:
                # Conectar modificações do documento
                editor.document().modificationChanged.connect(self.on_document_modified)
                
                # Conectar sinais de undo/redo
                editor.document().undoAvailable.connect(self.update_undo_redo_actions)
                editor.document().redoAvailable.connect(self.update_undo_redo_actions)
                
                print("✅ Conexões do editor configuradas")
            except Exception as e:
                print(f"❌ Erro ao configurar conexões do editor: {e}")
    def on_document_modified(self, modified):
        """Atualiza interface quando documento é modificado - NOVO MÉTODO"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            tab_text = self.tab_widget.tabText(current_index)
            
            if modified and not tab_text.endswith(' *'):
                self.tab_widget.setTabText(current_index, tab_text + ' *')
            elif not modified and tab_text.endswith(' *'):
                self.tab_widget.setTabText(current_index, tab_text[:-2])
    def update_undo_redo_actions(self):
        """Atualiza estado das ações undo/redo na toolbar/menu"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'document'):
            # Aqui você pode atualizar o estado dos botões na toolbar
            # Por exemplo, habilitar/desabilitar baseado na disponibilidade
            undo_available = editor.document().isUndoAvailable()
            redo_available = editor.document().isRedoAvailable()
            
            # Se você tiver referências para ações na toolbar, atualize-as aqui
            # self.undo_action.setEnabled(undo_available)
            # self.redo_action.setEnabled(redo_available)

    
    def show_replace_dialog(self):
        """Mostra diálogo de substituir - VERSÃO CORRIGIDA"""
        editor = self.get_current_editor()
        if not editor:
            QMessageBox.information(self, "Informação", "Nenhum editor ativo.")
            return

        find_text, ok1 = QInputDialog.getText(
            self,
            "Substituir",
            "Texto para buscar:",
            text=editor.textCursor().selectedText() or ""
        )

        if ok1 and find_text:
            replace_text, ok2 = QInputDialog.getText(
                self,
                "Substituir", 
                "Substituir por:"
            )

            if ok2:
                self.replace_in_editor(editor, find_text, replace_text)

    
    def replace_in_editor(self, editor, find_text, replace_text):
        """Substitui texto no editor - VERSÃO CORRIGIDA"""
        try:
            cursor = editor.textCursor()
            
            # Se há texto selecionado e é igual ao texto de busca, substitui
            if cursor.hasSelection() and cursor.selectedText() == find_text:
                cursor.insertText(replace_text)
                # Busca próxima ocorrência
                self.find_in_editor(editor, find_text)
            else:
                # Busca primeira ocorrência
                if self.find_in_editor(editor, find_text):
                    cursor = editor.textCursor()
                    if cursor.selectedText() == find_text:
                        cursor.insertText(replace_text)
                        
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro na substituição: {str(e)}")   
             
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


    def _filter_ansi_codes(self, text):
        """Remove códigos de escape ANSI do texto"""
        import re
        # Regex para remover códigos ANSI (cores, título, etc.)
        ansi_escape = re.compile(r'''
            \x1B  # ESC
            (?:   # 7-bit C1 Fe (except CSI)
                [@-Z\\-_]
            |     # or [ for CSI, followed by a control sequence
                \[
                [0-?]*  # Parameter bytes
                [ -/]*  # Intermediate bytes
                [@-~]   # Final byte
            )
        ''', re.VERBOSE)
            
        return ansi_escape.sub('', text)
    

    def restart_terminal(self):
        """Reinicia o terminal completamente"""
        try:
            self.start_shell()
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text._setup_initial_prompt()
        except Exception as e:
            print(f"Erro ao reiniciar terminal: {e}")

    def activate_project(self):
        """Ativa projeto e venv no terminal - VERSÃO CORRIGIDA"""
        try:
            if (not hasattr(self, 'shell_process') or not self.shell_process
                    or self.shell_process.state() != QProcess.Running):
                print("ℹ️ Shell não está rodando")
                return

            if not hasattr(self, 'project_path') or not self.project_path:
                print("ℹ️ Nenhum projeto aberto")
                return

            # CD para o projeto - COMANDOS SEPARADOS
            if os.name == 'nt':
                cd_cmd = f'cd /d "{self.project_path}"\n'
            else:
                cd_cmd = f'cd "{self.project_path}"\n'

            self.shell_process.write(cd_cmd.encode('utf-8'))
            print(f"📁 CD para: {self.project_path}")

            # Aguarda o CD processar antes do próximo comando
            QTimer.singleShot(500, self._activate_venv_after_cd)

        except Exception as e:
            print(f"❌ Erro ao ativar projeto: {str(e)}")

    def _activate_venv_after_cd(self):
        """Ativa venv após o CD - chamado por timer"""
        try:
            if not hasattr(self, 'project_path') or not self.project_path:
                return

            # Procura por venv
            venv_paths = ['venv', '.venv', 'env']
            venv_found = None
            
            for v in venv_paths:
                vpath = os.path.join(self.project_path, v)
                if os.path.isdir(vpath):
                    venv_found = vpath
                    break

            if venv_found:
                # Comando de ativação CORRETO
                if os.name == 'nt':
                    activate_cmd = f'"{os.path.join(venv_found, "Scripts", "activate.bat")}"\n'
                else:
                    activate_cmd = f'source "{os.path.join(venv_found, "bin", "activate")}"\n'
                
                self.shell_process.write(activate_cmd.encode('utf-8'))
                print(f"🐍 Venv ativado: {os.path.basename(venv_found)}")
                
                # Confirmação após ativação
                QTimer.singleShot(500, self._confirm_venv_activation)
            else:
                print("ℹ️ Nenhum venv encontrado")

        except Exception as e:
            print(f"❌ Erro ao ativar venv: {str(e)}")

    def _confirm_venv_activation(self):
        """Confirma que o venv foi ativado - VERSÃO CORRIGIDA"""
        try:
            if not hasattr(self, 'shell_process') or not self.shell_process:
                return
                
            # CORREÇÃO: Use encode('utf-8') explicitamente
            if os.name == 'nt':
                confirm_msg = 'echo ✅ Projeto e Venv ativados!\n'.encode('utf-8')
            else:
                confirm_msg = 'echo "✅ Projeto e Venv ativados!"\n'.encode('utf-8')
            
            self.shell_process.write(confirm_msg)
            print("✅ Confirmação de ativação enviada")
            
        except Exception as e:
            print(f"❌ Erro na confirmação: {e}")

    def handle_terminal_output(self):
        """Processa saída do terminal - VERSÃO SIMPLIFICADA E CORRETA"""
        try:
            if (not hasattr(self, 'shell_process') or not self.shell_process or
                    not hasattr(self, 'terminal_text') or not self.terminal_text):
                return

            data = self.shell_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if data:
                self.terminal_text.append_output(data)

        except Exception as e:
            print(f"❌ Erro em handle_terminal_output: {e}")

    def handle_terminal_error(self):
        """Processa erro do terminal - VERSÃO SIMPLIFICADA"""
        try:
            if (not hasattr(self, 'shell_process') or not self.shell_process or
                    not hasattr(self, 'terminal_text') or not self.terminal_text):
                return

            data = self.shell_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if data:
                self.terminal_text.append_output(f"[ERRO] {data}")

        except Exception as e:
            print(f"❌ Erro em handle_terminal_error: {e}")

    

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
        """Alterna visibilidade do NOVO minimap de forma inteligente"""
        if hasattr(self, 'minimap_widget'):
            self.minimap_widget.setVisible(not self.minimap_widget.isVisible())
            
            # Ajustar o splitter quando mostrar/ocultar
            if self.minimap_widget.isVisible():
                self.main_splitter.setSizes([700, 100])
            else:
                self.main_splitter.setSizes([1000, 0])

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

    # Adicionar à classe IDE
    def get_current_editor(self):
        """Obtém o editor atual de forma robusta - CORRIGIDO"""
        try:
            if not hasattr(self, 'tab_widget') or self.tab_widget.count() == 0:
                return None
                
            current_widget = self.tab_widget.currentWidget()
            if current_widget:
                # Se for um EditorTab, retorna o editor interno
                if hasattr(current_widget, 'editor'):
                    return current_widget.editor
                # Se for diretamente um editor, retorna ele mesmo
                elif isinstance(current_widget, (QPlainTextEdit, UnifiedCodeEditor)):
                    return current_widget
            return None
        except Exception as e:
            print(f"❌ Erro em get_current_editor: {e}")
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
    def navigate_to_line(self, line_number):
        """Navega para uma linha específica no editor atual"""
        editor = self.get_current_editor()
        if not editor:
            return
            
        # Converte para índice 0-based
        line_num = max(0, line_number - 1)
        
        # Move o cursor para a linha
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        for _ in range(line_num):
            cursor.movePosition(QTextCursor.Down)
            
        editor.setTextCursor(cursor)
        editor.setFocus()
        editor.centerCursor()  # Centraliza a linha na tela
    def start_shell(self):
        """Inicia shell - VERSÃO COMPLETAMENTE CORRIGIDA"""
        try:
            # Para processo anterior
            if hasattr(self, 'shell_process') and self.shell_process:
                if self.shell_process.state() == QProcess.Running:
                    self.shell_process.terminate()
                    self.shell_process.waitForFinished(1000)
                self.shell_process = None

            # Novo processo
            self.shell_process = QProcess(self)
            self.shell_process.readyReadStandardOutput.connect(self.handle_terminal_output)
            self.shell_process.readyReadStandardError.connect(self.handle_terminal_error)

            # Working directory
            if hasattr(self, 'project_path') and self.project_path:
                self.shell_process.setWorkingDirectory(self.project_path)

            # Comando por OS - CORRIGIDO
            if os.name == 'nt':
                self.shell_process.start("cmd.exe", ["/K", "echo Py Dragon Terminal"])
            else:
                self.shell_process.start("/bin/bash", ["-i"])

            # Espera iniciar
            if not self.shell_process.waitForStarted(5000):
                print("❌ Falha ao iniciar shell")
                if hasattr(self, 'terminal_text'):
                    self.terminal_text.setPlainText("❌ Falha ao iniciar terminal\n")
                return

            print("✅ Shell iniciado")
            
            # Configura terminal
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.set_shell_process(self.shell_process)

        except Exception as e:
            print(f"❌ Erro ao iniciar shell: {e}")
            if hasattr(self, 'terminal_text'):
                self.terminal_text.setPlainText(f"❌ Erro no terminal: {e}\n")

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

##############################################################
    # Métodos da classe IDE para autocomplete
    # NO IDE class - SUBSTITUIR O setup_autocomplete completo:

    def setup_autocomplete(self):
        """Configura o sistema de autocomplete de forma unificada - CORRIGIDO"""
        try:
            # Inicializa o completador híbrido
            self.completer = HybridCompleter()

            # Shortcut global para autocomplete
            self.autocomplete_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
            self.autocomplete_shortcut.activated.connect(self.trigger_global_autocomplete)

            print("✅ Sistema de autocomplete inicializado")

        except Exception as e:
            print(f"❌ Erro no setup do autocomplete: {e}")


    def trigger_auto_complete(self):
        """Força a exibição do autocomplete manualmente"""
        if hasattr(self, 'autocomplete_timer'):
            self.autocomplete_timer.start(100)  # Timer muito curto para resposta imediata
    def trigger_global_autocomplete(self):
        """Dispara autocomplete globalmente"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'trigger_auto_complete'):
            editor.trigger_auto_complete()
            

    def handle_suggestions(self, file_path, suggestions):
        """Processa sugestões recebidas do worker"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'show_suggestions'):
            editor.show_suggestions(editor, suggestions)

   
        
    def trigger_manual_autocomplete(self):
        """Dispara autocomplete manualmente"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'trigger_auto_complete'):
            editor.trigger_auto_complete()
    def insert_completion(self, item):
        """Insere a sugestão selecionada no editor"""
        editor = self.get_current_editor()  # CORRIGIDO
        if editor:
            completion_text = item.text()
            cursor = editor.textCursor()
            cursor.insertText(completion_text)
            self.completion_list.setVisible(False)


    def show_completions(self, file_path, suggestions):
        """Mostra lista de sugestões"""
        editor = self.get_current_editor()  # CORRIGIDO
        if not suggestions or not editor:
            self.completion_list.setVisible(False)
            return
        
        # Filtra sugestões duplicadas
        unique_suggestions = []
        seen = set()
        for sug in suggestions:
            if sug not in seen:
                unique_suggestions.append(sug)
                seen.add(sug)
        
        self.last_suggestions = unique_suggestions[:1000000]  # Limita a 10 sugestões
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
        editor = self.get_current_editor()  # CORRIGIDO
        if editor:
            # Atualiza texto e posição atual
            self.text = editor.toPlainText()
            cursor = editor.textCursor()
            self.cursor_position = cursor.position()
            
            # Obtém sugestões
            suggestions = self.get_enhanced_suggestions()
            
            if suggestions:
                self.completion_list.clear()
                for sug in suggestions:
                    self.completion_list.addItem(sug)
                self.completion_list.setVisible(True)
                self.completion_dock.raise_()


    def get_enhanced_suggestions(self):
        """Obtém sugestões melhoradas de forma unificada - CORREÇÃO"""
        suggestions = set()
        
        try:
            # 1. Palavras-chave da linguagem atual
            language_keywords = self.get_language_keywords()
            suggestions.update(language_keywords)
            
            # 2. Definições locais do arquivo
            local_definitions = self.extract_local_definitions()
            suggestions.update(local_definitions)
            
            # 3. Módulos do projeto (se disponível)
            if hasattr(self, 'project_path') and self.project_path:
                project_modules = self.get_project_modules()
                suggestions.update(project_modules)
                
            # 4. Sugestões do sistema de autocomplete base
            base_suggestions = self.get_suggestions_for_autocomplete()
            if base_suggestions:
                suggestions.update(base_suggestions)
            
            # 5. Remove duplicatas e limita resultados
            unique_suggestions = sorted(list(suggestions))
            return unique_suggestions[:25]  # Limita a 25 sugestões
            
        except Exception as e:
            print(f"❌ Erro no enhanced suggestions: {e}")
            return self._get_fallback_suggestions()


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

        return sorted(list(suggestions))[:1000000000]


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
            print(f"DEBUG: Sugestões hardcoded para '{module_name}': {list(suggestions)[:10000000]}...")
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
    def setup_lsp_system(self):
        """Configura sistema LSP no IDE"""
        self.lsp_manager = LSPManager(self)
        
        # Conectar sinais existentes para LSP
        self.tab_widget.currentChanged.connect(self._on_tab_changed_lsp)
        
    def _on_tab_changed_lsp(self, index):
        """Manipula mudança de aba para LSP"""
        if index >= 0:
            widget = self.tab_widget.widget(index)
            if isinstance(widget, EnhancedCodeEditor) and widget.file_path:
                # Atualizar LSP com documento atual
                if self.lsp_manager:
                    content = widget.toPlainText()
                    self.lsp_manager.open_document(widget.file_path, content)

    def set_project(self, project_path=None):
        """Define projeto atual com suporte LSP"""
        if not project_path:
            project_path = QFileDialog.getExistingDirectory(
                self,
                "Selecionar Projeto",
                self.project_path or QDir.homePath()
            )

        if project_path:
            self.project_path = project_path
            self.project_info_label.setText(f"📦 {os.path.basename(project_path)}")

            # Inicializar LSP para o workspace
            if hasattr(self, 'lsp_manager'):
                self.lsp_manager.initialize(project_path)

            # Atualiza explorador
            self.refresh_explorer()

            # Ativa no terminal
            self.activate_project()

            self.statusBar().showMessage(f"✅ Projeto carregado: {project_path}", 3000)

    def open_file(self, file_path=None):
        """Abre arquivo - ATUALIZADO com conexões de modificação"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Abrir Arquivo", 
                self.project_path or QDir.homePath(),
                "Arquivos de Código (*.py *.js *.html *.css *.json *.xml *.txt *.md *.yml *.yaml *.sql *.java *.cpp *.c *.cs *.php *.rb *.go *.rs *.swift *.kt *.ts);;Todos os Arquivos (*.*)"
            )

        if file_path:
            try:
                
                # Verifica se já está aberto
                for i in range(self.tab_widget.count()):
                    widget = self.tab_widget.widget(i)
                    if hasattr(widget, 'file_path') and widget.file_path == file_path:
                        self.tab_widget.setCurrentIndex(i)
                        return

                # Carrega conteúdo
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Cria editor
                editor = UnifiedCodeEditor(
                    text=content,
                    cursor_position=0, 
                    file_path=file_path,
                    project_path=self.project_path,
                    parent=self
                )
                
                # Configura conexões para modificações
                self.setup_editor_connections(editor)
                
                # Configura syntax highlighting
                if hasattr(self, 'syntax_highlighting_manager'):
                    self.syntax_highlighting_manager.setup_editor_highlighter(editor, file_path)

                # Cria widget de aba
                editor_tab = QWidget()
                layout = QVBoxLayout(editor_tab)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(editor)
                editor_tab.file_path = file_path
                editor_tab.editor = editor

                # Adiciona à aba
                index = self.tab_widget.addTab(editor_tab, os.path.basename(file_path))
                self.tab_widget.setCurrentIndex(index)

                self.update_file_info(file_path)
                self.statusBar().showMessage(f"✅ Arquivo aberto: {os.path.basename(file_path)}", 3000)

            except Exception as e:
                print(f"❌ Erro ao abrir arquivo: {e}")
                QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo:\n{str(e)}")

    def closeEvent(self, event):
        """Lida com o fechamento da aplicação de forma segura"""
        print("🔄 Finalizando aplicação...")
        
        # Finalizar LSP primeiro
        if hasattr(self, 'lsp_manager'):
            print("🔄 Finalizando LSP...")
            self.lsp_manager.shutdown()

        # Para workers em execução de forma segura
        if hasattr(self, 'auto_complete_worker') and self.auto_complete_worker:
            print("🔄 Parando worker de autocomplete...")
            self.auto_complete_worker.stop()
            
        if hasattr(self, 'linter_worker') and self.linter_worker:
            print("🔄 Parando worker de linting...")
            self.linter_worker.stop()
            
        if hasattr(self, 'debug_worker') and self.debug_worker:
            print("🔄 Parando worker de debug...")
            self.debug_worker.stop()

        # Para todos os processos
        print("🔄 Parando processos...")
        self.stop_execution()

        # Finaliza plugins
        if hasattr(self, 'plugin_manager'):
            print("🔄 Finalizando plugins...")
            self.plugin_manager.shutdown_plugins()

        # Aguarda um pouco para garantir que tudo foi finalizado
        QTimer.singleShot(100, event.accept)
        
        print("✅ Aplicação finalizada com sucesso")
    def update_minimap_theme(self):
        """Atualiza o tema do NOVO minimap baseado no tema atual"""
        if hasattr(self, 'minimap_widget'):
            self.minimap_widget.setStyleSheet("""
                Minimap {
                    background-color: #1e1e1e;
                    color: #858585;
                    border: none;
                    border-left: 1px solid #2d2d30;
                    font-family: 'Consolas', 'Monospace', monospace;
                }
            """)
# Na classe IDE, ADICIONAR este método:

    def setup_indicators(self):
        """Configura indicadores visuais do IDE - NOVO MÉTODO"""
        try:
            # Inicializar variáveis para indicadores
            self.current_line_highlight = True
            self.show_line_numbers = True
            self.show_minimap = True
            
            # Configurar cores dos indicadores
            self.indicator_colors = {
                'current_line': QColor(45, 45, 48, 80),
                'error': QColor(255, 0, 0, 50),
                'warning': QColor(255, 255, 0, 50),
                'info': QColor(0, 0, 255, 30)
            }
            
            # Conectar sinais para atualizar indicadores
            self.tab_widget.currentChanged.connect(self.update_indicators)
            
            print("✅ Indicadores visuais configurados")
            
        except Exception as e:
            print(f"⚠️ Erro ao configurar indicadores: {e}")

    def update_indicators(self, index):
        """Atualiza indicadores quando a aba muda - NOVO MÉTODO"""
        try:
            if index >= 0:
                widget = self.tab_widget.widget(index)
                if hasattr(widget, 'editor'):
                    # Aplicar indicadores ao editor atual
                    self.apply_editor_indicators(widget.editor)
                    
        except Exception as e:
            print(f"Erro ao atualizar indicadores: {e}")

    def apply_editor_indicators(self, editor):
        """Aplica indicadores visuais a um editor - NOVO MÉTODO"""
        try:
            if not editor:
                return
                
            # Destacar linha atual
            if self.current_line_highlight:
                editor.cursorPositionChanged.connect(
                    lambda: self.highlight_current_line(editor)
                )
                # Aplicar highlight inicial
                self.highlight_current_line(editor)
                
            # Configurar números de linha se disponível
            if hasattr(editor, 'line_number_area'):
                editor.line_number_area.setVisible(self.show_line_numbers)
                
        except Exception as e:
            print(f"Erro ao aplicar indicadores ao editor: {e}")

    def highlight_current_line(self, editor):
        """Destaca a linha atual do editor - NOVO MÉTODO"""
        try:
            if not editor:
                return
                
            extra_selections = []
            
            if not editor.isReadOnly():
                selection = QTextEdit.ExtraSelection()
                selection.format.setBackground(self.indicator_colors['current_line'])
                selection.format.setProperty(QTextFormat.FullWidthSelection, True)
                
                selection.cursor = editor.textCursor()
                selection.cursor.clearSelection()
                extra_selections.append(selection)
            
            editor.setExtraSelections(extra_selections)
            
        except Exception as e:
            print(f"Erro ao destacar linha atual: {e}")

    def toggle_line_numbers(self):
        """Alterna a visibilidade dos números de linha - NOVO MÉTODO"""
        try:
            self.show_line_numbers = not self.show_line_numbers
            editor = self.get_current_editor()
            if editor and hasattr(editor, 'line_number_area'):
                editor.line_number_area.setVisible(self.show_line_numbers)
                
            status = "ativados" if self.show_line_numbers else "desativados"
            self.statusBar().showMessage(f"📊 Números de linha {status}", 2000)
            
        except Exception as e:
            print(f"Erro ao alternar números de linha: {e}")

    def toggle_current_line_highlight(self):
        """Alterna o destaque da linha atual - NOVO MÉTODO"""
        try:
            self.current_line_highlight = not self.current_line_highlight
            editor = self.get_current_editor()
            if editor:
                if self.current_line_highlight:
                    editor.cursorPositionChanged.connect(
                        lambda: self.highlight_current_line(editor)
                    )
                    self.highlight_current_line(editor)
                else:
                    # Remove todos os extra selections
                    editor.setExtraSelections([])
                    
            status = "ativado" if self.current_line_highlight else "desativado"
            self.statusBar().showMessage(f"📝 Destaque da linha atual {status}", 2000)
            
        except Exception as e:
            print(f"Erro ao alternar destaque da linha: {e}")

    def show_error_indicator(self, line_number, message):
        """Mostra indicador de erro em uma linha específica - NOVO MÉTODO"""
        try:
            editor = self.get_current_editor()
            if not editor:
                return
                
            # Adiciona à lista de problemas
            if hasattr(self, 'problems_list'):
                item_text = f"Linha {line_number}: {message}"
                item = QListWidgetItem(item_text)
                item.setForeground(QColor(255, 0, 0))  # Vermelho para erros
                self.problems_list.addItem(item)
                
        except Exception as e:
            print(f"Erro ao mostrar indicador de erro: {e}")

    def clear_indicators(self):
        """Limpa todos os indicadores visuais - NOVO MÉTODO"""
        try:
            # Limpa lista de problemas
            if hasattr(self, 'problems_list'):
                self.problems_list.clear()
                
            # Remove destaques dos editores
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if hasattr(widget, 'editor'):
                    widget.editor.setExtraSelections([])
                    
            self.statusBar().showMessage("🗑️ Indicadores limpos", 2000)
            
        except Exception as e:
            print(f"Erro ao limpar indicadores: {e}")

# ===== CORREÇÃO DO SISTEMA DE INSTÂNCIA ÚNICA =====
class SingleApplication:
    def __init__(self, app_id):
        self.app_id = app_id
        self.server = None
        self.socket = QLocalSocket()
        self.ide_window = None

    def is_running(self):
        """Verifica se já existe uma instância rodando"""
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        if socket.waitForConnected(500):
            socket.disconnectFromServer()
            return True
        return False

    def run(self, ide_instance=None):
        """Tenta executar a aplicação"""
        if self.is_running():
            print("⚠️ Outra instância já está em execução")
            # Envia mensagem para instância existente
            self.send_activate_signal()
            return False
            
        # Remove servidor anterior se existir
        QLocalServer.removeServer(self.app_id)
        
        # Cria novo servidor
        self.server = QLocalServer()
        if not self.server.listen(self.app_id):
            print(f"❌ Não foi possível iniciar servidor: {self.server.errorString()}")
            return False
            
        self.ide_window = ide_instance
        self.server.newConnection.connect(self.handle_new_connection)
        print("✅ Servidor de instância única iniciado")
        return True

    def send_activate_signal(self):
        """Envia sinal para ativar instância existente"""
        try:
            socket = QLocalSocket()
            socket.connectToServer(self.app_id)
            if socket.waitForConnected(1000):
                socket.write(b"activate")
                socket.flush()
                socket.waitForBytesWritten(1000)
                socket.disconnectFromServer()
                print("✅ Sinal de ativação enviado")
        except Exception as e:
            print(f"❌ Erro ao enviar sinal: {e}")

    def handle_new_connection(self):
        """Manipula nova conexão do launcher"""
        try:
            connection = self.server.nextPendingConnection()
            if connection and connection.waitForReadyRead(1000):
                data = connection.readAll().data().decode('utf-8').strip()
                connection.disconnectFromServer()
                
                if data == "activate" and self.ide_window:
                    # Ativa a janela existente
                    QTimer.singleShot(100, self.activate_window)
                    
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")

    def activate_window(self):
        """Ativa a janela do IDE"""
        if self.ide_window:
            self.ide_window.show()
            self.ide_window.raise_()
            self.ide_window.activateWindow()
            print("✅ Janela do IDE ativada")

# ===== CORREÇÃO NO MÉTODO MAIN =====
if __name__ == "__main__":
    # Configurar encoding de forma segura
    try:
        if os.name == 'nt':
            if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if sys.stderr is not None and hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    # Criar QApplication PRIMEIRO
    app = QApplication(sys.argv)
    app.setApplicationName("Py Dragon Studio IDE")
    app.setApplicationVersion("1.0.0")

    # Verificar instância única
    single_app = SingleApplication("py_dragon_studio_ide")
    
    if not single_app.run():
        print("🚫 Aplicação já está em execução. Saindo.")
        sys.exit(0)

    try:
        window = IDE()
        single_app.ide_window = window  # Conectar referência
        
        window.show()
        
        exit_code = app.exec()
        
        # Limpeza final
        if single_app.server:
            single_app.server.close()
            
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        traceback.print_exc()
        QMessageBox.critical(None, "Erro de Inicialização", 
                           f"Falha ao iniciar o IDE:\n{str(e)}")
        sys.exit(1)



