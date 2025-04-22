#!/usr/bin/env python
import os
import sys
import requests
from dotenv import load_dotenv
import time
import logging

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def main():
    """验证Telegram机器人连接状态"""
    logger.info("开始验证Telegram机器人连接...")
    
    # 获取Bot Token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("未找到TELEGRAM_BOT_TOKEN环境变量")
        sys.exit(1)
    
    # 设置代理（如果有）
    proxies = {}
    http_proxy = os.getenv("HTTP_PROXY")
    if http_proxy:
        proxies = {
            'http': http_proxy,
            'https': http_proxy
        }
        logger.info(f"使用代理: {http_proxy}")
    
    # 1. 检查网络连接
    logger.info("正在检查网络连接...")
    try:
        response = requests.get("https://api.telegram.org", proxies=proxies, timeout=10)
        logger.info(f"Telegram API可访问性: {response.status_code}")
    except Exception as e:
        logger.error(f"无法访问Telegram API，请检查网络/代理设置: {str(e)}")
        sys.exit(1)
    
    # 2. 获取机器人信息
    logger.info("正在获取机器人信息...")
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, proxies=proxies, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            bot_info = result["result"]
            bot_name = bot_info.get("first_name", "未知")
            bot_username = bot_info.get("username", "未知")
            logger.info(f"机器人信息: 名称={bot_name}, 用户名=@{bot_username}")
        else:
            logger.error(f"获取机器人信息失败: {result}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"请求机器人信息时出错: {str(e)}")
        sys.exit(1)
    
    # 3. 获取webhook状态
    logger.info("正在获取webhook状态...")
    try:
        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        response = requests.get(url, proxies=proxies, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            webhook_info = result["result"]
            webhook_url = webhook_info.get("url", "")
            pending_updates = webhook_info.get("pending_update_count", 0)
            
            if webhook_url:
                logger.warning(f"警告: 发现webhook URL: {webhook_url}, 这可能会干扰polling模式")
                logger.warning(f"待处理更新: {pending_updates}")
                
                # 提示删除webhook
                logger.info("正在删除webhook以便使用polling模式...")
                delete_url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
                delete_response = requests.get(delete_url, proxies=proxies, timeout=10)
                delete_result = delete_response.json()
                
                if delete_result.get("ok"):
                    logger.info("webhook已成功删除")
                else:
                    logger.error(f"删除webhook失败: {delete_result}")
            else:
                logger.info("未配置webhook，机器人可使用polling模式")
        else:
            logger.error(f"获取webhook信息失败: {result}")
    except Exception as e:
        logger.error(f"请求webhook信息时出错: {str(e)}")
    
    # 4. 发送测试消息给自己（可选）
    logger.info("连接验证完成")
    logger.info("请确保HTTP_PROXY和HTTPS_PROXY环境变量正确设置（如需代理）")
    
    # 结果总结
    logger.info("验证结果:")
    logger.info("1. 网络连接: ✅")
    logger.info("2. 机器人Token: ✅")
    logger.info("3. Webhook状态已检查")
    logger.info("机器人应该可以正常连接Telegram API了")

if __name__ == "__main__":
    main() 