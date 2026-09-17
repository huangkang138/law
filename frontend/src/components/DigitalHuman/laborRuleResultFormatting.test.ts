import { strict as assert } from 'node:assert';
import { test } from 'node:test';

import { displayLaborCalculationValue } from './laborRuleResultFormatting';

test('解除审查路径枚举显示为中文', () => {
  assert.equal(
    displayLaborCalculationValue('termination_route', 'employer_fault_based_termination_review'),
    '用人单位过错性解除审查',
  );
  assert.equal(
    displayLaborCalculationValue('termination_route', 'mutual_termination_review'),
    '协商解除审查',
  );
  assert.equal(
    displayLaborCalculationValue('termination_route', 'undetermined_termination_route'),
    '解除路径待进一步确认',
  );
});

test('未知解除路径不暴露后端枚举值', () => {
  assert.equal(
    displayLaborCalculationValue('termination_route', 'new_backend_route'),
    '解除路径待进一步确认',
  );
});

test('其他计算值保持原有展示语义', () => {
  assert.equal(displayLaborCalculationValue('duration_exceeded', true), '是');
  assert.equal(displayLaborCalculationValue('duration_exceeded', false), '否');
  assert.equal(displayLaborCalculationValue('compensation', null), '未确定');
  assert.equal(displayLaborCalculationValue('compensation', 16000), '16000');
});
