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
create view account_activity as
with transfer_tb as (select t.id,
                            t.time,
                            t.debit_credit,
                            t.goods,
                            t.amount,
                            t.payment_method,
                            t.counterparty,
                            t.category,
                            t.status,
                            t.type,
                            t.source
                     from transaction t
                              join account_info a on t.counterparty = a.account_name),
     transaction_tb as (select t.id,
                               time,
                               debit_credit,
                               goods,
                               amount,
                               payment_method,
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
                             , '֧��' as debit_credit
                             , goods
                             , amount
                             , payment_method
                             , counterparty
                             , category
                             , status
                             , type
                             , source
                        from transfer_tb
                        union all
                        select id
                             , time
                             , '����'       as debit_credit
                             , goods
                             , amount
                             , counterparty as pay_method
                             , payment_method   as counterparty
                             , category
                             , status
                             , type
                             , source
                        from transfer_tb)
select id,
       time,
       debit_credit,
       counterparty,
       goods,
       amount,
       sum(case
               when debit_credit = '����' then amount
               when debit_credit = '֧��' then -amount
               else 0 end) over (partition by payment_method order by time) as balance,
       payment_method as account_name,
       category,
       status,
       type,
       source
from transaction_tb
order by time desc;




# �ʲ��������
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
             left join (select account_name
                             , min(time)                                       as create_time
                             , max(time)                                       as update_time
                             , sum(case
                                       when debit_credit = '����' then amount
                                       when debit_credit = '֧��' then -amount
                                       else 0 end)                             as balance
                             , sum(if(debit_credit = '����', amount, 0)) as income
                             , sum(if(debit_credit = '֧��', amount, 0)) as expenditure
                        from account_activity
                        group by account_name) t
                       on a.account_name = t.account_name
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


# �¶���֧�������ö��ֵ�����ʣ�����ѣ����ηѣ���Ϣ������
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
      from transaction
      group by month) tb
order by month;



# �¶ȷ����֧��
create view monthly_exp_category as
select cat.month,
       cat.category,
       cat.amount,
       (cat.amount / tot.expenditure) * 100 as percent
from (select date_format(time, '%Y-%m') as month
           , category
           , sum(amount)                as amount
      from money_track.transaction cat
      where debit_credit = '֧��'
      group by month, category) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;


# �¶�֧�������ۻ�ռ�� -- �����˱��
create view monthly_exp_cdf as
select cat.id
     , cat.month
     , cat.category
     , cat.amount
     , (cat.amount / tot.expenditure) * 100                                                             as percent
     , sum((cat.amount / tot.expenditure) * 100) over (partition by cat.month order by cat.amount desc) as cdf
     , cat.counterparty
     , cat.goods
from (select *, date_format(time, '%Y-%m') as month
      from transaction cat
      where debit_credit = '֧��'
      order by month desc, amount desc) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;

