from PySide6.QtCore import QThread, Signal
import subprocess



class DebugWorker(QThread):
    """Worker para execução de debug em thread separada"""
    output_received = Signal(str)
    finished = Signal(int)
    error_occurred = Signal(str)

    def __init__(self, python_exec, file_path, project_path):
        super().__init__()
        self.python_exec = python_exec
        self.file_path = file_path
        self.project_path = project_path
        self.process = None
        self._is_running = True
        self._mutex = threading.Lock()
        self._command_queue = Queue()

    def stop(self):
        """Para a execução do debug de forma segura"""
        with self._mutex:
            self._is_running = False
            
        if self.process:
            try:
                self.process.terminate()
                if not self.process.waitForFinished(1000):
                    self.process.kill()
            except Exception as e:
                print(f"Erro ao parar processo: {e}")
                
        self.quit()
        self.wait(2000)

    def run(self):
        """Executa o debug em thread separada"""
        try:
            with self._mutex:
                if not self._is_running:
                    return
                    
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.on_finished)
            self.process.errorOccurred.connect(self.on_error)

            # Comando para debug interativo
            cmd = [self.python_exec, "-m", "pdb", self.file_path]

            # Define working directory
            working_dir = self.project_path or os.path.dirname(self.file_path)
            self.process.setWorkingDirectory(working_dir)

            # Define variáveis de ambiente se necessário
            env = QProcessEnvironment.systemEnvironment()
            self.process.setProcessEnvironment(env)

            self.output_received.emit(f"🚀 Iniciando debug: {os.path.basename(self.file_path)}")
            self.output_received.emit(f"📁 Diretório: {working_dir}")
            self.output_received.emit(f"🐍 Python: {self.python_exec}")
            self.output_received.emit("-" * 50)

            self.process.start(cmd[0], cmd[1:])

            # Aguarda o processo iniciar
            if not self.process.waitForStarted(5000):
                self.error_occurred.emit("❌ Falha ao iniciar processo de debug")
                return

            # Loop principal para processar comandos
            while True:
                with self._mutex:
                    if not self._is_running:
                        break
                    if self.process.state() != QProcess.Running:
                        break

                # Processa comandos da fila
                try:
                    command = self._command_queue.get_nowait()
                    if command:
                        self.process.write(f"{command}\n".encode('utf-8'))
                except Empty:
                    pass

                self.msleep(50)

        except Exception as e:
            error_msg = f"❌ Erro no debug: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.output_received.emit(error_msg)

    def handle_stdout(self):
        """Processa saída padrão"""
        with self._mutex:
            if not self._is_running:
                return
                
        try:
            data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if data.strip():
                self.output_received.emit(data)
        except Exception as e:
            print(f"Erro ao processar stdout: {e}")

    def handle_stderr(self):
        """Processa erro padrão"""
        with self._mutex:
            if not self._is_running:
                return
                
        try:
            data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if data.strip():
                # Marca como erro
                error_text = f"[ERRO] {data}"
                self.output_received.emit(error_text)
        except Exception as e:
            print(f"Erro ao processar stderr: {e}")

    def on_finished(self, exit_code, exit_status):
        """Processa término do processo"""
        with self._mutex:
            if self._is_running:
                self.output_received.emit(f"\n🔚 Processo de debug finalizado (código: {exit_code})")
                self.finished.emit(exit_code)

    def on_error(self, error):
        """Processa erro do processo"""
        error_msg = f"❌ Erro no processo: {error.name()}"
        self.error_occurred.emit(error_msg)
        self.output_received.emit(error_msg)

    def send_command(self, command):
        """Envia comando para o processo de debug"""
        with self._mutex:
            if not self._is_running or not self.process or self.process.state() != QProcess.Running:
                return False
                
        try:
            # Adiciona quebra de linha se necessário
            if not command.endswith('\n'):
                command += '\n'
                
            self._command_queue.put(command)
            return True
        except Exception as e:
            print(f"Erro ao enviar comando: {e}")
            return False

    def get_state(self):
        """Retorna o estado atual do worker"""
        with self._mutex:
            if not self._is_running:
                return "stopped"
            if not self.process:
                return "not_started"
            return "running" if self.process.state() == QProcess.Running else "finished"



class LinterWorker(QThread):
    """Worker para execução de linter em background"""
    finished = Signal(dict, list)
    
    def __init__(self, file_path, python_exec, project_path):
        super().__init__()
        self.file_path = file_path
        self.python_exec = python_exec
        self.project_path = project_path
        self._is_running = True
        self._mutex = threading.Lock()

    def stop(self):
        """Para a thread de forma segura"""
        with self._mutex:
            self._is_running = False
        self.quit()
        self.wait(2000)

    def run(self):
        """Executa análise de linting em thread separada"""
        if not self._is_running or not self.file_path:
            return

        errors = {}
        lint_messages = []

        try:
            # Tenta pylint primeiro com enables corrigidos
            pylint_cmd = [
                self.python_exec, '-m', 'pylint',
                '--output-format=json',
                '--reports=n',
                '--disable=all',
                '--enable=E,W,fatal',
                self.file_path
            ]

            cwd = self.project_path if self.project_path else os.path.dirname(self.file_path)
            result = subprocess.run(
                pylint_cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                timeout=5
            )

            # Verifica se deve continuar
            with self._mutex:
                if not self._is_running:
                    return

            if result.returncode in [0, 1, 2, 4, 8, 16, 32] and result.stdout.strip():
                try:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        # Verifica se deve continuar a cada linha
                        with self._mutex:
                            if not self._is_running:
                                return
                                
                        if line.strip():
                            try:
                                issue = json.loads(line.strip())
                                if 'line' in issue and issue['line'] > 0:
                                    line_num = issue['line'] - 1
                                    msg = issue.get('message', 'No message')
                                    symbol = issue.get('symbol', 'unknown')
                                    msg_type = issue.get('type', 'warning')
                                    error_type = 'error' if msg_type == 'error' else 'warning'

                                    if line_num not in errors:
                                        errors[line_num] = []
                                    errors[line_num].append({
                                        'type': error_type,
                                        'msg': msg,
                                        'symbol': symbol
                                    })
                                    lint_messages.append(f"Line {issue['line']}: {msg} ({symbol})")
                            except json.JSONDecodeError:
                                continue
                except json.JSONDecodeError:
                    pass

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Linter error: {e}")

        # Verifica final antes de emitir
        with self._mutex:
            if self._is_running:
                self.finished.emit(errors, lint_messages)
