#!/bin/bash

# =============================================
# Py Dragon Studio IDE - Desinstalador Linux
# =============================================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Diretórios
INSTALL_DIR="$HOME/.local/share/pydragon-studio"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons"
CONFIG_DIR="$HOME/.config/pydragon-studio"
CACHE_DIR="$HOME/.cache/pydragon-studio"

log_info() {
    echo -e "${YELLOW}ℹ️ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_warning() {
    echo -e "${RED}"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║                ATENÇÃO!                       ║"
    echo "║       DESINSTALAÇÃO DO PY DRAGON STUDIO       ║"
    echo "║                                               ║"
    echo "║  Todos os dados e configurações serão         ║"
    echo "║  removidos permanentemente!                   ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

confirm_uninstall() {
    read -p "Tem certeza que deseja desinstalar? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Desinstalação cancelada."
        exit 0
    fi
}

remove_files() {
    log_info "Removendo arquivos..."
    
    # Remover executável
    if [ -f "$BIN_DIR/pydragon-studio" ]; then
        rm -f "$BIN_DIR/pydragon-studio"
        log_success "Executável removido"
    fi
    
    # Remover entrada do menu
    if [ -f "$DESKTOP_DIR/pydragon-studio.desktop" ]; then
        rm -f "$DESKTOP_DIR/pydragon-studio.desktop"
        log_success "Entrada do menu removida"
    fi
    
    # Remover ícone
    if [ -f "$ICONS_DIR/pydragon-studio.png" ]; then
        rm -f "$ICONS_DIR/pydragon-studio.png"
        log_success "Ícone removido"
    fi
    
    # Remover diretório de instalação
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        log_success "Diretório de instalação removido"
    fi
    
    # Atualizar banco de dados desktop
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_DIR"
    fi
}

remove_config() {
    log_info "Removendo configurações..."
    
    read -p "Deseja remover configurações e dados do usuário? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        if [ -d "$CONFIG_DIR" ]; then
            rm -rf "$CONFIG_DIR"
            log_success "Configurações removidas"
        fi
        
        if [ -d "$CACHE_DIR" ]; then
            rm -rf "$CACHE_DIR"
            log_success "Cache removido"
        fi
    else
        log_info "Configurações mantidas em:"
        echo "  $CONFIG_DIR"
        echo "  $CACHE_DIR"
    fi
}

main() {
    show_warning
    confirm_uninstall
    
    remove_files
    remove_config
    
    echo
    log_success "Py Dragon Studio IDE foi desinstalado com sucesso!"
    echo
}

main "$@"
