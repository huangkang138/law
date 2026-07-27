'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, RefreshCw, ShieldAlert } from 'lucide-react';

import type { DigitalHumanAgentRun, LaborTriageFacts, LaborTriageSnapshot, LaborTriageType } from '@/services/digitalHumanApi';

import styles from './LaborTriageCard.module.css';

interface Props {
  snapshot: LaborTriageSnapshot | null;
  agentRun: DigitalHumanAgentRun | null;
  isLoading: boolean;
  error: string;
  onSubmit: (facts: Partial<LaborTriageFacts>) => Promise<void>;
  onRetry: () => Promise<void>;
}

const TYPE_LABELS: Record<LaborTriageType, string> = {
  simple_labor_consultation: '简单劳动咨询',
  labor_relationship_assessment: '劳动关系判断',
  formal_labor_dispute: '正式劳动纠纷',
  non_labor_dispute: '非劳动纠纷',
  high_risk_handoff: '高风险人工处理',
};

const RISK_LABELS = { low: '低风险', medium: '中风险', high: '高风险' } as const;
const RELATIONSHIP_LABELS = {
  not_assessed: '暂不判断',
  uncertain: '尚不确定',
  likely_established: '倾向存在劳动关系',
  likely_not_established: '倾向不构成劳动关系',
} as const;

const BOOLEAN_FIELDS: Record<string, string> = {
  school_arranged: '是否由学校统一组织或纳入教学安排',
  employment_intent: '双方是否以建立持续用工关系为目的',
  employer_qualified: '对方是否是依法可以用工的公司或组织',
  paid_labor: '是否实际工作并获得工资、报酬或固定津贴',
  management_control: '对方是否安排岗位、考勤、工时并进行管理',
  business_integrated: '工作是否属于对方日常业务的一部分',
};

const URGENT_OPTIONS = [
  ['imminent_limitation_deadline', '仲裁或诉讼期限临近'],
  ['work_injury', '存在工伤'],
  ['personal_safety', '存在人身安全风险'],
  ['coercion_or_threat', '存在胁迫或威胁'],
  ['minor_worker', '涉及未成年劳动者'],
  ['mass_dispute', '涉及群体性纠纷'],
] as const;

function BooleanSelect({ field, value, onChange }: {
  field: string;
  value: boolean | null;
  onChange: (value: boolean | null) => void;
}) {
  return <label className={styles.field}>
    <span>{BOOLEAN_FIELDS[field]}</span>
    <select value={value === null ? '' : String(value)} onChange={(event) => {
      onChange(event.target.value === '' ? null : event.target.value === 'true');
    }}>
      <option value="">请选择</option>
      <option value="true">是</option>
      <option value="false">否</option>
    </select>
  </label>;
}

export default function LaborTriageCard({ snapshot, agentRun, isLoading, error, onSubmit, onRetry }: Props) {
  const [draft, setDraft] = useState<Partial<LaborTriageFacts>>({});

  useEffect(() => {
    if (snapshot) setDraft(snapshot.facts);
  }, [snapshot]);

  if (!snapshot && !isLoading && !error) return null;

  if (!snapshot) {
    return <section className={styles.card} aria-live="polite">
      {isLoading ? <p className={styles.loading}><RefreshCw size={16} />正在创建案件并判断分流…</p> : null}
      {error ? <div className={styles.error}><AlertTriangle size={16} /><span>{error}</span><button type="button" onClick={() => void onRetry()}>重试</button></div> : null}
    </section>;
  }

  const { result } = snapshot;
  const missing = new Set(result.missing_facts);
  const setField = <K extends keyof LaborTriageFacts>(field: K, value: LaborTriageFacts[K]) => {
    setDraft((current) => ({ ...current, [field]: value }));
  };

  return <section className={`${styles.card} ${styles[result.risk_level]}`} aria-label="劳动案件分流结果">
    <header className={styles.header}>
      <div>
        {result.risk_level === 'high' ? <ShieldAlert size={18} /> : <CheckCircle2 size={18} />}
        <strong>{TYPE_LABELS[result.triage_type]}</strong>
      </div>
      <span>{RISK_LABELS[result.risk_level]}</span>
    </header>

    <p className={styles.relationship}>{RELATIONSHIP_LABELS[result.relationship_status]}</p>
    {result.basis.length > 0 && <div className={styles.section}>
      <strong>判断依据</strong>
      <ul>{result.basis.map((item) => <li key={item}>{item}</li>)}</ul>
    </div>}
    {result.dispute_tags.length > 0 && <p className={styles.tags}>争议事项：{result.dispute_tags.join('、')}</p>}
    <div className={styles.next}>
      <strong>下一步建议</strong>
      <p>{result.recommended_next_step}</p>
    </div>
    {result.manual_review_required && <p className={styles.review}><AlertTriangle size={14} />该场景需要人工复核</p>}
    {agentRun && <div className={styles.next}>
      <strong>Agent Runtime</strong>
      <p>已启动 {agentRun.template_id || agentRun.task_type}，当前状态：{agentRun.status}</p>
    </div>}
    {!agentRun && result.missing_facts.length > 0 && <p className={styles.review}>等待补充事实，暂未启动 Agent Runtime</p>}
    {!agentRun && result.triage_type === 'high_risk_handoff' && <p className={styles.review}>自动 Runtime 已停止；当前仅标记人工复核，尚无真实人工服务通道</p>}

    {result.questions.length > 0 && <form className={styles.form} onSubmit={(event) => {
      event.preventDefault();
      void onSubmit(draft);
    }}>
      <strong>补充关键信息后重新判断</strong>
      <ol>{result.questions.map((question) => <li key={question}>{question}</li>)}</ol>

      {missing.has('issue_domain') && <label className={styles.field}><span>问题领域</span><select value={draft.issue_domain || 'unknown'} onChange={(event) => setField('issue_domain', event.target.value as LaborTriageFacts['issue_domain'])}><option value="unknown">请选择</option><option value="labor">劳动用工问题</option><option value="non_labor">非劳动纠纷</option></select></label>}
      {missing.has('scenario_type') && <label className={styles.field}><span>当前场景</span><select value={draft.scenario_type || 'unknown'} onChange={(event) => setField('scenario_type', event.target.value as LaborTriageFacts['scenario_type'])}><option value="unknown">请选择</option><option value="school_arranged_internship">学校安排实习</option><option value="independent_internship">自主实习</option><option value="work_study">勤工助学</option><option value="part_time">兼职</option><option value="graduate_employment">毕业初就业</option><option value="regular_employment">普通用工</option><option value="other">其他</option></select></label>}
      {missing.has('student_status') && <label className={styles.field}><span>事情发生时的学生身份</span><select value={draft.student_status || 'unknown'} onChange={(event) => setField('student_status', event.target.value as LaborTriageFacts['student_status'])}><option value="unknown">请选择</option><option value="current_student">在校</option><option value="graduating">临近毕业</option><option value="graduated">已经毕业</option><option value="not_student">非学生</option></select></label>}
      {Object.keys(BOOLEAN_FIELDS).filter((field) => missing.has(field)).map((field) => <BooleanSelect key={field} field={field} value={(draft[field as keyof LaborTriageFacts] as boolean | null | undefined) ?? null} onChange={(value) => setField(field as keyof LaborTriageFacts, value as never)} />)}

      <label className={styles.field}><span>争议事项（可选，用顿号分隔）</span><input value={(draft.claim_types || []).join('、')} onChange={(event) => setField('claim_types', event.target.value.split(/[、,，]/).map((item) => item.trim()).filter(Boolean))} placeholder="例如：欠薪、违法解除" /></label>
      <fieldset className={styles.risks}><legend>是否存在需优先处理的风险</legend>{URGENT_OPTIONS.map(([value, label]) => <label key={value}><input type="checkbox" checked={(draft.urgent_risks || []).includes(value)} onChange={(event) => {
        const current = draft.urgent_risks || [];
        setField('urgent_risks', event.target.checked ? [...current, value] : current.filter((item) => item !== value));
      }} />{label}</label>)}</fieldset>
      <button type="submit" disabled={isLoading}>{isLoading ? '重新判断中…' : '提交补充信息'}</button>
    </form>}

    {error && <div className={styles.error}><AlertTriangle size={16} /><span>{error}</span><button type="button" onClick={() => void onRetry()}>重试</button></div>}
    <small className={styles.notice}>{result.notice}</small>
  </section>;
}
