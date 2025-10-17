# plugins/plugin_manager_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QGroupBox, QProgressBar, QMessageBox,
    QFileDialog, QSplitter, QTextEdit, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal
import os
import json
import zipfile
import shutil
from pathlib import Path


class PluginInstallThread(QThread):
    """Thread para instalação de plugins em background"""
    progress = Signal(int)
    message = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, plugin_file, plugins_dir):
        super().__init__()
        self.plugin_file = plugin_file
        self.plugins_dir = plugins_dir

    def run(self):
        try:
            self.message.emit("🔍 Verificando arquivo do plugin...")
            
            if self.plugin_file.endswith('.zip'):
                self.install_from_zip()
            elif self.plugin_file.endswith('.py'):
                self.install_from_py()
            else:
                self.finished.emit(False, "Formato de arquivo não suportado")
                
        except Exception as e:
            self.finished.emit(False, f"Erro na instalação: {str(e)}")

    def install_from_zip(self):
        """Instala plugin a partir de arquivo ZIP"""
        self.message.emit("📦 Extraindo arquivo ZIP...")
        
        with zipfile.ZipFile(self.plugin_file, 'r') as zip_ref:
            # Verifica se é um plugin válido
            plugin_files = [f for f in zip_ref.namelist() if f.endswith('Plugin.py')]
            if not plugin_files:
                self.finished.emit(False, "Nenhum arquivo Plugin.py encontrado no ZIP")
                return
            
            # Extrai para diretório temporário primeiro
            temp_dir = Path(self.plugins_dir) / "temp_install"
            temp_dir.mkdir(exist_ok=True)
            
            zip_ref.extractall(temp_dir)
            
            # Move arquivos .py para o diretório de plugins
            for file_path in temp_dir.rglob("*.py"):
                if file_path.name.endswith('Plugin.py'):
                    dest_path = Path(self.plugins_dir) / file_path.name
                    shutil.move(str(file_path), str(dest_path))
                    self.message.emit(f"✅ Instalado: {file_path.name}")
            
            # Limpa diretório temporário
            shutil.rmtree(temp_dir)
            
        self.finished.emit(True, "Plugin instalado com sucesso!")

    def install_from_py(self):
        """Instala plugin a partir de arquivo .py"""
        plugin_name = os.path.basename(self.plugin_file)
        dest_path = Path(self.plugins_dir) / plugin_name
        
        if dest_path.exists():
            self.finished.emit(False, f"Plugin {plugin_name} já existe")
            return
        
        shutil.copy2(self.plugin_file, dest_path)
        self.finished.emit(True, f"Plugin {plugin_name} instalado com sucesso!")


class PluginManagerDialog(QDialog):
    def __init__(self, ide_instance, parent=None):
        super().__init__(parent)
        self.ide = ide_instance
        self.plugin_manager = ide_instance.plugin_manager
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("🔌 Gerenciador de Plugins")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        title_label = QLabel("Gerenciador de Plugins")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #569cd6;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.clicked.connect(self.refresh_plugins)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Lista de plugins
        self.setup_plugins_list(splitter)
        
        # Detalhes do plugin
        self.setup_plugin_details(splitter)
        
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Botões de ação
        self.setup_action_buttons(layout)
        
    def setup_plugins_list(self, parent):
        """Configura a lista de plugins"""
        plugins_group = QGroupBox("Plugins Instalados")
        layout = QVBoxLayout(plugins_group)
        
        self.plugins_list = QListWidget()
        self.plugins_list.itemSelectionChanged.connect(self.on_plugin_selected)
        layout.addWidget(self.plugins_list)
        
        parent.addWidget(plugins_group)
        self.update_plugins_list()
        
    def setup_plugin_details(self, parent):
        """Configura os detalhes do plugin selecionado"""
        details_group = QGroupBox("Detalhes do Plugin")
        layout = QVBoxLayout(details_group)
        
        # Abas para diferentes informações
        self.tabs = QTabWidget()
        
        # Informações básicas
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.tabs.addTab(self.info_text, "📋 Informações")
        
        # Configurações (se houver)
        self.settings_text = QTextEdit()
        self.settings_text.setReadOnly(True)
        self.tabs.addTab(self.settings_text, "⚙️ Configurações")
        
        layout.addWidget(self.tabs)
        parent.addWidget(details_group)
        
    def setup_action_buttons(self, parent):
        """Configura os botões de ação"""
        button_layout = QHBoxLayout()
        
        # Instalar
        self.install_btn = QPushButton("📥 Instalar Plugin")
        self.install_btn.clicked.connect(self.install_plugin)
        button_layout.addWidget(self.install_btn)
        
        # Exportar
        self.export_btn = QPushButton("📤 Exportar Plugin")
        self.export_btn.clicked.connect(self.export_plugin)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        # Desinstalar
        self.uninstall_btn = QPushButton("🗑️ Desinstalar")
        self.uninstall_btn.clicked.connect(self.uninstall_plugin)
        self.uninstall_btn.setEnabled(False)
        button_layout.addWidget(self.uninstall_btn)
        
        # Recarregar
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.reload_btn.clicked.connect(self.reload_plugin)
        self.reload_btn.setEnabled(False)
        button_layout.addWidget(self.reload_btn)
        
        button_layout.addStretch()
        
        # Fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        parent.addLayout(button_layout)
        
    def update_plugins_list(self):
        """Atualiza a lista de plugins"""
        self.plugins_list.clear()
        
        if not self.plugin_manager:
            return
            
        for plugin_info in self.plugin_manager.get_plugins_info():
            status_icon = "✅" if plugin_info.status == PluginStatus.LOADED else "❌"
            item_text = f"{status_icon} {plugin_info.name}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, {
                'name': plugin_info.name,
                'status': plugin_info.status,
                'info': plugin_info
            })
            
            # Cor baseada no status
            if plugin_info.status == PluginStatus.LOADED:
                item.setForeground(Qt.darkGreen)
            elif plugin_info.status == PluginStatus.ERROR:
                item.setForeground(Qt.red)
            else:
                item.setForeground(Qt.gray)
                
            self.plugins_list.addItem(item)
            
    def on_plugin_selected(self):
        """Quando um plugin é selecionado na lista"""
        current_item = self.plugins_list.currentItem()
        if not current_item:
            return
            
        plugin_data = current_item.data(Qt.UserRole)
        plugin_info = plugin_data['info']
        
        # Atualizar detalhes
        self.update_plugin_details(plugin_info)
        
        # Habilitar/desabilitar botões
        self.export_btn.setEnabled(True)
        self.uninstall_btn.setEnabled(True)
        self.reload_btn.setEnabled(True)
        
    def update_plugin_details(self, plugin_info):
        """Atualiza os detalhes do plugin selecionado"""
        # Informações básicas
        info_html = f"""
        <h3>{plugin_info.name}</h3>
        <p><b>Versão:</b> {plugin_info.version}</p>
        <p><b>Descrição:</b> {plugin_info.description}</p>
        <p><b>Autor:</b> {plugin_info.author}</p>
        <p><b>Tipo:</b> {plugin_info.plugin_type.value}</p>
        <p><b>Status:</b> {plugin_info.status.value}</p>
        """
        
        if plugin_info.error_message:
            info_html += f'<p><b style="color: red;">Erro:</b> {plugin_info.error_message}</p>'
            
        self.info_text.setHtml(info_html)
        
    def install_plugin(self):
        """Instala um novo plugin"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Selecionar Plugin")
        file_dialog.setNameFilter(
            "Arquivos de Plugin (*.py *.zip);;"
            "Script Python (*.py);;"
            "Pacote ZIP (*.zip)"
        )
        
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            if files:
                self.start_plugin_installation(files[0])
                
    def start_plugin_installation(self, plugin_file):
        """Inicia a instalação do plugin em uma thread separada"""
        self.progress_bar.setVisible(True)
        self.install_btn.setEnabled(False)
        
        self.install_thread = PluginInstallThread(
            plugin_file, 
            self.plugin_manager.plugins_dir
        )
        self.install_thread.message.connect(self.on_install_message)
        self.install_thread.finished.connect(self.on_install_finished)
        self.install_thread.start()
        
    def on_install_message(self, message):
        """Atualiza mensagem de progresso"""
        self.progress_bar.setFormat(message)
        
    def on_install_finished(self, success, message):
        """Finaliza a instalação"""
        self.progress_bar.setVisible(False)
        self.install_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Sucesso", message)
            # Recarrega plugins
            self.plugin_manager.auto_load_plugins()
            self.ide.integrate_plugins_with_existing_ui()
            self.update_plugins_list()
        else:
            QMessageBox.warning(self, "Erro", message)
            
    def export_plugin(self):
        """Exporta o plugin selecionado"""
        current_item = self.plugins_list.currentItem()
        if not current_item:
            return
            
        plugin_data = current_item.data(Qt.UserRole)
        plugin_name = plugin_data['name']
        
        # Encontra o arquivo do plugin
        plugin_file = self.plugin_manager.plugins_dir / f"{plugin_name}.py"
        if not plugin_file.exists():
            QMessageBox.warning(self, "Erro", f"Arquivo do plugin {plugin_name}.py não encontrado")
            return
            
        # Diálogo para salvar
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Plugin",
            f"{plugin_name}.py",
            "Script Python (*.py)"
        )
        
        if file_path:
            try:
                shutil.copy2(plugin_file, file_path)
                QMessageBox.information(self, "Sucesso", f"Plugin {plugin_name} exportado com sucesso!")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao exportar plugin: {str(e)}")
                
    def uninstall_plugin(self):
        """Desinstala o plugin selecionado"""
        current_item = self.plugins_list.currentItem()
        if not current_item:
            return
            
        plugin_data = current_item.data(Qt.UserRole)
        plugin_name = plugin_data['name']
        
        reply = QMessageBox.question(
            self,
            "Confirmar Desinstalação",
            f"Tem certeza que deseja desinstalar o plugin '{plugin_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Remove do plugin manager
                self.plugin_manager.unload_plugin(plugin_name)
                
                # Remove arquivo
                plugin_file = self.plugin_manager.plugins_dir / f"{plugin_name}.py"
                if plugin_file.exists():
                    plugin_file.unlink()
                
                # Atualiza UI
                self.ide.integrate_plugins_with_existing_ui()
                self.update_plugins_list()
                self.info_text.clear()
                
                QMessageBox.information(self, "Sucesso", f"Plugin {plugin_name} desinstalado com sucesso!")
                
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao desinstalar plugin: {str(e)}")
                
    def reload_plugin(self):
        """Recarrega o plugin selecionado"""
        current_item = self.plugins_list.currentItem()
        if not current_item:
            return
            
        plugin_data = current_item.data(Qt.UserRole)
        plugin_name = plugin_data['name']
        
        try:
            success = self.plugin_manager.reload_plugin(plugin_name)
            if success:
                self.ide.integrate_plugins_with_existing_ui()
                self.update_plugins_list()
                QMessageBox.information(self, "Sucesso", f"Plugin {plugin_name} recarregado com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", f"Erro ao recarregar plugin {plugin_name}")
                
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao recarregar plugin: {str(e)}")
            
    def refresh_plugins(self):
        """Atualiza a lista de plugins"""
        self.plugin_manager.auto_load_plugins()
        self.ide.integrate_plugins_with_existing_ui()
        self.update_plugins_list()
        QMessageBox.information(self, "Atualizado", "Plugins recarregados com sucesso!")