from plugins.plugin_base import BasePlugin, PluginInfo, PluginStatus, PluginType

class ThemePackPlugin(BasePlugin):
    """Plugin com pacotes de temas adicionais"""
    
    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="ThemePackPlugin",
            version="1.0.0",
            description="Pacote de temas adicionais para o IDE",
            author="Py Dragon Team",
            plugin_type=PluginType.THEME,
            status=PluginStatus.UNLOADED
        )
        self.themes = {
            "Dark Blue": self.dark_blue_theme,
            "Solarized Dark": self.solarized_dark_theme,
            "Monokai": self.monokai_theme,
            "GitHub Light": self.github_light_theme
        }
    
    def initialize(self) -> bool:
        try:
            self.setup_actions()
            self.plugin_info.status = PluginStatus.LOADED
            print(f"✅ {self.plugin_info.name} inicializado")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar ThemePackPlugin: {e}")
            self.plugin_info.status = PluginStatus.ERROR
            self.plugin_info.error_message = str(e)
            return False
    
    def setup_actions(self):
        """Configura as ações do plugin"""
        for theme_name in self.themes.keys():
            theme_action = self.create_action(
                f"🎨 {theme_name}",
                lambda checked, name=theme_name: self.apply_theme(name),
                tooltip=f"Aplica o tema {theme_name}"
            )
            if theme_action:
                self.actions.append(theme_action)
    
    def apply_theme(self, theme_name):
        """Aplica um tema específico"""
        try:
            if theme_name in self.themes:
                self.themes[theme_name]()
                self.show_message(f"🎨 Tema {theme_name} aplicado!")
            else:
                self.show_message(f"❌ Tema {theme_name} não encontrado")
        except Exception as e:
            self.show_message(f"❌ Erro ao aplicar tema: {e}")
    
    def dark_blue_theme(self):
        """Tema Dark Blue"""
        try:
            from PySide6.QtGui import QColor, QPalette
            palette = self.ide_instance.palette()
            palette.setColor(QPalette.Window, QColor(30, 35, 45))
            palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
            palette.setColor(QPalette.Base, QColor(20, 25, 35))
            palette.setColor(QPalette.Text, QColor(220, 220, 220))
            self.ide_instance.setPalette(palette)
        except Exception as e:
            print(f"❌ Erro ao aplicar Dark Blue: {e}")
    
    def solarized_dark_theme(self):
        """Tema Solarized Dark"""
        try:
            from PySide6.QtGui import QColor, QPalette
            palette = self.ide_instance.palette()
            palette.setColor(QPalette.Window, QColor(0, 43, 54))
            palette.setColor(QPalette.WindowText, QColor(131, 148, 150))
            palette.setColor(QPalette.Base, QColor(0, 30, 40))
            palette.setColor(QPalette.Text, QColor(131, 148, 150))
            self.ide_instance.setPalette(palette)
        except Exception as e:
            print(f"❌ Erro ao aplicar Solarized Dark: {e}")
    
    def monokai_theme(self):
        """Tema Monokai"""
        try:
            from PySide6.QtGui import QColor, QPalette
            palette = self.ide_instance.palette()
            palette.setColor(QPalette.Window, QColor(39, 40, 34))
            palette.setColor(QPalette.WindowText, QColor(248, 248, 242))
            palette.setColor(QPalette.Base, QColor(25, 26, 20))
            palette.setColor(QPalette.Text, QColor(248, 248, 242))
            self.ide_instance.setPalette(palette)
        except Exception as e:
            print(f"❌ Erro ao aplicar Monokai: {e}")
    
    def github_light_theme(self):
        """Tema GitHub Light"""
        try:
            from PySide6.QtGui import QColor, QPalette
            palette = self.ide_instance.palette()
            palette.setColor(QPalette.Window, QColor(255, 255, 255))
            palette.setColor(QPalette.WindowText, QColor(36, 41, 46))
            palette.setColor(QPalette.Base, QColor(246, 248, 250))
            palette.setColor(QPalette.Text, QColor(36, 41, 46))
            self.ide_instance.setPalette(palette)
        except Exception as e:
            print(f"❌ Erro ao aplicar GitHub Light: {e}")
    
    def show_message(self, message):
        """Mostra mensagem na statusbar do IDE"""
        if self.ide_instance and hasattr(self.ide_instance, 'statusBar'):
            self.ide_instance.statusBar().showMessage(message, 3000)