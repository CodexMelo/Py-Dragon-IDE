import os
import sys
import re
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import QThread, Signal, Qt, QProcess 
from PySide6.QtGui import QFont, QTextCursor, QKeyEvent

class DebugTerminal(QPlainTextEdit):
    """Terminal especializado para debug - versão completa"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.debug_worker = None
        self.input_start = 0
        
        # Comandos específicos do debug
        self.debug_commands = {
            'n': 'next', 's': 'step', 'c': 'continue', 'q': 'quit',
            'l': 'list', 'p': 'print', 'pp': 'pprint', 'w': 'where',
            'b': 'break', 'cl': 'clear', 'r': 'return', 'h': 'help'
        }
        
        self.setup_debug_terminal()

    def setup_debug_terminal(self):
        """Configura o terminal de debug"""
        self.setFont(QFont("Monospace", 10))
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ce9178;
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        self._add_prompt()

    def _add_prompt(self):
        """Adiciona prompt de debug"""
        prompt = "(Pdb) "
        self.insertPlainText(prompt)
        self._input_start = len(self.toPlainText())
        self._move_cursor_to_end()

    def _move_cursor_to_end(self):
        """Move cursor para o final"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

    def append_output(self, text):
        """Adiciona saída ao terminal"""
        try:
            # Limpa códigos ANSI básicos
            cleaned_text = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
            
            self._move_cursor_to_end()
            self.insertPlainText(cleaned_text)
            
            # Se não terminar com newline, adiciona
            if not cleaned_text.endswith('\n'):
                self.insertPlainText('\n')
                
            self._add_prompt()
            
        except Exception as e:
            print(f"Erro em append_output: {e}")

    def _get_current_input(self):
        """Obtém comando atual"""
        full_text = self.toPlainText()
        return full_text[self._input_start:].strip()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle de teclas para debug"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._execute_debug_command()
            event.accept()
            return
            
        elif event.key() == Qt.Key_Backspace:
            cursor = self.textCursor()
            if cursor.position() <= self._input_start:
                event.accept()
                return
            else:
                super().keyPressEvent(event)
                return
                
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self.stop_debug()
            event.accept()
            return
            
        else:
            super().keyPressEvent(event)

    def _execute_debug_command(self):
        """Executa comando de debug"""
        try:
            command = self._get_current_input()
            
            if not command:
                self.insertPlainText("\n")
                self._add_prompt()
                return
                
            if not self.debug_worker:
                self.insertPlainText("\n❌ Debug não está ativo\n")
                self._add_prompt()
                return

            # Processa comando abreviado
            clean_command = command.strip()
            if clean_command in self.debug_commands:
                full_command = self.debug_commands[clean_command]
                self.insertPlainText(f"\nExecutando: {full_command}\n")
                self.debug_worker.send_command(full_command)
            else:
                self.insertPlainText(f"\nExecutando: {clean_command}\n")
                self.debug_worker.send_command(clean_command)

        except Exception as e:
            self.insertPlainText(f"\n❌ Erro: {e}\n")
            self._add_prompt()

    def start_debug(self, python_exec, file_path, project_path):
        """Inicia sessão de debug"""
        self.clear()
        self.insertPlainText(f"🐛 Iniciando debug: {os.path.basename(file_path)}\n")
        self.insertPlainText("Comandos: n(next), s(step), c(continue), q(quit), l(list), p(print), b(break)\n")
        self.insertPlainText("-" * 50 + "\n")

        self.debug_worker = DebugWorker(python_exec, file_path, project_path)
        self.debug_worker.output_received.connect(self.append_output)
        self.debug_worker.finished.connect(self.on_debug_finished)
        self.debug_worker.start()

    def on_debug_finished(self, exit_code):
        """Callback quando debug termina"""
        self.insertPlainText(f"\n🔚 Sessão de debug finalizada (código: {exit_code})\n")
        self.debug_worker = None
        self._add_prompt()

    def stop_debug(self):
        """Para a sessão de debug"""
        if self.debug_worker:
            self.debug_worker.stop()
            self.insertPlainText("\n⏹️ Debug interrompido\n")
            self.debug_worker = None
        self._add_prompt()


class DebugWorker(QThread):
    """Thread para executar debugger"""
    output_received = Signal(str)
    finished = Signal(int)

    def __init__(self, python_exec, file_path, project_path):
        super().__init__()
        self.python_exec = python_exec
        self.file_path = file_path
        self.project_path = project_path
        self._process = None
        self._is_running = True

    def run(self):
        try:
            # Inicia processo de debug
            self._process = QProcess()
            self._process.readyReadStandardOutput.connect(self._handle_output)
            self._process.readyReadStandardError.connect(self._handle_error)
            self._process.finished.connect(self._handle_finished)

            # Comando para iniciar debug
            cmd = [self.python_exec, "-m", "pdb", self.file_path]
            self._process.start(cmd[0], cmd[1:])
            
            if not self._process.waitForStarted(5000):
                self.output_received.emit("❌ Falha ao iniciar debugger\n")
                return

            # Mantém a thread rodando
            while self._is_running and self._process.state() == QProcess.Running:
                self.msleep(100)

        except Exception as e:
            self.output_received.emit(f"❌ Erro no debug: {e}\n")

    def send_command(self, command):
        """Envia comando para o debugger"""
        if self._process and self._process.state() == QProcess.Running:
            self._process.write(f"{command}\n".encode())

    def stop(self):
        """Para o debugger"""
        self._is_running = False
        if self._process:
            self._process.terminate()
            if not self._process.waitForFinished(1000):
                self._process.kill()

    def _handle_output(self):
        """Processa saída padrão"""
        if self._process:
            data = self._process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if data.strip():
                self.output_received.emit(data)

    def _handle_error(self):
        """Processa saída de erro"""
        if self._process:
            data = self._process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if data.strip():
                self.output_received.emit(f"❌ {data}")

    def _handle_finished(self, exit_code):
        """Callback quando processo termina"""
        self.finished.emit(exit_code)
