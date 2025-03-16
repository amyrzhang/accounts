import pandas as pd
from bs4 import BeautifulSoup

# ��ȡExcel�ļ�
df = pd.read_excel('֪ʶ������.xlsx', engine='openpyxl')

# ����HTML��������Ϊ'html_column'������
html_column = '������'

# ����HTML��ת��Ϊ���ı�
def parse_html(html):
    # ���html��float���ͣ�������NaN�������ؿ��ַ���
    if pd.isna(html):
        return ""
    # ȷ��html���ַ������ͣ������������ת��
    if not isinstance(html, str):
        html = str(html)
    try:
        soup = BeautifulSoup(html, 'lxml')
        return soup.get_text()
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return ""

# Ӧ�ú�����DataFrame�е�ָ����
df['parsed_text'] = df[html_column].apply(parse_html)

# �����Ҫ���������һ��������������ı��ĳ���
df['text_length'] = df['parsed_text'].apply(len)

# д���µ�Excel�ļ������������У���������
df.to_excel('1-1.xlsx', index=False, engine='openpyxl')

print("�����ɹ���ɣ����ļ������ɡ�")