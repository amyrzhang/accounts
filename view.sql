# 历史余额
# INSERT INTO transaction (time, source, expenditure_income, counterparty, pay_method, amount, category, goods)
# VALUES ('2024-06-30 23:59:59', '手工', '收入', '', '民生银行储蓄卡(4827)',  675.72, '历史余额', '历史余额');

# 月度收支
create view monthly_balance as
select month, income - expenditure as balance, income, expenditure
from (select date_format(time, '%Y-%m')                      as month
           , sum(if(expenditure_income = '收入', amount, 0)) as income
           , sum(if(expenditure_income = '支出', amount, 0)) as expenditure
      from money_track.transaction
      group by month) tb
order by month desc;


# 卡余额
create view card_balance as
with transfer_tb as (select *
                     from money_track.transaction
                     where pay_method regexp '^.{2}银行储蓄卡\\([0-9]{4}\\)$' # 用收付款账户都是银行卡判断【转账】
                       and counterparty regexp '^.{2}银行储蓄卡\\([0-9]{4}\\)$'),
     spending_tb as (select *
                     from money_track.transaction
                     where not (pay_method regexp '^.{2}银行储蓄卡\\([0-9]{4}\\)$'
                         and counterparty regexp '^.{2}银行储蓄卡\\([0-9]{4}\\)$')), # 空值无法匹配
     transaction_tb as (select *
                        from spending_tb
                        union all
                        select id
                             , time
                             , source
                             , '支出' as expenditure_income
                             , status
                             , type
                             , category
                             , counterparty
                             , goods
                             , reversed
                             , amount
                             , pay_method
                             , processed_amount
                        from transfer_tb
                        union all
                        select id
                             , time
                             , source
                             , '收入'       as expenditure_income
                             , status
                             , type
                             , category
                             , pay_method   as counterparty
                             , goods
                             , reversed
                             , amount
                             , counterparty as pay_method
                             , processed_amount
                        from transfer_tb)
select *,
       sum(case
               when expenditure_income = '收入' then amount
               when expenditure_income = '支出' then -amount
               else 0 end) over (partition by pay_method order by time asc) as balance
from transaction_tb;



# 校准不计收支账单
select date_format(time, '%Y-%m') as month,
       sum(case when expenditure_income = '收入' then amount
                when expenditure_income = '支出' then -amount
       else 0 end) as balance,
        sum(if(expenditure_income = '收入', amount, 0)) as income,
        sum(if(expenditure_income = '支出', amount, 0)) as expenditure
from transaction
group by month;

select sum(case when expenditure_income='支出' then amount else 0 end) as amount
from transaction
where amount >= 1000;


# 月度卡对账单
# select date_format(time, '%Y-%m')                      as month
#      , pay_method                                      as card
#      , sum(case
#                when expenditure_income = '收入' then amount
#                when expenditure_income = '支出' then -amount
#                else 0 end)                             as balance
#      , sum(if(expenditure_income = '收入', amount, 0)) as income
#      , sum(if(expenditure_income = '支出', amount, 0)) as expenditure
# from transaction_tb
# group by month, pay_method
# order by month desc, pay_method desc;


select-- date_format(time, '%Y-%m')                      as month
      pay_method                                      as card
     , sum(case
               when expenditure_income = '收入' then amount
               when expenditure_income = '支出' then -amount
               else 0 end)                             as balance
     , sum(if(expenditure_income = '收入', amount, 0)) as income
     , sum(if(expenditure_income = '支出', amount, 0)) as expenditure
from card_balance
group by  pay_method
order by  pay_method desc;



# 月度分类别支出
create view monthly_expenditure_category as
select cat.month,
       cat.category,
       cat.amount,
       (cat.amount / tot.expenditure) * 100 as precent
from (select date_format(time, '%Y-%m') as month
           , category
           , sum(amount)                as amount
      from money_track.transaction cat
      where expenditure_income = '支出'
      group by month, category) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;


# 月度支出交易累积占比
create view monthly_expenditure_cdf as
select cat.month
     , cat.category
     , cat.counterparty
     , cat.goods
     , cat.amount
     , (cat.amount / tot.expenditure) * 100                                                             as percent
     , sum((cat.amount / tot.expenditure) * 100) over (partition by cat.month order by cat.amount desc) as cdf
from (select date_format(time, '%Y-%m') as month
           , category
           , counterparty
           , goods
           , amount
      from money_track.transaction cat
      where expenditure_income = '支出'
      order by month desc, amount desc) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;

