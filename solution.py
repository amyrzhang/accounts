import pandas as pd


def strip_in_data(data):  # 把列名中和数据中首尾的空格都去掉。
    data = data.rename(columns={column_name: column_name.strip() for column_name in data.columns})
    data = data.map(lambda x: x.strip().strip('¥') if isinstance(x, str) else x)
    return data


def read_data_wx(path):  # 获取微信数据
    d_wx = pd.read_csv(path, header=16, skipfooter=0, encoding='utf-8')  # 数据获取，微信
    d_wx = d_wx.iloc[:, [0, 4, 7, 1, 2, 3, 5]]  # 按顺序提取所需列
    d_wx = strip_in_data(d_wx)  # 去除列名与数值中的空格。
    d_wx['交易时间'] = pd.to_datetime(d_wx['交易时间'])  # 数据类型更改
    d_wx['金额(元)'] = d_wx['金额(元)'].astype('float64')  # 数据类型更改
    d_wx = d_wx.drop(d_wx[d_wx['收/支'] == '/'].index)  # 删除'收/支'为'/'的行
    d_wx.rename(columns={'当前状态': '支付状态', '交易类型': '类型', '金额(元)': '金额'}, inplace=True)  # 修改列名称
    d_wx.insert(1, '来源', "微信", allow_duplicates=True)  # 添加微信来源标识
    len1 = len(d_wx)
    print("成功读取 " + str(len1) + " 条「微信」账单数据\n")
    return d_wx


def read_data_zfb(path):  # 获取支付宝数据
    d_zfb = pd.read_csv(path, header=22, encoding='gbk')  # 数据获取，支付宝
    d_zfb = d_zfb.iloc[:, [0, 5, 8, 2, 4, 6]]  # 按顺序提取所需列
    d_zfb = strip_in_data(d_zfb)  # 去除列名与数值中的空格。
    d_zfb['交易时间'] = pd.to_datetime(d_zfb['交易时间'])  # 数据类型更改
    d_zfb.iloc[:, -1] = d_zfb.iloc[:, -1].astype('float64')  # 数据类型更改
    d_zfb = d_zfb.drop(d_zfb[d_zfb['收/支'] == ''].index)  # 删除'收/支'为空的行
    d_zfb.rename(columns={'交易状态': '支付状态', '商品说明': '商品'}, inplace=True)  # 修改列名称
    d_zfb.insert(1, '来源', "支付宝", allow_duplicates=True)  # 添加支付宝来源标识
    d_zfb.insert(4, '类型', "商户消费", allow_duplicates=True)  # 添加类型标识
    len2 = len(d_zfb)
    print("成功读取 " + str(len2) + " 条「支付宝」账单数据\n")
    return process_data_zfb(d_zfb)


def process_data_zfb(data_zfb):
    return data_zfb[(data_zfb['支付状态'] == '交易成功') & (data_zfb['收/支'] != '不计收支')]

def read_data_bank(path):
    data = pd.read_csv(path)
    data['交易时间'] = pd.to_datetime(data['交易时间'])
    data['金额'] = data['金额'].astype('float64')
    return data

def add_cols(data):  # 增加3列数据
    # 逻辑1：取值-1 or 1。-1表示支出，1表示收入。
    data.insert(8, '逻辑1', -1, allow_duplicates=True)  # 插入列，默认值为-1
    for index in range(len(data.iloc[:, 2])):  # 遍历第3列的值，判断为收入，则改'逻辑1'为1
        if data.iloc[index, 2] == '收入':
            data.iloc[index, 8] = 1

        # update 2021/12/29: 修复支付宝理财收支逻辑bug
        elif data.iloc[index, 5] == '蚂蚁财富-蚂蚁（杭州）基金销售有限公司' and '卖出' in data.iloc[index, 6]:
            data.iloc[index, 8] = 1
        elif data.iloc[index, 5] == '蚂蚁财富-蚂蚁（杭州）基金销售有限公司' and '转换至' in data.iloc[index, 6]:
            data.iloc[index, 8] = 0
        elif data.iloc[index, 2] == '其他' and '收益发放' in data.iloc[index, 6]:
            data.iloc[index, 8] = 1
        elif data.iloc[index, 2] == '其他' and '现金分红' in data.iloc[index, 6]:
            data.iloc[index, 8] = 1
        elif data.iloc[index, 2] == '其他' and '买入' in data.iloc[index, 6]:
            data.iloc[index, 8] = -1
        elif data.iloc[index, 2] == '其他':
            data.iloc[index, 8] = 0

    # 逻辑2：取值0 or 1。1表示计入，0表示不计入。
    data.insert(9, '逻辑2', 1, allow_duplicates=True)  # 插入列，默认值为1
    for index in range(len(data.iloc[:, 3])):  # 遍历第4列的值，判断为资金流动，则改'逻辑2'为0
        col3 = data.iloc[index, 3]
        if (col3 == '提现已到账') or (col3 == '已全额退款') or (col3 == '已退款') or (col3 == '退款成功') or (
                col3 == '还款成功') or (
                col3 == '交易关闭'):
            data.iloc[index, 9] = 0

    # 月份
    data.insert(1, '月份', 0, allow_duplicates=True)  # 插入列，默认值为0
    for index in range(len(data.iloc[:, 0])):
        time = data.iloc[index, 0]
        data.iloc[index, 1] = time.month  # 访问月份属性的值，赋给这月份列

    # 乘后金额
    data.insert(11, '乘后金额', 0, allow_duplicates=True)  # 插入列，默认值为0
    for index in range(len(data.iloc[:, 8])):
        money = data.iloc[index, 8] * data.iloc[index, 9] * data.iloc[index, 10]
        data.iloc[index, 11] = money
    return data


def check_bill_data(bill_data):
    data_resource = bill_data['来源'].unique()
    min_date, max_date = str(min(bill_data['交易时间']))[:10], str(max(bill_data['交易时间']))[:10]
    bill_date_range = min_date + '至' + max_date
    bill_num = bill_data.shape[0]
    bill_summary = bill_data.groupby('收/支')['金额'].sum()
    summary = """
    账单来源：{}
    账单周期：{}
    账单数量：{}条
    支出金额：￥{}
    收入金额：￥{}
    结余金额：￥{}
    """.format(data_resource, bill_date_range, bill_num, bill_summary['支出'], bill_summary['收入'],bill_summary['收入']-bill_summary['支出'],)
    print(summary)

    return summary
