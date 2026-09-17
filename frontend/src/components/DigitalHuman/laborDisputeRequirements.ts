export interface LaborRequirementValues {
  employee_name: string;
  employer_name: string;
  employment_start_date: string;
  termination_date: string;
  limitation_start_date: string;
  work_location: string;
  claim_types: string;
  demands: string;
  employment_active: string;
  wage_arrears_amount: string;
  wage_arrears_months: string;
  wage_arrears_start_date: string;
  wages_paid_through: string;
  contract_term_type: string;
  contract_term_months: string;
  probation_period_months: string;
  termination_reason: string;
  termination_initiator: string;
  local_average_monthly_salary: string;
  compensation_kind: string;
  working_hours_system: string;
  overtime_workday_hours: string;
  overtime_rest_day_hours: string;
  overtime_statutory_holiday_hours: string;
}

export interface LaborRequirementFlags {
  showWage: boolean;
  showProbation: boolean;
  showTermination: boolean;
  showCompensation: boolean;
  showOvertime: boolean;
}

export interface LaborDisputeRequirements {
  flags: LaborRequirementFlags;
  requiredFields: string[];
  missingFields: string[];
  missingFacts: string[];
  conflicts: string[];
}

const BASE_REQUIRED_FIELDS: Array<keyof LaborRequirementValues | 'monthly_salary'> = [
  'employee_name', 'employer_name', 'employment_start_date', 'monthly_salary',
  'work_location', 'claim_types', 'demands', 'limitation_start_date',
];

export function splitLaborValues(value: string): string[] {
  return value.split(/[、,，\n]/).map((item) => item.trim()).filter(Boolean);
}

function claimFlags(claimTypes: string): LaborRequirementFlags {
  const claims = splitLaborValues(claimTypes);
  const has = (terms: string[]) => claims.some((claim) => terms.some((term) => claim.includes(term)));
  return {
    showWage: has(['欠薪', '工资', '劳动报酬']),
    showProbation: has(['试用期']),
    showTermination: has(['解除', '辞退', '解雇']),
    showCompensation: has(['补偿', '赔偿']),
    showOvertime: has(['加班']),
  };
}

/** 红星、缺失定位和提交拦截共用的条件必填规则。 */
export function getLaborDisputeRequirements(
  value: LaborRequirementValues,
  monthlySalary: string,
): LaborDisputeRequirements {
  const flags = claimFlags(value.claim_types);
  const requiredFields = new Set<string>(BASE_REQUIRED_FIELDS);
  const missingFields = new Set<string>();
  const missingFacts: string[] = [];
  const conflicts: string[] = [];

  const requireEmpty = (field: keyof LaborRequirementValues, fact = field) => {
    requiredFields.add(field);
    if (value[field] === '') {
      missingFields.add(field);
      missingFacts.push(fact);
    }
  };

  BASE_REQUIRED_FIELDS.forEach((field) => {
    const empty = field === 'monthly_salary' ? monthlySalary === '' : value[field] === '';
    if (empty) {
      missingFields.add(field);
      missingFacts.push(field);
    }
  });

  if (flags.showWage) {
    const hasAmount = value.wage_arrears_amount !== ''
      || (monthlySalary !== '' && value.wage_arrears_months !== '');
    if (!hasAmount) {
      ['wage_arrears_amount', 'wage_arrears_months'].forEach((field) => {
        requiredFields.add(field);
        missingFields.add(field);
      });
      missingFacts.push('wage_arrears_amount_or_salary_and_months');
    }
    const hasPeriod = value.wage_arrears_start_date !== '' || value.wages_paid_through !== '';
    if (!hasPeriod) {
      ['wage_arrears_start_date', 'wages_paid_through'].forEach((field) => {
        requiredFields.add(field);
        missingFields.add(field);
      });
      missingFacts.push('wage_arrears_period');
    }
  }

  if (flags.showTermination || flags.showCompensation) {
    requireEmpty('termination_date');
    requireEmpty('employment_active');
    if (value.employment_active === 'true') {
      missingFields.add('employment_active');
      missingFacts.push('employment_status_conflict');
      conflicts.push('已选择解除、补偿或赔偿事项，但劳动关系仍标记为存续，请确认实际状态。');
    }
  }

  if (flags.showTermination) {
    requireEmpty('termination_reason');
    requireEmpty('termination_initiator');
  }

  if (flags.showCompensation) {
    requireEmpty('compensation_kind');
    requireEmpty('local_average_monthly_salary');
  }

  if (value.employment_start_date && value.termination_date
    && value.termination_date < value.employment_start_date) {
    missingFields.add('employment_start_date');
    missingFields.add('termination_date');
    missingFacts.push('valid_employment_period');
    conflicts.push('解除/终止日期不能早于入职日期。');
  }

  if (flags.showOvertime) {
    requireEmpty('working_hours_system');
    if (value.working_hours_system && value.working_hours_system !== 'standard') {
      missingFields.add('working_hours_system');
      missingFacts.push('standard_working_hours_system_required');
      conflicts.push('当前自动估算仅适用于标准工时制；非标准工时需结合审批材料和当地规则人工核算。');
    }
    const overtimeHours = [
      value.overtime_workday_hours,
      value.overtime_rest_day_hours,
      value.overtime_statutory_holiday_hours,
    ].reduce((total, raw) => total + Number(raw || 0), 0);
    if (overtimeHours <= 0) {
      ['overtime_workday_hours', 'overtime_rest_day_hours', 'overtime_statutory_holiday_hours']
        .forEach((field) => {
          requiredFields.add(field);
          missingFields.add(field);
        });
      missingFacts.push('overtime_hours_by_type');
    }
  }

  if (flags.showProbation) {
    requireEmpty('probation_period_months');
    requiredFields.add('contract_term_type');
    if (value.contract_term_type === '') {
      missingFields.add('contract_term_type');
      missingFacts.push('contract_term');
    } else if (value.contract_term_type === 'fixed') {
      requiredFields.add('contract_term_months');
      if (value.contract_term_months === '') {
        missingFields.add('contract_term_months');
        missingFacts.push('contract_term');
      }
    }
  }

  return {
    flags,
    requiredFields: Array.from(requiredFields),
    missingFields: Array.from(missingFields),
    missingFacts: Array.from(new Set(missingFacts)),
    conflicts,
  };
}
