
from PySide6.QtWidgets import QDialog, QComboBox, QLineEdit
from core.plugin_system import PluginBase


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
