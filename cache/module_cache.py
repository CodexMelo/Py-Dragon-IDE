from typing import Set, Dict, List, Any, Optional
import time
import threading
import os
import sys
import importlib
import inspect
import ast

class ModuleCacheManager:
    """Gerenciador de cache para módulos e métodos"""

    def __init__(self):
        self._cache_lock = threading.RLock()
        self._module_cache: Dict[str, Dict[str, Any]] = {}
        self._project_modules: Dict[str, Set[str]] = {}
        self._last_scan_time: Dict[str, float] = {}
        self._scan_interval = 5.0
        self._chain_cache: Dict[str, Set[str]] = {}
        self._preload_done = False

    def preload_all_project_modules(self, project_path: str, file_path: str = None):
        """PRELOAD AGRESSIVO: Carrega todos os módulos do projeto uma vez"""
        if self._preload_done or not project_path:
            return

        with self._cache_lock:
            self._preload_done = True
            print("🔄 Preloading todos os módulos do projeto...")

            # Encontra todos os .py no projeto
            py_files = []
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
                        py_files.append(os.path.join(root, file))

            # Carrega cada um
            for py_file in py_files:
                try:
                    # Calcula nome do módulo relativo
                    rel_path = os.path.relpath(py_file, project_path)
                    module_name = rel_path.replace(os.sep, '.').rstrip('.py')
                    
                    # Remove __init__ do final se for pacote
                    if module_name.endswith('.__init__'):
                        module_name = module_name[:-9]
                    
                    self.get_module_methods(module_name, py_file, project_path)
                except Exception as e:
                    print(f"⚠️ Erro ao preload {py_file}: {e}")

            print("✅ Preload concluído!")

    def get_module_methods(self, module_name: str, file_path: str = None, project_path: str = None) -> Set[str]:
        """Obtém todos os métodos de um módulo com cache"""
        with self._cache_lock:
            cache_key = f"{module_name}:{file_path or ''}"

            # Verifica se precisa atualizar o cache
            current_time = time.time()
            last_scan = self._last_scan_time.get(cache_key, 0)

            if current_time - last_scan > self._scan_interval:
                self._update_module_cache(module_name, file_path, project_path)
                self._last_scan_time[cache_key] = current_time

            methods = self._module_cache.get(cache_key, set())
            return {m if m.endswith('()') else f"{m}()" for m in methods}

    def _update_module_cache(self, module_name: str, file_path: str = None, project_path: str = None):
        """Atualiza o cache para um módulo específico"""
        cache_key = f"{module_name}:{file_path or ''}"
        methods = set()

        try:
            # Tenta carregar como módulo Python padrão
            if module_name in sys.builtin_module_names:
                methods.update(self._get_builtin_module_methods(module_name))

            # Tenta importar o módulo
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    methods.update(self._get_module_attributes(module))
            except Exception as e:
                # Fallback para análise estática
                pass

            # Procura módulos locais no projeto
            if project_path:
                local_methods = self._scan_local_module(module_name, project_path, file_path)
                methods.update(local_methods)

        except Exception as e:
            print(f"Erro ao atualizar cache para {module_name}: {e}")

        self._module_cache[cache_key] = methods

    def _get_builtin_module_methods(self, module_name: str) -> Set[str]:
        """Métodos para módulos built-in"""
        builtin_methods = {
            'os': ['path.join()', 'path.exists()', 'path.dirname()', 'path.basename()', 'mkdir()', 'listdir()',
                   'getcwd()', 'chdir()', 'remove()', 'rename()', 'system()', 'walk()'],
            'sys': ['argv', 'path', 'exit()', 'version', 'platform', 'modules', 'executable', 'stdin', 'stdout', 'stderr'],
            'json': ['loads()', 'dumps()', 'load()', 'dump()', 'JSONEncoder', 'JSONDecoder'],
            're': ['search()', 'match()', 'findall()', 'sub()', 'compile()', 'IGNORECASE', 'MULTILINE', 'DOTALL'],
            'datetime': ['datetime', 'date', 'time', 'timedelta', 'now()', 'today()', 'strftime()', 'strptime()'],
            'math': ['sqrt()', 'sin()', 'cos()', 'tan()', 'pi', 'e', 'log()', 'exp()', 'ceil()', 'floor()'],
            'random': ['random()', 'randint()', 'choice()', 'shuffle()', 'uniform()', 'seed()', 'sample()'],
            'pathlib': ['Path', 'PurePath', 'exists()', 'is_file()', 'is_dir()', 'name', 'stem', 'suffix'],
            'collections': ['deque', 'Counter', 'OrderedDict', 'defaultdict', 'namedtuple'],
            'itertools': ['chain', 'cycle', 'repeat', 'count', 'groupby', 'combinations', 'permutations'],
            'functools': ['partial', 'reduce', 'wraps', 'lru_cache'],
            'typing': ['List', 'Dict', 'Set', 'Tuple', 'Any', 'Union', 'Optional', 'Callable']
        }
        return set(builtin_methods.get(module_name, []))

    def _get_module_attributes(self, module) -> Set[str]:
        """Extrai atributos de um módulo importado"""
        attrs = set()
        try:
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    try:
                        attr = getattr(module, attr_name)
                        if callable(attr):
                            attrs.add(f"{attr_name}()")
                        else:
                            attrs.add(attr_name)
                    except (AttributeError, Exception):
                        # Ignora atributos que não podem ser acessados
                        pass
        except Exception:
            pass
        return attrs

    def _scan_local_module(self, module_name: str, project_path: str, current_file: str = None) -> Set[str]:
        """Escaneia módulos locais no projeto"""
        methods = set()
        try:
            # Possíveis locais do módulo
            possible_paths = [
                os.path.join(project_path, f"{module_name}.py"),
                os.path.join(project_path, module_name, "__init__.py"),
                os.path.join(project_path, module_name.replace('.', os.sep) + ".py"),
                os.path.join(project_path, module_name.replace('.', os.sep), "__init__.py")
            ]

            for module_path in possible_paths:
                if os.path.exists(module_path):
                    module_methods = self._parse_python_file_robust(module_path)
                    methods.update(module_methods)
                    break

        except Exception as e:
            print(f"Erro ao escanear módulo local {module_name}: {e}")

        return methods

    def _parse_python_file_robust(self, file_path: str) -> Set[str]:
        """Analisa um arquivo Python com AST robusta"""
        methods = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = None
            try:
                tree = ast.parse(content, mode='exec', filename=file_path)
            except (IndentationError, SyntaxError):
                # Fallback regex para arquivos com problemas de sintaxe
                return self._parse_with_regex(content)

            # Visita AST
            visitor = SafeDefinitionVisitor()
            visitor.visit(tree)
            methods.update(visitor.definitions)

        except Exception as e:
            print(f"Erro ao analisar arquivo {file_path}: {e}")

        return methods

    def _parse_with_regex(self, content: str) -> Set[str]:
        """Fallback regex para análise de código"""
        methods = set()
        
        # Funções
        functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update([f"{f}()" for f in functions])
        
        # Classes
        classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update(classes)
        
        # Imports para sugestões
        imports = re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        methods.update(imports)
        
        # From imports
        from_imports = re.findall(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', content)
        methods.update(from_imports)
        
        # Constantes (MAIÚSCULAS)
        constants = re.findall(r'^([A-Z_][A-Z0-9_]*)\s*=', content, re.MULTILINE)
        methods.update(constants)

        return methods

    def clear_cache(self):
        """Limpa todo o cache"""
        with self._cache_lock:
            self._module_cache.clear()
            self._project_modules.clear()
            self._last_scan_time.clear()
            self._chain_cache.clear()
            self._preload_done = False

    def get_cached_modules_count(self) -> int:
        """Retorna número de módulos em cache"""
        with self._cache_lock:
            return len(self._module_cache)

    def get_cache_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o cache"""
        with self._cache_lock:
            return {
                'total_modules': len(self._module_cache),
                'preload_done': self._preload_done,
                'project_modules': len(self._project_modules),
                'chain_cache_size': len(self._chain_cache)
            }



# Instância global do gerenciador de cache
module_cache_manager = ModuleCacheManager()
