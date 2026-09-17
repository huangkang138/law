'use client';

import type { LaborRuleDecision } from '@/services/digitalHumanApi';
import styles from './LaborRuleResults.module.css';
import { laborFactLabel } from './LaborDisputeForm';
import { displayLaborCalculationValue } from './laborRuleResultFormatting';

export const LABOR_ISSUE_LABELS: Record<string, string> = {
  wage_arrears: '欠薪核算', probation: '试用期核对', termination: '解除路径',
  economic_compensation: '补偿/赔偿核算',
  overtime_pay: '加班费核算',
};
const CALCULATION_LABELS: Record<string, string> = {
  estimated_arrears: '欠薪估算金额', months: '欠薪月数',
  maximum_probation_months: '法定试用期上限（月）', duration_exceeded: '试用期是否超限',
  salary_floor: '试用期工资下限', salary_below_floor: '试用期工资是否低于下限',
  repeat_probation: '是否重复约定试用期', termination_route: '解除审查路径',
  service_months: '完整工作月数', n_months: '补偿计发月数', salary_base: '补偿工资基数',
  high_salary_cap_applied: '是否适用高工资封顶', compensation: '经济补偿金额',
  damages_or_compensation: '补偿/赔偿金额', multiplier: '赔偿倍数',
  hourly_wage_base: '小时工资基数', workday_overtime_pay: '工作日加班费',
  rest_day_overtime_pay: '休息日加班费', statutory_holiday_overtime_pay: '法定节假日加班费',
  estimated_overtime_pay: '加班费合计', overtime_paid_amount: '已支付加班费',
  estimated_unpaid_overtime_pay: '预计欠付加班费',
};

export default function LaborRuleResults({ decisions }: { decisions: LaborRuleDecision[] }) {
  if (!decisions.length) return null;
  return <section className={styles.results}>
    <strong>规则详情（{decisions.length}项，均需人工复核）</strong>
    {decisions.map((decision) => <article key={decision.issue_tag}>
      <header><b>{LABOR_ISSUE_LABELS[decision.issue_tag] || '待核对事项'}</b><span>{decision.status === 'completed' ? '已完成初步核对' : '等待补充'}</span></header>
      <p>{decision.assessment}</p>
      {Object.keys(decision.calculations).length > 0 && <dl>{Object.entries(decision.calculations).map(([key, value]) => <div key={key}><dt>{CALCULATION_LABELS[key] || '计算项目'}</dt><dd>{displayLaborCalculationValue(key, value)}</dd></div>)}</dl>}
      {decision.missing_facts.length > 0 && <small>缺失事实：{decision.missing_facts.map(laborFactLabel).join('、')}</small>}
      {decision.assumptions.map((item) => <small key={item}>假设：{item}</small>)}
      {decision.warnings.map((item) => <small key={item}>提示：{item}</small>)}
      {decision.manual_review_required && <footer>本项结果仅供初步判断，仍需人工复核。</footer>}
    </article>)}
  </section>;
}
