#!/bin/bash

# 项目磁盘空间占用统计脚本
# 统计项目中各目录和文件类型的磁盘占用

echo "💾 项目磁盘空间占用统计"
echo "================================================"

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "项目路径: $PROJECT_ROOT"
echo ""

# 排除的目录
EXCLUDE_DIRS=(
    ".git"
    "venv"
    ".venv"
    "env"
    "*-env"
    "pdfkit-env"
    "node_modules"
    "__pycache__"
    ".pytest_cache"
    ".mypy_cache"
    ".ruff_cache"
    ".tox"
    ".claude"
    "build"
    "dist"
    "*.egg-info"
)

# 排除的文件类型
EXCLUDE_FILES=(
    "*.pyc"
    "*.pyo"
    "*.log"
    "*.tmp"
    ".DS_Store"
)

echo "排除的目录: ${EXCLUDE_DIRS[*]}"
echo "排除的文件: ${EXCLUDE_FILES[*]}"
echo ""
echo "================================================"

# 总体统计（不排除任何内容）
echo ""
echo "📊 整体磁盘占用 (含所有文件):"
echo "----------------------------------------"
total_size=$(du -sh . 2>/dev/null | cut -f1)
echo "项目总大小: $total_size"
echo "----------------------------------------"

# Git 仓库大小
if [ -d ".git" ]; then
    git_size=$(du -sh .git 2>/dev/null | cut -f1)
    echo "Git 仓库:   $git_size"
fi

# 虚拟环境大小
for env_dir in venv .venv env pdfkit-env "*-env"; do
    if [ -d "$env_dir" ]; then
        env_size=$(du -sh "$env_dir" 2>/dev/null | cut -f1)
        echo "$env_dir: $env_size"
    fi
done

echo "----------------------------------------"

# 核心代码统计（排除虚拟环境和 git）
echo ""
echo "📁 核心代码目录占用:"
echo "------------------------------------------------------------"
printf "%-30s  %10s  %s\n" "目录" "大小" "文件数"
echo "------------------------------------------------------------"

# 统计各个子目录
for dir in pdfkit tests scripts docs; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        count=$(find "$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
        printf "%-30s  %10s  %s\n" "$dir/" "$size" "$count"
    fi
done

echo "------------------------------------------------------------"

# 按文件类型统计
echo ""
echo "📄 按文件类型统计:"
echo "------------------------------------------------------------"
printf "%-20s  %10s  %s\n" "文件类型" "总大小" "文件数"
echo "------------------------------------------------------------"

# Python 文件
py_files=$(find . -name "*.py" -not -path "*/.*" -not -path "*/venv/*" -not -path "*/.venv/*" -not -path "*/env/*" -not -path "*/pdfkit-env/*" -not -path "*/__pycache__/*" 2>/dev/null)
if [ -n "$py_files" ]; then
    py_size=$(echo "$py_files" | xargs du -ch 2>/dev/null | tail -1 | cut -f1)
    py_count=$(echo "$py_files" | wc -l | tr -d ' ')
    printf "%-20s  %10s  %s\n" ".py 文件" "$py_size" "$py_count"
fi

# Shell 脚本
sh_files=$(find . -name "*.sh" -not -path "*/.*" -not -path "*/venv/*" 2>/dev/null)
if [ -n "$sh_files" ]; then
    sh_size=$(echo "$sh_files" | xargs du -ch 2>/dev/null | tail -1 | cut -f1)
    sh_count=$(echo "$sh_files" | wc -l | tr -d ' ')
    printf "%-20s  %10s  %s\n" ".sh 文件" "$sh_size" "$sh_count"
fi

# Markdown 文件
md_files=$(find . -name "*.md" -not -path "*/.*" -not -path "*/venv/*" 2>/dev/null)
if [ -n "$md_files" ]; then
    md_size=$(echo "$md_files" | xargs du -ch 2>/dev/null | tail -1 | cut -f1)
    md_count=$(echo "$md_files" | wc -l | tr -d ' ')
    printf "%-20s  %10s  %s\n" ".md 文件" "$md_size" "$md_count"
fi

# JSON 文件
json_files=$(find . -name "*.json" -not -path "*/.*" -not -path "*/venv/*" -not -path "*/node_modules/*" 2>/dev/null)
if [ -n "$json_files" ]; then
    json_size=$(echo "$json_files" | xargs du -ch 2>/dev/null | tail -1 | cut -f1)
    json_count=$(echo "$json_files" | wc -l | tr -d ' ')
    printf "%-20s  %10s  %s\n" ".json 文件" "$json_size" "$json_count"
fi

# YAML 文件
yaml_files=$(find . -name "*.yaml" -o -name "*.yml" -not -path "*/.*" -not -path "*/venv/*" 2>/dev/null)
if [ -n "$yaml_files" ]; then
    yaml_size=$(echo "$yaml_files" | xargs du -ch 2>/dev/null | tail -1 | cut -f1)
    yaml_count=$(echo "$yaml_files" | wc -l | tr -d ' ')
    printf "%-20s  %10s  %s\n" ".yaml/.yml" "$yaml_size" "$yaml_count"
fi

echo "------------------------------------------------------------"

# 最大的文件
echo ""
echo "🔍 项目中最大的文件 (Top 10):"
echo "------------------------------------------------------------"
echo "大小        文件"
echo "------------------------------------------------------------"
find . -type f -not -path "*/.git/*" -not -path "*/venv/*" -not -path "*/.venv/*" -not -path "*/env/*" -not -path "*/pdfkit-env/*" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -exec du -h {} + 2>/dev/null | sort -rh | head -10
echo "------------------------------------------------------------"

# 详细目录大小（如果需要更详细的信息）
echo ""
echo "📂 详细目录占用 (按大小排序):"
echo "------------------------------------------------------------"
du -h --max-depth=2 --exclude=".git" --exclude="venv" --exclude=".venv" --exclude="env" --exclude="pdfkit-env" --exclude="node_modules" --exclude="__pycache__" --exclude=".pytest_cache" --exclude=".mypy_cache" --exclude=".ruff_cache" --exclude=".tox" --exclude=".claude" --exclude="build" --exclude="dist" 2>/dev/null | sort -rh | head -20
echo "------------------------------------------------------------"

echo ""
echo "================================================"
