
class CodeTemplates:
    """Templates de código para diferentes linguagens"""
    
    # ===== PYTHON =====
    PYTHON_TEMPLATES = {
        # Estruturas de controle
        'for_loop': 'for {var} in range({start}, {end}):\n    {cursor}',
        'for_loop_with_step': 'for {var} in range({start}, {end}, {step}):\n    {cursor}',
        'for_loop_list': 'for {item} in {list_name}:\n    {cursor}',
        'for_loop_enumerate': 'for {index}, {item} in enumerate({list_name}):\n    {cursor}',
        'while_loop': 'while {condition}:\n    {cursor}',
        'if_statement': 'if {condition}:\n    {cursor}',
        'if_else': 'if {condition}:\n    {cursor}\nelse:\n    ',
        'if_elif_else': 'if {condition1}:\n    {cursor}\nelif {condition2}:\n    \nelse:\n    ',
        
        # Funções
        'function_def': 'def {function_name}({parameters}):\n    """{docstring}"""\n    {cursor}',
        'class_def': 'class {class_name}:\n    """{docstring}"""\n    \n    def __init__(self{parameters}):\n        {cursor}',
        'method_def': 'def {method_name}(self{parameters}):\n    """{docstring}"""\n    {cursor}',
        'staticmethod_def': '@staticmethod\ndef {method_name}({parameters}):\n    """{docstring}"""\n    {cursor}',
        'classmethod_def': '@classmethod\ndef {method_name}(cls{parameters}):\n    """{docstring}"""\n    {cursor}',
        
        # Estruturas de dados
        'list_comprehension': '[{expression} for {item} in {iterable} if {condition}]',
        'dict_comprehension': '{{ {key}: {value} for {item} in {iterable} if {condition} }}',
        'set_comprehension': '{{ {expression} for {item} in {iterable} if {condition} }}',
        'generator_expression': '({expression} for {item} in {iterable} if {condition})',
        
        # Tratamento de exceções
        'try_except': 'try:\n    {cursor}\nexcept {Exception} as e:\n    ',
        'try_except_finally': 'try:\n    {cursor}\nexcept {Exception} as e:\n    \nfinally:\n    ',
        'try_multiple_except': 'try:\n    {cursor}\nexcept {Exception1}:\n    \nexcept {Exception2}:\n    ',
        
        # Context managers
        'with_statement': 'with {context} as {var}:\n    {cursor}',
        
        # Imports comuns
        'import_os': 'import os',
        'import_sys': 'import sys',
        'import_json': 'import json',
        'import_datetime': 'import datetime',
        'import_from_datetime': 'from datetime import datetime, date, time',
        'import_pathlib': 'from pathlib import Path',
        
        # Testes
        'unittest_method': 'def test_{method_name}(self):\n    """Test {method_name}"""\n    {cursor}',
        'pytest_function': 'def test_{function_name}():\n    """Test {function_name}"""\n    {cursor}',
        
        # Docstrings
        'docstring_function': '"""\n{description}\n\nArgs:\n    {parameters}\n\nReturns:\n    {return_value}\n"""',
        'docstring_class': '"""\n{description}\n\nAttributes:\n    {attributes}\n"""',
        
        # Métodos mágicos
        '__str__': 'def __str__(self):\n    return f"{self.__class__.__name__}(...)"',
        '__repr__': 'def __repr__(self):\n    return f"{self.__class__.__name__}(...)"',
        '__init__': 'def __init__(self{parameters}):\n    {cursor}',
        
        # Padrões comuns
        'main_block': 'if __name__ == "__main__":\n    {cursor}',
        'shebang': '#!/usr/bin/env python3',
        'encoding': '# -*- coding: utf-8 -*-'
    }
    
    # ===== JAVASCRIPT =====
    JAVASCRIPT_TEMPLATES = {
        # Funções
        'function_def': 'function {functionName}({parameters}) {{\n    {cursor}\n}}',
        'arrow_function': 'const {functionName} = ({parameters}) => {{\n    {cursor}\n}}',
        'async_function': 'async function {functionName}({parameters}) {{\n    {cursor}\n}}',
        'anonymous_function': 'function({parameters}) {{\n    {cursor}\n}}',
        
        # Estruturas de controle
        'for_loop': 'for (let {var} = {start}; {var} < {end}; {var}++) {{\n    {cursor}\n}}',
        'for_of_loop': 'for (const {item} of {array}) {{\n    {cursor}\n}}',
        'for_in_loop': 'for (const {key} in {object}) {{\n    {cursor}\n}}',
        'while_loop': 'while ({condition}) {{\n    {cursor}\n}}',
        'do_while': 'do {{\n    {cursor}\n}} while ({condition})',
        'if_statement': 'if ({condition}) {{\n    {cursor}\n}}',
        'if_else': 'if ({condition}) {{\n    {cursor}\n}} else {{\n    \n}}',
        'switch_case': 'switch ({variable}) {{\n    case {value1}:\n        {cursor}\n        break;\n    case {value2}:\n        break;\n    default:\n        break;\n}}',
        
        # Classes
        'class_def': 'class {ClassName} {{\n    constructor({parameters}) {{\n        {cursor}\n    }}\n}}',
        'class_method': '{methodName}({parameters}) {{\n    {cursor}\n}}',
        
        # Eventos
        'event_listener': '{element}.addEventListener(\'{event}\', function(e) {{\n    {cursor}\n}})',
        'arrow_event_listener': '{element}.addEventListener(\'{event}\', (e) => {{\n    {cursor}\n}})',
        
        # Promises
        'promise': 'new Promise((resolve, reject) => {{\n    {cursor}\n}})',
        'async_await': 'async function {functionName}() {{\n    try {{\n        {cursor}\n    }} catch (error) {{\n        console.error(error);\n    }}\n}}',
        
        # Arrays
        'map_function': '{array}.map(({item}) => {{\n    return {cursor}\n}})',
        'filter_function': '{array}.filter(({item}) => {{\n    return {cursor}\n}})',
        'reduce_function': '{array}.reduce((accumulator, {item}) => {{\n    return {cursor}\n}}, {initialValue})',
        
        # Console
        'console_log': 'console.log({variable})',
        'console_error': 'console.error({variable})',
        'console_warn': 'console.warn({variable})',
        
        # DOM
        'get_element_by_id': 'document.getElementById(\'{id}\')',
        'query_selector': 'document.querySelector(\'{selector}\')',
        'query_selector_all': 'document.querySelectorAll(\'{selector}\')'
    }
    
    # ===== HTML =====
    HTML_TEMPLATES = {
        # Estrutura básica
        'html5_boilerplate': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{css_file}">
</head>
<body>
    {cursor}
    <script src="{js_file}"></script>
</body>
</html>''',
        
        # Elementos comuns
        'div': '<div{class}>{content}</div>',
        'span': '<span{class}>{content}</span>',
        'paragraph': '<p{class}>{content}</p>',
        'heading1': '<h1{class}>{content}</h1>',
        'heading2': '<h2{class}>{content}</h2>',
        'heading3': '<h3{class}>{content}</h3>',
        'link': '<a href="{url}"{class}>{content}</a>',
        'image': '<img src="{src}" alt="{alt}"{class}>',
        'button': '<button type="{type}"{class}>{content}</button>',
        'input_text': '<input type="text" name="{name}" id="{id}"{class}>',
        'input_email': '<input type="email" name="{name}" id="{id}"{class}>',
        'input_password': '<input type="password" name="{name}" id="{id}"{class}>',
        'textarea': '<textarea name="{name}" id="{id}"{class}>{content}</textarea>',
        'form': '<form action="{action}" method="{method}"{class}>\n    {cursor}\n</form>',
        'list_ordered': '<ol{class}>\n    <li>{item1}</li>\n    <li>{item2}</li>\n</ol>',
        'list_unordered': '<ul{class}>\n    <li>{item1}</li>\n    <li>{item2}</li>\n</ul>',
        'table': '''<table{class}>
    <thead>
        <tr>
            <th>{header1}</th>
            <th>{header2}</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>{data1}</td>
            <td>{data2}</td>
        </tr>
    </tbody>
</table>''',
        
        # Meta tags
        'meta_charset': '<meta charset="UTF-8">',
        'meta_viewport': '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        'meta_description': '<meta name="description" content="{description}">',
        'meta_keywords': '<meta name="keywords" content="{keywords}">',
        
        # Links e scripts
        'css_link': '<link rel="stylesheet" href="{css_file}">',
        'javascript': '<script src="{js_file}"></script>',
        'inline_script': '<script>\n    {cursor}\n</script>',
        'inline_style': '<style>\n    {cursor}\n</style>'
    }
    
    # ===== CSS =====
    CSS_TEMPLATES = {
        # Seletores
        'class_selector': '.{className} {{\n    {cursor}\n}}',
        'id_selector': '#{idName} {{\n    {cursor}\n}}',
        'element_selector': '{element} {{\n    {cursor}\n}}',
        'media_query': '@media ({condition}) {{\n    {cursor}\n}}',
        
        # Flexbox
        'flex_container': 'display: flex;\nflex-direction: {direction};\njustify-content: {justify};\nalign-items: {align};',
        'flex_item': 'flex: {grow} {shrink} {basis};',
        
        # Grid
        'grid_container': 'display: grid;\ngrid-template-columns: {columns};\ngrid-template-rows: {rows};\ngap: {gap};',
        'grid_item': 'grid-column: {column};\ngrid-row: {row};',
        
        # Posicionamento
        'position_absolute': 'position: absolute;\ntop: {top};\nleft: {left};\nright: {right};\nbottom: {bottom};',
        'position_relative': 'position: relative;',
        'position_fixed': 'position: fixed;\ntop: {top};\nleft: {left};\nright: {right};\nbottom: {bottom};',
        
        # Box model
        'box_sizing': 'box-sizing: border-box;',
        'margin_padding': 'margin: {margin};\npadding: {padding};',
        'border': 'border: {width} {style} {color};',
        'border_radius': 'border-radius: {radius};',
        
        # Tipografia
        'font_properties': 'font-family: {family};\nfont-size: {size};\nfont-weight: {weight};\nline-height: {height};',
        'text_align': 'text-align: {alignment};',
        'text_decoration': 'text-decoration: {decoration};',
        
        # Cores e fundos
        'background': 'background: {color};\nbackground-image: url({image});\nbackground-size: {size};\nbackground-position: {position};',
        'gradient_linear': 'background: linear-gradient({direction}, {color1}, {color2});',
        'gradient_radial': 'background: radial-gradient({shape} at {position}, {color1}, {color2});',
        
        # Animações
        'keyframes': '@keyframes {name} {{\n    from {{\n        {start_properties}\n    }}\n    to {{\n        {end_properties}\n    }}\n}}',
        'animation': 'animation: {name} {duration} {timing} {delay} {iteration} {direction};',
        'transition': 'transition: {property} {duration} {timing} {delay};',
        
        # Responsive design
        'mobile_first': '@media (min-width: {breakpoint}) {{\n    {cursor}\n}}',
        'desktop_first': '@media (max-width: {breakpoint}) {{\n    {cursor}\n}}'
    }
    
    # ===== SQL =====
    SQL_TEMPLATES = {
        # Consultas básicas
        'select_all': 'SELECT * FROM {table_name};',
        'select_columns': 'SELECT {column1}, {column2} FROM {table_name};',
        'select_where': 'SELECT * FROM {table_name} WHERE {condition};',
        'select_order_by': 'SELECT * FROM {table_name} ORDER BY {column} {direction};',
        'select_limit': 'SELECT * FROM {table_name} LIMIT {limit};',
        
        # Junções
        'inner_join': '''SELECT {columns}
FROM {table1}
INNER JOIN {table2} ON {table1}.{column} = {table2}.{column};''',
        'left_join': '''SELECT {columns}
FROM {table1}
LEFT JOIN {table2} ON {table1}.{column} = {table2}.{column};''',
        
        # Agregações
        'count': 'SELECT COUNT(*) FROM {table_name};',
        'sum': 'SELECT SUM({column}) FROM {table_name};',
        'avg': 'SELECT AVG({column}) FROM {table_name};',
        'group_by': 'SELECT {column}, COUNT(*) FROM {table_name} GROUP BY {column};',
        
        # Inserção/Atualização
        'insert': 'INSERT INTO {table_name} ({columns}) VALUES ({values});',
        'update': 'UPDATE {table_name} SET {column} = {value} WHERE {condition};',
        'delete': 'DELETE FROM {table_name} WHERE {condition};',
        
        # Criação de tabelas
        'create_table': '''CREATE TABLE {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {column1} {type1},
    {column2} {type2},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);''',
        
        # Índices
        'create_index': 'CREATE INDEX {index_name} ON {table_name} ({column});'
    }
    
    # ===== C/C++ =====
    C_CPP_TEMPLATES = {
        # Estruturas básicas
        'main_function': 'int main(int argc, char *argv[]) {{\n    {cursor}\n    return 0;\n}}',
        'include_guard': '''#ifndef {HEADER_NAME}_H
#define {HEADER_NAME}_H

{cursor}

#endif // {HEADER_NAME}_H''',
        
        # Loops
        'for_loop': 'for (int {var} = {start}; {var} < {end}; {var}++) {{\n    {cursor}\n}}',
        'while_loop': 'while ({condition}) {{\n    {cursor}\n}}',
        'do_while': 'do {{\n    {cursor}\n}} while ({condition});',
        
        # Condicionais
        'if_statement': 'if ({condition}) {{\n    {cursor}\n}}',
        'if_else': 'if ({condition}) {{\n    {cursor}\n}} else {{\n    \n}}',
        'switch_case': 'switch ({variable}) {{\n    case {value1}:\n        {cursor}\n        break;\n    case {value2}:\n        break;\n    default:\n        break;\n}}',
        
        # Funções
        'function_def': '{return_type} {function_name}({parameters}) {{\n    {cursor}\n}}',
        'function_declaration': '{return_type} {function_name}({parameters});',
        
        # Estruturas
        'struct_def': 'struct {struct_name} {{\n    {member1_type} {member1_name};\n    {member2_type} {member2_name};\n}};',
        'typedef_struct': 'typedef struct {{\n    {member1_type} {member1_name};\n    {member2_type} {member2_name};\n}} {struct_name};',
        
        # Ponteiros
        'pointer_declaration': '{type} *{pointer_name} = &{variable};',
        'dynamic_allocation': '{type} *{pointer_name} = ({type}*)malloc({size} * sizeof({type}));',
        'dynamic_free': 'free({pointer_name});',
        
        # Classes C++
        'class_def': '''class {ClassName} {{
public:
    {ClassName}();
    ~{ClassName}();
    
private:
    {cursor}
}};''',
        'constructor': '{ClassName}::{ClassName}() {{\n    {cursor}\n}}',
        'destructor': '{ClassName}::~{ClassName}() {{\n    {cursor}\n}}'
    }

    @classmethod
    def get_templates_for_language(cls, language):
        """Retorna templates para uma linguagem específica"""
        templates_map = {
            'python': cls.PYTHON_TEMPLATES,
            'javascript': cls.JAVASCRIPT_TEMPLATES,
            'html': cls.HTML_TEMPLATES,
            'css': cls.CSS_TEMPLATES,
            'sql': cls.SQL_TEMPLATES,
            'c': cls.C_CPP_TEMPLATES,
            'cpp': cls.C_CPP_TEMPLATES
        }
        return templates_map.get(language.lower(), {})

    @classmethod
    def get_template(cls, language, template_name, **kwargs):
        """Retorna um template específico com placeholders substituídos"""
        templates = cls.get_templates_for_language(language)
        template = templates.get(template_name, '')
        
        # Substitui placeholders
        for key, value in kwargs.items():
            placeholder = '{' + key + '}'
            template = template.replace(placeholder, str(value))
        
        # Remove placeholders não substituídos
        import re
        template = re.sub(r'\{[^}]+\}', '', template)
        
        return template


class CodeSnippets:
    """Snippets de código reutilizáveis"""
    
    # ===== SNIPPETS PYTHON =====
    PYTHON_SNIPPETS = {
        # File operations
        'read_file': '''with open('{filename}', 'r', encoding='utf-8') as file:
    content = file.read()''',
        
        'write_file': '''with open('{filename}', 'w', encoding='utf-8') as file:
    file.write({content})''',
        
        'read_lines': '''with open('{filename}', 'r', encoding='utf-8') as file:
    lines = file.readlines()''',
        
        # JSON
        'json_load': '''import json
with open('{filename}', 'r') as file:
    data = json.load(file)''',
        
        'json_dump': '''import json
with open('{filename}', 'w') as file:
    json.dump({data}, file, indent=4)''',
        
        # Datetime
        'current_time': '''from datetime import datetime
now = datetime.now()
formatted = now.strftime('%Y-%m-%d %H:%M:%S')''',
        
        # Requests (se disponível)
        'http_get': '''import requests
response = requests.get('{url}')
if response.status_code == 200:
    data = response.json()''',
        
        # List operations
        'list_to_string': "', '.join({list})",
        'string_to_list': "{string}.split('{separator}')",
        
        # Dictionary operations
        'dict_get': "{dict}.get('{key}', {default})",
        'dict_comprehension_filter': "{{k: v for k, v in {dict}.items() if {condition}}}",
        
        # Decorators
        'timer_decorator': '''import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper''',
        
        'singleton_decorator': '''def singleton(cls):
    instances = {}
    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return wrapper'''
    }
    
    # ===== SNIPPETS JAVASCRIPT =====
    JAVASCRIPT_SNIPPETS = {
        # AJAX/Fetch
        'fetch_get': '''fetch('{url}')
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));''',
        
        'fetch_post': '''fetch('{url}', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({data})
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));''',
        
        # Array methods
        'array_map': '{array}.map({item} => {expression})',
        'array_filter': '{array}.filter({item} => {condition})',
        'array_reduce': '{array}.reduce((acc, {item}) => acc + {item}, {initial})',
        
        # Object operations
        'object_destructuring': 'const {{ {property1}, {property2} }} = {object}',
        'object_spread': 'const newObject = {{ ...{object}, {newProperty}: {value} }}',
        
        # String operations
        'template_literal': '`String with ${variable} and ${expression}`',
        'string_interpolation': '`Text ${variable} more text`',
        
        # Local Storage
        'localstorage_set': 'localStorage.setItem("{key}", {value})',
        'localstorage_get': 'const value = localStorage.getItem("{key}")',
        'localstorage_remove': 'localStorage.removeItem("{key}")',
        
        # Event handling
        'event_prevent_default': 'event.preventDefault()',
        'event_stop_propagation': 'event.stopPropagation()'
    }
    
    # ===== SNIPPETS HTML =====
    HTML_SNIPPETS = {
        'favicon': '<link rel="icon" type="image/x-icon" href="/favicon.ico">',
        'meta_refresh': '<meta http-equiv="refresh" content="{seconds}">',
        'canonical_url': '<link rel="canonical" href="{url}">',
        'open_graph': '''<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{image_url}">''',
        
        'responsive_image': '''<img 
    src="{src}" 
    srcset="{srcset}"
    sizes="{sizes}"
    alt="{alt}"
    class="{class}">''',
        
        'video_element': '''<video controls width="{width}">
    <source src="{video_url}" type="video/mp4">
    Your browser does not support the video tag.
</video>'''
    }

    @classmethod
    def get_snippet(cls, language, snippet_name, **kwargs):
        """Retorna um snippet específico"""
        snippets_map = {
            'python': cls.PYTHON_SNIPPETS,
            'javascript': cls.JAVASCRIPT_SNIPPETS,
            'html': cls.HTML_SNIPPETS
        }
        
        snippets = snippets_map.get(language.lower(), {})
        snippet = snippets.get(snippet_name, '')
        
        # Substitui placeholders
        for key, value in kwargs.items():
            placeholder = '{' + key + '}'
            snippet = snippet.replace(placeholder, str(value))
        
        return snippet


class LanguageCompleter:
    """Classe para gerenciar autocompletions específicas por linguagem"""
    
    def __init__(self):
        self.templates = CodeTemplates()
        self.snippets = CodeSnippets()
    
    def get_completions(self, language, context=""):
        """Retorna completions para uma linguagem específica"""
        completions = {}
        
        # Adiciona templates
        templates = self.templates.get_templates_for_language(language)
        for name, template in templates.items():
            completions[name] = {
                'type': 'template',
                'content': template,
                'description': f"Template: {name}"
            }
        
        # Adiciona snippets se disponíveis
        snippets_map = {
            'python': self.snippets.PYTHON_SNIPPETS,
            'javascript': self.snippets.JAVASCRIPT_SNIPPETS,
            'html': self.snippets.HTML_SNIPPETS
        }
        
        snippets = snippets_map.get(language, {})
        for name, snippet in snippets.items():
            completions[name] = {
                'type': 'snippet',
                'content': snippet,
                'description': f"Snippet: {name}"
            }
        
        return completions
    
    def expand_completion(self, language, completion_name, **kwargs):
        """Expande um completion com valores específicos"""
        # Tenta como template primeiro
        template = self.templates.get_template(language, completion_name, **kwargs)
        if template:
            return template
        
        # Tenta como snippet
        snippet = self.snippets.get_snippet(language, completion_name, **kwargs)
        if snippet:
            return snippet
        
        return ""


# Instância global para uso fácil
completer = LanguageCompleter()


# Funções de utilidade para integração rápida
def quick_template(language, template_name, **kwargs):
    """Função rápida para obter templates"""
    return CodeTemplates.get_template(language, template_name, **kwargs)


def quick_snippet(language, snippet_name, **kwargs):
    """Função rápida para obter snippets"""
    return CodeSnippets.get_snippet(language, snippet_name, **kwargs)


def get_available_templates(language):
    """Retorna lista de templates disponíveis para uma linguagem"""
    return list(CodeTemplates.get_templates_for_language(language).keys())


def get_available_snippets(language):
    """Retorna lista de snippets disponíveis para uma linguagem"""
    snippets_map = {
        'python': CodeSnippets.PYTHON_SNIPPETS,
        'javascript': CodeSnippets.JAVASCRIPT_SNIPPETS,
        'html': CodeSnippets.HTML_SNIPPETS
    }
    snippets = snippets_map.get(language, {})
    return list(snippets.keys())


# Exemplo de uso:
if __name__ == "__main__":
    # Exemplos de uso dos templates
    print("=== Python For Loop ===")
    print(quick_template('python', 'for_loop', var='i', start='0', end='10', cursor='print(i)'))
    
    print("\n=== JavaScript Function ===")
    print(quick_template('javascript', 'function_def', functionName='calculateSum', parameters='a, b', cursor='return a + b;'))
    
    print("\n=== HTML Boilerplate ===")
    print(quick_template('html', 'html5_boilerplate', title='My Page', css_file='style.css', js_file='script.js', cursor='<h1>Hello World</h1>'))
    
    print("\n=== CSS Flexbox ===")
    print(quick_template('css', 'flex_container', direction='row', justify='center', align='center'))
    
    print("\n=== Python Snippet ===")
    print(quick_snippet('python', 'read_file', filename='data.txt'))
    
    print("\n=== Available Python Templates ===")
    print(get_available_templates('python')[:5])  # Primeiros 5