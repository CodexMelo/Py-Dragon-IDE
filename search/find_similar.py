from PySide6.QtWidgets import QDialog, QLineEdit, QListWidget
from PySide6.QtCore import QRegularExpression


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
