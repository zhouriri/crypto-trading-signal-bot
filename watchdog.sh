#!/bin/bash

# 交易信号机器人守护进程脚本
# 用于监控和自动重启机器人
# 推荐添加到crontab：*/10 * * * * /path/to/watchdog.sh >> /path/to/watchdog.log 2>&1

# 设置变量
BOT_DIR="$HOME/trading_bot"
BOT_SCRIPT="bot.py"
LOG_FILE="$BOT_DIR/bot_output.log"
WATCHDOG_LOG="$BOT_DIR/watchdog.log"
MAX_RESTART=5
RESTART_INTERVAL=3600  # 一小时内最多重启次数

# 确保工作目录存在
if [ ! -d "$BOT_DIR" ]; then
    echo "$(date) [ERROR] 工作目录不存在: $BOT_DIR" | tee -a "$WATCHDOG_LOG"
    exit 1
fi

# 创建日志文件（如果不存在）
if [ ! -f "$WATCHDOG_LOG" ]; then
    touch "$WATCHDOG_LOG"
    echo "$(date) [INFO] 创建了守护进程日志文件" | tee -a "$WATCHDOG_LOG"
fi

# 记录启动信息
echo "$(date) [INFO] 守护进程开始检查" | tee -a "$WATCHDOG_LOG"

# 检查机器人进程
BOT_RUNNING=$(pgrep -f "python.*$BOT_SCRIPT" | wc -l)

if [ "$BOT_RUNNING" -gt 0 ]; then
    echo "$(date) [INFO] 机器人正在运行，进程数: $BOT_RUNNING" | tee -a "$WATCHDOG_LOG"
    exit 0
fi

# 如果到这里，说明机器人没有运行
echo "$(date) [WARNING] 机器人未运行，准备重启" | tee -a "$WATCHDOG_LOG"

# 检查最近一小时内的重启次数
RECENT_RESTARTS=$(grep -c "重启机器人" "$WATCHDOG_LOG" | awk -v interval="$(date -d "1 hour ago" "+%s")" '{if ($1 > interval) count++} END {print count}')

if [ "$RECENT_RESTARTS" -ge "$MAX_RESTART" ]; then
    echo "$(date) [ERROR] 最近一小时内重启次数过多(${RECENT_RESTARTS}次)，不再自动重启。请手动检查问题" | tee -a "$WATCHDOG_LOG"
    # 可以在这里添加发送Telegram消息的代码
    exit 1
fi

# 杀死残留进程
pkill -9 -f "python.*$BOT_SCRIPT" || true
echo "$(date) [INFO] 清理残留进程" | tee -a "$WATCHDOG_LOG"
sleep 2

# 进入工作目录
cd "$BOT_DIR" || {
    echo "$(date) [ERROR] 无法进入工作目录: $BOT_DIR" | tee -a "$WATCHDOG_LOG"
    exit 1
}

# 激活虚拟环境并重启机器人
if [ -d "$BOT_DIR/venv" ]; then
    echo "$(date) [INFO] 使用虚拟环境" | tee -a "$WATCHDOG_LOG"
    source "$BOT_DIR/venv/bin/activate"
    
    # 清理Telegram连接
    echo "$(date) [INFO] 运行Telegram API修复工具" | tee -a "$WATCHDOG_LOG"
    python "$BOT_DIR/telegram_fix.py" >> "$LOG_FILE" 2>&1
    sleep 5
    
    # 启动机器人
    echo "$(date) [INFO] 重启机器人" | tee -a "$WATCHDOG_LOG"
    nohup python "$BOT_DIR/$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
    
    # 检查是否启动成功
    sleep 10
    if pgrep -f "python.*$BOT_SCRIPT" > /dev/null; then
        echo "$(date) [SUCCESS] 机器人已成功重启" | tee -a "$WATCHDOG_LOG"
    else
        echo "$(date) [ERROR] 机器人重启失败" | tee -a "$WATCHDOG_LOG"
        # 可以在这里添加发送Telegram消息的代码
    fi
else
    echo "$(date) [ERROR] 找不到虚拟环境，请先运行server_deploy.sh脚本" | tee -a "$WATCHDOG_LOG"
fi

# 清理过大的日志文件
LOG_SIZE=$(du -m "$LOG_FILE" | cut -f1)
if [ "$LOG_SIZE" -gt 50 ]; then  # 如果日志大于50MB
    echo "$(date) [INFO] 日志文件过大(${LOG_SIZE}MB)，进行清理" | tee -a "$WATCHDOG_LOG"
    tail -n 1000 "$LOG_FILE" > "${LOG_FILE}.tmp"
    mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi

WATCHDOG_SIZE=$(du -k "$WATCHDOG_LOG" | cut -f1)
if [ "$WATCHDOG_SIZE" -gt 1024 ]; then  # 如果守护进程日志大于1MB
    echo "$(date) [INFO] 守护进程日志文件过大(${WATCHDOG_SIZE}KB)，进行清理" | tee -a "$WATCHDOG_LOG"
    tail -n 500 "$WATCHDOG_LOG" > "${WATCHDOG_LOG}.tmp"
    mv "${WATCHDOG_LOG}.tmp" "$WATCHDOG_LOG"
fi

exit 0 