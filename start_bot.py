#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import subprocess
import requests
import signal
import psutil
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_starter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def kill_existing_bots():
    """强制终止所有可能正在运行的bot进程"""
    logger.info("正在检查并终止所有可能的bot实例...")
    
    # 方法1: 使用psutil查找和终止所有包含"bot.py"或"simple_bot.py"的Python进程
    killed_processes = []
    current_pid = os.getpid()  # 获取当前进程的PID，避免终止自身
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 跳过当前进程
            if proc.info['pid'] == current_pid:
                continue
                
            # 检查命令行参数中是否包含bot.py或simple_bot.py
            if proc.info['cmdline'] and any(bot_file in ' '.join(proc.info['cmdline']) 
                                            for bot_file in ['bot.py', 'simple_bot.py']):
                logger.info(f"发现bot进程: PID={proc.info['pid']}, CMD={' '.join(proc.info['cmdline'])}")
                # 发送SIGKILL信号强制终止进程
                try:
                    os.kill(proc.info['pid'], signal.SIGKILL)
                    killed_processes.append(proc.info['pid'])
                    logger.info(f"已终止进程 {proc.info['pid']}")
                except Exception as e:
                    logger.error(f"终止进程 {proc.info['pid']} 时出错: {str(e)}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # 方法2: 使用shell命令查找和终止进程
    try:
        # 查找并杀死所有python中包含bot.py的进程
        subprocess.run("pkill -9 -f 'python.*bot\.py'", shell=True)
        # 再次使用killall确保Python进程被终止
        subprocess.run("killall -9 python python3 | true", shell=True)
        logger.info("已执行额外的进程终止命令")
    except Exception as e:
        logger.error(f"执行shell终止命令时出错: {str(e)}")
    
    # 等待进程完全终止
    if killed_processes:
        logger.info(f"等待20秒确保所有进程已完全终止...")
        time.sleep(20)
        
        # 验证进程是否已终止
        still_running = []
        for pid in killed_processes:
            try:
                # 如果进程仍然存在，os.kill将不会引发异常
                os.kill(pid, 0)
                still_running.append(pid)
            except OSError:
                # 进程不存在，正常情况
                pass
        
        if still_running:
            logger.warning(f"以下进程仍在运行: {still_running}")
            # 再次尝试终止
            for pid in still_running:
                try:
                    os.kill(pid, signal.SIGKILL)
                    logger.info(f"再次尝试终止进程 {pid}")
                except Exception:
                    pass
            # 最后等待一次
            time.sleep(10)
    else:
        logger.info("未发现正在运行的bot进程")
    
    return True

def reset_telegram_connection():
    """重置Telegram API连接，删除webhook并清除所有待处理更新"""
    logger.info("正在重置Telegram API连接...")
    
    # 加载环境变量获取TOKEN
    load_dotenv()
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("未找到TELEGRAM_BOT_TOKEN环境变量")
        return False
    
    # 设置代理（如果有）
    proxies = {}
    http_proxy = os.getenv('HTTP_PROXY')
    if http_proxy:
        proxies = {
            'http': http_proxy,
            'https': http_proxy
        }
        logger.info(f"将使用代理: {http_proxy}")
    
    try:
        # 1. 检查当前webhook状态
        webhook_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(webhook_info_url, proxies=proxies if proxies else None, timeout=30)
        
        if response.status_code == 200:
            webhook_info = response.json()
            if webhook_info.get('ok'):
                webhook_url = webhook_info.get('result', {}).get('url', '')
                pending_updates = webhook_info.get('result', {}).get('pending_update_count', 0)
                logger.info(f"当前webhook状态: URL={webhook_url}, 待处理更新={pending_updates}")
            else:
                logger.warning(f"获取webhook信息失败: {webhook_info}")
        else:
            logger.error(f"获取webhook信息请求失败: {response.status_code} - {response.text}")
        
        # 2. 删除webhook并清除所有待处理更新
        delete_webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        
        # 多次尝试确保成功
        max_retries = 5
        success = False
        
        for i in range(max_retries):
            try:
                response = requests.get(delete_webhook_url, proxies=proxies if proxies else None, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logger.info(f"成功删除webhook和清除待处理更新 (尝试 {i+1}/{max_retries})")
                        success = True
                        break
                    else:
                        logger.warning(f"删除webhook失败 (尝试 {i+1}/{max_retries}): {result}")
                else:
                    logger.error(f"删除webhook请求失败 (尝试 {i+1}/{max_retries}): {response.status_code} - {response.text}")
                
                # 如果尚未成功，等待更长时间再重试
                if i < max_retries - 1:
                    wait_time = (i + 1) * 10  # 递增等待时间: 10秒, 20秒, 30秒...
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
            
            except Exception as e:
                logger.error(f"尝试删除webhook时出错 (尝试 {i+1}/{max_retries}): {str(e)}")
                if i < max_retries - 1:
                    wait_time = (i + 1) * 10
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
        
        if not success:
            logger.error("删除webhook失败，达到最大重试次数")
            return False
        
        # 3. 等待API完全处理请求
        logger.info("等待60秒确保Telegram API完全处理请求...")
        time.sleep(60)
        
        # 4. 验证webhook已被删除
        try:
            response = requests.get(webhook_info_url, proxies=proxies if proxies else None, timeout=30)
            
            if response.status_code == 200:
                webhook_info = response.json()
                if webhook_info.get('ok'):
                    webhook_url = webhook_info.get('result', {}).get('url', '')
                    if not webhook_url:
                        logger.info("验证成功: webhook已被完全删除")
                        return True
                    else:
                        logger.warning(f"webhook未完全删除，当前URL仍为: {webhook_url}")
                        return False
            
            logger.error("验证webhook删除状态失败")
            return False
            
        except Exception as e:
            logger.error(f"验证webhook删除状态时出错: {str(e)}")
            return False
    
    except Exception as e:
        logger.error(f"重置Telegram连接时出错: {str(e)}")
        return False

def start_bot(bot_type='main'):
    """启动指定的bot"""
    logger.info(f"正在启动 {bot_type} bot...")
    
    # 选择要启动的bot文件
    bot_file = 'bot.py' if bot_type == 'main' else 'simple_bot.py'
    
    try:
        # 使用完整的Python路径启动bot
        python_path = sys.executable
        logger.info(f"使用Python解释器: {python_path}")
        
        # 构建启动命令
        cmd = [python_path, bot_file]
        
        # 启动bot进程
        logger.info(f"执行命令: {' '.join(cmd)}")
        bot_process = subprocess.Popen(cmd)
        
        logger.info(f"Bot已启动，PID: {bot_process.pid}")
        return True
    
    except Exception as e:
        logger.error(f"启动bot时出错: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始安全启动Bot程序 ===")
    
    # 步骤1: 终止所有现有的bot实例
    if not kill_existing_bots():
        logger.error("终止现有bot实例失败，中止启动")
        return
    
    # 步骤2: 重置Telegram API连接
    if not reset_telegram_connection():
        logger.warning("重置Telegram API连接可能不完全，将继续尝试启动")
        # 额外等待时间以防万一
        logger.info("额外等待30秒...")
        time.sleep(30)
    
    # 步骤3: 启动指定的bot
    bot_type = 'main'  # 默认启动main bot
    
    # 检查命令行参数，看是否指定了bot类型
    if len(sys.argv) > 1 and sys.argv[1] in ['main', 'simple']:
        bot_type = sys.argv[1]
    
    logger.info(f"准备启动 {bot_type} bot...")
    if start_bot(bot_type):
        logger.info(f"{bot_type} bot已成功启动")
    else:
        logger.error(f"启动 {bot_type} bot失败")

if __name__ == "__main__":
    main() 