const TERMINATION_ROUTE_LABELS: Record<string, string> = {
  employer_fault_based_termination_review: '用人单位过错性解除审查',
  employer_notice_termination_review: '用人单位非过错性解除审查',
  economic_layoff_review: '经济性裁员审查',
  employee_resignation_review: '劳动者辞职审查',
  mutual_termination_review: '协商解除审查',
  undetermined_termination_route: '解除路径待进一步确认',
};

/** 将规则计算结果转换为面向用户的展示文本，不改变后端原始值。 */
export function displayLaborCalculationValue(key: string, value: unknown): string {
  if (key === 'termination_route') {
    if (typeof value !== 'string' || value === '') return '解除路径待进一步确认';
    return TERMINATION_ROUTE_LABELS[value] || '解除路径待进一步确认';
  }
  if (typeof value === 'boolean') return value ? '是' : '否';
  if (value === null || value === undefined || value === '') return '未确定';
  return String(value);
}
