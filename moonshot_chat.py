# -*- coding: utf-8 -*-
from pathlib import Path
from openai import OpenAI

MOONSHOT_API_KEY = 'sk-09cudzNN2PADe2WiNqYZRoqTSHjkBPD4EhbSMDFt5UsYFzVL'
BASE_URL = 'https://api.moonshot.cn/v1'


def get_chat_completion(content, file_path):
    client = OpenAI(
        api_key=MOONSHOT_API_KEY,
        base_url=BASE_URL,
    )

    # "hpf_records.jpg" 是一个示例文件, 我们支持 pdf, doc 以及图片等格式, 对于图片和 pdf 文件，提供 ocr 相关能力
    file_object = client.files.create(file=Path(file_path), purpose="file-extract")

    # 获取结果
    file_content = client.files.content(file_id=file_object.id).text
    print(type(file_content))
    # print(file_content)

    # 把它放进请求中
    messages = [
        {
            "role": "system",
            "content": file_content,
        },
        {
            "role": "user",
            "content": content
        },
    ]

    # 然后调用 chat-completion, 获取 Kimi 的回答
    completion = client.chat.completions.create(
        model="moonshot-v1-32k",
        messages=messages,
        temperature=1.0,
    )
    return completion.choices[0].message.content


question = """
我将给你一份截图，请按 time, debit_credit, amount, type, goods, payment_method 解析为json，其中
time的格式为 "%Y-%m-%d %H:%M:%S" ，借记卡4827 右边的内容表示 时分, 比如time: 2024-06-18 23:35:00
type的值为收入
文字部分是goods
当交易金额为负时debit_credit为支出，否则为收入，解析后的amount为正值
"payment_method": "民生银行储蓄卡(4827)"
"""
res = get_chat_completion(question, file_path='5.jpg')
print(res)

