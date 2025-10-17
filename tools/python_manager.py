from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
    QLineEdit, QTabWidget, QListWidget, QGroupBox, QCheckBox, 
    QProgressBar, QProgressDialog, QInputDialog, QMessageBox,
    QTextEdit, QPlainTextEdit, QWidget, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QColor, QFont, QFontDatabase

# ===== IMPORTS DO SISTEMA =====
import os
import sys
import re
import glob
import subprocess
import zipfile
import shutil
import platform
from pathlib import Path
import webbrowser


class PythonVersionManager:
    """Gerenciador robusto de versões Python"""
    
    def __init__(self):
        self.installed_versions = []
        self.available_versions = []
        self.current_version = self.get_current_python_version()
        
    def get_current_python_version(self):
        """Obtém a versão Python atual em uso"""
        try:
            version_info = sys.version_info
            return f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        except:
            return "Unknown"
    
    def scan_installed_versions(self):
        """Escaneia versões Python instaladas no sistema"""
        self.installed_versions = []
        
        try:
            # Versão atual
            self.installed_versions.append({
                'path': sys.executable,
                'version': f"Python {self.current_version} (Atual)",
                'type': 'current'
            })
            
            # Busca em locais comuns
            if platform.system() == "Windows":
                self._scan_windows_versions()
            elif platform.system() == "Linux":
                self._scan_linux_versions()
            elif platform.system() == "Darwin":
                self._scan_macos_versions()
                
            return self.installed_versions
            
        except Exception as e:
            print(f"❌ Erro ao escanear versões: {e}")
            return self.installed_versions
    
    def _scan_windows_versions(self):
        """Escaneia versões no Windows"""
        common_paths = [
            "C:\\Python*\\python.exe",
            "C:\\Program Files\\Python*\\python.exe", 
            "C:\\Users\\*\\AppData\\Local\\Programs\\Python\\Python*\\python.exe"
        ]
        
        for pattern in common_paths:
            for python_path in glob.glob(pattern):
                if python_path != sys.executable and os.path.isfile(python_path):
                    version = self._get_python_version(python_path)
                    if version:
                        self.installed_versions.append({
                            'path': python_path,
                            'version': f"Python {version}",
                            'type': 'system'
                        })
    
    def _scan_linux_versions(self):
        """Escaneia versões no Linux"""
        common_commands = ['python', 'python3', 'python3.8', 'python3.9', 
                          'python3.10', 'python3.11', 'python3.12']
        
        for cmd in common_commands:
            try:
                result = subprocess.run(['which', cmd], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    python_path = result.stdout.strip()
                    if python_path and python_path != sys.executable and os.path.exists(python_path):
                        version = self._get_python_version(python_path)
                        if version:
                            self.installed_versions.append({
                                'path': python_path,
                                'version': f"Python {version}",
                                'type': 'system'
                            })
            except:
                continue
    
    def _scan_macos_versions(self):
        """Escaneia versões no macOS"""
        common_paths = [
            '/usr/local/bin/python*',
            '/opt/homebrew/bin/python*',
            '/usr/bin/python*'
        ]
        
        for pattern in common_paths:
            for python_path in glob.glob(pattern):
                if python_path != sys.executable and os.path.isfile(python_path):
                    version = self._get_python_version(python_path)
                    if version:
                        self.installed_versions.append({
                            'path': python_path,
                            'version': f"Python {version}",
                            'type': 'system'
                        })
    
    def _get_python_version(self, python_path):
        """Obtém a versão de um executável Python"""
        try:
            result = subprocess.run(
                [python_path, '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Extrai apenas o número da versão: "Python 3.9.5" -> "3.9.5"
                version_output = result.stdout.strip()
                if version_output.startswith('Python '):
                    return version_output[7:]  # Remove "Python "
                return version_output
        except:
            pass
        return None
    
    def get_available_versions(self):
        """Retorna versões Python disponíveis para download"""
        # Versões estáveis mais recentes
        self.available_versions = [
            {'version': 'Python 3.12.0', 'url': 'https://www.python.org/downloads/release/python-3120/'},
            {'version': 'Python 3.11.6', 'url': 'https://www.python.org/downloads/release/python-3116/'},
            {'version': 'Python 3.10.12', 'url': 'https://www.python.org/downloads/release/python-31012/'},
            {'version': 'Python 3.9.18', 'url': 'https://www.python.org/downloads/release/python-3918/'},
            {'version': 'Python 3.8.18', 'url': 'https://www.python.org/downloads/release/python-3818/'},
        ]
        return self.available_versions
    
    def set_as_default(self, python_path):
        """Define uma versão Python como padrão (apenas no contexto do IDE)"""
        try:
            # Verifica se o caminho é válido
            if os.path.exists(python_path):
                version = self._get_python_version(python_path)
                if version:
                    return {
                        'success': True,
                        'path': python_path,
                        'version': version,
                        'message': f'Python {version} definido como padrão'
                    }
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro: {str(e)}'
            }
        
        return {
            'success': False,
            'message': 'Caminho Python inválido'
        }


class PythonVersionDialog(QDialog):
    """Diálogo principal do gerenciador de versões Python"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = PythonVersionManager()
        self.setup_ui()
        self.apply_styles()
        self.load_versions()
        
    def setup_ui(self):
        """Configura a interface do usuário"""
        self.setWindowTitle("🐍 Gerenciador de Versões Python")
        self.setMinimumSize(800, 600)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Gerenciador de Versões Python")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        
        self.refresh_btn = QPushButton("🔄 Atualizar Lista")
        self.refresh_btn.clicked.connect(self.load_versions)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Widget de abas
        self.tab_widget = QTabWidget()
        
        # Aba de versões instaladas
        self.installed_tab = self.create_installed_tab()
        self.tab_widget.addTab(self.installed_tab, "📦 Versões Instaladas")
        
        # Aba de versões disponíveis
        self.available_tab = self.create_available_tab()
        self.tab_widget.addTab(self.available_tab, "🌐 Versões Disponíveis")
        
        main_layout.addWidget(self.tab_widget)
        
        # Barra de status
        self.status_bar = QLabel(f"Python atual: {self.manager.current_version}")
        self.status_bar.setStyleSheet("background-color: #f8f9fa; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        main_layout.addWidget(self.status_bar)
        
    def create_installed_tab(self):
        """Cria a aba de versões instaladas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # Grupo de versões instaladas
        installed_group = QGroupBox("Versões Python Instaladas no Sistema")
        installed_layout = QVBoxLayout(installed_group)
        
        # Lista de versões instaladas
        self.installed_list = QListWidget()
        self.installed_list.itemSelectionChanged.connect(self.on_installed_selection_changed)
        installed_layout.addWidget(self.installed_list)
        
        # Painel de controles
        controls_layout = QHBoxLayout()
        
        self.set_default_btn = QPushButton("⭐ Definir como Padrão")
        self.set_default_btn.clicked.connect(self.set_default_version)
        self.set_default_btn.setEnabled(False)
        
        self.open_terminal_btn = QPushButton("💻 Abrir Terminal")
        self.open_terminal_btn.clicked.connect(self.open_terminal)
        self.open_terminal_btn.setEnabled(False)
        
        controls_layout.addWidget(self.set_default_btn)
        controls_layout.addWidget(self.open_terminal_btn)
        controls_layout.addStretch()
        
        installed_layout.addLayout(controls_layout)
        layout.addWidget(installed_group)
        
        return tab
        
    def create_available_tab(self):
        """Cria a aba de versões disponíveis"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # Grupo de versões disponíveis
        available_group = QGroupBox("Versões Python Disponíveis para Download")
        available_layout = QVBoxLayout(available_group)
        
        # Lista de versões disponíveis
        self.available_list = QListWidget()
        available_layout.addWidget(self.available_list)
        
        # Botão de download
        self.download_btn = QPushButton("⬇️ Abrir Página de Download")
        self.download_btn.clicked.connect(self.download_version)
        available_layout.addWidget(self.download_btn)
        
        layout.addWidget(available_group)
        
        return tab
        
    def apply_styles(self):
        """Aplica os estilos à interface"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #ecf0f1;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 16px;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
    def load_versions(self):
        """Carrega as versões instaladas e disponíveis"""
        # Versões instaladas
        self.installed_list.clear()
        installed_versions = self.manager.scan_installed_versions()
        
        for version_info in installed_versions:
            item_text = f"{version_info['version']}\nCaminho: {version_info['path']}"
            self.installed_list.addItem(item_text)
            
        # Versões disponíveis
        self.available_list.clear()
        available_versions = self.manager.get_available_versions()
        
        for version_info in available_versions:
            self.available_list.addItem(version_info['version'])
            
        self.update_status("Listas atualizadas com sucesso")
        
    def on_installed_selection_changed(self):
        """Handle selection change in installed versions list"""
        has_selection = len(self.installed_list.selectedItems()) > 0
        self.set_default_btn.setEnabled(has_selection)
        self.open_terminal_btn.setEnabled(has_selection)
        
    def set_default_version(self):
        """Define a versão selecionada como padrão"""
        selected_items = self.installed_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Selecione uma versão Python para definir como padrão")
            return
            
        selected_text = selected_items[0].text()
        # Extrai o caminho do Python do texto do item
        lines = selected_text.split('\n')
        python_path = None
        for line in lines:
            if line.startswith('Caminho: '):
                python_path = line.replace('Caminho: ', '')
                break
        
        if not python_path:
            QMessageBox.warning(self, "Erro", "Não foi possível extrair o caminho do Python")
            return
            
        result = self.manager.set_as_default(python_path)
        
        if result['success']:
            QMessageBox.information(self, "Sucesso", result['message'])
            self.update_status(f"Versão padrão alterada para Python {result['version']}")
        else:
            QMessageBox.warning(self, "Erro", result['message'])
            
    def open_terminal(self):
        """Abre o terminal com a versão selecionada"""
        selected_items = self.installed_list.selectedItems()
        if not selected_items:
            return
            
        selected_text = selected_items[0].text()
        lines = selected_text.split('\n')
        python_path = None
        for line in lines:
            if line.startswith('Caminho: '):
                python_path = line.replace('Caminho: ', '')
                break
        
        if not python_path:
            QMessageBox.warning(self, "Erro", "Não foi possível extrair o caminho do Python")
            return
            
        try:
            if platform.system() == "Windows":
                subprocess.Popen(['cmd', '/k', python_path, '-i'])
            else:
                subprocess.Popen(['x-terminal-emulator', '-e', python_path, '-i'])
                
            self.update_status("Terminal aberto com a versão selecionada")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o terminal: {str(e)}")
            
    def download_version(self):
        """Abre o navegador para download da versão selecionada"""
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Selecione uma versão para download")
            return
            
        version_name = selected_items[0].text()
        available_versions = self.manager.get_available_versions()
        
        version_info = next((v for v in available_versions if v['version'] == version_name), None)
        if version_info:
            webbrowser.open(version_info['url'])
            self.update_status(f"Abrindo página de download: {version_name}")
        else:
            QMessageBox.warning(self, "Erro", "URL de download não encontrada")
            
    def update_status(self, message):
        """Atualiza a barra de status"""
        self.status_bar.setText(f"{message} | Python atual: {self.manager.current_version}")


# Função principal para executar o aplicativo
def main():
    app = QApplication(sys.argv)
    
    # Criar e exibir a janela principal
    dialog = PythonVersionDialog()
    dialog.show()
    
    sys.exit(app.exec())


