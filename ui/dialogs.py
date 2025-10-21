# ===== IMPORTS DO PYSIDE6 =====
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
    QLineEdit, QTabWidget, QListWidget, QGroupBox, QCheckBox, 
    QProgressBar, QProgressDialog, QInputDialog, QMessageBox,
    QTextEdit, QPlainTextEdit, QWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QColor, QFont, QFontDatabase, QTextCharFormat

# ===== IMPORTS DO SISTEMA =====
import os
import sys
import re
import subprocess
import zipfile
import shutil
import json  # ADICIONADO

# ✅ IMPORTE CORRETO DO VERSION MANAGER
try:
    from ide.core.version_manager import PythonVersionManager
    VERSION_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Version manager não disponível: {e}")
    VERSION_MANAGER_AVAILABLE = False
    
    
    
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



class PythonVersionDialog(QDialog):
    def __init__(self, parent=None, version_manager=None):
        super().__init__(parent)
        
        # ✅ INICIALIZAÇÃO CORRETA DO VERSION MANAGER
        if version_manager is not None:
            self.version_manager = version_manager
        elif VERSION_MANAGER_AVAILABLE:
            try:
                self.version_manager = PythonVersionManager()
            except Exception as e:
                print(f"❌ Erro ao criar version manager: {e}")
                self.version_manager = None
        else:
            self.version_manager = None
            
        self.setup_ui()
        
        # ✅ CARREGA AS VERSÕES SE O MANAGER ESTIVER DISPONÍVEL
        if self.version_manager:
            self.refresh_installed_versions()

    def setup_ui(self):
        """Configura a interface do diálogo"""
        self.setWindowTitle("🐍 Gerenciador de Versões Python")
        self.setFixedSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # ✅ VERIFICA SE O VERSION MANAGER ESTÁ DISPONÍVEL
        if not self.version_manager:
            self.setup_fallback_ui()
            return
            
        # Título
        title = QLabel("Gerenciador de Versões Python")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E86AB;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Abas
        self.tab_widget = QTabWidget()
        
        # Aba de versões instaladas
        self.installed_tab = QWidget()
        self.setup_installed_tab()
        self.tab_widget.addTab(self.installed_tab, "📁 Versões Instaladas")
        
        # Aba de versões disponíveis
        self.available_tab = QWidget()
        self.setup_available_tab()
        self.tab_widget.addTab(self.available_tab, "🌐 Versões Disponíveis")
        
        layout.addWidget(self.tab_widget)
        
        # Botões
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.clicked.connect(self.refresh_installed_versions)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

    def setup_installed_tab(self):
        """Configura a aba de versões instaladas"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Versões Python Instaladas no Sistema")
        title.setStyleSheet("font-weight: bold; color: #2E86AB;")
        layout.addWidget(title)
        
        # Lista de versões
        self.installed_versions_list = QListWidget()
        self.installed_versions_list.itemDoubleClicked.connect(self.on_version_selected)
        layout.addWidget(self.installed_versions_list)
        
        # Informações da versão selecionada
        self.version_info = QLabel("Selecione uma versão para ver detalhes")
        self.version_info.setWordWrap(True)
        self.version_info.setStyleSheet(
            "background-color: #F8F9FA; padding: 10px; border: 1px solid #DEE2E6; border-radius: 5px;"
        )
        layout.addWidget(self.version_info)
        
        # Botão para definir como padrão
        self.set_default_btn = QPushButton("⭐ Definir como Padrão")
        self.set_default_btn.clicked.connect(self.set_default_version)
        self.set_default_btn.setEnabled(False)
        layout.addWidget(self.set_default_btn)
        
        self.installed_tab.setLayout(layout)

    def setup_available_tab(self):
        """Configura a aba de versões disponíveis"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Versões Python Disponíveis para Download")
        title.setStyleSheet("font-weight: bold; color: #2E86AB;")
        layout.addWidget(title)
        
        # Lista de versões disponíveis
        self.available_versions_list = QListWidget()
        layout.addWidget(self.available_versions_list)
        
        # Informações
        info_label = QLabel(
            "Para instalar uma nova versão do Python, visite:\n"
            "https://www.python.org/downloads/\n\n"
            "Versões estáveis mais recentes:"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Carrega versões disponíveis
        self.load_available_versions()
        
        self.available_tab.setLayout(layout)

    def setup_fallback_ui(self):
        """Interface quando o gerenciador não está disponível"""
        layout = QVBoxLayout()
        
        title = QLabel("🐍 Gerenciador de Versões Python")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Widget de erro
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        
        error_icon = QLabel("⚠️")
        error_icon.setStyleSheet("font-size: 48px;")
        error_icon.setAlignment(Qt.AlignCenter)
        error_layout.addWidget(error_icon)
        
        error_msg = QLabel("Gerenciador de versões não disponível")
        error_msg.setStyleSheet("color: #DC3545; font-size: 16px; font-weight: bold;")
        error_msg.setAlignment(Qt.AlignCenter)
        error_layout.addWidget(error_msg)
        
        info_msg = QLabel(
            "O sistema de gerenciamento de versões Python não pôde ser carregado.\n\n"
            "Isso é normal em ambientes virtuais ou instalações limitadas.\n\n"
            "Você pode:\n"
            "• Usar a versão Python atual: " + sys.executable + "\n"
            "• Instalar novas versões manualmente em python.org"
        )
        info_msg.setWordWrap(True)
        info_msg.setAlignment(Qt.AlignCenter)
        error_layout.addWidget(info_msg)
        
        layout.addWidget(error_widget)
        
        # Botão para fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

    def refresh_installed_versions(self):
        """Atualiza a lista de versões instaladas"""
        if not self.version_manager:
            return
            
        try:
            self.installed_versions_list.clear()
            
            versions = self.version_manager.scan_installed_versions()
            
            if not versions:
                self.installed_versions_list.addItem("Nenhuma versão Python encontrada")
                return
                
            for version_info in versions:
                item_text = f"{version_info['version']}\n{version_info['path']}"
                item = QListWidgetItem(item_text)
                
                # Destaque para versão atual
                if version_info.get('type') == 'current':
                    item.setBackground(Qt.green)
                    item.setForeground(Qt.white)
                    item_text = f"⭐ {item_text} (Atual)"
                    item.setText(item_text)
                
                self.installed_versions_list.addItem(item)
                
        except Exception as e:
            self.installed_versions_list.addItem(f"Erro ao carregar versões: {str(e)}")

    def load_available_versions(self):
        """Carrega a lista de versões disponíveis"""
        if not self.version_manager:
            return
            
        try:
            self.available_versions_list.clear()
            
            versions = self.version_manager.get_available_versions()
            
            for version_info in versions:
                item_text = f"{version_info['version']}\n{version_info['url']}"
                item = QListWidgetItem(item_text)
                self.available_versions_list.addItem(item)
                
        except Exception as e:
            self.available_versions_list.addItem(f"Erro ao carregar versões disponíveis: {str(e)}")

    def on_version_selected(self, item):
        """Quando uma versão é selecionada"""
        if not self.version_manager:
            return
            
        try:
            text = item.text()
            # Extrai o caminho do texto (última linha)
            lines = text.split('\n')
            python_path = lines[-1] if len(lines) > 1 else text
            
            # Atualiza informações
            version = self.version_manager._get_python_version(python_path)
            if version:
                info_text = f"""
                <b>Python {version}</b><br>
                <b>Caminho:</b> {python_path}<br>
                <b>Tipo:</b> {'Versão Atual' if '⭐' in text else 'Sistema'}
                """
                self.version_info.setText(info_text)
                self.set_default_btn.setEnabled(True)
                
        except Exception as e:
            self.version_info.setText(f"Erro ao obter informações: {str(e)}")

    def set_default_version(self):
        """Define a versão selecionada como padrão"""
        if not self.version_manager:
            return
            
        try:
            current_item = self.installed_versions_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Aviso", "Selecione uma versão primeiro!")
                return
                
            text = current_item.text()
            lines = text.split('\n')
            python_path = lines[-1] if len(lines) > 1 else text
            
            result = self.version_manager.set_as_default(python_path)
            
            if result['success']:
                QMessageBox.information(self, "Sucesso", result['message'])
                self.refresh_installed_versions()
            else:
                QMessageBox.warning(self, "Aviso", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao definir versão padrão: {str(e)}")


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


