from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import psutil
import sys
import traceback
import requests
import asyncio
import concurrent.futures
from threading import Lock
from queue import Queue
from functools import partial
import telegram

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 全局消息队列，用于线程间通信
message_queue = Queue()

# 全局应用上下文，用于在线程中访问应用和事件循环
app_context = None

# 从环境变量获取配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
HTTP_PROXY = os.getenv('HTTP_PROXY')
HTTPS_PROXY = os.getenv('HTTPS_PROXY')

# 设置系统环境变量
if HTTP_PROXY:
    os.environ['HTTP_PROXY'] = HTTP_PROXY
    os.environ['HTTPS_PROXY'] = HTTP_PROXY

# 创建市场数据和分析器实例
from market_data import MarketData
from market_analyzer import MarketAnalyzer

market_data = MarketData()
market_analyzer = MarketAnalyzer(market_data)

# 创建线程池以处理并行请求
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)  # 根据性能测试结果，设置为最优值
# 创建任务锁，防止同一用户同时触发多个分析任务
user_task_locks = {}
user_task_locks_mutex = Lock()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/start命令"""
    try:
        # 检查命令是否应该被处理
        command_name = "start"
        user_id = update.effective_user.id
        message_id = update.message.message_id
        command_id = f"{command_name}_{message_id}"
        
        # 初始化处理过的命令集合
        if 'processed_commands' not in context.bot_data:
            context.bot_data['processed_commands'] = set()
            
        # 检查命令是否已处理
        if command_id in context.bot_data['processed_commands']:
            logger.info(f"Command {command_id} already processed, ignoring")
            return
        
        # 标记命令为已处理
        context.bot_data['processed_commands'].add(command_id)
        
        # 清理过大的命令集合
        if len(context.bot_data['processed_commands']) > 1000:
            logger.info("Cleaning up processed commands cache")
            # 保留最近处理的命令，将集合转换为列表并保留后100个元素
            processed_list = list(context.bot_data['processed_commands'])
            context.bot_data['processed_commands'] = set(processed_list[-100:])
        
        user = update.effective_user
        logger.info(f"User {user.id} started the bot")
        
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
        logger.info(f"Welcome message sent to user {user.id}")
        
    except Exception as e:
        error_msg = f"处理start命令时出错: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        await update.message.reply_text("启动过程中出现错误，请稍后再试。")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理帮助命令"""
    try:
        # 检查命令是否应该被处理
        command_name = "help"
        user_id = update.effective_user.id
        message_id = update.message.message_id
        command_id = f"{command_name}_{message_id}"
        
        # 初始化处理过的命令集合
        if 'processed_commands' not in context.bot_data:
            context.bot_data['processed_commands'] = set()
            
        # 检查命令是否已处理
        if command_id in context.bot_data['processed_commands']:
            logger.info(f"Command {command_id} already processed, ignoring")
            return
        
        # 标记命令为已处理
        context.bot_data['processed_commands'].add(command_id)
        
        # 清理过大的命令集合
        if len(context.bot_data['processed_commands']) > 1000:
            logger.info("Cleaning up processed commands cache")
            # 保留最近处理的命令，将集合转换为列表并保留后100个元素
            processed_list = list(context.bot_data['processed_commands'])
            context.bot_data['processed_commands'] = set(processed_list[-100:])
        
        logger.info(f"Received help command from user {user_id}")
        
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
        logger.info(f"Help command processed successfully for user {user_id}")
    except Exception as e:
        logger.error(f"Error in help command: {str(e)}")
        await update.message.reply_text("处理命令时发生错误，请稍后重试")

# 后台线程函数，用于处理市场数据获取和分析
def analyze_market_data_task(symbol, strategy, user_id, update_obj, context_obj, message_obj, command_type):
    """后台线程任务，处理市场数据分析"""
    try:
        logger.info(f"后台线程开始分析 {symbol} 的 {strategy} 策略数据")
        
        # 生成分析报告
        report = market_analyzer.analyze_market(symbol, strategy)
        
        if not report:
            # 使用消息队列发送回主线程
            async def send_error_message():
                try:
                    await message_obj.reply_text(f"无法获取 {symbol} 的市场数据，请稍后再试。")
                    logger.info(f"发送了无法获取 {symbol} 市场数据的消息")
                except Exception as e:
                    logger.error(f"发送消息时出错: {str(e)}")
            
            # 将消息放入队列，由主线程的协程处理
            message_queue.put(send_error_message)
            logger.info(f"已将'无法获取{symbol}市场数据'的消息加入队列")
            return
        
        # 发送分析结果
        async def send_report():
            try:
                await message_obj.reply_text(report)
                logger.info(f"成功发送 {symbol} 的 {strategy} 分析报告")
            except Exception as e:
                logger.error(f"发送分析报告时出错: {str(e)}")
        
        message_queue.put(send_report)
        logger.info(f"成功完成 {symbol} 的 {strategy} 策略分析，报告已加入发送队列")
        
    except Exception as e:
        logger.error(f"线程分析 {symbol} 时发生错误: {str(e)}")
        traceback.print_exc()
        
        async def send_error():
            try:
                await message_obj.reply_text(f"分析 {symbol} 时发生错误，请稍后再试。")
                logger.info(f"发送了分析 {symbol} 错误的消息")
            except Exception as ex:
                logger.error(f"发送错误消息时出错: {str(ex)}")
        
        message_queue.put(send_error)
        logger.info(f"已将'分析{symbol}错误'的消息加入队列")
    finally:
        # 释放用户任务锁
        with user_task_locks_mutex:
            if user_id in user_task_locks:
                del user_task_locks[user_id]
                logger.info(f"用户 {user_id} 的任务锁已释放")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理分析命令"""
    try:
        # 检查消息ID，避免重复处理
        message_id = update.message.message_id
        command_id = f"analyze_{message_id}"
        
        # 初始化处理过的命令集合
        if 'processed_commands' not in context.bot_data:
            context.bot_data['processed_commands'] = set()
            
        # 如果已处理过，直接返回
        if command_id in context.bot_data['processed_commands']:
            logger.info(f"Command {command_id} already processed, ignoring")
            return
        
        # 标记为已处理
        context.bot_data['processed_commands'].add(command_id)
        
        # 获取用户ID
        user_id = update.effective_user.id
        logger.info(f"处理用户 {user_id} 的分析命令")
        
        # 检查用户是否已经有正在执行的任务
        with user_task_locks_mutex:
            if user_id in user_task_locks:
                await update.message.reply_text("您有一个正在进行的分析任务，请等待其完成后再发起新的请求。")
                return
            else:
                # 为用户添加任务锁
                user_task_locks[user_id] = True
        
        # 解析命令参数
        args = context.args
        if not args:
            with user_task_locks_mutex:
                if user_id in user_task_locks:
                    del user_task_locks[user_id]
            await update.message.reply_text("请指定要分析的交易对，例如：/analyze BTC")
            return
            
        # 获取交易对
        symbol = args[0].upper()
        strategy_param = args[1].lower() if len(args) > 1 else 'short'  # 默认为短期策略
        
        # 验证策略类型
        valid_strategies = ['short', 'mid', 'long']
        is_valid_strategy = strategy_param in valid_strategies
        
        # 使用有效的策略类型
        strategy = strategy_param if is_valid_strategy else 'short'
        strategy_desc = "短期" if strategy == 'short' else "中期" if strategy == 'mid' else "长期"
            
        # 保存交易对和策略类型
        context.user_data['last_symbol'] = symbol
        context.user_data['last_strategy'] = strategy
        
        # 构建统一的状态消息
        if not is_valid_strategy:
            status_msg = f"🔍 '{strategy_param}'不是有效的策略类型（可用：short/mid/long），将使用短期策略分析 {symbol}..."
        else:
            status_msg = f"🔍 正在分析 {symbol} 的{strategy_desc}市场数据，请稍候..."
        
        # 发送单一状态消息
        status_message = await update.message.reply_text(status_msg)
        logger.info(f"已发送分析状态消息：{status_msg}")
        
        # 在线程池中异步执行分析
        thread_pool.submit(
            analyze_market_data_task,
            symbol, 
            strategy, 
            user_id, 
            update, 
            context, 
            update.message,
            "analyze"
        )
        
    except Exception as e:
        logger.error(f"处理分析命令时发生错误: {str(e)}")
        traceback.print_exc()
        await update.message.reply_text("发生未知错误，请稍后再试。")
        # 确保释放用户任务锁
        with user_task_locks_mutex:
            if user_id in user_task_locks:
                del user_task_locks[user_id]

async def strategy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理策略切换命令"""
    try:
        # 检查消息ID，避免重复处理
        message_id = update.message.message_id
        command_id = f"strategy_{message_id}"
        
        # 初始化处理过的命令集合
        if 'processed_commands' not in context.bot_data:
            context.bot_data['processed_commands'] = set()
            
        # 如果已处理过，直接返回
        if command_id in context.bot_data['processed_commands']:
            logger.info(f"Command {command_id} already processed, ignoring")
            return
        
        # 标记为已处理
        context.bot_data['processed_commands'].add(command_id)
        
        # 获取用户ID
        user_id = update.effective_user.id
        logger.info(f"处理用户 {user_id} 的策略切换命令")
        
        # 检查用户是否已经有正在执行的任务
        with user_task_locks_mutex:
            if user_id in user_task_locks:
                await update.message.reply_text("您有一个正在进行的分析任务，请等待其完成后再发起新的请求。")
                return
            else:
                # 为用户添加任务锁
                user_task_locks[user_id] = True
        
        # 解析命令参数
        args = context.args
        if not args:
            with user_task_locks_mutex:
                if user_id in user_task_locks:
                    del user_task_locks[user_id]
            await update.message.reply_text("请指定要切换的策略类型，例如：/strategy mid")
            return
            
        # 获取策略类型
        strategy_param = args[0].lower()
        
        # 验证策略类型
        valid_strategies = ['short', 'mid', 'long']
        is_valid_strategy = strategy_param in valid_strategies
        
        # 使用有效的策略类型
        strategy = strategy_param if is_valid_strategy else 'short'
        strategy_desc = "短期" if strategy == 'short' else "中期" if strategy == 'mid' else "长期"
        
        # 获取之前分析的交易对
        symbol = context.user_data.get('last_symbol', 'BTC')
            
        # 保存策略类型
        context.user_data['last_strategy'] = strategy
        
        # 构建统一的状态消息
        if not is_valid_strategy:
            status_msg = f"🔍 '{strategy_param}'不是有效的策略类型（可用：short/mid/long），将使用短期策略分析 {symbol}..."
        else:
            status_msg = f"🔍 正在使用{strategy_desc}策略分析 {symbol}，请稍候..."
        
        # 发送单一状态消息
        await update.message.reply_text(status_msg)
        logger.info(f"已发送策略状态消息：{status_msg}")
        
        # 在线程池中异步执行分析
        thread_pool.submit(
            analyze_market_data_task,
            symbol, 
            strategy, 
            user_id, 
            update, 
            context, 
            update.message,
            "strategy"
        )
        
    except Exception as e:
        logger.error(f"处理策略切换命令时发生错误: {str(e)}")
        traceback.print_exc()
        await update.message.reply_text("发生未知错误，请稍后再试。")
        # 确保释放用户任务锁
        with user_task_locks_mutex:
            if user_id in user_task_locks:
                del user_task_locks[user_id]

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理错误"""
    try:
        # 获取异常信息
        error = context.error
        error_str = str(error)
        error_type = type(error).__name__
        
        # 详细记录错误
        logger.error(f"处理更新时发生错误: {error_type}: {error_str}")
        logger.error(f"导致错误的更新: {update}")
        
        # 特殊处理Telegram API冲突错误
        if isinstance(error, telegram.error.Conflict):
            conflict_count = context.bot_data.get('conflict_count', 0) + 1
            context.bot_data['conflict_count'] = conflict_count
            
            logger.critical(f"检测到Telegram API冲突错误 (第{conflict_count}次): 可能有多个bot实例正在运行")
            
            # 如果连续冲突次数过多，尝试主动重置连接
            if conflict_count >= 3:
                logger.critical("连续冲突次数过多，尝试重置API连接...")
                
                try:
                    # 重置连接 - 删除webhook并清除所有待处理更新
                    delete_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
                    async with telegram.request.HTTPXRequest().get(delete_url) as response:
                        result = await response.json()
                        logger.info(f"重置连接结果: {result}")
                    
                    # 等待连接冷却
                    logger.info("等待20秒让API冷却...")
                    await asyncio.sleep(20)
                    
                    # 重置冲突计数
                    context.bot_data['conflict_count'] = 0
                    logger.info("已重置冲突计数")
                except Exception as reset_error:
                    logger.error(f"尝试重置API连接时出错: {reset_error}")
                
                # 如果冲突次数过多，可能需要考虑退出应用程序
                if conflict_count >= 10:
                    logger.critical("冲突错误次数过多，将退出以防止API锁定！")
                    # 等待1分钟后退出，让其他任务有机会完成
                    await asyncio.sleep(60)
                    os._exit(1)  # 强制退出
        
        # 处理网络错误
        elif isinstance(error, (telegram.error.NetworkError, requests.exceptions.RequestException)):
            logger.error(f"网络错误: {error_str}")
            # 可以在这里添加重试逻辑
        
        # 处理Telegram API错误
        elif isinstance(error, telegram.error.TelegramError):
            logger.error(f"Telegram API错误: {error_str}")
            
            # 处理特定类型的错误
            if "Too Many Requests" in error_str:
                logger.warning("API限流，将暂停请求一段时间")
                # 可以在这里添加等待逻辑
            elif "Not Found" in error_str:
                logger.error("API资源未找到，可能是Token无效或API点已更改")
            elif "Unauthorized" in error_str:
                logger.critical("未授权访问API，可能是Token无效")
        
        # 处理其他类型的错误
        else:
            logger.error(f"未分类的错误: {error_type}: {error_str}")
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    except Exception as e:
        # 处理error_handler本身的错误
        logger.critical(f"处理错误时发生异常: {str(e)}")
        logger.critical(traceback.format_exc())

def main():
    """启动机器人"""
    try:
        # 记录启动开始时间
        start_time = datetime.now()
        logger.info(f"=== 机器人启动 | {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        
        # 彻底清理所有Python进程
        try:
            import subprocess
            logger.info("尝试终止所有现有的bot实例...")
            # 尝试多种方式终止进程
            subprocess.run("pkill -9 -f 'python.*bot.py'", shell=True)
            subprocess.run("ps aux | grep 'python.*bot.py' | grep -v grep | awk '{print $2}' | xargs -I{} kill -9 {}", shell=True)
            # 等待进程终止
            time.sleep(5)
            # 验证进程已终止
            result = subprocess.run("ps aux | grep 'python.*bot.py' | grep -v grep", shell=True, capture_output=True, text=True)
            if result.stdout.strip():
                logger.warning(f"仍有bot进程在运行: {result.stdout.strip()}")
            else:
                logger.info("已确认所有bot进程已终止")
        except Exception as e:
            logger.error(f"终止现有进程时出错: {str(e)}")
            logger.error(traceback.format_exc())
        
        # 确保不存在锁文件
        lock_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.lock')
        if os.path.exists(lock_file_path):
            try:
                os.remove(lock_file_path)
                logger.info(f"已删除锁文件 {lock_file_path}")
            except OSError as e:
                logger.error(f"删除锁文件失败: {e}")
        
        # 强制删除Telegram的webhook并清除所有待处理更新
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("未找到BOT_TOKEN环境变量，无法启动机器人")
            return
        
        try:
            import requests
            # 设置代理（如果有）
            proxies = {}
            http_proxy = os.getenv('HTTP_PROXY')
            if http_proxy:
                proxies = {
                    'http': http_proxy,
                    'https': http_proxy
                }
            
            # 获取当前webhook信息
            logger.info("获取当前webhook信息...")
            webhook_info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
            try:
                response = requests.get(webhook_info_url, proxies=proxies if proxies else None, timeout=15)
                webhook_info = response.json()
                if webhook_info.get('ok'):
                    webhook_url = webhook_info.get('result', {}).get('url', '')
                    pending_updates = webhook_info.get('result', {}).get('pending_update_count', 0)
                    logger.info(f"当前webhook URL: {webhook_url}, 待处理更新数量: {pending_updates}")
                else:
                    logger.warning(f"获取webhook信息失败: {webhook_info}")
            except Exception as e:
                logger.error(f"获取webhook信息时出错: {str(e)}")
            
            # 强制删除webhook和所有待处理更新
            logger.info("删除webhook并清除所有待处理的更新...")
            url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=true"
            
            # 多次尝试删除webhook，确保成功
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = requests.get(url, proxies=proxies if proxies else None, timeout=15)
                    result = response.json()
                    
                    if result.get('ok'):
                        logger.info(f"webhook删除成功，待处理更新已清除 (尝试 {retry+1}/{max_retries})")
                        break
                    else:
                        logger.warning(f"删除webhook失败 (尝试 {retry+1}/{max_retries}): {result}")
                        if retry < max_retries - 1:
                            logger.info(f"等待5秒后重试...")
                            time.sleep(5)
                except Exception as e:
                    logger.error(f"删除webhook时出错 (尝试 {retry+1}/{max_retries}): {str(e)}")
                    if retry < max_retries - 1:
                        logger.info(f"等待5秒后重试...")
                        time.sleep(5)
            
            # 等待Telegram API完全处理请求
            logger.info("等待Telegram API完全处理请求 (10秒)...")
            time.sleep(10)
            
            # 验证webhook已被删除
            try:
                response = requests.get(webhook_info_url, proxies=proxies if proxies else None, timeout=15)
                webhook_info = response.json()
                if webhook_info.get('ok'):
                    webhook_url = webhook_info.get('result', {}).get('url', '')
                    if not webhook_url:
                        logger.info("验证成功: webhook已被完全删除")
                    else:
                        logger.warning(f"webhook未完全删除，当前URL仍为: {webhook_url}")
                else:
                    logger.warning(f"验证webhook删除状态失败: {webhook_info}")
            except Exception as e:
                logger.error(f"验证webhook删除状态时出错: {str(e)}")
            
        except Exception as e:
            logger.error(f"处理webhook时出错: {str(e)}")
            logger.error(traceback.format_exc())
            
        # 设置代理配置
        try:
            logger.info("正在配置代理设置...")
            proxy_url = os.getenv('HTTP_PROXY')
            request = HTTPXRequest(proxy_url=proxy_url) if proxy_url else None
            logger.info(f"代理配置完成: {'使用代理' if proxy_url else '不使用代理'}")
        except Exception as e:
            logger.error(f"配置代理时出错: {str(e)}")
            traceback.print_exc()
 
        try:
            # 创建事件循环
            logger.info("正在创建事件循环...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("事件循环创建成功")
        except Exception as e:
            logger.error(f"创建事件循环时出错: {str(e)}")
            traceback.print_exc()
            raise

        try:
            # 创建应用
            logger.info("正在创建Telegram应用...")
            application = (
                Application.builder()
                .token(TELEGRAM_BOT_TOKEN)
                .request(request)
                .build()
            )
            logger.info("Telegram应用创建成功")
    
            # 存储应用程序和它的事件循环的引用，以便线程可以使用
            global app_context
            app_context = {
                'application': application,
                'loop': loop
            }
            logger.info("全局应用上下文设置完成")
        except Exception as e:
            logger.error(f"创建Telegram应用时出错: {str(e)}")
            traceback.print_exc()
            raise

        try:
            # 初始化应用的bot_data
            application.bot_data['processed_commands'] = set()
            logger.info("应用bot_data初始化完成")
    
            # 添加命令处理器 
            logger.info("正在添加命令处理器...")
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("analyze", analyze_command))
            application.add_handler(CommandHandler("strategy", strategy_command))
            logger.info("命令处理器添加完成")
    
            # 添加错误处理器
            application.add_error_handler(error_handler)
            logger.info("错误处理器添加完成")
        except Exception as e:
            logger.error(f"配置应用处理器时出错: {str(e)}")
            traceback.print_exc()
            raise
        
        try:
            async def message_processor():
                """处理来自线程的消息队列"""
                logger.info("启动消息处理器")
                try:
                    while True:
                        if not message_queue.empty():
                            task = message_queue.get()
                            try:
                                await task()
                            except Exception as e:
                                logger.error(f"执行消息任务时出错: {str(e)}")
                            finally:
                                message_queue.task_done()
                        await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"消息处理器异常: {str(e)}")
            
            # 创建一个异步任务来处理消息队列
            async def start_bot():
                """启动机器人和消息处理器"""
                logger.info("准备启动机器人和消息处理器...")
                try:
                    # 创建并启动消息处理任务
                    message_task = asyncio.create_task(message_processor())
                    logger.info("消息处理任务已创建")
                except Exception as e:
                    logger.error(f"创建消息处理任务时出错: {str(e)}")
                    traceback.print_exc()
                    raise
                
                try:
                    # 启动机器人
                    logger.info("正在初始化应用...")
                    await application.initialize()
                    logger.info("应用初始化完成")
                    
                    logger.info("正在启动应用...")
                    await application.start()
                    logger.info("应用启动完成")
                    
                    # 注意：在python-telegram-bot 22.0中，接口可能已更改
                    logger.info("正在启动updater轮询...")
                    try:
                        # 设置轮询参数
                        polling_params = {
                            "drop_pending_updates": True,
                            "allowed_updates": Update.ALL_TYPES
                        }
                        
                        # 尝试新API
                        if hasattr(application, 'updater') and hasattr(application.updater, 'start_polling'):
                            await application.updater.start_polling(**polling_params)
                            logger.info("使用updater.start_polling成功启动轮询")
                        # 尝试备用方法
                        elif hasattr(application, 'bot') and hasattr(application.bot, 'get_updates'):
                            logger.info("使用应用程序自身的轮询方法")
                            # 创建一个轮询任务
                            async def polling_task():
                                offset = None
                                error_count = 0
                                max_errors = 5
                                
                                while True:
                                    try:
                                        updates = await application.bot.get_updates(
                                            offset=offset,
                                            timeout=15,
                                            allowed_updates=Update.ALL_TYPES
                                        )
                                        
                                        if updates:
                                            offset = updates[-1].update_id + 1
                                            for update in updates:
                                                asyncio.create_task(application.process_update(update))
                                            
                                            # 重置错误计数
                                            error_count = 0
                                                
                                        await asyncio.sleep(0.5)
                                    except telegram.error.Conflict as ce:
                                        error_count += 1
                                        logger.error(f"轮询冲突错误 ({error_count}/{max_errors}): {ce}")
                                        
                                        if error_count >= max_errors:
                                            logger.critical("连续错误次数过多，尝试重置连接...")
                                            # 重置连接
                                            try:
                                                delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=true"
                                                requests.get(delete_url)
                                                logger.info("已尝试重置连接")
                                                # 重置错误计数
                                                error_count = 0
                                            except Exception as reset_error:
                                                logger.error(f"重置连接时出错: {reset_error}")
                                        
                                        await asyncio.sleep(5)  # 发生冲突错误时等待更长时间
                                    except Exception as e:
                                        error_count += 1
                                        logger.error(f"轮询过程中出错 ({error_count}/{max_errors}): {e}")
                                        
                                        if error_count >= max_errors:
                                            logger.critical("连续错误次数过多，将重启轮询...")
                                            # 重置错误计数
                                            error_count = 0
                                        
                                        await asyncio.sleep(5)  # 发生其他错误时等待时间
                            
                            polling_task_instance = asyncio.create_task(polling_task())
                            logger.info("手动轮询任务已启动")
                        else:
                            logger.error("无法找到合适的轮询方法，机器人可能无法收到消息")
                    except Exception as e:
                        logger.error(f"启动轮询时出错: {str(e)}")
                        traceback.print_exc()
                        raise
                    
                    logger.info("轮询启动完成")
                except Exception as e:
                    logger.error(f"启动应用时出错: {str(e)}")
                    traceback.print_exc()
                    raise
                
                # 保持机器人运行，直到被中断
                try:
                    logger.info("机器人已启动并正在运行...")
                    # 保持应用程序运行，直到按下Ctrl+C或发生其他中断
                    while True:
                        await asyncio.sleep(1)
                except (KeyboardInterrupt, asyncio.CancelledError) as e:
                    # 正常关闭
                    logger.info(f"机器人正在关闭: {type(e).__name__}")
                finally:
                    logger.info("开始清理资源...")
                    # 停止消息处理任务
                    try:
                        message_task.cancel()
                        await asyncio.wait_for(asyncio.shield(message_task), timeout=2)
                        logger.info("消息处理任务已取消")
                    except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                        logger.info(f"等待消息处理任务取消时超时或被取消: {type(e).__name__}")
                    
                    # 关闭机器人
                    try:
                        if 'polling_task_instance' in locals() and polling_task_instance:
                            logger.info("正在停止手动轮询任务...")
                            polling_task_instance.cancel()
                            try:
                                await asyncio.wait_for(asyncio.shield(polling_task_instance), timeout=2)
                            except (asyncio.TimeoutError, asyncio.CancelledError):
                                pass
                            logger.info("手动轮询任务已停止")
                        
                        if hasattr(application, 'updater') and hasattr(application.updater, 'stop'):
                            logger.info("正在停止updater...")
                            await application.updater.stop()
                            logger.info("updater已停止")
                        
                        logger.info("正在停止应用...")
                        await application.stop()
                        logger.info("应用已停止")
                        
                        logger.info("正在关闭应用...")
                        await application.shutdown()
                        logger.info("应用已关闭")
                    except Exception as e:
                        logger.error(f"关闭应用时出错: {str(e)}")
                        traceback.print_exc()
                    
                    logger.info("机器人已完全关闭")
            
            logger.info("准备启动机器人主循环...")
            
            # 运行事件循环直到完成
            loop.run_until_complete(start_bot())
            logger.info("机器人主循环完成，程序退出")

        except Exception as e:
            logger.error(f"在启动过程中发生未处理的异常: {str(e)}")
            traceback.print_exc()
            raise

    except Exception as e:
        logger.error(f"启动机器人失败: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        # 关闭线程池
        thread_pool.shutdown(wait=False)
    except Exception as e:
        logger.error(f"Bot stopped due to error: {str(e)}")
    finally:
        # 确保线程池被关闭
        thread_pool.shutdown(wait=False)
        logger.info("Bot shutdown complete") 