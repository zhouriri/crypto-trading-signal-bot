"""
简化版Telegram机器人

提供基本功能，适用于测试和简单场景
"""

import os
import asyncio
import time
import logging
from typing import Dict, Any, Optional
import traceback
import requests
import telegram
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
from dotenv import load_dotenv

from .trading_bot import TradingBot

class SimpleTelegramBot(TradingBot):
    """
    简化版Telegram机器人
    
    提供基本的交互功能，主要用于测试和简单场景
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化简化版Telegram机器人
        
        Args:
            config: 机器人配置信息
        """
        super().__init__(config)
        
        # 加载环境变量
        load_dotenv()
        
        # Telegram相关配置
        self.token = config.get('token', os.getenv('TELEGRAM_BOT_TOKEN'))
        if not self.token:
            raise ValueError("未找到Telegram Bot Token，请检查配置或环境变量")
        
        # 代理设置
        self.proxy = config.get('proxy', os.getenv('HTTP_PROXY'))
        
        # Telegram应用实例
        self.application = None
        
        self.logger.info(f"简化版Telegram机器人初始化完成")
    
    def initialize(self) -> bool:
        """
        初始化机器人
        
        Returns:
            初始化是否成功
        """
        super().initialize()
        
        try:
            # 设置代理（如果有）
            if self.proxy:
                os.environ['HTTP_PROXY'] = self.proxy
                os.environ['HTTPS_PROXY'] = self.proxy
                self.logger.info(f"已设置HTTP代理: {self.proxy}")
            
            # 强制删除webhook
            self._force_delete_webhook()
            
            self.logger.info("简化版Telegram机器人初始化成功")
            return True
        
        except Exception as e:
            self.logger.error(f"初始化简化版Telegram机器人失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def _force_delete_webhook(self) -> bool:
        """
        强制删除webhook和所有待处理的更新
        
        Returns:
            操作是否成功
        """
        try:
            self.logger.info("强制删除所有webhook和待处理更新...")
            
            # 使用直接HTTP请求删除webhook
            delete_webhook_url = f"https://api.telegram.org/bot{self.token}/deleteWebhook?drop_pending_updates=true"
            response = requests.get(delete_webhook_url, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.logger.info("成功删除webhook和清除所有待处理更新")
                else:
                    self.logger.error(f"删除webhook失败: {result.get('description', '未知错误')}")
            else:
                self.logger.error(f"删除webhook请求失败: {response.status_code} - {response.text}")
                
            # 等待API冷却
            self.logger.info("等待10秒，确保所有先前的请求已完成...")
            time.sleep(10)
            
            return True
            
        except Exception as e:
            self.logger.error(f"强制删除webhook时出错: {str(e)}")
            return False
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        处理/start命令
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
        """
        try:
            user = update.effective_user
            self.logger.info(f"收到来自用户 {user.id} ({user.first_name}) 的/start命令")
            
            await update.message.reply_text(f'你好，{user.first_name}！这是一个简单的测试机器人。')
            
            self.logger.info(f"成功回复用户 {user.id} 的/start命令")
        except Exception as e:
            self.logger.error(f"处理/start命令时出错: {str(e)}")
            await update.message.reply_text('发生错误，请稍后再试。')
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        处理/help命令
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
        """
        try:
            await update.message.reply_text('我是一个简单的测试机器人，目前只支持基本命令。')
        except Exception as e:
            self.logger.error(f"处理/help命令时出错: {str(e)}")
            await update.message.reply_text('发生错误，请稍后再试。')
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        处理错误
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
        """
        error = context.error
        error_str = str(error)
        error_type = type(error).__name__
        
        self.logger.error(f"更新 {update} 导致错误 {error_type}: {error_str}")
        
        try:
            # 处理Telegram API冲突错误
            if isinstance(error, telegram.error.Conflict):
                self.logger.error("检测到Telegram API冲突错误，可能有多个bot实例正在运行")
                
                # 尝试重置连接
                try:
                    # 强制删除webhook并清除所有待处理更新
                    delete_url = f"https://api.telegram.org/bot{self.token}/deleteWebhook?drop_pending_updates=true"
                    response = requests.get(delete_url, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('ok'):
                            self.logger.info("成功删除webhook和清除所有待处理更新")
                        else:
                            self.logger.error(f"删除webhook失败: {result}")
                    else:
                        self.logger.error(f"删除webhook请求失败: {response.status_code} - {response.text}")
                    
                    # 等待API冷却
                    self.logger.info("等待30秒让API冷却...")
                    await asyncio.sleep(30)
                    
                except Exception as reset_error:
                    self.logger.error(f"尝试重置连接时出错: {reset_error}")
                
                # 如果冲突无法解决，考虑关闭应用
                self.logger.warning("由于API冲突，将尝试优雅地关闭应用...")
                
                # 通知应用需要停止
                if hasattr(context, 'application') and hasattr(context.application, 'stop'):
                    try:
                        await context.application.stop()
                        self.logger.info("应用已优雅停止")
                    except Exception as stop_error:
                        self.logger.error(f"停止应用时出错: {stop_error}")
                
                # 标记机器人需要停止
                self.running = False
                
            # 处理其他类型的错误
            else:
                self.logger.error(f"未处理的错误类型: {error_type}")
        except:
            self.logger.exception("处理错误时发生异常")
    
    def analyze(self, symbol: str, strategy: Optional[str] = None) -> str:
        """
        分析市场数据（简化版本）
        
        Args:
            symbol: 交易对符号
            strategy: 策略类型，如果不提供则使用默认策略
            
        Returns:
            分析报告文本
        """
        return f"这是 {symbol} 的简单分析报告，使用 {strategy or self.strategy} 策略。\n\n" \
               f"注意：这是一个测试机器人，不提供实际的市场分析功能。"
    
    async def _start_polling(self) -> None:
        """
        启动机器人轮询
        """
        try:
            # 创建应用
            self.logger.info("正在创建应用实例...")
            self.application = Application.builder().token(self.token).build()
            self.logger.info("应用实例创建成功")
            
            # 添加命令处理器
            self.logger.info("正在添加命令处理器...")
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("help", self._help_command))
            self.logger.info("命令处理器添加成功")
            
            # 添加错误处理器
            self.application.add_error_handler(self._error_handler)
            
            # 启动机器人
            self.logger.info("准备启动轮询...")
            await self.application.start_polling(drop_pending_updates=True)
            
            # 保持运行直到收到停止信号
            while self.running:
                await asyncio.sleep(1)
            
            # 停止应用
            self.logger.info("正在停止应用...")
            await self.application.stop()
            
        except Exception as e:
            self.logger.error(f"启动轮询过程中出错: {str(e)}")
            traceback.print_exc()
            self.running = False
    
    def run(self) -> None:
        """
        运行机器人
        """
        super().run()
        
        try:
            # 运行异步事件循环
            asyncio.run(self._start_polling())
        except Exception as e:
            self.logger.error(f"运行机器人时出错: {str(e)}")
            traceback.print_exc()
        finally:
            self.logger.info("简化版Telegram机器人已停止")
    
    def stop(self) -> None:
        """
        停止机器人
        """
        self.logger.info("正在停止简化版Telegram机器人...")
        self.running = False
        
        # 应用实例将在异步循环中停止
        super().stop() 