
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
from debug.terminal import SystemTerminalWrapper, TerminalTextEdit
from debug.debug_system import  DebugTerminal, DebugWorker
















class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
    
    # ✅ CORREÇÃO: Inicializar variáveis PRIMEIRO
        self._initialize_variables()
        self._initialize_debug_log()
    
    # ✅ CORREÇÃO: Configurar UI DEPOIS das variáveis
        try:
            self.setup_plugins()
            self.setup_managers()
            self.setup_ui()  # ✅ Isso vai chamar setup_main_tabs e setup_terminal_tab
            self.setup_connections()
            self.setup_shortcuts()
            
        # Configurar sistemas avançados
            self.setup_syntax_highlighting_system()
            self.setup_autocomplete()
        
        # CORREÇÃO: Inicializar LSP de forma segura
            self.setup_lsp_system()
        
        # Configurar exceções globais
            sys.excepthook = self.exception_hook
        
        # CORREÇÃO: Inicialização sequencial com delays
            QTimer.singleShot(100, self.initialize_delayed_systems)
        
            self.debug_log("IDE inicializado com sucesso", "SUCCESS")
        
        except Exception as e:
            self.debug_log(f"Erro na inicialização do IDE: {e}", "ERROR")
            QMessageBox.critical(self, "Erro", f"Falha ao iniciar IDE: {e}")

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
        self.file_path = ""
        
        # CORREÇÃO: Inicializar editor como None
        self.editor = None
        
        # Inicializar processos como None
             
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
        self.system_terminal_wrapper = None
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
        
        # CORREÇÃO: Adicionar atributos faltantes para terminal
        
        self.terminal_dock = None
        
        # CORREÇÃO: Adicionar atributos para autocomplete
        self.autocomplete_widget = None
        self.autocomplete_timer = None
        
        # CORREÇÃO: Adicionar atributos para plugins
        self.plugin_manager = None
        
        # CORREÇÃO: Adicionar atributos para LSP
        self.lsp_manager = None
        
        # CORREÇÃO: Adicionar atributos para indicadores visuais
        self.current_line_highlight = True
        self.show_line_numbers = True
        self.show_minimap = True
        self.indicator_colors = {}
        
        # CORREÇÃO: Adicionar atributos para splitter
        self.main_splitter = None
        
        # CORREÇÃO: Adicionar atributos para outline
        self.outline_widget = None
        self.scope_info_label = None
        
        # CORREÇÃO: Adicionar atributos para debug
        self.debug_mode = False
        self.current_debug_file = None
        
        # CORREÇÃO: Adicionar atributos para syntax highlighting
        self.syntax_highlighting_manager = None
        self.language_config = None
        self.language_syntax_manager = None
        
        # CORREÇÃO: Adicionar atributos para gerenciadores
        self.python_version_manager = None
        self.theme_manager = None
        self.indentation_checker = None
    
    
    def _initialize_debug_log(self):
        """Inicializa o sistema de logging PRIMEIRO"""
    # Definir o método debug_log antes de qualquer uso
        def debug_log(message, level="INFO"):
                levels = {
                "INFO": "ℹ️",
                "SUCCESS": "✅", 
                "WARNING": "⚠️",
                "ERROR": "❌",
                "DEBUG": "🐛"
                }
                icon = levels.get(level, "🔵")
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"{icon} [{timestamp}] {message}")
    
        # Atribuir ao self
        self.debug_log = debug_log
        print("✅ Sistema de logging inicializado")
            
            
    def initialize_delayed_systems(self):
        """Inicializa sistemas que dependem da UI estar completamente carregada"""
        try:
            self.debug_log("🔄 Inicializando sistemas atrasados...")
            
        # Configurar escopo
            self.setup_scope_header()
        
        # Configurar indicadores visuais
            self.setup_indicators()
        
        # Conectar sinais de undo/redo
            QTimer.singleShot(200, self.setup_undo_redo_connections)
        
        # Atualizar outline inicial
            if hasattr(self, 'outline_widget'):
                QTimer.singleShot(300, self.outline_widget.refresh_outline)
            
        # ✅ REMOVIDO: Não mostrar terminal automaticamente
        # QTimer.singleShot(2000, lambda: self.show_terminal())
    
            self.debug_log("✅ Sistemas atrasados inicializados", "SUCCESS")
        
        except Exception as e:
            self.debug_log(f"❌ Erro em sistemas atrasados: {e}", "ERROR")

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
            self.debug_log(f"Erro ao verificar estado do terminal: {e}", "ERROR")
            return {'visible': False, 'available': False, 'tab_count': 0}         
        
    def setup_managers(self):
	    """Inicializa todos os gerenciadores do sistema - VERSÃO MAIS SEGURA"""
	    try:
	        print("🔧 Inicializando gerenciadores...")
    
        # Gerenciador de versões Python - COM VERIFICAÇÃO
	        try:
	            
	            self.python_version_manager = PythonVersionManager()
	            print("✅ Gerenciador de versões Python inicializado")
	        except Exception as e:
	            print(f"⚠️ Erro ao inicializar gerenciador de versões Python: {e}")
	            self.python_version_manager = None
            
        # Gerenciador de temas - COM VERIFICAÇÃO
	        try:
	            from core.theme_manager import ThemeManager
	            self.theme_manager = ThemeManager()
	            print("✅ Gerenciador de temas inicializado")
	        except Exception as e:
	            print(f"⚠️ Erro ao inicializar gerenciador de temas: {e}")
	            self.theme_manager = None
        
        # Verificador de indentação - COM VERIFICAÇÃO
	        try:
	            from tools.indentation_checker import IndentationChecker
	            self.indentation_checker = IndentationChecker()
	            print("✅ Verificador de indentação inicializado")
	        except Exception as e:
	            print(f"⚠️ Erro ao inicializar verificador de indentação: {e}")
	            self.indentation_checker = None
            
        # Configuração de linguagem - COM VERIFICAÇÃO
	        try:
	            from syntax.language_config import LanguageConfig
	            self.language_config = LanguageConfig()
	            print("✅ Configuração de linguagem inicializada")
	        except Exception as e:
	            print(f"⚠️ Erro ao inicializar configuração de linguagem: {e}")
	            self.language_config = None
            
        # Gerenciador de sintaxe - COM VERIFICAÇÃO
	        try:
	            from syntax.syntax_manager import LanguageSyntaxManager
	            self.language_syntax_manager = LanguageSyntaxManager()
	            print("✅ Gerenciador de sintaxe inicializado")
	        except Exception as e:
	            print(f"⚠️ Erro ao inicializar gerenciador de sintaxe: {e}")
	            self.language_syntax_manager = None

        # Gerenciador de cache global - COM VERIFICAÇÃO
	        try:
	            from cache.module_cache import ModuleCacheManager
	            global module_cache_manager
	            module_cache_manager = ModuleCacheManager()
	            print("✅ Gerenciador de cache inicializado")
	        except Exception as e:
	            print(f"⚠️ Erro ao inicializar gerenciador de cache: {e}")
	            module_cache_manager = None
            
        # Gerenciador de syntax highlighting (será configurado depois)
	        self.syntax_highlighting_manager = None
        
        # Gerenciador LSP (será configurado depois)
	        self.lsp_manager = None
        
	        print("✅ Gerenciadores principais inicializados")
        
	    except Exception as e:
	        print(f"❌ Erro crítico ao inicializar gerenciadores: {e}")
        # Define valores padrão para evitar NoneType errors
	        self.python_version_manager = None
	        self.theme_manager = None
	        self.indentation_checker = None
	        self.language_config = None
	        self.language_syntax_manager = None
    
    def debug_log(self, message, level="INFO"):
        """Sistema de logging consistente - DEFINIR AGORA"""
        levels = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🐛"
        }
        icon = levels.get(level, "🔵")
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{icon} [{timestamp}] {message}")
    
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
    

    def setup_ui(self):
        """Configura a interface do usuário - VERSÃO CORRIGIDA"""
        try:
            self.setWindowTitle("Py Dragon Studio IDE")
            self.setGeometry(100, 100, 1400, 900)
    
            self.set_dark_theme_optimized()
    
            # ✅ CORREÇÃO: Criar layout principal como objeto
            self.main_layout = QVBoxLayout()
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.setSpacing(0)
        
            # Criar widget central
            central_widget = QWidget()
            central_widget.setLayout(self.main_layout)
            self.setCentralWidget(central_widget)

        # ✅ CORREÇÃO: Chamar setup_main_tabs primeiro
            self.setup_main_tabs()
            self.setup_central_widget()
            self.setup_docks()  # ✅ Isso cria o output_tabs
            self.setup_menu()
            self.setup_toolbar()
            self.setup_statusbar()

       
        
            self.debug_log("UI configurada com sucesso", "SUCCESS")
    
        except Exception as e:
            self.debug_log(f"Erro ao configurar UI: {e}", "ERROR")
   
    
    def show_terminal(self):
        """Força o terminal a ficar visível"""
        try:
            # Mostra o dock de output
            for dock in self.findChildren(QDockWidget):
                if dock.windowTitle() == "Output":
                    dock.show()
                    dock.raise_()
                    break
        
            # Foca na aba do terminal
            if hasattr(self, 'output_tabs'):
                for i in range(self.output_tabs.count()):
                    if self.output_tabs.tabText(i) == "💻 Terminal":
                        self.output_tabs.setCurrentIndex(i)
                        self.debug_log("✅ Terminal focado", "SUCCESS")
                        return True
            
            self.debug_log("❌ Não foi possível encontrar a aba do terminal", "ERROR")
            return False
            
        except Exception as e:
            self.debug_log(f"Erro ao mostrar terminal: {e}", "ERROR")
            return False 

    def setup_terminal_fallback(self):
        try:
            self.debug_log("Usando fallback para terminal", "INFO")
            # Cria um terminal básico
            self.terminal_text = QPlainTextEdit()
            self.terminal_text.setReadOnly(True)
            self.terminal_text.setFont(QFont("Consolas", 10))
            self.terminal_text.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                    font-family: 'Consolas', monospace;
                }
            """)
            
            if hasattr(self, 'main_tabs'):
                self.main_tabs.addTab(self.terminal_text, "💻 Terminal")
                
            self.debug_log("Terminal fallback configurado", "SUCCESS")
        except Exception as e:
            self.debug_log(f"Erro no terminal fallback: {e}", "ERROR")

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
        """Configura todas as docks - VERSÃO CORRIGIDA"""
        try:
            self.setup_left_dock()
            self.setup_bottom_dock()  # ✅ GARANTIR QUE ESTA LINHA ESTÁ PRESENTE
            self.debug_log("Docks configuradas", "SUCCESS")
        except Exception as e:
            self.debug_log(f"Erro ao configurar docks: {e}", "ERROR")
            

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

    def setup_terminal_tab(self):
        """Configura a aba de terminal - APENAS SISTEMA"""
        try:
            # Container principal do terminal
            terminal_container = QWidget()
            terminal_layout = QVBoxLayout(terminal_container)
            terminal_layout.setContentsMargins(0, 0, 0, 0)
        
            # Abas para diferentes tipos de terminal
            self.terminal_tabs = QTabWidget()
            self.terminal_tabs.setStyleSheet("""
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
                
            # ✅ APENAS SystemTerminalWrapper
            try:
                from debug.terminal import SystemTerminalWrapper
                self.system_terminal_wrapper = SystemTerminalWrapper(self)
                self.terminal_tabs.addTab(self.system_terminal_wrapper, "⚡ Sistema")
            except ImportError as e:
                self.debug_log(f"SystemTerminalWrapper não disponível: {e}", "WARNING")
                # Fallback básico
                system_fallback = QWidget()
                layout = QVBoxLayout(system_fallback)
                label = QLabel("Terminal do Sistema não disponível\nUse o menu Ferramentas para abrir terminal externo")
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
                self.terminal_tabs.addTab(system_fallback, "⚡ Sistema (Fallback)")
            
            terminal_layout.addWidget(self.terminal_tabs)
            
            # ✅ Adicionar ao output_tabs
            if hasattr(self, 'output_tabs'):
                self.output_tabs.addTab(terminal_container, "💻 Terminal")
                self.debug_log("Terminal (apenas sistema) adicionado ao output_tabs", "SUCCESS")
            else:
                self.debug_log("output_tabs não disponível", "ERROR")
            
            self.debug_log("Terminal tab configurado com sucesso (apenas sistema)", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"Erro ao configurar terminal tab: {e}", "ERROR")
            
        
        
        
                
    def check_terminal_visibility(self):
        """Verifica se o terminal está visível e acessível"""
        try:
            # Verifica se o terminal está no output_tabs
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
            self.debug_log(f"Erro ao verificar terminal: {e}", "ERROR")
            return False            
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
    def test_syntax_highlighting(self):
        """Testa o syntax highlighting em todos os editores abertos"""
        print(f"\n🧪 TESTE DE SYNTAX HIGHLIGHTING")
        
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'editor'):
                print(f"\n--- Aba {i}: {self.tab_widget.tabText(i)} ---")
                widget.editor.debug_syntax_info()
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
        python_versions_action = QAction("🐍 Gerenciador de Versões Python", self)
        python_versions_action.triggered.connect(self.open_python_version_manager)
        tools_menu.addAction(python_versions_action)

        # Localizador de Textos Similares Aprimorado
        find_similar_action = QAction("🔍 Localizador de Textos Similares", self)
        find_similar_action.setShortcut("Ctrl+Shift+F")
        find_similar_action.triggered.connect(self.open_advanced_find_similar)
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
    
        # GERENCIADOR DE PLUGINS - CORRIGIDO
        plugin_manager_action = QAction("🔌 Gerenciador de Plugins", self)
        plugin_manager_action.triggered.connect(self.show_plugin_manager_dialog)  # Método correto
        tools_menu.addAction(plugin_manager_action)
    
        # Instalar Plugin
        install_plugin_action = QAction("📥 Instalar Plugin", self)
        install_plugin_action.triggered.connect(self.install_new_plugin)
        tools_menu.addAction(install_plugin_action)
    
        # Atualizar Plugins
        refresh_plugins_action = QAction("🔄 Atualizar Plugins", self)
        refresh_plugins_action.triggered.connect(self.refresh_plugins)
        tools_menu.addAction(refresh_plugins_action)
    
        tools_menu.addSeparator()

        # Outras ferramentas existentes
        manage_packages_action = QAction("🔧 Gerenciar Pacotes", self)
        manage_packages_action.triggered.connect(self.manage_packages)
        tools_menu.addAction(manage_packages_action)

        select_python_action = QAction("🐍 Selecionar Python", self)
        select_python_action.triggered.connect(self.select_python_version)
        tools_menu.addAction(select_python_action)
    
        format_action = QAction("📐 Formatar Código", self)
        format_action.setShortcut("Ctrl+Shift+L")
        format_action.triggered.connect(self.format_code)
        tools_menu.addAction(format_action)

        settings_action = QAction("⚙️ Configurações", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
   

    


    def open_python_version_manager(self):
        """Abre o gerenciador de versões Python"""
        try:
            # ✅ TENTA IMPORTAR E CRIAR O VERSION MANAGER
            try:
                version_manager = PythonVersionManager()
            except Exception as e:
                print(f"⚠️ Não foi possível criar version manager: {e}")
                version_manager = None
        
            dialog = PythonVersionDialog(self, version_manager)
            dialog.exec()
        
        except Exception as e:
            print(f"❌ Erro ao abrir gerenciador de versões: {e}")
            QMessageBox.critical(
                self, 
                "Erro", 
                f"Não foi possível abrir o gerenciador de versões:\n{str(e)}"
   	        )
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
        try:
            # Verifica se pip está disponível
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
        """Abre o gerenciador de temas - VERSÃO SEGURA"""
        try:
            if not hasattr(self, 'theme_manager') or self.theme_manager is None:
                QMessageBox.warning(self, "Aviso", 
                                  "Gerenciador de temas não está disponível.\n\n"
                                  "Recarregue o aplicativo ou verifique os logs.")
                return
                
            dialog = ThemeDialog(self.theme_manager, self)
            dialog.exec()
        except Exception as e:
            print(f"❌ Erro ao abrir gerenciador de temas: {e}")
            QMessageBox.warning(self, "Erro", 
                              f"Não foi possível abrir o gerenciador de temas:\n{str(e)}")

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
    def setup_main_tabs(self):
        """Configura as abas principais do IDE - VERSÃO CORRIGIDA"""
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
        
            # ✅ CORREÇÃO: Usar main_layout em vez de layout
            if hasattr(self, 'main_layout'):
                self.main_layout.addWidget(self.main_tabs)
            else:
                # Fallback: criar layout se não existir
                self.main_layout = QVBoxLayout()
                central_widget = QWidget()
                central_widget.setLayout(self.main_layout)
                self.setCentralWidget(central_widget)
                self.main_layout.addWidget(self.main_tabs)
                
            self.debug_log("Abas principais configuradas", "SUCCESS")
            
        except Exception as e:
            self.debug_log(f"Erro ao configurar abas principais: {e}", "ERROR")
    
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
            ("👁️ Mostrar/Ocultar Terminal", "Ctrl+`", self.toggle_terminal),  # ✅ APENAS ESTE

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
                try:
                    # Cria editor CORRETO - MOVER A CRIAÇÃO DO EDITOR PARA DENTRO DO TRY
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
    
                    # Configurar conexões do editor
                    self.setup_editor_connections(editor)
    
                    # Adiciona à aba
                    index = self.tab_widget.addTab(editor_tab, f"📄 {file_name}")
                    self.tab_widget.setCurrentIndex(index)
    
                    editor.setFocus()
                    self.update_file_info(None)
                
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Erro ao criar novo arquivo: {str(e)}")
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
	    """Define projeto atual com suporte LSP - VERSÃO CORRIGIDA"""
	    if not project_path:
	        project_path = QFileDialog.getExistingDirectory(
	            self,
	            "Selecionar Projeto",
	            self.project_path or QDir.homePath()
	        )

	    if project_path:
	        self.project_path = project_path
	        self.project_info_label.setText(f"📦 {os.path.basename(project_path)}")

        # CORREÇÃO: Verificar se LSP manager existe antes de usar
	        if hasattr(self, 'lsp_manager') and self.lsp_manager is not None:
	            try:
	                self.lsp_manager.initialize(project_path)
	                self.debug_log(f"LSP inicializado para projeto: {project_path}", "SUCCESS")
	            except Exception as e:
	                self.debug_log(f"Erro ao inicializar LSP: {e}", "ERROR")
	        else:
	            self.debug_log("LSP manager não disponível - continuando sem LSP", "WARNING")

        # Atualiza explorador
	        self.refresh_explorer()

        # Ativa no terminal
	        self.activate_project()

	        self.statusBar().showMessage(f"✅ Projeto carregado: {project_path}", 3000)

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
        """Remove códigos de escape ANSI de forma mais abrangente"""
        import re
        # Padrão mais abrangente para códigos ANSI
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
        
        # Remove também caracteres de controle problemáticos
        cleaned = ansi_escape.sub('', text)
        
        # Remove outros caracteres de controle problemáticos
        control_chars = re.compile(r'[\x00-\x1f\x7f-\x9f]')
        cleaned = control_chars.sub('', cleaned)
        
        return cleaned
    
    

    
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
        """Mostra/esconde o dock do terminal de forma inteligente"""
        try:
            dock_found = False
        
            # Procura pela dock de Output
            for dock in self.findChildren(QDockWidget):
                if dock.windowTitle() == "Output":
                    is_visible = dock.isVisible()
                    
                    if not is_visible:
                        # ✅ MOSTRAR: Torna visível e foca no terminal
                        dock.show()
                        dock.raise_()
                        
                        # Foca na aba do terminal
                        if hasattr(self, 'output_tabs'):
                            for i in range(self.output_tabs.count()):
                                if self.output_tabs.tabText(i) == "💻 Terminal":
                                    self.output_tabs.setCurrentIndex(i)
                                    break
                        
                        self.debug_log("✅ Terminal mostrado e focado", "SUCCESS")
                    else:
                        # ✅ OCULTAR: Apenas esconde
                        dock.hide()
                        self.debug_log("✅ Terminal ocultado", "SUCCESS")
                
                    dock_found = True
                    break

            if not dock_found:
                self.debug_log("❌ Dock 'Output' não encontrado", "ERROR")
                # Tenta criar a dock se não existir
                self.setup_bottom_dock()
                    
        except Exception as e:
            self.debug_log(f"Erro ao alternar terminal: {e}", "ERROR")
            
            
    def show_terminal_dock(self):
        """Força a exibição da dock do terminal"""
        try:
            dock_found = False
            
            for dock in self.findChildren(QDockWidget):
                if dock.windowTitle() == "Output":
                    if not dock.isVisible():
                        dock.show()
                        dock.raise_()
                    
                    # Foca no terminal
                    if hasattr(self, 'output_tabs'):
                        for i in range(self.output_tabs.count()):
                            if self.output_tabs.tabText(i) == "💻 Terminal":
                                self.output_tabs.setCurrentIndex(i)
                                break
                    
                    dock_found = True
                    self.debug_log("✅ Dock do terminal mostrada e focada", "SUCCESS")
                    break
            
            if not dock_found:
                self.debug_log("❌ Não foi possível encontrar a dock do terminal", "ERROR")
                return False
            
            return True
        
        except Exception as e:
            self.debug_log(f"Erro ao mostrar dock do terminal: {e}", "ERROR")
            return False            
            
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
                        
                        
                            
    def setup_bottom_dock(self):
        """Configura a dock inferior (Output) - SEM TERMINAL"""
        try:
            self.debug_log("🔄 Configurando dock inferior...", "INFO")
            
            # ✅ PRIMEIRO: Criar output_tabs se não existir
            if not hasattr(self, 'output_tabs') or self.output_tabs is None:
                self.output_tabs = QTabWidget()
                self.output_tabs.setTabPosition(QTabWidget.North)
                self.debug_log("✅ output_tabs criado", "SUCCESS")
            
            # ✅ SEGUNDO: Criar apenas as abas úteis (SEM TERMINAL)
            self.setup_output_tab()
            self.setup_debug_tab()
            self.setup_errors_tab() 
            self.setup_lint_tab()
            
            # ✅ TERCEIRO: NÃO criar a aba do terminal
            # self.setup_terminal_tab()  # ✅ REMOVIDO
            
            # ✅ QUARTO: Criar a dock
            bottom_dock = QDockWidget("Output", self)
            bottom_dock.setFeatures(
                QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
            bottom_dock.setMinimumHeight(0)
            bottom_dock.setWidget(self.output_tabs)
        
        # ✅ QUINTO: Adicionar ao IDE
            self.addDockWidget(Qt.BottomDockWidgetArea, bottom_dock)
        
        # ✅ MANTER VISÍVEL POR PADRÃO
            bottom_dock.setVisible(True)  # ✅ ALTERADO: True em vez de False
        
            self.debug_log("✅ Dock inferior (Output) configurada SEM terminal", "SUCCESS")
            return True
            
        except Exception as e:
            self.debug_log(f"❌ Erro crítico ao configurar dock inferior: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
        
    def set_light_theme(self):
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
    

    def stop_process(self, process):

        """Para um processo de forma segura"""

        if process and process.state() == QProcess.Running:
            process.terminate()
            if not process.waitForFinished(1000):
                process.kill()
                process.waitForFinished(1000)


    def trigger_unified_autocomplete(self):
        """Dispara autocomplete usando o sistema unificado"""
        try:
            editor = self.get_current_editor()
            if not editor or not hasattr(self, 'autocomplete_widget'):
                return
                
            # Implementação básica de autocomplete
            cursor = editor.textCursor()
            current_text = editor.toPlainText()
            cursor_position = cursor.position()
            
            # Obter sugestões do sistema unificado
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
        self.autocomplete_timer.start(300)  # 300ms delay
    
    def connect_editor_autocomplete(self, index):
        """Conecta autocomplete ao editor atual"""
        if index >= 0:
            widget = self.tab_widget.widget(index)
            if hasattr(widget, 'editor'):
                editor = widget.editor
                # Conectar modificações de texto
                editor.textChanged.connect(self.schedule_autocomplete)
    

    def trigger_auto_complete(self):
        """Força a exibição do autocomplete manualmente"""
        if hasattr(self, 'autocomplete_timer'):
            self.autocomplete_timer.start(100)  # Timer muito curto para resposta imediata
    
            

        
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


    

    def setup_lsp_system(self):
	    """Configura sistema LSP no IDE - VERSÃO SEGURA"""
	    try:
        # CORREÇÃO: Verificar se a classe existe antes de instanciar
	        from analysis.lsp_client import LSPManager
        
	        self.lsp_manager = LSPManager(self)
        
        # Conectar sinais existentes para LSP
	        self.tab_widget.currentChanged.connect(self._on_tab_changed_lsp)
        
	        self.debug_log("Sistema LSP configurado", "SUCCESS")
	    except ImportError as e:
	        self.debug_log(f"LSP não disponível: {e}", "WARNING")
	        self.lsp_manager = None
	    except Exception as e:
	        self.debug_log(f"Erro ao configurar LSP: {e}", "ERROR")
	        self.lsp_manager = None
        
    def _on_tab_changed_lsp(self, index):
	    """Manipula mudança de aba para LSP - VERSÃO SEGURA"""
	    try:
	        if (index >= 0 and hasattr(self, 'lsp_manager') and 
	            self.lsp_manager is not None):
	            widget = self.tab_widget.widget(index)
	            if hasattr(widget, 'editor') and hasattr(widget, 'file_path') and widget.file_path:
	                # Atualizar LSP com documento atual
	                content = widget.editor.toPlainText()
	                self.lsp_manager.open_document(widget.file_path, content)
	    except Exception as e:
	        self.debug_log(f"Erro em _on_tab_changed_lsp: {e}", "ERROR")

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
        self.debug_log("🔄 Finalizando aplicação...", "INFO")
        
        # CORREÇÃO: Verificar se LSP manager existe antes de shutdown
        if hasattr(self, 'lsp_manager') and self.lsp_manager is not None:
            self.debug_log("🔄 Finalizando LSP...", "INFO")
            try:
                self.lsp_manager.shutdown()
            except Exception as e:
                self.debug_log(f"❌ Erro ao finalizar LSP: {e}", "ERROR")
        else:
            self.debug_log("ℹ️ LSP manager não inicializado", "INFO")
    
        # CORREÇÃO: Parar shell process de forma segura
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
    
        # Para workers em execução de forma segura
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
    
        # Finaliza plugins
        if hasattr(self, 'plugin_manager'):
            self.debug_log("🔄 Finalizando plugins...", "INFO")
            try:
                self.plugin_manager.shutdown_plugins()
            except Exception as e:
                self.debug_log(f"❌ Erro ao finalizar plugins: {e}", "ERROR")
    
        # Aceita o evento de fechamento
        event.accept()
        self.debug_log("👋 Aplicação finalizada com sucesso", "SUCCESS")
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
    def setup_syntax_highlighting_system(self):
        """Configura o sistema de syntax highlighting"""
        try:
            self.syntax_highlighting_manager = SyntaxHighlightingManager(self)
            self.debug_log("Sistema de syntax highlighting configurado", "SUCCESS")
        except Exception as e:
            self.debug_log(f"Erro ao configurar syntax highlighting: {e}", "ERROR")
    
    def setup_autocomplete(self):
        """Configura o sistema unificado de autocomplete - VERSÃO MAIS ROBUSTA"""
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
                    elif not self.enabled:
                        print("🔴 Autocomplete desativado")
            
            # Usar o sistema básico por enquanto
            self.autocomplete_widget = BasicAutoCompleteSystem(self)
            
            # Configurar timer para autocomplete automático
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
            # Sistema mínimo de fallback
            self.autocomplete_widget = type('MinimalAutoComplete', (), {'enabled': False})()




    def setup_plugins(self):
        """Inicializa o sistema de plugins de forma robusta"""
        try:
            # Adiciona o caminho dos plugins ao sys.path
            plugins_path = Path(__file__).parent / "plugins"
            if plugins_path.exists():
                sys.path.insert(0, str(plugins_path))
            
            from plugins.plugin_manager import PluginManager
            self.plugin_manager = PluginManager()
            
            # ✅ CORREÇÃO: Configura a instância do IDE nos plugins ANTES de carregar
            if hasattr(self.plugin_manager, 'set_ide_instance'):
                self.plugin_manager.set_ide_instance(self)
            
            # Carrega plugins automaticamente
            loaded_count = self.plugin_manager.auto_load_plugins()
            
            if loaded_count > 0:
                self.debug_log(f"✅ {loaded_count} plugins carregados", "SUCCESS")
            
                # ✅ CORREÇÃO: Integra ações dos plugins IMEDIATAMENTE
                self.integrate_plugin_actions()
            else:
                self.debug_log("ℹ️ Nenhum plugin encontrado", "INFO")
                
        except Exception as e:
            self.debug_log(f"❌ Erro ao configurar plugins: {e}", "ERROR")
            self.plugin_manager = None
        
    def integrate_plugin_actions(self):
        """Integra ações dos plugins na interface de forma robusta - VERSÃO CORRIGIDA"""
        try:
            if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
                self.debug_log("❌ Plugin manager não disponível", "ERROR")
                return
            
            # Obtém ações dos plugins
            all_plugin_actions = self.plugin_manager.get_all_plugin_actions()
            
            if not all_plugin_actions:
                self.debug_log("ℹ️ Nenhuma ação de plugin encontrada", "INFO")
                return
            
            self.debug_log(f"🔍 Procurando menu Ferramentas...", "INFO")
            
            # ✅ CORREÇÃO: Busca mais flexível pelo menu
            tools_menu = None
            menu_bar = self.menuBar()
            
            # Lista todos os menus para debug
            for i, action in enumerate(menu_bar.actions()):
                menu_text = action.text().replace('&', '')  # Remove aceleradores
                self.debug_log(f"  Menu {i}: '{menu_text}'", "DEBUG")
                
                # Verifica várias possibilidades de nome
                if any(name in menu_text for name in ["Ferramentas", "Tools", "🛠️"]):
                    tools_menu = action.menu()
                    self.debug_log(f"✅ Menu encontrado: '{menu_text}'", "SUCCESS")
                    break
            
            if not tools_menu:
                self.debug_log("❌ Menu Ferramentas não encontrado. Criando...", "WARNING")
                # Cria o menu se não existir
                tools_menu = self.menuBar().addMenu("🛠️ Ferramentas")
            
            # ✅ CORREÇÃO: Remove ações anteriores de plugins para evitar duplicação
            actions_to_remove = []
            for action in tools_menu.actions():
                action_text = action.text()
                # Remove separadores e cabeçalhos de plugins anteriores
                if action_text in ["--- Plugins ---", "--- Plugins ---"] or action.isSeparator():
                    actions_to_remove.append(action)
            
            for action in actions_to_remove:
                tools_menu.removeAction(action)
            
            # ✅ CORREÇÃO: Adiciona separador apenas se houver outras ações no menu
            if tools_menu.actions():
                tools_menu.addSeparator()
            
            # Adiciona cabeçalho
            header_action = self.create_action("--- Plugins ---", lambda: None)
            header_action.setEnabled(False)
            tools_menu.addAction(header_action)
            
            # Adiciona ações dos plugins
            for action in all_plugin_actions:
                tools_menu.addAction(action)
                self.debug_log(f"✅ Ação integrada: {action.text()}", "DEBUG")
            
            self.debug_log(f"✅ {len(all_plugin_actions)} ações de plugins integradas no menu Ferramentas", "SUCCESS")
            
            # ✅ CORREÇÃO: Força atualização do menu
            tools_menu.update()
            
        except Exception as e:
            self.debug_log(f"❌ Erro ao integrar ações dos plugins: {e}", "ERROR")
            import traceback
            traceback.print_exc()
    def create_action(self, text, callback, shortcut=None, tooltip=None):
        """✅ ADICIONAR: Método auxiliar para criar ações"""
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
            print(f"❌ Erro ao criar ação: {e}")
            return None
        
    def show_plugin_manager_dialog(self):
        """Mostra informações básicas dos plugins"""
        if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
            QMessageBox.information(self, "Plugins", "Sistema de plugins não disponível")
            return
        
        try:
            plugins_info = self.plugin_manager.get_plugins_info()
        
            # Usar a aba de output existente para mostrar informações
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
        
            # Usar statusBar() em vez de status_bar
            self.statusBar().showMessage("Informações dos plugins carregadas", 3000)
            
        except Exception as e:
            self.debug_log(f"Erro ao mostrar plugins: {e}", "ERROR")
    
    def refresh_plugins(self):
        """Atualiza plugins de forma segura"""
        try:
            if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
                return
            
            # Recarrega plugins
            loaded_count = self.plugin_manager.auto_load_plugins()
            
            if loaded_count > 0:
                self.debug_log(f"{loaded_count} plugins recarregados", "SUCCESS")
            else:
                self.debug_log("Nenhum plugin encontrado", "INFO")
                
        except Exception as e:
            self.debug_log(f"Erro ao atualizar plugins: {e}", "ERROR")

    def install_new_plugin(self):
        """Instala um novo plugin - versão simplificada"""
        # Diálogo para selecionar arquivo de plugin
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Instalar Plugin",
            "",
            "Arquivos Python (*.py);;Todos os arquivos (*)"
        )
        
        if file_path:
            try:
                # Copia o arquivo para a pasta de plugins
                plugins_dir = Path(__file__).parent.parent / "plugins"
                plugin_name = Path(file_path).name
                dest_path = plugins_dir / plugin_name
                
                shutil.copy2(file_path, dest_path)
            
                # Recarrega plugins
                self.refresh_plugins()
            
                QMessageBox.information(self, "Sucesso", f"Plugin {plugin_name} instalado com sucesso!")
            
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao instalar plugin: {str(e)}")



    def exception_hook(self, exctype, value, tb):
        """Captura exceções globais de forma segura"""
        try:
            error_msg = f"ERRO GLOBAL: {exctype.__name__}: {value}"
            self.debug_log(error_msg, "ERROR")
            
            # Imprime o traceback completo no console
            import traceback
            traceback.print_exception(exctype, value, tb)
            
            # Chama o hook padrão do sistema
            sys.__excepthook__(exctype, value, tb)
            
        except Exception as e:
            # Fallback seguro se algo der errado no próprio exception handler
            print(f"❌ ERRO CRÍTICO no exception_hook: {e}")
            sys.__excepthook__(exctype, value, tb)



    def append_output(self, text):
        """Adiciona saída ao terminal com tratamento robusto de erros"""
        try:
            if not text:
                return
                
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            # Filtra códigos ANSI e caracteres problemáticos
            cleaned_text = self._filter_ansi_codes(str(text))
            
            # Garante que estamos na posição correta
            if cursor.position() < self.input_start:
                cursor.movePosition(QTextCursor.End)
            
            cursor.insertText(cleaned_text)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            
        except Exception as e:
            print(f"Erro ao adicionar output: {e}")
            # Tenta uma abordagem mais simples em caso de erro
            try:
                self.moveCursor(QTextCursor.End)
                self.insertPlainText(str(text))
            except:
                pass
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



