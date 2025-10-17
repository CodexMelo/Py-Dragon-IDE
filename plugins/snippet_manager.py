# SnippetManagerPlugin.py
from plugin_base import BasePlugin, PluginInfo, PluginType, PluginStatus
import json
import os


class SnippetManagerPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="Snippet Manager",
            version="1.0.0",
            description="Gerenciador de snippets de código",
            author="IDE System",
            plugin_type=PluginType.INTERNAL
        )
        self.snippets_file = "snippets.json"
        self.snippets = {}
    
    def initialize(self) -> bool:
        try:
            self.load_snippets()
            return True
        except Exception as e:
            self.plugin_info.status = PluginStatus.ERROR
            self.plugin_info.error_message = str(e)
            return False
    
    def load_snippets(self):
        """Carrega snippets do arquivo"""
        if os.path.exists(self.snippets_file):
            with open(self.snippets_file, 'r', encoding='utf-8') as f:
                self.snippets = json.load(f)
        else:
            # Snippets padrão
            self.snippets = {
                'python': {
                    'for_loop': {
                        'name': 'For Loop',
                        'code': 'for item in collection:\n    # do something with item\n    pass',
                        'language': 'python'
                    },
                    'function': {
                        'name': 'Function',
                        'code': 'def function_name(args):\n    """Docstring"""\n    return result',
                        'language': 'python'
                    }
                },
                'html': {
                    'basic_template': {
                        'name': 'HTML Basic Template',
                        'code': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Page Title</title>\n</head>\n<body>\n    \n</body>\n</html>',
                        'language': 'html'
                    }
                }
            }
            self.save_snippets()
    
    def save_snippets(self):
        """Salva snippets no arquivo"""
        with open(self.snippets_file, 'w', encoding='utf-8') as f:
            json.dump(self.snippets, f, indent=2, ensure_ascii=False)
    
    def get_snippets(self, language: str = None) -> dict:
        """Retorna snippets, filtrado por linguagem se especificado"""
        if language:
            return self.snippets.get(language, {})
        return self.snippets
    
    def add_snippet(self, language: str, key: str, name: str, code: str):
        """Adiciona um novo snippet"""
        if language not in self.snippets:
            self.snippets[language] = {}
        
        self.snippets[language][key] = {
            'name': name,
            'code': code,
            'language': language
        }
        self.save_snippets()
    
    def delete_snippet(self, language: str, key: str):
        """Remove um snippet"""
        if language in self.snippets and key in self.snippets[language]:
            del self.snippets[language][key]
            self.save_snippets()