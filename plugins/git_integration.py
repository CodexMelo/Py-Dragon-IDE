# GitIntegrationPlugin.py
from plugin_base import BasePlugin, PluginInfo, PluginType, PluginStatus
import subprocess
import os


class GitIntegrationPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="Git Integration",
            version="1.0.0",
            description="Integração com Git para controle de versão",
            author="IDE System",
            plugin_type=PluginType.INTERNAL
        )
    
    def initialize(self) -> bool:
        try:
            self.check_git_availability()
            return True
        except Exception as e:
            self.plugin_info.status = PluginStatus.ERROR
            self.plugin_info.error_message = str(e)
            return False
    
    def check_git_availability(self):
        """Verifica se o Git está disponível no sistema"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                raise Exception("Git não encontrado no sistema")
        except Exception as e:
            raise Exception(f"Git não disponível: {str(e)}")
    
    def get_git_status(self, repo_path: str) -> dict:
        """Retorna status do repositório Git"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'],
                                  cwd=repo_path, capture_output=True, text=True)
            
            changes = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': []
            }
            
            for line in result.stdout.split('\n'):
                if line:
                    status = line[:2]
                    filename = line[3:]
                    
                    if status == ' M':
                        changes['modified'].append(filename)
                    elif status == 'A ':
                        changes['added'].append(filename)
                    elif status == 'D ':
                        changes['deleted'].append(filename)
                    elif status == '??':
                        changes['untracked'].append(filename)
            
            return changes
        except Exception as e:
            return {'error': str(e)}