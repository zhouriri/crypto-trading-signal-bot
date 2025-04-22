#!/usr/bin/env python
import requests
import os
import time
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logger.error("无法获取TELEGRAM_BOT_TOKEN环境变量，请检查.env文件")
    exit(1)

# 获取代理设置（如果有）
HTTP_PROXY = os.getenv('HTTP_PROXY')
proxies = None
if HTTP_PROXY:
    proxies = {
        'http': HTTP_PROXY,
        'https': HTTP_PROXY
    }
    logger.info(f"使用代理: {HTTP_PROXY}")

def get_webhook_info():
    """获取当前webhook信息"""
    logger.info("获取当前webhook信息...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url, proxies=proxies, timeout=30)
        data = response.json()
        if data.get("ok"):
            webhook_url = data.get("result", {}).get("url", "")
            pending_updates = data.get("result", {}).get("pending_update_count", 0)
            logger.info(f"当前webhook URL: {webhook_url}, 待处理更新: {pending_updates}")
            return data.get("result")
        else:
            logger.error(f"获取webhook信息失败: {data}")
            return None
    except Exception as e:
        logger.error(f"请求webhook信息时发生错误: {str(e)}")
        return None

def delete_webhook():
    """删除webhook并清除所有待处理的更新"""
    logger.info("删除webhook并清除所有待处理的更新...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
    
    # 多次尝试删除webhook，确保成功
    max_retries = 3
    for retry in range(max_retries):
        try:
            response = requests.get(url, proxies=proxies, timeout=30)
            data = response.json()
            
            if data.get("ok"):
                logger.info(f"webhook删除成功，待处理更新已清除 (尝试 {retry+1}/{max_retries})")
                return True
            else:
                logger.warning(f"删除webhook失败 (尝试 {retry+1}/{max_retries}): {data}")
                if retry < max_retries - 1:
                    logger.info("等待5秒后重试...")
                    time.sleep(5)
        except Exception as e:
            logger.error(f"删除webhook时出错 (尝试 {retry+1}/{max_retries}): {str(e)}")
            if retry < max_retries - 1:
                logger.info("等待5秒后重试...")
                time.sleep(5)
    
    return False

def set_temp_webhook():
    """设置一个临时webhook然后删除它，这可以帮助重置连接"""
    logger.info("设置临时webhook以重置连接...")
    temp_url = "https://example.com/temp_webhook_" + str(int(time.time()))
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={temp_url}"
    
    try:
        response = requests.get(url, proxies=proxies, timeout=30)
        data = response.json()
        
        if data.get("ok"):
            logger.info(f"临时webhook设置成功: {temp_url}")
            # 等待一段时间后删除它
            time.sleep(5)
            return delete_webhook()
        else:
            logger.warning(f"设置临时webhook失败: {data}")
            return False
    except Exception as e:
        logger.error(f"设置临时webhook时出错: {str(e)}")
        return False

def main():
    """主函数，执行Telegram API连接修复流程"""
    logger.info("===== Telegram API 连接修复工具启动 =====")
    
    # 1. 获取当前webhook信息
    webhook_info = get_webhook_info()
    
    # 2. 尝试设置一个临时webhook (这会强制中断任何现有的getUpdates连接)
    set_temp_webhook()
    
    # 3. 删除webhook
    success = delete_webhook()
    
    # 4. 再次检查webhook状态
    time.sleep(5)
    final_info = get_webhook_info()
    
    if success and final_info and not final_info.get("url"):
        logger.info("===== Telegram API 连接修复成功 =====")
        return True
    else:
        logger.error("===== Telegram API 连接修复失败 =====")
        return False

if __name__ == "__main__":
    main() 