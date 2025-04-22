# 交易信号机器人香港服务器部署指南

此指南提供在香港云服务器上部署和运行交易信号机器人的详细步骤。

## 系统要求

- Linux系统（推荐Ubuntu 20.04/22.04或Debian 11/12）
- Python 3.8+
- 2GB+ RAM
- 10GB+ 磁盘空间
- 稳定的网络连接

## 部署步骤

### 1. 准备服务器

1. 连接到您的香港服务器：
   ```bash
   ssh user@your-server-ip
   ```

2. 更新系统（如果需要）：
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. 安装基本工具（如果需要）：
   ```bash
   sudo apt install git curl unzip python3 python3-pip python3-venv -y
   ```

### 2. 上传项目文件

**方法1：使用SCP**

在本地计算机上执行以下命令将项目文件上传到服务器：
   ```bash
   # 在本地计算机执行
   scp -r /本地项目路径/* user@your-server-ip:~/trading_bot/
   ```

**方法2：使用Git**

如果项目在Git仓库中：
   ```bash
   # 在服务器上执行
   mkdir -p ~/trading_bot
   cd ~/trading_bot
   git clone <repository-url> .
   ```

### 3. 运行部署脚本

1. 添加执行权限并运行部署脚本：
   ```bash
   cd ~/trading_bot
   chmod +x server_deploy.sh
   ./server_deploy.sh
   ```

2. 按照脚本提示输入必要信息（如Telegram Bot Token）。

### 4. 设置守护进程（可选）

如果您不想使用systemd服务，也可以设置crontab守护进程：

1. 添加执行权限：
   ```bash
   chmod +x watchdog.sh
   ```

2. 编辑crontab：
   ```bash
   crontab -e
   ```

3. 添加以下行，每10分钟检查一次机器人状态：
   ```
   */10 * * * * ~/trading_bot/watchdog.sh >> ~/trading_bot/watchdog.log 2>&1
   ```

## 管理机器人

部署后，您可以使用以下命令管理机器人：

### 使用systemd服务管理（推荐）

- **查看状态**：
  ```bash
  sudo systemctl status trading_bot.service
  ```

- **启动机器人**：
  ```bash
  sudo systemctl start trading_bot.service
  ```

- **停止机器人**：
  ```bash
  sudo systemctl stop trading_bot.service
  ```

- **重启机器人**：
  ```bash
  sudo systemctl restart trading_bot.service
  ```

- **查看日志**：
  ```bash
  journalctl -u trading_bot.service -f
  # 或者
  tail -f ~/trading_bot/bot_output.log
  ```

### 使用辅助脚本管理

部署脚本会创建以下辅助脚本：

- **启动机器人**：
  ```bash
  ~/trading_bot/start.sh
  ```

- **停止机器人**：
  ```bash
  ~/trading_bot/stop.sh
  ```

- **重启机器人**：
  ```bash
  ~/trading_bot/restart.sh
  ```

- **查看状态**：
  ```bash
  ~/trading_bot/status.sh
  ```

- **查看日志**：
  ```bash
  ~/trading_bot/logs.sh         # 显示最后100行日志
  ~/trading_bot/logs.sh follow  # 实时查看日志
  ```

## 故障排除

- **机器人无法启动**：
  查看日志文件 `~/trading_bot/bot_output.log` 获取错误信息。

- **冲突错误**：
  可能是多个机器人实例在运行，请运行 `pkill -9 -f "python.*bot.py"` 终止所有实例，然后重新启动。

- **Telegram连接问题**：
  手动运行Telegram修复工具：
  ```bash
  cd ~/trading_bot
  source venv/bin/activate
  python telegram_fix.py
  ```

- **更新代码后**：
  如果更新了代码，请重启服务：
  ```bash
  sudo systemctl restart trading_bot.service
  ```

## 安全提示

- 确保您的服务器有适当的防火墙配置
- 定期更新系统和软件包
- 避免使用root用户运行机器人
- 保护好您的.env文件和Telegram Token 