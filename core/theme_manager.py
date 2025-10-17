# ===== IMPORTS DO PYSIDE6 =====
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QComboBox, QColorDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from typing import Dict, Any




class ThemeManager:
    """Gerenciador de temas para o IDE"""

    def __init__(self):
        self.themes = {
            "Dark Professional": self.dark_professional_theme(),
            "Dark Blue": self.dark_blue_theme(),
            "Light Modern": self.light_modern_theme(),
            "Monokai": self.monokai_theme(),
            "Solarized Dark": self.solarized_dark_theme(),
            "Solarized Light": self.solarized_light_theme(),
        }
        self.current_theme = "Dark Professional"

    def dark_professional_theme(self):
        return {
            "name": "Dark Professional",
            "type": "dark",
            "colors": {
                "background": "#1e1e1e",
                "foreground": "#d4d4d4",
                "selection": "#264f78",
                "cursor": "#569cd6",
                "comment": "#6a9955",
                "string": "#ce9178",
                "number": "#b5cea8",
                "keyword": "#569cd6",
                "function": "#dcdcaa",
                "class": "#4ec9b0",
                "error": "#f44747",
                "warning": "#ffcc66",
                "info": "#9cdcfe"
            },
            "syntax": {
                "keyword": "#569cd6",
                "string": "#ce9178",
                "comment": "#6a9955",
                "number": "#b5cea8",
                "function": "#dcdcaa",
                "class": "#4ec9b0",
                "builtin": "#4ec9b0"
            }
        }

    def dark_blue_theme(self):
        return {
            "name": "Dark Blue",
            "type": "dark",
            "colors": {
                "background": "#0d1117",
                "foreground": "#c9d1d9",
                "selection": "#1c3b5a",
                "cursor": "#58a6ff",
                "comment": "#8b949e",
                "string": "#a5d6ff",
                "number": "#79c0ff",
                "keyword": "#ff7b72",
                "function": "#d2a8ff",
                "class": "#ffa657",
                "error": "#f85149",
                "warning": "#d29922",
                "info": "#a5d6ff"
            }
        }

    def light_modern_theme(self):
        return {
            "name": "Light Modern",
            "type": "light",
            "colors": {
                "background": "#ffffff",
                "foreground": "#24292e",
                "selection": "#0366d625",
                "cursor": "#0969da",
                "comment": "#6a737d",
                "string": "#032f62",
                "number": "#005cc5",
                "keyword": "#d73a49",
                "function": "#6f42c1",
                "class": "#22863a",
                "error": "#cb2431",
                "warning": "#f66a0a",
                "info": "#005cc5"
            }
        }

    def monokai_theme(self):
        return {
            "name": "Monokai",
            "type": "dark",
            "colors": {
                "background": "#272822",
                "foreground": "#f8f8f2",
                "selection": "#49483e",
                "cursor": "#f92672",
                "comment": "#75715e",
                "string": "#e6db74",
                "number": "#ae81ff",
                "keyword": "#f92672",
                "function": "#a6e22e",
                "class": "#a6e22e",
                "error": "#f44747",
                "warning": "#ffd700",
                "info": "#66d9ef"
            }
        }

    def solarized_dark_theme(self):
        return {
            "name": "Solarized Dark",
            "type": "dark",
            "colors": {
                "background": "#002b36",
                "foreground": "#839496",
                "selection": "#073642",
                "cursor": "#839496",
                "comment": "#586e75",
                "string": "#2aa198",
                "number": "#d33682",
                "keyword": "#859900",
                "function": "#b58900",
                "class": "#268bd2",
                "error": "#dc322f",
                "warning": "#cb4b16",
                "info": "#2aa198"
            }
        }

    def solarized_light_theme(self):
        return {
            "name": "Solarized Light",
            "type": "light",
            "colors": {
                "background": "#fdf6e3",
                "foreground": "#657b83",
                "selection": "#eee8d5",
                "cursor": "#657b83",
                "comment": "#93a1a1",
                "string": "#2aa198",
                "number": "#d33682",
                "keyword": "#859900",
                "function": "#b58900",
                "class": "#268bd2",
                "error": "#dc322f",
                "warning": "#cb4b16",
                "info": "#2aa198"
            }
        }

    def get_theme(self, theme_name):
        return self.themes.get(
            theme_name, self.themes["Dark Professional"])

    def get_theme_names(self):
        return list(self.themes.keys())


class ThemeDialog(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.current_theme = theme_manager.current_theme
        self.setWindowTitle("🎨 Gerenciador de Temas")
        self.setGeometry(400, 300, 800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()

        # Lista de temas
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Selecione um tema:"))

        self.theme_list = QListWidget()
        self.theme_list.addItems(
            self.theme_manager.get_theme_names())
        self.theme_list.currentItemChanged.connect(
            self.on_theme_selected)
        left_panel.addWidget(self.theme_list)

        # Pré-visualização
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Pré-visualização:"))

        self.preview_widget = QWidget()
        self.preview_widget.setMinimumSize(400, 300)
        self.preview_layout = QVBoxLayout(self.preview_widget)

        # Simula um editor na pré-visualização
        self.preview_editor = QPlainTextEdit()
        self.preview_editor.setPlainText("""# Exemplo de código Python
                                def hello_world():
                                                \"\"\"Função de exemplo\"\"\"
                                                name = "Mundo"
                                                number = 42
                                                # Saída: Olá, Mundo!
                                                print(f"Olá, {name}!")
                                                return number

                                class ExampleClass:
                                                def __init__(self):
                                                                self.value = 123

                                                def calculate(self, x):
                                                                return x * 2
                                """)
        self.preview_editor.setReadOnly(True)
        self.preview_layout.addWidget(self.preview_editor)

        right_panel.addWidget(self.preview_widget)

        # Informações do tema
        self.theme_info = QLabel()
        self.theme_info.setWordWrap(True)
        self.theme_info.setStyleSheet(
            "padding: 10px; border: 1px solid #ccc;")
        right_panel.addWidget(self.theme_info)

        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

        # Botões
        button_layout = QHBoxLayout()

        self.apply_btn = QPushButton("Aplicar Tema")
        self.apply_btn.clicked.connect(self.apply_theme)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)

        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Seleciona tema atual
        for i in range(self.theme_list.count()):
            if self.theme_list.item(
                    i).text() == self.current_theme:
                self.theme_list.setCurrentRow(
                    i)
                break

    def on_theme_selected(self, current, previous):
        """Quando um tema é selecionado na lista"""
        if current:
            theme_name = current.text()
            theme = self.theme_manager.get_theme(
                theme_name)
            self.apply_btn.setEnabled(
                theme_name != self.current_theme)
            self.update_preview(theme)
            self.update_theme_info(theme)

    def update_preview(self, theme):
        """Atualiza a pré-visualização com o tema selecionado"""
        colors = theme["colors"]

        # Aplica cores ao widget de pré-visualização
        style = f"""
                                                                                QPlainTextEdit {{
                                                                                                background-color: {colors['background']};
                                                                                                color: {
        colors['foreground']};
                                                                                                border: 1px solid #555;
                                                                                                font-family: 'Consolas', monospace;
                                                                                                font-size: 11px;
                                                                                }}
                                                                """
        self.preview_editor.setStyleSheet(style)

        # Aqui você aplicaria o syntax highlighting também
        # (simplificado para este exemplo)

    def update_theme_info(self, theme):
        """Atualiza informações do tema"""
        colors = theme["colors"]
        info_text = f"""
                                                                <h3>{theme['name']}</h3>
                                                                <p><b>Tipo:</b> {theme['type'].title()}</p>
                                                                <p><b>Cores principais:</b></p>
                                                                <table>
                                                                <tr><td>Fundo:</td><td style='background-color:{colors['background']}; color:{colors['foreground']};'>{colors['background']}</td></tr>
                                                                <tr><td>Texto:</td><td style='background-color:{colors['foreground']}; color:{colors['background']};'>{colors['foreground']}</td></tr>
                                                                <tr><td>Seleção:</td><td style='background-color:{colors['selection']}; color:{colors['foreground']};'>{colors['selection']}</td></tr>
                                                                </table>
                                                                """
        self.theme_info.setText(info_text)

    def apply_theme(self, theme_name):
        """Aplica um tema ao IDE (ATUALIZADO)"""
        theme = self.theme_manager.get_theme(theme_name)
        colors = theme["colors"]

        # Aplica o tema à interface
        self.apply_theme_to_ui(theme)

        # Aplica syntax highlighting aos editores
        self.apply_syntax_theme(theme)
        
        # Atualiza minimap
        self.update_minimap_theme()

        print(f"Tema '{theme_name}' aplicado!")

