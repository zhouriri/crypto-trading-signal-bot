#!/bin/bash

# 交易信号机器人服务器部署脚本
# 使用方法：./server_deploy.sh

echo "===== 交易信号机器人服务器部署脚本 ====="
echo "$(date) - 开始部署"

# 检查运行环境
if [ "$(uname)" != "Linux" ]; then
  echo "警告：此脚本设计用于Linux服务器，当前系统为$(uname)"
  echo "建议在Linux系统上运行，特别是Ubuntu/Debian"
  read -p "是否继续？(y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# 创建工作目录
INSTALL_DIR="$HOME/trading_bot"
echo "将在 $INSTALL_DIR 目录安装机器人"
mkdir -p $INSTALL_DIR

# 转到工作目录
cd $INSTALL_DIR
echo "当前工作目录: $(pwd)"

# 复制当前目录的所有文件（如果是通过SSH上传的）
if [ -f "./bot.py" ] && [ -f "./market_analyzer.py" ]; then
  echo "检测到当前目录已有项目文件，跳过复制步骤"
else
  echo "请将项目文件上传到 $INSTALL_DIR 目录"
  echo "可以使用以下命令通过SSH上传项目文件："
  echo "scp -r /本地项目路径/* user@服务器IP:$INSTALL_DIR/"
  read -p "完成后按任意键继续..." -n 1
  echo
fi

# 检查必要文件
REQUIRED_FILES=("bot.py" "market_analyzer.py" "market_data.py" "requirements.txt" ".env")
MISSING_FILES=false

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "./$file" ]; then
    echo "错误：找不到必要文件 $file"
    MISSING_FILES=true
  fi
done

if [ "$MISSING_FILES" = true ]; then
  echo "缺少必要文件，请确保所有文件都已上传"
  exit 1
fi

# 设置Python环境
echo "正在设置Python环境..."
if command -v python3 &>/dev/null; then
  echo "找到Python3: $(python3 --version)"
else
  echo "未找到Python3，正在安装..."
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip python3-venv
fi

# 创建虚拟环境
echo "正在创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "正在安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 检查配置
echo "正在检查配置文件..."
if [ -f ".env" ]; then
  echo ".env配置文件已存在"
  # 检查是否含有必要的配置项
  if ! grep -q "TELEGRAM_BOT_TOKEN" .env; then
    echo "警告：.env文件中找不到TELEGRAM_BOT_TOKEN配置项"
    read -p "是否现在添加？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      read -p "请输入Telegram Bot Token: " BOT_TOKEN
      echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> .env
    fi
  fi
else
  echo "创建.env配置文件..."
  read -p "请输入Telegram Bot Token: " BOT_TOKEN
  echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" > .env
  read -p "请输入Telegram Chat ID (如果有): " CHAT_ID
  if [ ! -z "$CHAT_ID" ]; then
    echo "TELEGRAM_CHAT_ID=$CHAT_ID" >> .env
  fi
fi

# 创建systemd服务文件
echo "正在创建systemd服务..."
SERVICE_FILE="$HOME/trading_bot.service"
cat > $SERVICE_FILE << EOL
[Unit]
Description=Trading Signal Bot Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStartPre=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/telegram_fix.py
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/bot_output.log
StandardError=append:$INSTALL_DIR/bot_output.log
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOL

echo "服务文件创建完成：$SERVICE_FILE"

# 安装系统服务
echo "正在安装系统服务..."
sudo cp $SERVICE_FILE /etc/systemd/system/trading_bot.service
sudo systemctl daemon-reload
sudo systemctl enable trading_bot.service

# 创建管理脚本
echo "正在创建管理脚本..."

# 启动脚本
cat > "$INSTALL_DIR/start.sh" << EOL
#!/bin/bash
echo "正在启动交易信号机器人..."
sudo systemctl start trading_bot.service
echo "检查服务状态..."
sudo systemctl status trading_bot.service
EOL
chmod +x "$INSTALL_DIR/start.sh"

# 停止脚本
cat > "$INSTALL_DIR/stop.sh" << EOL
#!/bin/bash
echo "正在停止交易信号机器人..."
sudo systemctl stop trading_bot.service
echo "服务已停止"
EOL
chmod +x "$INSTALL_DIR/stop.sh"

# 重启脚本
cat > "$INSTALL_DIR/restart.sh" << EOL
#!/bin/bash
echo "正在重启交易信号机器人..."
sudo systemctl restart trading_bot.service
echo "检查服务状态..."
sudo systemctl status trading_bot.service
EOL
chmod +x "$INSTALL_DIR/restart.sh"

# 状态检查脚本
cat > "$INSTALL_DIR/status.sh" << EOL
#!/bin/bash
echo "交易信号机器人状态："
sudo systemctl status trading_bot.service

echo -e "\n日志最后50行："
tail -n 50 $INSTALL_DIR/bot_output.log
EOL
chmod +x "$INSTALL_DIR/status.sh"

# 创建日志查看脚本
cat > "$INSTALL_DIR/logs.sh" << EOL
#!/bin/bash
if [ "\$1" == "follow" ]; then
  echo "实时查看日志..."
  tail -f $INSTALL_DIR/bot_output.log
else
  echo "显示最后100行日志..."
  tail -n 100 $INSTALL_DIR/bot_output.log
fi
EOL
chmod +x "$INSTALL_DIR/logs.sh"

echo "是否立即启动服务？(y/n)"
read -p "" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "正在启动服务..."
  sudo systemctl start trading_bot.service
  echo "等待服务启动..."
  sleep 3
  sudo systemctl status trading_bot.service
  echo -e "\n查看日志："
  tail -n 20 $INSTALL_DIR/bot_output.log
fi

echo -e "\n===== 部署完成 ====="
echo "管理命令："
echo "  启动: $INSTALL_DIR/start.sh"
echo "  停止: $INSTALL_DIR/stop.sh"
echo "  重启: $INSTALL_DIR/restart.sh"
echo "  状态: $INSTALL_DIR/status.sh"
echo "  日志: $INSTALL_DIR/logs.sh [follow]"
echo "系统服务已安装为：trading_bot.service"
echo "工作目录：$INSTALL_DIR"
echo "日志文件位置：$INSTALL_DIR/bot_output.log" 