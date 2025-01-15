# 收支记录表
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
    `reversed`           tinyint(1)     NOT NULL DEFAULT '0',
    `amount`             decimal(10, 2) NOT NULL,
    `pay_method`         varchar(20)    NOT NULL,
    `processed_amount`   decimal(10, 2)          DEFAULT '0.00',
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  AUTO_INCREMENT = 388
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;


# 资产信息表
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


# 卡余额，用账户表关联
create view card_balance as
with transfer_tb as (select t.id,
                            t.time,
                            t.expenditure_income,
                            t.goods,
                            t.amount,
                            t.pay_method,
                            t.counterparty,
                            t.category,
                            t.status,
                            t.type,
                            t.source
                     from transaction t
                              join account_info a on t.counterparty = a.account_name),
     transaction_tb as (select t.id,
                               time,
                               expenditure_income,
                               goods,
                               amount,
                               pay_method,
                               counterparty,
                               category,
                               status,
                               type,
                               source
                        from transaction t
                                 left join account_info a on t.counterparty = a.account_name
                        where a.account_name is null
                        union all
                        select `id`
                             , time
                             , '支出' as expenditure_income
                             , goods
                             , amount
                             , pay_method
                             , counterparty
                             , category
                             , status
                             , type
                             , source
                        from transfer_tb
                        union all
                        select id
                             , time
                             , '收入'       as expenditure_income
                             , goods
                             , amount
                             , counterparty as pay_method
                             , pay_method   as counterparty
                             , category
                             , status
                             , type
                             , source
                        from transfer_tb)
select id,
       time,
       expenditure_income as exp_income,
       counterparty,
       goods,
       amount,
       sum(case
               when expenditure_income = '收入' then amount
               when expenditure_income = '支出' then -amount
               else 0 end) over (partition by pay_method order by time) as balance,
       pay_method,
       category,
       status,
       type,
       source
from transaction_tb
order by time desc;




# 资产余额表更新
create view account_balance as
with base_tb as (
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
             left join (select pay_method
                             , min(time)                                       as create_time
                             , max(time)                                       as update_time
                             , sum(case
                                       when exp_income = '收入' then amount
                                       when exp_income = '支出' then -amount
                                       else 0 end)                             as balance
                             , sum(if(exp_income = '收入', amount, 0)) as income
                             , sum(if(exp_income = '支出', amount, 0)) as expenditure
                        from card_balance
                        group by pay_method) t
                       on a.account_name = t.pay_method
    where is_active = 1
    order by account_type desc, balance desc
)
select max(id) as id
      , '' as account_name
      , '' as account_type
      , sum(if(is_included=1, balance, 0)) as balance
      , sum(if(is_included=1, income, 0)) as credit
      , sum(if(is_included=1, expenditure, 0)) as debit
      , max(create_time) as create_time
     , max(update_time) as update_time
     , sum(is_included) as is_included
from base_tb
union all
select *
from base_tb;


# 月度收支，收入的枚举值：工资，劳务费，讲课费，结息，收益
drop view if exists monthly_balance;
create view monthly_balance as
select month
       , balance
       , income
       , tb.income - tb.balance as expenditure
       , credit
       , debit
from (select date_format(time, '%Y-%m')                      as month
           , sum(case
                     when expenditure_income = '收入' then amount
                     when expenditure_income = '支出' then -amount
                     else 0 end)                             as balance
           , sum(case
                     when expenditure_income = '收入' and goods rlike '工资|劳务费|讲课费|结息|收益|兼职' then amount
                     else 0 end)                             as income
           , sum(if(expenditure_income = '收入', amount, 0)) as credit
           , sum(if(expenditure_income = '支出', amount, 0)) as debit
      from transaction
      group by month) tb
order by month;



# 月度分类别支出
create view monthly_exp_category as
select cat.month,
       cat.category,
       cat.amount,
       (cat.amount / tot.expenditure) * 100 as percent
from (select date_format(time, '%Y-%m') as month
           , category
           , sum(amount)                as amount
      from money_track.transaction cat
      where expenditure_income = '支出'
      group by month, category) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;


# 月度支出交易累积占比 -- 带冲账标记
create view monthly_exp_cdf as
select cat.id
     , cat.month
     , cat.expenditure_income as exp_income
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

