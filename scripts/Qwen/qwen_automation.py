import json
import time
import logging
import os
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
from datetime import datetime


class QwenAutomation:
    """通义千问 AI 网页自动化工具"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化自动化工具
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件并处理环境变量替换"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 递归处理环境变量替换
            def replace_env_vars(obj):
                if isinstance(obj, dict):
                    return {k: replace_env_vars(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [replace_env_vars(item) for item in obj]
                elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
                    # 提取环境变量名
                    env_var = obj[2:-1]
                    env_value = os.getenv(env_var)
                    if env_value is None:
                        raise ValueError(f"环境变量 {env_var} 未设置")
                    return env_value
                else:
                    return obj
            
            return replace_env_vars(config)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        except ValueError as e:
            raise ValueError(f"配置文件处理错误: {e}")
    
    def _setup_logging(self):
        """设置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('qwen_automation.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_driver(self) -> webdriver.Chrome:
        """设置 Chrome 驱动"""
        options = Options()
        
        # 基本设置
        if self.config['browser']['headless']:
            options.add_argument('--headless')
        
        # 窗口大小
        window_size = self.config['browser']['window_size']
        options.add_argument(f'--window-size={window_size}')
        
        # 用户数据目录 - 创建唯一目录避免冲突
        user_data_dir = self.config['browser']['user_data_dir']
        if user_data_dir:
            # 添加时间戳确保唯一性
            import time
            unique_dir = f"{user_data_dir}_{int(time.time())}"
            options.add_argument(f'--user-data-dir={os.path.abspath(unique_dir)}')
        
        # 其他有用的选项
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 设置用户代理
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        
        try:
            # 创建驱动 - 为 Apple Silicon Mac 优化
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # 执行反检测脚本
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            self.logger.error(f"启动 ChromeDriver 失败: {str(e)}")
            # 尝试使用系统默认的 Chrome 路径
            try:
                self.logger.info("尝试使用系统 Chrome 浏览器...")
                options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                driver = webdriver.Chrome(options=options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                return driver
            except Exception as e2:
                self.logger.error(f"使用系统 Chrome 也失败: {str(e2)}")
                raise e2
    
    def start_browser(self):
        """启动浏览器"""
        self.logger.info("启动浏览器...")
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, self.config['browser']['timeout'])
        self.logger.info("浏览器启动成功")
    
    def navigate_to_qwen(self):
        """导航到通义千问 AI 网站"""
        url = "https://chat.qwen.ai/"
        self.logger.info(f"导航到 {url}")
        self.driver.get(url)
        time.sleep(self.config['automation']['wait_time'])
        
        # 检查是否遇到 Cloudflare 验证
        if self.handle_cloudflare_challenge():
            self.logger.info("Cloudflare 验证处理完成")
    
    def handle_cloudflare_challenge(self) -> bool:
        """处理 Cloudflare 安全验证
        
        Returns:
            bool: 是否遇到并处理了 Cloudflare 验证
        """
        try:
            # 检测 Cloudflare 验证页面的关键指示器
            cloudflare_indicators = [
                "继续之前，chat.qwen.ai 需要先检查您的连接的安全性",
                "Please wait while we check your browser",
                "Checking your browser"
            ]
            
            page_text = self.driver.page_source
            is_cloudflare_page = any(indicator in page_text for indicator in cloudflare_indicators)
            
            if not is_cloudflare_page:
                return False
                
            self.logger.info("检测到 Cloudflare 验证页面，开始处理...")
            
            # 从配置文件获取 Cloudflare 相关设置
            cf_config = self.config.get('cloudflare', {})
            max_wait_time = cf_config.get('max_wait_time', 30)
            check_interval = cf_config.get('check_interval', 1)
            auto_solve = cf_config.get('auto_solve', False)
            
            if not auto_solve:
                self.logger.info("自动解决 Cloudflare 验证已禁用，请手动完成验证")
                return False
            
            # 等待验证完成
            for attempt in range(max_wait_time):
                time.sleep(check_interval)
                current_page_text = self.driver.page_source
                
                # 如果页面不再包含 Cloudflare 验证文本，说明验证成功
                still_on_cloudflare = any(indicator in current_page_text for indicator in cloudflare_indicators)
                
                if not still_on_cloudflare:
                    self.logger.info("Cloudflare 验证成功，页面已跳转")
                    return True
                    
            self.logger.warning("Cloudflare 验证超时")
            return False
            
        except Exception as e:
            self.logger.error(f"处理 Cloudflare 验证时出错: {str(e)}")
            return False
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            # 通义千问登录状态检查：查找输入框或用户头像
            login_indicators = [
                'textarea[placeholder*="输入"]',  # 输入框
                'textarea',                       # 任何文本区域
                'div.user-avatar',               # 用户头像
                'button[data-testid="send-button"]',  # 发送按钮
                'div.sidebar-new-chat-button',   # 新建对话按钮
                'input[type="text"]',            # 文本输入框
                'div[contenteditable="true"]'    # 可编辑div
            ]
            
            # 首先尝试短时间等待
            for indicator in login_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    if elements and any(elem.is_displayed() for elem in elements):
                        self.logger.info(f"登录状态确认: 找到可见元素 {indicator}")
                        return True
                except Exception as e:
                    self.logger.debug(f"查找 {indicator} 失败: {str(e)}")
                    continue
            
            # 如果没找到明确的登录指示器，检查页面URL
            current_url = self.driver.current_url
            if 'chat.qwen.ai' in current_url and 'login' not in current_url.lower():
                self.logger.info(f"根据URL判断可能已登录: {current_url}")
                return True
            
            self.logger.warning("未找到明确的登录状态指示器")
            return False
            
        except Exception as e:
            self.logger.error(f"检查登录状态时出错: {str(e)}")
            return False
    
    def wait_for_login(self, timeout: int = 30) -> bool:
        """等待用户手动登录"""
        self.logger.info("请在浏览器中手动登录通义千问...")
        input("登录完成后，请按回车键继续...")
        return self.is_logged_in()
    
    def send_message(self, message: str) -> bool:
        """发送消息，使用增强的稳定性机制"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.info(f"发送消息尝试 {attempt + 1}/{max_retries}")
                
                # 使用改进的查找方法
                input_selectors = [
                    'textarea[placeholder*="输入"]',
                    'textarea[placeholder*="请输入"]', 
                    'textarea[placeholder*="发送消息"]',
                    'textarea.ant-input',
                    'textarea',
                    'div[contenteditable="true"]'
                ]
                
                input_element = self._wait_and_find_element(input_selectors, timeout=10)
                if not input_element:
                    self.logger.warning(f"发送消息尝试 {attempt + 1}/{max_retries} 失败: 未找到可用的输入框")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        self.logger.error("发送消息最终失败: 未找到可用的输入框")
                        return False
                
                # 使用安全输入方法
                send_result = self._safe_send_keys(input_element, message)
                if send_result is None:
                    # 需要重新查找元素
                    input_element = self._wait_and_find_element(input_selectors, timeout=5)
                    if input_element:
                        send_result = self._safe_send_keys(input_element, message)
                
                if not send_result:
                    self.logger.warning(f"输入消息失败，尝试 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        return False
                
                time.sleep(1)  # 等待输入完成
                
                # 查找并点击发送按钮
                send_selectors = [
                    'button.send-message-button',
                    'button[data-testid="send-button"]',
                    'div.send-button',
                    'button[type="submit"]',
                    'button[aria-label*="发送"]',
                    'svg[class*="send"]'  # 可能是 SVG 图标
                ]
                
                send_button = self._wait_and_find_element(send_selectors, timeout=5)
                if send_button:
                    click_result = self._safe_click(send_button)
                    if click_result is None:
                        # 重新查找发送按钮
                        send_button = self._wait_and_find_element(send_selectors, timeout=5)
                        if send_button:
                            click_result = self._safe_click(send_button)
                    
                    if not click_result:
                        # 尝试按回车键发送
                        try:
                            from selenium.webdriver.common.keys import Keys
                            input_element.send_keys(Keys.RETURN)
                        except Exception as e:
                            self.logger.warning(f"回车键发送失败: {str(e)}")
                else:
                    # 尝试按回车键发送
                    try:
                        from selenium.webdriver.common.keys import Keys
                        input_element.send_keys(Keys.RETURN)
                    except Exception as e:
                        self.logger.warning(f"回车键发送失败: {str(e)}")
                
                self.logger.info(f"消息已发送: {message[:50]}...")
                return True
                
            except Exception as e:
                self.logger.warning(f"发送消息尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待一下再重试
                    continue
                else:
                    self.logger.error(f"发送消息最终失败: {str(e)}")
                    return False
    
    def wait_for_response(self) -> Optional[Dict[str, str]]:
        """等待并获取AI回复"""
        try:
            timeout = self.config['automation']['response_timeout']
            start_time = time.time()
            
            self.logger.info("等待AI回复...")
            
            # 检查是否有思考按钮并尝试点击
            self._try_enable_thinking_mode()
            
            # 等待回复生成完成
            while time.time() - start_time < timeout:
                try:
                    # 检查是否有"正在思考"或"正在回复"的指示器
                    thinking_indicators = [
                        'div.thinking-indicator',
                        'div.loading-indicator',
                        'span[data-testid="thinking"]',
                        'div.response-generating',
                        'div[class*="generating"]',
                        'div[class*="loading"]'
                    ]
                    
                    is_thinking = False
                    for indicator in thinking_indicators:
                        if self.driver.find_elements(By.CSS_SELECTOR, indicator):
                            is_thinking = True
                            self.logger.debug(f"检测到思考指示器: {indicator}")
                            break
                    
                    if not is_thinking:
                        # 如果没有思考指示器，检查是否有完整回复
                        response_data = self._parse_response_with_bs4()
                        if response_data and (response_data.get('thinking_process') or response_data.get('formal_answer')):
                            return response_data
                    
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.debug(f"等待回复时出现错误: {str(e)}")
                    time.sleep(1)
            
            # 超时后尝试获取部分回复
            self.logger.warning("等待回复超时，尝试获取当前内容")
            return self._parse_response_with_bs4()
            
        except Exception as e:
            self.logger.error(f"等待回复时出错: {str(e)}")
            return None
    
    def _try_enable_thinking_mode(self):
        """尝试启用思考模式"""
        try:
            # 通义千问的深度思考按钮选择器（用户提供的具体路径）
            primary_thinking_selectors = [
                '#chat-message-input > div.chat-message-input-container.svelte-17xwb8y > div.chat-message-input-container-inner.svelte-17xwb8y > div.flex.items-center.min-h-\\[56px\\].mt-0\\.5.p-3.svelte-17xwb8y > div.scrollbar-none.flex.items-center.left-content.operationBtn.svelte-17xwb8y > div > button',
                # 简化版本的选择器
                'div.left-content.operationBtn button',
                '.operationBtn button',
                '#chat-message-input button'
            ]
            
            # 尝试找到并点击深度思考按钮
            for selector in primary_thinking_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            # 检查按钮文本是否包含思考相关词汇
                            button_text = elem.text.lower()
                            if any(keyword in button_text for keyword in ['思考', 'thinking', '深度', 'deep']):
                                elem.click()
                                self.logger.info(f"成功点击深度思考按钮: {selector}, 按钮文本: {elem.text}")
                                time.sleep(2)  # 等待思考模式激活
                                return True
                            # 如果没有文本，但是在已知的思考按钮位置，也尝试点击
                            elif selector == primary_thinking_selectors[0]:
                                elem.click()
                                self.logger.info(f"点击主要深度思考按钮（无文本验证）: {selector}")
                                time.sleep(2)
                                return True
                except Exception as e:
                    self.logger.debug(f"尝试点击思考按钮失败 {selector}: {str(e)}")
                    continue
            
            # 备用方案：查找其他可能的思考按钮
            fallback_selectors = [
                'button[class*="thinking"]',
                'button[data-testid*="thinking"]',
                'div[class*="thinking-toggle"]',
                'button[class*="reasoning"]',
                'button[title*="思考"]',
                'button[title*="详细"]',
                'button[aria-label*="thinking"]',
                'button[title*="深度"]',
                # 通过图标查找
                'button svg[class*="think"]',
                'button .icon-thinking'
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            elem.click()
                            self.logger.info(f"使用备用方案点击思考按钮: {selector}")
                            time.sleep(2)
                            return True
                except Exception as e:
                    self.logger.debug(f"备用思考按钮点击失败: {str(e)}")
                    continue
            
            self.logger.warning("未找到可用的深度思考按钮")
            return False
                    
        except Exception as e:
            self.logger.debug(f"尝试启用思考模式时出错: {str(e)}")
            return False
    
    def _parse_response_with_bs4(self) -> Optional[Dict[str, str]]:
        """使用BeautifulSoup解析页面获取回复内容，带改进的内容清理"""
        try:
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 调试：保存页面内容用于分析
            self._debug_save_page_content(html_content)
            
            # 首先尝试使用专门的提取方法
            thinking_content = self._extract_thinking_panel_content(soup)
            formal_answer = self._extract_main_response_content(soup)
            
            # 如果专门方法没有找到足够内容，使用原有的方法
            if not thinking_content or not formal_answer:
                # 分析页面结构
                structure = self._analyze_page_structure(soup)
                
                # 提取思考过程和正式回答
                if not thinking_content:
                    thinking_content = self._extract_thinking_content(soup, structure)
                if not formal_answer:
                    formal_answer = self._extract_formal_answer(soup, structure)
                
                # 如果思考过程和正式回答都提取到了相同内容，尝试分离
                if thinking_content and formal_answer and thinking_content == formal_answer:
                    thinking_content, formal_answer = self._separate_thinking_and_answer(formal_answer)
                
                if not thinking_content and not formal_answer:
                    # 使用回退方法
                    fallback_result = self._extract_content_fallback(soup)
                    if fallback_result:
                        thinking_content = fallback_result.get('thinking_process', '')
                        formal_answer = fallback_result.get('formal_answer', '')
            
            # 清理提取的内容
            if thinking_content:
                thinking_content = self._clean_extracted_content(thinking_content)
            if formal_answer:
                formal_answer = self._clean_extracted_content(formal_answer)
            
            return {
                'thinking_process': thinking_content or '',
                'formal_answer': formal_answer or '',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"解析回复内容失败: {str(e)}")
            return None
    
    def _debug_save_page_content(self, html_content: str):
        """调试用：保存页面内容用于分析"""
        try:
            # 只在调试时保存
            if self.logger.level <= logging.DEBUG:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                debug_file = f"debug_page_{timestamp}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.debug(f"页面内容已保存到: {debug_file}")
        except Exception as e:
            self.logger.debug(f"保存调试页面失败: {str(e)}")
    
    def _separate_thinking_and_answer(self, content: str) -> Tuple[str, str]:
        """分离思考过程和正式回答"""
        try:
            # 清理内容，移除重复的模型标识
            content = self._clean_qwen_response(content)
            
            # 尝试根据通义千问的实际回复格式分离内容
            lines = content.split('\n')
            thinking_lines = []
            answer_lines = []
            
            # 通义千问的分离策略
            is_in_answer_section = False
            step_count = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否包含步骤标记（这通常是思考过程）
                if any(marker in line.lower() for marker in ['step 1', 'step 2', 'step 3', '步骤1', '步骤2', '步骤3', 
                                                             'first', 'second', 'third', '首先', '其次', '然后']):
                    step_count += 1
                    thinking_lines.append(line)
                    is_in_answer_section = False
                    continue
                
                # 检查是否是最终答案的标志
                if any(marker in line.lower() for marker in ['final answer', '最终答案', '答案是', 'conclusion', 
                                                             '结论', '因此', 'therefore', 'so the answer', 
                                                             'boxed{', '答案：', '结果：']):
                    is_in_answer_section = True
                    answer_lines.append(line)
                    continue
                
                # 如果在答案部分，继续添加到答案
                if is_in_answer_section:
                    answer_lines.append(line)
                # 如果有步骤标记或者内容包含分析性质的词汇，归类为思考过程
                elif step_count > 0 or any(word in line.lower() for word in ['分析', '观察', '我们', '可以看到', 
                                                                              'examine', 'analyze', 'we can', 'note that']):
                    thinking_lines.append(line)
                # 其他情况，如果还没有明确的答案段落，归类为思考过程
                elif not is_in_answer_section:
                    thinking_lines.append(line)
                else:
                    answer_lines.append(line)
            
            thinking_content = '\n'.join(thinking_lines).strip()
            answer_content = '\n'.join(answer_lines).strip()
            
            # 如果没有明确分离出思考过程，但有步骤性内容，进行智能分割
            if not thinking_content and step_count == 0 and len(lines) > 3:
                # 将内容按照长度比例分割：前60%作为思考过程，后40%作为答案
                split_point = int(len(lines) * 0.6)
                thinking_content = '\n'.join(lines[:split_point]).strip()
                answer_content = '\n'.join(lines[split_point:]).strip()
                self.logger.info("使用智能长度分割分离思考过程和回答")
            
            # 如果分离结果合理，返回分离后的内容
            if thinking_content and answer_content:
                self.logger.info(f"成功分离内容 - 思考过程: {len(thinking_content)}字符, 回答: {len(answer_content)}字符")
                return thinking_content, answer_content
            elif thinking_content:
                # 如果只有思考过程，取后半部分作为答案
                mid_point = len(thinking_content) // 2
                answer_content = thinking_content[mid_point:]
                thinking_content = thinking_content[:mid_point]
                return thinking_content, answer_content
            else:
                # 如果都没有，将全部内容作为答案，思考过程为空
                return "", content
                
        except Exception as e:
            self.logger.debug(f"分离思考过程和回答失败: {str(e)}")
            return "", content
    
    def _clean_qwen_response(self, content: str) -> str:
        """清理通义千问回复中的重复和无用信息"""
        try:
            # 移除模型标识前缀（包含时间戳等）
            content = re.sub(r'Qwen\d*-\d*B-[A-Z0-9:]+\d+:\d+', '', content, flags=re.MULTILINE)
            content = re.sub(r'Qwen\d*-\d*B-[A-Z0-9:]+', '', content, flags=re.MULTILINE)
            
            # 移除复制询问解释文本
            content = re.sub(r'复制询问解释', '', content, flags=re.MULTILINE)
            
            # 移除界面元素
            content = re.sub(r'网页开发预览模式图像生成深度思考搜索', '', content, flags=re.MULTILINE)
            content = re.sub(r'人工智能生成的内容可能不准确。', '', content, flags=re.MULTILINE)
            content = re.sub(r'加载中\.\.\.', '', content, flags=re.MULTILINE)
            
            # 移除重复的问题
            lines = content.split('\n')
            cleaned_lines = []
            question_pattern = r'^[^=]*=.*这个等式是否成立'
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 跳过重复的问题行
                if re.match(question_pattern, line):
                    continue
                    
                # 跳过只包含表情符号的行
                if re.match(r'^[😊🎉]+$', line):
                    continue
                    
                # 跳过过短的行（可能是UI元素）
                if len(line) < 10 and not any(keyword in line.lower() for keyword in ['step', '步骤', '因此', '所以']):
                    continue
                    
                cleaned_lines.append(line)
            
            # 重新组合并清理多余空行
            content = '\n'.join(cleaned_lines)
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            self.logger.debug(f"清理回复内容失败: {str(e)}")
            return content
    
    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, str]:
        """分析页面结构"""
        structure = {}
        
        # 查找思考面板相关元素
        thinking_panels = soup.find_all(['div'], class_=re.compile(r'.*[Tt]hinking.*'))
        if thinking_panels:
            structure['thinking_panel'] = True
        
        # 查找消息容器
        message_containers = soup.find_all(['div'], class_=re.compile(r'.*[Mm]essage.*'))
        if message_containers:
            structure['message_container'] = True
        
        # 查找回复容器
        response_containers = soup.find_all(['div'], class_=re.compile(r'.*[Rr]esponse.*'))
        if response_containers:
            structure['response_container'] = True
        
        return structure
    
    def _extract_thinking_content(self, soup: BeautifulSoup, structure: Dict[str, str]) -> str:
        """提取思考过程内容"""
        thinking_content = ""
        
        try:
            # 通义千问启用深度思考后的选择器
            primary_thinking_selectors = [
                # 深度思考模式的专门容器
                'div[class*="deep-thinking"]',
                'div[class*="thinking-process"]',
                'div[class*="reasoning-step"]',
                'details[open] > div',  # 展开的思考详情
                'div.ThinkingPanel__Body--Visible',
                'div[data-testid*="thinking-content"]',
                # 可能的思考步骤容器
                'div[class*="step-by-step"]',
                'div[class*="analysis"]'
            ]
            
            # 先尝试主要的深度思考选择器
            for selector in primary_thinking_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 30:  # 确保有足够的内容
                        thinking_content = text
                        self.logger.info(f"找到深度思考内容，使用选择器: {selector}, 长度: {len(text)}")
                        break
                if thinking_content:
                    break
            
            # 如果没有找到，尝试通用的思考面板选择器
            if not thinking_content:
                fallback_selectors = [
                    'div[class*="thinking"]',
                    'div[class*="ThinkingPanel"]', 
                    'div.thinking-panel',
                    'div[class*="reasoning"]',
                    'details[class*="thinking"]',
                    'div[class*="thought"]',
                    'section[class*="thinking"]',
                    # 查找可能展开的详细内容
                    'details[open]',
                    'div[aria-expanded="true"]'
                ]
                
                for selector in fallback_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text and len(text) > 30:
                            thinking_content = text
                            self.logger.info(f"使用备用选择器找到思考内容: {selector}")
                            break
                    if thinking_content:
                        break
            
            # 如果还是没有找到专门的思考面板，尝试从回复内容中分离思考过程
            if not thinking_content:
                self.logger.info("未找到专门的思考面板，尝试从内容中分离")
                thinking_content = self._extract_thinking_from_content(soup)
            
        except Exception as e:
            self.logger.debug(f"提取思考内容时出错: {str(e)}")
        
        return thinking_content
    
    def _extract_thinking_from_content(self, soup: BeautifulSoup) -> str:
        """从回复内容中尝试分离思考过程"""
        try:
            # 查找所有可能包含回复的元素
            content_selectors = [
                'div[class*="message"]',
                'div[class*="response"]',
                'div[class*="content"]',
                'div[class*="chat"]',
                'pre', 'p'
            ]
            
            all_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 20:  # 过滤掉太短的内容
                        all_text += text + "\n"
            
            # 尝试识别思考过程的关键词
            thinking_keywords = [
                "Step 1", "步骤", "分析", "思考", "让我们", "首先", "我们可以看到",
                "根据", "因为", "所以", "推理", "证明", "解析", "观察"
            ]
            
            lines = all_text.split('\n')
            thinking_lines = []
            formal_lines = []
            
            is_thinking = False
            for line in lines:
                if any(keyword in line for keyword in thinking_keywords):
                    is_thinking = True
                    thinking_lines.append(line)
                elif "答案" in line or "结论" in line or "Final Answer" in line:
                    is_thinking = False
                    formal_lines.append(line)
                elif is_thinking:
                    thinking_lines.append(line)
                else:
                    formal_lines.append(line)
            
            thinking_content = '\n'.join(thinking_lines).strip()
            
            if thinking_content and len(thinking_content) > 50:
                self.logger.info("从内容中成功分离出思考过程")
                return thinking_content
            
        except Exception as e:
            self.logger.debug(f"从内容分离思考过程时出错: {str(e)}")
        
        return ""
    
    def _extract_formal_answer(self, soup: BeautifulSoup, structure: Dict[str, str]) -> str:
        """提取正式回答内容"""
        formal_answer = ""
        
        try:
            # 查找通义千问的回答内容
            answer_selectors = [
                'div.response-content-container',
                'div[class*="response"]',
                'div[class*="answer"]',
                'div.message-content',
                'div[class*="message"][data-role="assistant"]',
                'div[class*="ai-message"]',
                'div[class*="bot-message"]',
                # 通义千问特有的选择器
                'div[class*="chat-message"]',
                'div[data-testid*="message"]'
            ]
            
            # 首先尝试直接找到回答容器
            for selector in answer_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:
                        formal_answer = text
                        self.logger.info(f"找到回答内容，使用选择器: {selector}")
                        break
                if formal_answer:
                    break
            
            # 如果没有找到，尝试从所有文本中提取正式回答部分
            if not formal_answer:
                formal_answer = self._extract_answer_from_content(soup)
            
        except Exception as e:
            self.logger.debug(f"提取回答内容时出错: {str(e)}")
        
        return formal_answer
    
    def _extract_answer_from_content(self, soup: BeautifulSoup) -> str:
        """从页面内容中提取正式回答"""
        try:
            # 查找最后的AI回复消息
            message_containers = soup.find_all(['div'], class_=lambda x: x and ('message' in x.lower() or 'response' in x.lower() or 'chat' in x.lower()))
            
            # 从后往前查找，找到最新的AI回复
            for container in reversed(message_containers):
                text = container.get_text(strip=True)
                if text and len(text) > 20:
                    # 检查是否包含AI回复的特征
                    if any(indicator in text.lower() for indicator in ['qwen', '回答', 'answer', '解', '计算']):
                        self.logger.info("从消息容器中找到回答内容")
                        return text
            
            # 如果没找到，获取页面中最长的文本块
            all_divs = soup.find_all(['div', 'p', 'pre', 'span'])
            longest_text = ""
            for div in all_divs:
                text = div.get_text(strip=True)
                if len(text) > len(longest_text):
                    longest_text = text
            
            if longest_text and len(longest_text) > 50:
                self.logger.info("使用最长文本块作为回答内容")
                return longest_text
                
        except Exception as e:
            self.logger.debug(f"从内容提取回答时出错: {str(e)}")
        
        return ""
    
    def _extract_content_fallback(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """回退方法：提取最后的AI回复内容"""
        try:
            # 查找所有可能包含AI回复的元素
            possible_selectors = [
                'div[data-testid*="message"]',
                'div[class*="message"]',
                'div[class*="response"]',
                'div[class*="chat"]',
                'pre', 'p', 'span'
            ]
            
            all_content = ""
            for selector in possible_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:  # 过滤掉太短的内容
                        all_content += text + "\n"
            
            if all_content:
                return {
                    'thinking_process': '',
                    'formal_answer': all_content,
                    'timestamp': datetime.now().isoformat()
                }
            
        except Exception as e:
            self.logger.debug(f"回退内容提取失败: {str(e)}")
        
        return None
    
    def start_new_conversation(self):
        """开始新对话，使用增强的稳定性机制"""
        try:
            # 查找新建对话按钮的多种可能选择器
            new_chat_selectors = [
                'div.sidebar-new-chat-button > div',
                'button[data-testid="new-chat"]',
                'div.new-chat-button',
                'button.new-conversation',
                'button.new-chat-button',
                '[class*="new-chat"]',
                '[class*="new-conversation"]',
                'button[title*="新建"]',
                'button[aria-label*="新建"]'
            ]
            
            # 使用稳定的元素查找方法
            new_chat_button = self._wait_and_find_element(new_chat_selectors, timeout=5)
            if new_chat_button:
                click_result = self._safe_click(new_chat_button)
                if click_result is None:
                    # 重新查找按钮
                    new_chat_button = self._wait_and_find_element(new_chat_selectors, timeout=5)
                    if new_chat_button:
                        click_result = self._safe_click(new_chat_button)
                
                if click_result:
                    self.logger.info("成功点击新建对话按钮")
                    time.sleep(2)  # 等待新对话界面加载
                    return True
                else:
                    self.logger.warning("点击新建对话按钮失败")
            else:
                self.logger.warning("未找到新建对话按钮")
            
            return False
            
        except Exception as e:
            self.logger.error(f"开始新对话失败: {str(e)}")
            return False
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("浏览器已关闭")
            except Exception as e:
                self.logger.error(f"关闭浏览器时出错: {str(e)}")
    
    def ask_question(self, question: str) -> Optional[Dict[str, str]]:
        """提问并获取回复
        
        Args:
            question: 要提问的问题
            
        Returns:
            包含回复信息的字典，失败时返回None
        """
        try:
            # 如果配置了每条消息开启新对话
            if self.config['automation'].get('new_conversation_per_message', False):
                self.start_new_conversation()
            
            # 发送消息
            if not self.send_message(question):
                return None
            
            # 等待回复
            response_data = self.wait_for_response()
            
            if response_data:
                response_data['question'] = question
                
                # 保存回复到文件
                if self.config['automation'].get('save_responses', False):
                    self._save_response_to_file(question, response_data)
                
                return response_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"提问失败: {str(e)}")
            return None
    
    def ask_multiple_questions(self, questions: List[str]) -> List[Dict[str, str]]:
        """批量处理多个问题
        
        Args:
            questions: 问题列表
            
        Returns:
            结果列表
        """
        results = []
        
        for i, question in enumerate(questions, 1):
            self.logger.info(f"处理问题 {i}/{len(questions)}: {question[:50]}...")
            
            result = self.ask_question(question)
            if result:
                results.append(result)
            
            # 在问题之间添加延迟
            if i < len(questions):
                time.sleep(self.config['automation'].get('question_interval', 5))
        
        return results
    
    def _save_response_to_file(self, question: str, response_data: Dict[str, str]):
        """保存回复到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"qwen_response_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'question': question,
                    'response': response_data
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"回复已保存到: {filename}")
            
        except Exception as e:
            self.logger.error(f"保存回复失败: {str(e)}")
    
    def initialize(self) -> bool:
        """初始化浏览器并登录
        
        Returns:
            是否成功初始化
        """
        try:
            # 启动浏览器
            self.start_browser()
            
            # 导航到通义千问
            self.navigate_to_qwen()
            
            # 等待登录
            if not self.wait_for_login():
                self.logger.error("登录失败")
                return False
            
            self.logger.info("初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {str(e)}")
            return False
    
    def load_test_data(self, data_file: str = 'data/tricks/fusion_results_all.json'):
        """从融合结果文件加载测试数据"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                test_cases = []
                # 遍历所有结果
                if 'results' in data:
                    for formula, result in data['results'].items():
                        if isinstance(formula, str) and '=' in formula:
                            test_cases.append(formula)
                return test_cases
        except Exception as e:
            self.logger.error(f"加载测试数据失败: {str(e)}")
            return []
    
    def generate_prompt(self, formula: str) -> str:
        """生成提示词"""
        # 确保公式格式正确
        if not isinstance(formula, str):
            formula = str(formula)
        # 移除可能存在的多余空格
        formula = formula.strip()
        # 生成标准格式的提示词
        return f"{formula}\n这个等式是否成立？请给出尽量详细的思路和逐步化简或运算过程。"
    
    def _check_page_state(self) -> bool:
        """检查页面状态是否正常"""
        try:
            # 检查是否还在通义千问页面
            if not self.driver.current_url.startswith('https://chat.qwen.ai/'):
                self.logger.warning("不在通义千问页面")
                return False
            
            # 检查浏览器是否还可用
            if not self.driver.window_handles:
                self.logger.warning("浏览器窗口已关闭")
                return False
                
            # 检查是否有输入框
            try:
                input_selectors = [
                    'textarea[placeholder*="输入"]',
                    'textarea[placeholder*="请输入"]',
                    'textarea.chat-input',
                    'div[chat-input]',
                    'textarea'
                ]
                
                for selector in input_selectors:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        return True
                        
                self.logger.warning("未找到输入框")
                return False
            except:
                return False
                
        except Exception as e:
            self.logger.error(f"检查页面状态失败: {str(e)}")
            return False
    
    def _wait_for_login_state(self) -> bool:
        """等待登录状态"""
        try:
            timeout = 10
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.is_logged_in():
                    return True
                time.sleep(1)
            
            return False
        except:
            return False
    
    def _start_new_conversation(self):
        """开始新对话"""
        try:
            # 尝试点击新建对话按钮
            new_chat_selectors = [
                'div.sidebar-new-chat-button',
                'button[data-testid="new-chat"]',
                'div[class*="new-chat"]',
                'button[class*="new-chat"]'
            ]
            
            for selector in new_chat_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        element.click()
                        self.logger.info(f"成功点击新建对话按钮: {selector}")
                        time.sleep(2)
                        return True
                except:
                    continue
                    
            self.logger.warning("未找到新建对话按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"开始新对话失败: {str(e)}")
            return False

    def run_automation(self, test_data_file: str = 'data/tricks/fusion_results_all.json'):
        """运行自动化测试"""
        try:
            # 加载测试数据
            test_cases = self.load_test_data(test_data_file)
            if not test_cases:
                self.logger.error("没有可用的测试数据")
                return
            
            # 限制测试数量（前10个）
            test_cases = test_cases[:10]
            self.logger.info(f"开始测试 {len(test_cases)} 个案例")
            
            results = []
            for i, formula in enumerate(test_cases, 1):
                self.logger.info(f"测试案例 {i}/{len(test_cases)}: {formula}")
                
                try:
                    # 在每个案例开始前检查页面状态
                    if not self._check_page_state():
                        self.logger.warning(f"页面状态异常，尝试恢复...")
                        # 尝试刷新页面
                        self.driver.refresh()
                        time.sleep(3)
                        
                        # 等待登录状态
                        if not self._wait_for_login_state():
                            self.logger.error("无法恢复登录状态，跳过此案例")
                            continue
                    
                    # 生成提示词
                    prompt = self.generate_prompt(formula)
                    
                    # 提问并获取回复
                    result = self.ask_question(prompt)
                    if result:
                        result['original_formula'] = formula
                        results.append(result)
                        self.logger.info(f"案例 {i} 处理成功")
                    else:
                        self.logger.warning(f"案例 {i} 处理失败")
                    
                    # 在测试之间添加延迟并开始新对话
                    if i < len(test_cases):
                        self.logger.info("等待 3 秒并准备下一个案例...")
                        time.sleep(3)
                        
                        # 尝试开始新对话
                        self._start_new_conversation()
                        time.sleep(2)
                        
                except Exception as e:
                    self.logger.error(f"处理案例 {i} 时出错: {str(e)}")
                    continue
            
            # 保存所有结果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"qwen_automation_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"测试完成，结果已保存到: {filename}")
            self.logger.info(f"成功处理 {len(results)}/{len(test_cases)} 个案例")
            
        except Exception as e:
            self.logger.error(f"运行自动化测试失败: {str(e)}")

    def _wait_and_find_element(self, selectors, timeout=10, retry_count=3):
        """等待并查找元素，支持多个选择器和重试机制"""
        if isinstance(selectors, str):
            selectors = [selectors]
        
        for attempt in range(retry_count):
            try:
                # 等待页面稳定
                time.sleep(1)
                
                for selector in selectors:
                    try:
                        element = WebDriverWait(self.driver, timeout).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if element and element.is_displayed():
                            return element
                    except TimeoutException:
                        continue
                
                # 如果所有选择器都失败，再尝试一次
                if attempt < retry_count - 1:
                    logging.warning(f"元素查找失败，第{attempt + 1}次重试...")
                    time.sleep(2)
                    # 刷新页面状态
                    self.driver.execute_script("return document.readyState")
                    continue
                    
            except Exception as e:
                logging.warning(f"查找元素时出错: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
        
        return None

    def _safe_click(self, element, retry_count=3):
        """安全点击元素，处理stale element错误"""
        for attempt in range(retry_count):
            try:
                # 确保元素可见和可点击
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(element)
                )
                element.click()
                return True
            except StaleElementReferenceException:
                logging.warning(f"点击时发生stale element错误，第{attempt + 1}次重试...")
                # 重新查找元素
                if attempt < retry_count - 1:
                    time.sleep(1)
                    # 返回None表示需要重新查找元素
                    return None
            except Exception as e:
                logging.warning(f"点击元素失败: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
        return False

    def _safe_send_keys(self, element, text, retry_count=3):
        """安全输入文本，处理stale element错误"""
        for attempt in range(retry_count):
            try:
                # 清空并输入文本
                element.clear()
                time.sleep(0.5)
                element.send_keys(text)
                return True
            except StaleElementReferenceException:
                logging.warning(f"输入时发生stale element错误，第{attempt + 1}次重试...")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    return None  # 需要重新查找元素
            except Exception as e:
                logging.warning(f"输入文本失败: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
        return False

    def _clean_extracted_content(self, text: str) -> str:
        """清理提取的内容，移除页面元素和无关文本"""
        if not text:
            return ""
        
        # 需要过滤的无关内容模式
        noise_patterns = [
            r'Qwen3-\d+B-A\d+B\d+:\d+',  # 模型标识符
            r'加载中\.\.\.', 
            r'复制询问解释.*?(?=\n|$)',  # 页面按钮文本
            r'网页开发预览模式图像生成深度思考搜索.*?(?=\n|$)',
            r'人工智能生成的内容可能不准确。.*?(?=\n|$)',
            r'.*?复制询问解释.*?(?=\n|$)',
            r'\d{2}:\d{2}(?!\d)',  # 时间戳但不删除数学表达式
            r'(?:^|\n).*?(?:复制|询问|解释|搜索|图像生成|深度思考|网页开发|预览模式).*?(?=\n|$)',
            r'(?:^|\n)\s*[A-Z]\w*\d+-\d+[A-Z]-[A-Z]\d+[A-Z]\d+:\d+.*?(?=\n|$)',
        ]
        
        # 应用过滤模式
        cleaned_text = text
        for pattern in noise_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # 清理多余的空白
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # 多个空行变成两个
        cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)  # 移除行首行尾空白
        cleaned_text = cleaned_text.strip()
        
        # 如果清理后内容太短，可能是过度清理了，返回部分原文
        if len(cleaned_text) < 10 and len(text) > 50:
            # 尝试更温和的清理
            mild_clean = re.sub(r'Qwen3-\d+B-A\d+B.*?(?=\n|$)', '', text, flags=re.MULTILINE)
            mild_clean = re.sub(r'复制询问解释.*?(?=\n|$)', '', mild_clean, flags=re.MULTILINE)
            mild_clean = re.sub(r'\n\s*\n+', '\n', mild_clean).strip()
            return mild_clean if len(mild_clean) > 10 else text
        
        return cleaned_text

    def _extract_thinking_panel_content(self, soup: BeautifulSoup) -> str:
        """专门提取深度思考面板的内容"""
        try:
            # 通义千问的深度思考面板选择器
            thinking_selectors = [
                'div.ThinkingPanel__Body--Visible',
                'div[class*="ThinkingPanel"]',
                'div[class*="thinking-panel"]',
                'div[data-testid="thinking-panel"]',
                'div.reasoning-content',
                'div[class*="reasoning"]'
            ]
            
            for selector in thinking_selectors:
                elements = soup.select(selector)
                for element in elements:
                    if element and element.get_text():
                        content = element.get_text(separator='\n', strip=True)
                        if len(content) > 50:  # 确保有实质内容
                            return self._clean_extracted_content(content)
            
            return ""
        except Exception as e:
            self.logger.debug(f"提取思考面板内容失败: {str(e)}")
            return ""

    def _extract_main_response_content(self, soup: BeautifulSoup) -> str:
        """提取主要回复内容"""
        try:
            # 通义千问的回复内容选择器
            response_selectors = [
                'div[class*="markdown-body"]',
                'div[class*="message-content"]',
                'div[class*="response-text"]',
                'div.message-text',
                'div[data-testid="message-content"]',
                '.prose'  # Tailwind CSS 的排版类
            ]
            
            best_content = ""
            max_length = 0
            
            for selector in response_selectors:
                elements = soup.select(selector)
                for element in elements:
                    if element and element.get_text():
                        content = element.get_text(separator='\n', strip=True)
                        cleaned_content = self._clean_extracted_content(content)
                        if len(cleaned_content) > max_length and len(cleaned_content) > 20:
                            best_content = cleaned_content
                            max_length = len(cleaned_content)
            
            return best_content
        except Exception as e:
            self.logger.debug(f"提取主要回复内容失败: {str(e)}")
            return ""


def main():
    """主函数：运行基础测试"""
    import os
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    automation = QwenAutomation(config_path)
    try:
        # 初始化
        if not automation.initialize():
            print("初始化失败")
            return
        
        # 运行自动化测试
        automation.run_automation()
        
    finally:
        automation.close()


if __name__ == "__main__":
    main()