# CodeMetricsPlugin.py
from plugin_base import BasePlugin, PluginInfo, PluginType, PluginStatus
import re


class CodeMetricsPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="Code Metrics",
            version="1.0.0",
            description="Análise de métricas de código",
            author="IDE System",
            plugin_type=PluginType.INTERNAL
        )
    
    def initialize(self) -> bool:
        try:
            self.setup_metrics_calculators()
            return True
        except Exception as e:
            self.plugin_info.status = PluginStatus.ERROR
            self.plugin_info.error_message = str(e)
            return False
    
    def setup_metrics_calculators(self):
        """Configura os calculadores de métricas"""
        self.metrics_calculators = {
            'python': self.calculate_python_metrics,
            'javascript': self.calculate_js_metrics,
            'generic': self.calculate_generic_metrics
        }
    
    def calculate_python_metrics(self, code: str) -> dict:
        """Calcula métricas para código Python"""
        lines = code.split('\n')
        
        metrics = {
            'lines_of_code': len(lines),
            'blank_lines': len([l for l in lines if not l.strip()]),
            'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
            'functions': len(re.findall(r'def\s+(\w+)\s*\(', code)),
            'classes': len(re.findall(r'class\s+(\w+)', code)),
            'imports': len(re.findall(r'^import\s+|^from\s+', code, re.MULTILINE))
        }
        
        metrics['code_lines'] = metrics['lines_of_code'] - metrics['blank_lines'] - metrics['comment_lines']
        metrics['comment_ratio'] = metrics['comment_lines'] / max(metrics['lines_of_code'], 1)
        
        return metrics
    
    def calculate_metrics(self, code: str, language: str) -> dict:
        """Calcula métricas baseado na linguagem"""
        calculator = self.metrics_calculators.get(language.lower(), self.calculate_generic_metrics)
        return calculator(code)
    
    def calculate_generic_metrics(self, code: str) -> dict:
        """Calcula métricas genéricas"""
        lines = code.split('\n')
        return {
            'lines_of_code': len(lines),
            'blank_lines': len([l for l in lines if not l.strip()]),
            'characters': len(code)
        }