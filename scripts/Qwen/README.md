# 通义千问 AI 自动化工具

这是一个用于自动与通义千问 AI 交互的Python工具，支持思考过程提取，能够获取AI的思考过程和回答。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 配置文件设置

编辑 `config.json` 文件：

```json
{
  "login": {
    "email": "",
    "password": ""
  },
  "browser": {
    "headless": false,
    "window_size": "1200,800",
    "user_data_dir": "./chrome_profile_qwen",
    "timeout": 10
  },
  "automation": {
    "wait_time": 3,
    "response_timeout": 120,
    "save_responses": true,
    "close_browser": false,
    "new_conversation_per_message": true,
    "question_interval": 5
  },
  "cloudflare": {
    "max_wait_time": 30,
    "check_interval": 1,
    "auto_solve": false
  }
}
```

### 2. 基本使用

#### 单个问题处理

```python
from qwen_automation import QwenAutomation

automation = QwenAutomation()
try:
    # 初始化浏览器和登录
    if not automation.initialize():
        print("初始化失败")
        return
    
    # 提问 - 使用标准格式（与 load_test_data 和 generate_prompt 一致）
    formula = "1+1=?"
    question = automation.generate_prompt(formula)
    result = automation.ask_question(question)
    
    if result:
        print(f"时间戳: {result['timestamp']}")
        print(f"问题: {result['question']}")
        print(f"思考过程: {result['thinking_process']}")
        print(f"正式回答: {result['formal_answer']}")
        
        # 保存结果到文件
        with open(f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    else:
        print("获取回复失败")
        return None
        
finally:
    automation.close()
```

#### 批量问题处理

```python
from qwen_automation import QwenAutomation

# 创建自动化实例
automation = QwenAutomation()

try:
    # 初始化浏览器和登录
    if not automation.initialize():
        print("初始化失败")
        return
    
    # 准备问题列表 - 使用与 load_test_data 一致的公式格式
    formulas = [
        "1+1=?",
        "9.11和9.9哪个大"
    ]
    
    # 生成标准格式的问题
    questions = [automation.generate_prompt(formula) for formula in formulas]
    
    # 批量处理
    results = automation.ask_multiple_questions(questions)
    
    print(f"成功处理了 {len(results)}/{len(questions)} 个问题")
    
    # 保存所有结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f"batch_results_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    for i, result in enumerate(results, 1):
        print(f"\n问题 {i}: {result['question'][:50]}...")
        print(f"思考过程长度: {len(result.get('thinking_process', ''))} 字符")
        print(f"正式回答长度: {len(result.get('formal_answer', ''))} 字符")
    
    return results
    
finally:
    automation.close()
```

#### 使用测试数据自动化

```python
from qwen_automation import QwenAutomation

automation = QwenAutomation()
try:
    # 初始化浏览器和登录
    if not automation.initialize():
        print("初始化失败")
        return
    
    # 运行自动化测试（使用与 load_test_data 一致的数据文件）
    automation.run_automation('data/tricks/fusion_results_all.json')
    
    print("自动化测试完成")
    
finally:
    automation.close()
```

## 返回数据格式

每次提问都会返回一个字典，包含以下字段：

```python
{
    'timestamp': '2024-01-01T12:00:00.000000',  # 提问时间戳
    'question': '用户的问题',                    # 原始问题
    'thinking_process': '思考过程...',           # AI的思考过程
    'formal_answer': '正式回答内容...',          # AI的最终回答
    'original_formula': '原始公式'               # 原始公式（如果有）
}
```

## 配置说明

`config.json` 文件包含以下配置项：

```json
{
    "login": {
        "email": "登录邮箱（可选）",
        "password": "登录密码（可选）"
    },
    "browser": {
        "headless": false,                       # 是否无头模式
        "window_size": "1200,800",              # 浏览器窗口大小
        "user_data_dir": "./chrome_profile_qwen", # 用户数据目录
        "timeout": 10                            # 元素等待超时时间
    },
    "automation": {
        "wait_time": 3,                          # 操作间等待时间
        "response_timeout": 120,                 # 等待回复超时时间
        "save_responses": true,                  # 是否保存回复到文件
        "close_browser": false,                  # 是否自动关闭浏览器
        "new_conversation_per_message": true,    # 是否每条消息开启新对话
        "question_interval": 5                   # 问题间隔时间
    },
    "cloudflare": {
        "max_wait_time": 30,                     # Cloudflare 验证最大等待时间
        "check_interval": 1,                     # 检查间隔
        "auto_solve": false                      # 是否自动解决验证
    }
}
```

## 运行示例

直接运行示例文件：

```bash
python example_usage.py
```

## 数据一致性

本工具的 `load_test_data` 和 `generate_prompt` 方法与主项目保持一致：

- `load_test_data()`: 从 `data/tricks/fusion_results_all.json` 加载测试数据
- `generate_prompt()`: 生成标准格式的提示词：`"{formula}\n这个等式是否成立？请给出尽量详细的思路和逐步化简或运算过程。"`

## API 方法

### `initialize()`
初始化浏览器并登录到通义千问。

**返回**: `bool` - 是否成功初始化

### `ask_question(question)`
提问并获取AI回复。

**参数**:
- `question` (str): 要提问的问题

**返回**: `Dict[str, str]` - 包含回复信息的字典，失败时返回None

### `ask_multiple_questions(questions)`
批量处理多个问题。

**参数**:
- `questions` (List[str]): 问题列表

**返回**: `List[Dict[str, str]]` - 结果列表

### `load_test_data(data_file)`
从融合结果文件加载测试数据。

**参数**:
- `data_file` (str): 数据文件路径，默认为 'data/tricks/fusion_results_all.json'

**返回**: `List[str]` - 公式列表

### `generate_prompt(formula)`
生成标准格式的提示词。

**参数**:
- `formula` (str): 公式

**返回**: `str` - 标准格式的提示词

### `run_automation(test_data_file)`
运行自动化测试。

**参数**:
- `test_data_file` (str): 测试数据文件路径

### `close()`
关闭浏览器。

## 注意事项

1. 使用前需要手动登录通义千问，工具会等待用户按回车键确认登录完成。
2. 建议在非无头模式下首次运行，确保能够正确处理登录和验证。
3. 如果遇到 Cloudflare 验证，可以在配置中启用 `auto_solve`，但建议手动处理。
4. 所有输入的公式格式应与主项目的 `fusion_results_all.json` 文件保持一致。 