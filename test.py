import mysql.connector
from mysql.connector import Error


def execute_transaction(stock_code, action, quantity, price, fee):
    conn = None
    try:
        # 1. 连接数据库
        conn = mysql.connector.connect(
            host='localhost',
            database='trading_db',
            user='your_user',
            password='your_password'
        )
        cursor = conn.cursor()

        # 2. 开启事务
        conn.start_transaction()

        # 3. 插入交易记录
        insert_transaction = """
        INSERT INTO transaction (stock_code, type, quantity, price, fee, timestamp)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(insert_transaction, (stock_code, action, quantity, price, fee))

        # 4. 更新资金（买入扣款，卖出收款）
        cashflow_type = 'WITHDRAW' if action == 'BUY' else 'DEPOSIT'
        amount = (price * quantity) + (fee if action == 'BUY' else -fee)
        insert_cashflow = """
        INSERT INTO cashflow (type, amount, timestamp)
        VALUES (%s, %s, NOW())
        """
        cursor.execute(insert_cashflow, (cashflow_type, amount))

        # 5. 更新持仓
        if action == 'BUY':
            # 计算新平均成本（加权平均）
            update_position = """
            INSERT INTO position (stock_code, quantity, avg_cost, last_updated)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                quantity = quantity + VALUES(quantity),
                avg_cost = (avg_cost * quantity + VALUES(avg_cost) * VALUES(quantity)) / (quantity + VALUES(quantity)),
                last_updated = NOW()
            """
            cursor.execute(update_position, (stock_code, quantity, price))
        elif action == 'SELL':
            # 减少持仓数量（需先检查持仓是否足够）
            check_position = "SELECT quantity FROM position WHERE stock_code = %s FOR UPDATE"
            cursor.execute(check_position, (stock_code,))
            current_qty = cursor.fetchone()[0]
            if current_qty < quantity:
                raise Exception("持仓不足，无法卖出")

            update_position = """
            UPDATE position SET
                quantity = quantity - %s,
                last_updated = NOW()
            WHERE stock_code = %s
            """
            cursor.execute(update_position, (quantity, stock_code))

        # 6. 提交事务
        conn.commit()
        print("交易成功！")

    except Error as e:
        # 7. 失败时回滚
        if conn:
            conn.rollback()
        print(f"交易失败，已回滚: {e}")
    finally:
        # 8. 关闭连接
        if conn:
            cursor.close()
            conn.close()


# 示例：买入100股腾讯，单价350元，手续费5元
execute_transaction('00700.HK', 'BUY', 100, 350.0, 5.0)