"""
机器人管理器

负责创建、启动、停止和管理各种类型的交易机器人
"""

import os
import sys
import time
import logging
import signal
import traceback
import psutil
import subprocess
from typing import Dict, Any, Optional, Type, List
from dotenv import load_dotenv
import requests

from .trading_bot import TradingBot
from .telegram_bot import TelegramTradingBot
from .simple_bot import SimpleTelegramBot

class BotManager:
    """
    机器人管理器
    
    负责创建、启动、停止和管理各种类型的交易机器人
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化机器人管理器
        
        Args:
            config_path: 配置文件路径，如果不提供则使用默认配置
        """
        # 设置日志
        self.logger = self._setup_logger()
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 注册机器人类型
        self.bot_classes = {
            'telegram': TelegramTradingBot,
            'simple': SimpleTelegramBot
        }
        
        # 当前活跃的机器人实例
        self.active_bot = None
        
        self.logger.info("机器人管理器初始化完成")
    
    def _setup_logger(self) -> logging.Logger:
        """
        设置日志记录器
        
        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger("BotManager")
        
        # 避免重复设置处理器
        if not logger.handlers:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            formatter = logging.Formatter(log_format)
            
            # 添加文件处理器
            file_handler = logging.FileHandler("bot_manager.log")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # 设置日志级别
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        # 加载环境变量
        load_dotenv()
        
        # 默认配置
        config = {
            'bot_type': os.getenv('BOT_TYPE', 'telegram'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'proxy': os.getenv('HTTP_PROXY'),
            'default_strategy': 'short',
            'thread_pool_size': 4,
            'log_file': 'bot_output.log'
        }
        
        # 如果提供了配置文件路径，尝试加载配置文件
        if config_path and os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # 更新配置
                config.update(file_config)
                self.logger.info(f"从 {config_path} 加载配置")
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {str(e)}")
        
        return config
    
    def create_bot(self, bot_type: Optional[str] = None) -> Optional[TradingBot]:
        """
        创建机器人实例
        
        Args:
            bot_type: 机器人类型，如果不提供则使用配置中的类型
            
        Returns:
            创建的机器人实例，如果创建失败则返回None
        """
        try:
            # 确定机器人类型
            actual_type = bot_type or self.config.get('bot_type', 'telegram')
            
            # 检查是否支持该类型
            if actual_type not in self.bot_classes:
                self.logger.error(f"不支持的机器人类型: {actual_type}")
                return None
            
            # 获取机器人类
            bot_class = self.bot_classes[actual_type]
            
            # 创建机器人实例
            self.logger.info(f"正在创建 {actual_type} 类型的机器人...")
            bot = bot_class(self.config)
            
            self.logger.info(f"{actual_type} 机器人创建成功")
            return bot
            
        except Exception as e:
            self.logger.error(f"创建机器人失败: {str(e)}")
            traceback.print_exc()
            return None
    
    def start_bot(self, bot_type: Optional[str] = None) -> bool:
        """
        启动机器人
        
        Args:
            bot_type: 机器人类型，如果不提供则使用配置中的类型
            
        Returns:
            启动是否成功
        """
        try:
            # 先停止所有现有的机器人进程
            self.kill_existing_bots()
            
            # 重置Telegram API连接
            self.reset_telegram_connection()
            
            # 创建机器人实例
            bot = self.create_bot(bot_type)
            if not bot:
                self.logger.error("无法创建机器人实例")
                return False
            
            # 初始化机器人
            if not bot.initialize():
                self.logger.error("机器人初始化失败")
                return False
            
            # 保存为活跃的机器人实例
            self.active_bot = bot
            
            # 启动机器人
            self.logger.info("正在启动机器人...")
            bot.run()
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动机器人失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def stop_bot(self) -> bool:
        """
        停止当前活跃的机器人
        
        Returns:
            停止是否成功
        """
        try:
            if self.active_bot and self.active_bot.running:
                self.logger.info("正在停止活跃的机器人...")
                self.active_bot.stop()
                self.logger.info("机器人已停止")
                return True
            else:
                self.logger.warning("没有活跃的机器人需要停止")
                return False
                
        except Exception as e:
            self.logger.error(f"停止机器人失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def kill_existing_bots(self) -> bool:
        """
        强制终止所有可能正在运行的bot进程
        
        Returns:
            操作是否成功
        """
        self.logger.info("正在检查并终止所有可能的bot实例...")
        
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
                    self.logger.info(f"发现bot进程: PID={proc.info['pid']}, CMD={' '.join(proc.info['cmdline'])}")
                    # 发送SIGKILL信号强制终止进程
                    try:
                        os.kill(proc.info['pid'], signal.SIGKILL)
                        killed_processes.append(proc.info['pid'])
                        self.logger.info(f"已终止进程 {proc.info['pid']}")
                    except Exception as e:
                        self.logger.error(f"终止进程 {proc.info['pid']} 时出错: {str(e)}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # 方法2: 使用shell命令查找和终止进程
        try:
            # 查找并杀死所有python中包含bot.py的进程
            subprocess.run("pkill -9 -f 'python.*bot\.py'", shell=True)
            # 再次使用killall确保Python进程被终止
            subprocess.run("killall -9 python python3 | true", shell=True)
            self.logger.info("已执行额外的进程终止命令")
        except Exception as e:
            self.logger.error(f"执行shell终止命令时出错: {str(e)}")
        
        # 等待进程完全终止
        if killed_processes:
            self.logger.info(f"等待10秒确保所有进程已完全终止...")
            time.sleep(10)
            
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
                self.logger.warning(f"以下进程仍在运行: {still_running}")
                # 再次尝试终止
                for pid in still_running:
                    try:
                        os.kill(pid, signal.SIGKILL)
                        self.logger.info(f"再次尝试终止进程 {pid}")
                    except Exception:
                        pass
                # 最后等待一次
                time.sleep(5)
        else:
            self.logger.info("未发现正在运行的bot进程")
        
        return True
    
    def reset_telegram_connection(self) -> bool:
        """
        重置Telegram API连接
        
        Returns:
            操作是否成功
        """
        self.logger.info("正在重置Telegram API连接...")
        
        # 获取TOKEN
        bot_token = self.config.get('token', os.getenv('TELEGRAM_BOT_TOKEN'))
        if not bot_token:
            self.logger.error("未找到Telegram Bot Token")
            return False
        
        # 设置代理
        proxies = {}
        http_proxy = self.config.get('proxy', os.getenv('HTTP_PROXY'))
        if http_proxy:
            proxies = {
                'http': http_proxy,
                'https': http_proxy
            }
            self.logger.info(f"将使用代理: {http_proxy}")
        
        try:
            # 删除webhook并清除所有待处理更新
            delete_webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=true"
            
            # 多次尝试确保成功
            max_retries = 3
            success = False
            
            for i in range(max_retries):
                try:
                    response = requests.get(delete_webhook_url, proxies=proxies if proxies else None, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('ok'):
                            self.logger.info(f"成功删除webhook和清除待处理更新 (尝试 {i+1}/{max_retries})")
                            success = True
                            break
                        else:
                            self.logger.warning(f"删除webhook失败 (尝试 {i+1}/{max_retries}): {result}")
                    else:
                        self.logger.error(f"删除webhook请求失败 (尝试 {i+1}/{max_retries}): {response.status_code} - {response.text}")
                    
                    # 如果尚未成功，等待更长时间再重试
                    if i < max_retries - 1:
                        wait_time = (i + 1) * 5  # 递增等待时间
                        self.logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                
                except Exception as e:
                    self.logger.error(f"尝试删除webhook时出错 (尝试 {i+1}/{max_retries}): {str(e)}")
                    if i < max_retries - 1:
                        wait_time = (i + 1) * 5
                        self.logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
            
            if not success:
                self.logger.error("删除webhook失败，达到最大重试次数")
                return False
            
            # 等待API完全处理请求
            self.logger.info("等待30秒确保Telegram API完全处理请求...")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            self.logger.error(f"重置Telegram连接时出错: {str(e)}")
            return False
    
    def run_bot_externally(self, bot_type: str = 'main') -> bool:
        """
        使用外部进程启动机器人
        
        Args:
            bot_type: 机器人类型，'main'或'simple'
            
        Returns:
            启动是否成功
        """
        try:
            # 选择要启动的bot文件
            bot_file = 'bot.py' if bot_type == 'main' else 'simple_bot.py'
            
            # 使用完整的Python路径启动bot
            python_path = sys.executable
            self.logger.info(f"使用Python解释器: {python_path}")
            
            # 构建启动命令
            cmd = [python_path, bot_file]
            
            # 启动bot进程
            self.logger.info(f"执行命令: {' '.join(cmd)}")
            bot_process = subprocess.Popen(cmd)
            
            self.logger.info(f"Bot已启动，PID: {bot_process.pid}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动bot外部进程时出错: {str(e)}")
            return False 