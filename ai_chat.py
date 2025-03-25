# -*- coding: utf-8 -*-
from pathlib import Path
from openai import OpenAI
import base64

DEEPSEEK_API_KEY = 'sk-3dd683aed81348a49f794b4a84af96dc'
BASE_URL = 'https://api.deepseek.com/v1/'


def get_chat_completion(content, file_path):
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=BASE_URL,
    )

    # 本地读取文件内容
    with open(file_path, "rb") as image_file:
        file_content = base64.b64encode(image_file.read()).decode('utf-8')

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
        model="deepseek-chat",
        messages=messages,
        temperature=1.0,
    )
    return completion.choices[0].message.content


if __name__ == '__main__':
    get_chat_completion("请帮我总结一下这个文件内容", "screenshot.png")

