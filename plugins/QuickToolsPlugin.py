from plugins.plugin_base import BasePlugin, PluginInfo, PluginStatus, PluginType
import os
import subprocess
import webbrowser

class QuickToolsPlugin(BasePlugin):
    """Plugin com ferramentas rápidas e utilitárias"""
    
    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="QuickToolsPlugin",
            version="1.0.0",
            description="Coleção de ferramentas rápidas para desenvolvimento",
            author="Py Dragon Team",
            plugin_type=PluginType.TOOL,
            status=PluginStatus.UNLOADED
        )
    
    def initialize(self) -> bool:
        try:
            self.setup_actions()
            self.plugin_info.status = PluginStatus.LOADED
            print(f"✅ {self.plugin_info.name} inicializado")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar QuickToolsPlugin: {e}")
            self.plugin_info.status = PluginStatus.ERROR
            self.plugin_info.error_message = str(e)
            return False
    
    def setup_actions(self):
        """Configura as ações do plugin"""
        # Ação para abrir terminal na pasta
        terminal_action = self.create_action(
            "💻 Abrir Terminal Aqui",
            self.open_terminal_here,
            tooltip="Abre terminal na pasta do projeto"
        )
        
        # Ação para abrir no explorer/finder
        explorer_action = self.create_action(
            "📂 Abrir no Explorer",
            self.open_in_explorer,
            tooltip="Abre explorer/finder na pasta do projeto"
        )
        
        # Ação para pesquisar no Google
        search_action = self.create_action(
            "🌐 Pesquisar no Google",
            self.search_google,
            "Ctrl+Shift+G",
            "Pesquisa texto selecionado no Google"
        )
        
        if terminal_action:
            self.actions.append(terminal_action)
        if explorer_action:
            self.actions.append(explorer_action)
        if search_action:
            self.actions.append(search_action)
    
    def open_terminal_here(self):
        """Abre terminal na pasta atual"""
        try:
            if self.ide_instance and hasattr(self.ide_instance, 'project_path'):
                project_path = self.ide_instance.project_path
                if project_path and os.path.exists(project_path):
                    if os.name == 'nt':  # Windows
                        os.system(f'start cmd /K "cd /d "{project_path}""')
                    else:  # Linux/Mac
                        os.system(f'gnome-terminal --working-directory="{project_path}" 2>/dev/null || xterm -e "cd {project_path}; bash" 2>/dev/null || echo "Nenhum terminal encontrado"')
                    self.show_message("💻 Terminal aberto na pasta do projeto")
                else:
                    self.show_message("❌ Nenhum projeto aberto")
            else:
                self.show_message("❌ IDE não disponível")
        except Exception as e:
            self.show_message(f"❌ Erro ao abrir terminal: {e}")
    
    def open_in_explorer(self):
        """Abre explorer/finder na pasta atual"""
        try:
            if self.ide_instance and hasattr(self.ide_instance, 'project_path'):
                project_path = self.ide_instance.project_path
                if project_path and os.path.exists(project_path):
                    if os.name == 'nt':  # Windows
                        os.startfile(project_path)
                    else:  # Linux/Mac
                        subprocess.run(['xdg-open', project_path])
                    self.show_message("📂 Explorer aberto na pasta do projeto")
                else:
                    self.show_message("❌ Nenhum projeto aberto")
            else:
                self.show_message("❌ IDE não disponível")
        except Exception as e:
            self.show_message(f"❌ Erro ao abrir explorer: {e}")
    
    def search_google(self):
        """Pesquisa texto selecionado no Google"""
        try:
            if self.ide_instance and hasattr(self.ide_instance, 'get_current_editor'):
                editor = self.ide_instance.get_current_editor()
                if editor:
                    selected_text = editor.textCursor().selectedText()
                    if selected_text:
                        search_url = f"https://www.google.com/search?q={selected_text}"
                        webbrowser.open(search_url)
                        self.show_message(f"🌐 Pesquisando: {selected_text}")
                    else:
                        self.show_message("❌ Nenhum texto selecionado para pesquisa")
                else:
                    self.show_message("❌ Nenhum editor ativo")
            else:
                self.show_message("❌ IDE não disponível")
        except Exception as e:
            self.show_message(f"❌ Erro na pesquisa: {e}")
    
    def show_message(self, message):
        """Mostra mensagem na statusbar do IDE"""
        if self.ide_instance and hasattr(self.ide_instance, 'statusBar'):
            self.ide_instance.statusBar().showMessage(message, 3000)