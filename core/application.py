

import os
import sys
import re
import traceback
from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QTextEdit, QTreeWidget,
                            QListWidget, QSplitter, QStatusBar, QToolBar,
                            QMenuBar, QMenu, QFileDialog, QMessageBox,
                            QDockWidget, QPlainTextEdit, QLabel, QInputDialog,
                            QPushButton, QFileSystemModel, QTreeView,
                            QStyledItemDelegate, QSplitter, QDialog)
from PySide6.QtCore import Qt, QTimer, QSettings, QSize, QProcess, QDir
from PySide6.QtGui import (QKeySequence, QIcon, QFont, QPalette, QColor, QAction, 
                        QTextCursor, QTextDocument, QShortcut, QTextFormat)
try:
    from tools.python_manager import PythonVersionManager
    from analysis.lsp_client import LSPManager
    from core.plugin_system import PluginManager
    from core.theme_manager import ThemeManager
    from syntax.syntax_manager import SyntaxHighlightingManager
    from editor.editor_core import EditorTab, UnifiedCodeEditor
    from ui.widgets import OutlineWidget, Minimap ,ScopeHeaderWidget,ScopeIndicatorWidget,LoadingWidget,StatusBarProgress,ProblemsDelegate
    from ui.dialogs import (PythonVersionDialog, AdvancedFindSimilarDialog, 
                        PackageManagerDialog, ThemeDialog, NewFileDialog,
                        PackageDialog, DeployDialog, ProgressDialog)
    from debug.terminal import TerminalTextEdit, DebugTerminal
    from search.find_similar import FindSimilarDialog
    from tools.indentation_checker import IndentationChecker
    from syntax.language_config import LanguageConfig
    from analysis.code_analyzer import CodeAnalyzer
    from cache.module_cache import ModuleCacheManager
    from search.code_indicators import CodeIndicators
    from editor.autocomplete import HybridCompleter
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    # Define classes básicas se os imports falharem
    class PythonVersionManager:
        def __init__(self): print("PythonVersionManager placeholder")
    class LSPManager:
        def __init__(self): print("LSPManager placeholder") 
    class PluginManager:
        def __init__(self): print("PluginManager placeholder")
    class ThemeManager:
        def __init__(self): print("ThemeManager placeholder")
    class SyntaxHighlightingManager:
        def __init__(self): print("SyntaxHighlightingManager placeholder")
    class EditorTab(QWidget):
        def __init__(self): 
            super().__init__()
            self.editor = QPlainTextEdit()
            layout = QVBoxLayout(self)
            layout.addWidget(self.editor)
        def set_content(self, content): self.editor.setPlainText(content)
        def get_content(self): return self.editor.toPlainText()
    class UnifiedCodeEditor(QPlainTextEdit):
        def __init__(self, text="", cursor_position=0, file_path=None, project_path=None, parent=None):
            super().__init__(parent)
            self.setPlainText(text)
    class OutlineWidget(QWidget):
        def __init__(self, parent=None): super().__init__(parent)
    # CORREÇÃO: Adicionar Minimap placeholder
    class Minimap(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumWidth(80)
            self.setMaximumWidth(150)
            layout = QVBoxLayout(self)
            self.label = QLabel("Minimap\n(Placeholder)")
            self.label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.label)
        def set_main_editor(self, editor): pass
        def clear(self): pass
    # Diálogos placeholder
    class PythonVersionDialog(QDialog): pass
    # ... resto dos placeholders
    class AdvancedFindSimilarDialog(QDialog): pass
    class PackageManagerDialog(QDialog): pass
    class ThemeDialog(QDialog): pass
    class NewFileDialog(QDialog): pass
    class PackageDialog(QDialog): pass
    class DeployDialog(QDialog): pass
    class ProgressDialog(QDialog): pass
    class TerminalTextEdit(QPlainTextEdit): pass
    class DebugTerminal(QPlainTextEdit): pass
    class FindSimilarDialog(QDialog): pass
    class IndentationChecker: pass
    class LanguageConfig: pass
    class CodeAnalyzer: pass
    class ModuleCacheManager: pass
    class CodeIndicators: pass
    class HybridCompleter: pass


class ProblemsDelegate(QStyledItemDelegate):
    """Delegate personalizado para a lista de problemas"""
    def paint(self, painter, option, index):
        super().paint(painter, option, index)



class IDE(QMainWindow):
    """Classe principal da IDE"""
    
    def __init__(self):
        super().__init__()
        
        # INICIALIZAR ATRIBUTOS PRIMEIRO
        self._initialize_variables()
    
    # DEPOIS configurar a UI - COM MELHOR TRATAMENTO DE ERRO
        try:
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

            # Configurar scope header com delay para garantir que a UI está pronta
            QTimer.singleShot(100, self.setup_scope_header)
        
            print("✅ IDE inicializada com sucesso")
        
        except Exception as e:
            print(f"❌ Erro crítico na inicialização: {e}")
            # Tentar pelo menos mostrar a janela básica
            self.setWindowTitle("Py Dragon Studio IDE - Modo de Recuperação")
            self.statusBar().showMessage(f"Erro na inicialização: {e}")



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
    def setup_autocomplete(self):
        """Configura o sistema de autocomplete de forma unificada"""
        try:
            # Inicializa o completador híbrido
            self.completer = HybridCompleter()

            # Shortcut global para autocomplete
            self.autocomplete_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
            self.autocomplete_shortcut.activated.connect(self.trigger_global_autocomplete)

            print("✅ Sistema de autocomplete inicializado")

        except Exception as e:
            print(f"❌ Erro no setup do autocomplete: {e}")
    
    def setup_syntax_highlighting_system(self):
        """Configura o sistema de syntax highlighting"""
        try:
            self.syntax_highlighting_manager = SyntaxHighlightingManager(self)
            print("✅ Sistema de syntax highlighting configurado")
        except Exception as e:
            print(f"❌ Erro ao configurar syntax highlighting: {e}")


    def parse_command_line_args(self):
        """Processa --project e --python se launcher iniciar sem socket"""
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        project = None
        python_ver = None
        for i, arg in enumerate(args):
            if arg == "--project" and i + 1 < len(args):
                project = args[i + 1]
            elif arg == "--python" and i + 1 < len(args):
                python_ver = args[i + 1]
        if project:
            QTimer.singleShot(1000, lambda: self.set_project(project))  # Delay para UI carr

    def _initialize_variables(self):
        """INICIALIZAÇÃO SEGURA: Define TODAS as variáveis com valores padrão - VERSÃO ÚNICA"""
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
    
        # CORREÇÃO: Inicializar atributos do terminal
        self.terminal_process_started = False
    def exception_hook(self, exctype, value, tb):
        """Captura exceções globais"""
        print("ERRO GLOBAL:", exctype, value)
        traceback.print_exception(exctype, value, tb)
        sys.__excepthook__(exctype, value, tb)

    def setup_plugin_system(self):
        """Inicializa o sistema de plugins de forma segura"""
        try:
            self.plugin_manager = PluginManager(self)
            self.plugin_manager.load_plugins()
            self.integrate_plugins()
            print("🔌 Sistema de plugins inicializado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao inicializar plugins: {e}")

    def setup_managers(self):
        """Inicializa os novos gerenciadores"""
        try:
            self.python_version_manager = PythonVersionManager()
            self.theme_manager = ThemeManager()
            self.indentation_checker = IndentationChecker()
            self.language_config = LanguageConfig()
            
            # Gerenciador de cache global
            global module_cache_manager
            module_cache_manager = ModuleCacheManager()
            self.syntax_highlighting_manager = SyntaxHighlightingManager(self)
            
            print("✅ Managers inicializados")
        except Exception as e:
            print(f"❌ Erro ao inicializar managers: {e}")


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
        if editor and hasattr(editor, 'trigger_autocomplete'):
            editor.trigger_autocomplete()

            

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
        try:
            self.lsp_manager = LSPManager(self)
            # Conectar sinais existentes para LSP
            self.tab_widget.currentChanged.connect(self._on_tab_changed_lsp)
            print("✅ Sistema LSP configurado")
        except Exception as e:
            print(f"❌ Erro ao configurar LSP: {e}")
        
    def _on_tab_changed_lsp(self, index):
        """Manipula mudança de aba para LSP"""
        if index >= 0:
            widget = self.tab_widget.widget(index)
            if hasattr(widget, 'editor') and hasattr(widget, 'file_path') and widget.file_path:
                # Atualizar LSP com documento atual
                if self.lsp_manager:
                    content = widget.editor.toPlainText()
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
