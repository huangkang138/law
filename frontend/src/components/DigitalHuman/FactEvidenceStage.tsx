'use client';

import { useState } from 'react';
import { CheckCircle2, ChevronDown, ChevronUp, ListChecks } from 'lucide-react';

import type {
  DigitalHumanAgentRun,
  LaborFactSuggestions,
  MatterAnalysisResult,
} from '@/services/digitalHumanApi';
import LaborDisputeForm, { LaborDisputeFormValue } from './LaborDisputeForm';
import styles from './Workspace.module.css';

interface FactEvidenceStageProps {
  matterId: string | null;
  result: MatterAnalysisResult | null;
  expandedFact: string | null;
  onExpandedFactChange: (id: string | null) => void;
  laborSuggestions: LaborFactSuggestions | null;
  suggestionDecision: 'pending' | 'adopted' | 'dismissed';
  onSuggestionDecisionChange: (value: 'pending' | 'adopted' | 'dismissed') => void;
  laborFacts: LaborDisputeFormValue;
  onLaborFactsChange: (value: LaborDisputeFormValue) => void;
  salary: string;
  onSalaryChange: (value: string) => void;
  missingFacts: string[];
  loading: boolean;
  error: string;
  laborRun: DigitalHumanAgentRun | null;
  onAdoptSuggestions: () => void;
  onRunWorkflow: () => void;
}

/** 阶段三：事实与证据（候选事实、确认事实、时间线、原文出处、证据缺口、正式事实表单）。 */
export default function FactEvidenceStage({
  matterId, result, expandedFact, onExpandedFactChange, laborSuggestions,
  suggestionDecision, onSuggestionDecisionChange, laborFacts, onLaborFactsChange,
  salary, onSalaryChange, missingFacts, loading, error, laborRun,
  onAdoptSuggestions, onRunWorkflow,
}: FactEvidenceStageProps) {
  // 纯 UI 状态：用户尝试提交时才点亮缺失字段（橙色），不改变任何业务校验。
  const [validationAttempted, setValidationAttempted] = useState(false);

  return (
    <section className={styles.stageSection} aria-label="阶段三：事实与证据">
      <h3 className={styles.stageTitle}><ListChecks size={16} />事实与证据</h3>
      {!matterId ? (
        <p className={styles.stageHint}>先在「目标与法域」创建或选择案件。</p>
      ) : (
        <div className={styles.stageStack}>
          {result && result.facts.length > 0 && (
            <div className={styles.stagePanel}>
              <h4 className={styles.panelTitle}>事实出处（{result.facts.length}）</h4>
              {result.facts.map((fact) => (
                <article key={fact.fact_id} className="dh-fact-item">
                  <button onClick={() => onExpandedFactChange(expandedFact === fact.fact_id ? null : fact.fact_id)}>
                    <span><CheckCircle2 size={14} />{fact.fact_text}</span>
                    {expandedFact === fact.fact_id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                  {expandedFact === fact.fact_id && <div>
                    <p>来源：{result.checklist.available.find((item) => item.document_id === fact.material_ref.document_id)?.filename || '当前材料'}</p>
                    <p>位置：第 {fact.material_ref.start_offset + 1}–{fact.material_ref.end_offset} 字</p>
                    <blockquote>“{fact.material_ref.quote}”</blockquote>
                  </div>}
                </article>
              ))}
            </div>
          )}

          {result && result.timeline.length > 0 && (
            <div className={styles.stagePanel}>
              <h4 className={styles.panelTitle}>时间线</h4>
              {result.timeline.map((item) => (
                <p className="dh-timeline-item" key={`${item.fact_id}-${item.date}`}><time>{item.date}</time>{item.event}</p>
              ))}
            </div>
          )}

          {result && (
            <div className={styles.stagePanel}>
              <h4 className={styles.panelTitle}>证据缺口</h4>
              {result.checklist.missing.length === 0
                ? <p className={styles.panelLineOk}>当前材料已覆盖识别清单，暂无缺口提示。</p>
                : result.checklist.missing.map((item) => (
                  <p className={styles.panelLineWarn} key={item}>⚠ {item}</p>
                ))}
              {result.checklist.warning && <p className="dh-result-warning">{result.checklist.warning}</p>}
            </div>
          )}

          {laborSuggestions?.fields.length && suggestionDecision === 'pending' ? (
            <section className={`dh-labor-tool ${styles.stagePanel}`}>
              <div className="dh-suggestion-card">
                <strong>已从材料中提取 {laborSuggestions.fields.length} 项候选信息</strong>
                <small>{laborSuggestions.warning}</small>
                {laborSuggestions.fields.map((item) => <details key={item.field}>
                  <summary>{item.label}：{Array.isArray(item.value) ? item.value.join('、') : item.value}</summary>
                  <blockquote>{item.sources[0]?.quote}</blockquote>
                </details>)}
                <div><button type="button" onClick={onAdoptSuggestions}>采用材料建议</button><button type="button" onClick={() => onSuggestionDecisionChange('dismissed')}>暂不采用，我自己填写</button></div>
              </div>
            </section>
          ) : null}
          {suggestionDecision === 'adopted' && (
            <p className="dh-suggestion-status"><CheckCircle2 size={14} />已采用材料建议，下面字段仍可修改</p>
          )}

          <div className={styles.stagePanel}>
            <h4 className={styles.panelTitle}>正式事实表单</h4>
            <LaborDisputeForm
              value={laborFacts}
              monthlySalary={salary}
              missingFacts={missingFacts}
              disabled={loading || laborRun?.status === 'awaiting_approval'}
              highlightMissing={validationAttempted || laborRun?.status === 'awaiting_information'}
              onChange={onLaborFactsChange}
              onMonthlySalaryChange={onSalaryChange}
            />
            <button
              className={styles.primaryAction}
              onClick={() => {
                // 有缺失时不启动分析，只点亮缺失字段帮助定位；补齐后才真正发起 Agent。
                if (missingFacts.length > 0) {
                  setValidationAttempted(true);
                  return;
                }
                onRunWorkflow();
              }}
              disabled={loading || laborRun?.status === 'blocked_authority' || laborRun?.status === 'awaiting_approval'}
            >
              {loading ? '分析中…'
                : missingFacts.length > 0 ? `还需填写 ${missingFacts.length} 项必填信息`
                : laborRun?.status === 'failed' ? '重新开始新的分析任务'
                : '检查证据、期限和法源'}
            </button>
          </div>
        </div>
      )}
      {error && <p className="dh-matter-error">{error}</p>}
    </section>
  );
}
