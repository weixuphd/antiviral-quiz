#!/bin/bash
# 课堂快速启动脚本 — 抗病毒药题库
# Usage: bash start.sh

PORT=${PORT:-8080}

cd "$(dirname "$0")"

echo "=========================================="
echo "  药理学第四十四章 · 抗病毒药题库"
echo "=========================================="

# Check dependencies
python3 -c "import flask" 2>/dev/null || {
    echo "正在安装依赖..."
    pip3 install Flask Flask-Limiter
}

# Get local IP
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "localhost")

echo ""
echo "  服务器启动: http://${LOCAL_IP}:${PORT}"
echo "  学生访问地址: http://${LOCAL_IP}:${PORT}"
echo ""
echo "  按 Ctrl+C 停止服务器"
echo "=========================================="
echo ""

python3 app.py
