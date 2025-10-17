from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QComboBox, QLineEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

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

