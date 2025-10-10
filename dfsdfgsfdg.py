class AutoCompleteWorker(QThread):
    suggestion_ready = QSignal(str, list)  # Emite sugestões

    def __init__(self, ide):
        super().__init__()

    self._initialize_variables()  # Inicializa variáveis básicas
    self.setup_managers()  # Gerenciadores (theme, etc.)
    self.setup_ui()  # UI principal (tabs, docks, menus)
    self.setup_connections()  # Sinais e slots
    self.setup_shortcuts()  # Atalhos globais

    # Inicializar plugins APÓS a UI estar completamente configurada
    QTimer.singleShot(100, self.setup_plugin_system)

    # Configuração global de exceções
    sys.excepthook = self.exception_hook

    # ===== SETUP DO AUTOCOMPLETE (agora no final de __init__) =====
    # Worker para autocomplete (inicia se Jedi disponível)
    self.auto_complete_worker = AutoCompleteWorker(self)
    self.auto_complete_worker.suggestion_ready.connect(self.show_completions)
    self.auto_complete_worker.start()

    # Shortcut para autocomplete (Ctrl+Space)
    self.autocomplete_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
    self.autocomplete_shortcut.activated.connect(self.trigger_autocomplete)

    # Lista para mostrar sugestões (dock simples à direita)
    self.completion_list = QListWidget()
    self.completion_list.setVisible(False)
    self.completion_dock = QDockWidget("Completions", self)
    self.completion_dock.setWidget(self.completion_list)
    self.addDockWidget(Qt.RightDockWidgetArea, self.completion_dock)

    def run(self):
        while self.running:
            if hasattr(self.ide, 'current_editor') and self.ide.current_editor and JEDI_AVAILABLE:
                # Usa Jedi para sugestões
                try:
                    source = self.ide.current_editor.toPlainText()
                    script = jedi.Script(source)
                    completions = script.complete(len(source) - 1)  # Corrige posição
                    suggestions = [comp.name for comp in completions[:10]]  # Top 10
                    self.suggestion_ready.emit(getattr(self.ide, 'current_file', ''), suggestions)
                except Exception as e:
                    print(f"❌ Erro Jedi: {e}")
                    self.suggestion_ready.emit(getattr(self.ide, 'current_file', ''), [])
            else:
                # Fallback básico (palavras comuns Python)
                fallback = ['print', 'len', 'str', 'int', 'list', 'dict', 'os', 'sys']
                self.suggestion_ready.emit(getattr(self.ide, 'current_file', ''), fallback)
            self.msleep(500)  # Checa a cada 500ms

    def stop(self):
        self.running = False
        self.quit()
        self.wait(1000)

    def show_completions(self, file_path, suggestions):
        """Mostra lista de sugestões"""
        if not suggestions:
            return
        self.completion_list.clear()
        for sug in suggestions:
            self.completion_list.addItem(sug)
        self.completion_list.setVisible(True)
        self.completion_list.raise_()  # Levanta popup

    def trigger_autocomplete(self):
        """Dispara autocomplete manual"""
        if hasattr(self, 'current_editor') and self.current_editor:
            # Simula worker para sugestões rápidas
            self.auto_complete_worker.suggestion_ready.emit(getattr(self, 'current_file', ''), [])

    def get_enhanced_suggestions(self):
        """Usa sistema híbrido Jedi + análise própria"""
        return self.completer.get_completions(
            self.text,
            self.cursor_position,
            self.file_path,
            self.project_path
        )

    def get_fallback_suggestions(self):
        """Fallback caso o novo sistema falhe"""
        suggestions = set()

        # Sugestões básicas
        keywords = [
            "if", "else", "for", "while", "def", "class", "import"]
        suggestions.update(keywords)

        # Tenta análise simples com regex
        functions = re.findall(
            r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', self.text)
        suggestions.update([f"{f}()" for f in functions])

        return sorted(list(suggestions))[:15]

    def analyze_context(self, text_before_cursor, current_line):
        """Analisa o contexto atual - NOVO MÉTODO"""
        context = {'type': 'general'}

        # Verifica se está em import
        if 'import' in current_line:
            if 'from' in current_line:
                # from module import ...
                parts = current_line.split(
                    'import')
                if len(parts) > 1:
                    module_part = parts[0].replace(
                        'from', '').strip()
                    context = {
                        'type': 'from_import', 'module': module_part}
            else:
                # import module
                context = {
                    'type': 'import'}

        # Verifica se está acessando atributo (obj.)
        elif current_line.strip().endswith('.'):
            parts = current_line.split('.')
            if len(parts) >= 2:
                # Última palavra antes
                # do ponto
                obj_name = parts[-2].split()[-1]
                context = {
                    'type': 'attribute', 'object': obj_name}

        # Verifica se está em chamada de função
        elif '(' in current_line and not current_line.strip().endswith('('):
            context = {'type': 'function_call'}

        return context


    def get_import_suggestions(self):
        """Sugestões para imports - APRIMORADO"""
        common_modules = [
            'os', 'sys', 'json', 're', 'datetime', 'math', 'random',
            'subprocess', 'shutil', 'glob', 'ast', 'inspect', 'importlib',
            'platform', 'time', 'pathlib', 'collections', 'itertools', 'functools',
            'typing', 'logging', 'unittest', 'pytest', 'numpy', 'pandas',
            'matplotlib', 'seaborn', 'tkinter', 'PySide6', 'threading', 'multiprocessing'
        ]
        return common_modules


    def get_from_import_suggestions(self, module_name):
        """Sugestões para from module import - APRIMORADO COM HARDCODED"""
        suggestions = set()

        # HARDCODED para stdlib comuns (funciona sem import
        # falhar)
        hardcoded_stdlib = {
            'tkinter': ['Tk', 'Button', 'Label', 'Entry', 'Canvas', 'Frame', 'filedialog', 'messagebox', 'simpledialog',
                        'colorchooser', 'commondialog', 'Toplevel', 'Menu', 'Checkbutton', 'Radiobutton', 'Scale',
                        'Scrollbar', 'Listbox', 'Text', 'Spinbox'],
            'threading': ['Thread', 'Lock', 'RLock', 'Condition', 'Semaphore', 'BoundedSemaphore', 'Event', 'Timer',
                          'Barrier', 'BrokenBarrierError', 'current_thread', 'main_thread', 'active_count', 'enumerate',
                          'settrace', 'setprofile'],
            'subprocess': ['Popen', 'PIPE', 'STDOUT', 'call', 'check_call', 'check_output', 'run', 'CalledProcessError',
                           'TimeoutExpired', 'CompletedProcess', 'DEVNULL'],
            'os': ['path', 'environ', 'getcwd', 'listdir', 'mkdir', 'remove', 'rename', 'system', 'walk', 'chdir',
                   'getenv', 'makedirs', 'rmdir', 'scandir'],
            'sys': ['argv', 'path', 'exit', 'version', 'platform', 'modules', 'executable', 'stdin', 'stdout', 'stderr',
                    'gettrace', 'settrace'],
            'json': ['loads', 'dumps', 'load', 'dump', 'JSONEncoder', 'JSONDecoder', 'JSONDecodeError'],
            're': ['search', 'match', 'findall', 'sub', 'compile', 'escape', 'IGNORECASE', 'MULTILINE', 'DOTALL'],
            'datetime': ['datetime', 'date', 'time', 'timedelta', 'now', 'today', 'strftime', 'strptime', 'tzinfo',
                         'timezone'],
            'math': ['sqrt', 'sin', 'cos', 'tan', 'pi', 'e', 'log', 'exp', 'ceil', 'floor', 'fabs', 'gcd'],
            'random': ['random', 'randint', 'choice', 'shuffle', 'uniform', 'seed', 'randrange', 'sample', 'choices'],
            # Adicione mais: 'collections':
            # ['defaultdict', 'namedtuple',
            # 'Counter', 'deque'], etc.
        }

        if module_name in hardcoded_stdlib:
            suggestions.update(
                hardcoded_stdlib[module_name])
            # Debug no console
            print(
                f"DEBUG: Sugestões hardcoded para '{module_name}': {list(suggestions)[:5]}...")
            return sorted(list(suggestions))

        try:
            # Tenta importar o módulo para obter
            # seus atributos
            if module_name in sys.builtin_module_names:
                # Módulos built-in
                builtin_contents = {
                    'os': ['path', 'environ', 'getcwd', 'listdir', 'mkdir', 'remove'],
                    'sys': ['argv', 'path', 'exit', 'version', 'platform'],
                    'json': ['loads', 'dumps', 'load', 'dump'],
                    're': ['search', 'match', 'findall', 'sub', 'compile', 'IGNORECASE'],
                    'datetime': ['datetime', 'date', 'time', 'timedelta', 'now', 'today']
                }
                if module_name in builtin_contents:
                    suggestions.update(
                        builtin_contents[module_name])
            else:
                # Tenta importar o
                # módulo
                module = importlib.import_module(
                    module_name)
                for attr_name in dir(
                        module):
                    if not attr_name.startswith(
                            '_'):
                        suggestions.add(
                            attr_name)
                # Debug
                print(
                    f"DEBUG: Import de '{module_name}' OK, {len(suggestions)} sugestões.")
        except ImportError as e:
            # Debug
            print(
                f"DEBUG: Erro ao importar '{module_name}': {e} (usando hardcoded se disponível).")

        return sorted(list(suggestions))


    def get_attribute_suggestions(self, obj_name):
        """Sugestões para atributos de objeto - APRIMORADO"""
        suggestions = set()

        # Métodos comuns baseados no tipo de objeto
        common_methods = {
            'str': ['upper', 'lower', 'strip', 'split', 'join', 'replace', 'find',
                    'startswith', 'endswith', 'format', 'isalpha', 'isdigit'],
            'list': ['append', 'remove', 'pop', 'sort', 'reverse', 'index', 'count',
                     'extend', 'insert', 'clear', 'copy'],
            'dict': ['get', 'keys', 'values', 'items', 'update', 'pop', 'clear',
                     'copy', 'setdefault'],
            'set': ['add', 'remove', 'discard', 'union', 'intersection', 'difference'],
            # pandas
            'df': ['head', 'tail', 'describe', 'info', 'columns', 'shape', 'loc', 'iloc'],
        }

        # Verifica se é um objeto conhecido
        for obj_type, methods in common_methods.items():
            if obj_type in obj_name.lower():
                suggestions.update(
                    [f"{m}()" for m in methods])
                break

        # Se não encontrou, adiciona métodos genéricos
        if not suggestions:
            generic_methods = ['__str__', '__repr__', '__len__', '__getitem__',
                               '__setitem__', '__iter__', '__next__']
            suggestions.update(
                [f"{m}()" for m in generic_methods])

        return suggestions


    def get_function_suggestions(self):
        """Sugestões para chamadas de função - NOVO"""
        suggestions = set()

        # Adiciona funções built-in
        builtins = [
            'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
            'range', 'input', 'open', 'type', 'sum', 'min', 'max', 'abs', 'round',
            'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter', 'any', 'all',
            'isinstance', 'issubclass', 'hasattr', 'getattr', 'setattr'
        ]
        suggestions.update([f"{b}()" for b in builtins])

        return suggestions


    def get_general_suggestions(self):
        """Sugestões gerais - COMPLETAMENTE REFEITO"""
        suggestions = set()

        # 1. Palavras-chave Python
        keywords = {
            "if", "else", "elif", "for", "while", "break", "continue", "pass", "return",
            "try", "except", "finally", "raise", "def", "class", "lambda", "global",
            "nonlocal", "import", "from", "as", "and", "or", "not", "in", "is",
            "True", "False", "None", "with", "yield", "assert", "del", "async", "await"
        }
        suggestions.update(keywords)

        # 2. Funções built-in
        builtins = [
            "print", "len", "str", "int", "float", "list", "dict", "set", "tuple",
            "range", "input", "open", "type", "sum", "min", "max", "abs", "round",
            "sorted", "reversed", "enumerate", "zip", "map", "filter", "any", "all",
            "bool", "chr", "ord", "dir", "help", "id", "isinstance", "issubclass",
            "getattr", "setattr", "hasattr", "vars", "locals", "globals", "exec", "eval"
        ]
        suggestions.update([f"{b}()" for b in builtins])

        # 3. Definições locais do arquivo atual
        local_defs = self.extract_local_definitions()
        suggestions.update(local_defs)

        # 4. Módulos importados
        imported_modules = self.extract_imported_modules()
        suggestions.update(imported_modules)

        return suggestions


    def extract_local_definitions(self):
        """Extrai definições locais do código atual - APRIMORADO"""
        definitions = set()

        try:
            # Usa regex para encontrar definições
            # rapidamente
            code = self.text

            # Funções
            func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            functions = re.findall(
                func_pattern, code)
            definitions.update(
                [f"{f}()" for f in functions])

            # Classes
            class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            classes = re.findall(
                class_pattern, code)
            definitions.update(classes)

            # Variáveis (apenas as mais
            # significativas)
            var_pattern = r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=\s]'
            var_matches = re.findall(
                var_pattern, code, re.MULTILINE)
            for _, var in var_matches:
                if len(var) > 2 and not var.startswith(
                        '_'):  # Filtra variáveis muito curtas e privadas
                    definitions.add(
                        var)

        except Exception as e:
            print(
                f"Erro ao extrair definições locais: {e}")

        return definitions

    def extract_imported_modules(self):
         """Extrai módulos importados - APRIMORADO"""
         modules = set()

        try:
              code = self.text

            Import simples: import module


             simple_imports = re.findall(
               r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
             modules.update(simple_imports)

        # Import from: from module import ...
        from_imports = re.findall(
            r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', code)
        modules.update(from_imports)

        # Import com alias: import module as
        # alias
        alias_imports = re.findall(
            r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+as', code)
        modules.update(alias_imports)

        except Exception as e:
        print(
            f"Erro ao extrair módulos importados: {e}")

    return modules
