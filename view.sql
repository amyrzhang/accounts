# 收支记录表
CREATE TABLE `transaction` (
  `id` int NOT NULL AUTO_INCREMENT,
  `time` datetime NOT NULL,
  `source` varchar(128) NOT NULL,
  `expenditure_income` varchar(10) NOT NULL,
  `status` varchar(10) DEFAULT NULL,
  `type` varchar(10) DEFAULT NULL,
  `category` varchar(128) NOT NULL,
  `counterparty` varchar(128) DEFAULT NULL,
  `goods` varchar(128) NOT NULL,
  `reversed` tinyint(1) NOT NULL DEFAULT '0',
  `amount` decimal(10,2) NOT NULL,
  `pay_method` varchar(20) NOT NULL,
  `processed_amount` decimal(10,2) DEFAULT '0.00',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=388 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

# 历史余额
# INSERT INTO transaction (time, source, expenditure_income, counterparty, pay_method, amount, category, goods)
# VALUES ('2024-06-30 21:28:17', '手工', '收入', '', '民生银行储蓄卡(4827)',  675.72, '历史余额', '历史余额');

# 资产信息表
CREATE TABLE `asset_info` (
  `id` int NOT NULL AUTO_INCREMENT,
  `asset_name` varchar(255) NOT NULL,
  `asset_type` varchar(50) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `is_included` tinyint(1) NOT NULL DEFAULT '1',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;






SELECT
    a.asset_name
     , asset_type
     , t.balance
     , t.balance as total
FROM asset_info a
         left join (SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY pay_method ORDER BY time DESC) AS rn
                    FROM card_transaction) t on a.asset_name = t.pay_method
WHERE a.is_active = 1
  and a.is_included = 1
  and t.rn = 1;




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

# 资产余额表更新
create view asset_balance as
select a.id
     , a.asset_name
     , a.asset_type
     , t.balance
     , t.income
     , t.expenditure
     , t.create_time
     , t.update_time
     , a.is_active
     , a.is_included
from asset_info a
         left join (select pay_method
                         , min(time)                                       as create_time
                         , max(time)                                       as update_time
                         , sum(case
                                   when expenditure_income = '收入' then amount
                                   when expenditure_income = '支出' then -amount
                                   else 0 end)                             as balance
                         , sum(if(expenditure_income = '收入', amount, 0)) as income
                         , sum(if(expenditure_income = '支出', amount, 0)) as expenditure
                    from card_transaction
                    group by pay_method) t
                   on a.asset_name = t.pay_method
order by asset_type desc, balance desc
;

# 查询资产余额
select asset_type
     , sum(balance)     as tot_balance
     , sum(income)      as tot_income
     , sum(expenditure) as tot_expenditure
     , max(update_time) as update_time
from asset_balance
where is_active = 1
  and is_included = 1
group by asset_type;

# 月度卡对账单 - 用于校验数据读入
# TODO: 待完善，若该月无交易，无法拉取各卡数据
create view monthly_card_balance as
select date_format(time, '%Y-%m')                      as month
     , pay_method                                      as card
     , sum(case
               when expenditure_income = '收入' then amount
               when expenditure_income = '支出' then -amount
               else 0 end)                             as balance
     , sum(if(expenditure_income = '收入', amount, 0)) as income
     , sum(if(expenditure_income = '支出', amount, 0)) as expenditure
from card_transaction
group by month, pay_method
order by month desc, pay_method desc;




# 月度收支对账单 - 用于统计月度收支
create view monthly_balance as
select date_format(time, '%Y-%m')                      as month
     , sum(case
               when expenditure_income = '收入' then amount
               when expenditure_income = '支出' then -amount
               else 0 end)                             as balance
     , sum(if(expenditure_income = '收入', amount, 0)) as income
     , sum(if(expenditure_income = '支出', amount, 0)) as expenditure
from transaction
group by month
order by month desc;



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


# 月度支出交易累积占比 -- 带冲账标记
create view monthly_expenditure_cdf as
select cat.month
     , cat.id
     , cat.category
     , cat.amount
     , (cat.amount / tot.expenditure) * 100                                                             as percent
     , sum((cat.amount / tot.expenditure) * 100) over (partition by cat.month order by cat.amount desc) as cdf
     , cat.counterparty
     , cat.goods
from (select *, date_format(time, '%Y-%m') as month
      from transaction cat
      where expenditure_income = '支出'
        and reversed = 0
      order by month desc, amount desc) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;

