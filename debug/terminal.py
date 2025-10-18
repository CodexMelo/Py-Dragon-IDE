import os
import sys
import re
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (QVBoxLayout, QWidget, QPushButton, 
                              QMessageBox, QPlainTextEdit, QLabel, QHBoxLayout)
from PySide6.QtCore import QProcess, QTimer, Qt
from PySide6.QtGui import QFont, QTextCursor, QKeyEvent

class TerminalTextEdit(QPlainTextEdit):
    """Terminal integrado para execução de comandos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.shell_process = None
        self.input_start = 0
        self.command_history = []
        self.history_index = -1
        
        self.setup_terminal()
        
    def setup_terminal(self):
        """Configura o terminal"""
        self.setFont(QFont("Consolas", 10))
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        
        # Prompt inicial
        self._setup_initial_prompt()
        
    def _setup_initial_prompt(self):
        """Configura prompt inicial"""
        self.clear()
        self.appendPlainText("Py Dragon Terminal - Digite 'help' para comandos\n\n")
        self.input_start = self.textCursor().position()
        
        # Adiciona prompt inicial
        prompt = self.get_prompt()
        self.insertPlainText(prompt)
        self.input_start += len(prompt)
        
    def get_prompt(self):
        """Retorna o prompt baseado no SO"""
        if os.name == 'nt':
            return "C:\\> "
        else:
            return "$ "
            
    def set_shell_process(self, process):
        """Define o processo do shell"""
        self.shell_process = process
        
    def append_output(self, text):
        """Adiciona saída ao terminal"""
        try:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            # Remove códigos ANSI básicos
            cleaned_text = self._filter_ansi_codes(text)
            
            cursor.insertText(cleaned_text)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            
        except Exception as e:
            print(f"Erro ao adicionar output: {e}")
            
    def _filter_ansi_codes(self, text):
        """Remove códigos de escape ANSI"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
        
    def keyPressEvent(self, event: QKeyEvent):
        """Manipula pressionamento de teclas no terminal"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_enter_key()
            event.accept()
            return
            
        elif event.key() == Qt.Key_Backspace:
            cursor = self.textCursor()
            if cursor.position() <= self.input_start:
                event.accept()  # Não permite apagar o prompt
                return
            else:
                super().keyPressEvent(event)
                return
                
        elif event.key() == Qt.Key_Up:
            self._navigate_history(-1)
            event.accept()
            return
            
        elif event.key() == Qt.Key_Down:
            self._navigate_history(1)
            event.accept()
            return
            
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            if self.shell_process and self.shell_process.state() == QProcess.Running:
                self.shell_process.kill()
                self.append_output("\n^C\n")
                self._add_new_prompt()
            event.accept()
            return
            
        else:
            super().keyPressEvent(event)
            
    def _handle_enter_key(self):
        """Manipula tecla Enter - executa comando"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Obtém o comando atual
        full_text = self.toPlainText()
        if len(full_text) < self.input_start:
            self.input_start = len(full_text)
            
        command = full_text[self.input_start:].strip()
        
        if command:
            # Adiciona ao histórico
            if not self.command_history or self.command_history[-1] != command:
                self.command_history.append(command)
            self.history_index = -1
            
            # Envia para o processo do shell
            if self.shell_process and self.shell_process.state() == QProcess.Running:
                self.shell_process.write(f"{command}\n".encode('utf-8'))
            else:
                self.append_output(f"\n❌ Shell não está disponível\n")
                
        # Nova linha e prompt
        self.append_output("\n")
        self._add_new_prompt()
        
    def _add_new_prompt(self):
        """Adiciona novo prompt"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        prompt = self.get_prompt()
        cursor.insertText(prompt)
        
        self.input_start = cursor.position()
        self.setTextCursor(cursor)
        
    def _navigate_history(self, direction):
        """Navega pelo histórico de comandos"""
        if not self.command_history:
            return
            
        self.history_index += direction
        
        # Limita o índice
        if self.history_index < -1:
            self.history_index = -1
        elif self.history_index >= len(self.command_history):
            self.history_index = len(self.command_history) - 1
            
        # Obtém o comando do histórico
        if self.history_index == -1:
            command = ""
        else:
            command = self.command_history[self.history_index]
            
        # Substitui o texto atual
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.setPosition(self.input_start, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(command)
        
        self.setTextCursor(cursor)

class SystemTerminalWrapper(QWidget):
    """Wrapper para terminal do sistema - versão integrada"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ide = parent
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Título informativo
        title_label = QLabel("Terminal do Sistema")
        title_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                color: #569cd6;
                padding: 8px;
                font-weight: bold;
                border-bottom: 1px solid #3e3e42;
            }
        """)
        self.layout.addWidget(title_label)
        
        # Descrição
        desc_label = QLabel(
            "Abre o terminal nativo do sistema operacional.\n"
            "Útil para comandos que precisam de interface gráfica completa."
        )
        desc_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                padding: 10px;
                background-color: #252526;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        desc_label.setWordWrap(True)
        self.layout.addWidget(desc_label)
        
        # Botão principal
        self.btn_open_terminal = QPushButton("🖥️ Abrir Terminal do Sistema")
        self.btn_open_terminal.clicked.connect(self.open_system_terminal)
        self.btn_open_terminal.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
                border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0c5488;
            }
        """)
        self.layout.addWidget(self.btn_open_terminal)
        
        # Botões adicionais
        button_layout = QHBoxLayout()
        
        # Terminal com diretório do projeto
        self.btn_project_terminal = QPushButton("📁 Terminal no Projeto")
        self.btn_project_terminal.clicked.connect(self.open_project_terminal)
        self.btn_project_terminal.setStyleSheet("""
            QPushButton {
                background-color: #388a34;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3e9c39;
            }
        """)
        button_layout.addWidget(self.btn_project_terminal)
        
        # PowerShell (Windows) ou Bash (Linux)
        if os.name == 'nt':
            self.btn_powershell = QPushButton("🔷 PowerShell")
            self.btn_powershell.clicked.connect(self.open_powershell)
        else:
            self.btn_powershell = QPushButton("🐧 Bash")
            self.btn_powershell.clicked.connect(self.open_bash)
            
        self.btn_powershell.setStyleSheet("""
            QPushButton {
                background-color: #68217a;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #7a258f;
            }
        """)
        button_layout.addWidget(self.btn_powershell)
        
        self.layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("Pronto para abrir terminal...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #969696;
                padding: 5px;
                font-size: 11px;
            }
        """)
        self.layout.addWidget(self.status_label)

    def open_system_terminal(self):
        """Abre o terminal NATIVO do sistema"""
        try:
            self.status_label.setText("🔄 Abrindo terminal...")
            
            if os.name == 'nt':  # Windows
                self._open_windows_terminal()
            else:  # Linux/Mac
                self._open_linux_terminal()
                
            self.status_label.setText("✅ Terminal aberto com sucesso!")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Pronto para abrir terminal..."))
                
        except Exception as e:
            self.status_label.setText(f"❌ Erro: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Falha ao abrir terminal: {e}")

    def open_project_terminal(self):
        """Abre terminal no diretório do projeto atual"""
        try:
            project_dir = self._get_project_directory()
            if project_dir:
                self.status_label.setText(f"🔄 Abrindo terminal em: {os.path.basename(project_dir)}")
                
                if os.name == 'nt':
                    subprocess.Popen(f'cmd.exe /K "cd /d "{project_dir}""', shell=True)
                else:
                    subprocess.Popen(['gnome-terminal', '--working-directory', project_dir], 
                                   shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                self.status_label.setText("✅ Terminal do projeto aberto!")
                QTimer.singleShot(2000, lambda: self.status_label.setText("Pronto para abrir terminal..."))
            else:
                self.status_label.setText("❌ Nenhum projeto aberto")
                
        except Exception as e:
            self.status_label.setText(f"❌ Erro: {str(e)}")

    def open_powershell(self):
        """Abre PowerShell no Windows"""
        try:
            self.status_label.setText("🔄 Abrindo PowerShell...")
            subprocess.Popen(["powershell"], shell=True)
            self.status_label.setText("✅ PowerShell aberto!")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Pronto para abrir terminal..."))
        except Exception as e:
            self.status_label.setText(f"❌ Erro: {str(e)}")

    def open_bash(self):
        """Abre Bash no Linux/Mac"""
        try:
            self.status_label.setText("🔄 Abrindo Bash...")
            subprocess.Popen(["gnome-terminal", "--", "bash"], 
                           shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.status_label.setText("✅ Bash aberto!")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Pronto para abrir terminal..."))
        except Exception as e:
            self.status_label.setText(f"❌ Erro: {str(e)}")

    def _open_windows_terminal(self):
        """Abre CMD ou PowerShell no Windows"""
        try:
            # Tenta Windows Terminal (moderno)
            subprocess.Popen(["wt"], shell=True)
        except:
            try:
                # Tenta PowerShell
                subprocess.Popen(["powershell"], shell=True)
            except:
                # Usa CMD tradicional
                subprocess.Popen(["cmd"], shell=True)

    def _open_linux_terminal(self):
        """Abre terminal no Linux"""
        try:
            terminals = [
                "gnome-terminal", "konsole", "xfce4-terminal",
                "terminator", "xterm", "mate-terminal", "lxterminal"
            ]
            
            for terminal in terminals:
                try:
                    result = subprocess.run(["which", terminal], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        project_dir = self._get_project_directory()
                        if project_dir:
                            subprocess.Popen([terminal, "--working-directory", project_dir])
                        else:
                            subprocess.Popen([terminal])
                        return
                except:
                    continue
                    
            # Fallback
            subprocess.Popen(["xterm"])
            
        except Exception as e:
            print(f"❌ Erro ao abrir terminal Linux: {e}")

    def _get_project_directory(self):
        """Obtém o diretório do projeto atual"""
        try:
            if self.ide and hasattr(self.ide, 'project_path') and self.ide.project_path:
                return self.ide.project_path
        except:
            pass
        return None