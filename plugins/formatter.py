from plugins.plugin_base import BasePlugin, PluginInfo, PluginStatus, PluginType

class CodeFormatterPlugin(BasePlugin):
    """Plugin para formatação de código com múltiplas ferramentas"""
    
    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="CodeFormatterPlugin",
            version="1.1.0",
            description="Suporte a autopep8, black e outras ferramentas de formatação",
            author="Py Dragon Team",
            plugin_type=PluginType.TOOL,
            status=PluginStatus.UNLOADED,
            dependencies=["autopep8"]
        )
    
    def initialize(self) -> bool:
        try:
            # Verifica dependências
            deps_ok = self.check_dependencies()
            
            # Configura ações
            self.setup_actions()
            
            self.plugin_info.status = PluginStatus.LOADED
            print(f"✅ {self.plugin_info.name} inicializado")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar CodeFormatterPlugin: {e}")
            self.plugin_info.status = PluginStatus.ERROR
            self.plugin_info.error_message = str(e)
            return False
    
    def check_dependencies(self):
        """Verifica se as dependências estão instaladas"""
        try:
            import autopep8
            return True
        except ImportError:
            self.show_message("⚠️ autopep8 não instalado. Use: pip install autopep8")
            return False
    
    def setup_actions(self):
        """Configura as ações do plugin"""
        # Ação para formatar com autopep8
        format_action = self.create_action(
            "📐 Format com autopep8",
            self.format_with_autopep8,
            "Ctrl+Shift+F",
            "Formata código Python usando autopep8"
        )
        
        # Ação para verificar estilo
        check_action = self.create_action(
            "🔍 Verificar Estilo",
            self.check_code_style,
            tooltip="Verifica estilo do código"
        )
        
        if format_action:
            self.actions.append(format_action)
        if check_action:
            self.actions.append(check_action)
    
    def format_with_autopep8(self):
        """Formata código usando autopep8"""
        try:
            if self.ide_instance and hasattr(self.ide_instance, 'get_current_editor'):
                editor = self.ide_instance.get_current_editor()
                if editor and hasattr(editor, 'toPlainText'):
                    import autopep8
                    code = editor.toPlainText()
                    formatted_code = autopep8.fix_code(code)
                    editor.setPlainText(formatted_code)
                    self.show_message("✅ Código formatado com autopep8!")
                else:
                    self.show_message("❌ Nenhum editor ativo")
            else:
                self.show_message("❌ IDE não disponível")
        except ImportError:
            self.show_message("❌ autopep8 não instalado. Use: pip install autopep8")
        except Exception as e:
            self.show_message(f"❌ Erro ao formatar código: {e}")
    
    def check_code_style(self):
        """Verifica estilo do código"""
        self.show_message("🔍 Verificando estilo do código...")
        # Implementação futura para verificação de estilo
    
    def show_message(self, message):
        """Mostra mensagem na statusbar do IDE"""
        if self.ide_instance and hasattr(self.ide_instance, 'statusBar'):
            self.ide_instance.statusBar().showMessage(message, 3000)