import ast
import re
from typing import List, Dict




class CodeAnalyzer:
    """Analisador de código para autocomplete inteligente"""

    def __init__(self):
        self.imported_modules = {}
        self.local_symbols = {}

    def analyze_code(self, code, file_path="<string>"):
        """Analisa código e extrai símbolos - VERSÃO SIMPLIFICADA"""
        try:
            # Análise básica com regex
            imports = {}
            functions = set()
            classes = set()
            variables = set()
            
            # Detecta imports
            import_pattern = r'(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            import_matches = re.findall(import_pattern, code)
            for module in import_matches:
                imports[module] = []
            
            # Detecta funções
            func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            func_matches = re.findall(func_pattern, code)
            functions.update([f"{f}()" for f in func_matches])
            
            # Detecta classes
            class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            class_matches = re.findall(class_pattern, code)
            classes.update(class_matches)
            
            return {
                'imports': imports,
                'symbols': {
                    'functions': functions,
                    'classes': classes,
                    'variables': variables,
                    'methods': {}
                },
                'classes': {}
            }
        except Exception as e:
            print(f"Erro na análise: {e}")
            return {
                'imports': {},
                'symbols': {'functions': set(), 'classes': set(), 'variables': set(), 'methods': {}},
                'classes': {}
            }

    def analyze_with_regex(self, code):
        """Fallback com regex"""
        imports = {}
        # Detecta imports com regex
        import_pattern = r'(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(import_pattern, code)
        for module in matches:
            imports[module] = []

        return {
            'imports': imports,
            'symbols': {'functions': set(), 'classes': set(), 'variables': set(), 'methods': {}},
            'classes': {}
        }





class SymbolCollector(ast.NodeVisitor):
    """Coletor de símbolos via AST - COMPLETA"""

    def __init__(self):
        super().__init__()
        self.imported_modules = {}
        self.local_symbols = {
            'functions': set(), 'classes': set(), 'variables': set(), 'methods': {}
        }
        self.class_hierarchy = {}
        self.current_class = None

    def visit_Import(self, node):
        for alias in node.names:
            self.imported_modules[alias.name] = []
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            imports = [
                alias.name for alias in node.names]
            self.imported_modules[node.module] = imports
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.local_symbols['classes'].add(node.name)
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        if self.current_class:
            if self.current_class not in self.local_symbols['methods']:
                self.local_symbols['methods'][self.current_class] = set(
                )
            self.local_symbols['methods'][self.current_class].add(
                f"{node.name}()")
        else:
            self.local_symbols['functions'].add(
                f"{node.name}()")
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_symbols['variables'].add(
                    target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        # Captura nomes de variáveis em expressões
        if isinstance(node.ctx, ast.Store):
            self.local_symbols['variables'].add(
                node.id)
        self.generic_visit(node)

