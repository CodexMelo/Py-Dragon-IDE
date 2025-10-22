# settings_manager.py
import os
import json
import sys
import subprocess
from pathlib import Path

class SettingsManager:
    """Gerenciador SIMPLES de configurações - focado no Python selecionado"""
    
    def __init__(self, app_name="PyDragonStudio"):
        self.app_name = app_name
        
        # Diretório de dados
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', Path.home()))
        else:  # Linux/Mac
            base_dir = Path.home() / '.config'
        
        self.data_dir = base_dir / self.app_name
        self.settings_file = self.data_dir / "python_settings.json"
        
        # Garantir que o diretório existe
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurações padrão
        self.default_settings = {
            "selected_python": None,  # Caminho do Python selecionado
            "python_versions": [],    # Histórico de versões usadas
            "last_vm_python": None,   # Último Python usado para VM
            "project_python_mapping": {}  # Mapeamento projeto -> Python
        }
        
        # Carregar configurações
        self.load_settings()
    
    def debug_log(self, message, level="INFO"):
        """Sistema de logging simples para SettingsManager"""
        levels = {
            "INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️",
            "ERROR": "❌", "DEBUG": "🐛"
        }
        icon = levels.get(level, "🔵")
        print(f"{icon} [SettingsManager] {message}")

    def get_system_specific_python_paths(self):
        """Retorna caminhos específicos do sistema para Python"""
        python_paths = []
        
        if os.name == 'nt':  # Windows
            # Caminhos comuns no Windows
            common_patterns = [
                r"C:\Python3*\python.exe",
                r"C:\Program Files\Python3*\python.exe", 
                r"C:\Users\*\AppData\Local\Programs\Python\Python3*\python.exe",
                r"C:\Python\Python3*\python.exe"
            ]
        else:  # Linux/Mac
            common_patterns = [
                "/usr/bin/python3*",
                "/usr/local/bin/python3*",
                "/opt/homebrew/bin/python3*",
                os.path.expanduser("~/.pyenv/versions/*/bin/python"),
                "/usr/bin/python*",
                "/opt/python*/bin/python*"
            ]
        
        for pattern in common_patterns:
            try:
                for path in Path().glob(pattern):
                    if path.is_file() and os.access(path, os.X_OK):
                        python_paths.append(str(path.absolute()))
            except Exception:
                continue
        
        return python_paths

    def load_settings(self):
        """Carrega configurações do arquivo"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Mesclar com configurações padrão
                    for key, value in loaded_settings.items():
                        if key in self.default_settings:
                            self.default_settings[key] = value
                self.debug_log(f"Configurações carregadas: {self.settings_file}", "SUCCESS")
        except Exception as e:
            self.debug_log(f"Erro ao carregar configurações: {e}", "ERROR")

    def save_settings(self):
        """Salva configurações no arquivo"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.default_settings, f, indent=2, ensure_ascii=False)
            self.debug_log(f"Configurações salvas: {self.settings_file}", "SUCCESS")
            return True
        except Exception as e:
            self.debug_log(f"Erro ao salvar configurações: {e}", "ERROR")
            return False

    # ===== MÉTODOS PARA PYTHON =====
    
    def set_selected_python(self, python_path):
        """Define o Python selecionado e salva no histórico"""
        if python_path and os.path.exists(python_path):
            self.default_settings["selected_python"] = python_path
            
            # Adicionar ao histórico (sem duplicatas)
            if python_path not in self.default_settings["python_versions"]:
                self.default_settings["python_versions"].insert(0, python_path)
                # Manter apenas as últimas 10 versões
                self.default_settings["python_versions"] = self.default_settings["python_versions"][:10]
            
            self.save_settings()
            self.debug_log(f"Python selecionado: {python_path}", "SUCCESS")
            return True
        self.debug_log(f"Python inválido: {python_path}", "ERROR")
        return False

    def get_selected_python(self):
        """Obtém o Python selecionado"""
        python_path = self.default_settings["selected_python"]
        # Verificar se ainda existe
        if python_path and os.path.exists(python_path):
            return python_path
        return None

    def get_python_versions(self):
        """Obtém histórico de versões Python (apenas as que ainda existem)"""
        valid_versions = []
        for version in self.default_settings["python_versions"]:
            if os.path.exists(version):
                valid_versions.append(version)
        
        # Atualizar a lista removendo versões inválidas
        if len(valid_versions) != len(self.default_settings["python_versions"]):
            self.default_settings["python_versions"] = valid_versions
            self.save_settings()
        
        return valid_versions

    def set_last_vm_python(self, python_path):
        """Define o último Python usado para criar VM"""
        if python_path and os.path.exists(python_path):
            self.default_settings["last_vm_python"] = python_path
            self.save_settings()
            self.debug_log(f"Python para VM definido: {python_path}", "SUCCESS")
            return True
        return False

    def get_last_vm_python(self):
        """Obtém o último Python usado para criar VM"""
        python_path = self.default_settings["last_vm_python"]
        if python_path and os.path.exists(python_path):
            return python_path
        return None

    def map_project_python(self, project_path, python_path):
        """Mapeia um projeto a um Python específico"""
        if project_path and python_path and os.path.exists(python_path):
            self.default_settings["project_python_mapping"][project_path] = python_path
            self.save_settings()
            self.debug_log(f"Python mapeado para projeto {project_path}: {python_path}", "SUCCESS")
            return True
        return False

    def get_project_python(self, project_path):
        """Obtém o Python mapeado para um projeto"""
        return self.default_settings["project_python_mapping"].get(project_path)

    # ===== MÉTODOS ÚTEIS =====
    
    def get_python_version_info(self, python_path):
        """Obtém informações da versão do Python"""
        try:
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version_info = result.stdout.strip()
                self.debug_log(f"Versão Python {python_path}: {version_info}", "INFO")
                return version_info
        except Exception as e:
            self.debug_log(f"Erro ao obter versão do Python {python_path}: {e}", "ERROR")
        return "Versão desconhecida"

    def get_available_pythons(self):
        """Detecta Pythons disponíveis no sistema"""
        python_paths = []
        
        # Python atual
        python_paths.append(sys.executable)
        
        # Verificar diretórios comuns
        common_paths = []
        
        if os.name == 'nt':  # Windows
            common_paths = [
                r"C:\Python3*",
                r"C:\Program Files\Python3*", 
                r"C:\Users\*\AppData\Local\Programs\Python\Python3*"
            ]
        else:  # Linux/Mac
            common_paths = [
                "/usr/bin/python3*",
                "/usr/local/bin/python3*",
                "/opt/homebrew/bin/python3*",
                os.path.expanduser("~/.pyenv/versions/*/bin/python")
            ]
        
        for pattern in common_paths:
            for path in Path().glob(pattern):
                if path.is_file() and os.access(path, os.X_OK):
                    python_paths.append(str(path))
        
        # Remover duplicatas e verificar existência
        unique_paths = []
        seen = set()
        for path in python_paths:
            if path not in seen and os.path.exists(path):
                unique_paths.append(path)
                seen.add(path)
        
        self.debug_log(f"Encontrados {len(unique_paths)} Pythons disponíveis", "INFO")
        return unique_paths

    def detect_and_save_system_python(self):
        """Detecta e salva Python do sistema de forma robusta"""
        try:
            # Tentativas em ordem de prioridade
            python_candidates = []
            
            # 1. Python do sistema (sys.executable)
            if sys.executable and os.path.exists(sys.executable):
                python_candidates.append(sys.executable)
                self.debug_log(f"Python do sistema: {sys.executable}", "INFO")
            
            # 2. Python no PATH
            for python_name in ['python3', 'python', 'python3.11', 'python3.10', 'python3.9', 'python3.8']:
                try:
                    if os.name == 'nt':
                        result = subprocess.run(
                            ['where', python_name], 
                            capture_output=True, 
                            text=True,
                            timeout=5
                        )
                    else:
                        result = subprocess.run(
                            ['which', python_name], 
                            capture_output=True, 
                            text=True,
                            timeout=5
                        )
                    
                    if result.returncode == 0:
                        python_path = result.stdout.strip().split('\n')[0]
                        if python_path and os.path.exists(python_path):
                            python_candidates.append(python_path)
                            self.debug_log(f"Python no PATH: {python_path}", "INFO")
                except Exception as e:
                    self.debug_log(f"Erro ao buscar {python_name}: {e}", "DEBUG")
            
            # 3. Locais comuns
            common_paths = []
            if os.name == 'nt':  # Windows
                common_paths = [
                    'C:\\Python39\\python.exe',
                    'C:\\Python310\\python.exe', 
                    'C:\\Python311\\python.exe',
                    'C:\\Program Files\\Python39\\python.exe',
                    'C:\\Program Files\\Python310\\python.exe',
                    'C:\\Program Files\\Python311\\python.exe'
                ]
            else:  # Linux/Mac
                common_paths = [
                    '/usr/bin/python3',
                    '/usr/bin/python',
                    '/usr/local/bin/python3',
                    '/usr/local/bin/python',
                    '/opt/homebrew/bin/python3',
                    '/opt/homebrew/bin/python'
                ]
            
            for path in common_paths:
                if os.path.exists(path):
                    python_candidates.append(path)
                    self.debug_log(f"Python em local comum: {path}", "INFO")
            
            # Remover duplicatas e verificar validade
            valid_pythons = []
            for python_path in list(set(python_candidates)):
                if self._is_valid_python(python_path):
                    valid_pythons.append(python_path)
            
            if not valid_pythons:
                self.debug_log("Nenhum Python válido encontrado no sistema", "ERROR")
                return None
            
            # Ordenar por prioridade (Python 3 primeiro)
            def python_priority(path):
                path_lower = path.lower()
                if 'python3' in path_lower:
                    return 0
                elif 'python' in path_lower:
                    return 1
                else:
                    return 2
            
            valid_pythons.sort(key=python_priority)
            selected_python = valid_pythons[0]
            
            # Salvar nas configurações
            success = self.set_selected_python(selected_python)
            
            if success:
                version_info = self.get_python_version_info(selected_python)
                self.debug_log(f"Python do sistema detectado e salvo: {version_info}", "SUCCESS")
                return selected_python
            else:
                self.debug_log("Falha ao salvar Python nas configurações", "ERROR")
                return None
            
        except Exception as e:
            self.debug_log(f"Erro ao detectar Python do sistema: {e}", "ERROR")
            return None
    
    def _is_valid_python(self, python_path):
        """Verifica se um caminho de Python é válido"""
        try:
            if not python_path or not os.path.exists(python_path):
                self.debug_log(f"Python não existe: {python_path}", "DEBUG")
                return False
            
            # Verificar se é executável
            if not os.access(python_path, os.X_OK):
                self.debug_log(f"Python não é executável: {python_path}", "DEBUG")
                return False
            
            # Testar versão
            result = subprocess.run(
                [python_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            is_valid = result.returncode == 0
            if is_valid:
                self.debug_log(f"Python válido: {python_path} - {result.stdout.strip()}", "DEBUG")
            else:
                self.debug_log(f"Python inválido (falha no --version): {python_path}", "DEBUG")
            
            return is_valid
            
        except Exception as e:
            self.debug_log(f"Erro ao validar Python {python_path}: {e}", "DEBUG")
            return False
    
    def get_python_for_vm_creation(self):
        """Obtém o Python para criar VMs - com fallback inteligente"""
        self.debug_log("Buscando Python para criação de VMs...", "INFO")
        
        # 1. Tenta usar o último Python usado para VM
        last_vm_python = self.get_last_vm_python()
        if last_vm_python and os.path.exists(last_vm_python):
            self.debug_log(f"Usando último Python para VM: {last_vm_python}", "SUCCESS")
            return last_vm_python
        
        # 2. Tenta usar o Python selecionado
        selected_python = self.get_selected_python()
        if selected_python and os.path.exists(selected_python):
            self.debug_log(f"Usando Python selecionado: {selected_python}", "SUCCESS")
            return selected_python
        
        # 3. Detecta automaticamente Python do sistema
        self.debug_log("Nenhum Python configurado, detectando automaticamente...", "WARNING")
        system_python = self.detect_and_save_system_python()
        
        if system_python:
            self.debug_log(f"Usando Python do sistema detectado: {system_python}", "SUCCESS")
            return system_python
        
        # 4. Fallback final - Python atual
        self.debug_log(f"Usando Python atual como fallback: {sys.executable}", "WARNING")
        return sys.executable

    def set(self, key, value):
        """Método genérico para definir configurações"""
        if key in self.default_settings:
            self.default_settings[key] = value
            self.save_settings()
            return True
        return False

    def get(self, key, default=None):
        """Método genérico para obter configurações"""
        return self.default_settings.get(key, default)
    def send_command(self, command):
        """Envia comando para o terminal REAL"""
        try:
            if hasattr(self, 'shell_process') and self.shell_process:
                if self.shell_process.state() == QProcess.Running:
                    # Encode e envia o comando
                    encoded_command = command.encode('utf-8')
                    self.shell_process.write(encoded_command)
                    self.debug_log(f"✅ Comando enviado: {command.strip()}", "SUCCESS")
                    return True
                else:
                    self.debug_log("❌ Processo do terminal não está rodando", "ERROR")
                    return False
            else:
                self.debug_log("❌ Shell process não disponível", "ERROR")
                return False
        except Exception as e:
            self.debug_log(f"❌ Erro ao enviar comando: {e}", "ERROR")
            return False

# Instância global
settings_manager = SettingsManager()