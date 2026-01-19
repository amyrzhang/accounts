
create view v_user  as
select
      u.nick_name as name
     , d.dept_name as dept_name
     , p.dept_name as company_name
     , d.tenant_id as tenant_id
    , p.order_num as company_order
    , d.order_num as dept_order
    , u.people_order as people_order
from sys_user u
join sys_dept d on d.dept_id = u.dept_id
join sys_dept p on d.parent_id = p.dept_id
order by d.tenant_id, p.order_num, d.order_num, u.people_order;

# 0.【工资表】核算应发工资
# 基础公司1项，津补贴共计8 项
# 数产公司绩效计算逻辑：performance_salary + performance_salary
# 九章公司绩效计算逻辑：performance_salary + residual_performance_salary + performance_adjustment
create view v_salary as
select id
     , tenant_id
     , month
     , name
     , base_salary+
       education_allowance+skill_allowance+
       seniority_allowance+communication_allowance+
       duty_allowance+dietary_allowance+
       hygiene_allowance+property_allowance+
       performance_deduction+performance_salary as salary
from dpm.dpm_staff_salary;


# 1.【员工当期成本模型】
create view v_employee_cost as
select s.id
     , s.tenant_id
     , s.month
     , s.name
     , s.salary  # 应发工资
     , ss.pension_company  # 单位支付养老保险
     , ss.unemployment_company  # 单位支付失业保险
     , ss.work_injury_company  # 单位支付工伤保险
     , ss.housing_fund_company  # 单位支付公积金
     , ss.medical_insurance_company  # 单位支付医疗保险
     , ea.company_annuity  # 单位部分企业年金
     , uf.union_fund  # 工会经费
from v_salary s
left join dpm_staff_social_security ss
    on s.tenant_id=ss.tenant_id and s.month=ss.month and s.name=ss.name
left join dpm_staff_enterprise_annuity ea
    on s.tenant_id=ea.tenant_id and s.month=ea.month and s.name=ea.name
left join dpm_staff_union_fund uf
    on s.tenant_id=uf.tenant_id and s.month=uf.month and s.name=uf.name;



# 2.【研发费用分摊表】
create view v_rd_expense_apportionment as
with hour_rate as (select d.id                                                             as hour_id
                        , d.tenant_id
                        , date_format(d.date, '%Y-%m')                                     as `year_month`
                        , case
                              when d.fee_type = 1 then '研发支出'
                              when d.fee_type = 2 then '项目成本' end                      as expense_type
                        , p.name                                                           as project_name
                        , case
                              when d.fee_type = 1 and d.staff_type = 1 then '研发人员'
                              when d.fee_type = 1 and d.staff_type = 2 then '辅助人员' end as employee_type
                        , d.staff_name                                                     as employee_name
                        , d.workday                                                        as hours
                        , w.hours                                                          as total_hours
                        , d.workday / w.hours                                              as hour_rate
                   from dpm_details d # 工时表
    join dpm_project p  # 关联项目名称
      on d.project_id=p.id
    join (
        select distinct date, hours
        from dpm_workday
    ) w  on w.date=d.date  # 获取当月工作日天数，各租户分别记录，需要去重
)
select h.tenant_id
     , `year_month`
     , expense_type
     , project_name
     , employee_type
     , employee_name
     , round(ec.salary * hours / total_hours, 2)                    as gross_salary_amount
     , round(ec.pension_company * hours / total_hours, 2)           as pension_insurance_amount
     , round(ec.unemployment_company * hours / total_hours, 2)      as unemployment_insurance_amount
     , round(ec.work_injury_company * hours / total_hours, 2)       as work_injury_company_amount
     , round(ec.housing_fund_company * hours / total_hours, 2)      as housing_provident_fund_amount
     , round(ec.medical_insurance_company * hours / total_hours, 2) as medical_insurance_amount
     , round(ec.company_annuity * hours / total_hours, 2)           as enterprise_annuity_amount
     , round(ec.union_fund * hours / total_hours, 2)                as labor_union_fund_amount
     , hours  # 留个标记，方便筛选
     , total_hours
     , hour_rate
from hour_rate h  # 工时表
join v_employee_cost ec  # 人工成本模型
  on h.tenant_id=ec.tenant_id and `year_month`=ec.month and h.employee_name=ec.name
;

# 3. 【待分摊池】
drop view if exists v_pending_allocation_pool;
create view v_pending_allocation_pool as
select ec.tenant_id
     , ec.month                                                                        as `year_month`
     , if(dept_name in ('市场运营部', '市场拓展部', '市场部'), '销售费用', '管理费用') as expense_type
     , ec.name                                                                         as employee_name
     , ec.salary - coalesce(rea.gross_salary_amount, 0)                                as gross_salary_amount
     , ec.pension_company - coalesce(rea.pension_insurance_amount, 0)                  as pension_insurance_amount
     , ec.unemployment_company - coalesce(rea.unemployment_insurance_amount, 0)        as unemployment_insurance_amount
     , ec.work_injury_company - coalesce(rea.work_injury_company_amount, 0)            as work_injury_company_amount
     , ec.housing_fund_company - coalesce(rea.housing_provident_fund_amount, 0)        as housing_provident_fund_amount
     , ec.medical_insurance_company - coalesce(rea.medical_insurance_amount, 0)        as medical_insurance_amount
     , ec.company_annuity - coalesce(rea.enterprise_annuity_amount, 0)                 as enterprise_annuity_amount
     , ec.union_fund - coalesce(rea.labor_union_fund_amount, 0)                        as labor_union_fund_amount
from v_employee_cost ec
left join (select tenant_id
             , `year_month`
             , employee_name
             , sum(gross_salary_amount)           as gross_salary_amount
             , sum(pension_insurance_amount)      as pension_insurance_amount
             , sum(unemployment_insurance_amount) as unemployment_insurance_amount
             , sum(work_injury_company_amount)    as work_injury_company_amount
             , sum(housing_provident_fund_amount) as housing_provident_fund_amount
             , sum(medical_insurance_amount)      as medical_insurance_amount
             , sum(enterprise_annuity_amount)     as enterprise_annuity_amount
             , sum(labor_union_fund_amount)       as labor_union_fund_amount
             , sum(hours)                         as hours
             , avg(total_hours)                   as total_hours
        from v_rd_expense_apportionment
        group by tenant_id, `year_month`, employee_name) rea
   on ec.tenant_id = rea.tenant_id and ec.month = rea.year_month and ec.name = rea.employee_name
left join v_user vu on rea.tenant_id = vu.tenant_id and ec.name = vu.name
where hours is null or hours < total_hours   # 过滤掉纯研发人员
;

# 4.【人工成本分配表】
# drop view if exists v_labor_cost_allocation;
create view v_labor_cost_allocation as
with expense_detail as (
    select tenant_id
     , `year_month`
     , expense_type
     , project_name
     , employee_type
     , employee_name
     , gross_salary_amount
     , pension_insurance_amount
     , unemployment_insurance_amount
     , work_injury_company_amount
     , housing_provident_fund_amount
     , medical_insurance_amount
     , enterprise_annuity_amount
     , labor_union_fund_amount
from v_rd_expense_apportionment

union all

select tenant_id
     , `year_month`
     ,expense_type
     , null                                                                            as project_name
     , null                                                                            as employee_type
     , employee_name
     , gross_salary_amount
     , pension_insurance_amount
     , unemployment_insurance_amount
     , work_injury_company_amount
     , housing_provident_fund_amount
     , medical_insurance_amount
     , enterprise_annuity_amount
     , labor_union_fund_amount
from v_pending_allocation_pool
)
select ed.tenant_id
     , ed.`year_month`
     , vu.company_name
     , ed.expense_type
     , ed.project_name
     , ed.employee_type
     , vu.dept_name
     , ed.employee_name
     , ed.gross_salary_amount
     , ed.pension_insurance_amount
     , ed.unemployment_insurance_amount
     , ed.work_injury_company_amount
     , ed.housing_provident_fund_amount
     , ed.medical_insurance_amount
     , ed.enterprise_annuity_amount
     , ed.labor_union_fund_amount
     , slr.base_salary
     , slr.education_allowance
     , slr.skill_allowance
     , slr.seniority_allowance
     , slr.communication_allowance
     , slr.duty_allowance
     , slr.dietary_allowance
     , slr.hygiene_allowance
     , slr.property_allowance
     , slr.performance_deduction
     , slr.residual_performance
     , slr.performance_adjustment
     , slr.performance_salary
     , scr.large_medical_company
     , ant.payment_base as enterprise_annuity_contribution_base
     , fnd.total_salary as gross_salary
from expense_detail ed
left join dpm_staff_salary slr
  on slr.tenant_id=ed.tenant_id and slr.month=ed.year_month and slr.name=ed.employee_name
left join dpm_staff_social_security scr
  on scr.tenant_id=ed.tenant_id and scr.month=ed.year_month and scr.name=ed.employee_name
left join dpm_staff_enterprise_annuity ant
  on ant.tenant_id=ed.tenant_id and ant.month=ed.year_month and ant.name=ed.employee_name
left join dpm_staff_union_fund fnd
  on fnd.tenant_id=ed.tenant_id and fnd.month=ed.year_month and fnd.name=ed.employee_name
left join v_user vu
 on ed.tenant_id=vu.tenant_id and ed.employee_name=vu.name
order by ed.project_name, ed.expense_type, vu.company_order, vu.dept_order, vu.people_order
;

