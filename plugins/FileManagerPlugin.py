from plugins.plugin_base import BasePlugin, PluginInfo, PluginStatus, PluginType
import os
import glob
import shutil

class FileManagerPlugin(BasePlugin):
    """Plugin para gerenciamento avançado de arquivos"""
    
    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="FileManagerPlugin",
            version="1.0.0",
            description="Ferramentas avançadas para gerenciamento de arquivos",
            author="Py Dragon Team",
            plugin_type=PluginType.TOOL,
            status=PluginStatus.UNLOADED
        )
    
    def initialize(self) -> bool:
        try:
            # Cria ações
            self.setup_actions()
            self.plugin_info.status = PluginStatus.LOADED
            print(f"✅ {self.plugin_info.name} inicializado")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar FileManagerPlugin: {e}")
            self.plugin_info.status = PluginStatus.ERROR
            self.plugin_info.error_message = str(e)
            return False
    
    def setup_actions(self):
        """Configura as ações do plugin"""
        # Ação para criar arquivo rápido
        quick_file_action = self.create_action(
            "📄 Criar Arquivo Rápido",
            self.create_quick_file,
            tooltip="Cria um novo arquivo rapidamente"
        )
        
        # Ação para limpar arquivos temporários
        cleanup_action = self.create_action(
            "🧹 Limpar Temporários", 
            self.cleanup_temp_files,
            tooltip="Limpa arquivos temporários do projeto"
        )
        
        if quick_file_action:
            self.actions.append(quick_file_action)
        if cleanup_action:
            self.actions.append(cleanup_action)
    
    def create_quick_file(self):
        """Cria um arquivo rapidamente"""
        try:
            if self.ide_instance and hasattr(self.ide_instance, 'create_new_file_in_explorer'):
                self.ide_instance.create_new_file_in_explorer()
                self.show_message("📄 Arquivo criado com sucesso!")
            else:
                self.show_message("❌ IDE não disponível para criar arquivo")
        except Exception as e:
            self.show_message(f"❌ Erro ao criar arquivo: {e}")
    
    def cleanup_temp_files(self):
        """Limpa arquivos temporários do projeto"""
        try:
            if self.ide_instance and hasattr(self.ide_instance, 'project_path'):
                project_path = self.ide_instance.project_path
                if project_path and os.path.exists(project_path):
                    cleaned = self._clean_project_files(project_path)
                    self.show_message(f"🧹 Limpos {cleaned} arquivos temporários!")
                else:
                    self.show_message("❌ Nenhum projeto aberto")
            else:
                self.show_message("❌ IDE não disponível")
        except Exception as e:
            self.show_message(f"❌ Erro ao limpar arquivos: {e}")
    
    def _clean_project_files(self, project_path):
        """Limpa arquivos temporários do projeto"""
        cleaned = 0
        
        # Limpa arquivos .pyc
        pyc_files = glob.glob(f"{project_path}/**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
                cleaned += 1
            except:
                pass
        
        # Limpa diretórios __pycache__
        cache_dirs = glob.glob(f"{project_path}/**/__pycache__", recursive=True)
        for cache_dir in cache_dirs:
            try:
                shutil.rmtree(cache_dir)
                cleaned += 1
            except:
                pass
        
        return cleaned
    
    def show_message(self, message):
        """Mostra mensagem na statusbar do IDE"""
        if self.ide_instance and hasattr(self.ide_instance, 'statusBar'):
            self.ide_instance.statusBar().showMessage(message, 3000)