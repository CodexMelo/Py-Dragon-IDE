import os
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Optional

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, object] = {}
        self.loaded_plugins: List[object] = []
        self.plugins_dir = Path(__file__).parent
        self.ide_instance = None  # ✅ ADICIONAR: Referência ao IDE
    
    def set_ide_instance(self, ide_instance):
        """✅ NOVO: Define a instância do IDE para todos os plugins"""
        self.ide_instance = ide_instance
        # Injeta o IDE em plugins já carregados
        for plugin in self.plugins.values():
            if hasattr(plugin, 'set_ide_instance'):
                plugin.set_ide_instance(ide_instance)
        
    def auto_load_plugins(self):
        """Carrega plugins automaticamente - versão corrigida"""
        try:
            plugin_files = list(self.plugins_dir.glob("*Plugin.py"))
            loaded_count = 0
            
            for plugin_file in plugin_files:
                if plugin_file.name in ["plugin_base.py", "plugin_manager.py"]:
                    continue
                    
                try:
                    plugin_name = plugin_file.stem
                    if self.load_plugin_dynamically(plugin_name):
                        loaded_count += 1
                except Exception as e:
                    print(f"❌ Erro ao carregar {plugin_file.name}: {e}")
            
            print(f"📦 Carregados automaticamente: {loaded_count}/{len(plugin_files)} plugins")
            return loaded_count
            
        except Exception as e:
            print(f"❌ Erro no carregamento automático: {e}")
            return 0
    
    def load_plugin_dynamically(self, plugin_name):
        """Carrega um plugin dinamicamente - versão corrigida"""
        try:
            if plugin_name in self.plugins:
                return True
                
            # Importa o módulo do plugin
            module = importlib.import_module(f"plugins.{plugin_name}")
            plugin_class = getattr(module, plugin_name)
            
            # Cria instância
            plugin_instance = plugin_class()
            self.plugins[plugin_name] = plugin_instance
            
            # ✅ CORREÇÃO: Injeta a instância do IDE ANTES de inicializar
            if self.ide_instance and hasattr(plugin_instance, 'set_ide_instance'):
                plugin_instance.set_ide_instance(self.ide_instance)
            
            # Tenta inicializar
            if hasattr(plugin_instance, 'initialize'):
                success = plugin_instance.initialize()
                if success:
                    self.loaded_plugins.append(plugin_instance)
                    print(f"✅ Plugin carregado: {plugin_name}")
                    return True
                else:
                    print(f"❌ Falha na inicialização: {plugin_name}")
                    return False
            else:
                self.loaded_plugins.append(plugin_instance)
                print(f"✅ Plugin carregado (sem initialize): {plugin_name}")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao carregar plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, name):
        """Obtém um plugin pelo nome"""
        return self.plugins.get(name)
    
    def get_plugins_info(self):
        """Retorna informações dos plugins"""
        plugins_info = []
        
        for plugin_name, plugin_instance in self.plugins.items():
            try:
                if hasattr(plugin_instance, 'plugin_info'):
                    plugins_info.append(plugin_instance.plugin_info)
                else:
                    # Cria info básica se não existir
                    from plugins.plugin_base import PluginInfo, PluginStatus, PluginType
                    plugins_info.append(PluginInfo(
                        name=plugin_name,
                        version="1.0.0",
                        description="Plugin carregado",
                        author="Desconhecido",
                        plugin_type=PluginType.INTERNAL,
                        status=PluginStatus.LOADED
                    ))
            except Exception as e:
                print(f"❌ Erro ao obter info do plugin {plugin_name}: {e}")
        
        return plugins_info
    
    def get_all_plugin_actions(self):
        """✅ NOVO: Retorna todas as ações de todos os plugins"""
        all_actions = []
        for plugin_name, plugin_instance in self.plugins.items():
            if hasattr(plugin_instance, 'get_actions'):
                actions = plugin_instance.get_actions()
                if actions:
                    # Filtra ações válidas
                    valid_actions = [action for action in actions if action is not None]
                    all_actions.extend(valid_actions)
                    print(f"📋 Plugin {plugin_name}: {len(valid_actions)} ações")
        return all_actions