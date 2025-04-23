"""
Telegram交易机器人实现

基于TradingBot接口，实现通过Telegram与用户交互的机器人
"""

import os
import asyncio
import traceback
import concurrent.futures
from threading import Lock
from queue import Queue
from typing import Dict, Any, Optional, List, Callable
from functools import partial
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
import requests
import time
import psutil

from .trading_bot import TradingBot
from market_data import MarketData
from market_analyzer import MarketAnalyzer

class TelegramTradingBot(TradingBot):
    """
    Telegram交易机器人
    
    通过Telegram机器人API实现与用户的交互，提供市场分析和交易信号
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Telegram交易机器人
        
        Args:
            config: 机器人配置信息
        """
        super().__init__(config)
        
        # 加载环境变量
        load_dotenv()
        
        # Telegram相关属性
        self.token = config.get('token', os.getenv('TELEGRAM_BOT_TOKEN'))
        if not self.token:
            raise ValueError("未找到Telegram Bot Token，请检查配置或环境变量")
        
        # 设置代理
        self.http_proxy = config.get('http_proxy', os.getenv('HTTP_PROXY'))
        self.https_proxy = config.get('https_proxy', os.getenv('HTTPS_PROXY'))
        
        # 线程池和消息队列
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=config.get('thread_pool_size', 4)
        )
        self.message_queue = Queue()
        
        # 用户任务锁，防止同一用户同时触发多个分析任务
        self.user_task_locks = {}
        self.user_task_locks_mutex = Lock()
        
        # Telegram应用实例和缓存
        self.application = None
        self.processed_commands = set()
        self.command_processors = {}
        
        # 市场数据和分析器
        self.market_data = MarketData()
        self.market_analyzer = MarketAnalyzer(self.market_data)
        
        self.logger.info(f"Telegram交易机器人初始化完成: {self.token[:5]}...{self.token[-5:]}")
    
    def initialize(self) -> bool:
        """
        初始化Telegram交易机器人
        
        Returns:
            初始化是否成功
        """
        super().initialize()
        
        try:
            # 设置系统环境变量（如果配置了代理）
            if self.http_proxy:
                os.environ['HTTP_PROXY'] = self.http_proxy
                os.environ['HTTPS_PROXY'] = self.http_proxy
                self.logger.info(f"已设置HTTP代理: {self.http_proxy}")
            
            # 注册命令处理器
            self._register_command_handlers()
            
            # 尝试删除Telegram webhook
            self._delete_webhook()
            
            self.logger.info("Telegram交易机器人初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化Telegram机器人失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def _register_command_handlers(self) -> None:
        """注册命令处理器"""
        self.command_processors = {
            'start': self._start_command,
            'help': self._help_command,
            'analyze': self._analyze_command,
            'strategy': self._strategy_command
        }
    
    def _delete_webhook(self) -> bool:
        """删除Telegram webhook"""
        try:
            self.logger.info("正在删除Telegram webhook...")
            
            delete_url = f"https://api.telegram.org/bot{self.token}/deleteWebhook?drop_pending_updates=true"
            response = requests.get(delete_url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.logger.info("成功删除webhook")
                    time.sleep(5)  # 等待API处理
                    return True
                else:
                    self.logger.warning(f"删除webhook返回错误: {result}")
            else:
                self.logger.error(f"删除webhook请求失败: {response.status_code} - {response.text}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"删除webhook时出错: {str(e)}")
            return False
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理/start命令"""
        try:
            # 检查命令是否应该被处理
            if not self._should_process_command('start', update):
                return
            
            user = update.effective_user
            self.logger.info(f"用户 {user.id} 开始使用机器人")
            
            welcome_message = (
                f"*📊 欢迎使用加密货币交易信号机器人 📊*\n\n"
                f"本机器人基于专业技术指标分析市场行情，提供精准交易信号。\n\n"
                f"*🔍 核心功能：*\n"
                f"• 市场趋势识别与预测\n"
                f"• 多重技术指标综合分析\n"
                f"• 智能交易信号生成\n"
                f"• 多时间周期策略支持\n\n"
                f"*📱 使用指南：*\n"
                f"• /start - 获取欢迎信息\n"
                f"• /help - 查看完整使用说明\n"
                f"• /analyze [币种] [策略] - 分析指定币种\n"
                f"  例如：/analyze BTC short\n"
                f"• /strategy [类型] - 切换分析策略\n"
                f"  可选：short(短期)、mid(中期)、long(长期)\n\n"
                f"*⚠️ 风险提示：*\n"
                f"加密货币市场波动较大，所有分析仅供参考，请理性投资。"
            )
            
            await update.message.reply_markdown(welcome_message)
            self.logger.info(f"已向用户 {user.id} 发送欢迎消息")
            
        except Exception as e:
            self.logger.error(f"处理start命令时出错: {str(e)}")
            traceback.print_exc()
            await update.message.reply_text("启动过程中出现错误，请稍后再试。")
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理/help命令"""
        try:
            # 检查命令是否应该被处理
            if not self._should_process_command('help', update):
                return
            
            user_id = update.effective_user.id
            self.logger.info(f"收到用户 {user_id} 的help命令")
            
            help_text = """🤖 *交易信号机器人使用指南*

📊 *分析命令*
/analyze [交易对] [策略类型] - 分析指定交易对
  例如：
  /analyze BTC short - 短期策略分析（15分钟-1小时）
  /analyze BTC mid   - 中期策略分析（1-7天）
  /analyze BTC long  - 长期策略分析（1-4周）

🔄 *策略切换*
/strategy [策略类型] - 切换分析策略
  例如：
  /strategy short - 切换到短期策略
  /strategy mid   - 切换到中期策略
  /strategy long  - 切换到长期策略

📈 *策略说明*
1. 短期策略（short）
   - 时间周期：15分钟-1小时
   - 主要指标：RSI、MACD、EMA、成交量、资金费率
   - 适合：日内交易、短线操作

2. 中期策略（mid）
   - 时间周期：1-7天
   - 主要指标：MA20/MA50、OBV、RSI、箱体结构
   - 适合：趋势跟踪、波段操作

3. 长期策略（long）
   - 时间周期：1-4周
   - 主要指标：MVRV-Z、NVT、TVL、解锁周期
   - 适合：价值投资、定投布局

⚠️ *注意事项*
- 所有价格均为美元计价
- 建议搭配稳定币留足流动性
- 请根据自身风险承受能力调整仓位
- 市场有风险，投资需谨慎

📞 *支持*
如有问题或建议，请联系管理员"""
        
            await update.message.reply_text(help_text, parse_mode='Markdown')
            self.logger.info(f"已向用户 {user_id} 发送帮助信息")
            
        except Exception as e:
            self.logger.error(f"处理help命令时出错: {str(e)}")
            await update.message.reply_text("处理命令时发生错误，请稍后重试")
    
    async def _analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理/analyze命令"""
        try:
            # 检查命令是否应该被处理
            if not self._should_process_command('analyze', update):
                return
            
            # 获取用户ID
            user_id = update.effective_user.id
            self.logger.info(f"处理用户 {user_id} 的分析命令")
            
            # 检查用户是否已经有正在执行的任务
            with self.user_task_locks_mutex:
                if user_id in self.user_task_locks:
                    await update.message.reply_text("您有一个正在进行的分析任务，请等待其完成后再发起新的请求。")
                    return
                else:
                    # 为用户添加任务锁
                    self.user_task_locks[user_id] = True
            
            # 解析命令参数
            args = context.args
            if not args:
                with self.user_task_locks_mutex:
                    if user_id in self.user_task_locks:
                        del self.user_task_locks[user_id]
                await update.message.reply_text("请指定要分析的交易对，例如：/analyze BTC")
                return
                
            # 获取交易对
            symbol = args[0].upper()
            strategy_param = args[1].lower() if len(args) > 1 else self.strategy  # 使用当前策略
            
            # 验证策略类型
            valid_strategies = ['short', 'mid', 'long']
            is_valid_strategy = strategy_param in valid_strategies
            
            # 使用有效的策略类型
            strategy = strategy_param if is_valid_strategy else self.strategy
            strategy_desc = "短期" if strategy == 'short' else "中期" if strategy == 'mid' else "长期"
                
            # 保存用户的分析参数
            if not hasattr(context, 'user_data'):
                context.user_data = {}
            context.user_data['last_symbol'] = symbol
            context.user_data['last_strategy'] = strategy
            
            # 构建统一的状态消息
            if not is_valid_strategy:
                status_msg = f"🔍 '{strategy_param}'不是有效的策略类型（可用：short/mid/long），将使用{strategy_desc}策略分析 {symbol}..."
            else:
                status_msg = f"🔍 正在分析 {symbol} 的{strategy_desc}市场数据，请稍候..."
            
            # 发送状态消息
            await update.message.reply_text(status_msg)
            self.logger.info(f"已发送分析状态消息：{status_msg}")
            
            # 在线程池中异步执行分析
            self.thread_pool.submit(
                self._analyze_market_data_task,
                symbol, 
                strategy, 
                user_id, 
                update.message
            )
            
        except Exception as e:
            self.logger.error(f"处理analyze命令时出错: {str(e)}")
            traceback.print_exc()
            await update.message.reply_text("发生未知错误，请稍后再试。")
            # 确保释放用户任务锁
            with self.user_task_locks_mutex:
                if user_id in self.user_task_locks:
                    del self.user_task_locks[user_id]
    
    async def _strategy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理/strategy命令"""
        try:
            # 检查命令是否应该被处理
            if not self._should_process_command('strategy', update):
                return
            
            # 获取用户ID
            user_id = update.effective_user.id
            self.logger.info(f"处理用户 {user_id} 的策略切换命令")
            
            # 检查用户是否已经有正在执行的任务
            with self.user_task_locks_mutex:
                if user_id in self.user_task_locks:
                    await update.message.reply_text("您有一个正在进行的分析任务，请等待其完成后再发起新的请求。")
                    return
                else:
                    # 为用户添加任务锁
                    self.user_task_locks[user_id] = True
            
            # 解析命令参数
            args = context.args
            if not args:
                with self.user_task_locks_mutex:
                    if user_id in self.user_task_locks:
                        del self.user_task_locks[user_id]
                await update.message.reply_text("请指定要切换的策略类型，例如：/strategy mid")
                return
                
            # 获取策略类型
            strategy_param = args[0].lower()
            
            # 验证策略类型并切换
            if self.change_strategy(strategy_param):
                strategy_desc = "短期" if self.strategy == 'short' else "中期" if self.strategy == 'mid' else "长期"
                await update.message.reply_text(f"已切换到{strategy_desc}策略")
                self.logger.info(f"用户 {user_id} 已切换到 {self.strategy} 策略")
            else:
                await update.message.reply_text(f"'{strategy_param}'不是有效的策略类型，可用选项：short(短期)、mid(中期)、long(长期)")
                self.logger.info(f"用户 {user_id} 尝试切换到无效策略: {strategy_param}")
            
            # 释放用户任务锁
            with self.user_task_locks_mutex:
                if user_id in self.user_task_locks:
                    del self.user_task_locks[user_id]
                    
        except Exception as e:
            self.logger.error(f"处理strategy命令时出错: {str(e)}")
            traceback.print_exc()
            await update.message.reply_text("发生未知错误，请稍后再试。")
            # 确保释放用户任务锁
            with self.user_task_locks_mutex:
                if user_id in self.user_task_locks:
                    del self.user_task_locks[user_id]
    
    def _should_process_command(self, command_name: str, update: Update) -> bool:
        """
        检查命令是否应该被处理（避免重复处理）
        
        Args:
            command_name: 命令名称
            update: Telegram更新对象
            
        Returns:
            是否应该处理该命令
        """
        message_id = update.message.message_id
        command_id = f"{command_name}_{message_id}"
        
        # 检查命令是否已处理
        if command_id in self.processed_commands:
            self.logger.info(f"命令 {command_id} 已处理，跳过")
            return False
        
        # 标记命令为已处理
        self.processed_commands.add(command_id)
        
        # 清理过大的命令集合
        if len(self.processed_commands) > 1000:
            self.logger.info("清理命令缓存")
            # 保留最近处理的命令，将集合转换为列表并保留后100个元素
            processed_list = list(self.processed_commands)
            self.processed_commands = set(processed_list[-100:])
        
        return True
    
    def _analyze_market_data_task(self, symbol: str, strategy: str, user_id: int, message_obj) -> None:
        """
        后台线程任务，处理市场数据分析
        
        Args:
            symbol: 交易对符号
            strategy: 策略类型
            user_id: 用户ID
            message_obj: Telegram消息对象
        """
        try:
            self.logger.info(f"后台线程开始分析 {symbol} 的 {strategy} 策略数据")
            
            # 使用分析接口获取报告
            report = self.analyze(symbol, strategy)
            
            if not report:
                # 使用消息队列发送回主线程
                async def send_error_message():
                    try:
                        await message_obj.reply_text(f"无法获取 {symbol} 的市场数据，请稍后再试。")
                        self.logger.info(f"发送了无法获取 {symbol} 市场数据的消息")
                    except Exception as e:
                        self.logger.error(f"发送消息时出错: {str(e)}")
                
                # 将消息放入队列，由主线程的协程处理
                self.message_queue.put(send_error_message)
                self.logger.info(f"已将'无法获取{symbol}市场数据'的消息加入队列")
                return
            
            # 发送分析结果
            async def send_report():
                try:
                    await message_obj.reply_text(report)
                    self.logger.info(f"成功发送 {symbol} 的 {strategy} 分析报告")
                except Exception as e:
                    self.logger.error(f"发送分析报告时出错: {str(e)}")
            
            self.message_queue.put(send_report)
            self.logger.info(f"成功完成 {symbol} 的 {strategy} 策略分析，报告已加入发送队列")
            
        except Exception as e:
            self.logger.error(f"线程分析 {symbol} 时发生错误: {str(e)}")
            traceback.print_exc()
            
            async def send_error():
                try:
                    await message_obj.reply_text(f"分析 {symbol} 时发生错误，请稍后再试。")
                    self.logger.info(f"发送了分析 {symbol} 错误的消息")
                except Exception as ex:
                    self.logger.error(f"发送错误消息时出错: {str(ex)}")
            
            self.message_queue.put(send_error)
            self.logger.info(f"已将'分析{symbol}错误'的消息加入队列")
        finally:
            # 释放用户任务锁
            with self.user_task_locks_mutex:
                if user_id in self.user_task_locks:
                    del self.user_task_locks[user_id]
                    self.logger.info(f"用户 {user_id} 的任务锁已释放")
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        处理Telegram bot错误
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
        """
        try:
            # 获取异常信息
            error = context.error
            error_str = str(error)
            error_type = type(error).__name__
            
            # 详细记录错误
            self.logger.error(f"处理更新时发生错误: {error_type}: {error_str}")
            if update:
                self.logger.error(f"导致错误的更新: {update}")
            
            # 特殊处理Telegram API冲突错误
            if isinstance(error, telegram.error.Conflict):
                self.logger.critical(f"检测到Telegram API冲突错误: 可能有多个bot实例正在运行")
                
                # 尝试重置连接
                try:
                    self._delete_webhook()
                    
                    # 等待连接冷却
                    self.logger.info("等待20秒让API冷却...")
                    await asyncio.sleep(20)
                    
                except Exception as reset_error:
                    self.logger.error(f"尝试重置API连接时出错: {reset_error}")
            
            # 处理网络错误
            elif isinstance(error, (telegram.error.NetworkError, requests.exceptions.RequestException)):
                self.logger.error(f"网络错误: {error_str}")
            
            # 处理Telegram API错误
            elif isinstance(error, telegram.error.TelegramError):
                self.logger.error(f"Telegram API错误: {error_str}")
                
                # 处理特定类型的错误
                if "Too Many Requests" in error_str:
                    self.logger.warning("API限流，将暂停请求一段时间")
                    # 可以在这里添加等待逻辑
                elif "Not Found" in error_str:
                    self.logger.error("API资源未找到，可能是Token无效或API点已更改")
                elif "Unauthorized" in error_str:
                    self.logger.critical("未授权访问API，可能是Token无效")
            
            # 处理其他类型的错误
            else:
                self.logger.error(f"未分类的错误: {error_type}: {error_str}")
                self.logger.error(f"错误详情: {traceback.format_exc()}")
        
        except Exception as e:
            # 处理error_handler本身的错误
            self.logger.critical(f"处理错误时发生异常: {str(e)}")
            self.logger.critical(traceback.format_exc())
    
    async def _message_processor(self) -> None:
        """
        处理消息队列中的消息
        """
        self.logger.info("消息处理器启动")
        while self.running:
            try:
                # 检查队列中是否有消息
                if not self.message_queue.empty():
                    # 获取消息处理函数
                    message_func = self.message_queue.get()
                    
                    # 执行消息处理函数
                    await message_func()
                    
                    # 标记任务完成
                    self.message_queue.task_done()
                
                # 避免过度占用CPU
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"处理消息队列时出错: {str(e)}")
                traceback.print_exc()
                await asyncio.sleep(1)  # 出错后等待一段时间再继续
    
    def analyze(self, symbol: str, strategy: Optional[str] = None) -> str:
        """
        分析市场数据
        
        Args:
            symbol: 交易对符号
            strategy: 策略类型，如果不提供则使用默认策略
            
        Returns:
            分析报告文本
        """
        try:
            # 使用提供的策略或默认策略
            actual_strategy = strategy if strategy else self.strategy
            
            # 使用市场分析器获取分析结果
            self.logger.info(f"开始分析 {symbol} 使用 {actual_strategy} 策略")
            report = self.market_analyzer.analyze_market(symbol, actual_strategy)
            
            if not report:
                self.logger.warning(f"无法获取 {symbol} 的分析结果")
                return f"无法获取 {symbol} 的市场数据，请稍后再试。"
            
            self.logger.info(f"成功获取 {symbol} 的分析报告")
            return report
            
        except Exception as e:
            self.logger.error(f"分析 {symbol} 时出错: {str(e)}")
            traceback.print_exc()
            return f"分析 {symbol} 时发生错误: {str(e)}"
    
    async def _polling_task(self) -> None:
        """
        轮询任务
        """
        try:
            self.logger.info("开始轮询Telegram API")
            await self.application.start_polling(drop_pending_updates=True)
        except Exception as e:
            self.logger.error(f"轮询过程中出错: {str(e)}")
            traceback.print_exc()
            self.running = False
            
    async def _start_bot(self) -> None:
        """
        启动机器人
        """
        try:
            self.logger.info("准备创建Telegram应用")
            
            # 创建应用实例
            builder = Application.builder().token(self.token)
            
            # 如果设置了代理，配置请求对象
            if self.http_proxy:
                request = HTTPXRequest(proxy=self.http_proxy)
                builder = builder.request(request)
            
            self.application = builder.build()
            
            # 注册命令处理器
            for command, handler in self.command_processors.items():
                self.application.add_handler(CommandHandler(command, handler))
            
            # 注册错误处理器
            self.application.add_error_handler(self._error_handler)
            
            # 创建任务
            tasks = [
                asyncio.create_task(self._message_processor()),
                asyncio.create_task(self._polling_task())
            ]
            
            # 等待任务完成或者直到机器人停止运行
            self.logger.info("Telegram机器人启动成功，等待任务完成")
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"启动机器人时出错: {str(e)}")
            traceback.print_exc()
            self.running = False
    
    def run(self) -> None:
        """
        运行机器人
        """
        super().run()
        
        # 创建事件循环并运行
        try:
            self.logger.info("开始运行Telegram机器人")
            asyncio.run(self._start_bot())
        except Exception as e:
            self.logger.error(f"运行机器人时出错: {str(e)}")
            traceback.print_exc()
            self.running = False
        finally:
            self.logger.info("Telegram机器人已停止运行")
    
    def stop(self) -> None:
        """
        停止机器人
        """
        self.logger.info("正在停止Telegram机器人...")
        self.running = False
        
        # 关闭线程池
        self.thread_pool.shutdown(wait=False)
        
        # 停止异步应用（如果存在）
        if self.application:
            try:
                # 这里不能直接调用异步方法，只能标记为需要停止
                self.logger.info("已标记Telegram应用需要停止")
            except Exception as e:
                self.logger.error(f"停止Telegram应用时出错: {str(e)}")
        
        super().stop() 