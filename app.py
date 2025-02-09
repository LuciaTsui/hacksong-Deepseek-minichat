from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
from openai import OpenAI  # 引入 DeepSeek API 客户端

app = Flask(__name__)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_input TEXT,
                  bot_response TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

# 配置 DeepSeek API 客户端
client = OpenAI(
    base_url="https://api.ppinfra.com/v3/openai",
    api_key="sk_u_n86Ee3jzwSOz3mBCrgj6PEMoOwBbAApNVZ9SwNEeI",  # 替换为你的 API Key
)

# 修改 DeepSeek 模型函数，调用 API
def deepseek_model(input_text):
    model = "deepseek/deepseek-v3/community"
    stream = False  # 非流式输出，方便前端处理
    max_tokens = 2048
    system_content = "你是派欧算力云 AI 助手，你会以诚实专业的态度帮助用户，用中文回答问题。\n"
    
    try:
        # 调用 DeepSeek API
        chat_completion_res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": input_text}
            ],
            stream=stream,
            max_tokens=max_tokens,
            temperature=1,
            top_p=1,
            presence_penalty=0,
            frequency_penalty=0,
            response_format={"type": "text"},
            extra_body={
                "top_k": 50,
                "repetition_penalty": 1,
                "min_p": 0
            }
        )
        
        # 返回生成的回复
        return chat_completion_res.choices[0].message.content
    
    except Exception as e:
        return f"调用 DeepSeek API 失败：{str(e)}"

# 主页
@app.route('/')
def index():
    return render_template('index.html')

# 处理用户输入
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['user_input']
    bot_response = deepseek_model(user_input)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 保存聊天记录到数据库
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (user_input, bot_response, timestamp) VALUES (?, ?, ?)",
              (user_input, bot_response, timestamp))
    conn.commit()
    conn.close()

    return jsonify({'bot_response': bot_response})

# 获取历史记录
@app.route('/history', methods=['GET'])
def history():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT user_input, bot_response, timestamp FROM chat_history ORDER BY timestamp DESC")
    history = c.fetchall()
    conn.close()
    return jsonify({'history': history})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
