#!/bin/bash

# 交易信号机器人启动脚本
# 作用：安全地启动 bot，确保清理所有冲突连接

echo "=== 交易信号机器人启动脚本 ==="
echo "$(date) - 开始执行启动流程"

# 1. 停止所有 Python 进程
echo "正在停止所有 Python 进程..."
pkill -9 -f python
sleep 5
echo "等待进程完全终止..."
sleep 3

# 2. 激活虚拟环境
echo "正在激活虚拟环境..."
source .venv/bin/activate

# 3. 清理 Telegram webhook
echo "正在清理 Telegram webhook..."
TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d '=' -f2)
echo "正在删除 webhook..."
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook?drop_pending_updates=true"
echo -e "\nwebhook 已删除，等待 Telegram API 完全处理..."
sleep 10

# 4. 启动机器人
echo "正在启动机器人..."
nohup python bot.py > bot_output.log 2>&1 &
BOT_PID=$!
echo "机器人已在后台启动，PID: $BOT_PID"

# 5. 检查机器人是否成功启动
sleep 5
if ps -p $BOT_PID > /dev/null; then
    echo "$(date) - 机器人启动成功！"
    echo "进程 ID: $BOT_PID"
    echo "日志文件位置: $(pwd)/bot_output.log"
    echo "使用以下命令查看日志:"
    echo "tail -f bot_output.log"
else
    echo "$(date) - 机器人启动失败，请检查日志文件获取详细信息"
fi

echo "=== 启动脚本执行完毕 ===" 