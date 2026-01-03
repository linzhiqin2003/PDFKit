#!/bin/bash

# 代码行数统计脚本
# 统计代码库中编程语言文件的代码行数（不包括 markdown、json 等文档文件）

echo "📊 代码库行数统计"
echo "================================================"

# 定义要统计的代码文件扩展名
CODE_EXTS=(
    py        # Python
    sh        # Shell
    bash      # Bash
    js        # JavaScript
    ts        # TypeScript
    jsx       # React JSX
    tsx       # React TSX
    css       # CSS
    scss      # Sass
    sass      # Sass
    html      # HTML
    htm       # HTML
    c         # C
    cpp       # C++
    cc        # C++
    h         # C/C++ Header
    hpp       # C++ Header
    java      # Java
    go        # Go
    rs        # Rust
    php       # PHP
    rb        # Ruby
    swift     # Swift
    kt        # Kotlin
    scala     # Scala
)

# 排除的目录（使用 -prune 语法）
EXCLUDE_DIRS=(
    venv
    ".venv"
    env
    "pdfkit-env"
    "*env*"
    node_modules
    __pycache__
    ".pytest_cache"
    ".mypy_cache"
    ".ruff_cache"
    ".git"
    build
    dist
    ".tox"
    ".claude"
)

# 构建排除条件
exclude_condition=""
for dir in "${EXCLUDE_DIRS[@]}"; do
    if [ -n "$exclude_condition" ]; then
        exclude_condition="$exclude_condition -o"
    fi
    exclude_condition="$exclude_condition -name '$dir' -prune"
done

# 构建文件查找条件
file_condition=""
for ext in "${CODE_EXTS[@]}"; do
    if [ -n "$file_condition" ]; then
        file_condition="$file_condition -o"
    fi
    file_condition="$file_condition -name '*.$ext'"
done

# 执行查找和统计
if [ -n "$exclude_condition" ]; then
    find_cmd="find . \( $exclude_condition \) -o -type f \( $file_condition \) -print"
else
    find_cmd="find . -type f \( $file_condition \)"
fi

files=$(eval "$find_cmd" 2>/dev/null || true)

if [ -z "$files" ]; then
    echo "❌ 未找到代码文件"
    exit 0
fi

# 统计总行数和文件数
total_lines=$(echo "$files" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
total_files=$(echo "$files" | wc -l | tr -d ' ')

echo "统计的文件类型: ${CODE_EXTS[*]}"
echo "排除的目录: ${EXCLUDE_DIRS[*]}"
echo ""
echo "📈 统计结果:"
echo "  文件总数: $total_files"
echo "  代码总行数: $total_lines"
echo "================================================"
echo ""

# 按扩展名分类统计
echo "📋 按语言分类:"
echo "----------------------------------------"
echo "语言           文件数    行数"
echo "----------------------------------------"

for ext in "${CODE_EXTS[@]}"; do
    if [ -n "$exclude_condition" ]; then
        ext_find_cmd="find . \( $exclude_condition \) -o -type f -name '*.$ext' -print"
    else
        ext_find_cmd="find . -type f -name '*.$ext'"
    fi
    ext_files=$(eval "$ext_find_cmd" 2>/dev/null || true)
    if [ -n "$ext_files" ]; then
        count=$(echo "$ext_files" | wc -l | tr -d ' ')
        lines=$(echo "$ext_files" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
        printf "%-14s  %-6s  %s\n" ".$ext" "$count" "$lines"
    fi
done

echo "----------------------------------------"
echo ""

# 按目录分类统计
echo "📁 按目录分类:"
echo "----------------------------------------"
echo "目录/文件                         行数"
echo "----------------------------------------"

# 获取所有包含代码文件的目录
dirs=$(echo "$files" | while read file; do
    dirname "$file"
done | sort -u)

for dir in $dirs; do
    dir_lines=$(echo "$files" | grep "^$dir/" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
    if [ -n "$dir_lines" ]; then
        # 计算相对路径长度，用于格式化输出
        rel_path="${dir#./}"
        if [ "$rel_path" = "." ]; then
            rel_path="(根目录)"
        fi
        printf "%-32s  %s\n" "$rel_path" "$dir_lines"
    fi
done

echo "----------------------------------------"
