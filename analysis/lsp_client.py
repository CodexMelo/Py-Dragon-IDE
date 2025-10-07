from PySide6.QtCore import QProcess, QThread, Signal
import json
import subprocess






# ===== DIÁLOGO DO GESTOR DE VERSÕES =====
class LSPClient:
    """Cliente LSP para python-lsp-server (pylsp) - VERSÃO CORRIGIDA"""
    
    def __init__(self, workspace_path=None):
        self.workspace_path = workspace_path or os.getcwd()
        self.process = None
        self.seq_num = 0
        self.pending_requests = {}
        self.message_queue = Queue()
        self.initialized = False
        self.capabilities = {}
        
        # Configurar logging
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Configura sistema de logging para LSP"""
        logger = logging.getLogger('LSPClient')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def start_server(self):
        """Inicia o servidor LSP - VERSÃO CORRIGIDA"""
        try:
            self.logger.info("🔄 Iniciando python-lsp-server...")
            
            # Verificar se pylsp está instalado
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pylsp", "--help"], 
                    capture_output=True, 
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, result.args)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                self.logger.error("❌ python-lsp-server não encontrado. Instale com: pip install python-lsp-server")
                return False

            # Iniciar processo CORRETAMENTE
            self.process = subprocess.Popen(
                [sys.executable, "-m", "pylsp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                universal_newlines=False  # Mudar para False para lidar com bytes
            )
            
            # Iniciar threads para leitura
            self._start_reader_threads()
            
            # Inicializar LSP
            return self._initialize()
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao iniciar LSP server: {e}")
            return False

    def _start_reader_threads(self):
        """Inicia threads para ler stdout e stderr - VERSÃO CORRIGIDA"""
        def read_stdout():
            buffer = b""
            while self.process and self.process.poll() is None:
                try:
                    # Ler dados binários
                    data = self.process.stdout.read(1)
                    if data:
                        buffer += data
                        if buffer.endswith(b'\r\n\r\n'):
                            # Processar mensagem completa
                            try:
                                message = buffer.decode('utf-8').strip()
                                if message:
                                    self._process_message(message)
                            except UnicodeDecodeError:
                                self.logger.error("❌ Erro decodificando mensagem UTF-8")
                            buffer = b""
                    elif not data and buffer:
                        # Tentar processar buffer residual
                        try:
                            message = buffer.decode('utf-8').strip()
                            if message:
                                self._process_message(message)
                        except UnicodeDecodeError:
                            pass
                        buffer = b""
                except Exception as e:
                    self.logger.error(f"Erro lendo stdout: {e}")
                    break

        def read_stderr():
            while self.process and self.process.poll() is None:
                try:
                    line = self.process.stderr.readline()
                    if line:
                        self.logger.warning(f"LSP stderr: {line.strip()}")
                except Exception as e:
                    self.logger.error(f"Erro lendo stderr: {e}")
                    break

        Thread(target=read_stdout, daemon=True).start()
        Thread(target=read_stderr, daemon=True).start()

    def _process_message(self, message):
        """Processa mensagens do servidor LSP - VERSÃO CORRIGIDA"""
        try:
            if not message.strip():
                return
                
            # Extrair conteúdo JSON (pular headers LSP)
            if message.startswith('Content-Length:'):
                lines = message.split('\r\n')
                for line in lines:
                    if line and not line.startswith('Content-Length:') and not line.startswith('Content-Type:'):
                        try:
                            data = json.loads(line)
                            self._handle_json_message(data)
                        except json.JSONDecodeError:
                            continue
            else:
                # Tentar processar como JSON direto
                try:
                    data = json.loads(message)
                    self._handle_json_message(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"❌ Erro decodificando JSON: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Erro processando mensagem: {e}")

    def _handle_json_message(self, data):
        """Manipula mensagem JSON do LSP"""
        self.logger.debug(f"📨 Mensagem recebida: {data.get('method', 'Unknown')}")
        
        # Processar resposta para requisições pendentes
        if 'id' in data:
            request_id = data['id']
            if request_id in self.pending_requests:
                callback = self.pending_requests.pop(request_id)
                if callback:
                    callback(data)
        
        # Processar notificações
        elif 'method' in data:
            self._handle_notification(data)

    def _handle_notification(self, data):
        """Manipula notificações do servidor"""
        method = data.get('method')
        params = data.get('params', {})
        
        if method == 'textDocument/publishDiagnostics':
            self._handle_diagnostics(params)
        elif method == 'window/showMessage':
            self._handle_show_message(params)
        elif method == 'telemetry/event':
            self.logger.debug(f"Telemetria: {params}")

    def _handle_diagnostics(self, params):
        """Manipula diagnósticos (erros, avisos)"""
        uri = params.get('uri', '')
        diagnostics = params.get('diagnostics', [])
        
        # Converter URI para caminho de arquivo
        file_path = self._uri_to_path(uri)
        
        self.logger.info(f"🔍 Diagnósticos para {file_path}: {len(diagnostics)} problemas")
        
        # Emitir sinais ou processar diagnósticos
        for diagnostic in diagnostics:
            self._process_diagnostic(file_path, diagnostic)

    def _process_diagnostic(self, file_path, diagnostic):
        """Processa um diagnóstico individual"""
        try:
            range_info = diagnostic.get('range', {})
            start = range_info.get('start', {})
            line = start.get('line', 0) + 1  # LSP usa 0-based, IDE usa 1-based
            character = start.get('character', 0) + 1
            
            severity = diagnostic.get('severity', 1)
            message = diagnostic.get('message', '')
            source = diagnostic.get('source', 'pylsp')
            code = diagnostic.get('code', '')
            
            # Mapear severidade
            severity_map = {
                1: 'ERROR',
                2: 'WARNING', 
                3: 'INFO',
                4: 'HINT'
            }
            severity_str = severity_map.get(severity, 'INFO')
            
            self.logger.debug(f"📋 {severity_str} em {file_path}:{line}:{character} - {message}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro processando diagnóstico: {e}")

    def _handle_show_message(self, params):
        """Manipula mensagens do servidor"""
        message_type = params.get('type', 3)
        message = params.get('message', '')
        
        type_map = {
            1: 'ERROR',
            2: 'WARNING',
            3: 'INFO',
            4: 'LOG'
        }
        
        log_level = type_map.get(message_type, 'INFO')
        self.logger.info(f"💬 LSP {log_level}: {message}")

    def _initialize(self):
        """Inicializa conexão com servidor LSP"""
        initialize_params = {
            "processId": os.getpid(),
            "rootPath": self.workspace_path,
            "rootUri": self._path_to_uri(self.workspace_path),
            "capabilities": {
                "workspace": {
                    "configuration": True,
                    "workspaceFolders": True
                },
                "textDocument": {
                    "completion": {
                        "completionItem": {
                            "snippetSupport": True
                        }
                    },
                    "hover": {
                        "contentFormat": ["plaintext", "markdown"]
                    },
                    "signatureHelp": {
                        "signatureInformation": {
                            "parameterInformation": {
                                "labelOffsetSupport": True
                            }
                        }
                    }
                }
            },
            "workspaceFolders": [
                {
                    "uri": self._path_to_uri(self.workspace_path),
                    "name": os.path.basename(self.workspace_path)
                }
            ]
        }
        
        response = self.send_request("initialize", initialize_params)
        if response and not response.get('error'):
            self.capabilities = response.get('result', {}).get('capabilities', {})
            self.initialized = True
            
            # Enviar notificação initialized
            self.send_notification("initialized", {})
            
            self.logger.info("✅ LSP inicializado com sucesso")
            return True
        
        self.logger.error("❌ Falha na inicialização do LSP")
        return False

    def send_request(self, method, params, callback=None):
        """Envia requisição para servidor LSP - VERSÃO CORRIGIDA"""
        if not self.process:
            return None
            
        self.seq_num += 1
        request_id = self.seq_num
        
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        # Registrar callback se fornecido
        if callback:
            self.pending_requests[request_id] = callback
        
        try:
            json_message = json.dumps(message, ensure_ascii=False)
            content = f"Content-Length: {len(json_message.encode('utf-8'))}\r\n\r\n{json_message}"
            
            # Escrever bytes no stdin
            self.process.stdin.write(content.encode('utf-8'))
            self.process.stdin.flush()
            
            self.logger.debug(f"📤 Requisição enviada: {method}")
            
            # Para requisições síncronas, aguardar resposta
            if not callback:
                return self._wait_for_response(request_id)
                
        except Exception as e:
            self.logger.error(f"❌ Erro enviando requisição: {e}")
            if request_id in self.pending_requests:
                self.pending_requests.pop(request_id)
        
        return None

    def _wait_for_response(self, request_id, timeout=10):
        """Aguarda resposta para requisição síncrona"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Verificar se resposta chegou
            if request_id not in self.pending_requests:
                return None
            
            time.sleep(0.1)
        
        self.logger.warning(f"⏰ Timeout esperando resposta para requisição {request_id}")
        return None

    def send_notification(self, method, params):
        """Envia notificação para servidor LSP - VERSÃO CORRIGIDA"""
        if not self.process:
            return
            
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        try:
            json_message = json.dumps(message, ensure_ascii=False)
            content = f"Content-Length: {len(json_message.encode('utf-8'))}\r\n\r\n{json_message}"
            
            # Escrever bytes no stdin
            self.process.stdin.write(content.encode('utf-8'))
            self.process.stdin.flush()
            
            self.logger.debug(f"📤 Notificação enviada: {method}")
        except Exception as e:
            self.logger.error(f"❌ Erro enviando notificação: {e}")

    def did_open(self, file_path, text, language_id="python"):
        """Notifica que arquivo foi aberto"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": text
            }
        }
        self.send_notification("textDocument/didOpen", params)

    def did_change(self, file_path, text, version=1):
        """Notifica que arquivo foi modificado"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri,
                "version": version
            },
            "contentChanges": [
                {
                    "text": text
                }
            ]
        }
        self.send_notification("textDocument/didChange", params)

    def did_close(self, file_path):
        """Notifica que arquivo foi fechado"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            }
        }
        self.send_notification("textDocument/didClose", params)

    def get_completions(self, file_path, line, character, callback=None):
        """Obtém sugestões de autocomplete"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            },
            "position": {
                "line": line - 1,  # Converter para 0-based
                "character": character - 1
            },
            "context": {
                "triggerKind": 1  # Invoked
            }
        }
        
        return self.send_request("textDocument/completion", params, callback)

    def get_hover(self, file_path, line, character, callback=None):
        """Obtém informação de hover"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            },
            "position": {
                "line": line - 1,
                "character": character - 1
            }
        }
        
        return self.send_request("textDocument/hover", params, callback)

    def get_signature_help(self, file_path, line, character, callback=None):
        """Obtém ajuda de assinatura"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            },
            "position": {
                "line": line - 1,
                "character": character - 1
            }
        }
        
        return self.send_request("textDocument/signatureHelp", params, callback)

    def get_document_symbols(self, file_path, callback=None):
        """Obtém símbolos do documento"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            }
        }
        
        return self.send_request("textDocument/documentSymbol", params, callback)

    def format_document(self, file_path, callback=None):
        """Formata documento"""
        uri = self._path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri
            },
            "options": {
                "tabSize": 4,
                "insertSpaces": True
            }
        }
        
        return self.send_request("textDocument/formatting", params, callback)

    def _path_to_uri(self, path):
        """Converte caminho para URI de forma robusta"""
        try:
            if not path:
                return ""
                
            # Obter caminho absoluto
            abs_path = os.path.abspath(path)
            
            # Normalizar para formato URI
            if os.name == 'nt':  # Windows
                # Remover drive letter colon e substituir backslashes
                normalized_path = abs_path.replace('\\', '/')
                # Se tiver drive letter (ex: C:/), formatar corretamente
                if ':' in normalized_path:
                    # Formato: file:///C:/Users/...
                    return f"file:///{normalized_path}"
                else:
                    return f"file:///{normalized_path}"
            else:  # Linux/Mac
                # Formato: file:///home/user/...
                return f"file://{abs_path}"
                
        except Exception as e:
            self.logger.error(f"❌ Erro convertendo path para URI: {e}")
            # Fallback seguro
            return f"file://{os.path.abspath(path or '')}"

    def _uri_to_path(self, uri):
        """Converte URI para caminho de forma robusta"""
        try:
            if not uri or not uri.startswith('file://'):
                return uri or ""
                
            path = uri[7:]  # Remove 'file://'
            
            if os.name == 'nt':  # Windows
                # Remover barra inicial se existir: /C:/ → C:/
                if path.startswith('/') and len(path) > 2 and path[2] == ':':
                    path = path[1:]
                return path.replace('/', '\\')
            else:  # Linux/Mac
                return path
                
        except Exception as e:
            self.logger.error(f"❌ Erro convertendo URI para path: {e}")
            return uri.replace('file://', '') if uri else ""


    def shutdown(self):
        """Desliga servidor LSP"""
        if self.initialized:
            self.send_request("shutdown", {})
            self.send_notification("exit", {})
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                    self.process.wait(timeout=2)
                except:
                    pass
            
        self.initialized = False
        self.logger.info("🔚 LSP client finalizado")


class LSPManager:
    """Gerenciador LSP para o IDE"""
    
    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.lsp_client = None
        self.workspace_path = None
        self.open_documents = {}
        
    def initialize(self, workspace_path):
        """Inicializa LSP para workspace"""
        try:
            self.workspace_path = workspace_path
            self.lsp_client = LSPClient(workspace_path)
            
            if self.lsp_client.start_server():
                if hasattr(self.ide, 'statusBar'):
                    self.ide.statusBar().showMessage("✅ LSP inicializado com sucesso", 3000)
                return True
            else:
                if hasattr(self.ide, 'statusBar'):
                    self.ide.statusBar().showMessage("❌ Falha ao inicializar LSP", 3000)
                return False
                
        except Exception as e:
            print(f"❌ Erro inicializando LSP: {e}")
            return False
    
    def open_document(self, file_path, content):
        """Abre documento no LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            self.lsp_client.did_open(file_path, content)
            self.open_documents[file_path] = content
    
    def update_document(self, file_path, content):
        """Atualiza documento no LSP"""
        if (self.lsp_client and self.lsp_client.initialized and 
            file_path in self.open_documents):
            
            version = self.open_documents.get(f"{file_path}_version", 1) + 1
            self.lsp_client.did_change(file_path, content, version)
            self.open_documents[file_path] = content
            self.open_documents[f"{file_path}_version"] = version
    
    def close_document(self, file_path):
        """Fecha documento no LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            self.lsp_client.did_close(file_path)
            if file_path in self.open_documents:
                del self.open_documents[file_path]
    
    def get_completions(self, file_path, line, column, callback=None):
        """Obtém completions via LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            return self.lsp_client.get_completions(file_path, line, column, callback)
        return None
    
    def get_hover_info(self, file_path, line, column, callback=None):
        """Obtém informação de hover via LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            return self.lsp_client.get_hover(file_path, line, column, callback)
        return None
    
    def format_document(self, file_path, callback=None):
        """Formata documento via LSP"""
        if self.lsp_client and self.lsp_client.initialized:
            return self.lsp_client.format_document(file_path, callback)
        return None
    
    def shutdown(self):
        """Finaliza LSP"""
        if self.lsp_client:
            self.lsp_client.shutdown()
