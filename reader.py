import pandas as pd
from bs4 import BeautifulSoup

# 读取Excel文件
df = pd.read_excel('知识库数据.xlsx', engine='openpyxl')

# 假设HTML内容在名为'html_column'的列中
html_column = '答复内容'

# 解析HTML并转换为纯文本
def parse_html(html):
    # 如果html是float类型（可能是NaN），返回空字符串
    if pd.isna(html):
        return ""
    # 确保html是字符串类型，如果不是则尝试转换
    if not isinstance(html, str):
        html = str(html)
    try:
        soup = BeautifulSoup(html, 'lxml')
        return soup.get_text()
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return ""

# 应用函数到DataFrame中的指定列
df['parsed_text'] = df[html_column].apply(parse_html)

# 如果需要，可以添加一列来保存解析后文本的长度
df['text_length'] = df['parsed_text'].apply(len)

# 写入新的Excel文件，保留所有行，包括空行
df.to_excel('1-1.xlsx', index=False, engine='openpyxl')

print("操作成功完成，新文件已生成。")