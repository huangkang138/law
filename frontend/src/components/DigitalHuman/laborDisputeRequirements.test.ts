import { strict as assert } from 'node:assert';
import { test } from 'node:test';

import {
  getLaborDisputeRequirements,
  type LaborRequirementValues,
} from './laborDisputeRequirements';

function facts(overrides: Partial<LaborRequirementValues> = {}): LaborRequirementValues {
  return {
    employee_name: '张三',
    employer_name: '某公司',
    employment_start_date: '2024-01-01',
    termination_date: '',
    limitation_start_date: '2026-01-01',
    work_location: '深圳市',
    claim_types: '欠薪',
    demands: '支付拖欠工资',
    employment_active: 'true',
    wage_arrears_amount: '10000',
    wage_arrears_months: '',
    wage_arrears_start_date: '2026-01-01',
    wages_paid_through: '',
    contract_term_type: '',
    contract_term_months: '',
    probation_period_months: '',
    termination_reason: '',
    termination_initiator: '',
    local_average_monthly_salary: '',
    compensation_kind: '',
    working_hours_system: '',
    overtime_workday_hours: '',
    overtime_rest_day_hours: '',
    overtime_statutory_holiday_hours: '',
    ...overrides,
  };
}

test('纯欠薪且劳动关系存续时不要求解除日期', () => {
  const result = getLaborDisputeRequirements(facts(), '8000');
  assert.equal(result.requiredFields.includes('termination_date'), false);
  assert.equal(result.missingFacts.includes('termination_date'), false);
});

test('经济补偿或赔偿要求解除日期、请求类型、当地平均工资和存续状态', () => {
  const result = getLaborDisputeRequirements(facts({
    claim_types: '欠薪、经济补偿、赔偿金',
    employment_active: '',
  }), '8000');
  assert.deepEqual(
    ['termination_date', 'compensation_kind', 'local_average_monthly_salary', 'employment_active']
      .map((field) => result.requiredFields.includes(field)),
    [true, true, true, true],
  );
  assert.deepEqual(
    ['termination_date', 'compensation_kind', 'local_average_monthly_salary', 'employment_active']
      .map((field) => result.missingFacts.includes(field)),
    [true, true, true, true],
  );
});

test('条件必填字段填完后从缺失字段中移除', () => {
  const result = getLaborDisputeRequirements(facts({
    claim_types: '经济补偿',
    termination_date: '2026-01-01',
    employment_active: 'false',
    compensation_kind: '经济补偿',
    local_average_monthly_salary: '5000',
  }), '8000');
  assert.deepEqual(
    ['termination_date', 'employment_active', 'compensation_kind', 'local_average_monthly_salary']
      .map((field) => result.missingFields.includes(field)),
    [false, false, false, false],
  );
});

test('解除争议要求解除日期、原因和提出方', () => {
  const result = getLaborDisputeRequirements(facts({
    claim_types: '违法解除',
    employment_active: 'false',
  }), '8000');
  assert.deepEqual(
    ['termination_date', 'termination_reason', 'termination_initiator']
      .map((field) => result.missingFacts.includes(field)),
    [true, true, true],
  );
});

test('欠薪金额和欠薪期间支持二选一输入', () => {
  const alternative = getLaborDisputeRequirements(facts({
    wage_arrears_amount: '',
    wage_arrears_months: '2',
    wage_arrears_start_date: '',
    wages_paid_through: '2026-01-01',
  }), '8000');
  assert.equal(alternative.missingFacts.includes('wage_arrears_amount_or_salary_and_months'), false);
  assert.equal(alternative.missingFacts.includes('wage_arrears_period'), false);

  const empty = getLaborDisputeRequirements(facts({
    wage_arrears_amount: '',
    wage_arrears_months: '',
    wage_arrears_start_date: '',
    wages_paid_through: '',
  }), '8000');
  assert.equal(empty.missingFacts.includes('wage_arrears_amount_or_salary_and_months'), true);
  assert.equal(empty.missingFacts.includes('wage_arrears_period'), true);
});

test('试用期仅在固定期限合同时要求合同期限月数', () => {
  const openEnded = getLaborDisputeRequirements(facts({
    claim_types: '试用期',
    contract_term_type: 'open_ended',
    probation_period_months: '6',
  }), '8000');
  assert.equal(openEnded.requiredFields.includes('contract_term_months'), false);

  const fixed = getLaborDisputeRequirements(facts({
    claim_types: '试用期',
    contract_term_type: 'fixed',
    probation_period_months: '2',
  }), '8000');
  assert.equal(fixed.requiredFields.includes('contract_term_months'), true);
  assert.equal(fixed.missingFacts.includes('contract_term'), true);
});

test('加班时数为组合必填，填写任意一种即可', () => {
  const empty = getLaborDisputeRequirements(facts({
    claim_types: '加班费',
    working_hours_system: 'standard',
  }), '8000');
  assert.equal(empty.missingFacts.includes('overtime_hours_by_type'), true);
  assert.equal(empty.requiredFields.includes('overtime_workday_hours'), true);

  const supplied = getLaborDisputeRequirements(facts({
    claim_types: '加班费',
    working_hours_system: 'standard',
    overtime_rest_day_hours: '8',
  }), '8000');
  assert.equal(supplied.missingFacts.includes('overtime_hours_by_type'), false);
  assert.equal(supplied.requiredFields.includes('overtime_workday_hours'), false);
});

test('存续劳动关系与解除或补偿诉求冲突时给出明确提示', () => {
  const result = getLaborDisputeRequirements(facts({
    claim_types: '经济补偿',
    employment_active: 'true',
  }), '8000');
  assert.equal(result.conflicts.length, 1);
  assert.equal(result.missingFacts.includes('employment_status_conflict'), true);
});
