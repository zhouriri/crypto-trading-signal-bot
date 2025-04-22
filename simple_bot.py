#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import asyncio
import telegram
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv
import requests
import sys
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("未找到TELEGRAM_BOT_TOKEN环境变量")
logger.info(f"已获取Telegram Bot Token: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")

# 检查代理设置
PROXY = os.getenv("HTTP_PROXY")
if PROXY:
    logger.info(f"将使用HTTP代理: {PROXY}")
else:
    logger.info("没有设置HTTP代理")

def force_delete_webhook():
    """强制删除webhook和所有待处理的更新"""
    try:
        logger.info("强制删除所有webhook和待处理更新...")
        
        # 使用直接HTTP请求删除webhook
        delete_webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(delete_webhook_url, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info("成功删除webhook和清除所有待处理更新")
            else:
                logger.error(f"删除webhook失败: {result.get('description', '未知错误')}")
        else:
            logger.error(f"删除webhook请求失败: {response.status_code} - {response.text}")
            
        # 等待API冷却
        logger.info("等待10秒，确保所有先前的请求已完成...")
        time.sleep(10)
        
        # 验证webhook已删除
        webhook_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(webhook_info_url, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                webhook_url = result.get('result', {}).get('url', '')
                if not webhook_url:
                    logger.info("已确认webhook已成功删除")
                else:
                    logger.warning(f"webhook未完全删除，当前URL: {webhook_url}")
            else:
                logger.error(f"获取webhook信息失败: {result.get('description', '未知错误')}")
        
        # 再次等待，确保API已完全处理webhook删除请求
        logger.info("再等待10秒，确保API已完全处理webhook删除请求...")
        time.sleep(10)
        
    except Exception as e:
        logger.error(f"强制删除webhook时出错: {str(e)}")
        # 继续执行，不要让webhook删除失败阻止bot启动

async def start(update, context):
    """处理/start命令"""
    try:
        user = update.effective_user
        logger.info(f"收到来自用户 {user.id} ({user.first_name}) 的/start命令")
        
        await update.message.reply_text(f'你好，{user.first_name}！这是一个简单的测试机器人。')
        
        logger.info(f"成功回复用户 {user.id} 的/start命令")
    except Exception as e:
        logger.error(f"处理/start命令时出错: {str(e)}")
        await update.message.reply_text('发生错误，请稍后再试。')

async def help_command(update, context):
    """处理/help命令"""
    try:
        await update.message.reply_text('我是一个简单的测试机器人，目前只支持基本命令。')
    except Exception as e:
        logger.error(f"处理/help命令时出错: {str(e)}")
        await update.message.reply_text('发生错误，请稍后再试。')

async def error_handler(update, context):
    """处理错误"""
    error = context.error
    error_str = str(error)
    error_type = type(error).__name__
    
    logger.error(f"更新 {update} 导致错误 {error_type}: {error_str}")
    
    try:
        # 处理Telegram API冲突错误
        if isinstance(error, telegram.error.Conflict):
            logger.error("检测到Telegram API冲突错误，可能有多个bot实例正在运行")
            
            # 尝试重置连接
            try:
                # 强制删除webhook并清除所有待处理更新
                delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
                response = requests.get(delete_url, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logger.info("成功删除webhook和清除所有待处理更新")
                    else:
                        logger.error(f"删除webhook失败: {result}")
                else:
                    logger.error(f"删除webhook请求失败: {response.status_code} - {response.text}")
                
                # 等待API冷却
                logger.info("等待30秒让API冷却...")
                await asyncio.sleep(30)
                
            except Exception as reset_error:
                logger.error(f"尝试重置连接时出错: {reset_error}")
            
            # 如果冲突无法解决，考虑关闭应用
            logger.warning("由于API冲突，将尝试优雅地关闭应用...")
            
            # 等待一段时间以确保其他任务有机会完成
            await asyncio.sleep(10)
            
            # 通知应用需要停止
            if hasattr(context, 'application') and hasattr(context.application, 'stop'):
                try:
                    await context.application.stop()
                    logger.info("应用已优雅停止")
                except Exception as stop_error:
                    logger.error(f"停止应用时出错: {stop_error}")
            
            # 最后强制退出
            logger.critical("由于API冲突，程序即将退出")
            os._exit(1)  # 强制退出程序
            
        # 处理其他类型的错误
        else:
            logger.error(f"未处理的错误类型: {error_type}")
    except:
        logger.exception("处理错误时发生异常")

def main():
    """主函数"""
    try:
        logger.info("==== 简单测试机器人启动 ====")
        
        # 加载环境变量(已经在上面做了)
        logger.info("环境变量加载成功")
        
        # 强制删除webhook
        force_delete_webhook()
        
        # 创建应用
        logger.info("正在创建应用实例...")
        application = Application.builder().token(BOT_TOKEN).build()
        logger.info("应用实例创建成功")
        
        # 添加命令处理器
        logger.info("正在添加命令处理器...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        logger.info("命令处理器添加成功")
        
        # 添加错误处理器
        application.add_error_handler(error_handler)
        
        # 启动机器人
        logger.info("准备启动轮询...")
        application.run_polling(drop_pending_updates=True)
        
        logger.info("机器人已停止")
        
    except Exception as e:
        logger.error(f"机器人启动失败: {str(e)}")
        raise

if __name__ == "__main__":
    main() 