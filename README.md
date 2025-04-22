# 加密货币交易信号机器人

这是一个基于 Telegram 的加密货币交易信号机器人，能够分析市场数据并生成交易信号。

## 功能特点

- 基于 Telegram 机器人 API 构建，支持多用户同时交互
- 多种技术指标综合分析，包括 RSI、MACD、EMA 等
- 多时间周期策略支持：短期（15分钟-1小时）、中期（1-7天）、长期（1-4周）
- 可分析市场趋势、成交量、合约持仓、筹码分布等多维度数据
- 自动生成交易建议和详细分析报告

## 技术架构

- **后端**：Python 3.12
- **API**：Telegram Bot API、Binance API
- **数据源**：Binance、CoinMarketCap
- **分析库**：pandas、numpy
- **并发处理**：asyncio、concurrent.futures

## 安装指南

### 环境需求

- Python 3.12 或更高版本
- 网络连接（可能需要代理以访问 Telegram API）

### 安装步骤

1. 克隆仓库：
   ```bash
   git clone <repository-url>
   cd 交易信号工具
   ```

2. 创建虚拟环境：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或者
   .venv\Scripts\activate  # Windows
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   ```bash
   cp .env.example .env
   # 使用编辑器打开 .env 文件，填入必要的配置信息
   # 尤其是 TELEGRAM_BOT_TOKEN 必须设置正确
   ```

## 使用方法

### 启动机器人

使用提供的启动脚本来安全地启动机器人：

```bash
./start_bot.sh
```

此脚本会自动：
1. 停止所有已有的 Python 进程
2. 清理 Telegram webhook
3. 启动机器人并记录进程 ID
4. 验证机器人是否成功启动

### 停止机器人

使用停止脚本来安全地终止机器人：

```bash
./stop_bot.sh
```

此脚本会：
1. 查找并停止所有与机器人相关的进程
2. 清理 Telegram webhook
3. 验证所有进程是否已经终止

### 查看日志

启动后，机器人的日志会被记录到 `bot_output.log` 文件中，可以通过以下命令查看：

```bash
tail -f bot_output.log
```

### 机器人命令

机器人支持以下命令：

- `/start` - 获取欢迎信息
- `/help` - 查看完整使用说明
- `/analyze [币种] [策略]` - 分析指定币种
  例如：`/analyze BTC short`
- `/strategy [类型]` - 切换分析策略
  可选：short(短期)、mid(中期)、long(长期)

## 故障排除

如果机器人无法正常启动或运行，可以尝试以下步骤：

1. 检查日志文件中的错误信息：`cat bot_output.log`
2. 确保 `.env` 文件中的配置正确
3. 确保网络连接正常，特别是对 Telegram API 的访问
4. 运行停止脚本 `./stop_bot.sh` 然后重新启动
5. 如果问题仍然存在，可以尝试完全清理环境：
   ```bash
   pkill -9 -f python
   curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook?drop_pending_updates=true"
   ```

## 项目结构

- `bot.py` - 主要的机器人程序
- `market_data.py` - 处理市场数据的模块
- `market_analyzer.py` - 分析市场数据的模块
- `market_analysis_rules.py` - 定义分析规则的模块
- `cmc_data.py` - 处理 CoinMarketCap 数据的模块
- `main.py` - 简单的测试脚本
- `start_bot.sh` - 启动脚本
- `stop_bot.sh` - 停止脚本

## 贡献

欢迎提交 Pull Request 或 Issue 来帮助改进这个项目。 