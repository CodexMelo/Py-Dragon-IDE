from PySide6.QtWidgets import QDialog, QListWidget
from PySide6.QtCore import QThread, Signal
import subprocess



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
            
