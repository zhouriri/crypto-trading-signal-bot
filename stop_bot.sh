#!/bin/bash

# 交易信号机器人停止脚本
# 作用：安全地停止所有 bot 进程

echo "=== 交易信号机器人停止脚本 ==="
echo "$(date) - 开始执行停止流程"

# 1. 使用 pkill 停止 Python 进程
echo "正在停止 Python 进程..."
pkill -9 -f "python.*bot.py"
pkill -9 -f "python.*simple_bot.py"
echo "等待进程终止..."
sleep 3

# 2. 使用 pgrep + kill 终止进程
echo "使用 kill 确保进程终止..."
pgrep -f "python.*bot.py|python.*simple_bot.py" | xargs -I{} kill -9 {} 2>/dev/null || true
sleep 3

# 3. 检查是否仍有进程在运行
echo "验证进程是否已终止..."
REMAINING=$(ps aux | grep 'python.*bot.py\|python.*simple_bot.py' | grep -v grep)
if [ -z "$REMAINING" ]; then
    echo "所有 bot 进程已成功终止"
else
    echo "警告：以下进程仍在运行："
    echo "$REMAINING"
    echo "对剩余进程使用直接 kill..."
    ps aux | grep 'python.*bot.py\|python.*simple_bot.py' | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
    
    # 最后验证
    REMAINING=$(ps aux | grep 'python.*bot.py\|python.*simple_bot.py' | grep -v grep)
    if [ -z "$REMAINING" ]; then
        echo "所有 bot 进程现已成功终止"
    else
        echo "警告：无法终止以下进程，需要手动处理："
        echo "$REMAINING"
        echo "请使用以下命令手动终止："
        echo "sudo kill -9 $(ps aux | grep 'python.*bot.py\|python.*simple_bot.py' | grep -v grep | awk '{print $2}')"
    fi
fi

# 4. 清理 Telegram webhook
echo "正在清理 Telegram webhook..."
TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d '=' -f2)
echo "正在删除 webhook..."
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook?drop_pending_updates=true"
echo -e "\nwebhook 已删除"

echo "=== 停止脚本执行完毕 ===" 