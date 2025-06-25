# DeepSeek AI 自动化工具

这是一个用于自动与 DeepSeek AI 交互的Python工具，支持深度思考模式，能够提取AI的思考过程和回答。

## 安装依赖

```bash
pip install -r requirements.lock
```

## 快速开始

### 1. 配置登录信息

编辑 `config.json` 文件，填入你的DeepSeek账号信息：

```json
{
    "login": {
        "email": "your_email@example.com",
        "password": "your_password"
    }
}
```

### 2. 基本使用

#### 单个问题处理

```python
from deepseek_automation import DeepSeekAutomation

automation = DeepSeekAutomation()
try:
    # 初始化浏览器和登录
    if not automation.initialize():
        print("初始化失败")
        return
    
    # 提问
    question = "1+1=?"
    result = automation.ask_question(question)
    
    if result:
        print(f"时间戳: {result['timestamp']}")
        print(f"问题: {result['question']}")
        print(f"深度思考过程: {result['deep_thinking']}")
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
from deepseek_automation import DeepSeekAutomation

# 创建自动化实例
    automation = DeepSeekAutomation()
    
    try:
        # 初始化浏览器和登录
        if not automation.initialize():
            print("初始化失败")
            return
        
        # 准备问题列表
        questions = [
            "1+1=?",
            "9.11和9.9哪个大"
        ]
        
        # 批量处理
        results = automation.ask_multiple_questions(questions)
        
        print(f"成功处理了 {len(results)}/{len(questions)} 个问题")
        
        # 保存所有结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f"batch_results_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        for i, result in enumerate(results, 1):
            print(f"\n问题 {i}: {result['question']}")
            print(f"深度思考过程长度: {len(result['deep_thinking'])} 字符")
            print(f"正式回答长度: {len(result['formal_answer'])} 字符")
        
        return results
        
    finally:
        automation.close()
```

## 返回数据格式

每次提问都会返回一个字典，包含以下字段：

```python
{
    'timestamp': '2024-01-01T12:00:00.000000',  # 提问时间戳
    'question': '用户的问题',                    # 原始问题
    'deep_thinking': '深度思考过程...',          # AI的思考过程
    'formal_answer': '正式回答内容...',          # AI的最终回答
    'thinking_time': '思考时长'                  # AI的思考时长（单位：秒）
}
```

## 配置说明

`config.json` 文件包含以下配置项：

```json
{
    "login": {
        "email": "登录邮箱",
        "password": "登录密码"
    },
    "browser": {
        "headless": false,                    # 是否无头模式
        "window_size": "1200,800",           # 浏览器窗口大小
        "user_data_dir": "./chrome_profile_deepseek",  # 用户数据目录
        "timeout": 10                        # 元素等待超时时间
    },
    "automation": {
        "wait_time": 3,                      # 操作间等待时间
        "enable_deep_thinking": true,        # 是否启用深度思考模式
        "response_timeout": 120,             # 等待回复超时时间
        "save_responses": true,              # 是否保存回复到文件
        "close_browser": false,              # 是否自动关闭浏览器
        "new_conversation_per_message": true # 是否每条消息开启新对话
    }
}
```

## 运行示例

直接运行示例文件：

```bash
python example_usage.py
```

## API 方法

### `initialize()`
初始化浏览器并登录到DeepSeek。

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

### `close()`
关闭浏览器。
