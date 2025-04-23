# 贡献指南

感谢您考虑为加密货币交易信号机器人项目做出贡献！这份文档提供了贡献代码、报告问题或提出新功能建议的指南。

## 行为准则

参与本项目的所有贡献者都应遵循以下行为准则：

- 尊重所有项目参与者，不论其经验水平、性别、性取向、残疾、种族或宗教信仰
- 使用包容性语言，避免侮辱性评论
- 接受建设性批评，将项目和社区利益放在首位
- 在发现问题或有改进建议时，通过适当渠道沟通

## 如何贡献

### 报告问题

如果您发现bug或有功能建议，请通过GitHub Issues提交报告：

1. 检查现有Issues，确保没有重复报告
2. 使用清晰标题和详细描述创建新Issue
3. 对于bug，请提供重现步骤、期望行为和实际行为
4. 如可能，提供截图或日志片段

### 提交代码

1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建一个Pull Request

### Pull Request准则

- 每个PR应专注于单一功能或修复
- 确保您的代码符合项目现有的代码风格和格式
- 更新文档以反映您的更改（如适用）
- 添加测试以验证您的更改（如适用）
- 确保所有测试通过
- 在PR描述中详细说明您的更改和理由

## 开发环境设置

1. Fork并克隆仓库：
   ```bash
   git clone https://github.com/yourusername/crypto-trading-signal-bot.git
   cd crypto-trading-signal-bot
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

4. 设置环境变量：
   ```bash
   cp .env.example .env
   # 编辑.env文件设置必要的配置
   ```

## 代码风格指南

本项目遵循以下代码风格规范：

- PEP 8 Python风格指南
- 使用4个空格缩进（不使用Tab）
- 函数和方法应包含docstring说明功能和参数
- 变量和函数名使用snake_case命名风格
- 类名使用CamelCase命名风格
- 模块级常量使用全大写命名风格

## 分支策略

- `main`: 主分支，保持稳定可部署状态
- `develop`: 开发分支，新功能合并到这里
- `feature/*`: 功能分支，用于开发新功能
- `bugfix/*`: 错误修复分支
- `hotfix/*`: 紧急修复分支，直接从main分支创建

## 版本发布流程

1. 从develop分支创建release分支
2. 完成最终测试和文档更新
3. 合并到main分支并打上版本标签
4. 合并回develop分支

## 许可证

通过贡献您的代码，您同意您的贡献将在项目的[MIT许可证](LICENSE)下发布。 