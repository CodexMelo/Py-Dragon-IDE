
import os
import sys
import re
import traceback
import platform
import subprocess
import shutil
import zipfile
import threading
import importlib
import webbrowser
import json
import xml.etree.ElementTree as ET
import tempfile
import glob
import fnmatch
import inspect
import ast
import tokenize
import io
from pathlib import Path
from datetime import datetime
from pathlib import Path
# ===== IMPORTS DO PYSIDE6 =====
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTextEdit, QTreeWidget, QListWidget, QSplitter, 
    QStatusBar, QToolBar, QMenuBar, QMenu, QFileDialog, QMessageBox, 
    QDockWidget, QPlainTextEdit, QLabel, QInputDialog, QPushButton, 
    QFileSystemModel, QTreeView, QStyledItemDelegate, QDialog,
    QListWidgetItem, QToolButton, QFontDialog, QProgressDialog,
    QGroupBox, QTextEdit,  QTabWidget # ADICIONADOS
)
from PySide6.QtCore import (
    Qt, QTimer, QSettings, QSize, QProcess, QDir, QModelIndex,
    QThread, QObject, Signal, QEvent, QRegularExpression, QRect,
    QItemSelectionModel, QStringListModel, QProcessEnvironment
)
from PySide6.QtGui import (
    QKeySequence, QIcon, QFont, QPalette, QColor, QAction, 
    QTextCursor, QTextDocument, QShortcut, QTextFormat, QTextCharFormat,
    QSyntaxHighlighter, QGuiApplication, QClipboard, QPainter,
    QTextBlock, QKeyEvent, QMouseEvent, QFocusEvent, QResizeEvent,
    QDesktopServices, QLinearGradient, QBrush
)

# ===== IMPORTS DO PROJETO =====
# Core Systems
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from plugins.plugin_manager import PluginManager
    from plugins.plugin_base import PluginStatus
    PLUGINS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Sistema de plugins não disponível: {e}")
    PLUGINS_AVAILABLE = False

from core.theme_manager import ThemeManager, ThemeDialog

# Tools e Managers
from tools.python_manager import PythonVersionManager
from tools.indentation_checker import IndentationChecker
from tools.package_manager import PackageManagerDialog

# Analysis
from analysis.lsp_client import LSPManager
from analysis.code_analyzer import CodeAnalyzer

# Syntax
from syntax.language_config import LanguageConfig  
from syntax.syntax_manager import SyntaxHighlightingManager, LanguageSyntaxManager

# Editor
from editor.editor_core import UnifiedCodeEditor, EditorTab
from editor.autocomplete import UnifiedSuggestionSystem
from core.settings_manager import SettingsManager

# UI Components
from ui.widgets import (
    StatusBarProgress,
    OutlineWidget, ProblemsDelegate, Minimap
)

# UI Dialogs
from ui.dialogs import (
    NewFileDialog, PackageDialog, DeployDialog, ProgressDialog,
    PythonVersionDialog, AdvancedFindSimilarDialog,
    FindSimilarDialog
)

# Cache
from cache.module_cache import ModuleCacheManager

# Debug
from debug.terminal import RealTerminal  
from debug.debug_system import  DebugTerminal, DebugWorker




























class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ✅ ORDEM CORRETA DE INICIALIZAÇÃO
        self._initialize_debug_log()
        self._initialize_settings()
        self._initialize_variables()
        
        try:
            self.setup_plugins()
            self.setup_managers()
            self.setup_ui()
            self.setup_connections()
            self.setup_shortcuts()
            
            self.setup_syntax_highlighting_system()
            self.setup_autocomplete()
            self.setup_lsp_system()
        
            sys.excepthook = self.exception_hook
            QTimer.singleShot(100, self.initialize_delayed_systems)
        
            self.debug_log("IDE inicializado com sucesso", "SUCCESS")
        
        except Exception as e:
            self.debug_log(f"Erro na inicialização do IDE: {e}", "ERROR")
            QMessageBox.critical(self, "Erro", f"Falha ao iniciar IDE: {e}")

    # ===== SEÇÃO 1: INICIALIZAÇÃO =====
    
    def _initialize_debug_log(self):
        """Inicializa sistema de logging"""
        def debug_log(message, level="INFO"):
            levels = {
                "INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️",
                "ERROR": "❌", "DEBUG": "🐛"
            }
            icon = levels.get(level, "🔵")
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{icon} [{timestamp}] {message}")
        
        self.debug_log = debug_log
        print("✅ Sistema de logging inicializado")

    def _initialize_settings(self):
        """Inicializa sistema de configurações"""
        try:
            from core.settings_manager import SettingsManager
            self.settings_manager = SettingsManager()
        except ImportError as e:
            self.debug_log(f"⚠️ SettingsManager não disponível: {e}", "WARNING")
            self.python_path = sys.executable

    def _initialize_variables(self):
        """Define TODAS as variáveis com valores padrão"""
        # Variáveis básicas
        self.current_file = ""
        self.project_path = ""
        self.python_path = getattr(self, 'python_path', sys.executable)
        self.venv_path = ""
        self.current_font = "Consolas"
        self.clipboard_path = ""
        self.is_cut = False
        self.file_path = ""
        
        # Componentes UI
        self.editor = None
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
        self.terminal_dock = None
        self.autocomplete_widget = None
        self.autocomplete_timer = None
        self.plugin_manager = None
        self.lsp_manager = None
        self.main_splitter = None
        self.outline_widget = None
        self.scope_info_label = None
        self.minimap_widget = None
        
        # Estado
        self.current_class = "Global"
        self.current_function = "Nenhuma"
        self.current_line_highlight = True
        self.show_line_numbers = True
        self.show_minimap = True
        self.indicator_colors = {}
        self.debug_mode = False
        self.current_debug_file = None
        self.is_linting = False
        self.pending_lint = False
        self.last_lint_content = ""
        
        # Processos
        self.debug_process = None
        self.current_process = None
        self.linter_worker = None
        self.auto_complete_worker = None
        self.debug_worker = None
        self.system_terminal_wrapper = None
        
        # Gerenciadores
        self.python_version_manager = None
        self.theme_manager = None
        self.indentation_checker = None
        self.syntax_highlighting_manager = None
        self.language_config = None
        self.language_syntax_manager = None

    # ===== SEÇÃO 2: CONFIGURAÇÃO DE SISTEMAS =====
    
    def setup_plugins(self):
        """Inicializa sistema de plugins"""
        try:
            self.debug_log("🔌 Inicializando sistema de plugins...", "INFO")
            
            plugins_path = Path(__file__).parent / "plugins"
            if plugins_path.exists():
                sys.path.insert(0, str(plugins_path))
                self.debug_log(f"✅ Caminho de plugins adicionado: {plugins_path}", "SUCCESS")
            else:
                plugins_path.mkdir(parents=True, exist_ok=True)
                self.debug_log(f"✅ Diretório de plugins criado: {plugins_path}", "SUCCESS")
            
            try:
                from plugins.plugin_manager import PluginManager
                self.plugin_manager = PluginManager()
                
                # Configurar instância do IDE
                if hasattr(self.plugin_manager, 'set_ide_instance'):
                    self.plugin_manager.set_ide_instance(self)
                elif hasattr(self.plugin_manager, 'ide_instance'):
                    self.plugin_manager.ide_instance = self
                
                # Carregar plugins
                if hasattr(self.plugin_manager, 'auto_load_plugins'):
                    loaded_count = self.plugin_manager.auto_load_plugins()
                    if loaded_count > 0:
                        self.debug_log(f"✅ {loaded_count} plugins carregados", "SUCCESS")
                        self.integrate_plugin_actions()
                    else:
                        self.debug_log("ℹ️ Nenhum plugin encontrado", "INFO")
                        
            except ImportError as e:
                self.debug_log(f"❌ Não foi possível importar PluginManager: {e}", "ERROR")
                self.plugin_manager = None
                
        except Exception as e:
            self.debug_log(f"❌ Erro crítico ao configurar plugins: {e}", "ERROR")
            self.plugin_manager = None
    
    def setup_managers(self):
        """Inicializa todos os gerenciadores do sistema"""
        try:
            self.debug_log("🔧 Inicializando gerenciadores...", "INFO")
            
            # ✅ VERIFICAR E INICIALIZAR SETTINGS MANAGER PRIMEIRO
            if not hasattr(self, 'settings_manager') or self.settings_manager is None:
                try:
                    from core.settings_manager import SettingsManager
                    self.settings_manager = SettingsManager()
                    self.debug_log("✅ SettingsManager inicializado", "SUCCESS")
                except Exception as e:
                    self.debug_log(f"❌ Erro ao inicializar SettingsManager: {e}", "ERROR")
                    # Criar settings manager básico como fallback
                    self.settings_manager = self._create_fallback_settings_manager()
            
            # ✅ VERIFICAR python_path COM FALLBACK SEGURO
            if not hasattr(self, 'python_path') or not self.python_path:
                try:
                    if hasattr(self.settings_manager, 'detect_and_save_system_python'):
                        self.python_path = self.settings_manager.detect_and_save_system_python()
                        if self.python_path:
                            self.debug_log(f"✅ Python_path definido: {self.python_path}", "SUCCESS")
                        else:
                            self.python_path = sys.executable
                            self.debug_log(f"⚠️ Usando Python do sistema: {self.python_path}", "WARNING")
                    else:
                        self.python_path = sys.executable
                        self.debug_log(f"⚠️ SettingsManager não tem detect_and_save_system_python, usando: {self.python_path}", "WARNING")
                except Exception as e:
                    self.python_path = sys.executable
                    self.debug_log(f"❌ Erro ao detectar Python, usando fallback: {self.python_path}", "ERROR")
            
            # ✅ GERENCIADOR DE VERSÕES PYTHON (CORRIGIDO)
            try:
                # CORREÇÃO: Importação do arquivo correto
                from python_manager import PythonVersionManager
                self.python_version_manager = PythonVersionManager()
                self.debug_log("✅ Gerenciador de versões Python inicializado", "SUCCESS")
            except ImportError as e:
                self.debug_log(f"⚠️ PythonVersionManager não disponível: {e}", "WARNING")
                self.python_version_manager = None
            except Exception as e:
                self.debug_log(f"⚠️ Erro ao inicializar gerenciador de versões Python: {e}", "WARNING")
                self.python_version_manager = None
            
            # ✅ GERENCIADOR DE TEMAS
            try:
                from core.theme_manager import ThemeManager
                self.theme_manager = ThemeManager()
                self.debug_log("✅ Gerenciador de temas inicializado", "SUCCESS")
            except ImportError as e:
                self.debug_log(f"⚠️ ThemeManager não disponível: {e}", "WARNING")
                self.theme_manager = None
            except Exception as e:
                self.debug_log(f"⚠️ Erro ao inicializar gerenciador de temas: {e}", "WARNING")
                self.theme_manager = None
            
            # ✅ VERIFICADOR DE INDENTAÇÃO
            try:
                from tools.indentation_checker import IndentationChecker
                self.indentation_checker = IndentationChecker()
                self.debug_log("✅ Verificador de indentação inicializado", "SUCCESS")
            except ImportError as e:
                self.debug_log(f"⚠️ IndentationChecker não disponível: {e}", "WARNING")
                self.indentation_checker = None
            except Exception as e:
                self.debug_log(f"⚠️ Erro ao inicializar verificador de indentação: {e}", "WARNING")
                self.indentation_checker = None
            
            # ✅ CONFIGURAÇÃO DE LINGUAGEM
            try:
                from syntax.language_config import LanguageConfig
                self.language_config = LanguageConfig()
                self.debug_log("✅ Configuração de linguagem inicializada", "SUCCESS")
            except ImportError as e:
                self.debug_log(f"⚠️ LanguageConfig não disponível: {e}", "WARNING")
                self.language_config = None
            except Exception as e:
                self.debug_log(f"⚠️ Erro ao inicializar configuração de linguagem: {e}", "WARNING")
                self.language_config = None
            
            # ✅ GERENCIADOR DE SINTAXE
            try:
                from syntax.syntax_manager import LanguageSyntaxManager
                self.language_syntax_manager = LanguageSyntaxManager()
                self.debug_log("✅ Gerenciador de sintaxe inicializado", "SUCCESS")
            except ImportError as e:
                self.debug_log(f"⚠️ LanguageSyntaxManager não disponível: {e}", "WARNING")
                self.language_syntax_manager = None
            except Exception as e:
                self.debug_log(f"⚠️ Erro ao inicializar gerenciador de sintaxe: {e}", "WARNING")
                self.language_syntax_manager = None
    
            # ✅ GERENCIADOR DE CACHE GLOBAL
            try:
                from cache.module_cache import ModuleCacheManager
                global module_cache_manager
                module_cache_manager = ModuleCacheManager()
                self.debug_log("✅ Gerenciador de cache inicializado", "SUCCESS")
            except ImportError as e:
                self.debug_log(f"⚠️ ModuleCacheManager não disponível: {e}", "WARNING")
                module_cache_manager = None
            except Exception as e:
                self.debug_log(f"⚠️ Erro ao inicializar gerenciador de cache: {e}", "WARNING")
                module_cache_manager = None
            
            self.debug_log("✅ Gerenciadores principais inicializados", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"❌ Erro crítico ao inicializar gerenciadores: {e}", "ERROR")
            # Define valores padrão para evitar NoneType errors
            # (adicionar fallbacks aqui se necessário)
           
    def setup_syntax_highlighting_system(self):
        """Configura sistema de syntax highlighting"""
        try:
            self.syntax_highlighting_manager = SyntaxHighlightingManager(self)
            self.debug_log("✅ Sistema de syntax highlighting configurado", "SUCCESS")
        except Exception as e:
            self.debug_log(f"❌ Erro ao configurar syntax highlighting: {e}", "ERROR")

    def setup_autocomplete(self):
        """Configura sistema unificado de autocomplete"""
        try:
            # Sistema de fallback seguro
            class BasicAutoCompleteSystem:
                def __init__(self, parent=None):
                    self.parent = parent
                    self.enabled = True
                    self.suggestions = [
                        "print", "def", "class", "if", "else", "for", "while", 
                        "import", "from", "return", "True", "False", "None"
                    ]
                
                def get_suggestions(self, text, cursor_position, file_path="", project_path=""):
                    return self.suggestions
                
                def show_completions(self, editor, suggestions, position):
                    if suggestions and self.enabled:
                        print(f"📝 Autocomplete: {len(suggestions)} sugestões disponíveis")
            
            # Usar sistema básico
            self.autocomplete_widget = BasicAutoCompleteSystem(self)
            
            # Configurar timer
            self.autocomplete_timer = QTimer()
            self.autocomplete_timer.setSingleShot(True)
            self.autocomplete_timer.timeout.connect(self.trigger_unified_autocomplete)
            
            # Atalho manual
            QShortcut(QKeySequence("Ctrl+Space"), self).activated.connect(
                self.trigger_manual_autocomplete
            )
            
            self.debug_log("✅ Sistema de autocomplete básico configurado", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"❌ Erro crítico no autocomplete: {e}", "ERROR")
            self.autocomplete_widget = type('MinimalAutoComplete', (), {'enabled': False})()

    def setup_lsp_system(self):
        """Configura sistema LSP"""
        try:
            from analysis.lsp_client import LSPManager
            self.lsp_manager = LSPManager(self)
            self.tab_widget.currentChanged.connect(self._on_tab_changed_lsp)
            self.debug_log("✅ Sistema LSP configurado", "SUCCESS")
        except ImportError as e:
            self.debug_log(f"❌ LSP não disponível: {e}", "WARNING")
            self.lsp_manager = None
        except Exception as e:
            self.debug_log(f"❌ Erro ao configurar LSP: {e}", "ERROR")
            self.lsp_manager = None

    # ===== SEÇÃO 3: CONFIGURAÇÃO DA INTERFACE =====
    
    def setup_ui(self):
        """Configura interface do usuário"""
        try:
            self.setWindowTitle("Py Dragon Studio IDE")
            self.setGeometry(100, 100, 1400, 900)
    
            self.set_dark_theme_optimized()
    
            # Layout principal
            self.main_layout = QVBoxLayout()
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.setSpacing(0)
        
            # Widget central
            central_widget = QWidget()
            central_widget.setLayout(self.main_layout)
            self.setCentralWidget(central_widget)

            # Configurar componentes
            self.setup_main_tabs()
            self.setup_central_widget()
            self.setup_docks()
            self.setup_menu()
            self.setup_toolbar()
            self.setup_statusbar()

            self.debug_log("✅ UI configurada com sucesso", "SUCCESS")
    
        except Exception as e:
            self.debug_log(f"❌ Erro ao configurar UI: {e}", "ERROR")

    def setup_main_tabs(self):
        """Configura abas principais"""
        try:
            self.main_tabs = QTabWidget()
            self.main_tabs.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #3e3e42;
                    background-color: #1e1e1e;
                }
                QTabBar::tab {
                    background-color: #2d2d30;
                    color: #cccccc;
                    padding: 8px 16px;
                    border: 1px solid #3e3e42;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                    color: #569cd6;
                }
                QTabBar::tab:hover {
                    background-color: #383838;
                }
            """)
        
            if hasattr(self, 'main_layout'):
                self.main_layout.addWidget(self.main_tabs)
            else:
                self.main_layout = QVBoxLayout()
                central_widget = QWidget()
                central_widget.setLayout(self.main_layout)
                self.setCentralWidget(central_widget)
                self.main_layout.addWidget(self.main_tabs)
                
            self.debug_log("✅ Abas principais configuradas", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao configurar abas principais: {e}", "ERROR")

    def setup_central_widget(self):
        """Configura widget central com splitter"""
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
        
        # Área do minimap
        self.minimap_widget = Minimap()
        self.minimap_widget.setMaximumWidth(150)
        self.minimap_widget.setMinimumWidth(80)
        
        # Adicionar widgets ao splitter
        self.main_splitter.addWidget(self.tab_widget)
        self.main_splitter.addWidget(self.minimap_widget)
        
        # Configurar proporções
        self.main_splitter.setSizes([800, 150])
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 0)
        
        self.setCentralWidget(self.main_splitter)

    def setup_docks(self):
        """Configura todas as docks"""
        try:
            self.setup_left_dock()
            self.setup_bottom_dock()
            self.debug_log("✅ Docks configuradas", "SUCCESS")
        except Exception as e:
            self.debug_log(f"❌ Erro ao configurar docks: {e}", "ERROR")

    def setup_left_dock(self):
        """Configura dock esquerda"""
        left_dock = QDockWidget("Explorer", self)
        left_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        left_dock.setMaximumWidth(300)

        left_tabs = QTabWidget()
        left_tabs.setTabPosition(QTabWidget.West)

        self.setup_file_explorer(left_tabs)
        self.setup_outline_widget(left_tabs)
        self.setup_problems_widget(left_tabs)

        left_dock.setWidget(left_tabs)
        self.addDockWidget(Qt.LeftDockWidgetArea, left_dock)

    def setup_file_explorer(self, parent_tabs):
        """Configura explorador de arquivos"""
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
        self.file_tree.setRootIndex(self.file_model.index(QDir.homePath()))
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(15)
        self.file_tree.setSortingEnabled(True)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_explorer_context_menu)
        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)
    
        explorer_layout.addWidget(self.file_tree)
        parent_tabs.addTab(explorer_widget, "📁 Explorer")

    def setup_outline_widget(self, parent_tabs):
        """Configura widget de outline"""
        self.outline_widget = OutlineWidget(self)
        parent_tabs.addTab(self.outline_widget, "📊 Outline")

    def setup_problems_widget(self, parent_tabs):
        """Configura widget de problemas"""
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
        """Configura dock inferior (Output)"""
        try:
            self.debug_log("Configurando dock inferior...", "INFO")
            
            self.output_tabs = QTabWidget()
            
            # Criar abas básicas
            self.setup_output_tab()
            self.setup_debug_tab() 
            self.setup_errors_tab()
            self.setup_lint_tab()
            self.setup_terminal_tab()
            
            # Criar dock
            bottom_dock = QDockWidget("Output", self)
            bottom_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
            bottom_dock.setWidget(self.output_tabs)
            self.addDockWidget(Qt.BottomDockWidgetArea, bottom_dock)
            
            self.debug_log("✅ Dock inferior configurada", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao configurar dock inferior: {e}", "ERROR")

    def setup_output_tab(self):
        """Configura aba de output"""
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
        """Configura aba de debug"""
        self.debug_text = DebugTerminal(self)
        self.debug_text.setFont(QFont(self.current_font, 10))
        self.output_tabs.addTab(self.debug_text, "🐛 Debug")

    def setup_errors_tab(self):
        """Configura aba de erros"""
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
        """Configura aba de lint"""
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

    def setup_terminal_tab(self):
        """Configura aba de terminal com RealTerminal"""
        try:
            self.debug_log("Configurando aba do terminal REAL...", "INFO")
            
            terminal_container = QWidget()
            terminal_layout = QVBoxLayout(terminal_container)
            terminal_layout.setContentsMargins(0, 0, 0, 0)
            
            try:
                # ✅ USAR REAL TERMINAL
                self.real_terminal = RealTerminal(self)
                terminal_layout.addWidget(self.real_terminal)
                self.debug_log("✅ RealTerminal configurado com sucesso", "SUCCESS")
                
            except Exception as e:
                self.debug_log(f"❌ RealTerminal não disponível: {e}", "ERROR")
                # Fallback básico
                fallback_terminal = QPlainTextEdit()
                fallback_terminal.setReadOnly(True)
                fallback_terminal.setPlainText(f"Terminal não disponível\n\nErro: {str(e)}")
                terminal_layout.addWidget(fallback_terminal)
            
            if hasattr(self, 'output_tabs'):
                self.output_tabs.addTab(terminal_container, "💻 Terminal")
                self.debug_log("✅ Terminal REAL adicionado ao output_tabs", "SUCCESS")
            else:
                self.debug_log("❌ output_tabs não disponível", "ERROR")
                
            self.debug_log("✅ Terminal tab configurado com sucesso", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao configurar terminal tab: {e}", "ERROR")

    def setup_menu(self):
        """Configura menu principal"""
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

    def setup_file_menu(self, menu):
        """Configura menu Arquivo"""
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
        """Configura menu Editar"""
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
        """Configura menu Visualizar"""
        actions = [
            ("📊 Layout Dividido", "Ctrl+\\", self.split_view),
            ("🔍 Zoom In", "Ctrl+=", self.zoom_in),
            ("🔍 Zoom Out", "Ctrl+-", self.zoom_out),
            ("🔍 Zoom Reset", "Ctrl+0", self.zoom_reset),
            ("---", None, None),
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

    def setup_run_menu(self, menu):
        """Configura menu Executar"""
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
        """Configura menu Projeto"""
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
        """Configura menu Ferramentas"""
        # 🐍 SEÇÃO PYTHON
        python_menu = menu.addMenu("🐍 Python")
        
        python_status_action = QAction("📊 Status do Python", self)
        python_status_action.triggered.connect(self.show_python_status)
        python_menu.addAction(python_status_action)
        
        detect_python_action = QAction("🔍 Detectar Python do Sistema", self)
        detect_python_action.triggered.connect(self.detect_system_python)
        python_menu.addAction(detect_python_action)
        
        select_python_action = QAction("🎯 Selecionar Python", self)
        select_python_action.triggered.connect(self.select_python_for_vms)
        python_menu.addAction(select_python_action)
        
        python_manager_action = QAction("📁 Gerenciador de Versões", self)
        python_manager_action.triggered.connect(self.show_python_manager_dialog)
        python_menu.addAction(python_manager_action)
        
        python_menu.addSeparator()
        
        terminal_venv_action = QAction("🔧 Criar Venv (Dinâmico)", self)
        terminal_venv_action.triggered.connect(self.create_venv_dynamic)
        python_menu.addAction(terminal_venv_action)

        test_venv_action = QAction("🧪 Testar Virtual Environment", self)
        test_venv_action.triggered.connect(self.test_venv_creation)
        python_menu.addAction(test_venv_action)
    
        # 📦 SEÇÃO PACOTES
        packages_menu = menu.addMenu("📦 Pacotes")
        
        package_manager_action = QAction("🔧 Gerenciador de Pacotes", self)
        package_manager_action.setShortcut("Ctrl+Shift+P")
        package_manager_action.triggered.connect(self.open_package_manager)
        packages_menu.addAction(package_manager_action)
        
        install_deps_action = QAction("📚 Instalar Dependências", self)
        install_deps_action.triggered.connect(self.install_dependencies)
        packages_menu.addAction(install_deps_action)
        
        manage_packages_action = QAction("⚙️ Gerenciar Pacotes", self)
        manage_packages_action.triggered.connect(self.manage_packages)
        packages_menu.addAction(manage_packages_action)
    
        # 🎨 SEÇÃO TEMAS E INTERFACE
        interface_menu = menu.addMenu("🎨 Interface")
        
        theme_action = QAction("🎨 Gerenciador de Temas", self)
        theme_action.triggered.connect(self.open_theme_manager)
        interface_menu.addAction(theme_action)
        
        font_action = QAction("🔤 Selecionar Fonte...", self)
        font_action.triggered.connect(self.show_font_dialog)
        interface_menu.addAction(font_action)
        
        interface_menu.addSeparator()
        
        toggle_line_numbers = QAction("📊 Alternar Números de Linha", self)
        toggle_line_numbers.triggered.connect(self.toggle_line_numbers)
        interface_menu.addAction(toggle_line_numbers)
        
        toggle_minimap = QAction("🗺️ Alternar Minimap", self)
        toggle_minimap.triggered.connect(self.toggle_minimap)
        interface_menu.addAction(toggle_minimap)
        
        toggle_highlight = QAction("🎯 Alternar Destaque Linha", self)
        toggle_highlight.triggered.connect(self.toggle_current_line_highlight)
        interface_menu.addAction(toggle_highlight)
    
        # 🔧 SEÇÃO FERRAMENTAS DE CÓDIGO
        code_tools_menu = menu.addMenu("🔧 Código")
        
        format_action = QAction("📐 Formatar Código", self)
        format_action.setShortcut("Ctrl+Shift+L")
        format_action.triggered.connect(self.format_code)
        code_tools_menu.addAction(format_action)
        
        find_similar_action = QAction("🔍 Localizador de Textos Similares", self)
        find_similar_action.setShortcut("Ctrl+Shift+F")
        find_similar_action.triggered.connect(self.open_advanced_find_similar)
        code_tools_menu.addAction(find_similar_action)
        
        check_indentation = QAction("📏 Verificar Indentação", self)
        check_indentation.triggered.connect(self.check_indentation_errors)
        code_tools_menu.addAction(check_indentation)
    
        # 🔌 SEÇÃO PLUGINS
        plugins_menu = menu.addMenu("🔌 Plugins")
        
        plugin_manager_action = QAction("🔌 Gerenciador de Plugins", self)
        plugin_manager_action.triggered.connect(self.show_plugin_manager_dialog)
        plugins_menu.addAction(plugin_manager_action)
        
        install_plugin_action = QAction("📥 Instalar Plugin", self)
        install_plugin_action.triggered.connect(self.install_new_plugin)
        plugins_menu.addAction(install_plugin_action)
        
        refresh_plugins_action = QAction("🔄 Atualizar Plugins", self)
        refresh_plugins_action.triggered.connect(self.refresh_plugins)
        plugins_menu.addAction(refresh_plugins_action)
        
        test_plugins_action = QAction("🧪 Testar Sistema de Plugins", self)
        test_plugins_action.triggered.connect(self.test_plugins_system)
        plugins_menu.addAction(test_plugins_action)
    
        # ⚙️ SEÇÃO CONFIGURAÇÕES
        menu.addSeparator()
        
        settings_action = QAction("⚙️ Configurações", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

    def setup_help_menu(self, menu):
        """Configura menu Ajuda"""
        actions = [
            ("📚 Documentação", "F1", self.show_documentation),
            ("🐛 Reportar Bug", None, self.report_bug),
            ("💡 Sugerir Feature", None, self.suggest_feature),
            ("---", None, None),
            ("ℹ️ Sobre", None, self.show_about)
        ]
        self.create_menu_actions(menu, actions)

    def create_menu_actions(self, menu, actions):
        """Cria ações do menu"""
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

    def create_venv_with_persisted_python(self):
        """Cria virtualenv usando Python válido - VERSÃO CORRIGIDA E ORGANIZADA"""
        try:
            if not self.project_path:
                QMessageBox.information(self, "Virtualenv", "Abra um projeto primeiro!")
                return False
    
            # ✅ VERIFICAR SE O PROJETO TEM ESPAÇOS NO CAMINHO
            if ' ' in self.project_path:
                reply = QMessageBox.question(
                    self,
                    "Caminho com espaços",
                    f"⚠️  O caminho do projeto contém espaços:\n{self.project_path}\n\n"
                    f"Isso pode causar problemas com virtualenv!\n\n"
                    f"Deseja continuar mesmo assim?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return False
    
            venv_name, ok = QInputDialog.getText(
                self,
                "Criar Virtualenv", 
                "Nome do virtualenv:",
                text="venv"
            )
    
            if not ok or not venv_name:
                return False
    
            venv_path = os.path.join(self.project_path, venv_name)
            
            # ✅ VERIFICAÇÕES COMPLETAS DO CAMINHO
            if not self._is_valid_venv_path(venv_path):
                QMessageBox.critical(
                    self,
                    "Caminho inválido",
                    f"❌ O caminho para o virtualenv é inválido:\n{venv_path}\n\n"
                    f"Certifique-se de que:\n"
                    f"• O projeto está em local acessível\n"
                    f"• Você tem permissão de escrita\n"
                    f"• O caminho não contém caracteres especiais\n"
                    f"• Há espaço suficiente em disco"
                )
                return False
            
            # ✅ VERIFICAR SE JÁ EXISTE
            if os.path.exists(venv_path):
                reply = QMessageBox.question(
                    self,
                    "Virtualenv já existe",
                    f"O virtualenv '{venv_name}' já existe.\n\nDeseja sobrescrever?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    # Tentar usar o existente
                    if self.is_valid_venv(venv_path):
                        success = self.activate_venv_in_project(venv_path)
                        if success:
                            QMessageBox.information(
                                self,
                                "Virtualenv Ativado",
                                f"✅ Virtualenv existente ativado:\n{venv_path}"
                            )
                        return success
                    else:
                        QMessageBox.warning(
                            self,
                            "Virtualenv Inválido",
                            f"O virtualenv existente é inválido.\n\nDeseja recriá-lo?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return False
                
                elif reply == QMessageBox.Cancel:
                    return False
                
                # Remover existente se usuário confirmar
                try:
                    self.debug_log(f"🔄 Removendo venv existente: {venv_path}", "INFO")
                    shutil.rmtree(venv_path)
                    # Pequena pausa para garantir que foi removido
                    import time
                    time.sleep(1)
                except Exception as e:
                    QMessageBox.critical(
                        self, 
                        "Erro", 
                        f"Erro ao remover venv existente:\n{str(e)}"
                    )
                    return False
    
            # ✅ OBTER PYTHON VÁLIDO - AGORA COM DETECÇÃO DINÂMICA
            python_exec = self._detect_best_python_for_venv()  # ← MÉTODO ATUALIZADO!
            
            if not python_exec:
                QMessageBox.critical(
                    self,
                    "Python não encontrado",
                    "❌ Não foi possível encontrar um Python válido para criar o virtualenv.\n\n"
                    "Verifique se:\n"
                    "• Python 3.6+ está instalado\n"
                    "• O módulo 'venv' está disponível\n"
                    "• O Python está no PATH do sistema"
                )
                return False
            
            self.debug_log(f"🔄 Criando virtualenv com Python: {python_exec}", "INFO")
            
            # ✅ VERIFICAR MÓDULO VENV
            if not self._check_venv_module(python_exec):
                QMessageBox.critical(
                    self,
                    "Módulo venv não disponível",
                    f"❌ O Python selecionado não tem o módulo 'venv':\n{python_exec}\n\n"
                    f"Para corrigir:\n"
                    f"• No Ubuntu/Debian: sudo apt-get install python3-venv\n"
                    f"• No Windows: Instale o Python pelo site oficial\n"
                    f"• No Mac: brew install python3"
                )
                return False
    
            # ✅ MOSTRAR PROGRESSO
            progress = QProgressDialog(
                f"Criando virtualenv com:\n{python_exec}", 
                "Cancelar", 0, 0, self
            )
            progress.setWindowTitle("Criando Virtual Environment")
            progress.setModal(True)
            progress.show()
            QApplication.processEvents()
    
            # ✅ EXECUTAR DIAGNÓSTICO ANTES DA CRIAÇÃO
            self.debug_log("🔍 Executando diagnóstico pré-criação...", "INFO")
            self.diagnose_venv_creation(venv_path, python_exec)
    
            # ✅ CRIAR VIRTUALENV
            try:
                self.debug_log(f"🔨 Executando: {python_exec} -m venv {venv_path}", "INFO")
                
                result = subprocess.run(
                    [python_exec, "-m", "venv", venv_path],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path,
                    timeout=120
                )
    
                progress.close()
    
                if result.returncode == 0:
                    # ✅ EXECUTAR DIAGNÓSTICO APÓS CRIAÇÃO
                    self.debug_log("🔍 Executando diagnóstico pós-criação...", "INFO")
                    self.diagnose_venv_creation(venv_path, python_exec)
                    
                    # ✅ VERIFICAR SE FOI CRIADO COM SUCESSO
                    if self.is_valid_venv(venv_path):
                        self.venv_path = venv_path
                        self.debug_log(f"✅ Virtualenv criado e validado: {venv_path}", "SUCCESS")
                        
                        # ✅ ATIVAR AUTOMATICAMENTE
                        success = self.activate_venv_in_project(venv_path)
                        
                        if success:
                            version_info = self.settings_manager.get_python_version_info(python_exec)
                            QMessageBox.information(
                                self, 
                                "Sucesso", 
                                f"✅ Virtualenv criado com sucesso!\n\n"
                                f"🐍 Python: {version_info}\n"
                                f"📁 Local: {venv_path}\n"
                                f"⚡ Status: Ativado automaticamente\n\n"
                                f"O terminal foi configurado para usar este ambiente."
                            )
                            return True
                        else:
                            QMessageBox.warning(
                                self,
                                "Aviso",
                                f"Virtualenv criado mas não foi possível ativar:\n{venv_path}\n\n"
                                f"Você pode ativá-lo manualmente no terminal."
                            )
                            return True
                    else:
                        # Diagnóstico detalhado do problema
                        error_details = self.get_venv_error_details(venv_path, python_exec)
                        QMessageBox.critical(
                            self,
                            "Virtualenv inválido",
                            f"❌ O virtualenv foi criado mas é inválido:\n{venv_path}\n\n"
                            f"Detalhes do problema:\n{error_details}\n\n"
                            f"Tente:\n"
                            f"• Usar outro Python\n"
                            f"• Verificar permissões\n"
                            f"• Criar em outro local"
                        )
                        return False
                else:
                    error_msg = result.stderr if result.stderr else "Erro desconhecido"
                    self.debug_log(f"❌ Erro ao criar venv: {error_msg}", "ERROR")
                    
                    # ✅ TENTAR COM PYTHON DO SISTEMA COMO FALLBACK
                    if python_exec != sys.executable:
                        reply = QMessageBox.question(
                            self,
                            "Falha na criação",
                            f"❌ Falha ao criar virtualenv:\n{error_msg}\n\n"
                            f"Deseja tentar com o Python do sistema?\n{sys.executable}",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.Yes
                        )
                        
                        if reply == QMessageBox.Yes:
                            if self._check_venv_module(sys.executable):
                                self.settings_manager.set_selected_python(sys.executable)
                                # Tentar novamente com Python do sistema
                                QTimer.singleShot(500, self.create_venv_with_persisted_python)
                            else:
                                QMessageBox.critical(
                                    self,
                                    "Módulo venv não disponível",
                                    "O Python do sistema também não tem o módulo 'venv'.\n\n"
                                    "Instale o python3-venv ou equivalente."
                                )
                    else:
                        QMessageBox.critical(
                            self,
                            "Erro na criação",
                            f"❌ Falha ao criar virtualenv:\n{error_msg}\n\n"
                            f"Verifique:\n"
                            f"• Permissões no diretório\n"
                            f"• Espaço em disco\n"
                            f"• Se o Python está funcionando"
                        )
                    return False
    
            except subprocess.TimeoutExpired:
                progress.close()
                QMessageBox.critical(
                    self, 
                    "Timeout", 
                    "⏰ Timeout ao criar virtualenv.\n\n"
                    "O processo demorou muito para responder.\n"
                    "Possíveis causas:\n"
                    "• Disco lento\n"
                    "• Muitos arquivos no projeto\n"
                    "• Problemas de permissão"
                )
                return False
    
        except Exception as e:
            self.debug_log(f"❌ Erro inesperado ao criar venv: {e}", "ERROR")
            QMessageBox.critical(
                self, 
                "Erro inesperado", 
                f"❌ Erro inesperado:\n{str(e)}\n\n"
                f"Tente:\n"
                f"• Reiniciar o IDE\n"
                f"• Verificar permissões\n"
                f"• Usar outro local para o projeto"
            )
            return False
    def setup_toolbar(self):
        """Configura toolbar principal"""
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

        for action_data in actions:
            if len(action_data) == 4:
                icon, text, shortcut, callback = action_data
            elif len(action_data) == 3:
                icon, text, shortcut = action_data
                callback = None
            else:
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
        """Configura statusbar"""
        status_bar = self.statusBar()
        
        self.file_info_label = QLabel("Sem arquivo")
        self.scope_info_label = QLabel("Escopo: Global")
        self.cursor_info_label = QLabel("Linha: 1, Coluna: 1")
        self.project_info_label = QLabel("Sem projeto")
        self.status_progress = StatusBarProgress()
    
        status_bar.addWidget(self.file_info_label)
        status_bar.addWidget(self.scope_info_label)
        status_bar.addPermanentWidget(self.cursor_info_label)
        status_bar.addPermanentWidget(self.project_info_label)
        status_bar.addPermanentWidget(self.status_progress)

    def setup_connections(self):
        """Configura conexões entre sinais e slots"""
        self.file_tree.doubleClicked.connect(self.open_from_tree)
        self.file_tree.customContextMenuRequested.connect(self.show_explorer_context_menu)
        self.problems_list.itemClicked.connect(self.jump_to_error)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.refresh_explorer_btn.triggered.connect(self.refresh_explorer)
        self.new_file_btn.triggered.connect(self.create_new_file_in_explorer)
        self.new_folder_btn.triggered.connect(self.create_new_folder_in_explorer)
        self.clear_problems_btn.triggered.connect(self.clear_problems)
        self.run_lint_btn.triggered.connect(self.run_linter)
        self.tab_widget.currentChanged.connect(self.update_cursor_info)

    def setup_shortcuts(self):
        """Configura atalhos globais"""
        # Atalhos básicos de edição
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self).activated.connect(self.redo)
        QShortcut(QKeySequence("Ctrl+X"), self).activated.connect(self.cut)
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self.copy)
        QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(self.paste)
        QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(self.select_all)
        
        # Navegação
        QShortcut("Ctrl+Tab", self).activated.connect(self.next_tab)
        QShortcut("Ctrl+Shift+Tab", self).activated.connect(self.previous_tab)
        QShortcut("Ctrl+P", self).activated.connect(self.show_command_palette)
        
        # Folding
        QShortcut("Alt+Left", self).activated.connect(self.collapse_all_folds)
        QShortcut("Alt+Right", self).activated.connect(self.expand_all_folds)
        QShortcut("Alt+L", self).activated.connect(self.toggle_fold)
        
        # Interface
        QShortcut("Ctrl+Shift+M", self).activated.connect(self.toggle_minimap)
        QShortcut("Ctrl+L", self).activated.connect(self.toggle_line_numbers)
        QShortcut("Ctrl+Shift+O", self).activated.connect(self.focus_outline)
        QShortcut("Ctrl+Shift+H", self).activated.connect(self.toggle_current_line_highlight)
        QShortcut("Ctrl+Shift+C", self).activated.connect(self.clear_indicators)

    # ===== SEÇÃO 4: MÉTODOS DE INICIALIZAÇÃO TARDIA =====
    
    def initialize_delayed_systems(self):
        """Inicializa sistemas que dependem da UI estar carregada"""
        try:
            self.debug_log("🔄 Inicializando sistemas atrasados...")
            
            self.setup_scope_header()
            self.setup_indicators()
            QTimer.singleShot(200, self.setup_undo_redo_connections)
            
            if hasattr(self, 'outline_widget'):
                QTimer.singleShot(300, self.outline_widget.refresh_outline)
            
            self.debug_log("✅ Sistemas atrasados inicializados", "SUCCESS")
        
        except Exception as e:
            self.debug_log(f"❌ Erro em sistemas atrasados: {e}", "ERROR")

    def setup_scope_header(self):
        """Configura header de escopo"""
        try:
            self.current_class = "Global"
            self.current_function = "Nenhuma"
            self.tab_widget.currentChanged.connect(self.update_scope_display)
            self.debug_log("✅ Header de escopo configurado", "SUCCESS")
        except Exception as e:
            self.debug_log(f"⚠️ Erro ao configurar header de escopo: {e}", "WARNING")

    def setup_indicators(self):
        """Configura indicadores visuais"""
        try:
            self.current_line_highlight = True
            self.show_line_numbers = True
            self.show_minimap = True
            
            self.indicator_colors = {
                'current_line': QColor(45, 45, 48, 80),
                'error': QColor(255, 0, 0, 50),
                'warning': QColor(255, 255, 0, 50),
                'info': QColor(0, 0, 255, 30)
            }
            
            self.tab_widget.currentChanged.connect(self.update_indicators)
            self.debug_log("✅ Indicadores visuais configurados", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"⚠️ Erro ao configurar indicadores: {e}", "WARNING")

    def setup_undo_redo_connections(self):
        """Configura conexões para undo/redo"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'document'):
            try:
                editor.document().undoAvailable.connect(self.update_undo_action)
                editor.document().redoAvailable.connect(self.update_redo_action)
                self.debug_log("✅ Conexões undo/redo configuradas", "SUCCESS")
            except Exception as e:
                self.debug_log(f"⚠️ Erro ao configurar undo/redo: {e}", "WARNING")

    # ===== SEÇÃO 5: MÉTODOS DE EDITOR =====
    
    def get_current_editor(self):
        """Obtém o editor atual de forma robusta"""
        try:
            if not hasattr(self, 'tab_widget') or self.tab_widget.count() == 0:
                return None
                
            current_widget = self.tab_widget.currentWidget()
            if current_widget:
                if hasattr(current_widget, 'editor'):
                    return current_widget.editor
                elif isinstance(current_widget, (QPlainTextEdit, UnifiedCodeEditor)):
                    return current_widget
            return None
        except Exception as e:
            self.debug_log(f"❌ Erro em get_current_editor: {e}", "ERROR")
            return None

    def setup_editor_connections(self, editor):
        """Configura conexões para detectar modificações"""
        if editor and hasattr(editor, 'document'):
            try:
                editor.document().modificationChanged.connect(self.on_document_modified)
                editor.document().undoAvailable.connect(self.update_undo_redo_actions)
                editor.document().redoAvailable.connect(self.update_undo_redo_actions)
                self.debug_log("✅ Conexões do editor configuradas", "SUCCESS")
            except Exception as e:
                self.debug_log(f"❌ Erro ao configurar conexões do editor: {e}", "ERROR")

    def on_document_modified(self, modified):
        """Atualiza interface quando documento é modificado"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            tab_text = self.tab_widget.tabText(current_index)
            
            if modified and not tab_text.endswith(' *'):
                self.tab_widget.setTabText(current_index, tab_text + ' *')
            elif not modified and tab_text.endswith(' *'):
                self.tab_widget.setTabText(current_index, tab_text[:-2])

    def update_undo_redo_actions(self):
        """Atualiza estado das ações undo/redo"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'document'):
            undo_available = editor.document().isUndoAvailable()
            redo_available = editor.document().isRedoAvailable()
            # Aqui você pode atualizar o estado dos botões na toolbar

    # ===== SEÇÃO 6: MÉTODOS DE ARQUIVO E PROJETO =====
    
    def new_file(self):
        """Cria um novo arquivo"""
        dialog = NewFileDialog(self)
        if dialog.exec():
            file_name = dialog.get_file_name()
            if file_name:
                try:
                    editor = UnifiedCodeEditor(
                        text="",
                        cursor_position=0,
                        file_path=None,
                        project_path=self.project_path,
                        parent=self
                    )
                    
                    editor.setFocusPolicy(Qt.StrongFocus)
    
                    editor_tab = QWidget()
                    layout = QVBoxLayout(editor_tab)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.addWidget(editor)
                    editor_tab.file_path = None
                    editor_tab.editor = editor
                    editor_tab.is_new_file = True
                    editor_tab.file_name = file_name
    
                    self.setup_editor_connections(editor)
    
                    index = self.tab_widget.addTab(editor_tab, f"📄 {file_name}")
                    self.tab_widget.setCurrentIndex(index)
    
                    editor.setFocus()
                    self.update_file_info(None)
                
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Erro ao criar novo arquivo: {str(e)}")

    def open_file(self, file_path=None):
        """Abre um arquivo"""
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
                
                # Configura conexões
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
                self.debug_log(f"❌ Erro ao abrir arquivo: {e}", "ERROR")
                QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo:\n{str(e)}")

    def save_file(self):
        """Salva o arquivo atual"""
        try:
            current_widget = self.tab_widget.currentWidget()
            if not current_widget:
                QMessageBox.information(self, "Informação", "Nenhum arquivo para salvar.")
                return False

            if hasattr(current_widget, 'editor'):
                editor = current_widget.editor
                file_path = getattr(current_widget, 'file_path', None)
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(editor.toPlainText())
                    
                    editor.document().setModified(False)
                    
                    index = self.tab_widget.currentIndex()
                    tab_text = self.tab_widget.tabText(index)
                    if tab_text.endswith(' *'):
                        self.tab_widget.setTabText(index, tab_text[:-2])
                    
                    self.statusBar().showMessage(f"✅ Arquivo salvo: {os.path.basename(file_path)}", 3000)
                    return True
                else:
                    return self.save_file_as()
            else:
                QMessageBox.information(self, "Informação", "Tipo de editor não suportado.")
                return False
                
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
            return False

    def save_file_as(self):
        """Salva o arquivo atual com novo nome"""
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

                    current_widget.file_path = new_path
                    
                    index = self.tab_widget.currentIndex()
                    self.tab_widget.setTabText(index, os.path.basename(new_path))
                    
                    editor.document().setModified(False)
                    
                    self.update_file_info(new_path)
                    self.statusBar().showMessage(f"✅ Arquivo salvo como: {os.path.basename(new_path)}", 3000)
                    return True
                    
            return False
            
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
            return False

    def save_all_files(self):
        """Salva todos os arquivos abertos"""
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

    def set_project(self, project_path=None):
        """Define o projeto atual com ativação automática de venv"""
        try:
            if not project_path:
                project_path = QFileDialog.getExistingDirectory(
                    self, "Selecionar Projeto", self.project_path or QDir.homePath()
                )
    
            if project_path:
                self.project_path = project_path
                self.project_info_label.setText(f"📁 {os.path.basename(project_path)}")
                self.refresh_explorer()
                
                # ✅ ATIVAR VENV AUTOMATICAMENTE
                self.auto_activate_venv(project_path)
                
                # ✅ ATUALIZAR TERMINAL REAL
                if hasattr(self, 'real_terminal') and self.real_terminal:
                    self.real_terminal.change_directory(project_path)
                    # Forçar detecção de venv no terminal
                    QTimer.singleShot(1000, lambda: self.real_terminal.auto_detect_and_activate_venv())
                
                self.debug_log(f"✅ Projeto definido: {project_path}", "SUCCESS")
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao definir projeto: {e}", "ERROR")

    # ===== SEÇÃO 7: MÉTODOS DE EDIÇÃO =====
    
    def undo(self):
        """Desfaz a última ação"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'document'):
            try:
                if editor.document().isUndoAvailable():
                    editor.undo()
                    self.statusBar().showMessage("↶ Ação desfeita", 2000)
                    self.update_undo_redo_actions()
                else:
                    self.statusBar().showMessage("ℹ️ Nada para desfazer", 2000)
            except Exception as e:
                self.debug_log(f"❌ Erro ao desfazer: {e}", "ERROR")

    def redo(self):
        """Refaz a última ação"""
        editor = self.get_current_editor()
        if editor and hasattr(editor, 'document'):
            try:
                if editor.document().isRedoAvailable():
                    editor.redo()
                    self.statusBar().showMessage("↷ Ação refeita", 2000)
                    self.update_undo_redo_actions()
                else:
                    self.statusBar().showMessage("ℹ️ Nada para refazer", 2000)
            except Exception as e:
                self.debug_log(f"❌ Erro ao refazer: {e}", "ERROR")

    def cut(self):
        """Recorta texto selecionado"""
        editor = self.get_current_editor()
        if editor:
            try:
                editor.cut()
                self.statusBar().showMessage("✂️ Texto recortado", 2000)
            except Exception as e:
                self.debug_log(f"❌ Erro ao recortar: {e}", "ERROR")

    def copy(self):
        """Copia texto selecionado"""
        editor = self.get_current_editor()
        if editor:
            try:
                editor.copy()
                self.statusBar().showMessage("📋 Texto copiado", 2000)
            except Exception as e:
                self.debug_log(f"❌ Erro ao copiar: {e}", "ERROR")

    def paste(self):
        """Cola texto da área de transferência"""
        editor = self.get_current_editor()
        if editor:
            try:
                editor.paste()
                self.statusBar().showMessage("📝 Texto colado", 2000)
            except Exception as e:
                self.debug_log(f"❌ Erro ao colar: {e}", "ERROR")

    def select_all(self):
        """Seleciona todo o texto no editor atual"""
        editor = self.get_current_editor()
        if editor:
            editor.selectAll()

    # ===== SEÇÃO 8: MÉTODOS DE VISUALIZAÇÃO =====
    
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
        """Mostra/esconde o dock do terminal REAL"""
        try:
            dock_found = False
            
            for dock in self.findChildren(QDockWidget):
                if dock.windowTitle() == "Output":
                    is_visible = dock.isVisible()
                    
                    if not is_visible:
                        dock.show()
                        dock.raise_()
                        
                        if hasattr(self, 'output_tabs'):
                            for i in range(self.output_tabs.count()):
                                if self.output_tabs.tabText(i) == "💻 Terminal":
                                    self.output_tabs.setCurrentIndex(i)
                                    # Focar no terminal
                                    if hasattr(self, 'real_terminal') and self.real_terminal:
                                        self.real_terminal.setFocus()
                                    break
                        
                        self.debug_log("✅ Terminal REAL mostrado e focado", "SUCCESS")
                    else:
                        dock.hide()
                        self.debug_log("✅ Terminal REAL ocultado", "SUCCESS")
                    
                    dock_found = True
                    break
    
            if not dock_found:
                self.debug_log("❌ Dock 'Output' não encontrado", "ERROR")
                self.setup_bottom_dock()
                    
        except Exception as e:
            self.debug_log(f"❌ Erro ao alternar terminal REAL: {e}", "ERROR")

    def toggle_minimap(self):
        """Alterna visibilidade do minimap"""
        if hasattr(self, 'minimap_widget'):
            self.minimap_widget.setVisible(not self.minimap_widget.isVisible())
            
            if self.minimap_widget.isVisible():
                self.main_splitter.setSizes([700, 100])
            else:
                self.main_splitter.setSizes([1000, 0])

    def toggle_line_numbers(self):
        """Alterna a visibilidade dos números de linha"""
        try:
            self.show_line_numbers = not self.show_line_numbers
            editor = self.get_current_editor()
            if editor and hasattr(editor, 'line_number_area'):
                editor.line_number_area.setVisible(self.show_line_numbers)
                
            status = "ativados" if self.show_line_numbers else "desativados"
            self.statusBar().showMessage(f"📊 Números de linha {status}", 2000)
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao alternar números de linha: {e}", "ERROR")

    def toggle_current_line_highlight(self):
        """Alterna o destaque da linha atual"""
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
                    editor.setExtraSelections([])
                    
            status = "ativado" if self.current_line_highlight else "desativado"
            self.statusBar().showMessage(f"📝 Destaque da linha atual {status}", 2000)
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao alternar destaque da linha: {e}", "ERROR")

    def show_font_dialog(self):
        """Mostra diálogo para selecionar fonte"""
        font, ok = QFontDialog.getFont()
        if ok:
            self.current_font = font.family()
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if hasattr(widget, 'editor'):
                    widget.editor.setFont(font)

    def set_light_theme(self):
        """Aplica tema claro"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        QApplication.setPalette(palette)

    def set_dark_theme_optimized(self):
        """Aplica tema escuro otimizado"""
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
        palette.setColor(QPalette.HighlightedText, highlight_text)

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

    # ===== SEÇÃO 9: MÉTODOS DE EXECUÇÃO =====
    
    def run_code(self):
        """Executa o código atual"""
        current_widget = self.tab_widget.currentWidget()

        if not current_widget or not hasattr(current_widget, 'file_path'):
            QMessageBox.information(self, "Informação", "Nenhum arquivo para executar.")
            return

        file_path = current_widget.file_path
        if not file_path or not file_path.endswith('.py'):
            QMessageBox.information(self, "Informação", "Apenas arquivos Python podem ser executados.")
            return

        try:
            self.save_file()

            self.output_text.clear()
            self.output_tabs.setCurrentWidget(self.output_text)
            self.output_text.appendPlainText(f"🚀 Executando: {os.path.basename(file_path)}")
            self.output_text.appendPlainText("=" * 50 + "\n")

            python_exec = self.get_python_executable()

            self.current_process = QProcess(self)
            self.current_process.setProcessChannelMode(QProcess.MergedChannels)

            def handle_output():
                data = self.current_process.readAll().data().decode('utf-8', errors='ignore')
                if data:
                    self.output_text.appendPlainText(data)

            def handle_finished(exit_code, exit_status):
                if exit_code == 0:
                    self.output_text.appendPlainText(f"\n✅ Execução concluída com sucesso!")
                else:
                    self.output_text.appendPlainText(f"\n❌ Execução falhou (código: {exit_code})")

            self.current_process.readyRead.connect(handle_output)
            self.current_process.finished.connect(handle_finished)

            working_dir = self.project_path or os.path.dirname(file_path)
            self.current_process.setWorkingDirectory(working_dir)

            self.current_process.start(python_exec, [file_path])

            if not self.current_process.waitForStarted(5000):
                self.output_text.appendPlainText("❌ Erro: Não foi possível iniciar o processo Python")
                return

        except Exception as e:
            self.output_text.appendPlainText(f"💥 Erro na execução: {str(e)}")

    def debug_code(self):
        """Executa o código em modo debug"""
        try:
            current_widget = self.tab_widget.currentWidget()
            if not current_widget or not hasattr(current_widget, 'file_path'):
                QMessageBox.information(self, "Informação", "Nenhum arquivo para depurar.")
                return

            file_path = current_widget.file_path
            if not file_path or not file_path.endswith('.py'):
                QMessageBox.information(self, "Informação", "Apenas arquivos Python podem ser depurados.")
                return

            self.save_file()

            self.output_tabs.setCurrentWidget(self.debug_text)
            self.debug_text.clear()
            
            if self.debug_process and self.debug_process.state() == QProcess.Running:
                self.debug_process.kill()
                self.debug_process.waitForFinished(1000)

            self.debug_process = QProcess(self)
            self.debug_process.readyReadStandardOutput.connect(self.handle_debug_output)
            self.debug_process.readyReadStandardError.connect(self.handle_debug_error)
            self.debug_process.finished.connect(self.handle_debug_finished)

            python_exec = self.get_python_executable()
            cmd = [python_exec, "-u", "-m", "pdb", file_path]
            
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

    def handle_debug_output(self):
        """Processa saída do debug"""
        try:
            if self.debug_process and self.debug_mode:
                data = self.debug_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
                if data:
                    self.debug_text.appendPlainText(data)
        except Exception as e:
            self.debug_log(f"❌ Erro ao processar output do debug: {e}", "ERROR")

    def handle_debug_error(self):
        """Processa erro do debug"""
        try:
            if self.debug_process and self.debug_mode:
                data = self.debug_process.readAllStandardError().data().decode('utf-8', errors='ignore')
                if data:
                    self.debug_text.appendPlainText(f"[ERRO] {data}")
        except Exception as e:
            self.debug_log(f"❌ Erro ao processar erro do debug: {e}", "ERROR")

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
            self.debug_log(f"❌ Erro ao enviar comando de debug: {e}", "ERROR")
        return False

    # ===== SEÇÃO 10: MÉTODOS DE NAVEGAÇÃO E INTERAÇÃO =====
    
    def on_tab_changed(self, index):
        """Atualiza a interface quando a aba muda"""
        try:
            if index >= 0:
                widget = self.tab_widget.widget(index)
                if hasattr(widget, 'file_path') and widget.file_path:
                    self.update_file_info(widget.file_path)
                    
                    if hasattr(widget, 'editor') and hasattr(self, 'syntax_highlighting_manager'):
                        self.syntax_highlighting_manager.setup_editor_highlighter(widget.editor, widget.file_path)

                    if hasattr(self, 'minimap_widget'):
                        self.minimap_widget.set_main_editor(widget.editor)
                        
                    if hasattr(self, 'outline_widget'):
                        self.outline_widget.refresh_outline()
                        
                    QTimer.singleShot(100, self.setup_undo_redo_connections)
                    
                else:
                    self.update_file_info(None)
                    if hasattr(self, 'minimap_widget'):
                        self.minimap_widget.clear()
                        
                    if hasattr(self, 'outline_widget'):
                        self.outline_widget.tree_widget.clear()
                        
        except Exception as e:
            self.debug_log(f"❌ Erro em on_tab_changed: {e}", "ERROR")

    def update_cursor_info(self):
        """Atualiza informações do cursor na statusbar"""
        try:
            editor = self.get_current_editor()
            if editor and hasattr(self, 'cursor_info_label') and self.cursor_info_label:
                cursor = editor.textCursor()
                line = cursor.blockNumber() + 1
                column = cursor.columnNumber() + 1
                self.cursor_info_label.setText(f"Linha: {line}, Coluna: {column}")
                
                if hasattr(editor, 'file_path') and editor.file_path:
                    self.update_file_info(editor.file_path)
                    
        except Exception as e:
            self.debug_log(f"❌ Erro em update_cursor_info: {e}", "ERROR")

    def update_file_info(self, file_path):
        """Atualiza informações do arquivo na statusbar"""
        if file_path and os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path)
                size_str = f"{size} bytes" if size < 1024 else f"{size / 1024:.1f} KB"

                try:
                    with open(file_path, 'rb') as f:
                        raw = f.read()
                    encoding = "UTF-8"
                except:
                    encoding = "Desconhecido"

                file_name = os.path.basename(file_path)
                self.file_info_label.setText(f"📄 {file_name} ({size_str}, {encoding})")

                editor = self.get_current_editor()
                if editor:
                    cursor = editor.textCursor()
                    line = cursor.blockNumber() + 1
                    column = cursor.columnNumber() + 1
                    self.cursor_info_label.setText(f"Linha: {line}, Coluna: {column}")

            except Exception as e:
                self.file_info_label.setText("📄 Informações indisponíveis")
        else:
            self.file_info_label.setText("📄 Sem arquivo")
            self.cursor_info_label.setText("Linha: 1, Coluna: 1")

    def update_scope_display(self, index):
        """Atualiza o display do escopo quando a aba muda"""
        try:
            if index >= 0:
                widget = self.tab_widget.widget(index)
                if hasattr(widget, 'editor'):
                    widget.editor.cursorPositionChanged.connect(
                        lambda: self.update_scope_from_editor(widget.editor)
                    )
                    self.update_scope_from_editor(widget.editor)
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar display de escopo: {e}", "ERROR")

    def update_scope_from_editor(self, editor):
        """Atualiza o escopo baseado na posição do cursor"""
        try:
            if not editor:
                return
                
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            text = editor.toPlainText()
            lines = text.split('\n')
            
            current_class = "Global"
            for i in range(line - 1, -1, -1):
                if i < len(lines):
                    line_text = lines[i].strip()
                    if line_text.startswith('class '):
                        class_match = re.match(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line_text)
                        if class_match:
                            current_class = class_match.group(1)
                            break
            
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
            self.update_scope_in_statusbar()
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar escopo do editor: {e}", "ERROR")

    def update_scope_in_statusbar(self):
        """Atualiza as informações de escopo na statusbar"""
        try:
            scope_text = f"Escopo: {self.current_class}"
            if self.current_function != "Nenhuma":
                scope_text += f".{self.current_function}()"
            
            if hasattr(self, 'scope_info_label'):
                self.scope_info_label.setText(scope_text)
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar escopo na statusbar: {e}", "ERROR")

    def jump_to_error(self, item):
        """Salta para erro na lista de problemas"""
        try:
            if not item:
                return
                
            data = item.data(Qt.UserRole)
            if not data:
                return

            file_path = data.get('file')
            line_str = data.get('line', '0')

            try:
                line_num = int(line_str) - 1

                for i in range(self.tab_widget.count()):
                    widget = self.tab_widget.widget(i)
                    if hasattr(widget, 'file_path') and widget.file_path == file_path:
                        self.tab_widget.setCurrentIndex(i)

                        editor = widget.editor
                        cursor = editor.textCursor()
                        document = editor.document()

                        block = document.findBlockByLineNumber(line_num)
                        if block.isValid():
                            cursor.setPosition(block.position())
                            editor.setTextCursor(cursor)
                            editor.setFocus()
                            editor.centerCursor()
                        break

            except ValueError:
                QMessageBox.warning(self, "Erro", f"Número de linha inválido: {line_str}")
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao saltar para erro: {e}", "ERROR")
            QMessageBox.warning(self, "Erro", f"Falha ao navegar para erro:\n{str(e)}")

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

    def close_tab(self, index):
        """Fecha uma aba com confirmação se não salvo"""
        try:
            if index < 0 or index >= self.tab_widget.count():
                return

            widget = self.tab_widget.widget(index)
            
            if hasattr(widget, 'editor') and widget.editor.document().isModified():
                reply = QMessageBox.question(
                    self,
                    "Arquivo não salvo",
                    f"Deseja salvar as alterações em {self.tab_widget.tabText(index)}?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )

                if reply == QMessageBox.Save:
                    self.save_file()
                elif reply == QMessageBox.Cancel:
                    return

            self.tab_widget.removeTab(index)
            self.debug_log(f"✅ Aba fechada: índice {index}", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao fechar aba: {e}", "ERROR")

    # ===== SEÇÃO 11: MÉTODOS DE EXPLORER =====
    
    def open_from_tree(self, index):
        """Abre arquivo a partir do explorador"""
        try:
            if not index.isValid():
                return
                
            file_path = self.file_model.filePath(index)
            if os.path.isfile(file_path):
                self.open_file(file_path)
            else:
                self.set_project(file_path)
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao abrir do tree: {e}", "ERROR")

    def refresh_explorer(self):
        """Atualiza o explorador de arquivos"""
        try:
            if hasattr(self, 'file_model') and self.file_model:
                root_path = self.project_path or QDir.homePath()
                self.file_tree.setRootIndex(self.file_model.index(root_path))
                self.debug_log("✅ Explorer atualizado", "SUCCESS")
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar explorer: {e}", "ERROR")

    def show_explorer_context_menu(self, position):
        """Menu contexto do explorador"""
        try:
            index = self.file_tree.indexAt(position)
            if not index.isValid():
                return
    
            menu = QMenu(self)
            file_path = self.file_model.filePath(index)
    
            if os.path.isfile(file_path):
                menu.addAction("📄 Abrir", lambda: self.open_file(file_path))
                menu.addAction("📋 Copiar Caminho", lambda: self.copy_file_path(file_path))
                menu.addSeparator()
                menu.addAction("🗑️ Excluir", lambda: self.delete_file(file_path))
                menu.addAction("🔁 Renomear", lambda: self.rename_file(file_path))
            else:
                menu.addAction("📂 Abrir como Projeto", lambda: self.set_project(file_path))
                menu.addAction("📄 Novo Arquivo", lambda: self.create_new_file_in_explorer(file_path))
                menu.addAction("📁 Nova Pasta", lambda: self.create_new_folder_in_explorer(file_path))
                menu.addSeparator()
                menu.addAction("🗑️ Excluir", lambda: self.delete_folder(file_path))
                menu.addAction("🔁 Renomear", lambda: self.rename_folder(file_path))
    
            menu.exec(self.file_tree.viewport().mapToGlobal(position))
            
        except Exception as e:
            self.debug_log(f"❌ Erro no menu contexto: {e}", "ERROR")

    def create_new_file_in_explorer(self, parent_path=None):
        """Cria novo arquivo no explorador"""
        try:
            if not parent_path:
                current_index = self.file_tree.currentIndex()
                if current_index.isValid():
                    parent_path = self.file_model.filePath(current_index)
                    if not os.path.isdir(parent_path):
                        parent_path = os.path.dirname(parent_path)
                else:
                    parent_path = self.project_path or QDir.homePath()

            dialog = NewFileDialog(self)
            if dialog.exec():
                file_name = dialog.get_file_name()
                if file_name:
                    file_path = os.path.join(parent_path, file_name)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('# Novo arquivo\n')
                    
                    self.refresh_explorer()
                    self.open_file(file_path)
                    
                    self.debug_log(f"✅ Arquivo criado: {file_path}", "SUCCESS")
                    
        except Exception as e:
            self.debug_log(f"❌ Erro ao criar arquivo: {e}", "ERROR")
            QMessageBox.warning(self, "Erro", f"Não foi possível criar o arquivo:\n{str(e)}")

    def create_new_folder_in_explorer(self, parent_path=None):
        """Cria nova pasta no explorador"""
        try:
            if not parent_path:
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
                os.makedirs(new_folder_path, exist_ok=True)
                self.refresh_explorer()
                self.debug_log(f"✅ Pasta criada: {new_folder_path}", "SUCCESS")
                self.statusBar().showMessage(f"✅ Pasta criada: {folder_name}", 3000)
    
        except Exception as e:
            self.debug_log(f"❌ Erro ao criar pasta: {e}", "ERROR")
            QMessageBox.warning(self, "Erro", f"Não foi possível criar a pasta:\n{str(e)}")

    def copy_file_path(self, file_path):
        """Copia caminho do arquivo"""
        try:
            if file_path:
                clipboard = QGuiApplication.clipboard()
                clipboard.setText(file_path)
                self.debug_log(f"✅ Caminho copiado: {file_path}", "SUCCESS")
                self.statusBar().showMessage("✅ Caminho copiado para área de transferência", 2000)
        except Exception as e:
            self.debug_log(f"❌ Erro ao copiar caminho: {e}", "ERROR")

    def delete_file(self, file_path):
        """Exclui arquivo com confirmação"""
        try:
            reply = QMessageBox.question(
                self,
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir '{os.path.basename(file_path)}'?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                os.remove(file_path)
                self.refresh_explorer()
                self.debug_log(f"✅ Arquivo excluído: {file_path}", "SUCCESS")
                self.statusBar().showMessage(f"✅ Arquivo excluído: {os.path.basename(file_path)}", 3000)

        except Exception as e:
            self.debug_log(f"❌ Erro ao excluir arquivo: {e}", "ERROR")
            QMessageBox.warning(self, "Erro", f"Não foi possível excluir o arquivo:\n{str(e)}")

    def delete_folder(self, folder_path):
        """Exclui pasta com confirmação"""
        try:
            reply = QMessageBox.question(
                self,
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir a pasta '{os.path.basename(folder_path)}' e todo seu conteúdo?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                shutil.rmtree(folder_path)
                self.refresh_explorer()
                self.debug_log(f"✅ Pasta excluída: {folder_path}", "SUCCESS")
                self.statusBar().showMessage(f"✅ Pasta excluída: {os.path.basename(folder_path)}", 3000)

        except Exception as e:
            self.debug_log(f"❌ Erro ao excluir pasta: {e}", "ERROR")
            QMessageBox.warning(self, "Erro", f"Não foi possível excluir a pasta:\n{str(e)}")

    def rename_file(self, file_path):
        """Renomeia arquivo"""
        try:
            new_name, ok = QInputDialog.getText(
                self,
                "Renomear Arquivo",
                "Novo nome:",
                text=os.path.basename(file_path)
            )

            if ok and new_name:
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                os.rename(file_path, new_path)
                self.refresh_explorer()
                self.debug_log(f"✅ Arquivo renomeado: {file_path} -> {new_path}", "SUCCESS")
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao renomear arquivo: {e}", "ERROR")

    def rename_folder(self, folder_path):
        """Renomeia pasta"""
        try:
            new_name, ok = QInputDialog.getText(
                self,
                "Renomear Pasta",
                "Novo nome:",
                text=os.path.basename(folder_path)
            )

            if ok and new_name:
                new_path = os.path.join(os.path.dirname(folder_path), new_name)
                os.rename(folder_path, new_path)
                self.refresh_explorer()
                self.debug_log(f"✅ Pasta renomeada: {folder_path} -> {new_path}", "SUCCESS")
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao renomear pasta: {e}", "ERROR")

    # ===== SEÇÃO 12: MÉTODOS DE BUSCA E SUBSTITUIÇÃO =====
    
    def show_find_dialog(self):
        """Mostra diálogo de busca"""
        editor = self.get_current_editor()
        if not editor:
            QMessageBox.information(self, "Informação", "Nenhum editor ativo.")
            return

        find_text, ok = QInputDialog.getText(
            self,
            "Buscar",
            "Texto para buscar:",
            text=editor.textCursor().selectedText() or ""
        )

        if ok and find_text:
            self.find_in_editor(editor, find_text)

    def find_in_editor(self, editor, find_text, backward=False):
        """Busca texto no editor"""
        try:
            cursor = editor.textCursor()
            document = editor.document()
            
            options = QTextDocument.FindFlag(0)
            if backward:
                options = QTextDocument.FindBackward
            
            found_cursor = document.find(find_text, cursor, options)
            
            if found_cursor.isNull():
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

    def show_replace_dialog(self):
        """Mostra diálogo de substituir"""
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
        """Substitui texto no editor"""
        try:
            cursor = editor.textCursor()
            
            if cursor.hasSelection() and cursor.selectedText() == find_text:
                cursor.insertText(replace_text)
                self.find_in_editor(editor, find_text)
            else:
                if self.find_in_editor(editor, find_text):
                    cursor = editor.textCursor()
                    if cursor.selectedText() == find_text:
                        cursor.insertText(replace_text)
                        
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro na substituição: {str(e)}")

    # ===== SEÇÃO 13: MÉTODOS DE FOLDING =====
    
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
                    for i in range(left_tabs.count()):
                        if left_tabs.tabText(i) == "📊 Outline":
                            left_tabs.setCurrentIndex(i)
                            break
                break

    def focus_outline(self):
        """Foca no widget de Outline"""
        if hasattr(self, 'outline_widget'):
            for dock in self.findChildren(QDockWidget):
                if dock.windowTitle() == "Explorer":
                    left_tabs = dock.widget()
                    if isinstance(left_tabs, QTabWidget):
                        for i in range(left_tabs.count()):
                            if left_tabs.tabText(i) == "📊 Outline":
                                left_tabs.setCurrentIndex(i)
                                self.outline_widget.tree_widget.setFocus()
                                break
                    break

    # ===== SEÇÃO 14: MÉTODOS DE INDICADORES VISUAIS =====
    
    def update_indicators(self, index):
        """Atualiza indicadores quando a aba muda"""
        try:
            if index >= 0:
                widget = self.tab_widget.widget(index)
                if hasattr(widget, 'editor'):
                    self.apply_editor_indicators(widget.editor)
                    
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar indicadores: {e}", "ERROR")

    def apply_editor_indicators(self, editor):
        """Aplica indicadores visuais a um editor"""
        try:
            if not editor:
                return
                
            if self.current_line_highlight:
                editor.cursorPositionChanged.connect(
                    lambda: self.highlight_current_line(editor)
                )
                self.highlight_current_line(editor)
                
            if hasattr(editor, 'line_number_area'):
                editor.line_number_area.setVisible(self.show_line_numbers)
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao aplicar indicadores ao editor: {e}", "ERROR")

    def highlight_current_line(self, editor):
        """Destaca a linha atual do editor"""
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
            self.debug_log(f"❌ Erro ao destacar linha atual: {e}", "ERROR")

    def clear_indicators(self):
        """Limpa todos os indicadores visuais"""
        try:
            if hasattr(self, 'problems_list'):
                problem_count = self.problems_list.count()
                self.problems_list.clear()
                self.debug_log(f"🗑️ {problem_count} problemas limpos", "INFO")
                    
            editor_count = 0
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if hasattr(widget, 'editor'):
                    widget.editor.setExtraSelections([])
                    editor_count += 1
            
            self.clear_current_line_highlights()
            
            self.statusBar().showMessage(f"🗑️ {editor_count} editores limpos", 2000)
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao limpar indicadores: {e}", "ERROR")

    def clear_current_line_highlights(self):
        """Remove destaque da linha atual de todos os editores"""
        try:
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if hasattr(widget, 'editor'):
                    editor = widget.editor
                    current_selections = []
                    for selection in editor.extraSelections():
                        if not selection.format.property(QTextFormat.FullWidthSelection):
                            current_selections.append(selection)
                    editor.setExtraSelections(current_selections)
        except Exception as e:
            self.debug_log(f"❌ Erro ao limpar destaques de linha: {e}", "ERROR")

    def show_error_indicator(self, line_number, message):
        """Mostra indicador de erro em uma linha específica"""
        try:
            editor = self.get_current_editor()
            if not editor:
                return
                
            if hasattr(self, 'problems_list'):
                item_text = f"Linha {line_number}: {message}"
                item = QListWidgetItem(item_text)
                item.setForeground(QColor(255, 0, 0))
                self.problems_list.addItem(item)
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao mostrar indicador de erro: {e}", "ERROR")

    # ===== SEÇÃO 15: MÉTODOS DE PROJETO E VIRTUALENV =====
        
    def create_project(self):
        """Cria um novo projeto com estrutura completa E virtualenv automático - VERSÃO CORRIGIDA"""
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
    
        project_full_path = os.path.join(project_path, project_name)
    
        try:
            # ✅ CRIAR DIRETÓRIOS
            dirs = [
                project_full_path,
                os.path.join(project_full_path, "src"),
                os.path.join(project_full_path, "tests"),
                os.path.join(project_full_path, "docs"),
                os.path.join(project_full_path, "data")
            ]
    
            for dir_path in dirs:
                os.makedirs(dir_path, exist_ok=True)
    
            # ✅ CRIAR ARQUIVOS BÁSICOS
            main_file = os.path.join(project_full_path, "main.py")
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
    
            readme_file = os.path.join(project_full_path, "README.md")
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"# {project_name}\n\nProjeto criado com Py Dragon Studio IDE\n")
    
            requirements_file = os.path.join(project_full_path, "requirements.txt")
            with open(requirements_file, 'w', encoding='utf-8') as f:
                f.write("# Dependências do projeto\n")
    
            gitignore_file = os.path.join(project_full_path, ".gitignore")
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
    
            # ✅ DEFINIR PROJETO
            self.set_project(project_full_path)
            self.open_file(main_file)
    
            # ✅ PERGUNTAR SE QUER CRIAR VIRTUALENV
            reply = QMessageBox.question(
                self,
                "Virtualenv",
                f"Deseja criar um virtualenv para o projeto '{project_name}'?\n\n"
                f"Recomendado para isolar dependências do projeto.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Criar venv automaticamente - USANDO TERMINAL
                QTimer.singleShot(2000, self.create_venv_for_new_project)
            
            QMessageBox.information(
                self, "Sucesso", f"Projeto '{project_name}' criado com sucesso!")
    
        except Exception as e:
            QMessageBox.warning(
                self, "Erro", f"Não foi possível criar o projeto:\n{str(e)}")
             
    def auto_activate_venv(self, project_path):
        """Detecta e ativa virtualenv automaticamente - MELHORADO"""
        try:
            if not project_path or not os.path.exists(project_path):
                return False
                
            venv_candidates = [
                os.path.join(project_path, "venv"),
                os.path.join(project_path, ".venv"),
                os.path.join(project_path, "env"),
            ]
            
            for venv_path in venv_candidates:
                if os.path.exists(venv_path):
                    if self.is_valid_venv(venv_path):
                        self.venv_path = venv_path
                        self.debug_log(f"✅ Virtualenv detectado e ativado: {venv_path}", "SUCCESS")
                        
                        # ✅ ATIVAR NO TERMINAL
                        if hasattr(self, 'real_terminal') and self.real_terminal:
                            success = self.real_terminal.activate_venv(venv_path)
                            if success:
                                self.debug_log("✅ Venv ativado no terminal", "SUCCESS")
                        
                        venv_name = os.path.basename(venv_path)
                        self.statusBar().showMessage(f"🐍 Virtualenv ativado: {venv_name}", 5000)
                        return True
                    else:
                        self.debug_log(f"⚠️ Venv inválido encontrado: {venv_path}", "WARNING")
            
            self.debug_log("ℹ️ Nenhum virtualenv válido detectado", "INFO")
            self.venv_path = None
            return False
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao detectar virtualenv: {e}", "ERROR")
            return False

    def get_venv_error_details(self, venv_path, python_exec):
        """Obtém detalhes específicos do erro do venv"""
        try:
            details = []
            
            # Verificar se o venv foi criado
            if not os.path.exists(venv_path):
                details.append("❌ O diretório do virtualenv não foi criado")
                return "\n".join(details)
            
            details.append(f"📁 Virtualenv criado em: {venv_path}")
            
            # Verificar estrutura básica
            if os.name == 'nt':
                python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
                bin_dir = "Scripts"
            else:
                python_exe = os.path.join(venv_path, "bin", "python")
                pip_exe = os.path.join(venv_path, "bin", "pip")
                bin_dir = "bin"
            
            # Verificar se o Python existe
            if not os.path.exists(python_exe):
                details.append(f"❌ Arquivo Python não encontrado: {python_exe}")
            else:
                details.append(f"✅ Arquivo Python encontrado: {python_exe}")
                
                # Verificar permissões do Python
                if not os.access(python_exe, os.X_OK):
                    details.append(f"❌ Sem permissão de execução no Python")
                else:
                    details.append(f"✅ Permissão de execução OK")
                
                # Testar execução do Python
                try:
                    result = subprocess.run(
                        [python_exe, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=os.path.dirname(venv_path)
                    )
                    if result.returncode == 0:
                        details.append(f"✅ Python executável: {result.stdout.strip()}")
                    else:
                        details.append(f"❌ Python não executável: {result.stderr}")
                except subprocess.TimeoutExpired:
                    details.append(f"❌ Timeout ao executar Python")
                except Exception as e:
                    details.append(f"❌ Erro ao executar Python: {e}")
            
            # Verificar diretório bin
            bin_path = os.path.join(venv_path, bin_dir)
            if not os.path.exists(bin_path):
                details.append(f"❌ Diretório {bin_dir} não encontrado")
            else:
                details.append(f"✅ Diretório {bin_dir} encontrado")
                
                # Listar conteúdo do bin
                try:
                    bin_contents = os.listdir(bin_path)
                    details.append(f"📁 Conteúdo de {bin_dir}: {len(bin_contents)} arquivos")
                    
                    # Mostrar arquivos importantes
                    important_files = ['python', 'pip', 'activate']
                    for important_file in important_files:
                        if any(important_file in item for item in bin_contents):
                            details.append(f"   ✅ {important_file} encontrado")
                        else:
                            details.append(f"   ❌ {important_file} NÃO encontrado")
                            
                except Exception as e:
                    details.append(f"❌ Erro ao listar {bin_dir}: {e}")
            
            # Verificar outros diretórios importantes
            important_dirs = ['lib', 'Lib', 'include', 'Include']
            for dir_name in important_dirs:
                dir_path = os.path.join(venv_path, dir_name)
                if os.path.exists(dir_path):
                    details.append(f"✅ Diretório {dir_name} encontrado")
                else:
                    details.append(f"❌ Diretório {dir_name} NÃO encontrado")
            
            # Verificar permissões gerais
            try:
                # Verificar se podemos escrever no venv
                test_file = os.path.join(venv_path, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                details.append("✅ Permissão de escrita OK")
            except Exception as e:
                details.append(f"❌ Sem permissão de escrita: {e}")
            
            # Verificar espaço em disco
            try:
                stat = os.statvfs(os.path.dirname(venv_path))
                free_space_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
                details.append(f"💾 Espaço livre: {free_space_mb:.1f} MB")
                
                if free_space_mb < 10:
                    details.append("⚠️  Pouco espaço em disco (< 10 MB)")
            except:
                details.append("💾 Espaço livre: Não foi possível verificar")
            
            return "\n".join(details)
            
        except Exception as e:
            return f"❌ Erro ao obter detalhes: {e}"
    def update_venv_indicator(self):
        """Atualiza indicador visual do venv na interface"""
        try:
            if self.venv_path and self.is_valid_venv(self.venv_path):
                venv_name = os.path.basename(self.venv_path)
                python_exe = self.get_python_executable()
                
                # ✅ ATUALIZAR STATUSBAR
                try:
                    result = subprocess.run(
                        [python_exe, "--version"],
                        capture_output=True, text=True, timeout=5
                    )
                    python_version = result.stdout.strip() if result.returncode == 0 else "Desconhecido"
                except:
                    python_version = "Desconhecido"
                
                self.statusBar().showMessage(
                    f"🐍 Virtualenv ativo: {venv_name} | {python_version}", 
                    10000  # Mostrar por 10 segundos
                )
                
                # ✅ ATUALIZAR LABEL DO PROJETO
                if hasattr(self, 'project_info_label'):
                    self.project_info_label.setText(
                        f"📁 {os.path.basename(self.project_path)} 🐍{venv_name}"
                    )
            else:
                # ✅ SEM VENV
                if hasattr(self, 'project_info_label') and self.project_path:
                    self.project_info_label.setText(f"📁 {os.path.basename(self.project_path)}")
                    
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar indicador do venv: {e}", "ERROR")
    def create_venv_for_new_project(self):
        """Cria venv automaticamente para novo projeto - USANDO TERMINAL"""
        try:
            if not self.project_path:
                self.debug_log("❌ Nenhum projeto aberto para criar venv", "ERROR")
                return
                
            self.debug_log("🔄 Criando venv automático para novo projeto via terminal...", "INFO")
            
            venv_name = "venv"
            venv_path = os.path.join(self.project_path, venv_name)
            
            # Verificar se já existe
            if os.path.exists(venv_path):
                self.debug_log(f"✅ Venv já existe: {venv_path}", "INFO")
                return self.activate_venv_in_project(venv_path)
            
            # 🎯 USAR TERMINAL REAL
            if hasattr(self, 'real_terminal') and self.real_terminal:
                # Garantir que estamos no diretório do projeto
                self.real_terminal.change_directory(self.project_path)
                
                # Comando específico que sabemos que funciona
                venv_command = "python3.9 -m venv venv\n"
                
                # Enviar comando
                self.real_terminal.send_command(f"echo '🔨 Criando virtualenv para novo projeto...'\n")
                self.real_terminal.send_command(venv_command)
                self.real_terminal.send_command(f"echo '✅ Virtualenv criado! Ativando...'\n")
                
                # Pequena pausa para criação
                QTimer.singleShot(3000, lambda: self.activate_venv_after_creation(venv_path))
                
                self.debug_log("✅ Comando de criação de venv enviado ao terminal", "SUCCESS")
                return True
            else:
                self.debug_log("❌ Terminal não disponível para criar venv", "ERROR")
                return False
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao criar venv para novo projeto: {e}", "ERROR")
            return False

    def activate_venv_after_creation(self, venv_path):
        """Ativa o venv após criação (com delay)"""
        try:
            if os.path.exists(venv_path) and self.is_valid_venv(venv_path):
                success = self.activate_venv_in_project(venv_path)
                if success:
                    self.debug_log("✅ Venv ativado automaticamente após criação", "SUCCESS")
                else:
                    self.debug_log("⚠️ Venv criado mas não foi possível ativar", "WARNING")
            else:
                self.debug_log("❌ Venv não foi criado corretamente", "ERROR")
        except Exception as e:
            self.debug_log(f"❌ Erro ao ativar venv após criação: {e}", "ERROR")
    def _get_valid_python_for_venv(self):
        """Obtém um Python válido para criar virtualenv - VERSÃO CORRIGIDA"""
        try:
            python_candidates = []
            
            # 1. Tentar Python persistido (com fallback)
            try:
                if hasattr(self, 'settings_manager') and self.settings_manager:
                    python_exec = self.settings_manager.get_python_for_vm_creation()
                    if python_exec and os.path.exists(python_exec) and self._check_venv_module(python_exec):
                        return python_exec
            except Exception as e:
                self.debug_log(f"⚠️ Erro no Python persistido: {e}", "WARNING")
            
            # 2. Python do sistema
            python_candidates.append(sys.executable)
            
            # 3. Procurar Python no PATH
            python_names = ['python3', 'python', 'python3.11', 'python3.10', 'python3.9', 'python3.8']
            for python_name in python_names:
                try:
                    if os.name == 'nt':
                        result = subprocess.run(
                            ['where', python_name], 
                            capture_output=True, 
                            text=True,
                            timeout=5
                        )
                    else:
                        result = subprocess.run(
                            ['which', python_name], 
                            capture_output=True, 
                            text=True,
                            timeout=5
                        )
                    
                    if result.returncode == 0:
                        python_path = result.stdout.strip().split('\n')[0]
                        if python_path and os.path.exists(python_path):
                            python_candidates.append(python_path)
                except:
                    continue
            
            # Testar cada candidato
            for python_exec in python_candidates:
                if python_exec and os.path.exists(python_exec) and self._check_venv_module(python_exec):
                    self.debug_log(f"✅ Python válido encontrado: {python_exec}", "SUCCESS")
                    return python_exec
            
            self.debug_log("❌ Nenhum Python válido encontrado", "ERROR")
            return None
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao obter Python válido: {e}", "ERROR")
            return None
    
    def _check_venv_module(self, python_exec):
        """Verifica se o Python tem módulo venv"""
        try:
            result = subprocess.run(
                [python_exec, '-m', 'venv', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    # ADICIONAR ESTE MÉTODO À CLASSE IDE
    def is_valid_venv(self, venv_path):
        """Verifica se é um virtualenv válido - VERSÃO CORRIGIDA"""
        try:
            if not venv_path or not os.path.exists(venv_path):
                return False
                
            # Verificar arquivos essenciais
            if os.name == 'nt':
                python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
            else:
                python_exe = os.path.join(venv_path, "bin", "python")
                activate_script = os.path.join(venv_path, "bin", "activate")
            
            # Verificar se arquivos essenciais existem
            essential_files = [python_exe, activate_script]
            files_exist = all(os.path.exists(f) for f in essential_files)
            
            if not files_exist:
                self.debug_log(f"❌ Arquivos essenciais faltando em {venv_path}", "ERROR")
                missing_files = [f for f in essential_files if not os.path.exists(f)]
                self.debug_log(f"❌ Arquivos faltando: {missing_files}", "ERROR")
                return False
                
            # Testar se o Python funciona
            try:
                result = subprocess.run(
                    [python_exe, "--version"],
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    cwd=os.path.dirname(venv_path)
                )
                
                if result.returncode == 0:
                    self.debug_log(f"✅ Venv Python válido: {result.stdout.strip()}", "SUCCESS")
                    return True
                else:
                    self.debug_log(f"❌ Venv Python inválido: {result.stderr}", "ERROR")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.debug_log(f"❌ Timeout ao testar venv Python", "ERROR")
                return False
            except Exception as e:
                self.debug_log(f"❌ Erro ao testar venv Python: {e}", "ERROR")
                return False
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao validar venv {venv_path}: {e}", "ERROR")
            return False

    def _is_valid_venv_path(self, venv_path):
        """Verifica se o caminho para venv é válido"""
        try:
            # Verificar se o diretório pai existe e é gravável
            parent_dir = os.path.dirname(venv_path)
            if not os.path.exists(parent_dir):
                return False
            
            if not os.access(parent_dir, os.W_OK):
                return False
            
            # Verificar se o caminho não contém caracteres problemáticos
            problematic_chars = [' ', '&', ';', '|', '$', '`']
            for char in problematic_chars:
                if char in venv_path:
                    return False
            
            return True
            
        except Exception as e:
            self.debug_log(f"❌ Caminho de venv inválido: {e}", "ERROR")
            return False

    def diagnose_venv_creation(self, venv_path, python_exec):
        """Diagnósticos detalhados de problemas na criação do venv"""
        try:
            self.debug_log("\n🔍 DIAGNÓSTICO DE VENV", "INFO")
            
            # 1. Verificar permissões
            parent_dir = os.path.dirname(venv_path)
            self.debug_log(f"📁 Diretório pai: {parent_dir}", "INFO")
            self.debug_log(f"🔑 Permissão de escrita: {os.access(parent_dir, os.W_OK)}", "INFO")
            
            # 2. Verificar espaço em disco
            try:
                stat = os.statvfs(parent_dir)
                free_space = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)  # MB
                self.debug_log(f"💾 Espaço livre: {free_space:.1f} MB", "INFO")
            except:
                self.debug_log("💾 Espaço livre: Não foi possível verificar", "WARNING")
            
            # 3. Verificar Python usado
            self.debug_log(f"🐍 Python usado: {python_exec}", "INFO")
            
            # 4. Verificar se Python existe e é executável
            if os.path.exists(python_exec):
                self.debug_log(f"✅ Python encontrado: {python_exec}", "SUCCESS")
                if os.access(python_exec, os.X_OK):
                    self.debug_log("✅ Python é executável", "SUCCESS")
                else:
                    self.debug_log("❌ Python NÃO é executável", "ERROR")
            else:
                self.debug_log(f"❌ Python NÃO encontrado: {python_exec}", "ERROR")
            
            # 5. Verificar se venv foi criado
            if os.path.exists(venv_path):
                self.debug_log(f"📁 Venv criado em: {venv_path}", "SUCCESS")
                
                # Listar conteúdo
                try:
                    contents = []
                    for root, dirs, files in os.walk(venv_path):
                        for file in files[:10]:  # Primeiros 10 arquivos
                            contents.append(os.path.relpath(os.path.join(root, file), venv_path))
                    
                    self.debug_log(f"📄 Conteúdo do venv ({len(contents)} arquivos):", "INFO")
                    for item in contents[:5]:
                        self.debug_log(f"   - {item}", "INFO")
                    if len(contents) > 5:
                        self.debug_log(f"   ... e mais {len(contents) - 5} arquivos", "INFO")
                        
                except Exception as e:
                    self.debug_log(f"❌ Erro ao listar conteúdo: {e}", "ERROR")
            else:
                self.debug_log(f"❌ Venv NÃO criado em: {venv_path}", "ERROR")
            
            # 6. Verificar estrutura do venv
            if os.path.exists(venv_path):
                expected_dirs = []
                if os.name == 'nt':
                    expected_dirs = ["Scripts", "Lib", "Include"]
                else:
                    expected_dirs = ["bin", "lib", "include"]
                
                for dir_name in expected_dirs:
                    dir_path = os.path.join(venv_path, dir_name)
                    exists = os.path.exists(dir_path)
                    status = "✅" if exists else "❌"
                    self.debug_log(f"{status} {dir_name}: {exists}", "INFO")
                    
        except Exception as e:
                self.debug_log(f"❌ Erro no diagnóstico: {e}", "ERROR")
    

    def create_venv(self):
            """Método antigo - substituído por create_venv_with_persisted_python"""
            return self.create_venv_with_persisted_python()

    # ADICIONAR ESTE MÉTODO À CLASSE IDE
    def activate_venv(self, venv_path):
        """Ativa um venv - método de compatibilidade"""
        return self.activate_venv_in_project(venv_path)

    def activate_venv_in_project(self, venv_path):
        """Ativa o venv no projeto E no terminal REAL - VERSÃO MELHORADA"""
        try:
            # ✅ VALIDAÇÃO ROBUSTA DO VENV
            if not self.is_valid_venv(venv_path):
                self.debug_log(f"❌ Venv inválido: {venv_path}", "ERROR")
                return False
                
            # ✅ DEFINIR VENV NO IDE
            self.venv_path = venv_path
            self.debug_log(f"✅ Venv definido no IDE: {venv_path}", "SUCCESS")
            
            # ✅ ATIVAÇÃO NO TERMINAL REAL
            terminal_success = False
            if hasattr(self, 'real_terminal') and self.real_terminal:
                try:
                    terminal_success = self.real_terminal.activate_venv(venv_path)
                    if terminal_success:
                        self.debug_log("✅ Venv ativado no terminal REAL", "SUCCESS")
                    else:
                        self.debug_log("⚠️ Falha ao ativar venv no terminal REAL", "WARNING")
                except Exception as e:
                    self.debug_log(f"❌ Erro ao ativar venv no terminal REAL: {e}", "ERROR")
            
            # ✅ ATUALIZAR INTERFACE
            self.update_venv_indicator()
            
            # ✅ MENSAGEM DE STATUS
            venv_name = os.path.basename(venv_path)
            status_msg = f"🐍 Virtualenv ativado: {venv_name}"
            if not terminal_success:
                status_msg += " (terminal: manual)"
            
            self.statusBar().showMessage(status_msg, 5000)
            
            return True
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao ativar venv no projeto: {e}", "ERROR")
            return False
    def check_real_terminal_status(self):
        """Verifica o status do terminal REAL"""
        try:
            if hasattr(self, 'real_terminal') and self.real_terminal:
                if hasattr(self.real_terminal, 'shell_process'):
                    state = self.real_terminal.shell_process.state()
                    states = {
                        QProcess.NotRunning: "❌ Parado",
                        QProcess.Starting: "🔄 Iniciando", 
                        QProcess.Running: "✅ Rodando"
                    }
                    status = states.get(state, "❓ Desconhecido")
                    
                    venv_status = "Com Venv" if self.real_terminal.venv_active else "Sem Venv"
                    
                    self.debug_log(f"Terminal REAL: {status} | {venv_status}", "INFO")
                    return True
            return False
        except Exception as e:
            self.debug_log(f"❌ Erro ao verificar terminal: {e}", "ERROR")
            return False
    def diagnose_venv_issues(self):
        """Diagnósticos detalhados dos problemas de venv"""
        self.debug_log("\n🔍 DIAGNÓSTICO DE VENV", "INFO")
        
        # Verificar Python do sistema
        self.debug_log(f"🐍 Python do sistema: {sys.executable}", "INFO")
        
        # Verificar módulo venv
        try:
            result = subprocess.run(
                [sys.executable, "-m", "venv", "--help"],
                capture_output=True, text=True, timeout=10
            )
            venv_available = result.returncode == 0
            self.debug_log(f"📦 Módulo venv disponível: {venv_available}", "INFO" if venv_available else "ERROR")
        except Exception as e:
            self.debug_log(f"❌ Erro ao verificar módulo venv: {e}", "ERROR")
        
        # Verificar projeto atual
        self.debug_log(f"📁 Projeto atual: {self.project_path}", "INFO")
        
        # Verificar venv atual
        if hasattr(self, 'venv_path') and self.venv_path:
            self.debug_log(f"🐍 Venv atual: {self.venv_path}", "INFO")
            self.debug_log(f"✅ Venv válido: {self.is_valid_venv(self.venv_path)}", "INFO")
        
        # Verificar terminal
        if hasattr(self, 'real_terminal') and self.real_terminal:
            self.debug_log("💻 Terminal: Disponível", "SUCCESS")
        else:
            self.debug_log("❌ Terminal: Não disponível", "ERROR")
    def activate_project(self):
        """Ativa o projeto no terminal"""
        try:
            if hasattr(self, 'real_terminal') and self.real_terminal:
                if self.project_path and os.path.exists(self.project_path):
                    self.real_terminal.change_directory(self.project_path)
                    
                    if self.venv_path and self.is_valid_venv(self.venv_path):
                        self.real_terminal.activate_venv(self.venv_path)
                    
                self.debug_log(f"✅ Projeto ativado: {self.project_path}", "SUCCESS")
                
            self.update_venv_display()
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao ativar projeto: {e}", "ERROR")

    def update_venv_display(self):
        """Atualiza a exibição do venv na interface"""
        try:
            if self.venv_path and self.is_valid_venv(self.venv_path):
                venv_name = os.path.basename(self.venv_path)
                python_exe = self.get_python_executable()
                
                self.statusBar().showMessage(
                    f"🐍 Virtualenv ativo: {venv_name} | Python: {python_exe}", 
                    5000
                )
            else:
                self.statusBar().showMessage(
                    f"🐍 Python: {self.get_python_executable()} (sem virtualenv)", 
                    5000
                )
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar display do venv: {e}", "ERROR")

    def auto_activate_venv(self, project_path):
        """Detecta e ativa virtualenv automaticamente"""
        try:
            venv_candidates = [
                os.path.join(project_path, "venv"),
                os.path.join(project_path, ".venv"),
                os.path.join(project_path, "env"),
            ]
            
            for venv_path in venv_candidates:
                if os.path.exists(venv_path):
                    if self.is_valid_venv(venv_path):
                        self.venv_path = venv_path
                        self.debug_log(f"✅ Virtualenv detectado e ativado: {venv_path}", "SUCCESS")
                        
                        self.update_terminal_with_venv()
                        
                        venv_name = os.path.basename(venv_path)
                        self.statusBar().showMessage(f"🐍 Virtualenv ativado: {venv_name}", 5000)
                        return True
            
            self.debug_log("ℹ️ Nenhum virtualenv detectado", "INFO")
            self.venv_path = None
            return False
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao detectar virtualenv: {e}", "ERROR")
            return False

    def update_terminal_with_venv(self):
        """Atualiza o terminal para usar o virtualenv"""
        try:
            if hasattr(self, 'real_terminal') and self.real_terminal and self.venv_path:
                if os.name == 'nt':
                    activate_cmd = f'call "{os.path.join(self.venv_path, "Scripts", "activate.bat")}"\r\n'
                else:
                    activate_cmd = f'source "{os.path.join(self.venv_path, "bin", "activate")}"\n'
                
                self.real_terminal.shell_process.write(activate_cmd.encode('utf-8'))
                self.debug_log("✅ Comando de ativação do venv enviado ao terminal", "SUCCESS")
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar terminal com venv: {e}", "ERROR")

    # ===== SEÇÃO 16: MÉTODOS DE PYTHON E PACOTES =====
    
    def get_python_executable(self):
        """Obtém o executável Python"""
        if self.venv_path and os.path.exists(self.venv_path):
            if os.name == 'nt':
                return os.path.join(self.venv_path, "Scripts", "python.exe")
            else:
                return os.path.join(self.venv_path, "bin", "python")
        return sys.executable

    def detect_system_python(self):
        """Detecta e salva Python do sistema automaticamente"""
        try:
            python_path = self.settings_manager.detect_and_save_system_python()
            version_info = self.settings_manager.get_python_version_info(python_path)
            
            QMessageBox.information(
                self,
                "Python Detectado",
                f"✅ Python do sistema detectado e salvo:\n\n"
                f"{version_info}\n"
                f"📍 {python_path}\n\n"
                f"Este Python será usado para criar virtual environments."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"❌ Não foi possível detectar Python do sistema:\n{str(e)}"
            )

    def select_python_for_vms(self):
        """Seleciona Python específico para criar virtual environments"""
        try:
            available_pythons = self.settings_manager.get_system_specific_python_paths()
            
            if not available_pythons:
                QMessageBox.information(self, "Python", "Nenhum Python encontrado no sistema")
                return
            
            python_list = []
            for python_path in available_pythons:
                version_info = self.settings_manager.get_python_version_info(python_path)
                python_list.append(f"{version_info} - {python_path}")
            
            python_choice, ok = QInputDialog.getItem(
                self,
                "Selecionar Python para VMs",
                "Escolha o Python para criar virtual environments:",
                python_list,
                0,
                False
            )
            
            if ok and python_choice:
                selected_python = python_choice.split(" - ")[-1]
                
                self.settings_manager.set_last_vm_python(selected_python)
                self.settings_manager.set_selected_python(selected_python)
                
                QMessageBox.information(
                    self,
                    "Python Definido",
                    f"✅ Python definido para virtual environments:\n\n{python_choice}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao selecionar Python:\n{str(e)}")

    def show_python_status(self):
        """Mostra status completo do Python"""
        try:
            current_python = self.get_python_executable()
            current_version = self.settings_manager.get_python_version_info(current_python)
            
            vm_python = self.settings_manager.get_last_vm_python()
            vm_version = self.settings_manager.get_python_version_info(vm_python) if vm_python else "Não definido"
            
            selected_python = self.settings_manager.get_selected_python()
            selected_version = self.settings_manager.get_python_version_info(selected_python) if selected_python else "Não definido"
            
            python_versions = self.settings_manager.get_python_versions()
            
            message = f"""🐍 STATUS DO PYTHON - SISTEMA
    
    📌 EM USO ATUAL:
      {current_version}
      📍 {current_python}
    
    🎯 PARA VIRTUAL ENVIRONMENTS:
      {vm_version}
      📍 {vm_python or 'Usará Python do sistema'}
    
      💾 SELECIONADO:
      {selected_version}
      📍 {selected_python or 'Não definido'}
    
      📚 HISTÓRICO ({len(python_versions)} versões):
      """
            for i, version in enumerate(python_versions[:5], 1):
                ver_info = self.settings_manager.get_python_version_info(version)
                message += f"  {i}. {ver_info}\n     {version}\n"
    
            QMessageBox.information(self, "Status do Python - Sistema", message)
            
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao obter status do Python:\n{str(e)}")

    def show_python_manager_dialog(self):
        """Mostra gerenciador de Python com persistência"""
        try:
            from tools.python_manager import PythonVersionManager
            manager = PythonVersionManager()
            dialog = PythonVersionDialog(self, manager)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir o gerenciador:\n{str(e)}")

    def open_package_manager(self):
        """Abre o gerenciador de pacotes Python"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True, text=True, timeout=10
            )
        
            if result.returncode != 0:
                QMessageBox.warning(
                    self, 
                    "Pip não disponível", 
                    "O pip não está disponível neste ambiente Python.\n\n"
                    "Certifique-se de que o Python está instalado corretamente."
                )
                return
            
            dialog = PackageManagerDialog(self)
            dialog.exec()
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Erro", 
                f"Não foi possível abrir o gerenciador de pacotes:\n{str(e)}"
            )

    def install_dependencies(self):
        """Instala dependências do projeto"""
        if not self.project_path:
            return

        requirements_file = os.path.join(self.project_path, "requirements.txt")
        if not os.path.exists(requirements_file):
            try:
                with open(requirements_file, 'w', encoding='utf-8') as f:
                    f.write("# Adicione suas dependências aqui\n")
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
                    cmd = [python_exec, "-m", "pip", "install", package]
                else:
                    cmd = [python_exec, "-m", "pip", "install", "-r", "requirements.txt"]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                self.output_tabs.setCurrentWidget(self.output_text)
                self.output_text.clear()

                if package:
                    self.output_text.appendPlainText(f"📦 Instalando {package}...\n")
                else:
                    self.output_text.appendPlainText("📦 Instalando dependências do requirements.txt...\n")

                self.output_text.appendPlainText("-" * 50 + "\n")

                if result.stdout:
                    self.output_text.appendPlainText(result.stdout)
                if result.stderr:
                    self.output_text.appendPlainText(result.stderr)

                if result.returncode == 0:
                    self.output_text.appendPlainText("\n✅ Instalação concluída com sucesso!")
                else:
                    self.output_text.appendPlainText(f"\n❌ Falha na instalação (código: {result.returncode})")

            except Exception as e:
                self.output_text.appendPlainText(f"💥 Erro: {str(e)}")

    # ===== SEÇÃO 17: MÉTODOS DE PLUGINS =====
    
    def integrate_plugin_actions(self):
        """Integra ações dos plugins na interface"""
        try:
            if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
                self.debug_log("❌ Plugin manager não disponível", "ERROR")
                return
            
            all_plugin_actions = self.plugin_manager.get_all_plugin_actions()
            
            if not all_plugin_actions:
                self.debug_log("ℹ️ Nenhuma ação de plugin encontrada", "INFO")
                return
            
            self.debug_log(f"🔍 Procurando menu Ferramentas...", "INFO")
            
            tools_menu = None
            menu_bar = self.menuBar()
            
            for i, action in enumerate(menu_bar.actions()):
                menu_text = action.text().replace('&', '')
                self.debug_log(f"  Menu {i}: '{menu_text}'", "DEBUG")
                
                if any(name in menu_text for name in ["Ferramentas", "Tools", "🛠️"]):
                    tools_menu = action.menu()
                    self.debug_log(f"✅ Menu encontrado: '{menu_text}'", "SUCCESS")
                    break
            
            if not tools_menu:
                self.debug_log("❌ Menu Ferramentas não encontrado. Criando...", "WARNING")
                tools_menu = self.menuBar().addMenu("🛠️ Ferramentas")
            
            actions_to_remove = []
            for action in tools_menu.actions():
                action_text = action.text()
                if action_text in ["--- Plugins ---", "--- Plugins ---"] or action.isSeparator():
                    actions_to_remove.append(action)
            
            for action in actions_to_remove:
                tools_menu.removeAction(action)
            
            if tools_menu.actions():
                tools_menu.addSeparator()
            
            header_action = self.create_action("--- Plugins ---", lambda: None)
            header_action.setEnabled(False)
            tools_menu.addAction(header_action)
            
            for action in all_plugin_actions:
                tools_menu.addAction(action)
                self.debug_log(f"✅ Ação integrada: {action.text()}", "DEBUG")
            
            self.debug_log(f"✅ {len(all_plugin_actions)} ações de plugins integradas no menu Ferramentas", "SUCCESS")
            
            tools_menu.update()
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao integrar ações dos plugins: {e}", "ERROR")
            import traceback
            traceback.print_exc()

    def create_action(self, text, callback, shortcut=None, tooltip=None):
        """Cria ações de menu"""
        try:
            from PySide6.QtGui import QAction, QKeySequence
            action = QAction(text, self)
            action.triggered.connect(callback)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            if tooltip:
                action.setToolTip(tooltip)
            return action
        except Exception as e:
            self.debug_log(f"❌ Erro ao criar ação: {e}", "ERROR")
            return None

    def show_plugin_manager_dialog(self):
        """Mostra informações básicas dos plugins"""
        if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
            QMessageBox.information(self, "Plugins", "Sistema de plugins não disponível")
            return
        
        try:
            plugins_info = self.plugin_manager.get_plugins_info()
        
            self.output_tabs.setCurrentWidget(self.output_text)
            self.output_text.clear()
            self.output_text.appendPlainText("🔌 GERENCIADOR DE PLUGINS")
            self.output_text.appendPlainText("=" * 50)
        
            if not plugins_info:
                self.output_text.appendPlainText("\nℹ️ Nenhum plugin carregado")
            else:
                for info in plugins_info:
                    status_icon = "✅" if hasattr(info, 'status') and info.status.name == "LOADED" else "❌"
                    name = getattr(info, 'name', 'Desconhecido')
                    version = getattr(info, 'version', '1.0.0')
                    
                    self.output_text.appendPlainText(f"\n{status_icon} {name} v{version}")
            
            self.output_text.appendPlainText(f"\n📦 Total: {len(plugins_info)} plugins")
        
            self.statusBar().showMessage("Informações dos plugins carregadas", 3000)
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao mostrar plugins: {e}", "ERROR")

    def refresh_plugins(self):
        """Atualiza plugins de forma segura"""
        try:
            if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
                return
            
            loaded_count = self.plugin_manager.auto_load_plugins()
            
            if loaded_count > 0:
                self.debug_log(f"{loaded_count} plugins recarregados", "SUCCESS")
            else:
                self.debug_log("Nenhum plugin encontrado", "INFO")
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao atualizar plugins: {e}", "ERROR")

    def install_new_plugin(self):
        """Instala um novo plugin"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Instalar Plugin",
            "",
            "Arquivos Python (*.py);;Todos os arquivos (*)"
        )
        
        if file_path:
            try:
                plugins_dir = Path(__file__).parent.parent / "plugins"
                plugin_name = Path(file_path).name
                dest_path = plugins_dir / plugin_name
                
                shutil.copy2(file_path, dest_path)
                self.refresh_plugins()
            
                QMessageBox.information(self, "Sucesso", f"Plugin {plugin_name} instalado com sucesso!")
            
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao instalar plugin: {str(e)}")

    def test_plugins_system(self):
        """Testa o sistema de plugins"""
        try:
            if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
                print("❌ Plugin manager não disponível")
                return
        
            plugins_info = self.plugin_manager.get_plugins_info()
            print(f"📦 Plugins carregados: {len(plugins_info)}")
            
            for info in plugins_info:
                print(f"  - {info.name}: {info.status.value}")
                
            actions = self.plugin_manager.get_all_plugin_actions()
            print(f"🛠️ Ações disponíveis: {len(actions)}")
            
            for action in actions:
                print(f"  - {action.text()}")
                
        except Exception as e:
            print(f"❌ Erro no teste de plugins: {e}")

    # ===== SEÇÃO 18: MÉTODOS DE TEMAS =====
    
    def open_theme_manager(self):
        """Abre o gerenciador de temas"""
        try:
            if not hasattr(self, 'theme_manager') or self.theme_manager is None:
                QMessageBox.warning(self, "Aviso", 
                                  "Gerenciador de temas não está disponível.\n\n"
                                  "Recarregue o aplicativo ou verifique os logs.")
                return
                
            dialog = ThemeDialog(self.theme_manager, self)
            dialog.exec()
        except Exception as e:
            self.debug_log(f"❌ Erro ao abrir gerenciador de temas: {e}", "ERROR")
            QMessageBox.warning(self, "Erro", 
                              f"Não foi possível abrir o gerenciador de temas:\n{str(e)}")

    def apply_theme(self, theme_name):
        """Aplica um tema ao IDE"""
        theme = self.theme_manager.get_theme(theme_name)
        colors = theme["colors"]

        self.apply_theme_to_ui(theme)
        self.apply_syntax_theme(theme)

        self.debug_log(f"✅ Tema '{theme_name}' aplicado", "SUCCESS")

    def apply_theme_to_ui(self, theme):
        """Aplica o tema à interface do usuário"""
        colors = theme["colors"]

        palette = QPalette()

        if theme["type"] == "dark":
            palette.setColor(QPalette.Window, QColor(colors["background"]))
            palette.setColor(QPalette.WindowText, QColor(colors["foreground"]))
            palette.setColor(QPalette.Base, QColor(colors["background"]))
            palette.setColor(QPalette.AlternateBase, QColor(colors["selection"]))
            palette.setColor(QPalette.ToolTipBase, QColor(colors["background"]))
            palette.setColor(QPalette.ToolTipText, QColor(colors["foreground"]))
            palette.setColor(QPalette.Text, QColor(colors["foreground"]))
            palette.setColor(QPalette.Button, QColor(colors["background"]))
            palette.setColor(QPalette.ButtonText, QColor(colors["foreground"]))
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(colors["info"]))
            palette.setColor(QPalette.Highlight, QColor(colors["selection"]))
            palette.setColor(QPalette.HighlightedText, QColor(colors["foreground"]))
        else:
            palette.setColor(QPalette.Window, QColor(colors["background"]))
            palette.setColor(QPalette.WindowText, QColor(colors["foreground"]))
            palette.setColor(QPalette.Base, Qt.white)
            palette.setColor(QPalette.AlternateBase, QColor(colors["selection"]))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.black)
            palette.setColor(QPalette.Text, Qt.black)
            palette.setColor(QPalette.Button, QColor(colors["background"]))
            palette.setColor(QPalette.ButtonText, Qt.black)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(colors["info"]))
            palette.setColor(QPalette.Highlight, QColor(colors["selection"]))
            palette.setColor(QPalette.HighlightedText, Qt.white)

        QApplication.setPalette(palette)

    def apply_syntax_theme(self, theme):
        """Aplica o tema de syntax highlighting a todos os editores"""
        if hasattr(self, 'syntax_highlighting_manager'):
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

    # ===== SEÇÃO 19: MÉTODOS DE AJUDA E INFORMAÇÃO =====
    
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
                        f"<p>Desenvolvido com PySide6</p>")

    # ===== SEÇÃO 20: MÉTODOS DE UTILITÁRIOS =====
    
    def get_terminal_state(self):
        """Retorna o estado atual do terminal"""
        try:
            for dock in self.findChildren(QDockWidget):
                if dock.windowTitle() == "Output":
                    return {
                        'visible': dock.isVisible(),
                        'available': True,
                        'tab_count': self.output_tabs.count() if hasattr(self, 'output_tabs') else 0
                    }
            return {'visible': False, 'available': False, 'tab_count': 0}
        except Exception as e:
            self.debug_log(f"❌ Erro ao verificar estado do terminal: {e}", "ERROR")
            return {'visible': False, 'available': False, 'tab_count': 0}

    def show_terminal(self):
        """Força o terminal a ficar visível"""
        try:
            for dock in self.findChildren(QDockWidget):
                if dock.windowTitle() == "Output":
                    dock.show()
                    dock.raise_()
                    break
        
            if hasattr(self, 'output_tabs'):
                for i in range(self.output_tabs.count()):
                    if self.output_tabs.tabText(i) == "💻 Terminal":
                        self.output_tabs.setCurrentIndex(i)
                        self.debug_log("✅ Terminal focado", "SUCCESS")
                        return True
            
            self.debug_log("❌ Não foi possível encontrar a aba do terminal", "ERROR")
            return False
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao mostrar terminal: {e}", "ERROR")
            return False

    def check_terminal_visibility(self):
        """Verifica se o terminal está visível e acessível"""
        try:
            if hasattr(self, 'output_tabs') and self.output_tabs:
                for i in range(self.output_tabs.count()):
                    if self.output_tabs.tabText(i) == "💻 Terminal":
                        self.debug_log("✅ Terminal encontrado no output_tabs", "SUCCESS")
                        return True
                
                self.debug_log("❌ Terminal NÃO encontrado no output_tabs", "ERROR")
                return False
            else:
                self.debug_log("❌ output_tabs não disponível", "ERROR")
                return False
        except Exception as e:
            self.debug_log(f"❌ Erro ao verificar terminal: {e}", "ERROR")
            return False

    def test_terminal(self):
        """Testa o terminal integrado"""
        try:
            if hasattr(self, 'terminal_emulator') and self.terminal_emulator:
                terminal = self.terminal_emulator
                if terminal.process and terminal.process.state() == QProcess.Running:
                    self.debug_log("✅ Terminal está funcionando", "SUCCESS")
                    return True
                else:
                    self.debug_log("❌ Terminal não está rodando", "ERROR")
                    return False
            else:
                self.debug_log("❌ Terminal não disponível", "ERROR")
                return False
        except Exception as e:
            self.debug_log(f"❌ Erro ao testar terminal: {e}", "ERROR")
            return False

    def test_syntax_highlighting(self):
        """Testa o syntax highlighting em todos os editores abertos"""
        self.debug_log(f"\n🧪 TESTE DE SYNTAX HIGHLIGHTING", "INFO")
        
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'editor'):
                self.debug_log(f"\n--- Aba {i}: {self.tab_widget.tabText(i)} ---", "INFO")
                widget.editor.debug_syntax_info()

    def check_python_version(self):
        """Verifica e exibe a versão do Python"""
        try:
            result = subprocess.run([self.get_python_executable(), "--version"],
                                    capture_output=True, text=True)
            version = result.stdout.strip()
            self.statusBar().showMessage(f"🐍 {version}", 5000)
        except:
            self.statusBar().showMessage("❌ Não foi possível detectar Python", 5000)

    def test_venv_creation(self):
        """Testa a criação de virtualenv"""
        if not self.project_path:
            QMessageBox.information(self, "Teste", "Abra um projeto primeiro")
            return
            
        test_path = os.path.join(self.project_path, "test_venv")
        
        result = subprocess.run(
            [sys.executable, "-m", "venv", test_path],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            if self.is_valid_venv(test_path):
                QMessageBox.information(self, "Teste", "✅ Venv funciona corretamente!")
                shutil.rmtree(test_path)
            else:
                QMessageBox.warning(self, "Teste", "❌ Venv criado mas inválido")
        else:
            QMessageBox.warning(self, "Teste", f"❌ Falha na criação:\n{result.stderr}")

    # ===== SEÇÃO 21: MÉTODOS DE AUTOMATIZAÇÃO =====
    
    def trigger_unified_autocomplete(self):
        """Dispara autocomplete usando o sistema unificado"""
        try:
            editor = self.get_current_editor()
            if not editor or not hasattr(self, 'autocomplete_widget'):
                return
                
            cursor = editor.textCursor()
            current_text = editor.toPlainText()
            cursor_position = cursor.position()
            
            suggestions = self.autocomplete_widget.get_suggestions(
                current_text, cursor_position, 
                getattr(editor, 'file_path', ''), 
                self.project_path or ""
            )
            
            if suggestions:
                cursor_rect = editor.cursorRect()
                self.autocomplete_widget.show_completions(editor, suggestions, cursor_rect.bottomLeft())
                
        except Exception as e:
            self.debug_log(f"❌ Erro no autocomplete unificado: {e}", "ERROR")
    
    def trigger_manual_autocomplete(self):
        """Dispara autocomplete manualmente"""
        self.trigger_unified_autocomplete()

    def schedule_autocomplete(self):
        """Agenda autocomplete quando o texto muda"""
        if hasattr(self, 'autocomplete_timer'):
            self.autocomplete_timer.start(300)

    def connect_editor_autocomplete(self, index):
        """Conecta autocomplete ao editor atual"""
        if index >= 0:
            widget = self.tab_widget.widget(index)
            if hasattr(widget, 'editor'):
                editor = widget.editor
                editor.textChanged.connect(self.schedule_autocomplete)

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

    def check_indentation_errors(self):
        """Verifica erros de indentação no arquivo atual"""
        editor = self.get_current_editor()
        if not editor or not hasattr(editor, 'file_path') or not editor.file_path.endswith('.py'):
            return

        code = editor.toPlainText()
        errors = self.indentation_checker.check_code(code, editor.file_path)

        if errors:
            self.show_indentation_errors(errors)
        else:
            self.statusBar().showMessage("✅ Nenhum erro de indentação encontrado", 3000)

    def show_indentation_errors(self, errors):
        """Mostra erros de indentação na lista de problemas"""
        for i in range(self.problems_list.count() - 1, -1, -1):
            item = self.problems_list.item(i)
            data = item.data(Qt.UserRole)
            if data and data.get('type') == 'indentation':
                self.problems_list.takeItem(i)

        for error in errors:
            item_text = f"Linha {error['line']}: {error['message']} - {error['suggestion']}"
            item = QListWidgetItem(item_text)
            item.setForeground(QColor(255, 0, 0))

            data = {
                'file': getattr(self.get_current_editor(), 'file_path', ''),
                'line': error['line'],
                'type': 'indentation',
                'message': error['message']
            }
            item.setData(Qt.UserRole, data)

            self.problems_list.addItem(item)

        self.statusBar().showMessage(f"❌ Encontrados {len(errors)} erro(s) de indentação", 5000)

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
                QTimer.singleShot(2000, self.run_linter)

            self.check_indentation_errors()

    def run_linter(self):
        """Executa o linter no arquivo atual"""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, EditorTab) and current_widget.file_path and current_widget.file_path.endswith('.py'):
            current_widget.start_linting()
        else:
            QMessageBox.information(self, "Informação", "Apenas arquivos Python podem ser analisados.")

    def clear_problems(self):
        """Limpa a lista de problemas"""
        if hasattr(self, 'problems_list'):
            self.problems_list.clear()
            self.debug_log("🗑️ Lista de problemas limpa", "SUCCESS")

    # ===== SEÇÃO 22: MÉTODOS DE LSP =====
    
    def _on_tab_changed_lsp(self, index):
        """Manipula mudança de aba para LSP"""
        try:
            if (index >= 0 and hasattr(self, 'lsp_manager') and 
                self.lsp_manager is not None):
                widget = self.tab_widget.widget(index)
                if hasattr(widget, 'editor') and hasattr(widget, 'file_path') and widget.file_path:
                    content = widget.editor.toPlainText()
                    self.lsp_manager.open_document(widget.file_path, content)
        except Exception as e:
            self.debug_log(f"❌ Erro em _on_tab_changed_lsp: {e}", "ERROR")

    # ===== SEÇÃO 23: MÉTODOS DE EXECUÇÃO AVANÇADA =====
    
    def pause_execution(self):
        """Pausa a execução atual"""
        try:
            if hasattr(self, 'current_process') and self.current_process:
                if self.current_process.state() == QProcess.Running:
                    self.current_process.kill()
                    self.output_text.appendPlainText("⏸️ Execução pausada")
                else:
                    self.output_text.appendPlainText("ℹ️ Nenhum processo em execução")
            else:
                self.output_text.appendPlainText("ℹ️ Nenhum processo para pausar")

        except Exception as e:
            self.output_text.appendPlainText(f"❌ Erro ao pausar execução: {str(e)}")

    def stop_execution(self):
        """Para completamente a execução"""
        try:
            processes = [
                getattr(self, 'current_process', None),
                getattr(self, 'shell_process', None),
                getattr(self, 'debug_process', None)
            ]

            stopped = False
            for proc in processes:
                if proc and proc.state() == QProcess.Running:
                    proc.terminate()
                    if not proc.waitForFinished(1000):
                        proc.kill()
                    stopped = True

            if stopped:
                self.output_text.appendPlainText("⏹️ Todas as execuções paradas")
            else:
                self.output_text.appendPlainText("ℹ️ Nenhuma execução em andamento")

        except Exception as e:
            self.output_text.appendPlainText(f"❌ Erro ao parar execução: {str(e)}")

    def stop_process(self, process):
        """Para um processo de forma segura"""
        if process and process.state() == QProcess.Running:
            process.terminate()
            if not process.waitForFinished(1000):
                process.kill()
                process.waitForFinished(1000)

    # ===== SEÇÃO 24: MÉTODOS DE LAYOUT =====
    
    def split_view(self):
        """Divide a visualização em horizontal/vertical"""
        try:
            if isinstance(self.centralWidget(), QSplitter):
                splitter = self.centralWidget()
                widgets = []
                for i in range(splitter.count()):
                    widgets.append(splitter.widget(i))
                
                splitter.deleteLater()
                
                if widgets:
                    self.setCentralWidget(widgets[0])
                    
                self.statusBar().showMessage("🔲 Layout único restaurado", 2000)
            else:
                splitter = QSplitter(Qt.Horizontal)
                
                right_tab_widget = QTabWidget()
                right_tab_widget.setTabsClosable(True)
                right_tab_widget.setMovable(True)
                right_tab_widget.setDocumentMode(True)
                
                right_tab_widget.setStyleSheet("""
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
                
                current_index = self.tab_widget.currentIndex()
                if current_index >= 0:
                    widget = self.tab_widget.widget(current_index)
                    tab_text = self.tab_widget.tabText(current_index)
                    self.tab_widget.removeTab(current_index)
                    right_tab_widget.addTab(widget, tab_text)
                
                splitter.addWidget(self.tab_widget)
                splitter.addWidget(right_tab_widget)
                
                splitter.setSizes([600, 400])
                self.setCentralWidget(splitter)
                
                self.statusBar().showMessage("📊 Layout dividido ativado", 2000)
                
        except Exception as e:
            self.debug_log(f"❌ Erro no split view: {e}", "ERROR")

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
                for dock in self.findChildren(QDockWidget):
                    if dock.windowTitle() == "Explorer":
                        left_tabs = dock.widget()
                        if isinstance(left_tabs, QTabWidget):
                            left_tabs.setCurrentIndex(1)
                        break
            elif command == "Minimap":
                self.toggle_minimap()

    def navigate_to_line(self, line_number):
        """Navega para uma linha específica no editor atual"""
        editor = self.get_current_editor()
        if not editor:
            return
            
        line_num = max(0, line_number - 1)
        
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        for _ in range(line_num):
            cursor.movePosition(QTextCursor.Down)
            
        editor.setTextCursor(cursor)
        editor.setFocus()
        editor.centerCursor()

    # ===== SEÇÃO 25: MÉTODOS DE PROJETO AVANÇADO =====
    
    def configure_project(self):
        """Configura o projeto"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        QMessageBox.information(self, "Configurar Projeto",
                                f"Configurações do projeto: {os.path.basename(self.project_path)}\n\n"
                                "Esta funcionalidade está em desenvolvimento.")

    def package_project(self):
        """Empacota o projeto"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        main_files = [
            os.path.join(self.project_path, "main.py"),
            os.path.join(self.project_path, "app.py"),
            os.path.join(self.project_path, "src", "main.py"),
        ]

        main_file = None
        for file in main_files:
            if os.path.exists(file):
                main_file = os.path.basename(file)
                break

        if not main_file:
            main_file, ok = QInputDialog.getText(
                self,
                "Empacotar Projeto",
                "Arquivo principal:",
                text="main.py"
            )
            if not ok or not main_file:
                return

        dialog = PackageDialog(self, self.project_path, main_file)
        dialog.exec()

    def deploy_project(self):
        """Implementa deploy automático do projeto"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        try:
            dialog = DeployDialog(self, self.project_path)
            if dialog.exec():
                deploy_config = dialog.get_deploy_config()

                self.output_tabs.setCurrentWidget(self.output_text)
                self.output_text.clear()
                self.output_text.appendPlainText("🚀 Iniciando deploy...\n")
                self.output_text.appendPlainText("=" * 50 + "\n")

                if deploy_config['type'] == 'zip':
                    self.deploy_as_zip(deploy_config)
                elif deploy_config['type'] == 'git':
                    self.deploy_via_git(deploy_config)
                elif deploy_config['type'] == 'ftp':
                    self.deploy_via_ftp(deploy_config)
                else:
                    self.output_text.appendPlainText("❌ Tipo de deploy não suportado")

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha no deploy: {str(e)}")

    def deploy_via_ftp(self, config):
        """Deploy via FTP"""
        self.output_text.appendPlainText("⚠️ Deploy FTP em desenvolvimento...")

    def deploy_via_git(self, config):
        """Deploy via Git"""
        try:
            if not os.path.exists(os.path.join(self.project_path, '.git')):
                self.output_text.appendPlainText("❌ Não é um repositório Git")
                return

            commands = [
                ["git", "add", "."],
                ["git", "commit", "-m", config.get('commit_message', 'Deploy automático')],
                ["git", "push", config.get('remote', 'origin'), config.get('branch', 'main')]
            ]

            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                self.output_text.appendPlainText(f"Comando: {' '.join(cmd)}")

                if result.stdout:
                    self.output_text.appendPlainText(result.stdout)
                if result.stderr:
                    self.output_text.appendPlainText(result.stderr)

                if result.returncode != 0:
                    self.output_text.appendPlainText(f"❌ Falha no comando: {' '.join(cmd)}")
                    return

            self.output_text.appendPlainText("✅ Deploy via Git concluído!")

        except Exception as e:
            self.output_text.appendPlainText(f"❌ Erro no deploy Git: {str(e)}")

    def deploy_as_zip(self, config):
        """Cria arquivo ZIP do projeto"""
        try:
            zip_path = os.path.join(
                config['output_dir'], f"{os.path.basename(self.project_path)}.zip")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.project_path):
                    if '__pycache__' in dirs:
                        dirs.remove('__pycache__')
                    if '.git' in dirs:
                        dirs.remove('.git')

                    for file in files:
                        if not file.endswith(('.pyc', '.tmp')):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.project_path)
                            zipf.write(file_path, arcname)

            self.output_text.appendPlainText(f"✅ Projeto compactado: {zip_path}")
            self.output_text.appendPlainText(f"📦 Tamanho: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")

        except Exception as e:
            self.output_text.appendPlainText(f"❌ Erro ao criar ZIP: {str(e)}")

    def open_advanced_find_similar(self):
        """Abre o localizador de textos similares aprimorado"""
        try:
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
            self.debug_log(f"❌ Erro ao abrir localizador de textos similares: {e}", "ERROR")
            QMessageBox.warning(self, "Erro", 
                            f"Não foi possível abrir o localizador de textos similares:\n{str(e)}")

    def open_find_similar(self):
        """Abre a busca de textos similares"""
        current_editor = self.get_current_editor()
        if current_editor:
            dialog = FindSimilarDialog(current_editor, self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum editor ativo!")

    def open_find_files(self):
        """Abre a busca de arquivos por nome"""
        if hasattr(self, 'project_path') and self.project_path:
            dialog = FindFilesDialog(self.project_path, self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum projeto aberto!")

    def format_code(self):
        """Formata o código atual"""
        editor = self.get_current_editor()
        if not editor or not hasattr(editor, 'file_path') or not editor.file_path.endswith('.py'):
            QMessageBox.information(self, "Informação", "Apenas arquivos Python podem ser formatados.")
            return

        try:
            python_exec = self.get_python_executable()
            result = subprocess.run(
                [python_exec, "-m", "autopep8", "-", "--aggressive"],
                input=editor.toPlainText().encode('utf-8'),
                capture_output=True,
                text=False
            )

            if result.returncode == 0:
                formatted_code = result.stdout.decode('utf-8')
                editor.setPlainText(formatted_code)
                self.statusBar().showMessage("✅ Código formatado com sucesso!", 3000)
            else:
                QMessageBox.warning(
                    self, "Erro", "Falha ao formatar código. Instale autopep8: pip install autopep8")

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao formatar código: {str(e)}")

    def manage_packages(self):
        """Gerencia pacotes Python"""
        QMessageBox.information(self, "Gerenciar Pacotes",
                                "Esta funcionalidade está em desenvolvimento.\n\n"
                                "Use o terminal para gerenciar pacotes:\n"
                                "• pip install <pacote>\n"
                                "• pip uninstall <pacote>\n"
                                "• pip list")

    def show_settings(self):
        """Mostra configurações"""
        QMessageBox.information(self, "Configurações",
                                "Painel de configurações em desenvolvimento.\n\n"
                                "Configurações atuais:\n"
                                f"• Python: {self.get_python_executable()}\n"
                                f"• Projeto: {self.project_path or 'Nenhum'}\n"
                                f"• Virtualenv: {self.venv_path or 'Nenhum'}")

    # ===== SEÇÃO 26: MÉTODOS DE TESTES =====
    
    def run_tests(self):
        """Executa testes do projeto"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        try:
            self.output_tabs.setCurrentWidget(self.output_text)
            self.output_text.clear()
            self.output_text.appendPlainText("🧪 Executando testes...\n")
            self.output_text.appendPlainText("=" * 50 + "\n")

            python_exec = self.get_python_executable()

            test_commands = [
                [python_exec, "-m", "pytest", "-v"],
                [python_exec, "-m", "unittest", "discover", "-v"],
                [python_exec, "-m", "doctest", "**/*.py"]
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

                    self.output_text.appendPlainText(f"Comando: {' '.join(cmd)}\n")

                    if result.stdout:
                        self.output_text.appendPlainText(result.stdout)
                    if result.stderr and "Error" in result.stderr:
                        self.output_text.appendPlainText(f"Erros:\n{result.stderr}")

                    if result.returncode == 0:
                        self.output_text.appendPlainText(f"\n✅ Testes executados com sucesso usando {cmd[2]}!")
                        success = True
                        break
                    else:
                        self.output_text.appendPlainText(f"\n❌ {cmd[2]} falhou, tentando próximo...\n")
                        self.output_text.appendPlainText("-" * 30 + "\n")

                except subprocess.TimeoutExpired:
                    self.output_text.appendPlainText(f"⏰ Timeout no comando: {' '.join(cmd)}\n")
                except Exception as e:
                    self.output_text.appendPlainText(f"⚠️ Erro com {cmd[2]}: {str(e)}\n")

            if not success:
                self.output_text.appendPlainText(
                    "\n❌ Não foi possível executar testes com nenhum framework conhecido.")
                self.output_text.appendPlainText(
                    "Frameworks suportados: pytest, unittest, doctest")

        except Exception as e:
            self.output_text.appendPlainText(f"💥 Erro inesperado: {str(e)}")

    def run_coverage(self):
        """Executa análise de cobertura de código"""
        if not self.project_path:
            QMessageBox.information(self, "Informação", "Nenhum projeto aberto.")
            return

        try:
            python_exec = self.get_python_executable()

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
                    self.install_package("coverage")
                else:
                    return

            self.output_tabs.setCurrentWidget(self.output_text)
            self.output_text.clear()
            self.output_text.appendPlainText("📊 Executando análise de cobertura...\n")
            self.output_text.appendPlainText("=" * 50 + "\n")

            result = subprocess.run(
                [python_exec, "-m", "coverage", "run", "-m", "pytest"],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=60
            )

            if result.stdout:
                self.output_text.appendPlainText("Saída dos testes:\n")
                self.output_text.appendPlainText(result.stdout)

            if result.stderr:
                self.output_text.appendPlainText("Erros:\n")
                self.output_text.appendPlainText(result.stderr)

            if result.returncode in [0, 1]:
                report_result = subprocess.run(
                    [python_exec, "-m", "coverage", "report"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                self.output_text.appendPlainText("\n" + "=" * 50 + "\n")
                self.output_text.appendPlainText("RELATÓRIO DE COBERTURA:\n")
                self.output_text.appendPlainText("=" * 50 + "\n")

                if report_result.stdout:
                    self.output_text.appendPlainText(report_result.stdout)

                html_result = subprocess.run(
                    [python_exec, "-m", "coverage", "html"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                if html_result.returncode == 0:
                    html_path = os.path.join(self.project_path, 'htmlcov', 'index.html')
                    self.output_text.appendPlainText(f"\n📁 Relatório HTML: {html_path}")

                    open_report_btn = QPushButton("Abrir Relatório HTML")
                    open_report_btn.clicked.connect(lambda: self.open_html_report(html_path))

                    self.output_text.appendPlainText("\n[Clique aqui para abrir o relatório HTML]")

                xml_result = subprocess.run(
                    [python_exec, "-m", "coverage", "xml"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )

                if xml_result.returncode == 0:
                    self.output_text.appendPlainText("📊 Relatório XML gerado: coverage.xml")

            else:
                self.output_text.appendPlainText("❌ Falha na execução da cobertura")

        except subprocess.TimeoutExpired:
            self.output_text.appendPlainText("⏰ Timeout na análise de cobertura")
        except Exception as e:
            self.output_text.appendPlainText(f"💥 Erro na cobertura: {str(e)}")

    def install_package(self, package_name):
        """Instala um pacote Python"""
        try:
            python_exec = self.get_python_executable()

            self.output_tabs.setCurrentWidget(self.output_text)
            self.output_text.appendPlainText(f"📦 Instalando {package_name}...\n")

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

    def open_html_report(self, html_path):
        """Abre relatório HTML no navegador padrão"""
        try:
            import webbrowser
            webbrowser.open(f"file://{html_path}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o relatório: {str(e)}")

    # ===== SEÇÃO 27: MÉTODOS DE EXCEÇÃO E FINALIZAÇÃO =====
    
    def exception_hook(self, exctype, value, tb):
        """Captura exceções globais de forma segura"""
        try:
            error_msg = f"ERRO GLOBAL: {exctype.__name__}: {value}"
            self.debug_log(error_msg, "ERROR")
            
            import traceback
            traceback.print_exception(exctype, value, tb)
            
            sys.__excepthook__(exctype, value, tb)
            
        except Exception as e:
            print(f"❌ ERRO CRÍTICO no exception_hook: {e}")
            sys.__excepthook__(exctype, value, tb)

    def closeEvent(self, event):
        """Lida com o fechamento da aplicação de forma segura"""
        self.debug_log("🔄 Finalizando aplicação...", "INFO")
        
        # Finalizar LSP
        if hasattr(self, 'lsp_manager') and self.lsp_manager is not None:
            self.debug_log("🔄 Finalizando LSP...", "INFO")
            try:
                self.lsp_manager.shutdown()
            except Exception as e:
                self.debug_log(f"❌ Erro ao finalizar LSP: {e}", "ERROR")
        else:
            self.debug_log("ℹ️ LSP manager não inicializado", "INFO")
    
        # Parar terminal REAL
        if hasattr(self, 'real_terminal') and self.real_terminal:
            self.debug_log("🔄 Fechando terminal REAL...", "INFO")
            try:
                self.real_terminal.close_terminal()
            except Exception as e:
                self.debug_log(f"❌ Erro ao fechar terminal REAL: {e}", "ERROR")
    
        # Parar shell process
        if hasattr(self, 'shell_process') and self.shell_process:
            self.debug_log("🔄 Parando shell process...", "INFO")
            try:
                if self.shell_process.state() == QProcess.Running:
                    self.shell_process.terminate()
                    if not self.shell_process.waitForFinished(1000):
                        self.shell_process.kill()
                        self.shell_process.waitForFinished(1000)
            except Exception as e:
                self.debug_log(f"❌ Erro ao parar shell: {e}", "ERROR")
    
        # Parar processos de execução
        processes = [
            getattr(self, 'current_process', None),
            getattr(self, 'debug_process', None)
        ]
        
        for proc in processes:
            if proc and proc.state() == QProcess.Running:
                self.debug_log("🔄 Parando processo de execução...", "INFO")
                try:
                    self.stop_process(proc)
                except Exception as e:
                    self.debug_log(f"❌ Erro ao parar processo: {e}", "ERROR")
    
        # Parar workers
        workers = [
            ('auto_complete_worker', 'autocomplete'),
            ('linter_worker', 'linting'), 
            ('debug_worker', 'debug')
        ]
        
        for worker_attr, worker_name in workers:
            if hasattr(self, worker_attr) and getattr(self, worker_attr):
                self.debug_log(f"🔄 Parando worker de {worker_name}...", "INFO")
                try:
                    getattr(self, worker_attr).stop()
                except Exception as e:
                    self.debug_log(f"❌ Erro ao parar worker {worker_name}: {e}", "ERROR")
    
        # Finalizar plugins
        if hasattr(self, 'plugin_manager'):
            self.debug_log("🔄 Finalizando plugins...", "INFO")
            try:
                self.plugin_manager.shutdown_plugins()
            except Exception as e:
                self.debug_log(f"❌ Erro ao finalizar plugins: {e}", "ERROR")
    
        # Salvar configurações
        try:
            if hasattr(self, 'settings_manager'):
                self.settings_manager.save_settings()
                self.debug_log("💾 Configurações salvas", "SUCCESS")
        except Exception as e:
            self.debug_log(f"❌ Erro ao salvar configurações: {e}", "ERROR")
    
        # Fechar todas as abas
        try:
            while self.tab_widget.count() > 0:
                widget = self.tab_widget.widget(0)
                if hasattr(widget, 'editor') and widget.editor.document().isModified():
                    # Tentar salvar arquivos modificados
                    try:
                        self.tab_widget.setCurrentIndex(0)
                        if hasattr(widget, 'file_path') and widget.file_path:
                            self.save_file()
                    except:
                        pass
                self.tab_widget.removeTab(0)
        except Exception as e:
            self.debug_log(f"❌ Erro ao fechar abas: {e}", "ERROR")
    
        event.accept()
        self.debug_log("👋 Aplicação finalizada com sucesso", "SUCCESS")
    def update_minimap_theme(self):
        """Atualiza o tema do minimap"""
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
    
    def parse_command_line_args(self):
        """Processa argumentos de linha de comando"""
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
            QTimer.singleShot(1000, lambda: self.set_project(project))

    def set_project_with_python_mapping(self, project_path=None):
        """Define o projeto atual com mapeamento de Python"""
        try:
            if not project_path:
                project_path = QFileDialog.getExistingDirectory(
                    self, "Selecionar Projeto", self.project_path or QDir.homePath()
                )
    
            if project_path and os.path.exists(project_path):
                self.project_path = project_path
                self.project_info_label.setText(f"📁 {os.path.basename(project_path)}")
                
                self.auto_activate_venv(project_path)
                self.refresh_explorer()
                
                if hasattr(self, 'real_terminal') and self.real_terminal:
                    self.real_terminal.change_directory(project_path)
                
                python_path = self.settings_manager.get_project_python(project_path)
                if python_path and os.path.exists(python_path):
                    self.python_path = python_path
                    self.debug_log(f"✅ Python do projeto carregado: {python_path}", "SUCCESS")
                
                self.debug_log(f"✅ Projeto definido: {project_path}", "SUCCESS")
                return True
                
            return False
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao definir projeto: {e}", "ERROR")
            return False

    def _filter_ansi_codes(self, text):
        """Remove códigos de escape ANSI"""
        import re
        ansi_escape = re.compile(r'''
            \x1B  # ESC
            (?:   # 7-bit C1 Fe (except CSI)
                [@-Z\\-_]
            |     # ou
                \[  # CSI
                [0-?]*  # Parameter bytes
                [ -/]*  # Intermediate bytes
                [@-~]   # Final byte
            )
        ''', re.VERBOSE)
        
        cleaned = ansi_escape.sub('', text)
        
        control_chars = re.compile(r'[\x00-\x1f\x7f-\x9f]')
        cleaned = control_chars.sub('', cleaned)
        
        return cleaned

    def append_output(self, text):
        """Adiciona saída ao terminal com tratamento robusto de erros"""
        try:
            if not text:
                return
                
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            cleaned_text = self._filter_ansi_codes(str(text))
            
            if cursor.position() < self.input_start:
                cursor.movePosition(QTextCursor.End)
            
            cursor.insertText(cleaned_text)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            
        except Exception as e:
            print(f"Erro ao adicionar output: {e}")
            try:
                self.moveCursor(QTextCursor.End)
                self.insertPlainText(str(text))
            except:
                pass
            
    
    def shutdown_plugins(self):
        """Desliga todos os plugins de forma segura"""
        try:
            self.debug_log("🔄 Desligando plugins...", "INFO")
            
            for plugin_name, plugin_info in self.plugins.items():
                try:
                    plugin_instance = plugin_info['instance']
                    if hasattr(plugin_instance, 'shutdown'):
                        plugin_instance.shutdown()
                        self.debug_log(f"✅ Plugin {plugin_name} desligado", "SUCCESS")
                except Exception as e:
                    self.debug_log(f"❌ Erro ao desligar plugin {plugin_name}: {e}", "ERROR")
            
            self.debug_log("✅ Todos os plugins desligados", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"❌ Erro crítico ao desligar plugins: {e}", "ERROR")


    
    
    def cleanup_temp_scripts(self, script_path):
        """Limpa scripts temporários após uso"""
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
                self.debug_log(f"🗑️ Script temporário removido: {script_path}", "SUCCESS")
            
            # Também limpar variações do script
            base_name = os.path.splitext(script_path)[0]
            for ext in ['.bat', '.sh', '.cmd']:
                temp_script = base_name + ext
                if os.path.exists(temp_script):
                    os.remove(temp_script)
                    
        except Exception as e:
            self.debug_log(f"⚠️ Não foi possível limpar script temporário: {e}", "WARNING")
    
    def create_venv_simple_fallback(self):
        """Método de fallback simples para criar virtualenv"""
        try:
            if not self.project_path:
                return False
                
            venv_name = "venv"
            venv_path = os.path.join(self.project_path, venv_name)
            
            # Tentar método mais direto possível
            python_candidates = []
            
            # 1. Python do sistema
            python_candidates.append(sys.executable)
            
            # 2. Python no PATH
            for python_cmd in ['python3', 'python']:
                try:
                    result = subprocess.run(
                        [python_cmd, '--version'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        python_candidates.append(python_cmd)
                except:
                    continue
            
            # Tentar cada candidato
            for python_exec in python_candidates:
                try:
                    self.debug_log(f"🧪 Tentando criar venv com: {python_exec}", "INFO")
                    
                    result = subprocess.run(
                        [python_exec, '-m', 'venv', venv_path],
                        capture_output=True, text=True, timeout=60,
                        cwd=self.project_path
                    )
                    
                    if result.returncode == 0:
                        self.debug_log(f"✅ Venv criado com: {python_exec}", "SUCCESS")
                        
                        if self.is_valid_venv(venv_path):
                            self.activate_venv_in_project(venv_path)
                            QMessageBox.information(
                                self, "Sucesso", 
                                f"✅ Virtualenv criado com sucesso!\n\n"
                                f"Usando: {python_exec}\n"
                                f"Local: {venv_path}"
                            )
                            return True
                    
                except Exception as e:
                    self.debug_log(f"❌ Falha com {python_exec}: {e}", "ERROR")
                    continue
            
            # Se nenhum funcionou
            QMessageBox.critical(
                self, "Erro",
                "❌ Não foi possível criar virtualenv com nenhum Python disponível.\n\n"
                "Soluções:\n"
                "• Instale Python 3.6+ no sistema\n"  
                "• No Ubuntu: sudo apt-get install python3-venv\n"
                "• No Windows: Baixe do python.org\n"
                "• No Mac: brew install python3"
            )
            return False
            
        except Exception as e:
            self.debug_log(f"❌ Erro no fallback: {e}", "ERROR")
            return False

    
   
    
        
        
    def create_venv_dynamic(self):
        """Cria virtualenv com detecção dinâmica de Python - MÉTODO UNIFICADO"""
        try:
            if not self.project_path:
                QMessageBox.information(self, "Virtualenv", "Abra um projeto primeiro!")
                return False
    
            venv_name, ok = QInputDialog.getText(
                self,
                "Criar Virtualenv", 
                "Nome do virtualenv:",
                text="venv"
            )
    
            if not ok or not venv_name:
                return False
    
            venv_path = os.path.join(self.project_path, venv_name)
            
            # Verificar se já existe
            if os.path.exists(venv_path):
                reply = QMessageBox.question(
                    self,
                    "Virtualenv já existe",
                    f"O virtualenv '{venv_name}' já existe.\n\nDeseja sobrescrever?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        shutil.rmtree(venv_path)
                        import time
                        time.sleep(1)
                    except Exception as e:
                        QMessageBox.critical(self, "Erro", f"Erro ao remover: {str(e)}")
                        return False
                else:
                    # Tentar usar o existente
                    if self.is_valid_venv(venv_path):
                        return self.activate_venv_in_project(venv_path)
                    return False
    
            # 🎯 DETECÇÃO DINÂMICA DE PYTHON
            python_exec = self._detect_best_python_for_venv()
            
            if not python_exec:
                QMessageBox.critical(
                    self,
                    "Python não encontrado",
                    "❌ Não foi possível encontrar um Python válido para criar o virtualenv.\n\n"
                    "Verifique se:\n"
                    "• Python 3.6+ está instalado\n"
                    "• O módulo 'venv' está disponível\n"
                    "• O Python está no PATH do sistema"
                )
                return False
    
            self.debug_log(f"🔄 Criando virtualenv com Python: {python_exec}", "INFO")
            
            # ✅ VERIFICAR MÓDULO VENV
            if not self._check_venv_module(python_exec):
                QMessageBox.critical(
                    self,
                    "Módulo venv não disponível",
                    f"❌ O Python selecionado não tem o módulo 'venv':\n{python_exec}\n\n"
                    f"Para corrigir:\n"
                    f"• No Ubuntu/Debian: sudo apt-get install python3-venv\n"
                    f"• No Windows: Instale o Python pelo site oficial\n"
                    f"• No Mac: brew install python3"
                )
                return False
    
            # ✅ MOSTRAR PROGRESSO
            progress = QProgressDialog(
                f"Criando virtualenv com:\n{python_exec}", 
                "Cancelar", 0, 0, self
            )
            progress.setWindowTitle("Criando Virtual Environment")
            progress.setModal(True)
            progress.show()
            QApplication.processEvents()
    
            # ✅ CRIAR VIRTUALENV
            try:
                self.debug_log(f"🔨 Executando: {python_exec} -m venv {venv_path}", "INFO")
                
                result = subprocess.run(
                    [python_exec, "-m", "venv", venv_path],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path,
                    timeout=120
                )
    
                progress.close()
    
                if result.returncode == 0:
                    # ✅ VERIFICAR SE FOI CRIADO COM SUCESSO
                    if self.is_valid_venv(venv_path):
                        self.venv_path = venv_path
                        self.debug_log(f"✅ Virtualenv criado e validado: {venv_path}", "SUCCESS")
                        
                        # ✅ ATIVAR AUTOMATICAMENTE
                        success = self.activate_venv_in_project(venv_path)
                        
                        if success:
                            version_info = self.settings_manager.get_python_version_info(python_exec)
                            QMessageBox.information(
                                self, 
                                "Sucesso", 
                                f"✅ Virtualenv criado com sucesso!\n\n"
                                f"🐍 Python: {version_info}\n"
                                f"📁 Local: {venv_path}\n"
                                f"⚡ Status: Ativado automaticamente"
                            )
                            return True
                        else:
                            QMessageBox.warning(
                                self,
                                "Aviso",
                                f"Virtualenv criado mas não foi possível ativar:\n{venv_path}\n\n"
                                f"Você pode ativá-lo manualmente no terminal."
                            )
                            return True
                    else:
                        error_details = self.get_venv_error_details(venv_path, python_exec)
                        QMessageBox.critical(
                            self,
                            "Virtualenv inválido",
                            f"❌ O virtualenv foi criado mas é inválido:\n{venv_path}\n\n"
                            f"Detalhes do problema:\n{error_details}"
                        )
                        return False
                else:
                    error_msg = result.stderr if result.stderr else "Erro desconhecido"
                    self.debug_log(f"❌ Erro ao criar venv: {error_msg}", "ERROR")
                    
                    # ✅ TENTAR MÉTODO ALTERNATIVO VIA TERMINAL
                    reply = QMessageBox.question(
                        self,
                        "Falha na criação",
                        f"❌ Falha ao criar virtualenv:\n{error_msg}\n\n"
                        f"Deseja tentar via terminal automático?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        return self._create_venv_via_terminal_fallback(venv_name)
                    else:
                        QMessageBox.critical(
                            self,
                            "Erro na criação",
                            f"❌ Falha ao criar virtualenv:\n{error_msg}"
                        )
                    return False
    
            except subprocess.TimeoutExpired:
                progress.close()
                QMessageBox.critical(
                    self, 
                    "Timeout", 
                    "⏰ Timeout ao criar virtualenv.\n\n"
                    "O processo demorou muito para responder."
                )
                return False
    
        except Exception as e:
            self.debug_log(f"❌ Erro inesperado ao criar venv: {e}", "ERROR")
            QMessageBox.critical(
                self, 
                "Erro inesperado", 
                f"❌ Erro inesperado:\n{str(e)}"
            )
            return False
    
    def _detect_best_python_for_venv(self):
        """Detecta o melhor Python disponível para criar virtualenv - DINÂMICO E COMPLETO"""
        try:
            python_candidates = []
            
            # 1. Python do SettingsManager (prioridade máxima)
            try:
                if hasattr(self, 'settings_manager') and self.settings_manager:
                    python_exec = self.settings_manager.get_python_for_vm_creation()
                    if python_exec and os.path.exists(python_exec) and self._check_venv_module(python_exec):
                        self.debug_log(f"✅ Python do SettingsManager: {python_exec}", "SUCCESS")
                        return python_exec
            except Exception as e:
                self.debug_log(f"⚠️ Erro no Python do SettingsManager: {e}", "WARNING")
            
            # 2. Python do sistema atual
            if sys.executable and self._check_venv_module(sys.executable):
                python_candidates.append(sys.executable)
                self.debug_log(f"✅ Python do sistema: {sys.executable}", "SUCCESS")
            
            # 3. DETECÇÃO DINÂMICA DE TODAS AS VERSÕES PYTHON 3.x
            python_commands = self._generate_python_commands()
            
            # Testar cada comando
            for cmd in python_commands:
                try:
                    python_path = self._test_python_command(cmd)
                    if python_path and python_path not in python_candidates:
                        python_candidates.append(python_path)
                        self.debug_log(f"✅ Python válido encontrado: {python_path}", "SUCCESS")
                except Exception as e:
                    continue
            
            # 4. Ordenar por versão (mais recente primeiro)
            python_candidates = self._sort_python_by_version(python_candidates)
            
            # 5. Selecionar o melhor candidato
            for python_exec in python_candidates:
                if python_exec and self._check_venv_module(python_exec):
                    version_info = self._get_python_version(python_exec)
                    self.debug_log(f"🎯 Python selecionado: {python_exec} ({version_info})", "SUCCESS")
                    return python_exec
            
            self.debug_log("❌ Nenhum Python válido encontrado", "ERROR")
            return None
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao detectar Python: {e}", "ERROR")
            return None
    
    def _generate_python_commands(self):
        """Gera lista de comandos Python para testar - VERSÕES 3.0 ATÉ 3.30"""
        python_commands = []
        
        # Comandos genéricos (maior compatibilidade)
        generic_commands = ['python3', 'python']
        
        if os.name == 'nt':  # Windows
            generic_commands.extend(['py', 'py -3'])
        else:  # Linux/Mac
            generic_commands.extend(['python3', 'python'])
        
        python_commands.extend(generic_commands)
        
        # Versões específicas do Python 3.0 até 3.30
        for version_major in [3]:  # Python 3.x
            for version_minor in range(31, -1, -1):  # 3.30 até 3.0 (ordem decrescente)
                version = f"{version_major}.{version_minor}"
                
                if os.name == 'nt':  # Windows
                    # Comandos py launcher
                    python_commands.append(f"py -{version}")
                    python_commands.append(f"py -{version_major}.{version_minor}")
                    
                    # Caminhos comuns do Windows
                    python_commands.extend([
                        f'C:\\Python{version}\\python.exe',
                        f'C:\\Program Files\\Python{version}\\python.exe',
                        f'C:\\Users\\{os.getenv("USERNAME", "User")}\\AppData\\Local\\Programs\\Python\\Python{version}\\python.exe'
                    ])
                else:  # Linux/Mac
                    # Comandos diretos
                    python_commands.append(f"python{version}")
                    python_commands.append(f"python{version_major}.{version_minor}")
                    
                    # Caminhos comuns do Linux/Mac
                    python_commands.extend([
                        f'/usr/bin/python{version}',
                        f'/usr/local/bin/python{version}',
                        f'/opt/homebrew/bin/python{version}',
                        f'/usr/bin/python{version_major}.{version_minor}',
                        f'/usr/local/bin/python{version_major}.{version_minor}'
                    ])
        
        # Remover duplicatas
        unique_commands = []
        seen = set()
        for cmd in python_commands:
            if cmd not in seen:
                unique_commands.append(cmd)
                seen.add(cmd)
        
        self.debug_log(f"🔍 Gerados {len(unique_commands)} comandos Python para testar", "INFO")
        return unique_commands
    
    def _test_python_command(self, cmd):
        """Testa um comando Python específico"""
        try:
            if ' ' in cmd:  # Comando com argumentos (ex: py -3.11)
                parts = cmd.split()
                result = subprocess.run(
                    parts + ['--version'],
                    capture_output=True, text=True, timeout=3
                )
            else:  # Comando simples
                result = subprocess.run(
                    [cmd, '--version'],
                    capture_output=True, text=True, timeout=3
                )
            
            if result.returncode == 0:
                # Obter o caminho real do Python
                if ' ' in cmd:
                    parts = cmd.split()
                    path_result = subprocess.run(
                        parts + ['-c', 'import sys; print(sys.executable)'],
                        capture_output=True, text=True, timeout=3
                    )
                else:
                    path_result = subprocess.run(
                        [cmd, '-c', 'import sys; print(sys.executable)'],
                        capture_output=True, text=True, timeout=3
                    )
                
                if path_result.returncode == 0:
                    python_path = path_result.stdout.strip()
                    if python_path and os.path.exists(python_path):
                        return python_path
            
            return None
            
        except Exception as e:
            return None
    
    def _get_python_version(self, python_exec):
        """Obtém a versão do Python de forma segura"""
        try:
            result = subprocess.run(
                [python_exec, '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "Versão desconhecida"
        except:
            return "Versão desconhecida"
    
    def _sort_python_by_version(self, python_list):
        """Ordena lista de Pythons por versão (mais recente primeiro)"""
        if not python_list:
            return []
        
        version_pairs = []
        
        for python_exec in python_list:
            try:
                version = self._extract_version_number(python_exec)
                if version:
                    version_pairs.append((version, python_exec))
            except:
                continue
        
        # Ordenar por versão (decrescente)
        version_pairs.sort(key=lambda x: x[0], reverse=True)
        
        return [pair[1] for pair in version_pairs]
    
    def _extract_version_number(self, python_exec):
        """Extrai número de versão do caminho/comando do Python"""
        try:
            # Tentar obter versão executando o Python
            result = subprocess.run(
                [python_exec, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                version_str = result.stdout.strip()
                # Converter "3.11.2" para número 311.2 para comparação
                parts = version_str.split('.')
                if len(parts) >= 2:
                    major = int(parts[0])
                    minor = int(parts[1])
                    micro = int(parts[2]) if len(parts) > 2 else 0
                    return major * 100 + minor + micro * 0.01
        except:
            pass
        
        # Fallback: extrair do caminho/nome
        python_str = str(python_exec).lower()
        
        # Padrões para extrair versão do caminho
        patterns = [
            r'python-?(\d+)\.(\d+)',  # python-3.11, python3.11
            r'py-?(\d+)\.(\d+)',      # py-3.11
            r'\\python(\d)(\d+)\\',   # \python311\ (Windows)
            r'/python(\d)(\d+)/',     # /python311/ (Linux)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, python_str)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                return major * 100 + minor
        
        return 0  # Versão desconhecida - menor prioridade
    
    def _check_venv_module(self, python_exec):
        """Verifica se o Python tem módulo venv - COM FALLBACK"""
        try:
            # Método 1: Verificar help do módulo venv
            result = subprocess.run(
                [python_exec, '-m', 'venv', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True
            
            # Método 2: Tentar importar o módulo
            result = subprocess.run(
                [python_exec, '-c', 'import venv'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except:
            return False
    
    def _create_venv_via_terminal_fallback(self, venv_name):
        """Fallback via terminal para criação de venv"""
        try:
            if not hasattr(self, 'real_terminal') or not self.real_terminal:
                self.debug_log("❌ Terminal não disponível para fallback", "ERROR")
                return False
            
            # Garantir que o terminal está visível
            self.show_terminal()
            
            # Mudar para o diretório do projeto
            self.real_terminal.change_directory(self.project_path)
            
            # Comando simples que tem maior chance de funcionar
            venv_command = "python3 -m venv venv\n"
            
            # Enviar comando
            self.real_terminal.send_command(f"echo '🔨 Criando virtualenv via fallback...'\n")
            self.real_terminal.send_command(venv_command)
            self.real_terminal.send_command(f"echo '⏳ Aguarde...'\n")
            
            # Pequena pausa para criação
            QTimer.singleShot(5000, lambda: self._check_venv_after_terminal_fallback(venv_name))
            
            self.debug_log("✅ Comando de fallback enviado ao terminal", "SUCCESS")
            return True
            
        except Exception as e:
            self.debug_log(f"❌ Erro no fallback via terminal: {e}", "ERROR")
            return False
    
    def _check_venv_after_terminal_fallback(self, venv_name):
        """Verifica se o venv foi criado após tentativa via terminal"""
        try:
            venv_path = os.path.join(self.project_path, venv_name)
            
            if os.path.exists(venv_path) and self.is_valid_venv(venv_path):
                success = self.activate_venv_in_project(venv_path)
                if success:
                    QMessageBox.information(
                        self, 
                        "Sucesso via Terminal", 
                        f"✅ Virtualenv criado com sucesso via terminal!\n\n"
                        f"📁 Local: {venv_path}\n"
                        f"⚡ Status: Ativado automaticamente"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Aviso",
                        f"Virtualenv criado mas não foi possível ativar:\n{venv_path}"
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Falha via Terminal",
                    f"❌ Não foi possível criar virtualenv via terminal.\n\n"
                    f"Tente criar manualmente no terminal:\n"
                    f"python3 -m venv {venv_name}"
                )
        except Exception as e:
            self.debug_log(f"❌ Erro ao verificar venv após fallback: {e}", "ERROR")