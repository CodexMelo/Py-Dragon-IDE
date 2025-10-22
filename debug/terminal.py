# terminalc.py - Versão Corrigida do RealTerminal

import os
import sys
import re
import subprocess
import platform
from pathlib import Path

from PySide6.QtWidgets import (QVBoxLayout, QWidget, QPushButton, 
                              QMessageBox, QPlainTextEdit, QLabel, QHBoxLayout)
from PySide6.QtCore import QProcess, QTimer, Qt
from PySide6.QtGui import QFont, QTextCursor, QKeyEvent, QTextCharFormat, QColor

class RealTerminal(QPlainTextEdit):
    """Terminal REAL com virtualenv - VERSÃO CORRIGIDA"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Processo do shell
        self.shell_process = QProcess()
        self.shell_process.readyReadStandardOutput.connect(self.handle_stdout)
        self.shell_process.readyReadStandardError.connect(self.handle_stderr)
        self.shell_process.finished.connect(self.handle_finished)
        
        # Estado do terminal
        self.command_history = []
        self.history_index = -1
        self.input_start = 0
        self.current_directory = os.getcwd()
        self.is_windows = os.name == 'nt'
        self.venv_active = False
        self.venv_name = None
        self.waiting_for_command = True
        self.prompt_shown = False
        
        # Timer para controle de prompt
        self.prompt_timer = QTimer()
        self.prompt_timer.setSingleShot(True)
        self.prompt_timer.timeout.connect(self._safe_show_prompt)
        
        # Cores
        self.success_color = "#4EC9B0"
        self.error_color = "#F44747" 
        self.warning_color = "#FFCC66"
        self.info_color = "#569CD6"
        self.command_color = "#DCDCAA"
        self.prompt_color = "#00ff00"
        self.output_color = "#d4d4d4"
        
        self.setup_real_terminal()
        
    def setup_real_terminal(self):
        """Configura o terminal REAL"""
        self.setFont(QFont("Consolas", 11))
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                selection-background-color: #264f78;
                padding: 8px;
            }
        """)
        
        # Iniciar shell
        self.start_real_shell()
        
    def get_prompt(self):
        """Gera prompt formatado"""
        user = os.getenv('USERNAME') or os.getenv('USER') or 'user'
        hostname = platform.node()
        
        # Formata diretório
        home = os.path.expanduser("~")
        cwd = self.current_directory
        
        if cwd == home:
            display_cwd = "~"
        elif cwd.startswith(home):
            display_cwd = "~" + cwd[len(home):]
        else:
            display_cwd = cwd
            
        # Limita comprimento
        if len(display_cwd) > 30:
            display_cwd = "..." + display_cwd[-27:]
        
        # Venv apenas se ativo
        prompt_parts = [f"┌──[{user}@{hostname}]"]
        
        if self.venv_active and self.venv_name:
            prompt_parts.append(f"[venv: {self.venv_name}]")
        
        prompt_parts.append(f"─[{display_cwd}]")
        prompt_line = "".join(prompt_parts)
        
        return f"{prompt_line}\n└──╼ "
    
    def show_prompt(self):
        """Mostra prompt - EVITA DUPLICAÇÃO"""
        if self.prompt_shown:
            return
            
        self.waiting_for_command = True
        self.prompt_shown = True
        self.prompt_timer.stop()

        self.append_colored_text(self.get_prompt(), self.prompt_color)
        self.moveCursor(QTextCursor.End)
        self.input_start = self.textCursor().position()
    
    def _safe_show_prompt(self):
        """Mostra prompt de forma segura"""
        try:
            if not self.prompt_shown:
                self.show_prompt()
        except Exception as e:
            print(f"Erro ao mostrar prompt: {e}")
    
    def start_real_shell(self):
        """Inicia shell do sistema"""
        try:
            # Para processo anterior
            if self.shell_process.state() == QProcess.Running:
                self.shell_process.kill()
                self.shell_process.waitForFinished(1000)
            
            # Reset estado
            self.prompt_shown = False
            self.waiting_for_command = True
            
            # Header
            self.append_colored_text("🚀 Terminal PyDragon\n", self.info_color)
            
            if self.is_windows:
                self.shell_process.setProgram("cmd.exe")
                self.shell_process.setArguments(["/Q", "/K"])
                shell_name = "CMD"
            else:
                self.shell_process.setProgram("/bin/bash")
                self.shell_process.setArguments(["-i"])
                shell_name = "Bash"
                
                # Configurar ambiente
                env = self.shell_process.processEnvironment()
                env.insert("TERM", "dumb")
                env.insert("CLICOLOR", "0")
                env.insert("PS1", "")
                env.insert("VIRTUAL_ENV_DISABLE_PROMPT", "1")
                self.shell_process.setProcessEnvironment(env)
            
            self.shell_process.setWorkingDirectory(self.current_directory)
            
            # Iniciar processo
            self.shell_process.start()
            
            if self.shell_process.waitForStarted(3000):
                self.append_colored_text(f"✅ {shell_name} iniciado\n", self.success_color)
                self.append_colored_text(f"📁 {self.current_directory}\n", self.info_color)
                self.append_colored_text("=" * 50 + "\n", self.info_color)
                
                # Configurar bash
                if not self.is_windows:
                    setup_commands = [
                        "export PS1=''",
                        "export VIRTUAL_ENV_DISABLE_PROMPT=1", 
                        "unset PROMPT_COMMAND",
                    ]
                    
                    for cmd in setup_commands:
                        self.shell_process.write(f"{cmd}\n".encode())
                
                # Verificar venv
                QTimer.singleShot(1000, self._check_and_activate_venv_if_exists)
                
                # Mostrar prompt
                self.prompt_timer.start(1500)
                
            else:
                self.append_colored_text("❌ Falha ao iniciar shell\n", self.error_color)
                
        except Exception as e:
            self.append_colored_text(f"❌ Erro: {str(e)}\n", self.error_color)
    
    def _check_and_activate_venv_if_exists(self):
        """Verifica e ativa venv se existir"""
        try:
            venv_candidates = [
                os.path.join(self.current_directory, "venv"),
                os.path.join(self.current_directory, ".venv"),
                os.path.join(self.current_directory, "env"),
            ]
            
            venv_found = False
            for venv_path in venv_candidates:
                if self.is_valid_venv(venv_path):
                    self.activate_venv(venv_path)
                    venv_found = True
                    break
            
            if not venv_found:
                self.venv_active = False
                self.venv_name = None
                
        except Exception as e:
            print(f"Erro ao verificar venv: {e}")
            self.venv_active = False
            self.venv_name = None
    
    def is_valid_venv(self, venv_path):
        """Verifica se é um virtualenv válido"""
        try:
            if not venv_path or not os.path.exists(venv_path):
                return False
                
            # Verificar arquivos essenciais
            if os.name == 'nt':
                python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
            else:
                python_exe = os.path.join(venv_path, "bin", "python")
                activate_script = os.path.join(venv_path, "bin", "activate")
            
            essential_files = [python_exe, activate_script]
            for file_path in essential_files:
                if not os.path.exists(file_path):
                    return False
            
            # Testar Python do venv
            try:
                result = subprocess.run(
                    [python_exe, "--version"],
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                return result.returncode == 0
            except:
                return False
                
        except Exception as e:
            print(f"Erro na validação do venv: {e}")
            return False
    
    def activate_venv(self, venv_path):
        """Ativa virtualenv"""
        try:
            if self.is_windows:
                activate_cmd = f'call "{os.path.join(venv_path, "Scripts", "activate.bat")}"\n'
            else:
                activate_cmd = f'source "{os.path.join(venv_path, "bin", "activate")}"\n'
            
            self.shell_process.write(activate_cmd.encode('utf-8'))
            self.venv_active = True
            self.venv_name = os.path.basename(venv_path)
            
            # Atualizar prompt
            if self.prompt_shown:
                self._force_prompt_update()
            
            self.append_colored_text(f"✅ Venv ativado: {self.venv_name}\n", self.success_color)
            return True
            
        except Exception as e:
            print(f"Erro ao ativar venv: {e}")
            self.append_colored_text(f"❌ Erro ao ativar venv: {e}\n", self.error_color)
            return False
    
    def _force_prompt_update(self):
        """Força atualização do prompt"""
        try:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()
            
            if "└──╼" in current_line:
                cursor.removeSelectedText()
                self.prompt_shown = False
                self.prompt_timer.start(100)
                
        except Exception as e:
            print(f"Erro ao atualizar prompt: {e}")
        
    def deactivate_venv(self):
        """Desativa o venv atual"""
        try:
            if self.venv_active:
                deactivate_cmd = "deactivate\n"
                if not self.is_windows:
                    deactivate_cmd += "export PS1=''\n"
                
                self.shell_process.write(deactivate_cmd.encode('utf-8'))
                self.venv_active = False
                self.venv_name = None
                
                if self.prompt_shown:
                    self._force_prompt_update()
                
                self.append_colored_text("🔴 Venv desativado\n", self.warning_color)
                return True
            return False
        except Exception as e:
            print(f"Erro ao desativar venv: {e}")
            return False
        
    def append_colored_text(self, text, color):
        """Adiciona texto colorido"""
        if not text.strip():
            return
            
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
    
    def clean_ansi_codes(self, text):
        """Remove códigos ANSI"""
        import re
        
        ansi_escape = re.compile(r'''
            \x1B  # ESC
            (?:   # 7-bit C1 Fe (except CSI)
                [@-Z\\-_]
            |     # ou
                \[  # CSI
                [0-?]*  # Parameter bytes
                [ -/]*  # Intermediate bytes
                [@-~]   # Final byte
            )
        ''', re.VERBOSE)
        
        cleaned = ansi_escape.sub('', text)
        
        # Remove outros caracteres de controle
        control_chars = re.compile(r'[\x00-\x1f\x7f-\x9f]')
        cleaned = control_chars.sub('', cleaned)
        
        # Remove prompts indesejados
        cleaned = re.sub(r'\]0;[^\n]*', '', cleaned)
        cleaned = re.sub(r'^\(venv\)\s*', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^\S+@\S+:\S+[\$\#]\s*', '', cleaned, flags=re.MULTILINE)
        
        return cleaned.strip()
    
    def handle_stdout(self):
        """Processa stdout - CORRIGIDO"""
        try:
            data = self.shell_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            
            if data.strip():
                cleaned_data = self.clean_ansi_codes(data)
                
                # Filtra linhas
                lines = cleaned_data.split('\n')
                filtered_lines = []
                
                for line in lines:
                    clean_line = line.strip()
                    if (clean_line and 
                        not clean_line.endswith('$') and 
                        not clean_line.endswith('#') and
                        not clean_line.startswith('(venv)') and
                        not re.match(r'^\S+@\S+:', clean_line) and
                        '└──╼' not in clean_line and
                        '┌──' not in clean_line):
                        filtered_lines.append(line)
                
                cleaned_data = '\n'.join(filtered_lines)
                
                if cleaned_data.strip():
                    self._process_shell_output(cleaned_data)
                
                # Mostrar prompt após processamento
                self.prompt_shown = False
                self.prompt_timer.start(100)
                
        except Exception as e:
            print(f"Erro stdout: {e}")
            self.prompt_shown = False
            self.prompt_timer.start(100)
    
    def handle_stderr(self):
        """Processa stderr"""
        try:
            data = self.shell_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if data.strip():
                cleaned_data = self.clean_ansi_codes(data)
                if cleaned_data.strip():
                    self.append_colored_text(cleaned_data + '\n', self.error_color)
            
            self.prompt_shown = False
            self.prompt_timer.start(100)
            
        except Exception as e:
            print(f"Erro stderr: {e}")
            self.prompt_shown = False
            self.prompt_timer.start(100)
    
    def _process_shell_output(self, text):
        """Processa saída do shell com cores"""
        if not text.strip():
            return
            
        lines = text.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            line_lower = line.lower()
            
            if any(word in line_lower for word in ['error', 'falhou', 'failed', 'não encontrado', 'not found']):
                color = self.error_color
            elif any(word in line_lower for word in ['warning', 'aviso', 'atenção']):
                color = self.warning_color
            elif any(word in line_lower for word in ['sucesso', 'success', 'concluído', 'completed']):
                color = self.success_color
            elif line.startswith(('(', '[', '{')) or 'python' in line_lower:
                color = self.info_color
            else:
                color = self.output_color
            
            self.append_colored_text(line + '\n', color)
    
    def keyPressEvent(self, event):
        """Manipula pressionamento de teclas"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._execute_command()
            return
            
        elif event.key() == Qt.Key_Backspace:
            cursor = self.textCursor()
            if cursor.position() > self.input_start:
                super().keyPressEvent(event)
            return
                
        elif event.key() == Qt.Key_Up:
            self._navigate_history(-1)
            return
                
        elif event.key() == Qt.Key_Down:
            self._navigate_history(1)
            return
                
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            if self.shell_process.state() == QProcess.Running:
                self.append_colored_text("^C\n", self.warning_color)
                self.shell_process.write(b"\x03")
                self.prompt_shown = False
                self.prompt_timer.start(100)
            return
            
        elif event.key() == Qt.Key_L and event.modifiers() == Qt.ControlModifier:
            self.clear()
            self.input_start = 0
            self.prompt_shown = False
            self.append_colored_text("🧹 Tela limpa\n", self.info_color)
            self.prompt_timer.start(300)
            return
            
        elif event.key() == Qt.Key_E and event.modifiers() == Qt.ControlModifier:
            self.deactivate_venv()
            return
            
        else:
            cursor = self.textCursor()
            if cursor.position() >= self.input_start:
                super().keyPressEvent(event)
    
    def _execute_command(self):
        """Executa comando no shell"""
        if not self.waiting_for_command:
            return
            
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Pega o comando atual
        cursor.setPosition(self.input_start, QTextCursor.KeepAnchor)
        command_text = cursor.selectedText().strip()
        
        if command_text:
            # Remove linha do prompt atual
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()
            
            if "└──╼" in current_line:
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.select(QTextCursor.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.movePosition(QTextCursor.End)
            
            # Mostra comando executado
            self.append_colored_text(f"{command_text}\n", self.command_color)
            
            # Adicionar ao histórico
            if not self.command_history or self.command_history[-1] != command_text:
                self.command_history.append(command_text)
            self.history_index = len(self.command_history)
            
            # Enviar comando
            self.waiting_for_command = False
            self.prompt_shown = False

            if self.shell_process.state() == QProcess.Running:
                try:
                    self.shell_process.write(f"{command_text}\n".encode('utf-8'))
                    
                    if command_text.startswith('cd ') or command_text == 'cd':
                        QTimer.singleShot(300, self._update_directory)
                except Exception as e:
                    self.append_colored_text(f"❌ Erro: {str(e)}\n", self.error_color)
                    self.prompt_shown = False
                    self.prompt_timer.start(100)
            else:
                self.append_colored_text("❌ Shell não disponível\n", self.error_color)
                self.prompt_shown = False
                self.prompt_timer.start(100)
        else:
            # Comando vazio
            self.prompt_shown = False
            self.show_prompt()
    
    def _update_directory(self):
        """Atualiza diretório atual"""
        try:
            if self.shell_process.state() != QProcess.Running:
                return

            if platform.system() == "Windows":
                self.shell_process.write(b"cd\r\n")
            else:
                self.shell_process.write(b"pwd\n")

            # Atualiza venv
            self.auto_detect_and_activate_venv()
            
        except Exception as e:
            print(f"Erro ao atualizar diretório: {e}")
    
    def auto_detect_and_activate_venv(self):
        """Detecta e ativa venv automaticamente"""
        try:
            venv_candidates = [
                os.path.join(self.current_directory, "venv"),
                os.path.join(self.current_directory, ".venv"),
                os.path.join(self.current_directory, "env"),
            ]
            
            venv_found = False
            for venv_path in venv_candidates:
                if self.is_valid_venv(venv_path):
                    self.activate_venv(venv_path)
                    venv_found = True
                    break
            
            if not venv_found and self.venv_active:
                self.venv_active = False
                self.venv_name = None
                
            return venv_found
            
        except Exception as e:
            print(f"Erro ao detectar venv: {e}")
            self.venv_active = False
            self.venv_name = None
            return False
    
    def _navigate_history(self, direction):
        """Navega pelo histórico"""
        if not self.command_history:
            return
            
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.setPosition(self.input_start, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        
        new_index = self.history_index + direction
        
        if new_index < 0:
            new_index = 0
        elif new_index >= len(self.command_history):
            new_index = len(self.command_history) - 1
            self.history_index = new_index
            return
        
        self.history_index = new_index
        
        command = self.command_history[self.history_index]
        format = QTextCharFormat()
        format.setForeground(QColor(self.command_color))
        cursor.setCharFormat(format)
        cursor.insertText(command)
        
        self.setTextCursor(cursor)
    
    def handle_finished(self, exit_code, exit_status):
        """Shell terminado"""
        self.append_colored_text(f"\n💀 Processo finalizado ({exit_code})\n", self.warning_color)
        self.append_colored_text("🔄 Reiniciando...\n", self.info_color)
        QTimer.singleShot(2000, self.start_real_shell)
    
    def change_directory(self, new_dir):
        """Muda diretório"""
        if os.path.exists(new_dir):
            self.current_directory = new_dir
            self.shell_process.setWorkingDirectory(new_dir)
            
            if self.shell_process.state() == QProcess.Running:
                if self.is_windows:
                    self.shell_process.write(f'cd /d "{new_dir}"\r\n'.encode())
                else:
                    self.shell_process.write(f'cd "{new_dir}"\n'.encode())
                
                QTimer.singleShot(500, self.auto_detect_and_activate_venv)
    
    def close_terminal(self):
        """Fecha terminal"""
        if self.shell_process.state() == QProcess.Running:
            self.append_colored_text("👋 Fechando terminal...\n", self.info_color)
            if self.is_windows:
                self.shell_process.write(b"exit\r\n")
            else:
                self.shell_process.write(b"exit\n")
            self.shell_process.waitForFinished(2000)
            if self.shell_process.state() == QProcess.Running:
                self.shell_process.kill()