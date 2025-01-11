SELECT
    a.account_name
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
                     where pay_method regexp '^\\([0-9]{4}\\)$' # ���ո����˻��������п��жϡ�ת�ˡ�
                       and counterparty regexp '^\\([0-9]{4}\\)$'),
     spending_tb as (select *
                     from money_track.transaction
                     where not (pay_method regexp '^\\([0-9]{4}\\)$'
                         and counterparty regexp '^\\([0-9]{4}\\)$')), # ��ֵ�޷�ƥ��
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

# �ʲ��������
create view account_balance as
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
from asset_balance
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
select date_format(time, '%Y-%m')                      as month
     , sum(case
               when expenditure_income = '����' then amount
               when expenditure_income = '֧��' then -amount
               else 0 end)                             as balance
     , sum(if(expenditure_income = '����', amount, 0)) as income
     , sum(if(expenditure_income = '֧��', amount, 0)) as expenditure
from transaction
group by month
order by month desc;



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

