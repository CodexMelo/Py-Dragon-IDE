# plugin_base.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class PluginType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class PluginStatus(Enum):
    LOADED = "loaded"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInfo:
    """Classe base para informações do plugin"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType = PluginType.INTERNAL
    status: PluginStatus = PluginStatus.LOADED
    error_message: Optional[str] = None


class BasePlugin:
    """Classe base para todos os plugins"""
    
    def __init__(self):
        self.plugin_info = PluginInfo(
            name="Base Plugin",
            version="1.0.0",
            description="Plugin base",
            author="System"
        )
    
    def initialize(self) -> bool:
        """Inicializa o plugin"""
        return True
    
    def shutdown(self):
        """Finaliza o plugin"""
        pass
    
    def get_info(self) -> PluginInfo:
        """Retorna informações do plugin"""
        return self.plugin_info