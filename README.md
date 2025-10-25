
---

<h1 align="center">🐉 Py-Dragon-IDE</h1>

<p align="center">
  <b>IDE open-source, leve, poderosa e altamente personalizável</b><br>
  Inspirada em VS Code e PyCharm, com suporte inicial a Python e linguagens web.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Plataforma-Linux%20|%20Windows-blueviolet?style=for-the-badge" alt="Plataforma">
  <img src="https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Licença-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/github/downloads/CodexMelo/Py-Dragon-IDE/total?style=for-the-badge" alt="Downloads">
</p>

---

## 🚀 Sobre o Projeto

**Py-Dragon-IDE** é uma IDE **open-source**, leve e moderna, focada em **Python** e linguagens web (**HTML, CSS, JS**), com suporte futuro a **Java, C, C++ e C#**.  

Inspirada em editores modernos e sistemas de regras como CLIPS, o projeto combina:

- **Leveza e performance**, ideal para máquinas de baixa configuração  
- **Extensibilidade via plugins** para novas linguagens e ferramentas  
- **Designer Visual de Forms**, para criar GUIs desktop com drag-and-drop intuitivo  

> Objetivo: fornecer uma IDE completa e personalizável, que permita desenvolvimento multiplataforma eficiente.

---

## ✨ Recursos Atuais

- 💻 **Editor de Código Inteligente:** Sintaxe highlight, autocompletar e linting  
- 🖥 **Suporte Multiplataforma:** Linux e Windows  
- 🧰 **Terminal Integrado:** Execute scripts Python diretamente  
- 🔧 **Extensibilidade via Plugins:** Adicione suporte a novas linguagens (C, C++, C#)  
- 🌈 **Interface Minimalista:** Inspirada no VS Code, com foco em performance  

---

## ⚡ Recursos Planejados

- 🖌 **Designer Visual de Forms:** Drag-and-drop, preview em tempo real, geração automática de código  
- 📦 **Integração GUI:** Tkinter, PyQt, Kivy com templates multiplataforma  
- 🧑‍💻 **Suporte a Linguagens Compiladas:** C, C++, C#  
- 🐞 **Depurador Interno:** Python e futuras linguagens  
- 🌐 **Loja de Plugins Online:** Instalação e gerenciamento direto de extensões  

---

## 🛠️ Requisitos

- **Python:** 3.9 ou superior  
- **SO:** Linux (Debian/Ubuntu recomendado) ou Windows 10/11  
- **Dependências:** via `pip` (veja `requirements.txt`)  

---

## ⚙️ Instalação

```bash
git clone -b PY-IDE https://github.com/CodexMelo/Py-Dragon-IDE.git
cd Py-Dragon-IDE

python -m venv venv
source venv/bin/activate   # Linux
# Windows: venv\Scripts\activate

pip install -r requirements.txt
python main.py


---

## 📝 Uso

* Crie projetos Python ou web
* **Ctrl + S:** salvar | **F5:** executar Python
* Visualizador integrado para HTML/CSS/JS
* Futuro: Designer de Forms via menu "Ferramentas"

### Exemplo Python

```python
print("Olá, mundo do Py-Dragon-IDE!")
```

### Exemplo Designer de Forms (conceitual)

```python
import tkinter as tk

root = tk.Tk()
root.title("Meu App - Gerado pelo Py-Dragon-IDE")

label = tk.Label(root, text="Olá, Windows Forms-like!")
label.pack()

button = tk.Button(root, text="Clique Aqui", command=lambda: print("Botão clicado!"))
button.pack()

root.mainloop()
```

---

## 💻 Linguagens Suportadas

| Linguagem  | Suporte Atual | Status Futuro |
| ---------- | ------------- | ------------- |
| Python     | ✅ Completo    | -             |
| HTML/CSS   | ✅ Básico      | Avançado      |
| JavaScript | ✅ Básico      | Avançado      |
| Java       | ❌ Não         | Planejado     |
| CLIPS      | ❌ Não         | Planejado     |
| C          | ❌ Não         | Planejado     |
| C++        | ❌ Não         | Planejado     |
| C#         | ❌ Não         | Planejado     |

---

## 🧭 Roadmap Visual

| Versão | Status          | Principais Funcionalidades                                                 |
| ------ | --------------- | -------------------------------------------------------------------------- |
| 0.1    | 🔄 Em Progresso | Suporte básico a Python e web                                              |
| 0.2    | ⏳ Planejado     | Integração de debugger e suporte a Java                                    |
| 0.3    | ⏳ Planejado     | Suporte a C/C++, compilação via GCC/Clang, início Designer de Forms        |
| 0.4    | ⏳ Planejado     | Suporte a C# e expansão Designer de Forms (PyQt)                           |
| 1.0    | ⭐ Futuro        | Competição com VS Code, suporte completo a CLIPS, Designer de Forms maduro |

---

## 🎨 Screenshots / GIFs

<p align="center">
  <img src="docs/screenshot_editor.png" width="600" alt="Editor Python">
</p>

<p align="center">
  <img src="docs/screenshot_autocomplete.gif" width="600" alt="Autocompletar em ação">
</p>

<p align="center">
  <img src="docs/screenshot_designer.png" width="600" alt="Designer de Forms (conceitual)">
</p>

> Substitua os arquivos `docs/*.png/gif` com imagens reais do projeto.

---

## 🤝 Contribuições

1. Fork o repositório
2. Crie uma branch para sua feature

```bash
git checkout -b feature/nova-funcionalidade
```

3. Commit suas alterações

```bash
git commit -m "Adiciona nova funcionalidade"
```

4. Push para a branch

```bash
git push origin feature/nova-funcionalidade
```

5. Abra um Pull Request

> Contribuições para Designer de Forms ou suporte a C/C++/C# são altamente incentivadas.

---

## 📜 Licença

MIT License. Consulte `LICENSE`.

---

## 📬 Contato

* **Autor:** CodexMelo
* **Issues:** [Abra uma issue](https://github.com/CodexMelo/Py-Dragon-IDE/issues)
* **Discussões:** Participe das discussões no repositório

<p align="center">
🐉 <b>Py-Dragon-IDE</b> — feito com dedicação, propósito e Python.
</p>
```

---

