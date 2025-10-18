# Py-Dragon-IDE

[![Python 3.9](https://img.shields.io/badge/Python-3.9-green.svg)](https://www.python.org/downloads/release/python-390/)

## Descrição

O **Py-Dragon-IDE** é um ambiente de desenvolvimento integrado (IDE) open-source projetado para competir diretamente com o Visual Studio Code (VS Code), mas otimizado para plataformas **Linux** e **Windows**. Nosso objetivo é criar uma ferramenta leve, poderosa e altamente personalizável, inspirada em editores como PyCharm e sistemas como CLIPS (para lógica de regras), com suporte expandido para linguagens como Java, C, C++ e C#. Além disso, planejamos incluir um **sistema de design visual de interfaces gráficas semelhante ao Windows Forms**, permitindo o desenvolvimento de aplicativos desktop com drag-and-drop intuitivo, integrado ao editor de código.

Atualmente, o projeto está em fase inicial de desenvolvimento e suporta **Python** como linguagem principal, além de linguagens web como **HTML, CSS e JavaScript**. Planejamos expandir rapidamente para incluir C, C++, C# e o builder de forms visual, visando uma cobertura ampla para desenvolvimento multiplataforma.

## Recursos Atuais

- **Editor de Código Inteligente**: Sintaxe highlight, autocompletar e linting para Python e linguagens web.
- **Suporte Multiplataforma**: Funciona nativamente em Linux e Windows.
- **Integração com Terminal**: Execução de scripts Python diretamente no IDE.
- **Extensibilidade**: Baseada em plugins para adicionar suporte a novas linguagens (ex: C, C++ e C# em breve).
- **Interface Minimalista**: Inspirada no VS Code, mas com foco em performance para máquinas de baixa configuração.

## Recursos Planejados

- **Designer Visual de Forms**: Um sistema semelhante ao Windows Forms para criação de GUIs desktop em Python (usando bibliotecas como Tkinter ou PyQt). Inclui drag-and-drop de componentes, preview em tempo real e geração automática de código.
- **Integração com Bibliotecas GUI**: Suporte nativo para Tkinter, PyQt e Kivy, com templates prontos para apps multiplataforma.

## Requisitos

- **Python**: Versão 3.9 ou superior.
- **Sistema Operacional**: Linux (distribuições baseadas em Debian/Ubuntu recomendadas) ou Windows 10/11.
- **Dependências**: Instaladas via `pip` (veja abaixo).

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/CodexMelo/Py-Dragon-IDE.git
   cd Py-Dragon-IDE
   ```

2. Crie um ambiente virtual (recomendado):
   ```
   python -m venv venv
   source venv/bin/activate  # No Linux
   # Ou no Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Execute o IDE:
   ```
   python main.py
   ```

> **Nota**: O arquivo `requirements.txt` será adicionado em breve com as bibliotecas iniciais (ex: Tkinter para GUI, Pygments para highlight). Para o designer de forms, incluiremos suporte a `tkinter` e `pyqt5` nas próximas atualizações.

## Uso

- Abra o IDE e crie um novo projeto Python ou web.
- Use `Ctrl + S` para salvar, `F5` para executar (Python).
- Para linguagens web, use o visualizador integrado para preview de HTML/CSS/JS.
- **Futuro**: Acesse o Designer de Forms via menu "Ferramentas" para criar interfaces visuais.

Exemplo de script Python simples:
```python
print("Olá, mundo do Py-Dragon-IDE!")
```

Exemplo conceitual de uso do Designer de Forms (geração automática de código):
```python
# Código gerado pelo Designer
import tkinter as tk

root = tk.Tk()
root.title("Meu App - Gerado pelo Py-Dragon-IDE")

label = tk.Label(root, text="Olá, Windows Forms-like!")
label.pack()

button = tk.Button(root, text="Clique Aqui", command=lambda: print("Botão clicado!"))
button.pack()

root.mainloop()
```

## Linguagens Suportadas

| Linguagem | Suporte Atual | Status Futuro |
|-----------|---------------|---------------|
| Python   | ✅ Completo  | -            |
| HTML/CSS | ✅ Básico    | Avançado     |
| JavaScript | ✅ Básico  | Avançado     |
| Java     | ❌ Não      | Planejado    |
| CLIPS    | ❌ Não      | Planejado    |
| C        | ❌ Não      | Planejado    |
| C++      | ❌ Não      | Planejado   |
| C#       | ❌ Não      | Planejado   |

## Roadmap

- **Versão 0.1**: Suporte básico a Python e web (em progresso).
- **Versão 0.2**: Integração de debugger e suporte a Java.
- **Versão 0.3**: Adição de suporte a C e C++, com compilação integrada via GCC/Clang; introdução inicial do Designer de Forms para Python.
- **Versão 0.4**: Suporte a C# com integração ao .NET para Windows/Linux; expansão do Designer de Forms com suporte a PyQt.
- **Versão 1.0**: Competição total com VS Code – temas, extensões, Git integration e suporte completo a CLIPS; Designer de Forms maduro, compatível com Windows Forms.
- **Futuro**: Expansão para mais linguagens e ferramentas de depuração avançadas para C/C++/C#; exportação de forms para multiplataforma (Linux/Windows).

## Contribuições

Contribuições são bem-vindas! Siga estes passos:
1. Fork o repositório.
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`).
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`).
4. Push para a branch (`git push origin feature/nova-funcionalidade`).
5. Abra um Pull Request.

Por favor, leia o [Código de Conduta](CODE_OF_CONDUCT.md) antes de contribuir. Contribuições para o Designer de Forms (semelhante ao Windows Forms) ou suporte inicial a C, C++ ou C# são especialmente incentivadas!

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## Contato

- **Autor**: CodexMelo
- **Issues**: [Abra uma issue](https://github.com/CodexMelo/Py-Dragon-IDE/issues)
- **Discussões**: Participe das discussões no repositório.

Obrigado por apoiar o Py-Dragon-IDE! 🐉✨
