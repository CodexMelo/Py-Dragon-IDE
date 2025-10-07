from PySide6.QtWidgets import QAction, QMessageBox
from PySide6.QtCore import QObject, Signal
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import os
import importlib
import inspect
import tempfile
import zipfile
import shutil
from urllib.request import urlretrieve


@dataclass
class PluginInfo:
    name: str
    version: str
    author: str
    description: str
    enabled: bool = True


class PluginBase(ABC):
    """Classe base para todos os plugins"""

    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.info = PluginInfo(
            name="Plugin Base",
            version="1.0.0",
            author="Desconhecido",
            description="Plugin base"
        )

    @abstractmethod
    def initialize(self):
        """Inicializa o plugin"""
        pass

    @abstractmethod
    def shutdown(self):
        """Finaliza o plugin"""
        pass

    def get_actions(self) -> List[QAction]:
        """Retorna ações do plugin para a interface"""
        return []

    def get_menu_items(self) -> Dict[str, List[QAction]]:
        """Retorna itens de menu do plugin"""
        return {}

    def get_toolbar_items(self) -> List[QAction]:
        """Retorna itens para a toolbar"""
        return []


class PluginManager:
    """Gerenciador de plugins"""

    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.plugins: Dict[str, PluginBase] = {}
        self.plugins_dir = os.path.join(
            os.path.expanduser("~"), ".py_dragon_plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)

    def discover_plugins(self):
        """Descobre plugins disponíveis"""
        plugins = {}

        # Plugins internos (com tratamento de erro)
        internal_plugins = []
        try:
            from plugins.formatter import CodeFormatterPlugin
            internal_plugins.append(CodeFormatterPlugin)
        except ImportError:
            print("⚠️ CodeFormatterPlugin não encontrado")
        
        try:
            from plugins.git_integration import GitIntegrationPlugin
            internal_plugins.append(GitIntegrationPlugin)
        except ImportError:
            print("⚠️ GitIntegrationPlugin não encontrado")
            
        try:
            from plugins.code_metrics import CodeMetricsPlugin
            internal_plugins.append(CodeMetricsPlugin)
        except ImportError:
            print("⚠️ CodeMetricsPlugin não encontrado")
            
        try:
            from plugins.snippet_manager import SnippetManagerPlugin
            internal_plugins.append(SnippetManagerPlugin)
        except ImportError:
            print("⚠️ SnippetManagerPlugin não encontrado")

        for plugin_class in internal_plugins:
            try:
                plugin = plugin_class(self.ide)
                plugins[plugin.info.name] = plugin
            except Exception as e:
                print(f"Erro ao carregar plugin interno {plugin_class.__name__}: {e}")

        # Plugins externos
        for file in os.listdir(self.plugins_dir):
            if file.endswith('.py') and not file.startswith('_'):
                try:
                    plugin_path = os.path.join(self.plugins_dir, file)
                    spec = importlib.util.spec_from_file_location(file[:-3], plugin_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (inspect.isclass(attr) and
                                issubclass(attr, PluginBase) and
                                attr != PluginBase):
                            plugin = attr(self.ide)
                            plugins[plugin.info.name] = plugin

                except Exception as e:
                    print(f"Erro ao carregar plugin externo {file}: {e}")

        return plugins

    def load_plugins(self):
        """Carrega todos os plugins"""
        self.plugins = self.discover_plugins()

        for name, plugin in self.plugins.items():
            try:
                plugin.initialize()
                print(f"✅ Plugin carregado: {name} v{plugin.info.version}")
            except Exception as e:
                print(f"❌ Erro ao inicializar plugin {name}: {e}")

    def shutdown_plugins(self):
        """Finaliza todos os plugins de forma segura"""
        if not hasattr(self, 'plugins'):
            return

        for name, plugin in list(self.plugins.items()):
            try:
                if hasattr(plugin, 'shutdown'):
                    plugin.shutdown()
                print(f"✅ Plugin finalizado: {name}")
            except Exception as e:
                print(f"❌ Erro ao finalizar plugin {name}: {e}")

        # Limpa dicionário
        self.plugins.clear()

    def get_plugin_actions(self):
        """Obtém todas as ações dos plugins"""
        actions = []
        for plugin in self.plugins.values():
            if plugin.info.enabled:
                actions.extend(plugin.get_actions())
        return actions

    def install_plugin(self, plugin_path_or_url):
        """Instala um novo plugin"""
        try:
            if plugin_path_or_url.startswith('http'):
                # Download de URL
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                urlretrieve(plugin_path_or_url, temp_file.name)
                plugin_path = temp_file.name
            else:
                plugin_path = plugin_path_or_url

            # Extrai/instala o plugin
            if plugin_path.endswith('.zip'):
                with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                    zip_ref.extractall(self.plugins_dir)
            elif plugin_path.endswith('.py'):
                shutil.copy(plugin_path, self.plugins_dir)

            QMessageBox.information(self.ide, "Sucesso", "Plugin instalado com sucesso!")

        except Exception as e:
            QMessageBox.warning(self.ide, "Erro", f"Falha na instalação: {str(e)}")