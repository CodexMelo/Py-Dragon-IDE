# plugins/plugin_template.py
"""
TEMPLATE PARA NOVOS PLUGINS

Como usar:
1. Copie este arquivo para um novo nome (ex: MeuPlugin.py)
2. Renomeie a classe para o mesmo nome do arquivo
3. Implemente os métodos necessários
4. Use o Gerenciador de Plugins para instalar

Exemplo de plugin simples:
"""

from plugin_base import BasePlugin, PluginInfo, PluginType, PluginStatus

class MeuPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="Meu Plugin",
            version="1.0.0",
            description="Descrição do meu plugin",
            author="Seu Nome",
            plugin_type=PluginType.INTERNAL
        )
    
    def initialize(self) -> bool:
        """Inicializa o plugin"""
        try:
            # Sua lógica de inicialização aqui
            print(f"✅ Plugin {self.plugin_info.name} inicializado")
            return True
        except Exception as e:
            self.plugin_info.status = PluginStatus.ERROR
            self.plugin_info.error_message = str(e)
            return False
    
    def shutdown(self):
        """Finaliza o plugin"""
        # Limpeza necessária
        pass
    
    # Adicione seus métodos personalizados aqui
    def minha_funcao(self):
        """Exemplo de função personalizada"""
        return "Hello from my plugin!"