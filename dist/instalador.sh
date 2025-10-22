#!/bin/bash

# =============================================
# Py Dragon Studio IDE - Instalador Linux
# Para versão empacotada
# =============================================

set -e  # Sai em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
INSTALL_DIR="$HOME/.local/share/pydragon-studio"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons"
VERSION="1.0.0"

# Funções de log
log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Banner
show_banner() {
    echo -e "${BLUE}"
    cat << "BANNER"
╔═══════════════════════════════════════════════╗
║           PY DRAGON STUDIO IDE                ║
║            Instalador Linux                   ║
║                                               ║
║  🐍 Uma IDE Python moderna e poderosa        ║
║  🚀 Foco em produtividade e experiência       ║
╚═══════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
}

# Verificar dependências do sistema
check_system_deps() {
    log_info "Verificando dependências do sistema..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 não encontrado!"
        log_info "Instale Python 3.8+ com:"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  Fedora: sudo dnf install python3 python3-pip"
        echo "  Arch: sudo pacman -S python python-pip"
        exit 1
    fi
    
    # Verificar versão do Python
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_success "Python $PYTHON_VERSION detectado"
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        log_warning "pip3 não encontrado, tentando instalar..."
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y python3-pip
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-pip
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm python-pip
        else
            log_error "Não foi possível instalar pip automaticamente"
            exit 1
        fi
    fi
    
    log_success "Dependências do sistema verificadas"
}

# Criar diretórios
create_directories() {
    log_info "Criando diretórios..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICONS_DIR"
    mkdir -p "$INSTALL_DIR/plugins"
    mkdir -p "$INSTALL_DIR/themes"
    mkdir -p "$INSTALL_DIR/config"
    
    log_success "Diretórios criados"
}

# Instalar dependências Python
install_python_deps() {
    log_info "Instalando dependências Python..."
    
    # Criar venv para isolamento
    python3 -m venv "$INSTALL_DIR/venv"
    
    # Ativar venv e instalar dependências
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Atualizar pip
    pip install --upgrade pip
    
    # Instalar dependências
    if [ -f "requirements-linux.txt" ]; then
        pip install -r requirements-linux.txt
    else
        log_warning "requirements-linux.txt não encontrado, instalando dependências básicas..."
        pip install PySide6==6.6.1 pygments==2.17.2 jedi==0.19.1 psutil==5.9.6 watchdog==3.0.0
    fi
    
    log_success "Dependências Python instaladas"
}

# Copiar arquivos da IDE
copy_ide_files() {
    log_info "Copiando arquivos da IDE..."
    
    # Copiar arquivos principais
    if [ -f "ide.py" ]; then
        cp ide.py "$INSTALL_DIR/"
    else
        log_error "Arquivo principal ide.py não encontrado!"
        exit 1
    fi
    
    # Copiar diretórios
    for dir in core ui syntax tools plugins analysis editor cache debug; do
        if [ -d "$dir" ]; then
            cp -r "$dir" "$INSTALL_DIR/"
        fi
    done
    
    # Copiar ícone se existir
    if [ -f "icons/ide.png" ]; then
        cp icons/ide.png "$ICONS_DIR/pydragon-studio.png"
    fi
    
    log_success "Arquivos da IDE copiados"
}

# Criar executável
create_executable() {
    log_info "Criando executável..."
    
    cat > "$BIN_DIR/pydragon-studio" << 'EOF'
#!/bin/bash
# Py Dragon Studio IDE - Launcher

INSTALL_DIR="$HOME/.local/share/pydragon-studio"

# Verificar se o diretório existe
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Erro: Py Dragon Studio não está instalado!"
    echo "Execute o instalador novamente."
    exit 1
fi

# Ativar ambiente virtual e executar
cd "$INSTALL_DIR"
source "$INSTALL_DIR/venv/bin/activate"
python3 ide.py "$@"
EOF
    
    chmod +x "$BIN_DIR/pydragon-studio"
    log_success "Executável criado: $BIN_DIR/pydragon-studio"
}

# Criar arquivo .desktop
create_desktop_file() {
    log_info "Criando entrada no menu de aplicações..."
    
    cat > "$DESKTOP_DIR/pydragon-studio.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Py Dragon Studio IDE
Comment=Modern Python IDE for productive development
Exec=$BIN_DIR/pydragon-studio
Icon=$ICONS_DIR/pydragon-studio.png
Terminal=false
Categories=Development;IDE;
Keywords=python;ide;development;code;editor;
StartupWMClass=PyDragonStudio
MimeType=text/x-python;
EOF
    
    # Atualizar banco de dados de desktop
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_DIR"
    fi
    
    log_success "Entrada de menu criada"
}

# Configurar permissões
setup_permissions() {
    log_info "Configurando permissões..."
    
    chmod -R 755 "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/ide.py"
    
    log_success "Permissões configuradas"
}

# Instalar pacotes do sistema (opcional)
install_system_packages() {
    log_info "Verificando pacotes do sistema recomendados..."
    
    local missing_packages=()
    
    # Verificar pacotes recomendados
    if ! command -v git &> /dev/null; then
        missing_packages+=("git")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_packages+=("curl")
    fi
    
    if [ ${#missing_packages[@]} -ne 0 ]; then
        log_warning "Pacotes recomendados não encontrados: ${missing_packages[*]}"
        read -p "Deseja instalar? (s/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            if command -v apt &> /dev/null; then
                sudo apt update && sudo apt install -y "${missing_packages[@]}"
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y "${missing_packages[@]}"
            elif command -v pacman &> /dev/null; then
                sudo pacman -S --noconfirm "${missing_packages[@]}"
            else
                log_warning "Gerenciador de pacotes não suportado, instale manualmente: ${missing_packages[*]}"
            fi
        fi
    fi
    
    log_success "Pacotes do sistema verificados"
}

# Verificar instalação
verify_installation() {
    log_info "Verificando instalação..."
    
    local errors=0
    
    # Verificar se executável existe
    if [ ! -f "$BIN_DIR/pydragon-studio" ]; then
        log_error "Executável não criado"
        errors=$((errors + 1))
    fi
    
    # Verificar se arquivo desktop existe
    if [ ! -f "$DESKTOP_DIR/pydragon-studio.desktop" ]; then
        log_error "Arquivo .desktop não criado"
        errors=$((errors + 1))
    fi
    
    # Verificar se diretório de instalação existe
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "Diretório de instalação não existe"
        errors=$((errors + 1))
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "Instalação verificada com sucesso"
        return 0
    else
        log_error "Instalação com $errors erro(s)"
        return 1
    fi
}

# Mostrar resumo pós-instalação
show_summary() {
    echo
    echo -e "${GREEN}=============================================${NC}"
    echo -e "${GREEN}🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
    echo -e "${GREEN}=============================================${NC}"
    echo
    echo -e "${BLUE}📁 Diretório de instalação:${NC}"
    echo "  $INSTALL_DIR"
    echo
    echo -e "${BLUE}🚀 Como executar:${NC}"
    echo "  • Menu de aplicações: Procure por 'Py Dragon Studio'"
    echo "  • Terminal: pydragon-studio"
    echo "  • Direto: $BIN_DIR/pydragon-studio"
    echo
    echo -e "${BLUE}🔧 Diretório de configuração:${NC}"
    echo "  $HOME/.config/pydragon-studio/"
    echo
    echo -e "${BLUE}📝 Logs:${NC}"
    echo "  $HOME/.cache/pydragon-studio/logs/"
    echo
    echo -e "${YELLOW}💡 Dica: Reinicie sua sessão para ver o ícone no menu${NC}"
    echo
}

# Função principal
main() {
    show_banner
    
    log_info "Iniciando instalação do Py Dragon Studio IDE..."
    
    # Verificar se não é root
    if [ "$EUID" -eq 0 ]; then
        log_error "Não execute como root! O instalador configurará permissões de usuário."
        exit 1
    fi
    
    # Executar etapas de instalação
    check_system_deps
    create_directories
    install_python_deps
    copy_ide_files
    create_executable
    create_desktop_file
    setup_permissions
    install_system_packages
    
    # Verificar instalação
    if verify_installation; then
        show_summary
    else
        log_error "Houve problemas na instalação. Verifique os logs acima."
        exit 1
    fi
}

# Executar instalação
main "$@"
