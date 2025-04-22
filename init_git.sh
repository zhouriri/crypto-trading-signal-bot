#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== 初始化Git仓库 ===${NC}"

# 检查Git是否已安装
if ! command -v git &> /dev/null; then
    echo -e "${RED}错误: Git未安装. 请先安装Git.${NC}"
    exit 1
fi

# 检查是否已是Git仓库
if [ -d .git ]; then
    echo -e "${YELLOW}提示: 这个目录已经是一个Git仓库.${NC}"
    
    # 提示用户是否要重新初始化
    read -p "是否要重新初始化? (y/n): " answer
    if [ "$answer" != "y" ]; then
        echo -e "${BLUE}操作已取消.${NC}"
        exit 0
    fi
    
    # 备份并删除旧的.git目录
    echo -e "${YELLOW}备份并删除旧的.git目录...${NC}"
    mv .git .git_backup_$(date +"%Y%m%d%H%M%S")
fi

# 初始化Git仓库
echo -e "${GREEN}初始化Git仓库...${NC}"
git init

# 添加.gitignore文件
if [ -f .gitignore ]; then
    echo -e "${GREEN}.gitignore文件已存在.${NC}"
else
    echo -e "${YELLOW}.gitignore文件不存在, 正在创建...${NC}"
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 虚拟环境
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# 日志文件
*.log
*.log.*
output.log
simple_bot.log
simple_bot_output.log
bot_log.txt
bot_output.log
bot_debug.log
bot_starter.log
market_analyzer.log
test_strategies.log

# 结果和临时文件
pip in
results/
backup_*/

# 本地配置
.env

# IDE相关
.idea/
.vscode/
*.swp
*.swo
.DS_Store
EOF
    echo -e "${GREEN}.gitignore文件已创建.${NC}"
fi

# 添加文件到暂存区
echo -e "${GREEN}添加文件到暂存区...${NC}"
git add .

# 给用户显示即将提交的文件
echo -e "${BLUE}将要提交的文件:${NC}"
git status -s

# 确认提交
read -p "确认初始提交? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo -e "${YELLOW}提交操作已取消, 但Git仓库已初始化成功.${NC}"
    echo -e "${YELLOW}您可以稍后手动提交文件.${NC}"
    exit 0
fi

# 提交
echo -e "${GREEN}创建初始提交...${NC}"
git commit -m "初始提交: 交易信号机器人"

echo -e "${BLUE}下一步:${NC}"
echo -e "${GREEN}1. 创建远程仓库 (如GitHub, GitLab等)${NC}"
echo -e "${GREEN}2. 添加远程仓库: ${YELLOW}git remote add origin <远程仓库URL>${NC}"
echo -e "${GREEN}3. 推送到远程仓库: ${YELLOW}git push -u origin master${NC} 或 ${YELLOW}git push -u origin main${NC}"
echo -e "${BLUE}Git仓库初始化完成!${NC}" 