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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re


class DeepSeekAutomation:
    """DeepSeek AI 网页自动化工具"""
    
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
                logging.FileHandler('deepseek_automation.log', encoding='utf-8'),
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
        
        # 用户数据目录
        user_data_dir = self.config['browser']['user_data_dir']
        if user_data_dir:
            options.add_argument(f'--user-data-dir={os.path.abspath(user_data_dir)}')
        
        # 其他有用的选项
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 创建驱动
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 执行反检测脚本
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def start_browser(self):
        """启动浏览器"""
        self.logger.info("启动浏览器...")
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, self.config['browser']['timeout'])
        self.logger.info("浏览器启动成功")
    
    def navigate_to_deepseek(self):
        """导航到 DeepSeek AI 网站"""
        url = "https://chat.deepseek.com"
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
                "继续之前，chat.deepseek.com 需要先检查您的连接的安全性",
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
            
            # 等待页面完全加载
            time.sleep(5)
            
            # 尝试使用真实的鼠标模拟
            try:
                import pyautogui
                pyautogui_available = True
                # 配置 pyautogui
                pyautogui.FAILSAFE = False
                pyautogui.PAUSE = 0.1
            except ImportError:
                pyautogui_available = False
                self.logger.warning("pyautogui 未安装，将使用 Selenium 模拟点击")
            
            # 尝试查找并处理 Turnstile 验证组件
            max_attempts = max_wait_time
            for attempt in range(max_attempts):
                try:
                    # 查找 Cloudflare Turnstile 验证框
                    turnstile_selectors = [
                        "#TCCAL6",  # 从 HTML 中看到的特定 ID
                        "iframe[src*='turnstile']",  # Turnstile iframe
                        "iframe[src*='cloudflare']",  # Cloudflare iframe
                    ]
                    
                    verification_element = None
                    for selector in turnstile_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed():
                                    verification_element = element
                                    self.logger.info(f"找到验证元素: {selector}")
                                    break
                            if verification_element:
                                break
                        except Exception:
                            continue
                    
                    # 如果找到了验证元素，尝试与之交互
                    if verification_element:
                        if pyautogui_available:
                            # 使用 pyautogui 进行真实的鼠标点击
                            success = self._real_mouse_click(verification_element)
                            if success:
                                self.logger.info("使用真实鼠标点击完成验证")
                            else:
                                # 如果真实鼠标点击失败，回退到 Selenium
                                self._selenium_click(verification_element)
                        else:
                            # 使用改进的 Selenium 点击
                            self._selenium_click(verification_element)
                        
                        # 等待验证处理
                        time.sleep(5)
                    
                    # 检查是否验证成功（页面是否跳转或变化）
                    time.sleep(check_interval)
                    current_page_text = self.driver.page_source
                    
                    # 如果页面不再包含 Cloudflare 验证文本，说明验证成功
                    still_on_cloudflare = any(indicator in current_page_text for indicator in cloudflare_indicators)
                    
                    if not still_on_cloudflare:
                        self.logger.info("Cloudflare 验证成功，页面已跳转")
                        return True
                    
                    # 检查是否有成功提示
                    success_indicators = [
                        "验证成功",
                        "正在等待",
                        "Success",
                        "Verified",
                        "正在跳转",
                        "Redirecting"
                    ]
                    
                    verification_success = any(indicator in current_page_text for indicator in success_indicators)
                    if verification_success:
                        self.logger.info("检测到验证成功提示，等待页面跳转...")
                        # 等待页面自动跳转
                        for wait_attempt in range(20):  # 等待最多20秒
                            time.sleep(1)
                            new_page_text = self.driver.page_source
                            if not any(indicator in new_page_text for indicator in cloudflare_indicators):
                                self.logger.info("验证完成，页面已跳转")
                                return True
                        break  # 如果等待超时，跳出循环
                    
                    self.logger.info(f"验证尝试 {attempt + 1}/{max_attempts}，等待中...")
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.debug(f"验证尝试 {attempt + 1} 出错: {e}")
                    time.sleep(check_interval)
            
            # 如果达到最大尝试次数，检查是否自动通过了验证
            final_page_text = self.driver.page_source
            still_on_cloudflare = any(indicator in final_page_text for indicator in cloudflare_indicators)
            
            if not still_on_cloudflare:
                self.logger.info("Cloudflare 验证可能已自动完成")
                return True
            else:
                self.logger.warning(f"Cloudflare 验证处理超时（{max_wait_time}秒），可能需要手动处理")
                # 给用户一些时间手动完成验证
                self.logger.info("等待30秒以便手动完成验证...")
                for manual_wait in range(30):
                    time.sleep(1)
                    manual_check_text = self.driver.page_source
                    if not any(indicator in manual_check_text for indicator in cloudflare_indicators):
                        self.logger.info("检测到验证已手动完成")
                        return True
                return False
                
        except Exception as e:
            self.logger.error(f"处理 Cloudflare 验证时发生错误: {e}")
            return False
    
    def _real_mouse_click(self, element) -> bool:
        """使用真实鼠标点击元素
        
        Args:
            element: 要点击的元素
            
        Returns:
            bool: 是否成功点击
        """
        try:
            import pyautogui
            import random
            
            # 滚动到元素可见位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # 获取元素在页面中的位置和大小
            location = element.location
            size = element.size
            
            # 获取浏览器窗口信息
            window_position = self.driver.get_window_position()
            window_size = self.driver.get_window_size()
            
            # 获取浏览器内容区域相对于窗口的偏移
            # 使用 JavaScript 获取更准确的偏移量
            content_offset = self.driver.execute_script("""
                var rect = document.documentElement.getBoundingClientRect();
                return {
                    x: -rect.left,
                    y: -rect.top
                };
            """)
            
            # 获取更精确的浏览器chrome偏移（工具栏、地址栏等）
            try:
                browser_offset = self.driver.execute_script("""
                    // 获取窗口内容区域的实际偏移
                    var body = document.body;
                    var html = document.documentElement;
                    
                    // 计算viewport相对于window的偏移
                    var viewportOffset = {
                        x: window.outerWidth - window.innerWidth,
                        y: window.outerHeight - window.innerHeight
                    };
                    
                    // 获取页面滚动位置
                    var scrollX = window.pageXOffset || document.documentElement.scrollLeft;
                    var scrollY = window.pageYOffset || document.documentElement.scrollTop;
                    
                    // 获取设备像素比和缩放级别
                    var dpr = window.devicePixelRatio || 1;
                    var zoom = window.outerWidth / window.innerWidth / dpr;
                    
                    return {
                        chrome_x: Math.round(viewportOffset.x / 2),  // 通常是左右边框的一半
                        chrome_y: Math.round(viewportOffset.y * 0.85),  // 主要是顶部工具栏
                        scroll_x: scrollX,
                        scroll_y: scrollY,
                        dpr: dpr,
                        zoom: zoom,
                        inner_width: window.innerWidth,
                        inner_height: window.innerHeight,
                        outer_width: window.outerWidth,
                        outer_height: window.outerHeight
                    };
                """)
                
                self.logger.info(f"浏览器偏移信息: {browser_offset}")
                
                # 使用更精确的偏移计算，考虑DPR和滚动
                chrome_offset_x = browser_offset['chrome_x']
                chrome_offset_y = browser_offset['chrome_y']
                
                # 如果DPR不是1，可能需要调整
                dpr = browser_offset['dpr']
                if dpr != 1:
                    self.logger.info(f"检测到设备像素比: {dpr}")
                    # 对于高DPI显示器，坐标可能需要调整
                    # 但这通常由操作系统自动处理，所以先不调整
                
                # 更新内容偏移
                content_offset['x'] += chrome_offset_x
                content_offset['y'] += chrome_offset_y
                
                # 记录滚动位置（如果需要的话）
                scroll_x = browser_offset['scroll_x']
                scroll_y = browser_offset['scroll_y']
                if scroll_x != 0 or scroll_y != 0:
                    self.logger.info(f"页面滚动位置: ({scroll_x}, {scroll_y})")
                
            except Exception as e:
                self.logger.debug(f"无法获取精确的浏览器偏移，使用默认值: {e}")
                # 使用经验值作为后备
                content_offset['x'] += 8   # 左边框
                content_offset['y'] += 85  # 顶部工具栏
            
            # 计算元素在屏幕上的绝对位置
            # 考虑窗口位置、内容偏移、滚动位置
            element_center_x = location['x'] + size['width'] // 2
            element_center_y = location['y'] + size['height'] // 2
            
            # 方法1: 使用传统计算
            screen_x_traditional = window_position['x'] + content_offset['x'] + element_center_x
            screen_y_traditional = window_position['y'] + content_offset['y'] + element_center_y
            
            # 方法2: 使用JavaScript获取更精确的坐标
            try:
                js_coords = self.driver.execute_script("""
                    var element = arguments[0];
                    var rect = element.getBoundingClientRect();
                    
                    // 获取元素中心点相对于viewport的坐标
                    var centerX = rect.left + rect.width / 2;
                    var centerY = rect.top + rect.height / 2;
                    
                    // 获取窗口的实际偏移（考虑浏览器工具栏等）
                    var windowOffset = {
                        x: window.screenX || window.screenLeft || 0,
                        y: window.screenY || window.screenTop || 0
                    };
                    
                    // 计算最终屏幕坐标
                    var screenX = windowOffset.x + centerX;
                    var screenY = windowOffset.y + centerY;
                    
                    return {
                        viewport_x: centerX,
                        viewport_y: centerY,
                        window_offset_x: windowOffset.x,
                        window_offset_y: windowOffset.y,
                        screen_x: screenX,
                        screen_y: screenY,
                        rect: {
                            left: rect.left,
                            top: rect.top,
                            width: rect.width,
                            height: rect.height
                        }
                    };
                """, element)
                
                self.logger.info(f"JavaScript坐标信息: {js_coords}")
                
                # 使用JavaScript计算的坐标
                screen_x = js_coords['screen_x']
                screen_y = js_coords['screen_y']
                
                self.logger.info(f"使用JavaScript计算的屏幕坐标: ({screen_x}, {screen_y})")
                
            except Exception as e:
                self.logger.warning(f"JavaScript坐标计算失败，使用传统方法: {e}")
                screen_x = screen_x_traditional
                screen_y = screen_y_traditional
            
            # 添加小范围随机偏移以模拟人类行为
            random_offset_x = random.randint(-3, 3)
            random_offset_y = random.randint(-3, 3)
            
            final_x = screen_x + random_offset_x
            final_y = screen_y + random_offset_y
            
            self.logger.info(f"元素位置: ({location['x']}, {location['y']})")
            self.logger.info(f"元素大小: {size['width']}x{size['height']}")
            self.logger.info(f"窗口位置: ({window_position['x']}, {window_position['y']})")
            self.logger.info(f"内容偏移: ({content_offset['x']}, {content_offset['y']})")
            self.logger.info(f"传统计算屏幕坐标: ({screen_x_traditional}, {screen_y_traditional})")
            self.logger.info(f"最终使用屏幕坐标: ({screen_x}, {screen_y})")
            self.logger.info(f"最终点击坐标: ({final_x}, {final_y})")
            
            # 验证坐标是否合理（考虑多屏幕环境）
            try:
                # pyautogui没有getAllDisplays方法，使用其他方式检测多屏幕
                screen_width, screen_height = pyautogui.size()
                
                # 多重检测方法确定是否为多屏幕环境
                is_multi_monitor = False
                
                # 方法1: 检查窗口位置是否为负数（左侧或上方屏幕）
                if window_position['x'] < 0 or window_position['y'] < 0:
                    is_multi_monitor = True
                    self.logger.info("检测到多屏幕（窗口位置为负坐标）")
                
                # 方法2: 检查窗口位置是否超出主屏幕范围
                elif (window_position['x'] >= screen_width or 
                      window_position['y'] >= screen_height):
                    is_multi_monitor = True
                    self.logger.info("检测到多屏幕（窗口位置超出主屏幕）")
                
                # 方法3: 尝试使用tkinter获取总屏幕尺寸
                if not is_multi_monitor:
                    try:
                        import tkinter as tk
                        root = tk.Tk()
                        
                        # 获取所有屏幕的总宽度和高度
                        total_width = root.winfo_screenwidth()
                        total_height = root.winfo_screenheight()
                        
                        root.destroy()
                        
                        # 检查总尺寸是否大于主屏幕尺寸
                        if total_width > screen_width or total_height > screen_height:
                            is_multi_monitor = True
                            self.logger.info(f"检测到多屏幕（总尺寸vs主屏幕: {total_width}x{total_height} vs {screen_width}x{screen_height}）")
                        
                    except ImportError:
                        self.logger.debug("无法导入tkinter")
                    except Exception as e:
                        self.logger.debug(f"tkinter检测失败: {e}")
                
                # 根据检测结果设置坐标范围
                if is_multi_monitor:
                    self.logger.info("确认为多屏幕环境")
                    # 为多屏幕设置扩展范围
                    min_x = -screen_width * 2   # 左侧最多2个屏幕
                    max_x = screen_width * 3    # 右侧最多2个屏幕  
                    min_y = -screen_height      # 上方最多1个屏幕
                    max_y = screen_height * 2   # 下方最多1个屏幕
                    
                    self.logger.info(f"多屏幕坐标范围: X({min_x} 到 {max_x}), Y({min_y} 到 {max_y})")
                else:
                    self.logger.info("检测为单屏幕环境")
                    # 但即使是单屏幕，也允许一定的负坐标误差
                    min_x, max_x = -200, screen_width + 200   # 允许200像素误差
                    min_y, max_y = -200, screen_height + 200
                    self.logger.info(f"单屏幕坐标范围（含误差）: X({min_x} 到 {max_x}), Y({min_y} 到 {max_y})")
                
                # 验证坐标是否在计算的范围内
                if not (min_x <= final_x <= max_x and min_y <= final_y <= max_y):
                    self.logger.warning(f"坐标超出预期范围: ({final_x}, {final_y})")
                    self.logger.warning(f"允许范围: X({min_x} 到 {max_x}), Y({min_y} 到 {max_y})")
                    
                    # 检查坐标是否完全不合理（可能是计算错误）
                    if (abs(final_x) > screen_width * 5 or abs(final_y) > screen_height * 3):
                        self.logger.error("坐标严重异常，可能是计算错误")
                        return False
                    
                    # 对于轻微超出范围的坐标，尝试修正
                    corrected_x = max(min_x, min(final_x, max_x))
                    corrected_y = max(min_y, min(final_y, max_y))
                    
                    # 如果是多屏幕环境或修正幅度不大，则使用修正后的坐标
                    if is_multi_monitor or (abs(corrected_x - final_x) < 100 and abs(corrected_y - final_y) < 100):
                        self.logger.info(f"坐标修正: ({final_x}, {final_y}) -> ({corrected_x}, {corrected_y})")
                        final_x, final_y = corrected_x, corrected_y
                    else:
                        self.logger.info("坐标超出范围但在多屏幕环境下可能有效，保持原坐标")
                else:
                    self.logger.info("坐标在有效范围内")
                    
            except Exception as e:
                self.logger.warning(f"坐标验证失败，继续执行: {e}")
                # 如果验证失败，只检查极端异常的坐标
                screen_width, screen_height = pyautogui.size()
                if (abs(final_x) > screen_width * 5 or abs(final_y) > screen_height * 3):
                    self.logger.error("坐标异常，停止执行")
                    return False
            
            # 获取当前鼠标位置
            current_x, current_y = pyautogui.position()
            
            # 计算移动距离
            distance = ((final_x - current_x) ** 2 + (final_y - current_y) ** 2) ** 0.5
            
            # 根据距离调整移动时间和步数
            if distance < 100:
                steps = random.randint(2, 4)
                base_duration = 0.1
            elif distance < 300:
                steps = random.randint(3, 6)
                base_duration = 0.2
            else:
                steps = random.randint(5, 8)
                base_duration = 0.3
            
            # 分步移动到目标位置，模拟人类鼠标移动
            for i in range(steps):
                progress = (i + 1) / steps
                # 使用缓动函数使移动更自然
                eased_progress = progress * progress * (3 - 2 * progress)  # smooth step
                
                intermediate_x = current_x + (final_x - current_x) * eased_progress
                intermediate_y = current_y + (final_y - current_y) * eased_progress
                
                # 添加微小的随机抖动
                jitter_x = random.uniform(-1, 1)
                jitter_y = random.uniform(-1, 1)
                
                move_x = intermediate_x + jitter_x
                move_y = intermediate_y + jitter_y
                
                duration = base_duration + random.uniform(-0.05, 0.05)
                pyautogui.moveTo(move_x, move_y, duration=duration)
                time.sleep(random.uniform(0.01, 0.03))
            
            # 在目标位置稍作停顿
            time.sleep(random.uniform(0.2, 0.5))
            
            # 执行点击
            pyautogui.click(final_x, final_y)
            self.logger.info("真实鼠标点击执行完成")
            
            # 点击后稍作停顿
            time.sleep(random.uniform(0.3, 0.7))
            
            return True
            
        except Exception as e:
            self.logger.error(f"真实鼠标点击失败: {e}")
            import traceback
            self.logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    def _selenium_click(self, element):
        """使用改进的 Selenium 点击
        
        Args:
            element: 要点击的元素
        """
        try:
            # 对于 iframe，需要切换到 iframe 内部
            if element.tag_name == 'iframe':
                try:
                    self.driver.switch_to.frame(element)
                    time.sleep(2)
                    
                    # 在 iframe 内查找复选框或点击区域
                    iframe_selectors = [
                        "input[type='checkbox']",
                        "label",
                        "div[role='checkbox']",
                        "div[role='button']",
                        ".checkbox",
                        "[tabindex='0']",
                        "span",
                        "div"
                    ]
                    
                    clicked = False
                    for iframe_selector in iframe_selectors:
                        try:
                            iframe_elements = self.driver.find_elements(By.CSS_SELECTOR, iframe_selector)
                            for iframe_element in iframe_elements:
                                if iframe_element.is_displayed():
                                    # 使用多种点击方式
                                    self._try_multiple_click_methods(iframe_element)
                                    self.logger.info(f"点击了 iframe 内的验证元素: {iframe_selector}")
                                    clicked = True
                                    break
                        except Exception as e:
                            self.logger.debug(f"尝试点击 {iframe_selector} 失败: {e}")
                            continue
                        if clicked:
                            break
                    
                    # 切换回主页面
                    self.driver.switch_to.default_content()
                except Exception as e:
                    self.logger.debug(f"处理 iframe 验证时出错: {e}")
                    self.driver.switch_to.default_content()
            else:
                # 直接点击验证元素
                self._try_multiple_click_methods(element)
                self.logger.info(f"点击了验证元素: {element.tag_name}")
                
        except Exception as e:
            self.logger.error(f"Selenium 点击失败: {e}")
    
    def _try_multiple_click_methods(self, element):
        """尝试多种点击方法
        
        Args:
            element: 要点击的元素
        """
        from selenium.webdriver.common.action_chains import ActionChains
        import random
        
        methods = [
            # 方法1: ActionChains 与随机行为
            lambda: self._action_chains_click_with_behavior(element),
            # 方法2: JavaScript 点击
            lambda: self.driver.execute_script("arguments[0].click();", element),
            # 方法3: 原生点击
            lambda: element.click(),
            # 方法4: ActionChains 基本点击
            lambda: ActionChains(self.driver).click(element).perform()
        ]
        
        # 随机选择一种方法
        method = random.choice(methods)
        try:
            method()
        except Exception:
            # 如果失败，尝试其他方法
            for backup_method in methods:
                try:
                    backup_method()
                    break
                except Exception:
                    continue
    
    def _action_chains_click_with_behavior(self, element):
        """使用 ActionChains 进行带人类行为的点击
        
        Args:
            element: 要点击的元素
        """
        from selenium.webdriver.common.action_chains import ActionChains
        import random
        
        actions = ActionChains(self.driver)
        
        # 模拟人类行为：先随机移动鼠标
        actions.move_by_offset(random.randint(-10, 10), random.randint(-10, 10))
        actions.pause(random.uniform(0.1, 0.3))
        
        # 移动到元素
        actions.move_to_element(element)
        actions.pause(random.uniform(0.2, 0.6))
        
        # 稍微偏移一点，模拟人类不精确的点击
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        actions.move_to_element_with_offset(element, offset_x, offset_y)
        actions.pause(random.uniform(0.1, 0.4))
        
        # 执行点击
        actions.click()
        actions.pause(random.uniform(0.1, 0.3))
        
        # 执行所有动作
        actions.perform()
        
        # 点击后停顿
        time.sleep(random.uniform(0.2, 0.5))
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            # 检查是否存在聊天输入框或用户头像等登录后的元素
            login_indicators = [
                "#chat-input",  # 聊天输入框
                "textarea[placeholder*='DeepSeek']",
            ]
            
            for selector in login_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.logger.info("检测到已登录状态")
                        return True
                except NoSuchElementException:
                    continue
                    
            # 如果没有找到登录指示器，检查是否还在登录页面
            login_page_indicators = [
                "input.ds-input__input[type='text']",  # 邮箱输入框
                "input.ds-input__input[type='password']",  # 密码输入框
                ".ds-button.ds-sign-up-form__register-button",  # 登录按钮
                "input[placeholder*='邮箱']",
                "input[placeholder*='密码']"
            ]
            
            for selector in login_page_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.logger.info("检测到登录页面，未登录")
                        return False
                except NoSuchElementException:
                    continue
            
            self.logger.info("无法确定登录状态")
            return False
            
        except Exception as e:
            self.logger.error(f"检查登录状态时发生错误: {e}")
            return False
    
    def login(self) -> bool:
        """登录到 DeepSeek AI
        
        Returns:
            bool: 登录是否成功
        """
        if self.is_logged_in():
            self.logger.info("已经处于登录状态")
            return True
        
        self.logger.info("开始登录流程...")
        
        try:
            # 查找登录按钮或链接 - 根据实际 HTML 结构
            login_button = None
            css_selectors = [
                ".ds-button.ds-sign-up-form__register-button",  # DeepSeek 特定的登录按钮
                ".ds-button[role='button']",  # DeepSeek 按钮样式
                "div[role='button']",  # 通用的 div 按钮
                "button[data-testid='login']",
                "a[href*='login']",
                ".login-button",
                "[class*='login']",
                "button[class*='login']",
                "a[class*='login']"
            ]
            
            for selector in css_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_button.is_displayed() and login_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            # 如果 CSS 选择器没找到，尝试 XPath
            if not login_button:
                xpath_selectors = [
                    "//div[@role='button' and contains(text(), '登录')]",  # DeepSeek 登录按钮
                    "//div[contains(@class, 'ds-button') and contains(text(), '登录')]",
                    "//button[contains(text(), '登录')]",
                    "//button[contains(text(), 'Login')]",
                    "//a[contains(text(), '登录')]",
                    "//a[contains(text(), 'Login')]",
                    "//button[contains(@class, 'login')]",
                    "//a[contains(@class, 'login')]"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        login_button = self.driver.find_element(By.XPATH, xpath)
                        if login_button.is_displayed() and login_button.is_enabled():
                            break
                    except NoSuchElementException:
                        continue
            
            if login_button:
                login_button.click()
                self.logger.info("点击登录按钮")
                time.sleep(1)
            else:
                self.logger.info("未找到登录按钮，可能已在登录页面")
            
            # 输入邮箱 - 根据 DeepSeek 实际结构
            email_selectors = [
                "input.ds-input__input[type='text']",  # DeepSeek 特定的邮箱输入框
                "input.ds-input__input[placeholder*='邮箱']",
                "input.ds-input__input[placeholder*='手机号']",
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='邮箱']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']",
                "input[placeholder*='手机号/邮箱']",
                "input[id*='email']",
                "input[class*='email']"
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if email_input:
                email_input.clear()
                email_input.send_keys(self.config['login']['email'])
                self.logger.info("输入邮箱地址")
                time.sleep(1)
            else:
                self.logger.error("未找到邮箱输入框")
                return False
            
            # 输入密码 - 根据 DeepSeek 实际结构
            password_selectors = [
                "input.ds-input__input[type='password']",  # DeepSeek 特定的密码输入框
                "input[type='password']",
                "input[name='password']",
                "input[placeholder*='密码']",
                "input[placeholder*='password']",
                "input[placeholder*='Password']",
                "input[placeholder*='请输入密码']",
                "input[id*='password']",
                "input[class*='password']"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if password_input:
                password_input.clear()
                password_input.send_keys(self.config['login']['password'])
                self.logger.info("输入密码")
                time.sleep(1)
            else:
                self.logger.error("未找到密码输入框")
                return False
            
            # 点击登录提交按钮 - 根据 DeepSeek 实际结构
            submit_button = None
            css_submit_selectors = [
                ".ds-button.ds-sign-up-form__register-button",  # DeepSeek 登录按钮
                ".ds-button[role='button']",  # DeepSeek 按钮样式
                "div[role='button'][class*='ds-button']",
                "button[type='submit']",
                "input[type='submit']",
                ".submit-button",
                "button[class*='submit']",
                "button[id*='submit']"
            ]
            
            for selector in css_submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button.is_displayed() and submit_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            # 如果没找到，尝试 XPath
            if not submit_button:
                xpath_submit_selectors = [
                    "//div[@role='button' and contains(text(), '登录')]",
                    "//div[contains(@class, 'ds-button') and contains(text(), '登录')]",
                    "//button[contains(text(), '登录')]",
                    "//button[contains(text(), 'Login')]",
                    "//button[contains(text(), '提交')]",
                    "//button[contains(text(), 'Submit')]",
                    "//input[@value='登录']",
                    "//input[@value='Login']"
                ]
                
                for xpath in xpath_submit_selectors:
                    try:
                        submit_button = self.driver.find_element(By.XPATH, xpath)
                        if submit_button.is_displayed() and submit_button.is_enabled():
                            break
                    except NoSuchElementException:
                        continue
            
            if submit_button:
                submit_button.click()
                self.logger.info("点击登录提交按钮")
                time.sleep(1)
            else:
                self.logger.error("未找到登录提交按钮")
                return False
            
            # 等待登录完成
            if self.wait_for_login():
                self.logger.info("登录成功")
                return True
            else:
                self.logger.error("登录失败")
                return False
                
        except Exception as e:
            self.logger.error(f"登录过程中发生错误: {e}")
            return False
    
    def wait_for_login(self, timeout: int = 30) -> bool:
        """等待登录完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_logged_in():
                return True
            time.sleep(1)
        return False
    
    def send_message(self, message: str) -> bool:
        """发送消息
        
        Args:
            message: 要发送的消息
            
        Returns:
            bool: 发送是否成功
        """
        try:
            self.logger.info(f"发送消息: {message}")
            
            # 在发送消息前尝试启用深度思考模式
            if not self.enable_deep_thinking():
                self.logger.warning("深度思考模式启用失败，但继续发送消息")
            
            # 查找输入框 - 根据常见的聊天界面结构
            input_selectors = [
                "textarea",  # 最常见的消息输入框
                "textarea[placeholder*='输入']",
                "textarea[placeholder*='message']",
                "textarea[placeholder*='Message']",
                "input[type='text'][placeholder*='输入']",
                "input[type='text'][placeholder*='message']",
                "[data-testid='chat-input']",
                ".chat-input",
                "[contenteditable='true']",
                "[placeholder*='输入']",
                "[placeholder*='message']",
                "[placeholder*='Message']",
                "[class*='input']",
                "[id*='input']",
                "input[type='text']"  # 作为最后的备选
            ]
            
            message_input = None
            for selector in input_selectors:
                try:
                    message_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not message_input:
                self.logger.error("未找到消息输入框")
                return False
            
            # 清空并输入消息
            message_input.clear()
            time.sleep(0.5)
            message_input.send_keys(message)
            time.sleep(1)
            
            # 查找发送按钮 - 先尝试 CSS 选择器
            send_button = None
            css_send_selectors = [
                "button[type='submit']",
                "[data-testid='send-button']",
                ".send-button",
                "button[aria-label*='发送']",
                "button[title*='发送']",
                "button[aria-label*='Send']",
                "button[title*='Send']",
                "button[class*='send']",
                "button[id*='send']",
                "button svg",  # 可能只有图标的发送按钮
                "button[class*='submit']"
            ]
            
            for selector in css_send_selectors:
                try:
                    send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if send_button.is_enabled() and send_button.is_displayed():
                        break
                except NoSuchElementException:
                    continue
            
            # 如果 CSS 选择器没找到，尝试 XPath
            if not send_button:
                xpath_send_selectors = [
                    "//button[contains(text(), '发送')]",
                    "//button[contains(text(), 'Send')]",
                    "//button[contains(text(), '提交')]",
                    "//button[contains(@aria-label, '发送')]",
                    "//button[contains(@aria-label, 'Send')]",
                    "//button[contains(@class, 'send')]",
                    "//button[contains(@title, '发送')]",
                    "//button[contains(@title, 'Send')]",
                    "//button[.//*[name()='svg']]",  # 包含 SVG 图标的按钮
                    "//div[@role='button' and contains(@class, 'send')]"
                ]
                
                for xpath in xpath_send_selectors:
                    try:
                        send_button = self.driver.find_element(By.XPATH, xpath)
                        if send_button.is_enabled() and send_button.is_displayed():
                            break
                    except NoSuchElementException:
                        continue
            
            if send_button:
                send_button.click()
                self.logger.info("消息发送成功")
                time.sleep(1)  # 等待消息发送
                return True
            else:
                # 尝试按回车键发送
                from selenium.webdriver.common.keys import Keys
                message_input.send_keys(Keys.RETURN)
                self.logger.info("通过回车键发送消息")
                time.sleep(1)  # 等待消息发送
                return True
                
        except Exception as e:
            self.logger.error(f"发送消息时发生错误: {e}")
            return False
    
    def wait_for_response(self) -> Optional[Dict[str, str]]:
        """等待 AI 回复并解析深度思考过程和正式回答
        
        Returns:
            Dict[str, str]: 包含深度思考过程和正式回答的字典，如果超时返回 None
            格式: {
                'deep_thinking': '深度思考过程内容',
                'formal_answer': '正式回答内容',
                'thinking_time': '思考用时',
                'page_structure': '页面结构信息'
            }
        """
        self.logger.info("等待 AI 回复...")
        
        try:
            start_time = time.time()
            max_wait_time = self.config.get('automation', {}).get('response_timeout', 120)
            
            # 首先等待AI开始回复（aria-disabled变为false）
            ai_started_replying = False
            
            for _ in range(10):  # 等待AI开始回复，最多10秒
                try:
                    # 查找回复状态指示器
                    status_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        "div[role='button'][aria-disabled]")
                    
                    for element in status_elements:
                        aria_disabled = element.get_attribute("aria-disabled")
                        if aria_disabled == "false":
                            self.logger.info("检测到AI开始回复 (aria-disabled=false)")
                            ai_started_replying = True
                            break
                    
                    if ai_started_replying:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"检查回复状态时出错: {e}")
                
                time.sleep(1)
            
            if not ai_started_replying:
                self.logger.warning("未检测到AI开始回复，尝试继续等待...")
            
            # 等待AI完成回复（aria-disabled变为true）
            while time.time() - start_time < max_wait_time:
                try:
                    # 检查回复状态
                    status_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        "div[role='button'][aria-disabled]")
                    
                    reply_completed = False
                    for element in status_elements:
                        aria_disabled = element.get_attribute("aria-disabled")
                        if aria_disabled == "true":
                            self.logger.info("检测到AI回复完成 (aria-disabled=true)")
                            reply_completed = True
                            break
                    
                    if reply_completed:
                        # 回复完成，等待一下确保内容完全加载
                        time.sleep(3)
                        
                        # 使用BeautifulSoup解析页面结构
                        return self._parse_response_with_bs4()
                
                except Exception as e:
                    self.logger.debug(f"检查回复状态时出错: {e}")
                
                time.sleep(2)  # 每2秒检查一次
            
            # 超时情况下也尝试解析
            self.logger.warning(f"等待超时（{max_wait_time}秒），尝试解析当前内容...")
            return self._parse_response_with_bs4()
                            
        except Exception as e:
            self.logger.error(f"等待回复时发生错误: {e}")
            return None

    def _parse_response_with_bs4(self) -> Optional[Dict[str, str]]:
        """使用BeautifulSoup解析AI回复内容
        
        Returns:
            Dict[str, str]: 解析结果字典
        """
        try:
            self.logger.info("开始使用BeautifulSoup解析页面结构...")
            
            # 获取页面源码
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 解析页面层级结构
            structure_info = self._analyze_page_structure(soup)
            self.logger.info(f"页面结构解析完成: {structure_info}")
            
            # 根据解析到的结构提取内容
            result = self._extract_content_by_structure(soup, structure_info)
            
            if result:
                result['page_structure'] = structure_info
                self.logger.info("成功提取AI回复内容")
                return result
            else:
                self.logger.warning("未能提取到有效内容")
                return None
                
        except Exception as e:
            self.logger.error(f"BeautifulSoup解析失败: {e}")
            import traceback
            self.logger.debug(f"详细错误: {traceback.format_exc()}")
            return None

    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, str]:
        """分析页面结构，获取动态类名
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            Dict[str, str]: 包含各层级动态类名的字典
        """
        structure = {}
        
        try:
            # 1. 找到根容器
            root = soup.find('div', id='root')
            if root:
                structure['root'] = 'div#root'
                self.logger.debug("找到根容器: div#root")
                
                # 2. 找到主题容器
                theme_container = root.find('div', class_=lambda x: x and 'ds-theme' in x)
                if theme_container:
                    theme_classes = ' '.join(theme_container.get('class', []))
                    structure['theme_container'] = f"div.{theme_classes.replace(' ', '.')}"
                    self.logger.debug(f"找到主题容器: {structure['theme_container']}")
                    
                    # 3. 遍历查找聊天容器
                    chat_containers = theme_container.find_all('div', recursive=True)
                    
                    for container in chat_containers:
                        classes = container.get('class', [])
                        if not classes:
                                continue
                        
                        class_str = ' '.join(classes)
                        
                        # 查找滚动容器（通常包含scrollable类或类似特征）
                        if any(keyword in class_str for keyword in ['scroll', 'chat', 'message']):
                            # 检查是否包含消息内容
                            if self._contains_message_content(container):
                                structure['scrollable_container'] = f"div.{class_str.replace(' ', '.')}"
                                self.logger.debug(f"找到滚动容器: {structure['scrollable_container']}")
                                
                                # 4. 在滚动容器内查找消息容器
                                message_containers = container.find_all('div', recursive=True)
                                structure.update(self._find_message_containers(message_containers))
                                break
            
            # 5. 查找特定的内容容器
            self._find_content_containers(soup, structure)
                
        except Exception as e:
            self.logger.error(f"分析页面结构时出错: {e}")
        
        return structure

    def _contains_message_content(self, container) -> bool:
        """检查容器是否包含消息内容
        
        Args:
            container: BeautifulSoup元素
            
        Returns:
            bool: 是否包含消息内容
        """
        try:
            # 查找可能的消息指示器
            text_content = container.get_text(strip=True)
            
            # 检查是否包含常见的消息相关文本
            message_indicators = [
                '深度思考', '思考', 'thinking', '回答', '回复',
                'markdown', 'message', 'chat', '用时'
            ]
            
            return any(indicator in text_content.lower() for indicator in message_indicators)
            
        except Exception:
            return False

    def _find_message_containers(self, containers: list) -> Dict[str, str]:
        """在容器列表中查找消息相关的容器
        
        Args:
            containers: 容器元素列表
            
        Returns:
            Dict[str, str]: 消息容器的类名映射
        """
        result = {}
        
        try:
            for container in containers:
                classes = container.get('class', [])
                if not classes:
                    continue
                
                class_str = ' '.join(classes)
                text_content = container.get_text(strip=True)
                
                # 查找深度思考容器
                if ('深度思考' in text_content or '思考' in text_content) and len(text_content) > 20:
                    # 向上查找父容器
                    parent = container.parent
                    while parent and parent.name == 'div':
                        parent_classes = parent.get('class', [])
                        if parent_classes:
                            parent_class_str = ' '.join(parent_classes)
                            result['deep_thinking_container'] = f"div.{parent_class_str.replace(' ', '.')}"
                            self.logger.debug(f"找到深度思考容器: {result['deep_thinking_container']}")
                            break
                        parent = parent.parent
                
                # 查找包含markdown的容器（正式回答）
                if 'ds-markdown' in class_str:
                    result['formal_answer_container'] = f"div.{class_str.replace(' ', '.')}"
                    self.logger.debug(f"找到正式回答容器: {result['formal_answer_container']}")
                
                # 查找AI消息容器
                if len(text_content) > 50 and any(keyword in text_content for keyword in ['思考', '回答', '根据']):
                    # 查找最近的有意义的父容器
                    parent = container.parent
                    level = 0
                    while parent and parent.name == 'div' and level < 3:
                        parent_classes = parent.get('class', [])
                        if parent_classes and len(parent_classes) >= 2:
                            parent_class_str = ' '.join(parent_classes)
                            if 'ai_message_container' not in result:
                                result['ai_message_container'] = f"div.{parent_class_str.replace(' ', '.')}"
                                self.logger.debug(f"找到AI消息容器: {result['ai_message_container']}")
                                break
                        parent = parent.parent
                        level += 1
                            
        except Exception as e:
            self.logger.error(f"查找消息容器时出错: {e}")
        
        return result

    def _find_content_containers(self, soup: BeautifulSoup, structure: Dict[str, str]):
        """查找特定的内容容器
        
        Args:
            soup: BeautifulSoup对象
            structure: 结构字典（会被修改）
        """
        try:
            # 查找所有可能包含深度思考的元素
            thinking_elements = soup.find_all(['div', 'p'], string=lambda text: text and '深度思考' in text)
            
            for element in thinking_elements:
                # 向上查找包含完整思考过程的容器
                parent = element.parent
                level = 0
                while parent and level < 5:
                    if parent.name == 'div':
                        classes = parent.get('class', [])
                        if classes:
                            class_str = ' '.join(classes)
                            text_content = parent.get_text(strip=True)
                            
                            # 如果包含完整的思考内容（长度较长）
                            if len(text_content) > 100 and 'thinking_content_container' not in structure:
                                structure['thinking_content_container'] = f"div.{class_str.replace(' ', '.')}"
                                self.logger.debug(f"找到思考内容容器: {structure['thinking_content_container']}")
                                break
                    
                    parent = parent.parent
                    level += 1
            
            # 查找markdown段落容器
            markdown_paragraphs = soup.find_all('p', class_=lambda x: x and 'markdown' in ' '.join(x))
            if markdown_paragraphs:
                first_p = markdown_paragraphs[0]
                classes = first_p.get('class', [])
                if classes:
                    class_str = ' '.join(classes)
                    structure['markdown_paragraph'] = f"p.{class_str.replace(' ', '.')}"
                    self.logger.debug(f"找到markdown段落: {structure['markdown_paragraph']}")
            
        except Exception as e:
            self.logger.error(f"查找内容容器时出错: {e}")

    def _extract_content_by_structure(self, soup: BeautifulSoup, structure: Dict[str, str]) -> Optional[Dict[str, str]]:
        """根据解析到的结构提取内容
        
        Args:
            soup: BeautifulSoup对象
            structure: 页面结构信息
            
        Returns:
            Dict[str, str]: 提取的内容
        """
        result = {
            'deep_thinking': '',
            'formal_answer': '',
            'thinking_time': '',
            'extracted_structure': structure
        }
        
        try:
            # 1. 提取深度思考内容
            deep_thinking = self._extract_deep_thinking(soup, structure)
            if deep_thinking:
                result['deep_thinking'] = deep_thinking['content']
                result['thinking_time'] = deep_thinking.get('time', '')
            
            # 2. 提取正式回答
            formal_answer = self._extract_formal_answer(soup, structure)
            if formal_answer:
                result['formal_answer'] = formal_answer
            
            # 3. 如果没有通过结构提取到内容，尝试通用方法
            if not result['deep_thinking'] and not result['formal_answer']:
                self.logger.warning("结构化提取失败，尝试通用方法...")
                fallback_result = self._extract_content_fallback(soup)
                if fallback_result:
                    result.update(fallback_result)
            
            return result if (result['deep_thinking'] or result['formal_answer']) else None
            
        except Exception as e:
            self.logger.error(f"提取内容时出错: {e}")
            return None
    
    def _extract_deep_thinking(self, soup: BeautifulSoup, structure: Dict[str, str]) -> Optional[Dict[str, str]]:
        """提取深度思考内容
        
        Args:
            soup: BeautifulSoup对象
            structure: 页面结构信息
            
        Returns:
            Dict[str, str]: 深度思考内容和用时
        """
        try:
            thinking_content = ""
            thinking_time = ""
            
            self.logger.debug("开始从根容器按层级提取深度思考内容...")
            
            # 方法1：从根容器开始按层级查找深度思考内容
            root = soup.find('div', id='root')
            if not root:
                root = soup.find('div', class_=lambda x: x and 'ds-theme' in x)
            
            if root:
                self.logger.debug("找到根容器，开始层级查找...")
                
                # 查找所有可能的AI消息容器
                ai_message_containers = self._find_ai_message_containers(root)
                self.logger.debug(f"找到 {len(ai_message_containers)} 个AI消息容器")
                
                # 优先尝试固定位置的容器（第11个，索引10）
                target_container_index = 10  # 从0开始数的第10个
                
                if len(ai_message_containers) > target_container_index:
                    target_container = ai_message_containers[target_container_index]
                    self.logger.debug(f"尝试从固定位置容器（索引{target_container_index}）提取深度思考内容")
                    
                    # 检查这个容器是否包含深度思考内容
                    container_text = target_container.get_text(strip=True)
                    
                    # 如果包含深度思考标识且内容较长，直接使用这个容器
                    if ('已深度思考' in container_text or '用时' in container_text) and len(container_text) > 100:
                        # 提取思考时间
                        thinking_time = self._extract_thinking_time_from_section(target_container)
                        
                        # 提取思考内容
                        thinking_content = self._extract_pure_thinking_content(target_container)
                        
                        if thinking_content:
                            self.logger.debug(f"从固定位置容器成功提取思考内容: {len(thinking_content)}字符")
                        else:
                            self.logger.debug("固定位置容器未能提取到有效内容，尝试其他方法")
                    else:
                        self.logger.debug("固定位置容器不包含深度思考内容")
                else:
                    self.logger.debug(f"AI消息容器数量不足，无法访问索引{target_container_index}")
                
            if thinking_content or thinking_time:
                return {
                    'content': thinking_content,
                    'time': thinking_time
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取深度思考内容时出错: {e}")
            return None
    
    def _extract_pure_thinking_content(self, container) -> str:
        """从固定位置容器提取纯净的深度思考内容
        
        Args:
            container: 目标容器
            
        Returns:
            str: 思考内容
        """
        try:
            container_text = container.get_text(strip=True)
            cleaned_text = re.sub(r'^已深度思考.*?秒\）?', '', container_text, flags=re.MULTILINE).strip()
            
            if len(cleaned_text) > 1:
                self.logger.debug(f"从固定容器提取到纯净思考内容: {len(cleaned_text)}字符")
                return cleaned_text
            return ""
        
        except Exception as e:
            self.logger.debug(f"从固定容器提取内容时出错: {e}")
            return ""

    def _find_ai_message_containers(self, root) -> list:
        """在根容器中查找AI消息容器
        
        Args:
            root: 根容器元素
            
        Returns:
            list: AI消息容器列表
        """
        containers = []
        
        try:
            # 查找所有可能包含AI消息的div
            all_divs = root.find_all('div', recursive=True)
            
            for div in all_divs:
                # 检查是否包含AI头像和消息内容的特征
                if self._is_ai_message_container(div):
                    containers.append(div)
                    self.logger.debug(f"找到AI消息容器")
            
        except Exception as e:
            self.logger.debug(f"查找AI消息容器时出错: {e}")
        
        return containers

    def _is_ai_message_container(self, div) -> bool:
        """判断div是否是AI消息容器
        
        Args:
            div: 要检查的div元素
            
        Returns:
            bool: 是否是AI消息容器
        """
        try:
            # 检查是否包含AI头像（SVG图标）
            has_ai_avatar = False
            svg_elements = div.find_all('svg', recursive=True)
            for svg in svg_elements:
                # 检查SVG的路径或viewBox，AI头像通常有特定的图形特征
                if svg.get('viewBox') == '0 0 30 30' or 'path' in str(svg):
                    has_ai_avatar = True
                    break
            
            # 检查是否包含深度思考相关文本
            text_content = div.get_text()
            has_thinking_text = any(keyword in text_content for keyword in [
                '深度思考', '已深度思考', '用时', '秒'
            ])
            
            # 检查是否包含markdown内容（正式回答）
            has_markdown = bool(div.find('div', class_=lambda x: x and 'ds-markdown' in x))
            
            # AI消息容器应该同时包含这些特征
            return has_ai_avatar and (has_thinking_text or has_markdown)
            
        except Exception as e:
            self.logger.debug(f"检查AI消息容器时出错: {e}")
            return False


    def _extract_thinking_time_from_section(self, section) -> str:
        """从深度思考部分提取思考时间
        
        Args:
            section: 深度思考部分
            
        Returns:
            str: 思考时间
        """
        try:
            text = section.get_text()
            
            # 匹配 "已深度思考（用时 X 秒）" 格式
            time_patterns = [
                r'已深度思考.*?用时[\s]*(\d+(?:\.\d+)?)\s*秒',
                r'用时[\s]*(\d+(?:\.\d+)?)\s*秒',
                r'(\d+(?:\.\d+)?)\s*秒'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, text)
                if match:
                    thinking_time = match.group(1) + "秒"
                    self.logger.debug(f"从思考部分提取到思考时间: {thinking_time}")
                    return thinking_time
                    
            return ""
            
        except Exception as e:
            self.logger.debug(f"从思考部分提取时间时出错: {e}")
            return ""

    def _extract_thinking_content_from_section(self, section) -> str:
        """从深度思考部分提取思考内容
        
        Args:
            section: 深度思考部分
            
        Returns:
            str: 思考内容
        """
        try:
            # 查找所有段落
            paragraphs = section.find_all(['p', 'div'], recursive=True)
            thinking_paragraphs = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                # 过滤条件：
                # 1. 长度适中（不要太短的文本）
                # 2. 不是标题文本
                # 3. 包含思考关键词
                if (len(text) > 15 and 
                    not text.startswith('已深度思考') and
                    not text.startswith('深度思考') and
                    not re.match(r'^[\s\W]*$', text) and  # 不是纯空白或符号
                    not text in ['', ' ', '。', '，']):   # 不是空内容
                    
                    # 进一步检查是否是有意义的思考内容
                    if (any(keyword in text for keyword in [
                        '用户', '问题', '分析', '考虑', '思考', '理解', '评估', 
                        '判断', '比较', '因为', '所以', '首先', '然后', '最后',
                        '需要', '应该', '可以', '可能', '也许', '但是', '然而',
                        '如果', '那么', '这样', '这里', '这个', '那个'
                    ]) or 
                    len(text) > 50):  # 或者是较长的文本
                        thinking_paragraphs.append(text)
            
            if thinking_paragraphs:
                content = '\n\n'.join(thinking_paragraphs)
                self.logger.debug(f"从思考部分提取到 {len(thinking_paragraphs)} 个段落")
                return content
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"从思考部分提取内容时出错: {e}")
            return ""

    def _extract_thinking_by_content_features(self, soup: BeautifulSoup) -> str:
        """通过内容特征提取思考内容（备用方法）
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 思考内容
        """
        try:
            self.logger.debug("使用内容特征提取思考内容...")
            
            # 查找所有段落
            all_paragraphs = soup.find_all(['p', 'div'])
            potential_thinking = []
            
            for p in all_paragraphs:
                text = p.get_text(strip=True)
                
                # 检查是否是思考段落
                if (len(text) > 30 and 
                    any(keyword in text for keyword in [
                        '用户的问题', '首先', '分析', '考虑', '思考', '理解', 
                        '比较', '检查', '确认', '验证', '计算', '评估'
                    ]) and
                    not '深度思考' in text[:20] and  # 排除标题
                    not text.startswith('9.') and   # 排除正式回答中的内容
                    not 'ds-markdown' in str(p.get('class', []))):  # 排除markdown内容
                    
                    potential_thinking.append(text)
            
            if potential_thinking:
                content = '\n\n'.join(potential_thinking[:10])  # 取前10段避免过长
                self.logger.debug(f"通过内容特征提取到 {len(potential_thinking)} 个思考段落")
                return content
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"内容特征提取失败: {e}")
            return ""

    def _extract_formal_answer(self, soup: BeautifulSoup, structure: Dict[str, str]) -> Optional[str]:
        """提取正式回答内容
        
        Args:
            soup: BeautifulSoup对象
            structure: 页面结构信息
            
        Returns:
            str: 正式回答内容
        """
        try:
            formal_answer = ""
            
            # 方法1：使用markdown容器
            if 'formal_answer_container' in structure:
                selector = structure['formal_answer_container'].replace('div.', '').replace('.', ' ')
                container = soup.find('div', class_=selector.split())
                if container:
                    formal_answer = container.get_text(strip=True)
                    self.logger.debug(f"通过结构提取正式回答: {len(formal_answer)}字符")
            
            # 方法2：查找ds-markdown容器
            if not formal_answer:
                markdown_containers = soup.find_all('div', class_=lambda x: x and 'ds-markdown' in ' '.join(x))
                
                for container in markdown_containers:
                    text = container.get_text(strip=True)
                    if len(text) > 30:  # 过滤掉太短的内容
                        formal_answer = text
                        self.logger.debug(f"通过markdown容器提取正式回答: {len(formal_answer)}字符")
                        break
            
            # 方法3：查找markdown段落
            if not formal_answer:
                if 'markdown_paragraph' in structure:
                    selector = structure['markdown_paragraph'].replace('p.', '').replace('.', ' ')
                    paragraphs = soup.find_all('p', class_=selector.split())
                    
                    if paragraphs:
                        formal_answer = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
                        self.logger.debug(f"通过markdown段落提取正式回答: {len(formal_answer)}字符")
            
            # 方法4：查找最后的大段文本（可能是回答）
            if not formal_answer:
                all_divs = soup.find_all('div')
                for div in reversed(all_divs):  # 从后往前查找
                    text = div.get_text(strip=True)
                    if (len(text) > 100 and 
                        '深度思考' not in text and 
                        '用时' not in text and
                        not any(keyword in text for keyword in ['导航', '菜单', '按钮'])):
                        formal_answer = text
                        self.logger.debug(f"通过大段文本提取正式回答: {len(formal_answer)}字符")
                        break
            
            return formal_answer if formal_answer else None
            
        except Exception as e:
            self.logger.error(f"提取正式回答时出错: {e}")
            return None

    def _extract_content_fallback(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """备用内容提取方法
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            Dict[str, str]: 提取的内容
        """
        try:
            result = {
                'deep_thinking': '',
                'formal_answer': '',
                'thinking_time': ''
            }
            
            # 查找所有文本内容
            all_text_elements = soup.find_all(['div', 'p', 'span'])
            
            # 提取思考时间
            import re
            for element in all_text_elements:
                text = element.get_text(strip=True)
                time_match = re.search(r'用时[\s]*(\d+(?:\.\d+)?)\s*秒', text)
                if time_match:
                    result['thinking_time'] = time_match.group(1) + "秒"
                    break
            
            # 简单的内容分类
            long_texts = []
            for element in all_text_elements:
                text = element.get_text(strip=True)
                if len(text) > 50:
                    long_texts.append(text)
            
            # 假设第一个长文本是思考过程，最后一个是正式回答
            if len(long_texts) >= 2:
                result['deep_thinking'] = long_texts[0]
                result['formal_answer'] = long_texts[-1]
            elif len(long_texts) == 1:
                # 如果只有一个长文本，尝试判断是思考还是回答
                text = long_texts[0]
                if any(keyword in text for keyword in ['分析', '思考', '考虑']):
                    result['deep_thinking'] = text
                else:
                    result['formal_answer'] = text
            
            return result if (result['deep_thinking'] or result['formal_answer']) else None
            
        except Exception as e:
            self.logger.error(f"备用提取方法失败: {e}")
            return None

    def start_new_conversation(self):
        """开启新的对话会话"""
        try:
            self.logger.info("重新导航到主页开启新对话...")
            
            # 重新导航到DeepSeek主页
            self.driver.get("https://chat.deepseek.com")
            time.sleep(2)
            
            # 检查是否需要重新处理Cloudflare验证
            if self.handle_cloudflare_challenge():
                self.logger.info("Cloudflare 验证处理完成")
            
            # 检查登录状态，如果未登录则重新登录
            if not self.is_logged_in():
                self.logger.info("检测到未登录状态，重新登录...")
            if not self.login():
                    self.logger.error("重新登录失败")
                    return False
            
            # 尝试点击"新建对话"按钮（如果存在）
            self._click_new_conversation_button()
            
            # 等待页面完全加载
            time.sleep(self.config.get('automation', {}).get('wait_time', 3))
            
            # 尝试启用深度思考模式（会自动检测当前状态）
            if not self.enable_deep_thinking():
                self.logger.warning("深度思考模式启用失败，但继续执行")
            
            self.logger.info("新对话会话已准备就绪")
            return True
            
        except Exception as e:
            self.logger.error(f"开启新对话时发生错误: {e}")
            return False

    def _click_new_conversation_button(self):
        """尝试点击新建对话按钮"""
        try:
            # 查找新建对话按钮的各种可能选择器
            new_conversation_selectors = [
                # 基于提供的HTML结构的精确选择器
                "div.ds-icon.d7829b2f._23ecf90",  # 具体的图标类名
                "div.ds-icon[style*='font-size: 24px']",  # 基于样式的选择器
                "div.ds-icon[style*='width: 24px'][style*='height: 24px']",  # 基于尺寸的选择器
                
                # 查找包含这个图标的父元素（可能是真正的按钮）
                "button:has(div.ds-icon.d7829b2f)",  # 包含特定图标的按钮
                "div[role='button']:has(div.ds-icon)",  # 包含ds-icon的div按钮
                "[role='button']:has(svg[width='28'][height='28'])",  # 包含特定SVG的按钮
                
                # 基于SVG的选择器
                "svg[width='28'][height='28'][viewBox='0 0 28 28']",  # 特定的SVG
                
                # 通用的新建对话按钮选择器
                "button[aria-label*='新建']",
                "button[title*='新建']",
                "div[role='button'][aria-label*='新建']",
                "div[role='button'][title*='新建']",
                ".new-conversation",
                ".new-chat",
                "[data-testid='new-conversation']",
                "[data-testid='new-chat']",
                "button[class*='new']",
                "div[class*='new'][role='button']",
                
                # DeepSeek特定的类名模式
                "div.ds-icon",  # 所有ds-icon
                "div[class*='ds-icon']",  # 包含ds-icon的类
            ]
            
            # XPath选择器
            xpath_selectors = [
                # 基于SVG路径内容的选择器
                "//div[contains(@class, 'ds-icon')]//svg[@width='28' and @height='28']",
                "//div[contains(@class, 'ds-icon') and contains(@style, 'font-size: 24px')]",
                
                # 查找包含特定图标的父元素
                "//button[descendant::div[contains(@class, 'ds-icon')]]",
                "//div[@role='button' and descendant::div[contains(@class, 'ds-icon')]]",
                "//div[@role='button' and descendant::svg[@width='28']]",
                
                # 传统的文本选择器
                "//button[contains(text(), '新建对话')]",
                "//button[contains(text(), '新建')]",
                "//div[@role='button' and contains(text(), '新建对话')]",
                "//div[@role='button' and contains(text(), '新建')]",
                "//button[contains(@aria-label, '新建')]",
                "//div[contains(@aria-label, '新建')]",
                "//button[contains(text(), 'New')]",
                "//button[contains(text(), 'New Chat')]",
                "//div[@role='button' and contains(text(), 'New')]",
            ]
            
            new_conversation_button = None
            
            # 首先尝试CSS选择器
            for selector in new_conversation_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            # 如果找到的是图标，查找其可点击的父元素
                            if 'ds-icon' in element.get_attribute('class') or element.tag_name == 'svg':
                                # 向上查找可点击的父元素
                                parent = element.parent
                                level = 0
                                while parent and level < 5:
                                    if (parent.tag_name in ['button', 'div'] and 
                                        (parent.get_attribute('role') == 'button' or 
                                         parent.tag_name == 'button')):
                                        if parent.is_enabled():
                                            new_conversation_button = parent
                                            self.logger.debug(f"通过CSS选择器找到新建对话按钮的父元素: {selector}")
                                            break
                                    parent = parent.parent
                                    level += 1
                            elif element.is_enabled():
                                new_conversation_button = element
                                self.logger.debug(f"通过CSS选择器找到新建对话按钮: {selector}")
                            
                            if new_conversation_button:
                                break
                except Exception as e:
                    self.logger.debug(f"CSS选择器 {selector} 失败: {e}")
                    continue
                if new_conversation_button:
                    break
            
            # 如果CSS选择器没找到，尝试XPath
            if not new_conversation_button:
                for xpath in xpath_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            if element.is_displayed():
                                # 如果找到的是图标，查找其可点击的父元素
                                if element.tag_name in ['div', 'svg'] and 'ds-icon' in element.get_attribute('class'):
                                    # 向上查找可点击的父元素
                                    parent = element.parent
                                    level = 0
                                    while parent and level < 5:
                                        if (parent.tag_name in ['button', 'div'] and 
                                            (parent.get_attribute('role') == 'button' or 
                                             parent.tag_name == 'button')):
                                            if parent.is_enabled():
                                                new_conversation_button = parent
                                                self.logger.debug(f"通过XPath找到新建对话按钮的父元素: {xpath}")
                                                break
                                        parent = parent.parent
                                        level += 1
                                elif element.is_enabled():
                                    new_conversation_button = element
                                    self.logger.debug(f"通过XPath找到新建对话按钮: {xpath}")
                                
                                if new_conversation_button:
                                    break
                    except Exception as e:
                        self.logger.debug(f"XPath {xpath} 失败: {e}")
                        continue
                    if new_conversation_button:
                        break
            
            if new_conversation_button:
                # 点击新建对话按钮
                try:
                    # 滚动到按钮位置确保可见
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", new_conversation_button)
                    time.sleep(0.5)
                    
                    new_conversation_button.click()
                    self.logger.info("成功点击新建对话按钮")
                    time.sleep(2)  # 等待新对话页面加载
                    return True
                except Exception as e:
                    self.logger.warning(f"点击新建对话按钮失败: {e}")
                    # 尝试使用JavaScript点击
                    try:
                        self.driver.execute_script("arguments[0].click();", new_conversation_button)
                        self.logger.info("使用JavaScript成功点击新建对话按钮")
                        time.sleep(2)
                        return True
                    except Exception as js_e:
                        self.logger.warning(f"JavaScript点击也失败: {js_e}")
                        return False
                else:
                    self.logger.debug("未找到新建对话按钮，页面刷新可能已经是新对话")
                    return True
                
        except Exception as e:
            self.logger.debug(f"查找新建对话按钮时出错: {e}")
            return True  # 即使失败也继续执行，因为页面刷新通常已经是新对话了

    def _find_clickable_parent(self, element, max_levels=5):
        """向上查找可点击的父元素
        
        Args:
            element: 起始元素
            max_levels: 最大向上查找的层级数
            
        Returns:
            WebElement or None: 找到的可点击父元素
        """
        try:
            parent = element.parent if hasattr(element, 'parent') else element.find_element(By.XPATH, '..')
            level = 0
            
            while parent and level < max_levels:
                try:
                    # 检查是否是可点击的元素
                    if (parent.tag_name in ['button', 'a'] or 
                        parent.get_attribute('role') in ['button', 'link'] or
                        parent.get_attribute('onclick') or
                        'click' in parent.get_attribute('class') or '' or
                        'btn' in parent.get_attribute('class') or ''):
                        
                        if parent.is_enabled() and parent.is_displayed():
                            return parent
                    
                    # 继续向上查找
                    parent = parent.find_element(By.XPATH, '..')
                    level += 1
                    
                except Exception:
                    break
            
            return None
            
        except Exception as e:
            self.logger.debug(f"查找可点击父元素时出错: {e}")
            return None
    
    def _save_response_to_file(self, message_index: int, question: str, response_data: Dict[str, str]):
        """保存回复内容到文件
        
        Args:
            message_index: 消息索引
            question: 问题内容
            response_data: 回复数据
        """
        try:
            import json
            from datetime import datetime
            
            # 创建保存目录
            save_dir = "responses"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{save_dir}/response_{message_index:02d}_{timestamp}.json"
            
            # 准备保存的数据
            save_data = {
                'timestamp': datetime.now().isoformat(),
                'message_index': message_index,
                'question': question,
                'thinking_time': response_data.get('thinking_time', ''),
                'deep_thinking': response_data.get('deep_thinking', ''),
                'formal_answer': response_data.get('formal_answer', ''),
                'page_structure': response_data.get('page_structure', {}),
                'extracted_structure': response_data.get('extracted_structure', {})
            }
            
            # 保存到JSON文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"回复内容已保存到: {filename}")
            
        except Exception as e:
            self.logger.error(f"保存回复内容失败: {e}")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.logger.info("关闭浏览器")
            self.driver.quit()

    def enable_deep_thinking(self) -> bool:
        """启用深度思考模式
        
        Returns:
            bool: 是否成功启用深度思考模式
        """
        try:
            if not self.config['automation'].get('enable_deep_thinking', False):
                self.logger.info("深度思考模式已禁用")
                return True
                
            self.logger.info("检查深度思考模式状态...")
            
            # 查找深度思考按钮
            deep_thinking_selectors = [
                "div[role='button'][class*='ds-button'][class*='primary']:has(.ad0c98fd)",  # 包含特定类的按钮
                "div[role='button']:has(span.ad0c98fd)",  # 包含深度思考文本的按钮
                ".ds-button.ds-button--primary:has(span:contains('深度思考'))",  # 包含深度思考文本的主要按钮
                "div[role='button'][class*='ds-button']",  # 所有ds-button
                "button[class*='deep']",  # 包含deep的按钮
                "div[class*='deep']",  # 包含deep的div
            ]
            
            # 使用XPath查找包含"深度思考"文本的按钮
            xpath_selectors = [
                "//div[@role='button' and contains(., '深度思考')]",
                "//div[@role='button' and contains(., 'R1')]",
                "//div[contains(@class, 'ds-button') and contains(., '深度思考')]",
                "//button[contains(., '深度思考')]",
                "//span[contains(@class, 'ad0c98fd')]/../..",  # 找到包含特定类的span的祖父元素
                "//span[contains(text(), '深度思考')]/ancestor::div[@role='button']"
            ]
            
            deep_thinking_button = None
            
            # 先尝试CSS选择器
            for selector in deep_thinking_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            # 检查按钮文本是否包含"深度思考"
                            if "深度思考" in button.text or "R1" in button.text:
                                deep_thinking_button = button
                                self.logger.info(f"通过CSS选择器找到深度思考按钮: {selector}")
                                break
                except Exception as e:
                    self.logger.debug(f"CSS选择器 {selector} 失败: {e}")
                    continue
                if deep_thinking_button:
                    break
            
            # 如果CSS选择器没找到，尝试XPath
            if not deep_thinking_button:
                for xpath in xpath_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, xpath)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                deep_thinking_button = button
                                self.logger.info(f"通过XPath找到深度思考按钮: {xpath}")
                                break
                    except Exception as e:
                        self.logger.debug(f"XPath {xpath} 失败: {e}")
                        continue
                    if deep_thinking_button:
                        break
            
            if not deep_thinking_button:
                self.logger.warning("未找到深度思考按钮，继续使用普通模式")
                return True
            
            # 检查深度思考模式是否已经激活
            is_activated = self._is_deep_thinking_activated(deep_thinking_button)
            
            if is_activated:
                self.logger.info("深度思考模式已经激活，无需重复激活")
                return True
            else:
                self.logger.info("深度思考模式未激活，正在激活...")
                
                # 点击深度思考按钮
                try:
                    deep_thinking_button.click()
                    self.logger.info("深度思考模式已激活")
                    time.sleep(1)  # 等待模式切换
                    
                    # 再次检查是否激活成功
                    if self._is_deep_thinking_activated(deep_thinking_button):
                        self.logger.info("深度思考模式激活成功")
                        return True
                    else:
                        self.logger.warning("深度思考模式激活可能失败，但继续执行")
                        return True
                        
                except Exception as e:
                    self.logger.error(f"点击深度思考按钮失败: {e}")
                    return False
                
        except Exception as e:
            self.logger.error(f"启用深度思考模式时发生错误: {e}")
            return True  # 即使失败也继续执行

    def _is_deep_thinking_activated(self, button_element) -> bool:
        """检查深度思考模式是否已激活
        
        Args:
            button_element: 深度思考按钮元素
            
        Returns:
            bool: 是否已激活深度思考模式
        """
        try:
            # 方法1：检查按钮的style属性中的颜色
            style_attr = button_element.get_attribute("style")
            if style_attr:
                # 激活状态的特征：蓝色文字和背景
                activated_indicators = [
                    "--button-text-color: #4CAEFF",  # 蓝色文字
                    "rgba(77, 107, 254, 0.40)",      # 蓝色背景
                    "rgba(0, 122, 255, 0.15)",       # 蓝色边框
                ]
                
                # 未激活状态的特征：白色文字
                deactivated_indicators = [
                    "--button-text-color: #F8FAFF",  # 白色文字
                    "transparent"                     # 透明背景
                ]
                
                # 检查激活指示器
                activated_count = sum(1 for indicator in activated_indicators if indicator in style_attr)
                deactivated_count = sum(1 for indicator in deactivated_indicators if indicator in style_attr)
                
                if activated_count > 0:
                    self.logger.debug(f"检测到激活状态指示器 {activated_count} 个")
                    return True
                elif deactivated_count > 0:
                    self.logger.debug(f"检测到未激活状态指示器 {deactivated_count} 个")
                    return False
            
            # 方法2：检查图标的颜色属性
            try:
                icon_elements = button_element.find_elements(By.CSS_SELECTOR, ".ds-icon")
                for icon in icon_elements:
                    icon_style = icon.get_attribute("style")
                    if icon_style:
                        if "rgb(76, 174, 255)" in icon_style:  # 蓝色图标 - 已激活
                            self.logger.debug("检测到蓝色图标，深度思考模式已激活")
                            return True
                        elif "rgb(248, 250, 255)" in icon_style:  # 白色图标 - 未激活
                            self.logger.debug("检测到白色图标，深度思考模式未激活")
                            return False
            except Exception as e:
                self.logger.debug(f"检查图标颜色失败: {e}")
            
            # 方法3：检查CSS类名变化（如果有的话）
            try:
                button_classes = button_element.get_attribute("class")
                if button_classes:
                    # 某些情况下可能有特殊的激活类名
                    if "active" in button_classes.lower() or "selected" in button_classes.lower():
                        self.logger.debug("检测到激活类名")
                        return True
            except Exception as e:
                self.logger.debug(f"检查CSS类名失败: {e}")
            
            # 方法4：通过JavaScript获取计算样式
            try:
                computed_color = self.driver.execute_script("""
                    var element = arguments[0];
                    var style = window.getComputedStyle(element);
                    return {
                        color: style.getPropertyValue('color'),
                        backgroundColor: style.getPropertyValue('background-color'),
                        borderColor: style.getPropertyValue('border-color')
                    };
                """, button_element)
                
                if computed_color:
                    # 检查计算后的颜色值
                    color = computed_color.get('color', '')
                    bg_color = computed_color.get('backgroundColor', '')
                    
                    # 蓝色系表示激活
                    if any(blue_indicator in color.lower() for blue_indicator in ['rgb(76, 174, 255)', '4caeff']):
                        self.logger.debug(f"通过计算样式检测到激活状态: color={color}")
                        return True
                    
                    # 检查背景色
                    if 'rgba(77, 107, 254' in bg_color:  # 部分匹配蓝色背景
                        self.logger.debug(f"通过计算样式检测到激活状态: bg={bg_color}")
                        return True
                    
                    self.logger.debug(f"计算样式: color={color}, bg={bg_color}")
                    
            except Exception as e:
                self.logger.debug(f"获取计算样式失败: {e}")
            
            # 如果所有方法都无法确定状态，默认认为未激活
            self.logger.debug("无法确定深度思考模式状态，默认认为未激活")
            return False
            
        except Exception as e:
            self.logger.debug(f"检查深度思考模式状态时出错: {e}")
            return False

    def ask_question(self, question: str) -> Optional[Dict[str, str]]:
        """提问并获取AI回复
        
        Args:
            question: 要提问的问题
            
        Returns:
            Dict[str, str]: 包含时间戳、问题、深度思考过程和正式回答的字典
            格式: {
                'timestamp': '2024-01-01T12:00:00',
                'question': '用户的问题',
                'deep_thinking': '深度思考过程',
                'formal_answer': '正式回答'
            }
        """
        try:
            from datetime import datetime
            
            self.logger.info(f"开始处理问题: {question}")
            
            self.logger.info("开启新对话会话...")
            if not self.start_new_conversation():
                self.logger.error("开启新对话失败")
                return None
            
            # 发送消息
            if not self.send_message(question):
                self.logger.error("消息发送失败")
                return None
            
            # 等待回复
            response_data = self.wait_for_response()
            if not response_data:
                self.logger.warning("未收到回复或解析失败")
                return None
            
            # 构造返回结果
            result = {
                'timestamp': datetime.now().isoformat(),
                'question': question,
                'deep_thinking': response_data.get('deep_thinking', ''),
                'formal_answer': response_data.get('formal_answer', ''),
                'thinking_time': response_data.get('thinking_time', '')
            }
            
            self.logger.info("问题处理完成")
            return result
            
        except Exception as e:
            self.logger.error(f"处理问题时发生错误: {e}")
            import traceback
            self.logger.debug(f"详细错误: {traceback.format_exc()}")
            return None

    def ask_multiple_questions(self, questions: List[str]) -> List[Dict[str, str]]:
        """批量提问并获取AI回复
        
        Args:
            questions: 问题列表
            
        Returns:
            List[Dict[str, str]]: 结果列表，每个元素包含时间戳、问题、深度思考过程和正式回答
        """
        results = []
        
        try:
            for i, question in enumerate(questions, 1):
                self.logger.info(f"处理第 {i}/{len(questions)} 条问题")
                
                result = self.ask_question(question)
                if result:
                    results.append(result)
                    
                    # 记录处理结果
                    self.logger.info("=" * 60)
                    self.logger.info(f"问题 {i}: {question}")
                    self.logger.info("=" * 60)
                    
                    if result.get('deep_thinking'):
                        self.logger.info(f"深度思考: {result['deep_thinking'][:300]}")
                    
                    if result.get('formal_answer'):
                        self.logger.info(f"正式回答: {result['formal_answer']}")
                    
                    self.logger.info("=" * 60)
                else:
                    self.logger.warning(f"问题 {i} 处理失败: {question}")
                
            
            return results
            
        except Exception as e:
            self.logger.error(f"批量处理问题时发生错误: {e}")
            return results

    def initialize(self) -> bool:
        """初始化浏览器和登录
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 启动浏览器
            self.start_browser()
            
            # 导航到网站并登录
            self.navigate_to_deepseek()
            
            # 登录
            if not self.login():
                self.logger.error("登录失败")
                return False
            
            self.logger.info("初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化时发生错误: {e}")
            return False

    def run_automation(self):
        """运行自动化流程（兼容旧版本，现在主要用于测试）"""
        try:
            # 初始化
            if not self.initialize():
                self.logger.error("初始化失败，停止自动化")
                return
            
            # 检查是否有配置的消息列表（向后兼容）
            messages = self.config.get('messages', [])
            if messages:
                self.logger.info("使用配置文件中的消息列表")
                results = self.ask_multiple_questions(messages)
                
                # 可选：保存详细内容到文件
                if self.config.get('automation', {}).get('save_responses', False):
                    for i, result in enumerate(results, 1):
                        self._save_response_to_file(i, result.get('question', ''), {
                            'deep_thinking': result.get('deep_thinking', ''),
                            'formal_answer': result.get('formal_answer', ''),
                            'thinking_time': '',
                            'page_structure': {}
                        })
            else:
                self.logger.info("配置文件中没有消息列表，请使用ask_question()或ask_multiple_questions()方法")
            
            self.logger.info("自动化流程完成")
            
        except Exception as e:
            self.logger.error(f"自动化过程中发生错误: {e}")
            import traceback
            self.logger.debug(f"详细错误: {traceback.format_exc()}")
        finally:
            # 根据配置决定是否关闭浏览器
            if self.config.get('automation', {}).get('close_browser', False):
                self.close()
            else:
                self.logger.info("浏览器保持打开状态")

    def _extract_thinking_time(self, soup: BeautifulSoup) -> str:
        """提取思考用时（备用方法）
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 思考用时
        """
        try:
            # 在整个页面中搜索思考时间
            page_text = soup.get_text()
            
            time_patterns = [
                r'已深度思考.*?用时[\s]*(\d+(?:\.\d+)?)\s*秒',
                r'用时[\s]*(\d+(?:\.\d+)?)\s*秒',
                r'(\d+(?:\.\d+)?)\s*秒'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, page_text)
                if match:
                    thinking_time = match.group(1)
                    self.logger.debug(f"通过备用方法提取到思考时间: {thinking_time}")
                    return thinking_time
                    
            return ""
            
        except Exception as e:
            self.logger.debug(f"提取思考时间时出错: {e}")
            return ""

def main():
    """主函数"""
    automation = DeepSeekAutomation()
    automation.run_automation()


if __name__ == "__main__":
    main() 