#!/bin/bash
# ============================================================================
# PDFKit 一键安装脚本 (macOS)
# ============================================================================
# 用法: curl -fsSL https://raw.githubusercontent.com/linzhiqin2003/pdfkit/main/scripts/install.sh | bash
# 或者: bash install.sh
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
REPO_URL="https://github.com/linzhiqin2003/pdfkit.git"
INSTALL_DIR="$HOME/.pdfkit-cli"
VENV_NAME="venv"

# ============================================================================
# 工具函数
# ============================================================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║   ██████╗ ██████╗ ███████╗██╗  ██╗██╗████████╗               ║"
    echo "║   ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║╚══██╔══╝               ║"
    echo "║   ██████╔╝██║  ██║█████╗  █████╔╝ ██║   ██║                  ║"
    echo "║   ██╔═══╝ ██║  ██║██╔══╝  ██╔═██╗ ██║   ██║                  ║"
    echo "║   ██║     ██████╔╝██║     ██║  ██╗██║   ██║                  ║"
    echo "║   ╚═╝     ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝                  ║"
    echo "║                                                               ║"
    echo "║              一键安装脚本 v1.0.0                              ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

step() {
    echo -e "\n${CYAN}[$1/$TOTAL_STEPS]${NC} ${YELLOW}$2${NC}"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# 安装步骤
# ============================================================================

TOTAL_STEPS=6

install_homebrew() {
    step 1 "检查 Homebrew..."
    
    if command_exists brew; then
        success "Homebrew 已安装: $(brew --version | head -n1)"
    else
        info "正在安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加到 PATH (Apple Silicon)
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        success "Homebrew 安装完成"
    fi
}

install_git() {
    step 2 "检查 Git..."
    
    if command_exists git; then
        success "Git 已安装: $(git --version)"
    else
        info "正在安装 Git..."
        brew install git
        success "Git 安装完成"
    fi
}

install_python() {
    step 3 "检查 Python..."
    
    # 检查 Python 3.10+
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        
        if [[ "$PYTHON_MAJOR" -ge 3 ]] && [[ "$PYTHON_MINOR" -ge 10 ]]; then
            success "Python 已安装: Python $PYTHON_VERSION"
        else
            warning "Python 版本过低 ($PYTHON_VERSION)，需要 3.10+"
            info "正在安装 Python 3.12..."
            brew install python@3.12
            success "Python 3.12 安装完成"
        fi
    else
        info "正在安装 Python 3.12..."
        brew install python@3.12
        success "Python 3.12 安装完成"
    fi
}

clone_repository() {
    step 4 "克隆代码仓库..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        warning "安装目录已存在: $INSTALL_DIR"
        info "正在更新代码..."
        cd "$INSTALL_DIR"
        git pull origin main || git pull origin master
        success "代码更新完成"
    else
        info "正在克隆仓库..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        success "代码克隆完成: $INSTALL_DIR"
    fi
}

install_dependencies() {
    step 5 "安装 Python 依赖..."
    
    cd "$INSTALL_DIR"
    
    # 创建虚拟环境
    if [[ ! -d "$VENV_NAME" ]]; then
        info "创建虚拟环境..."
        python3 -m venv "$VENV_NAME"
    fi
    
    # 激活虚拟环境
    source "$VENV_NAME/bin/activate"
    
    # 升级 pip
    info "升级 pip..."
    pip install --upgrade pip -q
    
    # 安装项目
    info "安装 PDFKit..."
    pip install -e . -q
    
    # 安装 Playwright 浏览器 (可选，用于网页转PDF)
    if command_exists playwright; then
        info "安装 Playwright 浏览器..."
        playwright install chromium -q 2>/dev/null || true
    fi
    
    success "依赖安装完成"
}

configure_shell() {
    step 6 "配置系统命令..."
    
    SHELL_RC=""
    SHELL_NAME=""
    
    # 检测 shell 类型
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
        SHELL_NAME="zsh"
    elif [[ "$SHELL" == *"bash"* ]]; then
        SHELL_RC="$HOME/.bashrc"
        SHELL_NAME="bash"
        # macOS 默认使用 .bash_profile
        if [[ "$(uname)" == "Darwin" ]] && [[ -f "$HOME/.bash_profile" ]]; then
            SHELL_RC="$HOME/.bash_profile"
        fi
    else
        SHELL_RC="$HOME/.profile"
        SHELL_NAME="sh"
    fi
    
    # 添加激活函数到 shell 配置
    ACTIVATE_SCRIPT="
# PDFKit CLI
pdfkit() {
    source \"$INSTALL_DIR/$VENV_NAME/bin/activate\"
    \"$INSTALL_DIR/$VENV_NAME/bin/pdfkit\" \"\$@\"
}
"
    
    # 检查是否已添加
    if grep -q "# PDFKit CLI" "$SHELL_RC" 2>/dev/null; then
        warning "Shell 配置已存在，跳过..."
    else
        info "添加到 $SHELL_RC..."
        echo "$ACTIVATE_SCRIPT" >> "$SHELL_RC"
        success "Shell 配置完成"
    fi
    
    # 确定 wrapper 脚本位置
    # 优先使用 ~/.local/bin (用户本地目录，不需要 sudo)
    BIN_DIR="$HOME/.local/bin"
    
    # 创建目录（如果不存在）
    if [[ ! -d "$BIN_DIR" ]]; then
        info "创建目录 $BIN_DIR..."
        mkdir -p "$BIN_DIR"
    fi
    
    WRAPPER_PATH="$BIN_DIR/pdfkit"
    
    # 创建 wrapper 脚本
    cat > "$WRAPPER_PATH" << EOF
#!/bin/bash
source "$INSTALL_DIR/$VENV_NAME/bin/activate"
"$INSTALL_DIR/$VENV_NAME/bin/pdfkit" "\$@"
EOF
    chmod +x "$WRAPPER_PATH"
    
    # 检查 ~/.local/bin 是否在 PATH 中
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        # 添加到 shell 配置
        PATH_EXPORT="
# Add ~/.local/bin to PATH
export PATH=\"\$HOME/.local/bin:\$PATH\"
"
        if ! grep -q "\.local/bin" "$SHELL_RC" 2>/dev/null; then
            info "添加 $BIN_DIR 到 PATH..."
            echo "$PATH_EXPORT" >> "$SHELL_RC"
        fi
    fi
    
    success "系统命令已配置: $WRAPPER_PATH"
}

# ============================================================================
# 安装后提示
# ============================================================================

print_success() {
    echo -e "\n${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}              ✓ PDFKit 安装成功！${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}安装位置:${NC} $INSTALL_DIR"
    echo -e "  ${CYAN}虚拟环境:${NC} $INSTALL_DIR/$VENV_NAME"
    echo ""
    echo -e "  ${YELLOW}开始使用:${NC}"
    echo -e "    ${GREEN}pdfkit --help${NC}          # 查看帮助"
    echo -e "    ${GREEN}pdfkit info system${NC}     # 检查系统状态"
    echo -e "    ${GREEN}pdfkit info doc.pdf${NC}    # 查看 PDF 信息"
    echo ""
    echo -e "  ${YELLOW}常用命令:${NC}"
    echo -e "    ${GREEN}pdfkit merge a.pdf b.pdf -o combined.pdf${NC}"
    echo -e "    ${GREEN}pdfkit split doc.pdf --single${NC}"
    echo -e "    ${GREEN}pdfkit compress large.pdf -o small.pdf${NC}"
    echo -e "    ${GREEN}pdfkit ocr scan.pdf${NC}"
    echo ""
    echo -e "  ${YELLOW}配置 API Key (OCR/AI 功能):${NC}"
    echo -e "    ${GREEN}export DASHSCOPE_API_KEY=\"your-api-key\"${NC}"
    echo ""
    echo -e "  ${CYAN}重新加载 shell 配置:${NC}"
    echo -e "    ${GREEN}source $SHELL_RC${NC}"
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
}

# ============================================================================
# 主程序
# ============================================================================

main() {
    print_banner
    
    echo -e "${YELLOW}即将安装 PDFKit CLI 到: $INSTALL_DIR${NC}"
    echo ""
    
    # 确认安装
    read -p "是否继续安装? [Y/n] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "安装已取消"
        exit 0
    fi
    
    echo ""
    
    install_homebrew
    install_git
    install_python
    clone_repository
    install_dependencies
    configure_shell
    
    print_success
}

# 运行主程序
main "$@"
