# -*- coding: utf-8 -*-
from pathlib import Path
from openai import OpenAI

MOONSHOT_API_KEY = 'sk-09cudzNN2PADe2WiNqYZRoqTSHjkBPD4EhbSMDFt5UsYFzVL'
BASE_URL = 'https://api.moonshot.cn/v1'


client = OpenAI(
    api_key=MOONSHOT_API_KEY,
    base_url=BASE_URL,
)

# "hpf_records.jpg" 是一个示例文件, 我们支持 pdf, doc 以及图片等格式, 对于图片和 pdf 文件，提供 ocr 相关能力
file_object = client.files.create(file=Path("hpf_records.jpg"), purpose="file-extract")

# 获取结果
file_content = client.files.content(file_id=file_object.id).text

# 把它放进请求中
messages = [
    {
        "role": "system",
        "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
    },
    {
        "role": "system",
        "content": file_content,
    },
    {"role": "user", "content": '请帮我解析图片内容，返回json，格式是 [{"time": "%Y-%m-%d 00:00:00", "type": "汇缴", "payment_method": "住房公积金", "debit_credit": "收入", "amount": $amount}]'},
]

# 然后调用 chat-completion, 获取 Kimi 的回答
completion = client.chat.completions.create(
    model="moonshot-v1-32k",
    messages=messages,
    temperature=0,
)

print(completion.choices[0].message.content)