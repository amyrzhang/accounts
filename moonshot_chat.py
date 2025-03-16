# -*- coding: utf-8 -*-
from pathlib import Path
from openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import load_tools, initialize_agent, AgentType

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


llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
tools = load_tools(["wikipedia", "llm-math"], llm=llm)
agent = initialize_agent(
    tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

question = """What is the square root of the population of the capital
of the Country where the Olympic Games were held in 2016?"""
agent.run(question)
# res = get_chat_completion(question, file_path='5.jpg')
# print(res)

