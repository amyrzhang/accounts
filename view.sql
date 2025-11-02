# 分账户净流入统计-用户对账
select
    date_format(time, '%Y-%m') as month_date
    , payment_method
    , sum(case when debit_credit='收入' then amount
        when debit_credit='支出' then -amount
        else 0 end ) as net_debit
from cashflow
where type not in ('申购', '赎回') -- 过滤证券交易记录，只考虑现金流动
group by month_date, payment_method
order by month_date desc, abs(net_debit) desc ;


# 卡余额，用账户表关联
create view v_account_activity as
select cashflow_id,
       time,
       debit_credit,
       counterparty,
       goods,
       sum(case
       amount,
               when debit_credit = '收入' then amount
               when debit_credit = '支出' then -amount
               else 0 end) over (partition by payment_method order by time) as balance,
       payment_method as account_name,
       category,
       type
from cashflow
order by time desc;




# 资产余额表更新
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
                                       when debit_credit = '收入' then amount
                                       when debit_credit = '支出' then -amount
                                       else 0 end)                             as balance
                             , sum(if(debit_credit = '收入', amount, 0)) as income
                             , sum(if(debit_credit = '支出', amount, 0)) as expenditure
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
order by is_included desc , account_type desc , balance desc;




# 月度收支，收入的枚举值：工资薪金，劳务报酬，其他所得
create view money_track.monthly_balance as
select month
       , balance
       , income
       , tb.income - tb.balance as expenditure
       , credit
       , debit
from (
        select date_format(time, '%Y-%m') as month
               , sum(case
                         when debit_credit = '收入' then amount
                         when debit_credit = '支出' then -amount
                         else 0 end)                             as balance
               , sum(case
                         when debit_credit = '收入' and type in ('工资薪金', '劳务报酬', '其他所得')  then amount
                         else 0 end)                             as income
               , sum(if(debit_credit = '收入', amount, 0))       as credit
               , sum(if(debit_credit = '支出', amount, 0))       as debit
        from money_track.cashflow cf
        left join money_track.account_info ai on cf.counterparty = ai.account_name
        where cf.transaction_id is null  -- 过滤掉`证券交易`
        and ai.account_name is null  -- 过滤掉`转账记录`
        group by date_format(cf.time, '%Y-%m')) tb
order by month;


# 季度收支
create view v_quarterly_balance as
select concat(year(concat(month, '-01')), '-Q', quarter(concat(month, '-01'))) as month
      , sum(balance) as balance
      , sum(income) as income
      , sum(expenditure) as expenditure
      , sum(credit) as credit
      , sum(debit) as debit
from monthly_balance
group by concat(year(concat(month, '-01')), '-Q', quarter(concat(month, '-01')))
order by concat(year(concat(month, '-01')), '-Q', quarter(concat(month, '-01')));


# 年度收支
create view v_annual_balance as
select year(concat(month, '-01')) as month
      , sum(balance) as balance
      , sum(income) as income
      , sum(expenditure) as expenditure
      , sum(credit) as credit
      , sum(debit) as debit
from monthly_balance
group by year(concat(month, '-01'))
order by year(concat(month, '-01'));


# 月度分类别支出
create view money_track.monthly_exp_category as
select cat.month,
       cat.category,
       cat.amount,
       (cat.amount / tot.expenditure) * 100 as percent
from (
         select
            date_format(m.time, '%Y-%m') as month
            , m.debit_credit
            , sum(case when m.debit_credit='收入' then m.amount
                when m.debit_credit='支出' then m.amount  else 0 end) as amount
            , m.category
        from money_track.cashflow m
        where m.transaction_id is null  -- 过滤掉证券交易记录
          and m.debit_credit='支出'      -- 只统计支出消费记录
        group by month, category

) cat
left join money_track.monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;

# 统计归因收支
create view v_cashflow as
select
    m.cashflow_id
     , m.time
     , date_format(m.time, '%Y-%m') as month
     , concat(year(m.time), '-Q', quarter(m.time)) as quarter
     , date_format(m.time, '%Y') as year
     , m.type
     , m.counterparty
     , m.goods
     , m.debit_credit
     , case when m.debit_credit='收入' then m.amount + coalesce(s.amount, 0)
            when m.debit_credit='支出' then m.amount - coalesce(s.amount, 0) else 0 end as amount
     , m.payment_method
     , m.status
     , m.category
     , m.source
     , m.transaction_id
from money_track.cashflow m
         left join (
            select sum(case when debit_credit='收入' then amount
                            when debit_credit='支出' then -amount else 0 end) as amount
            from money_track.cashflow
         ) s on m.cashflow_id = s.fk_cashflow_id
where m.fk_cashflow_id is null;  -- 保留主记录



# 月度支出交易累积占比
# drop view money_track.monthly_exp_cdf;                               d
create view money_track.monthly_exp_cdf as
select cat.cashflow_id as id
     , cat.month
     , cat.category
     , cat.amount
     , (cat.amount / tot.expenditure) * 100                                                             as percent
     , sum((cat.amount / tot.expenditure) * 100) over (partition by cat.month order by cat.amount desc) as cdf
     , cat.counterparty
     , cat.goods
from (
         select
            m.cashflow_id
            , date_format(m.time, '%Y-%m') as month
            , m.type
            , m.counterparty
            , m.goods
            , m.debit_credit
            , case when m.debit_credit='收入' then m.amount
                when m.debit_credit='支出' then m.amount  else 0 end as amount
            , m.payment_method
            , m.status
            , m.category
            , m.source
            , m.transaction_id
        from money_track.cashflow m
        where m.transaction_id is null  -- 过滤掉证券交易记录
          and m.debit_credit='支出'      -- 只统计支出消费记录
          and m.counterparty not in (
                select distinct account_name from money_track.account_info
     )
) cat
         left join money_track.monthly_balance tot on cat.month = tot.month

order by month desc, amount desc;



CREATE TABLE asset_snapshot (
                                snapshot_id   INT AUTO_INCREMENT PRIMARY KEY,
                                date          DATE         NOT NULL UNIQUE,  -- 假设每日仅一条快照
                                cash          DECIMAL(18,3) NOT NULL,        -- 可用资金（可交易现金）
                                position_value DECIMAL(18,3) NOT NULL,       -- 持仓总市值
                                total_asset   DECIMAL(18,3) NOT NULL,        -- 总资产 = cash + position_value
                                INDEX (date)
);


CREATE TABLE transaction (
                             transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                             stock_code    VARCHAR(10)   NOT NULL,        -- 股票代码（如 002991.SZ）
                             type          ENUM('BUY','SELL', 'DIVIDEND') NOT NULL,   -- 交易类型
                             timestamp     DATETIME      NOT NULL,        -- 交易时间
                             quantity      INT           NOT NULL,        -- 交易数量（股）
                             price         DECIMAL(18,3) NOT NULL,        -- 成交单价
                             fee           DECIMAL(18,2) NOT NULL DEFAULT 0,  -- 手续费
                             INDEX (stock_code, timestamp)
);


CREATE TABLE stock_price (
                             stock_code        VARCHAR(10)   NOT NULL,   -- 股票代码（如002991.SZ）
                             date              DATE          NOT NULL,   -- 交易日
                             open              DECIMAL(18,2) NOT NULL,   -- 开盘价
                             high              DECIMAL(18,2) NOT NULL,   -- 最高价
                             low               DECIMAL(18,2) NOT NULL,   -- 最低价
                             close             DECIMAL(18,2) NOT NULL,   -- 收盘价
                             volume            BIGINT        NOT NULL,   -- 成交量（股）
                             amount            DECIMAL(18,2) NOT NULL,   -- 成交额（元）
                             outstanding_share BIGINT        NOT NULL,   -- 流通股本（股）
                             turnover          DECIMAL(2,18) NOT NULL,   -- 换手率（如0.016853）
                             PRIMARY KEY (stock_code, date),             -- 复合主键
                             INDEX (date),                               -- 按日期查询优化
                             INDEX (stock_code)                          -- 按股票代码查询优化
);


# CREATE TABLE position (
#                           position_id  INT AUTO_INCREMENT PRIMARY KEY,
#                           stock_code   VARCHAR(10)   NOT NULL UNIQUE,  -- 股票代码唯一（单只股票一条记录）
#                           quantity     INT           NOT NULL,         -- 当前持仓数量
#                           avg_cost     DECIMAL(18,3) NOT NULL,         -- 动态计算的平均成本价
#                           last_updated DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP        -- 最后更新时间
# );

# 持仓视图
create view money_track.v_position as
select stock_code
    , quantity
    , round(cost / quantity, 3) as avg_cost
    , round(cost, 2) as total_cost
    , last_updated
from (
         SELECT stock_code,
                SUM(case
                        when type = 'BUY' then quantity
                        when type = 'SELL' then -quantity else 0 end)           AS quantity,
                SUM(CASE
                        WHEN type = 'BUY' THEN amount + fee
                        when type = 'SELL' then -amount + fee
                        when type = 'DIVIDEND' then -amount
                        ELSE 0 END)                                             AS cost,
                MAX(timestamp)                                                  AS last_updated
         FROM money_track.transaction
         GROUP BY stock_code
)tb;


CREATE VIEW v_current_asset AS
SELECT
    a.cash,
    SUM(p.quantity * sp.close) AS position_value,
    a.cash + SUM(p.quantity * sp.close) AS total_asset
FROM asset_snapshot a
         JOIN position p ON 1=1  -- 单账户无需关联条件
         JOIN stock_price sp ON p.stock_code = sp.stock_code
WHERE sp.date = (SELECT MAX(date) FROM stock_price);  -- 获取最新价格

# 持仓盈亏，TODO： 盈亏比例有问题
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

-- 示例：统计 2023 年 10 月盈亏
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
    (sp.close - p.avg_cost) * p.quantity AS unrealized_pnl  -- 未实现盈亏
FROM position p
         JOIN stock_price sp ON p.stock_code = sp.stock_code
WHERE sp.date = (SELECT MAX(date) FROM stock_price);
