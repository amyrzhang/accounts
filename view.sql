# �¶���֧
create view monthly_balance as
select month, income - expenditure as balance, income, expenditure
from (select date_format(time, '%Y-%m')                      as month
           , sum(if(expenditure_income = '����', amount, 0)) as income
           , sum(if(expenditure_income = '֧��', amount, 0)) as expenditure
      from money_track.transaction
      group by month) tb
order by month desc;


# �����
# drop view card_balance;
# create view card_balance as
with transfer_tb as (select time
                          , expenditure_income
                          , counterparty
                          , pay_method
                          , amount
                     from money_track.transaction
                     where pay_method regexp '^.{2}���д��\\([0-9]{4}\\)$' # ���ո����˻��������п��жϡ�ת�ˡ�
                       and counterparty regexp '^.{2}���д��\\([0-9]{4}\\)$'),
     spending_tb as (select time
                          , expenditure_income
                          , counterparty
                          , pay_method
                          , amount
                     from money_track.transaction
                     where not (pay_method regexp '^.{2}���д��\\([0-9]{4}\\)$'
                         and counterparty regexp '^.{2}���д��\\([0-9]{4}\\)$')),
     transaction_tb as (select time, expenditure_income, counterparty, pay_method, amount
                        from spending_tb
                        union all
                        select
                            time
                             , '֧��' as expenditure_income
                             , counterparty
                             , pay_method
                             , amount
                        from transfer_tb
                        union all
                        select
                            time
                             , '����' as expenditure_income
                             , pay_method as counterparty
                             , counterparty as pay_method
                             , amount
                        from transfer_tb)

select date_format(time, '%Y-%m')                      as month
     , pay_method                                      as card
     , sum(case
               when expenditure_income = '����' then amount
               when expenditure_income = '֧��' then -amount
               else 0 end)                             as balance
     , sum(if(expenditure_income = '����', amount, 0)) as income
     , sum(if(expenditure_income = '֧��', amount, 0)) as expenditure
from transaction_tb
group by month, pay_method
order by month desc, pay_method desc;


select *
from transaction
where amount >=1000;


select date_format(time, '%Y-%m') as month,
       sum(case when expenditure_income = '����' then amount
                when expenditure_income = '֧��' then -amount
       else 0 end) as balance,
        sum(if(expenditure_income = '����', amount, 0)) as income,
        sum(if(expenditure_income = '֧��', amount, 0)) as expenditure
from transaction
group by month;

select sum(case when expenditure_income='֧��' then amount else 0 end) as amount
from transaction
where amount >= 1000;


# �¶ȿ����˵�
# select date_format(time, '%Y-%m')                      as month
#      , pay_method                                      as card
#      , sum(case
#                when expenditure_income = '����' then amount
#                when expenditure_income = '֧��' then -amount
#                else 0 end)                             as balance
#      , sum(if(expenditure_income = '����', amount, 0)) as income
#      , sum(if(expenditure_income = '֧��', amount, 0)) as expenditure
# from transaction_tb
# group by month, pay_method
# order by month desc, pay_method desc;






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


# �¶�֧�������ۻ�ռ��
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
      where expenditure_income = '֧��'
      order by month desc, amount desc) cat
         left join monthly_balance tot on cat.month = tot.month
order by month desc, amount desc;

