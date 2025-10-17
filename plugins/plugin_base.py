import os
import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

class PluginStatus(Enum):
    LOADED = "loaded"
    ERROR = "error"
    DISABLED = "disabled"
    UNLOADED = "unloaded"

class PluginType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    THEME = "theme"
    LANGUAGE = "language"
    TOOL = "tool"

@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    status: PluginStatus = PluginStatus.UNLOADED
    dependencies: List[str] = None
    error_message: str = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class BasePlugin(ABC):
    """Classe base para todos os plugins do Py Dragon Studio com injeção completa"""
    
    def __init__(self):
        self.plugin_info = PluginInfo(
            name=self.__class__.__name__,
            version="1.0.0",
            description="Plugin base",
            author="Unknown",
            plugin_type=PluginType.INTERNAL,
            status=PluginStatus.UNLOADED
        )
        self.ide_instance = None
        self.actions = []
        
        # Injeção dinâmica de atributos do IDE
        self._injected_attributes = []
    
    @abstractmethod
    def initialize(self) -> bool:
        """Inicializa o plugin"""
        pass
    
    def shutdown(self) -> bool:
        """Finaliza o plugin"""
        self.plugin_info.status = PluginStatus.UNLOADED
        return True
    
    def get_actions(self):
        """Retorna ações QAction para menus/toolbars"""
        return self.actions
    
    def create_action(self, text, callback, shortcut=None, tooltip=None):
        """Cria uma ação QAction de forma segura"""
        try:
            from PySide6.QtGui import QAction, QKeySequence
            
            action = QAction(text, self.ide_instance)
            action.triggered.connect(callback)
            
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            if tooltip:
                action.setToolTip(tooltip)
                
            return action
        except ImportError as e:
            print(f"❌ Erro ao criar ação: {e}")
            return None
    
    def set_ide_instance(self, ide_instance):
        """Define a instância do IDE principal e injeta todos os atributos"""
        self.ide_instance = ide_instance
        self._inject_ide_attributes(ide_instance)
    
    def _inject_ide_attributes(self, ide_instance):
        """Injeta dinamicamente todos os atributos públicos do IDE no plugin"""
        try:
            # Lista de atributos para injetar
            attributes_to_inject = [
                # Componentes de UI
                'tab_widget', 'file_tree', 'file_model', 'problems_list',
                'output_tabs', 'terminal_text', 'output_text', 'debug_text',
                'errors_text', 'lint_text', 'minimap_widget',
                
                # Labels de status
                'file_info_label', 'cursor_info_label', 'project_info_label', 
                'scope_info_label', 'status_progress',
                
                # Gerenciadores
                'python_version_manager', 'theme_manager', 'indentation_checker',
                'language_config', 'language_syntax_manager', 'lsp_manager',
                'syntax_highlighting_manager', 'plugin_manager',
                
                # Estado da aplicação
                'project_path', 'venv_path', 'python_path', 'current_file',
                'current_font', 'current_class', 'current_function',
                'debug_mode', 'current_debug_file',
                
                # Processos
                'shell_process', 'debug_process', 'current_process',
                
                # Métodos públicos importantes
                'get_current_editor', 'open_file', 'save_file', 'save_file_as',
                'save_all_files', 'run_code', 'debug_code', 'new_file',
                'set_project', 'refresh_explorer', 'show_find_dialog',
                'show_replace_dialog', 'toggle_terminal', 'toggle_explorer',
                'toggle_minimap', 'zoom_in', 'zoom_out', 'zoom_reset',
                'show_font_dialog', 'update_file_info', 'update_cursor_info',
                'navigate_to_line', 'create_new_file_in_explorer',
                'create_new_folder_in_explorer', 'copy_file_path',
                'delete_file', 'delete_folder', 'clear_problems',
                'run_linter', 'activate_project', 'get_python_executable',
                'check_python_version', 'format_code', 'show_settings',
                'show_documentation', 'show_about', 'next_tab', 'previous_tab',
                'show_command_palette', 'pause_execution', 'stop_execution',
                'run_tests', 'run_coverage', 'install_package',
                
                # Sistema de logging
                'debug_log', 'statusBar'
            ]
            
            # Injeta atributos existentes
            for attr_name in attributes_to_inject:
                if hasattr(ide_instance, attr_name):
                    setattr(self, attr_name, getattr(ide_instance, attr_name))
                    self._injected_attributes.append(attr_name)
            
            # Injeta módulos Qt dinamicamente
            self._inject_qt_modules()
            
            print(f"✅ Plugin {self.plugin_info.name}: {len(self._injected_attributes)} atributos injetados")
            
        except Exception as e:
            print(f"❌ Erro na injeção de atributos: {e}")
    
    def _inject_qt_modules(self):
        """Injeta módulos Qt no plugin"""
        try:
            # Injeta módulos Qt principais
            import PySide6
            self.Qt = PySide6.QtCore.Qt
            self.QTimer = PySide6.QtCore.QTimer
            self.Signal = PySide6.QtCore.Signal
            self.QThread = PySide6.QtCore.QThread
            self.QProcess = PySide6.QtCore.QProcess
            
            # Injeta módulos GUI
            self.QAction = PySide6.QtGui.QAction
            self.QKeySequence = PySide6.QtGui.QKeySequence
            self.QColor = PySide6.QtGui.QColor
            self.QPalette = PySide6.QtGui.QPalette
            self.QFont = PySide6.QtGui.QFont
            self.QTextCursor = PySide6.QtGui.QTextCursor
            self.QTextDocument = PySide6.QtGui.QTextDocument
            
            # Injeta módulos Widgets
            self.QMainWindow = PySide6.QtWidgets.QMainWindow
            self.QWidget = PySide6.QtWidgets.QWidget
            self.QVBoxLayout = PySide6.QtWidgets.QVBoxLayout
            self.QHBoxLayout = PySide6.QtWidgets.QHBoxLayout
            self.QTabWidget = PySide6.QtWidgets.QTabWidget
            self.QTextEdit = PySide6.QtWidgets.QTextEdit
            self.QPlainTextEdit = PySide6.QtWidgets.QPlainTextEdit
            self.QTreeWidget = PySide6.QtWidgets.QTreeWidget
            self.QListWidget = PySide6.QtWidgets.QListWidget
            self.QSplitter = PySide6.QtWidgets.QSplitter
            self.QStatusBar = PySide6.QtWidgets.QStatusBar
            self.QToolBar = PySide6.QtWidgets.QToolBar
            self.QMenuBar = PySide6.QtWidgets.QMenuBar
            self.QMenu = PySide6.QtWidgets.QMenu
            self.QFileDialog = PySide6.QtWidgets.QFileDialog
            self.QMessageBox = PySide6.QtWidgets.QMessageBox
            self.QDockWidget = PySide6.QtWidgets.QDockWidget
            self.QLabel = PySide6.QtWidgets.QLabel
            self.QInputDialog = PySide6.QtWidgets.QInputDialog
            self.QPushButton = PySide6.QtWidgets.QPushButton
            self.QFileSystemModel = PySide6.QtWidgets.QFileSystemModel
            self.QTreeView = PySide6.QtWidgets.QTreeView
            self.QProgressDialog = PySide6.QtWidgets.QProgressDialog
            self.QGroupBox = PySide6.QtWidgets.QGroupBox
            self.QShortcut = PySide6.QtWidgets.QShortcut
            
            self._injected_attributes.extend([
                'Qt', 'QTimer', 'Signal', 'QThread', 'QProcess',
                'QAction', 'QKeySequence', 'QColor', 'QPalette', 'QFont',
                'QTextCursor', 'QTextDocument', 'QMainWindow', 'QWidget',
                'QVBoxLayout', 'QHBoxLayout', 'QTabWidget', 'QTextEdit',
                'QPlainTextEdit', 'QTreeWidget', 'QListWidget', 'QSplitter',
                'QStatusBar', 'QToolBar', 'QMenuBar', 'QMenu', 'QFileDialog',
                'QMessageBox', 'QDockWidget', 'QLabel', 'QInputDialog',
                'QPushButton', 'QFileSystemModel', 'QTreeView', 
                'QProgressDialog', 'QGroupBox', 'QShortcut'
            ])
            
        except Exception as e:
            print(f"❌ Erro ao injetar módulos Qt: {e}")
    
    def call_ide_method(self, method_name, *args, **kwargs):
        """Chama um método do IDE de forma segura"""
        try:
            if hasattr(self.ide_instance, method_name):
                method = getattr(self.ide_instance, method_name)
                return method(*args, **kwargs)
            else:
                print(f"❌ Método {method_name} não encontrado no IDE")
                return None
        except Exception as e:
            print(f"❌ Erro ao chamar {method_name}: {e}")
            return None
    
    def show_message(self, message, duration=3000):
        """Mostra mensagem na statusbar do IDE"""
        try:
            if hasattr(self, 'statusBar') and self.statusBar:
                self.statusBar().showMessage(message, duration)
            elif hasattr(self, 'debug_log'):
                self.debug_log(message, "INFO")
            else:
                print(f"📢 {message}")
        except Exception as e:
            print(f"❌ Erro ao mostrar mensagem: {e}")
    
    def get_current_editor_safe(self):
        """Obtém o editor atual de forma segura"""
        try:
            if hasattr(self, 'get_current_editor'):
                return self.get_current_editor()
            elif hasattr(self, 'tab_widget') and self.tab_widget:
                current_widget = self.tab_widget.currentWidget()
                if current_widget and hasattr(current_widget, 'editor'):
                    return current_widget.editor
            return None
        except Exception as e:
            print(f"❌ Erro ao obter editor atual: {e}")
            return None
    
    def get_project_path_safe(self):
        """Obtém o caminho do projeto de forma segura"""
        try:
            if hasattr(self, 'project_path') and self.project_path:
                return self.project_path
            elif hasattr(self, 'ide_instance') and self.ide_instance:
                return getattr(self.ide_instance, 'project_path', None)
            return None
        except Exception as e:
            print(f"❌ Erro ao obter projeto: {e}")
            return None
    
    def create_editor_tab(self, file_path=None, content=""):
        """Cria uma nova aba de editor de forma segura"""
        try:
            if hasattr(self, 'open_file') and file_path:
                return self.open_file(file_path)
            else:
                # Fallback: cria editor básico
                from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget
                
                editor = QPlainTextEdit()
                editor.setPlainText(content)
                
                tab_widget = QWidget()
                layout = QVBoxLayout(tab_widget)
                layout.addWidget(editor)
                
                if hasattr(self, 'tab_widget') and self.tab_widget:
                    index = self.tab_widget.addTab(tab_widget, "Novo Arquivo")
                    self.tab_widget.setCurrentIndex(index)
                    return editor
                
                return editor
        except Exception as e:
            print(f"❌ Erro ao criar editor: {e}")
            return None
    
    # Métodos de hook para eventos do IDE
    def on_editor_created(self, editor):
        """Chamado quando um novo editor é criado"""
        pass
    
    def on_file_saved(self, file_path: str):
        """Chamado quando um arquivo é salvo"""
        pass
    
    def on_project_loaded(self, project_path: str):
        """Chamado quando um projeto é carregado"""
        pass
    
    def on_tab_changed(self, index):
        """Chamado quando a aba é alterada"""
        pass
    
    def on_text_modified(self):
        """Chamado quando o texto é modificado"""
        pass
    
    def on_cursor_position_changed(self):
        """Chamado quando a posição do cursor muda"""
        pass
    
    def get_injected_attributes(self):
        """Retorna lista de atributos injetados"""
        return self._injected_attributes.copy()
