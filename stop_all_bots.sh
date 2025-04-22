#!/bin/bash

# 停止所有可能正在运行的bot进程

echo "正在查找和停止所有bot进程..."

# 终止所有与bot.py相关的进程
pkill -9 -f "python.*bot.py" || true
pkill -9 -f "python.*simple_bot.py" || true

# 等待进程终止
echo "等待10秒确保所有进程已终止..."
sleep 10

# 检查是否还有bot进程在运行
RUNNING_BOTS=$(ps aux | grep -E "python.*bot.py" | grep -v grep | wc -l)

if [ "$RUNNING_BOTS" -gt 0 ]; then
    echo "警告: 仍有 $RUNNING_BOTS 个bot进程在运行, 尝试强制终止..."
    
    # 查找进程ID并终止
    ps aux | grep -E "python.*bot.py" | grep -v grep | awk '{print $2}' | xargs -I{} kill -9 {} 2>/dev/null || true
    
    # 再次等待
    echo "再次等待5秒..."
    sleep 5
    
    # 最终检查
    FINAL_CHECK=$(ps aux | grep -E "python.*bot.py" | grep -v grep | wc -l)
    if [ "$FINAL_CHECK" -gt 0 ]; then
        echo "警告: 仍有 $FINAL_CHECK 个bot进程无法终止!"
    else
        echo "所有bot进程已成功终止"
    fi
else
    echo "所有bot进程已成功终止"
fi

# 重置Telegram的webhook
echo "正在重置Telegram API webhook..."

# 获取BOT_TOKEN (需要从.env文件或环境变量获取)
if [ -f .env ]; then
    source .env
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "错误: 未找到TELEGRAM_BOT_TOKEN环境变量"
    exit 1
fi

# 删除webhook并清除所有待处理更新
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook?drop_pending_updates=true"

echo "等待30秒让Telegram API完全释放连接..."
sleep 30

echo "所有清理步骤已完成" 