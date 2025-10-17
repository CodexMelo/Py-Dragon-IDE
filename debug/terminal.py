import os  # ✅ ADICIONE ESTE IMPORT
import sys
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt, QProcess
class TerminalTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Monospace", 10))
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        self._shell_process = None
        self._input_start = 0
        self._is_waiting_output = False
        self._command_history = []
        self._history_index = -1
        self._current_command = ""

    def set_shell_process(self, process):
        """Define o processo do shell"""
        self._shell_process = process
        self._setup_initial_prompt()

    def _setup_initial_prompt(self):
        """Configura prompt inicial"""
        self.clear()
        initial_text = "Py Dragon Terminal - Digite 'help' para ajuda\n"
        self.setPlainText(initial_text)
        self._add_prompt()
        self._move_cursor_to_end()

    def _add_prompt(self):
        """Adiciona novo prompt"""
        prompt = self._get_prompt()
        self.insertPlainText(prompt)
        self._input_start = len(self.toPlainText())
        self._move_cursor_to_end()

    def _get_prompt(self):
        """Retorna o prompt baseado no OS"""
        if os.name == 'nt':
            return "C:\\> "
        else:
            return "$ "

    def _move_cursor_to_end(self):
        """Move cursor para o final"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

    def append_output(self, data):
        """Adiciona saída do terminal - CORRIGIDO"""
        try:
            if not data.strip():
                return

            # Filtra códigos ANSI
            from re import sub
            cleaned_data = sub(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\][0-9;].*?\x07', '', data)
            
            if not cleaned_data.strip():
                return

            cursor = self.textCursor()
            current_pos = cursor.position()
            
            # Se estiver digitando, move para o final antes de adicionar output
            if current_pos < len(self.toPlainText()):
                self._move_cursor_to_end()
                cursor = self.textCursor()

            # Adiciona quebra de linha se necessário
            current_text = self.toPlainText()
            if current_text and not current_text.endswith('\n'):
                self.insertPlainText('\n')

            # Insere a saída LIMPA
            self.insertPlainText(cleaned_data.strip())
            
            # Novo prompt
            self.insertPlainText("\n")
            self._add_prompt()
            
            self._is_waiting_output = False

        except Exception as e:
            print(f"Erro em append_output: {e}")

    def keyPressEvent(self, event):
        """Handle de teclas - COMPLETAMENTE CORRIGIDO"""
        try:
            # Enter - executa comando
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if not self._is_waiting_output:
                    self._execute_command()
                event.accept()
                return
                
            # Backspace - protege prompt
            elif event.key() == Qt.Key_Backspace:
                cursor = self.textCursor()
                if cursor.position() <= self._input_start:
                    event.accept()
                    return
                else:
                    super().keyPressEvent(event)
                    
            # Setas para cima/baixo - histórico
            elif event.key() == Qt.Key_Up:
                self._navigate_history(-1)
                event.accept()
                return
            elif event.key() == Qt.Key_Down:
                self._navigate_history(1)
                event.accept()
                return
                
            # Setas esquerda/direita - protegem prompt
            elif event.key() in (Qt.Key_Left, Qt.Key_Right):
                cursor = self.textCursor()
                if event.key() == Qt.Key_Left and cursor.position() <= self._input_start:
                    event.accept()
                    return
                elif event.key() == Qt.Key_Right and cursor.position() < self._input_start:
                    event.accept()
                    return
                else:
                    super().keyPressEvent(event)

            # Ctrl+C - interrompe comando atual
            elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
                if self._shell_process and self._shell_process.state() == QProcess.Running:
                    self._shell_process.kill()
                    self.insertPlainText("^C\n")
                    self._add_prompt()
                event.accept()
                return
                
            # Ctrl+L - limpa terminal
            elif event.key() == Qt.Key_L and event.modifiers() == Qt.ControlModifier:
                self.clear()
                self._add_prompt()
                event.accept()
                return

            # Teclas normais
            else:
                super().keyPressEvent(event)
            
        except Exception as e:
            print(f"Erro no keyPressEvent: {e}")

    def _navigate_history(self, direction):
        """Navega pelo histórico de comandos"""
        if not self._command_history:
            return
            
        if self._history_index == -1:
            self._current_command = self._get_current_input()
            
        self._history_index += direction
        
        # Limita o índice ao histórico
        if self._history_index < 0:
            self._history_index = 0
        elif self._history_index >= len(self._command_history):
            self._history_index = len(self._command_history) - 1
            
        # Substitui o comando atual
        self._replace_current_input(self._command_history[self._history_index])

    def _get_current_input(self):
        """Obtém o texto atual do input"""
        full_text = self.toPlainText()
        return full_text[self._input_start:].strip()

    def _replace_current_input(self, new_text):
        """Substitui o texto atual do input"""
        cursor = self.textCursor()
        cursor.setPosition(self._input_start)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(new_text)
        self._move_cursor_to_end()

    def _execute_command(self):
        """Executa comando no shell - CORRIGIDO"""
        try:
            if not self._shell_process or self._shell_process.state() != QProcess.Running:
                self.insertPlainText("\n❌ Shell não está rodando\n")
                self._add_prompt()
                return

            # Obtém comando atual
            command = self._get_current_input()
            
            if command:
                # Adiciona ao histórico
                if command not in self._command_history:
                    self._command_history.append(command)
                self._history_index = -1
                
                # Envia comando
                self._shell_process.write(f"{command}\n".encode('utf-8'))
                self._is_waiting_output = True
                
                # Move para nova linha (o output será adicionado pelo append_output)
                self.insertPlainText("\n")
                
            else:
                # Comando vazio, apenas novo prompt
                self.insertPlainText("\n")
                self._add_prompt()
                
        except Exception as e:
            self.insertPlainText(f"\n❌ Erro ao executar comando: {e}\n")
            self._add_prompt()

    def restart_shell(self):
        """Reinicia o shell de forma segura"""
        try:
            # Para processo anterior
            if self._shell_process:
                if self._shell_process.state() == QProcess.Running:
                    self._shell_process.terminate()
                    self._shell_process.waitForFinished(1000)
                self._shell_process = None

            # Obtém referência do IDE
            ide = self.get_ide()
            if not ide:
                return

            # Cria novo processo
            ide.shell_process = QProcess(ide)
            ide.shell_process.readyReadStandardOutput.connect(ide.handle_terminal_output)
            ide.shell_process.readyReadStandardError.connect(ide.handle_terminal_error)

            # Comando baseado no OS
            if os.name == 'nt':
                ide.shell_process.start("cmd.exe")
            else:
                ide.shell_process.start("/bin/bash", ["-i"])

            # Atualiza referência
            self._shell_process = ide.shell_process
            
            # Configura prompt inicial após um delay
            QTimer.singleShot(500, self._setup_initial_prompt)

        except Exception as e:
            print(f"Erro ao reiniciar shell: {e}")

    def get_ide(self):
        """Encontra a instância do IDE pai"""
        parent = self.parent()
        while parent and not hasattr(parent, 'project_path'):
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                parent = None
        return parent

class DebugTerminal(TerminalTextEdit):
    """Terminal especializado para debug"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.debug_worker = None
        self.setStyleSheet("""
                                                                                DebugTerminal {
                                                                                                background-color: #1e1e1e;
                                                                                                color: #ce9178;
                                                                                                font-family: 'Consolas', monospace;
                                                                                                font-size: 11px;
                                                                                }
                                                                """)

        # Comandos específicos do debug
        self.debug_commands = {
            'n': 'next', 's': 'step', 'c': 'continue', 'q': 'quit',
            'l': 'list', 'p': 'print', 'pp': 'pprint', 'w': 'where',
            'b': 'break', 'cl': 'clear', 'r': 'return'
        }

    def start_debug(self, python_exec, file_path, project_path):
        self.clear()
        self.append_output(
            f"🐛 Iniciando debug: {os.path.basename(file_path)}\n")
        self.append_output(
            "Comandos: n(next), s(step), c(continue), q(quit), l(list), p(print), b(break)\n")
        self.append_output("-" * 50 + "\n")

        self.debug_worker = DebugWorker(
            python_exec, file_path, project_path)
        self.debug_worker.output_received.connect(
            self.append_output)
        self.debug_worker.finished.connect(
            self.on_debug_finished)
        self.debug_worker.start()

        self.input_start = len(self.toPlainText())

    def on_debug_finished(self, exit_code):
        self.append_output(
            f"\n🔚 Sessão de debug finalizada (código: {exit_code})\n")
        self.debug_worker = None

    def execute_command(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        command_line = cursor.selectedText().strip()

        if command_line and self.debug_worker:
            clean_command = command_line.strip()
            if clean_command in self.debug_commands:
                full_command = self.debug_commands[clean_command]
                self.append_output(
                    f"Executando: {full_command}\n")
                self.debug_worker.send_command(
                    full_command)
            else:
                self.debug_worker.send_command(
                    clean_command)

            self.append_output("\n(Pdb) ")
        else:
            self.append_output("\n(Pdb) ")

    def keyPressEvent(self, event):
        """Manipula eventos de teclado incluindo folding"""
        # Atalhos para folding
        if event.modifiers() == Qt.AltModifier:
            if event.key() == Qt.Key_Right:
                self.expand_all_folds()
                event.accept()
                return
            elif event.key() == Qt.Key_Left:
                self.collapse_all_folds()
                event.accept()
                return
        
        # Atalho para toggle folding (Alt+L)
        elif event.modifiers() == Qt.AltModifier and event.key() == Qt.Key_L:
            cursor = self.textCursor()
            block = cursor.block()
            if self.folding_area.is_block_foldable(block):
                self.folding_area.toggle_fold(block)
                event.accept()
                return
        
        super().keyPressEvent(event)

    def stop_debug(self):
        if self.debug_worker:
            self.debug_worker.stop()
            self.debug_worker.wait(1000)
            self.append_output(
                "\n⏹️ Debug interrompido\n")
