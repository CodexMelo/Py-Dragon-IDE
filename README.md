# 🐉 Py Dragon Studio IDE

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-green)](https://doc.qt.io/qt-6/pyside6.html)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-yellow)](https://github.com/CodexMelo/Py-Dragon-IDE)

**Uma IDE Python moderna e completa** com foco em produtividade, experiência do desenvolvedor e desenvolvimento multi-linguagem.

---

## ✨ Características Principais

### 🎯 **Editor Inteligente**
- **Syntax highlighting** para múltiplas linguagens (Python, JavaScript, HTML, CSS, Java, C++, etc.)
- **Autocomplete inteligente** com análise de contexto e sugestões baseadas em imports
- **Sistema LSP integrado** (python-lsp-server) para análise de código em tempo real
- **Formatação automática** de código com múltiplos formatadores
- **Correção de indentação** automática
- **Navegação por símbolos** e estrutura do código

### 🔧 **Ferramentas de Desenvolvimento**
- **Terminal integrado** com suporte a comandos shell
- **Sistema de debug** integrado com pdb
- **Linting em tempo real** com pylint
- **Gerenciador de pacotes Python** integrado
- **Controle de versões Git** integrado
- **Virtualenv management** automático

### 📁 **Gerenciamento de Projetos**
- **Estrutura de projetos** com templates pré-configurados
- **Explorador de arquivos** com navegação rápida
- **Busca e substituição** avançada com regex
- **Minimap** para navegação em arquivos grandes
- **Multi-abas** com organização flexível

### 🎨 **Interface Moderna**
- **Temas personalizáveis** (Dark Professional, Monokai, Solarized, etc.)
- **Interface responsiva** com docks redimensionáveis
- **Layouts customizáveis** com divisão de tela
- **Atalhos personalizáveis**
- **Barra de status** informativa

### 🔌 **Sistema de Plugins**
- **Arquitetura modular** para extensões
- **Plugins incluídos**: Formatador, Git, Métricas, Snippets
- **API para desenvolvimento** de novos plugins
- **Gerenciador de plugins** integrado

---

## 🚀 Instalação e Uso

### Pré-requisitos
- Python 3.8 ou superior
- PySide6
- Dependências opcionais para funcionalidades avançadas

### Instalação Rápida
```bash
# Clone o repositório
git clone https://github.com/CodexMelo/Py-Dragon-IDE.git
cd Py-Dragon-IDE

# Instale as dependências
pip install PySide6 python-lsp-server pylint autopep8

# Execute o launcher
python py_dragon_launcher.py
```

### Execução Direta
```bash
# Para executar diretamente a IDE
python py_dragon_ide.py

# Ou com projeto específico
python py_dragon_ide.py --project /caminho/do/projeto --python 3.11
```

---

## 🛠️ Funcionalidades Detalhadas

### Editor de Código
- **Realce de sintaxe** para 20+ linguagens de programação
- **Autocomplete contextual** baseado em análise estática e LSP
- **Fold de código** para melhor organização
- **Números de linha** e indicadores de erro
- **Seleção múltipla** e edição em múltiplos cursores
- **Zoom** e configurações de fonte

### Desenvolvimento Python
- **Execução de código** com captura de output em tempo real
- **Debug integrado** com breakpoints e inspeção de variáveis
- **Análise de código** com pylint e flake8
- **Cobertura de testes** integrada
- **Virtualenv** automático por projeto

### Ferramentas de Produtividade
- **Gerenciador de snippets** com biblioteca personalizável
- **Busca em projeto** por texto e arquivos
- **Comparação de arquivos** integrada
- **Histórico de comandos** no terminal
- **Exportação de projetos** para executáveis

### Integrações
- **Git** integrado para controle de versão
- **Terminal** com suporte a múltiplos shells
- **Gerenciador de pacotes** pip integrado
- **Servidor LSP** para inteligência de código
- **API para extensões** personalizadas

---

## 📦 Estrutura do Projeto

```
Py-Dragon-IDE/
├── core/                    # Núcleo da IDE
│   ├── editor/             # Sistema de edição
│   ├── lsp/               # Cliente LSP
│   ├── plugins/           # Sistema de plugins
│   └── project/           # Gerenciamento de projetos
├── features/              # Funcionalidades
│   ├── autocomplete/      # Sistema de autocomplete
│   ├── debug/            # Depurador integrado
│   ├── linting/          # Análise de código
│   └── terminal/         # Terminal integrado
├── ui/                    # Interface do usuário
│   ├── themes/           # Sistema de temas
│   ├── widgets/          # Componentes personalizados
│   └── dialogs/          # Diálogos e janelas
├── utils/                 # Utilitários
│   ├── syntax/           # Realce de sintaxe
│   ├── analyzers/        # Analisadores de código
│   └── cache/            # Sistema de cache
└── launcher/             # Launcher de projetos
```

---

## 🔧 Configuração

### Teclas de Atalho Principais
- `Ctrl+N` - Novo arquivo
- `Ctrl+O` - Abrir arquivo  
- `Ctrl+S` - Salvar arquivo
- `Ctrl+Shift+S` - Salvar como
- `Ctrl+Space` - Autocomplete
- `F5` - Executar código
- `F6` - Debug
- `Ctrl+F` - Buscar
- `Ctrl+Shift+F` - Buscar em projeto

### Configurações de Projeto
- **Python interpreter** por projeto
- **Virtualenv** automático
- **Estrutura de pastas** personalizável
- **Configurações de linting** específicas
- **Variáveis de ambiente** do projeto

---

## 🐛 Problemas Conhecidos e Status

### ✅ Funcionalidades Estáveis
- ✅ Editor de código base
- ✅ Syntax highlighting multi-linguagem
- ✅ Terminal integrado
- ✅ Sistema de projetos
- ✅ Gerenciador de arquivos
- ✅ Execução de código Python
- ✅ Sistema de temas

### 🔄 Em Desenvolvimento
- 🔄 Sistema LSP (estável para Python)
- 🔄 Autocomplete inteligente
- 🔄 Debug integrado
- 🔄 Sistema de plugins
- 🔄 Performance do editor

### 🚧 Problemas Conhecidos
- 🚧 **Autocomplete**: Às vezes lento em projetos muito grandes
- 🚧 **LSP**: Configuração requer python-lsp-server instalado
- 🚧 **Performance**: Pode ser lento em máquinas com poucos recursos
- 🚧 **Terminal**: Problemas esporádicos de encoding no Windows

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Areas onde você pode ajudar:

### Desenvolvimento
- **Melhorar performance** do editor
- **Otimizar sistema LSP**
- **Implementar novas linguagens**
- **Criar novos plugins**

### Testes e Qualidade
- **Reportar bugs** e issues
- **Testar em diferentes sistemas**
- **Melhorar documentação**
- **Criar testes automatizados**

### Como Contribuir
1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🔮 Roadmap Futuro

### Próximas Versões
- [ ] Suporte completo para C/C++ com CLangd
- [ ] Integração com JavaScript/TypeScript
- [ ] Debug visual com inspeção de variáveis
- [ ] Sistema de testes integrado
- [ ] Deploy automático para nuvem
- [ ] Integração com IA para code generation

### Versões Futuras
- [ ] Suporte para desenvolvimento web full-stack
- [ ] Integração com bancos de dados
- [ ] Desenvolvimento mobile
- [ ] Cloud IDE version
- [ ] Marketplace de plugins

---

## 📞 Suporte

- **Documentação**: [Em desenvolvimento]
- **Issues**: [GitHub Issues](https://github.com/CodexMelo/Py-Dragon-IDE/issues)
- **Email**: [Em breve]

---

## 🙏 Agradecimentos

- **Qt/PySide6** pelo framework de UI
- **Python LSP Server** pela base do sistema LSP
- **Comunidade Python** pelas bibliotecas e ferramentas
- **Contribuidores** que ajudaram no desenvolvimento

---

**Py Dragon Studio IDE** - Potencialize seu desenvolvimento Python! 🐉🚀
