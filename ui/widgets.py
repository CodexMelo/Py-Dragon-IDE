from PySide6.QtWidgets import (QWidget, QTreeWidget, QListWidget, 
                              QPlainTextEdit, QProgressBar)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor

class OutlineWidget(QWidget):
    """Widget que mostra a estrutura do código (classes e funções) igual ao VS Code"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ide = parent
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        self.refresh_btn = QAction("🔄", self)
        self.refresh_btn.setToolTip("Atualizar outline")
        self.refresh_btn.triggered.connect(self.refresh_outline)
        
        self.collapse_btn = QAction("📁", self)
        self.collapse_btn.setToolTip("Recolher tudo")
        self.collapse_btn.triggered.connect(self.collapse_all)
        
        self.expand_btn = QAction("📂", self)
        self.expand_btn.setToolTip("Expandir tudo")
        self.expand_btn.triggered.connect(self.expand_all)
        
        toolbar.addAction(self.refresh_btn)
        toolbar.addAction(self.collapse_btn)
        toolbar.addAction(self.expand_btn)
        
        layout.addWidget(toolbar)
        
        # Tree widget para mostrar a estrutura
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(12)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Estilo do tree widget
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px 2px;
                border: 1px solid transparent;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)
        
        layout.addWidget(self.tree_widget)
        
    def refresh_outline(self):
        """Atualiza o outline baseado no editor atual"""
        editor = self.ide.get_current_editor()
        if not editor:
            self.tree_widget.clear()
            return
            
        content = editor.toPlainText()
        self.parse_content(content)
        
    def parse_content(self, content):
        """Analisa o conteúdo e extrai classes e funções de forma mais robusta"""
        self.tree_widget.clear()
        
        try:
            lines = content.split('\n')
            current_class = None
            class_item = None
            current_indent = 0
            
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                    
                # Calcula indentação atual
                indent = len(line) - len(line.lstrip())
                
                # Detecta classes
                class_match = re.match(r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped_line)
                if class_match:
                    class_name = class_match.group(1)
                    current_class = class_name
                    class_item = QTreeWidgetItem(self.tree_widget)
                    class_item.setText(0, f"📦 {class_name}")
                    class_item.setData(0, Qt.UserRole, {"type": "class", "line": line_num})
                    class_item.setExpanded(True)
                    current_indent = indent
                    continue
                
                # Detecta funções (apenas no nível correto de indentação)
                func_match = re.match(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped_line)
                if func_match:
                    func_name = func_match.group(1)
                    
                    if current_class and indent > current_indent:
                        # Método dentro de classe
                        func_item = QTreeWidgetItem(class_item)
                        func_item.setText(0, f"🔧 {func_name}()")
                        func_item.setData(0, Qt.UserRole, {"type": "method", "line": line_num, "class": current_class})
                    else:
                        # Função global
                        func_item = QTreeWidgetItem(self.tree_widget)
                        func_item.setText(0, f"📋 {func_name}()")
                        func_item.setData(0, Qt.UserRole, {"type": "function", "line": line_num})
                        current_class = None  # Reset da classe atual
                        
        except Exception as e:
            print(f"Erro ao analisar outline: {e}")
            
    def on_item_double_clicked(self, item, column):
        """Navega para a linha quando um item é clicado"""
        data = item.data(0, Qt.UserRole)
        if data and 'line' in data:
            self.ide.navigate_to_line(data['line'])
            
    def collapse_all(self):
        """Recolhe todos os itens"""
        self.tree_widget.collapseAll()
        
    def expand_all(self):
        """Expande todos os itens"""
        self.tree_widget.expandAll()

# ===== SISTEMA DE AUTOCOMPLETE FLUTUANTE =====
class ScopeHeaderWidget(QWidget):
    """Widget que mostra o escopo atual (classe/função)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_class = "Global"
        self.current_function = "Nenhuma"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.scope_label = QLabel()
        self.scope_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                color: #9cdcfe;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        
        layout.addWidget(self.scope_label)
        self.setLayout(layout)
        self.update_display()
        
    def update_scope(self, current_class, current_function):
        """Atualiza o escopo atual"""
        self.current_class = current_class
        self.current_function = current_function
        self.update_display()
        
    def update_display(self):
        """Atualiza o display do escopo"""
        text_parts = []
        if self.current_class != "Global":
            text_parts.append(f"📦 {self.current_class}")
        if self.current_function != "Nenhuma":
            text_parts.append(f"📋 {self.current_function}")
            
        if text_parts:
            self.scope_label.setText(" → ".join(text_parts))
        else:
            self.scope_label.setText("🌍 Global")
            
    def show_scope(self):
        """Mostra o widget de escopo"""
        self.show()
        
    def hide_scope(self):
        """Esconde o widget de escopo"""
        self.hide()

        

class ScopeIndicatorWidget(QWidget):
    """Widget que mostra a classe/função atual como no VS Code"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_class = "Global"
        self.current_function = "Nenhuma"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.scope_label = QLabel()
        self.scope_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                color: #9cdcfe;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        
        layout.addWidget(self.scope_label)
        self.setLayout(layout)
        self.update_display()
        
    def update_scope(self, current_class, current_function):
        """Atualiza o escopo atual"""
        self.current_class = current_class
        self.current_function = current_function
        self.update_display()
        
    def update_display(self):
        """Atualiza o display do escopo"""
        text_parts = []
        if self.current_class != "Global":
            text_parts.append(f"📦 {self.current_class}")
        if self.current_function != "Nenhuma":
            text_parts.append(f"📋 {self.current_function}")
            
        if text_parts:
            self.scope_label.setText(" → ".join(text_parts))
        else:
            self.scope_label.setText("🌍 Global")




class Minimap(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_editor = None
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setFrameShape(QFrame.NoFrame)
        
        # Configuração de fonte muito pequena para o minimap
        self.setFont(QFont("Monospace", 2))
        self.setWordWrapMode(QTextOption.NoWrap)
        
        # Cores do minimap (tema escuro)
        self.setStyleSheet("""
            Minimap {
                background-color: #1e1e1e;
                color: #858585;
                border: none;
                border-left: 1px solid #2d2d30;
            }
        """)
        
        # Área de visão atual (retângulo que mostra a região visível)
        self.viewport_rect = QRect()
        self.viewport_rect_color = QColor(100, 100, 100, 100)
        
        # Conectar eventos
        self.verticalScrollBar().valueChanged.connect(self.update_viewport_position)
        
    def set_main_editor(self, editor):
        """Define o editor principal que o minimap irá espelhar"""
        self.main_editor = editor
        if self.main_editor:
            # Conectar sinais do editor principal
            self.main_editor.verticalScrollBar().valueChanged.connect(self.update_from_main_editor)
            self.main_editor.textChanged.connect(self.update_minimap_content)
            
            # Atualizar conteúdo inicial
            self.update_minimap_content()
            
    def update_minimap_content(self):
        """Atualiza o conteúdo do minimap baseado no editor principal"""
        if not self.main_editor:
            return
            
        # Obter texto do editor principal
        main_text = self.main_editor.toPlainText()
        
        # Processar texto para o minimap (reduzir linhas muito longas)
        processed_lines = []
        lines = main_text.split('\n')
        
        for line in lines:
            if len(line) > 150:  # Limitar linhas muito longas
                processed_line = line[:147] + "..."
            else:
                processed_line = line
            processed_lines.append(processed_line)
            
        self.setPlainText('\n'.join(processed_lines))
        
        # Atualizar a posição do viewport
        self.update_viewport_position()
        
    def update_from_main_editor(self):
        """Atualiza o minimap quando o editor principal é rolado"""
        self.update_viewport_position()
        
    def update_viewport_position(self):
        """Atualiza a posição do retângulo de viewport - CORRIGIDO"""
        if not self.main_editor:
            return
            
        # Calcular proporções
        main_doc = self.main_editor.document()
        minimap_doc = self.document()
        
        if main_doc.lineCount() == 0 or minimap_doc.lineCount() == 0:
            return
            
        # Obter a região visível atual do editor principal
        main_scrollbar = self.main_editor.verticalScrollBar()
        main_max = main_scrollbar.maximum()
        main_value = main_scrollbar.value()
        
        # Calcular a proporção de rolagem
        if main_max > 0:
            scroll_ratio = main_value / main_max
        else:
            scroll_ratio = 0
            
        # Calcular altura visível proporcional
        minimap_height = self.height()
        main_visible_ratio = self.main_editor.viewport().height() / main_doc.size().height()
        viewport_height = max(minimap_height * main_visible_ratio, 20)  # Altura mínima
        
        # Calcular posição do viewport no minimap
        available_height = minimap_height - viewport_height
        viewport_top = scroll_ratio * available_height
        
        # Atualizar o retângulo do viewport
        self.viewport_rect = QRect(0, int(viewport_top), self.width(), int(viewport_height))
        self.viewport_rect_color = QColor(86, 156, 214, 80)  # Azul translúcido
        
        self.viewport().update()
        
    def paintEvent(self, event):
        """Evento de pintura personalizado para desenhar o viewport - CORRIGIDO"""
        super().paintEvent(event)
        
        # Desenhar o retângulo do viewport
        if self.viewport_rect.isValid():
            painter = QPainter(self.viewport())
            painter.fillRect(self.viewport_rect, self.viewport_rect_color)
            
            # Borda do viewport
            painter.setPen(QColor(86, 156, 214))
            painter.drawRect(self.viewport_rect)
            
    def resizeEvent(self, event):
        """Atualiza quando o minimap é redimensionado"""
        super().resizeEvent(event)
        self.update_viewport_position()
        
    def mousePressEvent(self, event):
        """Navega para a posição clicada no minimap - CORRIGIDO"""
        if event.button() == Qt.LeftButton and self.main_editor:
            self.navigate_to_click_position(event.pos())
            
    def mouseMoveEvent(self, event):
        """Permite arrastar o viewport - CORRIGIDO"""
        if event.buttons() & Qt.LeftButton and self.main_editor:
            self.navigate_to_click_position(event.pos())
            
    def wheelEvent(self, event):
        """Rola o editor principal quando roda no minimap"""
        if self.main_editor:
            # Encaminhar evento de roda para o editor principal
            self.main_editor.wheelEvent(event)
            
    def navigate_to_click_position(self, pos):
        """Navega para a posição clicada no minimap - CORRIGIDO"""
        if not self.main_editor:
            return
            
        # Calcular a posição proporcional no editor principal
        click_y = pos.y()
        minimap_height = self.height()
        
        if minimap_height <= 0:
            return
            
        click_ratio = click_y / minimap_height
        
        # Calcular nova posição de rolagem no editor principal
        main_scrollbar = self.main_editor.verticalScrollBar()
        main_max = main_scrollbar.maximum()
        new_scroll_value = int(click_ratio * main_max)
        
        # Aplicar a nova posição de rolagem
        main_scrollbar.setValue(new_scroll_value)

    def clear(self):
        """Limpa o conteúdo do minimap"""
        self.setPlainText("")



class LoadingWidget(QWidget):
    """Widget de carregamento para o autocomplete"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
                                                                                QProgressBar {
                                                                                                border: none;
                                                                                                background-color: #2d2d30;
                                                                                                border-radius: 3px;
                                                                                }
                                                                                QProgressBar::chunk {
                                                                                                background-color: #569cd6;
                                                                                                border-radius: 3px;
                                                                                }
                                                                """)

        # Texto de carregamento
        self.loading_label = QLabel("🔄 Carregando sugestões...")
        self.loading_label.setStyleSheet(
            "color: #9cdcfe; font-size: 10px;")
        self.loading_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.loading_label)
        self.setLayout(layout)
        self.hide()



class StatusBarProgress(QWidget):
    """Widget de progresso para a barra de status"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        # Ícone
        self.icon_label = QLabel("🔄")
        self.icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.icon_label)

        # Texto
        self.text_label = QLabel("Carregando...")
        self.text_label.setStyleSheet(
            "color: #9cdcfe; font-size: 12px;")
        layout.addWidget(self.text_label)

        # Barra de progresso pequena
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
                                                                                QProgressBar {
                                                                                                border: 1px solid #3c3c3c;
                                                                                                border-radius: 3px;
                                                                                                background-color: #1e1e1e;
                                                                                }
                                                                                QProgressBar::chunk {
                                                                                                background-color: #569cd6;
                                                                                                border-radius: 2px;
                                                                                }
                                                                """)
        layout.addWidget(self.progress_bar)

        # Botão fechar
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setStyleSheet("""
                                                                                QPushButton {
                                                                                                background-color: transparent;
                                                                                                color: #cccccc;
                                                                                                border: none;
                                                                                                font-size: 12px;
                                                                                                font-weight: bold;
                                                                                }
                                                                                QPushButton:hover {
                                                                                                background-color: #d84f4f;
                                                                                                color: white;
                                                                                                border-radius: 2px;
                                                                                }
                                                                """)
        self.close_btn.clicked.connect(self.hide)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)
        self.hide()

    def update_progress(self, value, message=""):
        """Atualiza o progresso"""
        self.progress_bar.setValue(value)
        if message:
            self.text_label.setText(message)

    def show_loading(self, message="Carregando..."):
        """Mostra o widget de carregamento"""
        self.icon_label.setText("🔄")
        self.text_label.setText(message)
        self.progress_bar.setValue(0)
        self.show()

    def show_success(self, message="Concluído!"):
        """Mostra sucesso"""
        self.icon_label.setText("✅")
        self.text_label.setText(message)
        self.progress_bar.setValue(100)
        QTimer.singleShot(2000, self.hide)

    def show_error(self, message="Erro!"):
        """Mostra erro"""
        self.icon_label.setText("❌")
        self.text_label.setText(message)
        self.progress_bar.setValue(0)
        QTimer.singleShot(3000, self.hide)



class ProblemsDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        super().paint(painter, option, index)
        data = index.data(Qt.UserRole)
        if data:
            error_type = data.get('type', 'info')
            color = QColor("red") if error_type == 'error' else QColor("yellow") if error_type == 'warning' else QColor(
                "blue")
            painter.setPen(color)
            painter.drawText(
                option.rect.x() + 5, option.rect.bottom() - 5, "●")

