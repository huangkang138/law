'use client';

import { useCallback, useEffect, useRef } from 'react';

import {
  DigitalHumanAgentRun,
  LaborTriageFacts,
  LaborTriageSnapshot,
  createDigitalHumanMatter,
  getDigitalHumanAgentRun,
  getLaborCaseTriage,
  startLaborDisputeAgentRun,
  updateLaborCaseTriage,
} from '@/services/digitalHumanApi';
import { useDigitalHumanStore } from '@/store/digitalHumanStore';

const LABOR_TERMS = [
  '劳动', '工资', '薪资', '薪水', '欠薪', '加班', '辞退', '解雇', '离职', '入职',
  '试用期', '实习', '兼职', '勤工助学', '社保', '工伤', '用人单位', '劳动合同',
];
const CLAIM_MAPPINGS: Array<[string, string]> = [
  ['欠薪', '欠薪'], ['工资', '欠薪'], ['试用期', '试用期'],
  ['加班费', '加班费'], ['加班', '加班费'],
  ['辞退', '违法解除'], ['解雇', '违法解除'],
  ['经济补偿', '经济补偿'], ['赔偿', '赔偿金'],
];

export function isLaborQuestion(question: string): boolean {
  return LABOR_TERMS.some((term) => question.includes(term));
}

function inferInitialFacts(question: string): Partial<LaborTriageFacts> {
  const facts: Partial<LaborTriageFacts> = {
    issue_domain: /(不是|不属于|并非|非).{0,3}劳动|与劳动无关/.test(question) ? 'non_labor' : 'labor',
  };
  if (/学校.{0,6}(安排|组织).{0,6}实习/.test(question)) facts.scenario_type = 'school_arranged_internship';
  else if (question.includes('勤工助学')) facts.scenario_type = 'work_study';
  else if (question.includes('实习')) facts.scenario_type = 'independent_internship';
  else if (question.includes('兼职')) facts.scenario_type = 'part_time';
  else if (/(应届|毕业).{0,8}(入职|工作|就业)/.test(question)) facts.scenario_type = 'graduate_employment';
  else if (/(入职|正式员工|劳动合同)/.test(question)) facts.scenario_type = 'regular_employment';

  if (/(在校生|在校学生|大[一二三四]|研究生在读)/.test(question)) facts.student_status = 'current_student';
  else if (/(应届|即将毕业|临近毕业)/.test(question)) facts.student_status = 'graduating';
  else if (/(已经毕业|已毕业)/.test(question)) facts.student_status = 'graduated';

  const claimTypes = Array.from(new Set(
    CLAIM_MAPPINGS.filter(([term]) => question.includes(term)).map(([, claim]) => claim),
  ));
  if (claimTypes.length) facts.claim_types = claimTypes;
  const urgentRisks: string[] = [];
  if (/(人身安全|殴打|暴力|生命危险)/.test(question)) urgentRisks.push('personal_safety');
  if (/(威胁|胁迫|强迫)/.test(question)) urgentRisks.push('coercion_or_threat');
  if (question.includes('工伤')) urgentRisks.push('work_injury');
  if (/(未成年|童工)/.test(question)) urgentRisks.push('minor_worker');
  if (/(集体|群体).{0,6}(欠薪|纠纷|维权)/.test(question)) urgentRisks.push('mass_dispute');
  if (urgentRisks.length) facts.urgent_risks = urgentRisks;
  return facts;
}

function taskTypeFor(snapshot: LaborTriageSnapshot) {
  const expected = {
    simple_labor_consultation: 'labor_consultation',
    labor_relationship_assessment: 'labor_relationship_assessment',
    formal_labor_dispute: 'labor_case_analysis',
  } as const;
  const expectedTask = expected[snapshot.result.triage_type as keyof typeof expected] || null;
  return snapshot.result.recommended_task_type === expectedTask ? expectedTask : null;
}

export interface LaborTriageFlow {
  snapshot: LaborTriageSnapshot | null;
  agentRun: DigitalHumanAgentRun | null;
  isLoading: boolean;
  error: string;
  start: (question: string) => Promise<void>;
  submitFacts: (facts: Partial<LaborTriageFacts>) => Promise<void>;
  retry: () => Promise<void>;
}

export function useLaborTriage(): LaborTriageFlow {
  const {
    currentMatterId, currentTriage, currentAgentRun, laborTriageLoading, laborTriageError,
    laborContextBySession, sessionId, setLaborContext,
  } = useDigitalHumanStore();
  const inFlight = useRef(false);
  const lastQuestion = useRef('');

  const startRuntime = useCallback(async (snapshot: LaborTriageSnapshot) => {
    if (snapshot.result.missing_facts.length) {
      setLaborContext({ triage: snapshot, run: null });
      return null;
    }
    const taskType = taskTypeFor(snapshot);
    if (!taskType) {
      setLaborContext({ triage: snapshot, run: null });
      return null;
    }
    const run = await startLaborDisputeAgentRun(snapshot.matter_id, { ...snapshot.facts }, taskType);
    setLaborContext({ triage: snapshot, run });
    return run;
  }, [setLaborContext]);

  const assess = useCallback(async (matterId: string, facts: Partial<LaborTriageFacts>) => {
    const snapshot = await updateLaborCaseTriage(matterId, facts);
    setLaborContext({ matterId, triage: snapshot });
    await startRuntime(snapshot);
  }, [setLaborContext, startRuntime]);

  const start = useCallback(async (question: string) => {
    if (inFlight.current) return;
    inFlight.current = true;
    lastQuestion.current = question;
    setLaborContext({ matterId: null, triage: null, run: null, loading: true, error: '' });
    try {
      const matter = await createDigitalHumanMatter(question, sessionId);
      setLaborContext({ matterId: matter.matter_id });
      await assess(matter.matter_id, inferInitialFacts(question));
    } catch (error) {
      setLaborContext({ error: error instanceof Error ? error.message : '劳动案件分流暂时不可用' });
    } finally {
      inFlight.current = false;
      setLaborContext({ loading: false });
    }
  }, [assess, sessionId, setLaborContext]);

  const submitFacts = useCallback(async (facts: Partial<LaborTriageFacts>) => {
    if (!currentMatterId || inFlight.current) return;
    inFlight.current = true;
    setLaborContext({ loading: true, error: '' });
    try {
      await assess(currentMatterId, facts);
    } catch (error) {
      setLaborContext({ error: error instanceof Error ? error.message : '重新判断失败' });
    } finally {
      inFlight.current = false;
      setLaborContext({ loading: false });
    }
  }, [assess, currentMatterId, setLaborContext]);

  const retry = useCallback(async () => {
    if (currentTriage && currentMatterId) await submitFacts(currentTriage.facts);
    else if (lastQuestion.current) await start(lastQuestion.current);
  }, [currentMatterId, currentTriage, start, submitFacts]);

  useEffect(() => {
    const context = sessionId ? laborContextBySession[sessionId] : null;
    if (
      !sessionId || !currentMatterId || !context || context.triageStarted === false
      || currentTriage || inFlight.current
    ) return;
    let active = true;
    const restore = async () => {
      try {
        const [triage, run] = await Promise.all([
          getLaborCaseTriage(currentMatterId),
          context?.runId ? getDigitalHumanAgentRun(context.runId) : Promise.resolve(null),
        ]);
        if (active) setLaborContext({ triage, run });
      } catch (error) {
        if (active) setLaborContext({ error: error instanceof Error ? error.message : '案件状态恢复失败' });
      }
    };
    void restore();
    return () => { active = false; };
  }, [currentMatterId, currentTriage, laborContextBySession, sessionId, setLaborContext]);

  return {
    snapshot: currentTriage,
    agentRun: currentAgentRun,
    isLoading: laborTriageLoading,
    error: laborTriageError,
    start, submitFacts, retry,
  };
}
