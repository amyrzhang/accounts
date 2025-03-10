# ��֧��¼��
CREATE TABLE `transaction`
(
    `id`                 int            NOT NULL AUTO_INCREMENT,
    `time`               datetime       NOT NULL,
    `source`             varchar(128)   NOT NULL,
    `expenditure_income` varchar(10)    NOT NULL,
    `status`             varchar(10)             DEFAULT NULL,
    `type`               varchar(10)             DEFAULT NULL,
    `category`           varchar(128)   NOT NULL,
    `counterparty`       varchar(128)            DEFAULT NULL,
    `goods`              varchar(128)   NOT NULL,
    `amount`             decimal(10, 2) NOT NULL,
    payment_method         varchar(20)    NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  AUTO_INCREMENT = 388
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;


# �ʲ���Ϣ��
CREATE TABLE `account_info`
(
    `id`           int          NOT NULL AUTO_INCREMENT,
    `account_name` varchar(255) NOT NULL,
    `account_type` varchar(50)  NOT NULL,
    `is_active`    tinyint(1)   NOT NULL DEFAULT '1',
    `is_included`  tinyint(1)   NOT NULL DEFAULT '1',
    `create_time`  datetime              DEFAULT CURRENT_TIMESTAMP,
    `update_time`  datetime              DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  AUTO_INCREMENT = 10
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;


# �������˻������
create view v_account_activity as
select cashflow_id,
       time,
       debit_credit,
       counterparty,
       goods,
       sum(case
       amount,
               when debit_credit = '����' then amount
               when debit_credit = '֧��' then -amount
               else 0 end) over (partition by payment_method order by time) as balance,
       payment_method as account_name,
       category,
       type
from cashflow
order by time desc;




# �ʲ��������
# drop view account_balance;
create view account_balance as
with cash_tb as (
    select a.id
         , a.account_name
         , a.account_type
         , t.balance
         , t.income
         , t.expenditure
         , t.create_time
         , t.update_time
         , a.is_included
    from account_info a
             left join (select payment_method
                             , min(time)                                       as create_time
                             , max(time)                                       as update_time
                             , sum(case
                                       when debit_credit = '����' then amount
                                       when debit_credit = '֧��' then -amount
                                       else 0 end)                             as balance
                             , sum(if(debit_credit = '����', amount, 0)) as income
                             , sum(if(debit_credit = '֧��', amount, 0)) as expenditure
                        from cashflow
                        group by payment_method) t
                       on a.account_name = t.payment_method
    where is_active = 1
    order by account_type desc, balance desc
),
stock_tb as (
        select null as id
             , stock_code as account_name
             , 'investment' as account_type
             , position_value as balance
             , 0 as credit
             , 0 as debit
             , date as create_time
             , date as update_time
             , 1 as is_included
        from v_current_asset),
base_tb as (
    select *
    from cash_tb
    union all
    select *
    from stock_tb
) ,
total_tb as (
    select
        max(id) as id
         , '' as account_name
         , '' as account_type
         , round(sum(if(is_included=1, balance, 0)), 2) as balance
         , sum(if(is_included=1, income, 0)) as credit
         , sum(if(is_included=1, expenditure, 0)) as debit
         , max(create_time) as create_time
         , max(update_time) as update_time
         , sum(is_included) as is_included
    from base_tb
)
select
    a.id
    , a.account_name
    , a.account_type
    , a.balance
    , round(a.balance / t.balance * 100, 2) as percent
    , a.credit
    , a.debit
    , a.create_time
    , a.update_time
    , a.is_included
from (
         select *
         from total_tb
         union all
         select *
         from base_tb
     )a
cross join total_tb t
order by is_included desc , balance desc;




# �¶���֧�������ö��ֵ�����ʣ�����ѣ����ηѣ���Ϣ������
drop view monthly_balance;
create view monthly_balance as
select month
       , balance
       , income
       , tb.income - tb.balance as expenditure
       , credit
       , debit
from (select date_format(time, '%Y-%m')                      as month
           , sum(case
                     when debit_credit = '����' then amount
                     when debit_credit = '֧��' then -amount
                     else 0 end)                             as balance
           , sum(case
                     when debit_credit = '����' and goods rlike '����|�����|���η�|��Ϣ|����|��ְ' then amount
                     else 0 end)                             as income
           , sum(if(debit_credit = '����', amount, 0)) as credit
           , sum(if(debit_credit = '֧��', amount, 0)) as debit
      from cashflow
      where transaction_id is null
      group by month) tb
order by month;



# �¶ȷ����֧��
create view monthly_exp_category as
select cat.month,
       cat.category,
       cat.amount,
       (cat.amount / tot.expenditure) * 100 as percent
from (
         select date_format(time, '%Y-%m') as month
              , category
              , sum(amount)                as amount
         from money_track.cashflow cat
         where debit_credit = '֧��'
           and transaction_id is null
           and cashflow_id in (
             select cashflow_id
             from money_track.cashflow
             group by cashflow_id
             having count(*) = 1
         )
         group by month, category
) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;


# �¶�֧�������ۻ�ռ��
create view monthly_exp_cdf as
select cat.cashflow_id as id
     , cat.month
     , cat.category
     , cat.amount
     , (cat.amount / tot.expenditure) * 100                                                             as percent
     , sum((cat.amount / tot.expenditure) * 100) over (partition by cat.month order by cat.amount desc) as cdf
     , cat.counterparty
     , cat.goods
from (
         select *, date_format(time, '%Y-%m') as month
         from cashflow cat
         where debit_credit = '֧��'
           and transaction_id is null
           and cashflow_id in (
             select cashflow_id
             from cashflow
             group by cashflow_id
             having count(*) = 1
         )
         order by month desc, amount desc
) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;



CREATE TABLE asset_snapshot (
                                snapshot_id   INT AUTO_INCREMENT PRIMARY KEY,
                                date          DATE         NOT NULL UNIQUE,  -- ����ÿ�ս�һ������
                                cash          DECIMAL(18,3) NOT NULL,        -- �����ʽ𣨿ɽ����ֽ�
                                position_value DECIMAL(18,3) NOT NULL,       -- �ֲ�����ֵ
                                total_asset   DECIMAL(18,3) NOT NULL,        -- ���ʲ� = cash + position_value
                                INDEX (date)
);


CREATE TABLE transaction (
                             transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                             stock_code    VARCHAR(10)   NOT NULL,        -- ��Ʊ���루�� 002991.SZ��
                             type          ENUM('BUY','SELL', 'DIVIDEND') NOT NULL,   -- ��������
                             timestamp     DATETIME      NOT NULL,        -- ����ʱ��
                             quantity      INT           NOT NULL,        -- �����������ɣ�
                             price         DECIMAL(18,3) NOT NULL,        -- �ɽ�����
                             fee           DECIMAL(18,2) NOT NULL DEFAULT 0,  -- ������
                             INDEX (stock_code, timestamp)
);


CREATE TABLE stock_price (
                             stock_code        VARCHAR(10)   NOT NULL,   -- ��Ʊ���루��002991.SZ��
                             date              DATE          NOT NULL,   -- ������
                             open              DECIMAL(18,2) NOT NULL,   -- ���̼�
                             high              DECIMAL(18,2) NOT NULL,   -- ��߼�
                             low               DECIMAL(18,2) NOT NULL,   -- ��ͼ�
                             close             DECIMAL(18,2) NOT NULL,   -- ���̼�
                             volume            BIGINT        NOT NULL,   -- �ɽ������ɣ�
                             amount            DECIMAL(18,2) NOT NULL,   -- �ɽ��Ԫ��
                             outstanding_share BIGINT        NOT NULL,   -- ��ͨ�ɱ����ɣ�
                             turnover          DECIMAL(2,18) NOT NULL,   -- �����ʣ���0.016853��
                             PRIMARY KEY (stock_code, date),             -- ��������
                             INDEX (date),                               -- �����ڲ�ѯ�Ż�
                             INDEX (stock_code)                          -- ����Ʊ�����ѯ�Ż�
);


# CREATE TABLE position (
#                           position_id  INT AUTO_INCREMENT PRIMARY KEY,
#                           stock_code   VARCHAR(10)   NOT NULL UNIQUE,  -- ��Ʊ����Ψһ����ֻ��Ʊһ����¼��
#                           quantity     INT           NOT NULL,         -- ��ǰ�ֲ�����
#                           avg_cost     DECIMAL(18,3) NOT NULL,         -- ��̬�����ƽ���ɱ���
#                           last_updated DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP        -- ������ʱ��
# );

# �ֲֳɱ���
# drop view v_position;
create view v_position as
select stock_code
    , quantity
    , cost/quantity as avg_cost
    , round(cost/quantity, 3) as avg_cost_short
    , last_updated
from (
         SELECT stock_code,
                SUM(case
                        when type = 'BUY' then quantity
                        when type = 'SELL' then -quantity else 0 end)           AS quantity,
                SUM(CASE
                        WHEN type = 'BUY' THEN quantity * price + fee
                        when type = 'SELL' then -quantity * price + fee
                        when type = 'DIVIDEND' then -quantity * price
                        ELSE 0 END)         AS cost,
                  MAX(timestamp)                               AS last_updated
          FROM transaction
          GROUP BY stock_code
)tb;

# ���¹ɼ�
select *
from (
        select stock_code,
       date ,
       close,
       row_number() over (partition by stock_code order by date desc) as rn
        from stock_price
     )t
where rn = 1;



CREATE VIEW v_current_asset AS
SELECT
    a.cash,
    SUM(p.quantity * sp.close) AS position_value,
    a.cash + SUM(p.quantity * sp.close) AS total_asset
FROM asset_snapshot a
         JOIN position p ON 1=1  -- ���˻������������
         JOIN stock_price sp ON p.stock_code = sp.stock_code
WHERE sp.date = (SELECT MAX(date) FROM stock_price);  -- ��ȡ���¼۸�

# �ֲ�ӯ����TODO�� ӯ������������
# drop view v_current_asset;
create view v_current_asset as
select
    p.stock_code
    , sp.date
    , p.quantity
    , round(sp.close, 3) as price
    , round(p.avg_cost, 3) as avg_cost
    , round(p.quantity * sp.close - p.avg_cost * p.quantity, 2) as unrealized_pnl
    , round((p.quantity * sp.close - p.avg_cost * p.quantity) / (p.quantity * p.avg_cost) * 100, 3) as pnl_ratio
    , round(p.quantity * sp.close, 2) as position_value
    , round(p.quantity * p.avg_cost,2) as realized_pnl
from v_position p
left join (
        select date, stock_code, close,
            row_number() over (partition by stock_code order by date desc) as rn
        from stock_price
) sp on p.stock_code = sp.stock_code
where sp.rn = 1;

-- ʾ����ͳ�� 2023 �� 10 ��ӯ��
CREATE VIEW v_monthly_pnl AS
SELECT
    (SELECT total_asset FROM asset_snapshot WHERE date = '2023-10-31') -
    (SELECT total_asset FROM asset_snapshot WHERE date = '2023-09-30') -
    (SELECT SUM(IF(type='DEPOSIT', amount, -amount))
     FROM cashflow
     WHERE timestamp BETWEEN '2023-10-01' AND '2023-10-31') AS pnl;



CREATE VIEW v_position_pnl AS
SELECT
    p.stock_code,
    p.quantity,
    p.avg_cost,
    sp.close AS current_price,
    (sp.close - p.avg_cost) * p.quantity AS unrealized_pnl  -- δʵ��ӯ��
FROM position p
         JOIN stock_price sp ON p.stock_code = sp.stock_code
WHERE sp.date = (SELECT MAX(date) FROM stock_price);
