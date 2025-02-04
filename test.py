import mysql.connector
from mysql.connector import Error


def execute_transaction(stock_code, action, quantity, price, fee):
    conn = None
    try:
        # 1. �������ݿ�
        conn = mysql.connector.connect(
            host='localhost',
            database='trading_db',
            user='your_user',
            password='your_password'
        )
        cursor = conn.cursor()

        # 2. ��������
        conn.start_transaction()

        # 3. ���뽻�׼�¼
        insert_transaction = """
        INSERT INTO transaction (stock_code, type, quantity, price, fee, timestamp)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(insert_transaction, (stock_code, action, quantity, price, fee))

        # 4. �����ʽ�����ۿ�����տ
        cashflow_type = 'WITHDRAW' if action == 'BUY' else 'DEPOSIT'
        amount = (price * quantity) + (fee if action == 'BUY' else -fee)
        insert_cashflow = """
        INSERT INTO cashflow (type, amount, timestamp)
        VALUES (%s, %s, NOW())
        """
        cursor.execute(insert_cashflow, (cashflow_type, amount))

        # 5. ���³ֲ�
        if action == 'BUY':
            # ������ƽ���ɱ�����Ȩƽ����
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
            # ���ٳֲ����������ȼ��ֲ��Ƿ��㹻��
            check_position = "SELECT quantity FROM position WHERE stock_code = %s FOR UPDATE"
            cursor.execute(check_position, (stock_code,))
            current_qty = cursor.fetchone()[0]
            if current_qty < quantity:
                raise Exception("�ֲֲ��㣬�޷�����")

            update_position = """
            UPDATE position SET
                quantity = quantity - %s,
                last_updated = NOW()
            WHERE stock_code = %s
            """
            cursor.execute(update_position, (quantity, stock_code))

        # 6. �ύ����
        conn.commit()
        print("���׳ɹ���")

    except Error as e:
        # 7. ʧ��ʱ�ع�
        if conn:
            conn.rollback()
        print(f"����ʧ�ܣ��ѻع�: {e}")
    finally:
        # 8. �ر�����
        if conn:
            cursor.close()
            conn.close()


# ʾ��������100����Ѷ������350Ԫ��������5Ԫ
execute_transaction('00700.HK', 'BUY', 100, 350.0, 5.0)