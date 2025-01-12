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
    `reversed`           tinyint(1)     NOT NULL DEFAULT '0',
    `amount`             decimal(10, 2) NOT NULL,
    `pay_method`         varchar(20)    NOT NULL,
    `processed_amount`   decimal(10, 2)          DEFAULT '0.00',
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  AUTO_INCREMENT = 388
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;

# ��ʷ���
# INSERT INTO transaction (time, source, expenditure_income, counterparty, pay_method, amount, category, goods)
# VALUES ('2024-06-30 21:28:17', '�ֹ�', '����', '', '�������д��(4827)',  675.72, '��ʷ���', '��ʷ���');

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

SELECT a.account_name
     , account_type
     , t.balance
     , t.balance as total
FROM account_info a
         left join (SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY pay_method ORDER BY time DESC) AS rn
                    FROM card_transaction) t on a.account_name = t.pay_method
WHERE a.is_active = 1
  and a.is_included = 1
  and t.rn = 1;



# �����
create view card_balance as
with transfer_tb as (select *
                     from money_track.transaction
                     where pay_method regexp '^.{2}���д��\\([0-9]{4}\\)$' # ���ո����˻��������п��жϡ�ת�ˡ�
                       and counterparty regexp '^.{2}���д��\\([0-9]{4}\\)$'),
     spending_tb as (select *
                     from money_track.transaction
                     where not (pay_method regexp '^.{2}���д��\\([0-9]{4}\\)$'
                         and counterparty regexp '^.{2}���д��\\([0-9]{4}\\)$')), # ��ֵ�޷�ƥ��
     transaction_tb as (select *
                        from spending_tb
                        union all
                        select id
                             , time
                             , source
                             , '֧��' as expenditure_income
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
                             , '����'       as expenditure_income
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
               when expenditure_income = '����' then amount
               when expenditure_income = '֧��' then -amount
               else 0 end) over (partition by pay_method order by time asc) as balance
from transaction_tb;

# �������˻�����
drop view card_balance;
create view card_balance as
with transfer_tb as (select t.id,
                            t.time,
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
                               expenditure_income as exp_income,
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
                             , '֧��' as exp_income
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
                             , '����'       as exp_income
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
       counterparty,
       goods,
       amount,
       sum(case
               when exp_income = '����' then amount
               when exp_income = '֧��' then -amount
               else 0 end) over (partition by pay_method order by time) as balance,
       pay_method,
       category,
       status,
       type,
       source
from transaction_tb
order by time
;




# �ʲ��������
create view account__balance as
select a.id
     , a.account_name
     , a.account_type
     , t.balance
     , t.income
     , t.expenditure
     , t.create_time
     , t.update_time
     , a.is_active
     , a.is_included
from account_info a
         left join (select pay_method
                         , min(time)                                       as create_time
                         , max(time)                                       as update_time
                         , sum(case
                                   when expenditure_income = '����' then amount
                                   when expenditure_income = '֧��' then -amount
                                   else 0 end)                             as balance
                         , sum(if(expenditure_income = '����', amount, 0)) as income
                         , sum(if(expenditure_income = '֧��', amount, 0)) as expenditure
                    from card_transaction
                    group by pay_method) t
                   on a.account_name = t.pay_method
order by account_type desc, balance desc
;

# ��ѯ�ʲ����
select account_type
     , sum(balance)     as tot_balance
     , sum(income)      as tot_income
     , sum(expenditure) as tot_expenditure
     , max(update_time) as update_time
from account_balance
where is_active = 1
  and is_included = 1
group by account_type;

# �¶ȿ����˵� - ����У�����ݶ���
# TODO: �����ƣ��������޽��ף��޷���ȡ��������
create view monthly_card_balance as
select date_format(time, '%Y-%m')                      as month
     , pay_method                                      as card
     , sum(case
               when expenditure_income = '����' then amount
               when expenditure_income = '֧��' then -amount
               else 0 end)                             as balance
     , sum(if(expenditure_income = '����', amount, 0)) as income
     , sum(if(expenditure_income = '֧��', amount, 0)) as expenditure
from card_transaction
group by month, pay_method
order by month desc, pay_method desc;



# �¶���֧���˵� - ����ͳ���¶���֧
create view monthly_balance as
select month,
       balance,
       salary,
       tb.salary - tb.balance as consumption,
       income,
       expenditure
from (select date_format(time, '%Y-%m')                      as month
           , sum(case
                     when expenditure_income = '����' then amount
                     when expenditure_income = '֧��' then -amount
                     else 0 end)                             as balance
           , sum(case
                     when expenditure_income = '����' and goods rlike '����|�����|���η�' then amount
                     else 0 end)                             as salary
           , sum(if(expenditure_income = '����', amount, 0)) as income
           , sum(if(expenditure_income = '֧��', amount, 0)) as expenditure
      from transaction
      group by month) tb
order by month;



# �¶ȷ����֧��
create view monthly_expenditure_category as
select cat.month,
       cat.category,
       cat.amount,
       (cat.amount / tot.expenditure) * 100 as precent
from (select date_format(time, '%Y-%m') as month
           , category
           , sum(amount)                as amount
      from money_track.transaction cat
      where expenditure_income = '֧��'
      group by month, category) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;


# �¶�֧�������ۻ�ռ�� -- �����˱��
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
      where expenditure_income = '֧��'
        and reversed = 0
      order by month desc, amount desc) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;

