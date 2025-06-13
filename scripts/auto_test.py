from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time
import os
from datetime import datetime
import logging
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import platform

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_test.log'),
        logging.StreamHandler()
    ]
)

class ModelTester:
    def __init__(self):
        self.results = []
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        options = webdriver.ChromeOptions()
        # 添加用户数据目录，这样可以保持登录状态
        user_data_dir = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default')
        options.add_argument(f'user-data-dir={user_data_dir}')
        
        # 添加一些额外的选项以提高稳定性
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        
        try:
            # 连接到本地运行的 ChromeDriver
            service = Service('http://localhost:50209')  # 使用终端显示的端口号
            self.driver = webdriver.Remote(
                command_executor='http://localhost:50209',
                options=options
            )
            self.driver.set_window_size(1920, 1080)  # 设置窗口大小
            logging.info("成功连接到本地运行的 ChromeDriver")
        except Exception as e:
            logging.error(f"连接本地 ChromeDriver 失败: {str(e)}")
            raise

    def _get_chrome_version(self):
        """获取Chrome浏览器版本"""
        try:
            if platform.system() == 'Darwin':  # macOS
                # 尝试从应用程序包获取版本
                chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
                if os.path.exists(chrome_path):
                    import subprocess
                    result = subprocess.run([chrome_path, '--version'], capture_output=True, text=True)
                    version = result.stdout.strip().split()[-1]
                    return version.split('.')[0]  # 只返回主版本号
            return None
        except Exception as e:
            logging.error(f"获取Chrome版本失败: {str(e)}")
            return None

    def load_test_data(self):
        """从construct_result_all.json加载测试数据"""
        try:
            with open('data/composition/construct_result_all.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 遍历所有规则
                for rule_name, rule_data in data.items():
                    if 'formulas' in rule_data:
                        for formula_data in rule_data['formulas']:
                            if 'executions' in formula_data:
                                for execution in formula_data['executions']:
                                    if 'results' in execution:
                                        for result in execution['results']:
                                            if 'tricks' in result and result['tricks']:
                                                for trick in result['tricks']:
                                                    if 'formula_after' in trick:
                                                        self.results.append({
                                                            'original_formula': result.get('formula', {}).get('left', '') + ' = ' + result.get('formula', {}).get('right', ''),
                                                            'transformed_formula': trick['formula_after'],
                                                            'operations': trick.get('operation', []),
                                                            'rule_name': rule_name,
                                                            'complexity': result.get('complexity', 0)
                                                        })
            logging.info(f"成功加载 {len(self.results)} 个测试用例")
            if len(self.results) == 0:
                logging.warning("没有找到任何测试用例，请检查数据文件结构")
        except Exception as e:
            logging.error(f"加载测试数据失败: {str(e)}")
            raise

    def generate_prompt(self, formula):
        # 生成提示词
        return f"{formula}\n这个等式是否成立？请给出尽量详细的思路和逐步化简或运算过程。"

    def test_on_qwen(self, formula):
        # 在通义千问上测试
        try:
            # 打开通义千问网页
            self.driver.get('https://qianwen.aliyun.com/')
            time.sleep(5)  # 等待页面加载
            
            # 找到输入框并输入提示词
            prompt = self.generate_prompt(formula)
            input_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='输入您的问题']"))
            )
            input_box.send_keys(prompt)
            input_box.send_keys(Keys.RETURN)
            
            # 等待回复
            response = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".response-content"))
            )
            
            return {
                'model': 'Qwen',
                'response': response.text,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"通义千问测试失败: {str(e)}")
            return None

    # def test_on_gpt4(self, formula):
    #     # 在GPT-4上测试
    #     try:
    #         # 打开ChatGPT网页
    #         self.driver.get('https://chat.openai.com/')
    #         time.sleep(5)  # 等待页面加载
            
    #         # 找到输入框并输入提示词
    #         prompt = self.generate_prompt(formula)
    #         input_box = WebDriverWait(self.driver, 10).until(
    #             EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='Send a message']"))
    #         )
    #         input_box.send_keys(prompt)
    #         input_box.send_keys(Keys.RETURN)
            
    #         # 等待回复
    #         response = WebDriverWait(self.driver, 30).until(
    #             EC.presence_of_element_located((By.CSS_SELECTOR, ".markdown-content"))
    #         )
            
    #         return {
    #             'model': 'GPT-4',
    #             'response': response.text,
    #             'timestamp': datetime.now().isoformat()
    #         }
    #     except Exception as e:
    #         logging.error(f"GPT-4测试失败: {str(e)}")
    #         return None

    def test_on_deepseek(self, formula):
        # 在DeepSeek上测试
        try:
            # 打开DeepSeek网页
            self.driver.get('https://chat.deepseek.com/')
            time.sleep(5)  # 等待页面加载
            
            # 找到输入框并输入提示词
            prompt = self.generate_prompt(formula)
            input_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='输入消息']"))
            )
            input_box.send_keys(prompt)
            input_box.send_keys(Keys.RETURN)
            
            # 等待回复
            response = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".message-content"))
            )
            
            return {
                'model': 'DeepSeek',
                'response': response.text,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"DeepSeek测试失败: {str(e)}")
            return None

    def save_results(self, test_results):
        """保存测试结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/model_test_results_{timestamp}.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(test_results, f, ensure_ascii=False, indent=2)
            logging.info(f"测试结果已保存到: {filename}")
        except Exception as e:
            logging.error(f"保存测试结果失败: {str(e)}")

    def run_tests(self):
        """运行所有测试"""
        self.load_test_data()
        all_test_results = []
        
        for idx, result in enumerate(self.results, 1):
            logging.info(f"测试用例 {idx}/{len(self.results)}: {result['transformed_formula']}")
            
            test_result = {
                'original_formula': result['original_formula'],
                'transformed_formula': result['transformed_formula'],
                'operations': result['operations'],
                'model_responses': []
            }
            
            # 在每个模型上测试
            for model_test in [self.test_on_qwen,  self.test_on_deepseek]:
                response = model_test(result['transformed_formula'])
                if response:
                    test_result['model_responses'].append(response)
                time.sleep(5)  # 在模型之间添加延迟
            
            all_test_results.append(test_result)
            
            # 每10个测试用例保存一次结果
            if idx % 10 == 0:
                self.save_results(all_test_results)
        
        # 保存最终结果
        self.save_results(all_test_results)
        self.driver.quit()

if __name__ == "__main__":
    tester = ModelTester()
    try:
        tester.run_tests()
    except Exception as e:
        logging.error(f"测试过程发生错误: {str(e)}")
        if tester.driver:
            tester.driver.quit() 