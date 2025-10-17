import ast
from typing import List




class DefinitionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.definitions = set()
        self.imported_modules = set()
        self.current_class = None
        self.import_statements = []

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.definitions.add(node.name)
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class:
            self.definitions.add(
                f"{self.current_class}.{node.name}()")
        else:
            self.definitions.add(f"{node.name}()")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if self.current_class:
            self.definitions.add(
                f"{self.current_class}.{node.name}()")
        else:
            self.definitions.add(f"{node.name}()")
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.definitions.add(
                    target.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            self.definitions.add(module_name)
            self.imported_modules.add(module_name)
            self.import_statements.append(
                alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.definitions.add(node.module)
            self.imported_modules.add(node.module)
            self.import_statements.append(
                f"from {node.module} import ...")
        for alias in node.names:
            self.definitions.add(alias.name)
        self.generic_visit(node)
        self.generic_visit(node)

class SafeDefinitionVisitor(ast.NodeVisitor):
    """Visitor AST seguro com tratamento de erros"""

    def __init__(self):
        self.definitions = set()

    def visit_ClassDef(self, node):
        try:
            self.definitions.add(node.name)
            self.generic_visit(node)
        except:
            pass

    def visit_FunctionDef(self, node):
        try:
            self.definitions.add(f"{node.name}()")
            self.generic_visit(node)
        except:
            pass

    def visit_Import(self, node):
        try:
            for alias in node.names:
                module_name = alias.name.split('.')[
                    0]
                self.definitions.add(
                    module_name)
            self.generic_visit(node)
        except:
            pass

    def visit_ImportFrom(self, node):
        try:
            if node.module:
                self.definitions.add(
                    node.module)
            for alias in node.names:
                self.definitions.add(
                    alias.name)
            self.generic_visit(node)
        except:
            pass


class ClassRelationVisitor(ast.NodeVisitor):
    """Visitor para detectar relações entre classes e métodos"""

    def __init__(self):
        self.classes = set()
        self.methods = {}
        self.current_class = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.classes.add(node.name)
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class:
            if self.current_class not in self.methods:
                self.methods[self.current_class] = set(
                )
            self.methods[self.current_class].add(
                node.name)
        self.generic_visit(node)
