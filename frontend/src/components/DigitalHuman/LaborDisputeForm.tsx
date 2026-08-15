'use client';

import styles from './LaborDisputeForm.module.css';

export interface LaborDisputeFormValue {
  employee_name: string;
  employer_name: string;
  employment_start_date: string;
  termination_date: string;
  limitation_start_date: string;
  work_location: string;
  claim_types: string;
  demands: string;
  employment_active: string;
  limitation_interruption_dates: string;
  limitation_suspension_days: string;
  wage_arrears_amount: string;
  wage_arrears_months: string;
  wage_arrears_start_date: string;
  wage_arrears_end_date: string;
  wages_paid_through: string;
  wage_payment_day: string;
  attendance_days: string;
  contract_term_type: string;
  contract_term_months: string;
  probation_period_months: string;
  probation_salary: string;
  regular_salary: string;
  local_minimum_wage: string;
  prior_probation_with_same_employer: string;
  termination_reason: string;
  termination_initiator: string;
  termination_basis: string;
  termination_notice_date: string;
  notice_period_days: string;
  union_notified: string;
  protected_statuses: string;
  local_average_monthly_salary: string;
  compensation_kind: string;
  working_hours_system: string;
  overtime_monthly_wage_base: string;
  overtime_workday_hours: string;
  overtime_rest_day_hours: string;
  overtime_statutory_holiday_hours: string;
  rest_day_compensatory_leave_hours: string;
  overtime_paid_amount: string;
}

export const EMPTY_LABOR_DISPUTE_FORM: LaborDisputeFormValue = {
  employee_name: '', employer_name: '', employment_start_date: '', termination_date: '',
  limitation_start_date: '', work_location: '', claim_types: '', demands: '',
  employment_active: '', limitation_interruption_dates: '', limitation_suspension_days: '0',
  wage_arrears_amount: '', wage_arrears_months: '', wage_arrears_start_date: '',
  wage_arrears_end_date: '', wages_paid_through: '', wage_payment_day: '', attendance_days: '',
  contract_term_type: '', contract_term_months: '', probation_period_months: '',
  probation_salary: '', regular_salary: '', local_minimum_wage: '',
  prior_probation_with_same_employer: '', termination_reason: '', termination_initiator: '',
  termination_basis: '', termination_notice_date: '', notice_period_days: '', union_notified: '',
  protected_statuses: '', local_average_monthly_salary: '', compensation_kind: '',
  working_hours_system: '', overtime_monthly_wage_base: '', overtime_workday_hours: '',
  overtime_rest_day_hours: '', overtime_statutory_holiday_hours: '',
  rest_day_compensatory_leave_hours: '', overtime_paid_amount: '',
};

const NUMBER_FIELDS: Array<keyof LaborDisputeFormValue> = [
  'limitation_suspension_days', 'wage_arrears_amount', 'wage_arrears_months',
  'wage_payment_day', 'attendance_days', 'contract_term_months', 'probation_period_months',
  'probation_salary', 'regular_salary', 'local_minimum_wage', 'notice_period_days',
  'local_average_monthly_salary', 'overtime_monthly_wage_base', 'overtime_workday_hours',
  'overtime_rest_day_hours', 'overtime_statutory_holiday_hours',
  'rest_day_compensatory_leave_hours', 'overtime_paid_amount',
];
const BOOLEAN_FIELDS: Array<keyof LaborDisputeFormValue> = [
  'employment_active', 'prior_probation_with_same_employer', 'union_notified',
];
const LIST_FIELDS: Array<keyof LaborDisputeFormValue> = [
  'claim_types', 'limitation_interruption_dates', 'protected_statuses',
];

function splitValues(value: string): string[] {
  return value.split(/[、,，\n]/).map((item) => item.trim()).filter(Boolean);
}

export function buildLaborDisputePayload(
  value: LaborDisputeFormValue,
  monthlySalary: string,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  Object.entries(value).forEach(([key, raw]) => {
    if (raw === '') return;
    const field = key as keyof LaborDisputeFormValue;
    if (NUMBER_FIELDS.includes(field)) payload[key] = Number(raw);
    else if (BOOLEAN_FIELDS.includes(field)) payload[key] = raw === 'true';
    else if (LIST_FIELDS.includes(field)) payload[key] = splitValues(raw);
    else payload[key] = raw;
  });
  if (monthlySalary !== '') payload.monthly_salary = Number(monthlySalary);
  return payload;
}

export function mergeLaborSuggestions(
  current: LaborDisputeFormValue,
  suggested: Record<string, unknown>,
): LaborDisputeFormValue {
  const next = { ...current };
  (Object.keys(next) as Array<keyof LaborDisputeFormValue>).forEach((field) => {
    const suggestion = suggested[field];
    if (suggestion === undefined || suggestion === null || suggestion === '') return;
    next[field] = Array.isArray(suggestion) ? suggestion.join('、') : String(suggestion);
  });
  return next;
}

const MISSING_LABELS: Record<string, string> = {
  employee_name: '申请人姓名', employer_name: '用人单位', employment_start_date: '入职日期',
  monthly_salary: '月工资', work_location: '工作地点', claim_types: '争议类型', demands: '仲裁请求',
  limitation_start_date: '权利受损日期', wage_arrears_amount_or_salary_and_months: '欠薪总金额',
  wage_arrears_period: '欠薪开始日期', probation_period_months: '试用期月数', contract_term: '合同期限',
  termination_reason: '解除原因', termination_initiator: '解除提出方', termination_date: '解除日期',
  compensation_kind: '补偿或赔偿类型', local_average_monthly_salary: '当地上年度职工月平均工资',
  valid_employment_period: '有效工作期间',
  working_hours_system: '工时制度', standard_working_hours_system_required: '非标准工时审批材料和计算周期',
  overtime_wage_base: '加班费月工资基数', overtime_hours_by_type: '各类加班小时数',
};

export function laborFactLabel(field: string): string {
  return MISSING_LABELS[field] || field;
}

export function humanizeLaborMessage(message: string): string {
  return Object.entries(MISSING_LABELS)
    .sort(([left], [right]) => right.length - left.length)
    .reduce((text, [field, label]) => text.replaceAll(field, label), message);
}

const BASE_REQUIRED_FACTS = [
  'employee_name', 'employer_name', 'employment_start_date', 'monthly_salary',
  'work_location', 'claim_types', 'demands', 'limitation_start_date',
];

export function findMissingLaborDisputeFacts(
  value: LaborDisputeFormValue,
  monthlySalary: string,
): string[] {
  const claims = splitValues(value.claim_types);
  const has = (terms: string[]) => claims.some((claim) => terms.some((term) => claim.includes(term)));
  const missing = BASE_REQUIRED_FACTS.filter((field) => {
    if (field === 'monthly_salary') return monthlySalary === '';
    return value[field as keyof LaborDisputeFormValue] === '';
  });
  if (has(['欠薪', '工资', '劳动报酬'])) {
    if (value.wage_arrears_amount === '') {
      missing.push('wage_arrears_amount_or_salary_and_months');
    }
    if (value.wage_arrears_start_date === '') {
      missing.push('wage_arrears_period');
    }
  }
  if (has(['解除', '辞退', '解雇'])) {
    if (value.termination_date === '') missing.push('termination_date');
    if (value.termination_reason === '') missing.push('termination_reason');
    if (value.termination_initiator === '') missing.push('termination_initiator');
  }
  if (has(['补偿', '赔偿']) && value.local_average_monthly_salary === '') {
    missing.push('local_average_monthly_salary');
  }
  if (has(['加班'])) {
    if (value.working_hours_system === '') missing.push('working_hours_system');
    else if (value.working_hours_system !== 'standard') missing.push('standard_working_hours_system_required');
    if (monthlySalary === '' && value.overtime_monthly_wage_base === '') missing.push('overtime_wage_base');
    const overtimeHours = [
      value.overtime_workday_hours,
      value.overtime_rest_day_hours,
      value.overtime_statutory_holiday_hours,
    ].reduce((total, raw) => total + Number(raw || 0), 0);
    if (overtimeHours <= 0) missing.push('overtime_hours_by_type');
  }
  if (has(['试用期'])) {
    if (value.probation_period_months === '') missing.push('probation_period_months');
    if (value.contract_term_type === '' || (
      value.contract_term_type !== 'open_ended' && value.contract_term_months === ''
    )) missing.push('contract_term');
  }
  return Array.from(new Set(missing));
}

interface Props {
  value: LaborDisputeFormValue;
  monthlySalary: string;
  missingFacts: string[];
  disabled?: boolean;
  // 橙色缺失态门控：仅在校验真正触发（提交尝试 / Agent 定位缺失）时点亮，
  // 未填写的必填项平时只显示红色 *，避免表单持续"报警"。
  highlightMissing?: boolean;
  onChange: (value: LaborDisputeFormValue) => void;
  onMonthlySalaryChange: (value: string) => void;
}

export default function LaborDisputeForm({
  value, monthlySalary, missingFacts, disabled = false, highlightMissing = false,
  onChange, onMonthlySalaryChange,
}: Props) {
  const claims = splitValues(value.claim_types);
  const has = (terms: string[]) => claims.some((claim) => terms.some((term) => claim.includes(term)));
  const showWage = has(['欠薪', '工资', '劳动报酬']);
  const showProbation = has(['试用期']);
  const showTermination = has(['解除', '辞退', '解雇']);
  const showCompensation = has(['补偿', '赔偿']);
  const showOvertime = has(['加班']);
  const missing = new Set(missingFacts);
  const required = new Set([
    ...BASE_REQUIRED_FACTS,
    ...(showWage ? ['wage_arrears_amount_or_salary_and_months', 'wage_arrears_period'] : []),
    ...(showTermination ? ['termination_date', 'termination_reason', 'termination_initiator'] : []),
    ...(showCompensation ? ['local_average_monthly_salary'] : []),
    ...(showOvertime ? ['working_hours_system'] : []),
    ...(showProbation ? ['probation_period_months', 'contract_term'] : []),
  ]);
  const set = (field: keyof LaborDisputeFormValue, next: string) => onChange({ ...value, [field]: next });
  const fieldClass = (fields: string[]) => [
    // 橙色边框/黄底只在校验触发后出现，让警告色真正具有定位问题的意义。
    highlightMissing && fields.some((field) => missing.has(field)) ? styles.missing : '',
    fields.some((field) => required.has(field)) ? styles.required : '',
  ].filter(Boolean).join(' ');

  return <div className={styles.form}>
    <div className={styles.guide}>
      <span><b>*</b> 必填</span>
      <span>没有星号的项目均可留空</span>
    </div>
    {missingFacts.length > 0 && <section className={styles.missingSummary}>
      <strong>当前还缺 {missingFacts.length} 项必填信息</strong>
      <p>{missingFacts.map(laborFactLabel).join('、')}</p>
    </section>}

    <fieldset className={styles.wide}>
      <legend>基础事实</legend>
      <div className={styles.grid2}>
        <label className={fieldClass(['employee_name'])}>申请人姓名<input disabled={disabled} value={value.employee_name} onChange={(e) => set('employee_name', e.target.value)} /></label>
        <label className={fieldClass(['employer_name'])}>用人单位<input disabled={disabled} value={value.employer_name} onChange={(e) => set('employer_name', e.target.value)} /></label>
        <label className={fieldClass(['employment_start_date'])}>入职日期<input type="date" disabled={disabled} value={value.employment_start_date} onChange={(e) => set('employment_start_date', e.target.value)} /></label>
        <label className={fieldClass(['termination_date', 'valid_employment_period'])}>解除/终止日期<input type="date" disabled={disabled} value={value.termination_date} onChange={(e) => set('termination_date', e.target.value)} /></label>
        <label className={fieldClass(['limitation_start_date'])}>知道权利受损日期<input type="date" disabled={disabled} value={value.limitation_start_date} onChange={(e) => set('limitation_start_date', e.target.value)} /></label>
        <label className={fieldClass(['monthly_salary'])}>离职前十二个月平均工资<input type="number" min="0" disabled={disabled} value={monthlySalary} onChange={(e) => onMonthlySalaryChange(e.target.value)} /></label>
        <label className={fieldClass(['work_location'])}>实际工作地点<input disabled={disabled} value={value.work_location} onChange={(e) => set('work_location', e.target.value)} /></label>
        <label>劳动关系是否仍存续<select disabled={disabled} value={value.employment_active} onChange={(e) => set('employment_active', e.target.value)}><option value="">请选择</option><option value="true">是</option><option value="false">否</option></select></label>
      </div>
      <label className={fieldClass(['claim_types'])}>争议类型（顿号分隔）<input disabled={disabled} value={value.claim_types} onChange={(e) => set('claim_types', e.target.value)} placeholder="欠薪、加班费、试用期、违法解除、赔偿金" /></label>
      <label className={fieldClass(['demands'])}>具体仲裁请求<textarea rows={3} disabled={disabled} value={value.demands} onChange={(e) => set('demands', e.target.value)} /></label>
      <details>
        <summary>时效中断或中止（没有可不填）</summary>
        <div className={styles.grid2}>
          <label>中断日期（顿号分隔）<input disabled={disabled} value={value.limitation_interruption_dates} onChange={(e) => set('limitation_interruption_dates', e.target.value)} placeholder="2026-06-15、2026-06-30" /></label>
          <label>中止天数<input type="number" min="0" disabled={disabled} value={value.limitation_suspension_days} onChange={(e) => set('limitation_suspension_days', e.target.value)} /></label>
        </div>
      </details>
    </fieldset>

    {showWage && <fieldset>
      <legend>欠薪事实</legend>
      <p className={styles.sectionHelp}>填写公司拖欠的工资总额，以及第一笔欠薪对应月份的开始日期。</p>
      <div className={styles.grid2}>
        <label className={fieldClass(['wage_arrears_amount_or_salary_and_months'])}>欠薪总金额<input type="number" min="0" disabled={disabled} value={value.wage_arrears_amount} onChange={(e) => set('wage_arrears_amount', e.target.value)} placeholder="例如：17400" /></label>
        <label>欠薪月数（选填）<input type="number" min="1" disabled={disabled} value={value.wage_arrears_months} onChange={(e) => set('wage_arrears_months', e.target.value)} placeholder="例如：2" /></label>
        <label className={fieldClass(['wage_arrears_period'])}>欠薪开始日期<input type="date" disabled={disabled} value={value.wage_arrears_start_date} onChange={(e) => set('wage_arrears_start_date', e.target.value)} /></label>
        <label>欠薪结束日期（选填）<input type="date" disabled={disabled} value={value.wage_arrears_end_date} onChange={(e) => set('wage_arrears_end_date', e.target.value)} /></label>
        <label>此前工资支付到哪天（选填）<input type="date" disabled={disabled} value={value.wages_paid_through} onChange={(e) => set('wages_paid_through', e.target.value)} /></label>
        <label>每月约定发薪日（选填）<input type="number" min="1" max="31" disabled={disabled} value={value.wage_payment_day} onChange={(e) => set('wage_payment_day', e.target.value)} placeholder="例如：10" /></label>
        <label>欠薪期间实际出勤天数（选填）<input type="number" min="0" max="366" disabled={disabled} value={value.attendance_days} onChange={(e) => set('attendance_days', e.target.value)} /></label>
      </div>
    </fieldset>}

    {showOvertime && <fieldset>
      <legend>加班费事实</legend>
      <p className={styles.sectionHelp}>请至少填写一种实际发生的加班时数；没有发生的类型可以留空或填 0。</p>
      <div className={styles.grid2}>
        <label className={fieldClass(['working_hours_system', 'standard_working_hours_system_required'])}>工时制度<select disabled={disabled} value={value.working_hours_system} onChange={(e) => set('working_hours_system', e.target.value)}><option value="">请选择</option><option value="standard">标准工时制</option><option value="comprehensive">综合计算工时制</option><option value="flexible">不定时工作制</option><option value="unknown">不确定</option></select></label>
        <label className={fieldClass(['overtime_wage_base'])}>加班费月工资基数<input type="number" min="0" disabled={disabled} value={value.overtime_monthly_wage_base} onChange={(e) => set('overtime_monthly_wage_base', e.target.value)} placeholder="不填则暂按月工资" /></label>
        <label>工作日加班小时<input type="number" min="0" step="0.5" disabled={disabled} value={value.overtime_workday_hours} onChange={(e) => set('overtime_workday_hours', e.target.value)} /></label>
        <label>休息日加班小时<input type="number" min="0" step="0.5" disabled={disabled} value={value.overtime_rest_day_hours} onChange={(e) => set('overtime_rest_day_hours', e.target.value)} /></label>
        <label>法定节假日加班小时<input type="number" min="0" step="0.5" disabled={disabled} value={value.overtime_statutory_holiday_hours} onChange={(e) => set('overtime_statutory_holiday_hours', e.target.value)} /></label>
        <label>休息日已补休小时<input type="number" min="0" step="0.5" disabled={disabled} value={value.rest_day_compensatory_leave_hours} onChange={(e) => set('rest_day_compensatory_leave_hours', e.target.value)} /></label>
        <label>已支付加班费<input type="number" min="0" disabled={disabled} value={value.overtime_paid_amount} onChange={(e) => set('overtime_paid_amount', e.target.value)} /></label>
      </div>
      <small>自动估算仅适用于标准工时制；综合计算工时制、不定时工作制需结合审批文件和当地规则人工核算。</small>
    </fieldset>}

    {showProbation && <fieldset>
      <legend>试用期事实</legend>
      <div className={styles.grid2}>
        <label className={fieldClass(['contract_term'])}>合同期限类型<select disabled={disabled} value={value.contract_term_type} onChange={(e) => set('contract_term_type', e.target.value)}><option value="">请选择</option><option value="fixed">固定期限</option><option value="open_ended">无固定期限</option><option value="task_based">以完成任务为期限</option></select></label>
        <label className={fieldClass(['contract_term'])}>合同期限（月）<input type="number" min="1" disabled={disabled} value={value.contract_term_months} onChange={(e) => set('contract_term_months', e.target.value)} /></label>
        <label className={fieldClass(['probation_period_months'])}>约定试用期（月）<input type="number" min="0" max="12" disabled={disabled} value={value.probation_period_months} onChange={(e) => set('probation_period_months', e.target.value)} /></label>
        <label>试用期工资<input type="number" min="0" disabled={disabled} value={value.probation_salary} onChange={(e) => set('probation_salary', e.target.value)} /></label>
        <label>转正工资<input type="number" min="0" disabled={disabled} value={value.regular_salary} onChange={(e) => set('regular_salary', e.target.value)} /></label>
        <label>当地最低工资<input type="number" min="0" disabled={disabled} value={value.local_minimum_wage} onChange={(e) => set('local_minimum_wage', e.target.value)} /></label>
        <label>同一单位是否约定过试用期<select disabled={disabled} value={value.prior_probation_with_same_employer} onChange={(e) => set('prior_probation_with_same_employer', e.target.value)}><option value="">不确定</option><option value="true">是</option><option value="false">否</option></select></label>
      </div>
    </fieldset>}

    {showTermination && <fieldset>
      <legend>解除事实</legend>
      <div className={styles.grid2}>
        <label className={fieldClass(['termination_initiator'])}>解除提出方<select disabled={disabled} value={value.termination_initiator} onChange={(e) => set('termination_initiator', e.target.value)}><option value="">请选择</option><option value="employer">用人单位</option><option value="employee">劳动者</option><option value="mutual">协商一致</option><option value="expiry">合同到期</option><option value="unknown">暂不确定</option></select></label>
        <label className={fieldClass(['termination_reason'])}>解除原因<input disabled={disabled} value={value.termination_reason} onChange={(e) => set('termination_reason', e.target.value)} /></label>
        <label>单位主张的法律或制度依据<input disabled={disabled} value={value.termination_basis} onChange={(e) => set('termination_basis', e.target.value)} /></label>
        <label>通知日期<input type="date" disabled={disabled} value={value.termination_notice_date} onChange={(e) => set('termination_notice_date', e.target.value)} /></label>
        <label>提前通知天数<input type="number" min="0" max="365" disabled={disabled} value={value.notice_period_days} onChange={(e) => set('notice_period_days', e.target.value)} /></label>
        <label>是否通知工会<select disabled={disabled} value={value.union_notified} onChange={(e) => set('union_notified', e.target.value)}><option value="">不确定/不适用</option><option value="true">是</option><option value="false">否</option></select></label>
      </div>
      <label>特殊保护状态（顿号分隔）<input disabled={disabled} value={value.protected_statuses} onChange={(e) => set('protected_statuses', e.target.value)} placeholder="孕期、医疗期、工伤" /></label>
    </fieldset>}

    {showCompensation && <fieldset>
      <legend>补偿或赔偿事实</legend>
      <div className={styles.grid2}>
        <label className={fieldClass(['compensation_kind'])}>请求类型<select disabled={disabled} value={value.compensation_kind} onChange={(e) => set('compensation_kind', e.target.value)}><option value="">请选择</option><option value="compensation">经济补偿</option><option value="damages">违法解除赔偿</option></select></label>
        <label className={fieldClass(['local_average_monthly_salary'])}>当地上年度职工月平均工资<input type="number" min="0" disabled={disabled} value={value.local_average_monthly_salary} onChange={(e) => set('local_average_monthly_salary', e.target.value)} /></label>
      </div>
    </fieldset>}
  </div>;
}
