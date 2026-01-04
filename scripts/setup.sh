#!/bin/bash
# ============================================================================
# PDFKit 本地部署脚本 (macOS/Linux)
# ============================================================================
# 用法: 在项目目录中运行 ./scripts/setup.sh
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_NAME="pdfkit-env"
BIN_DIR="$HOME/.local/bin"

# ============================================================================
# 工具函数
# ============================================================================

info() { echo -e "${BLUE}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }
step() { echo -e "\n${CYAN}[$1/$TOTAL_STEPS]${NC} ${YELLOW}$2${NC}"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# ============================================================================
# 安装步骤
# ============================================================================

TOTAL_STEPS=4

check_python() {
    step 1 "检查 Python..."
    
    if ! command_exists python3; then
        error "未找到 Python3，请先安装 Python 3.10+"
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [[ "$PYTHON_MAJOR" -lt 3 ]] || [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 10 ]]; then
        error "Python 版本过低 ($PYTHON_VERSION)，需要 3.10+"
    fi
    
    success "Python $PYTHON_VERSION"
}

create_venv() {
    step 2 "创建虚拟环境..."
    
    cd "$PROJECT_DIR"
    
    if [[ -d "$VENV_NAME" ]]; then
        warning "虚拟环境已存在: $VENV_NAME"
    else
        python3 -m venv "$VENV_NAME"
        success "虚拟环境已创建: $VENV_NAME"
    fi
}

install_deps() {
    step 3 "安装依赖..."
    
    cd "$PROJECT_DIR"
    source "$VENV_NAME/bin/activate"
    
    info "升级 pip..."
    pip install --upgrade pip -q
    
    info "安装 PDFKit..."
    pip install -e . -q
    
    success "依赖安装完成"
}

configure_command() {
    step 4 "配置系统命令..."
    
    # 创建 bin 目录
    mkdir -p "$BIN_DIR"
    
    # 创建 wrapper 脚本
    WRAPPER_PATH="$BIN_DIR/pdfkit"
    cat > "$WRAPPER_PATH" << EOF
#!/bin/bash
source "$PROJECT_DIR/$VENV_NAME/bin/activate"
"$PROJECT_DIR/$VENV_NAME/bin/pdfkit" "\$@"
EOF
    chmod +x "$WRAPPER_PATH"
    
    # 检查 PATH
    SHELL_RC="$HOME/.zshrc"
    [[ "$SHELL" == *"bash"* ]] && SHELL_RC="$HOME/.bashrc"
    
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        if ! grep -q "\.local/bin" "$SHELL_RC" 2>/dev/null; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
            info "已添加 $BIN_DIR 到 PATH"
        fi
    fi
    
    success "命令已配置: $WRAPPER_PATH"
}

print_success() {
    echo -e "\n${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}              ✓ PDFKit 部署成功！${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}项目目录:${NC} $PROJECT_DIR"
    echo -e "  ${CYAN}虚拟环境:${NC} $PROJECT_DIR/$VENV_NAME"
    echo ""
    echo -e "  ${YELLOW}激活虚拟环境:${NC}"
    echo -e "    ${GREEN}source $PROJECT_DIR/$VENV_NAME/bin/activate${NC}"
    echo ""
    echo -e "  ${YELLOW}使用命令:${NC}"
    echo -e "    ${GREEN}pdfkit --help${NC}"
    echo -e "    ${GREEN}pdfkit info system${NC}"
    echo ""
    echo -e "  ${YELLOW}刷新 PATH (如需要):${NC}"
    echo -e "    ${GREEN}source $SHELL_RC${NC}"
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
}

# ============================================================================
# 主程序
# ============================================================================

main() {
    echo -e "${CYAN}PDFKit 本地部署脚本${NC}"
    echo -e "项目目录: ${YELLOW}$PROJECT_DIR${NC}"
    echo ""
    
    check_python
    create_venv
    install_deps
    configure_command
    print_success
}

main "$@"
