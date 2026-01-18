# 资产余额期间变动表
# 期间为左开右闭
# create view reconciliation_variance_worksheet as
with base_tb as (
    select *
        ,  row_number() over (partition by account_name order by balance_date ) as rk
    from money_track.asset_snapshot
)
select curr.id, curr.`year_month` as `year_month`
     , curr.account_name
     , prev.balance_date as opening_date, curr.balance_date as closing_date
     , coalesce(prev.balance, 0) as opening_balance, curr.balance as closing_balance
     , curr.balance - coalesce(prev.balance, 0) as current_period_change
     , cf.balance, cf.income, cf.expense
     , curr.balance - coalesce(prev.balance, 0) - cf.balance as variance
     , (curr.balance - coalesce(prev.balance, 0) - cf.balance) / curr.balance as variance_rate
     , curr.is_verified
     , curr.remark
from base_tb curr
left join base_tb prev on curr.account_name=prev.account_name and prev.rk=curr.rk-1
left join stat_monthly_income_expense cf on cf.`year_month` = curr.`year_month` and cf.account_name = curr.account_name
# 每账户的首条记录无前记录，期间变动总记录数 = 资产账户余额记录数 - 1
where prev.balance is not null;


select *
from cashflow
where year(time)=2025 and payment_method rlike '招商|107819A';


select *,if(debit_credit='收入', amount, -amount) as net_income
from cashflow
where year(time)=2025 and counterparty rlike '107819A';

select *
from cashflow
where transaction_id is not null




# 【年度资产余额表】
# 若是期初账户还未建立，则期初余额为空，其含义为0，需将空值补为0
create view annual_account_balance as
select closing_tb.id
     , closing_tb.account_name
     , opening_tb.balance_date                              as opening_date
     , closing_tb.balance_date                              as closing_date
     , coalesce(opening_tb.balance, 0)                      as opending_balance
     , closing_tb.balance                                   as closing_balance
     , closing_tb.balance - coalesce(opening_tb.balance, 0) as current_period_change
from (
        select *
        from money_track.asset_snapshot
        where balance_date='2025-12-31'
    )closing_tb
left join (
        select *
        from (
                select *
                     , row_number() over (partition by account_name order by balance_date  desc) as rk
                from money_track.asset_snapshot
                where date_format(balance_date, '%Y') < '2025'
        )tb
        where rk = 1
    )opening_tb on opening_tb.account_name = closing_tb.account_name;




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



# 【月度科目余额表】以 月&账户 粒度
# 注意：只有当期有凭证的科目余额才会被计算
create view stat_monthly_income_expense as
with cashflow_tb as (select date_format(cf.time, '%Y-%m')                                                       as `year_month`
                          , if(ai.account_name is not null, account_name, 'other')                              as account_name
                          , sum(case
                                    when debit_credit = '收入' then amount
                                    when debit_credit = '支出' then -amount
                                    else 0 end)                                                                 as balance
                          , sum(IF(
            debit_credit = '收入' and type in ('工资薪金', '劳务报酬', '利息', '证券账户浮盈', '其他所得'), amount,
            0))                                                                                                 as income
                          , sum(IF(
            debit_credit = '收入' and type in ('工资薪金', '劳务报酬', '利息', '证券账户浮盈', '其他所得'), amount, 0)
                            ) - sum(case
                                        when debit_credit = '收入' then amount
                                        when debit_credit = '支出' then -amount
                                        else 0 end)                                                             as expense
                     from money_track.cashflow cf
                              left join money_track.account_info ai on cf.payment_method = ai.account_name # 关联获取账户名称

                     where cf.transaction_id is null # 只考虑现金流，不包括证券交易，因其只在证券账户内部流转
                     group by date_format(cf.time, '%Y-%m'),
                              if(ai.account_name is not null, account_name, 'other'))
select `year_month`
     , account_name
     , balance
     , sum(balance) over (partition by substr(`year_month`, 1, 4), account_name order by `year_month`) as ytd_balance
     , income
     , sum(income) over (partition by substr(`year_month`, 1, 4), account_name order by `year_month`)  as ytd_income
     , expense
     , sum(expense) over (partition by substr(`year_month`, 1, 4), account_name order by `year_month`) as ytd_expense
from cashflow_tb
order by `year_month`, account_name;



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


create view money_track.v_position as
select stock_code
    , quantity
    , if(quantity>0, round(cost/quantity, 3), 0) as avg_cost
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
