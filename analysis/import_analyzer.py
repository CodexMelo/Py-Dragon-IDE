import ast
from typing import List, Dict
import os


class ProjectImportAnalyzer:
    """Analisa imports e arquivos do projeto para autocomplete"""
    
    def __init__(self):
        self.project_files_cache = {}
        self.import_cache = {}
        self.last_scan_time = 0
        
    def scan_project_files(self, project_path):
        """Escaneia todos os arquivos Python do projeto"""
        if not project_path or not os.path.exists(project_path):
            return {}
            
        current_time = time.time()
        # Recarrega cache a cada 30 segundos
        if (project_path in self.project_files_cache and 
            current_time - self.last_scan_time < 30):
            return self.project_files_cache[project_path]
            
        python_files = {}
        
        try:
            # Busca arquivos .py em todo o projeto
            for root, dirs, files in os.walk(project_path):
                # Ignora diretórios comuns
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if '.git' in dirs:
                    dirs.remove('.git')
                if 'venv' in dirs:
                    dirs.remove('venv')
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, project_path)
                        module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                        
                        # Extrai definições do arquivo
                        definitions = self._extract_file_definitions(full_path)
                        python_files[module_name] = {
                            'path': full_path,
                            'definitions': definitions,
                            'name': file[:-3]  # Remove .py
                        }
                        
        except Exception as e:
            print(f"⚠️ Erro ao escanear projeto: {e}")
            
        self.project_files_cache[project_path] = python_files
        self.last_scan_time = current_time
        return python_files
    
    def _extract_file_definitions(self, file_path):
        """Extrai funções, classes e variáveis de um arquivo"""
        definitions = {
            'functions': set(),
            'classes': set(), 
            'variables': set(),
            'imports': set()
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Análise com regex (fallback se AST falhar)
            functions = re.findall(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
            classes = re.findall(r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
            imports = re.findall(r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
            from_imports = re.findall(r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', content, re.MULTILINE)
            
            definitions['functions'].update([f"{f}()" for f in functions])
            definitions['classes'].update(classes)
            definitions['imports'].update(imports)
            definitions['imports'].update(from_imports)
            
            # Tenta análise AST para mais precisão
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        definitions['functions'].add(f"{node.name}()")
                    elif isinstance(node, ast.ClassDef):
                        definitions['classes'].add(node.name)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            definitions['imports'].add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        definitions['imports'].add(node.module)
            except:
                pass  # Usa apenas regex se AST falhar
                
        except Exception as e:
            print(f"⚠️ Erro ao analisar {file_path}: {e}")
            
        return definitions
    
    def get_import_suggestions(self, project_path, current_file=""):
        """Sugere módulos para import"""
        suggestions = set()
        
        # Módulos padrão do Python
        stdlib_modules = [
            'os', 'sys', 'json', 're', 'datetime', 'math', 'random',
            'subprocess', 'shutil', 'glob', 'ast', 'inspect', 'importlib',
            'platform', 'time', 'pathlib', 'collections', 'itertools', 'functools',
            'typing', 'logging', 'unittest', 'threading', 'multiprocessing'
        ]
        suggestions.update(stdlib_modules)
        
        # Módulos do projeto
        if project_path:
            project_files = self.scan_project_files(project_path)
            suggestions.update(project_files.keys())
            
            # Também adiciona nomes de arquivos sem extensão
            for module_info in project_files.values():
                suggestions.add(module_info['name'])
        
        return sorted(list(suggestions))
    
    def get_from_import_suggestions(self, project_path, module_name, current_file=""):
        """Sugere o que importar de um módulo específico"""
        suggestions = set()
        
        # Verifica se é um módulo do projeto
        project_files = self.scan_project_files(project_path) if project_path else {}
        
        if module_name in project_files:
            # É um módulo local - usa definições do arquivo
            definitions = project_files[module_name]['definitions']
            suggestions.update(definitions['functions'])
            suggestions.update(definitions['classes'])
            suggestions.update(definitions['imports'])
        else:
            # É um módulo externo ou stdlib - usa mapeamento hardcoded
            stdlib_contents = self._get_stdlib_contents(module_name)
            suggestions.update(stdlib_contents)
        
        return sorted(list(suggestions))
    
    def _get_stdlib_contents(self, module_name):
        """Conteúdo hardcoded de módulos stdlib comuns"""
        stdlib_map = {
            'os': ['path', 'environ', 'getcwd', 'listdir', 'mkdir', 'remove', 'rename', 
                   'system', 'walk', 'chdir', 'getenv', 'makedirs', 'rmdir'],
            'sys': ['argv', 'path', 'exit', 'version', 'platform', 'modules', 'executable'],
            'json': ['loads', 'dumps', 'load', 'dump', 'JSONEncoder', 'JSONDecoder'],
            're': ['search', 'match', 'findall', 'sub', 'compile', 'escape', 'IGNORECASE'],
            'datetime': ['datetime', 'date', 'time', 'timedelta', 'now', 'today'],
            'math': ['sqrt', 'sin', 'cos', 'tan', 'pi', 'e', 'log', 'exp', 'ceil', 'floor'],
            'random': ['random', 'randint', 'choice', 'shuffle', 'uniform', 'seed'],
            'subprocess': ['run', 'call', 'check_output', 'Popen', 'PIPE', 'STDOUT'],
            'pathlib': ['Path', 'PurePath', 'WindowsPath', 'PosixPath'],
            'collections': ['deque', 'Counter', 'OrderedDict', 'defaultdict', 'namedtuple'],
            'typing': ['List', 'Dict', 'Set', 'Tuple', 'Any', 'Union', 'Optional']
        }
        return stdlib_map.get(module_name, [])



class SmartImportCompleter:
    """Completador inteligente para imports e arquivos do projeto"""
    
    def __init__(self):
        self.analyzer = ProjectImportAnalyzer()
        self.last_context = {}
        
    def get_import_completions(self, code, cursor_position, file_path="", project_path=""):
        """Obtém sugestões específicas para contexto de import"""
        context = self._analyze_import_context(code, cursor_position)
        self.last_context = context
        
        if context['type'] == 'import':
            return self.analyzer.get_import_suggestions(project_path, file_path)
            
        elif context['type'] == 'from_import':
            return self.analyzer.get_from_import_suggestions(
                project_path, context['module'], file_path)
                
        elif context['type'] == 'project_file':
            return self._get_project_file_suggestions(project_path)
            
        else:
            return self._get_general_suggestions(code, project_path, file_path)
    
    def _analyze_import_context(self, code, cursor_position):
        """Analisa o contexto atual para determinar tipo de sugestão"""
        text_before = code[:cursor_position]
        current_line = text_before.split('\n')[-1] if '\n' in text_before else text_before
        
        # Verifica se está em import
        if 'import' in current_line:
            if 'from' in current_line:
                # from module import ...
                parts = current_line.split('import')
                if len(parts) > 1:
                    module_part = parts[0].replace('from', '').strip()
                    return {'type': 'from_import', 'module': module_part}
                else:
                    module_part = current_line.replace('from', '').strip()
                    return {'type': 'from_import', 'module': module_part}
            else:
                # import module
                return {'type': 'import'}
        
        # Verifica se está digitando caminho de arquivo
        elif any(keyword in current_line for keyword in ['open(', 'Path(', 'with open']):
            if any(quote in current_line for quote in ['"', "'"]):
                return {'type': 'project_file'}
        
        # Contexto geral
        return {'type': 'general'}
    
    def _get_project_file_suggestions(self, project_path):
        """Sugere arquivos do projeto"""
        suggestions = set()
        
        if not project_path:
            return list(suggestions)
            
        try:
            # Busca arquivos comuns
            patterns = ['*.py', '*.txt', '*.json', '*.xml', '*.html', '*.css', '*.js']
            
            for pattern in patterns:
                for file_path in glob.glob(os.path.join(project_path, '**', pattern), recursive=True):
                    if '__pycache__' not in file_path and '.git' not in file_path:
                        rel_path = os.path.relpath(file_path, project_path)
                        suggestions.add(f"'{rel_path}'")
                        
        except Exception as e:
            print(f"⚠️ Erro ao buscar arquivos: {e}")
            
        return sorted(list(suggestions))
    
    def _get_general_suggestions(self, code, project_path, file_path):
        """Sugestões gerais incluindo definições locais"""
        suggestions = set()
        
        # Palavras-chave Python
        keywords = [
            "if", "else", "elif", "for", "while", "def", "class", "import", "from",
            "return", "print", "len", "str", "list", "dict", "True", "False", "None"
        ]
        suggestions.update(keywords)
        
        # Definições do arquivo atual
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                suggestions.update([f"{f}()" for f in functions])
                
                classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                suggestions.update(classes)
                
            except:
                pass
        
        # Módulos do projeto
        if project_path:
            project_files = self.analyzer.scan_project_files(project_path)
            suggestions.update(project_files.keys())
        
        return sorted(list(suggestions))

