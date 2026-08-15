'use client';

import { Calculator, Download, FileText, Gavel, ScrollText } from 'lucide-react';

import type {
  DigitalHumanAgentRun,
  LaborAnalysisResult,
  LaborAuthorityCatalog,
  LaborCompensationResult,
  LaborDisputeDraft,
  LaborDisputeWorkflow,
  MatterAnalysisResult,
} from '@/services/digitalHumanApi';

import LaborRuleResults, { LABOR_ISSUE_LABELS } from './LaborRuleResults';
import { laborFactLabel } from './LaborDisputeForm';
import { humanizeLaborMessage, laborStepStatusLabel } from './useMatterWorkspace';
import styles from './Workspace.module.css';

interface AnalysisDocumentStageProps {
  matterId: string | null;
  laborRun: DigitalHumanAgentRun | null;
  workflowStatus: LaborDisputeWorkflow['status'] | null;
  runtimeAnalysis: LaborAnalysisResult | undefined;
  verifiedAuthorities: NonNullable<LaborAnalysisResult['authorities']>;
  authorityCatalog: LaborAuthorityCatalog | null;
  laborDraft: LaborDisputeDraft | null;
  laborResult: LaborCompensationResult | null;
  salary: string;
  onSalaryChange: (value: string) => void;
  years: string;
  onYearsChange: (value: string) => void;
  months: string;
  onMonthsChange: (value: string) => void;
  loading: boolean;
  error: string;
  result: MatterAnalysisResult | null;
  onCalculate: () => void;
  onRetryAuthorities: () => void;
  onApprove: () => void;
  onExport: (format: 'word' | 'pdf') => void;
}

const RUN_STATUS_LABELS: Record<string, string> = {
  planning: '正在规划分析', awaiting_jurisdiction: '等待确认适用法域', awaiting_information: '等待补充案件信息',
  executing: '正在分析案件', verifying: '正在校验分析依据', retrying: '正在重新验证',
  awaiting_approval: '等待确认生成草稿', awaiting_draft_approval: '等待确认生成草稿',
  blocked_authority: '法律依据待恢复', replanning: '正在调整分析步骤', human_handoff: '需要人工处理',
  completed: '分析已完成', failed: '分析未完成', cancelled: '分析已取消', ready: '等待开始分析',
};

function uniqueItems(items: Array<string | null | undefined>): string[] {
  return Array.from(new Set(items.map((item) => item?.trim()).filter((item): item is string => Boolean(item))));
}

function issueLabel(issueTag: string): string {
  return LABOR_ISSUE_LABELS[issueTag] || '待核对事项';
}

/** 阶段四：以既有运行结果组织案件成果，不改变任何分析、审批或计算逻辑。 */
export default function AnalysisDocumentStage({
  matterId, laborRun, workflowStatus, runtimeAnalysis, verifiedAuthorities,
  authorityCatalog, laborDraft, laborResult, salary, onSalaryChange,
  years, onYearsChange, months, onMonthsChange, loading, error, result,
  onCalculate, onRetryAuthorities, onApprove, onExport,
}: AnalysisDocumentStageProps) {
  if (!matterId) {
    return <section className={styles.stageSection} aria-label="阶段四：分析与文书">
      <h3 className={styles.stageTitle}><Gavel size={16} />分析与文书</h3>
      <p className={styles.stageHint}>先在「目标与法域」创建或选择案件。</p>
      {error && <p className="dh-matter-error">{error}</p>}
    </section>;
  }

  const decisions = runtimeAnalysis?.rule_decisions || [];
  const initialConclusions = decisions
    .filter((decision) => decision.status === 'completed' && decision.assessment.trim())
    .map((decision) => ({ label: issueLabel(decision.issue_tag), text: decision.assessment }));
  const issueTags = Array.from(new Set(decisions.map((decision) => decision.issue_tag)));
  const riskItems = uniqueItems([
    ...decisions.flatMap((decision) => decision.missing_facts.map((fact) => `待确认：${laborFactLabel(fact)}`)),
    ...decisions.flatMap((decision) => decision.assumptions.map((item) => `分析假设：${item}`)),
    ...decisions.flatMap((decision) => decision.warnings),
    ...(runtimeAnalysis?.missing_rule_facts || []).map((fact) => `待确认：${laborFactLabel(fact)}`),
    ...(runtimeAnalysis?.deadline?.warnings || []),
    ...(laborRun?.questions || []),
    laborRun?.blocked_reason ? humanizeLaborMessage(laborRun.blocked_reason) : null,
    ...(result?.checklist.missing || []).map((item) => `缺少材料：${item}`),
    result?.checklist.warning,
  ]);
  const hasConclusion = initialConclusions.length > 0 || issueTags.length > 0 || riskItems.length > 0;
  const status = laborRun?.status || workflowStatus || '';
  const statusLabel = RUN_STATUS_LABELS[status] || '尚未开始分析';
  const isAwaitingApproval = laborRun?.status === 'awaiting_approval';
  const draftStatus = laborDraft ? '已生成' : isAwaitingApproval || workflowStatus === 'awaiting_draft_approval' ? '待确认' : '待生成';

  return <section className={styles.stageSection} aria-label="阶段四：分析与文书">
    <div className={styles.analysisStageHeading}>
      <h3 className={styles.stageTitle}><Gavel size={16} />分析与文书</h3>
      <span className={styles.analysisStatus} aria-live="polite"><i />{statusLabel}</span>
      {laborRun?.status === 'blocked_authority' && <button className={styles.analysisStatusAction} onClick={onRetryAuthorities} disabled={loading}>
        {loading ? '正在重新验证…' : '重新验证法律依据'}
      </button>}
    </div>

    {!laborRun && !workflowStatus && <p className={styles.stageHint}>完成事实确认后，可在「事实与证据」发起案件分析。</p>}

    <div className={styles.stageStack}>
      {hasConclusion && <section className={styles.analysisConclusion} aria-labelledby="case-analysis-title">
        <div className={styles.analysisConclusionHead}>
          <div><p className={styles.analysisEyebrow}>案件成果</p><h4 id="case-analysis-title">案件分析结论</h4></div>
          <span>均需人工复核</span>
        </div>
        {initialConclusions.length > 0 && <div className={styles.analysisConclusionBlock}>
          <strong>初步结论</strong>
          {initialConclusions.map((item, index) => <p key={`${item.label}-${index}`}><b>{item.label}</b>{item.text}</p>)}
        </div>}
        {issueTags.length > 0 && <div className={styles.analysisConclusionBlock}>
          <strong>争议焦点</strong>
          <div className={styles.analysisIssueTags}>{issueTags.map((tag) => <span key={tag}>{issueLabel(tag)}</span>)}</div>
        </div>}
        {riskItems.length > 0 && <div className={styles.analysisConclusionBlock}>
          <strong>风险 / 待确认</strong>
          <ul>{riskItems.slice(0, 6).map((item) => <li key={item}>{item}</li>)}</ul>
        </div>}
      </section>}

      <details className={styles.compensationCard}>
        <summary>
          <span className={styles.compensationTitle}><Calculator size={15} />可主张金额测算</span>
          <span className={styles.compensationSummary}><strong>{laborResult ? `¥${laborResult.compensation.toLocaleString()}` : '尚未测算'}</strong><small>{laborResult ? '基于当前已确认事实计算' : '展开填写参数并计算'}</small></span>
        </summary>
        <div className={styles.compensationDetails}>
          <p>此金额仅为参考测算，不代表仲裁请求已提交或获得支持。</p>
          <div className="dh-labor-tool-inputs">
            <input type="number" min="0" value={salary} onChange={(event) => onSalaryChange(event.target.value)} placeholder="月工资" />
            <input type="number" min="0" value={years} onChange={(event) => onYearsChange(event.target.value)} placeholder="工作年数" />
            <input type="number" min="0" max="11" value={months} onChange={(event) => onMonthsChange(event.target.value)} placeholder="额外月数" />
          </div>
          <button onClick={onCalculate} disabled={loading || !salary || !years}>{loading ? '计算中…' : '计算参考补偿金额'}</button>
          {laborResult && <div className={styles.compensationResult}><p>{laborResult.calculation}</p><small>{laborResult.warning}</small></div>}
        </div>
      </details>

      <section className={styles.draftCard} aria-labelledby="labor-draft-title">
        <div className={styles.draftCardHead}>
          <div><p className={styles.analysisEyebrow}>文书成果</p><h4 id="labor-draft-title"><ScrollText size={15} />仲裁申请草稿</h4></div>
          <span className={laborDraft ? styles.draftStatusReady : styles.draftStatusPending}>{draftStatus}</span>
        </div>
        {laborDraft ? <>
          <p className={styles.draftDescription}>{laborDraft.title}</p>
          <div className={styles.draftActions}>
            <details className={styles.draftPreview}><summary>预览草稿</summary><pre className="dh-draft-preview">{laborDraft.content}</pre></details>
            <button type="button" onClick={() => onExport('word')}><Download size={14} />导出 Word</button>
            <button type="button" onClick={() => onExport('pdf')}><FileText size={14} />导出 PDF</button>
          </div>
          <small>草稿与导出文件均需人工复核，不代表已向仲裁机构提交。</small>
        </> : <>
          <p className={styles.draftDescription}>{isAwaitingApproval ? '分析已完成，确认后生成仲裁申请草稿。' : '完成事实确认与案件分析后，可在这里确认生成草稿。'}</p>
          {isAwaitingApproval && <button className={styles.primaryAction} onClick={onApprove} disabled={loading}>{laborRun.approval?.prompt || '确认并生成仲裁申请书草稿'}</button>}
        </>}
      </section>

      {verifiedAuthorities.length > 0 && <section className={styles.authorityCard} aria-labelledby="authority-title">
        <div className={styles.authorityCardHead}>
          <div><p className={styles.analysisEyebrow}>已验证依据</p><h4 id="authority-title">相关法律依据</h4></div>
          {authorityCatalog?.status === 'ready' && <span>法源库已就绪</span>}
        </div>
        <div className={styles.authorityList}>{verifiedAuthorities.map((authority) => {
          const relatedIssues = decisions.filter((decision) => decision.authority_refs.includes(authority.authority_id)).map((decision) => issueLabel(decision.issue_tag));
          return <article key={authority.authority_id} className={styles.authorityItem}>
            <strong>{authority.title}</strong>
            {authority.provision && <p>{authority.provision}</p>}
            <small>与本案关联：{relatedIssues.length ? `用于${Array.from(new Set(relatedIssues)).join('、')}分析` : '作为本案已验证分析依据'}</small>
            <details><summary>查看完整信息</summary><p>发布机关：{authority.issuing_body}</p><a href={authority.source_url} target="_blank" rel="noreferrer">查看原文</a></details>
          </article>;
        })}</div>
      </section>}

      {laborRun && <details className={styles.analysisRuntimeDetails}>
        <summary>查看运行详情</summary>
        <div>
          {laborRun.steps.map((item) => <p key={item.id}>• {item.name}：{laborStepStatusLabel(item, laborRun)}</p>)}
          {laborRun.error_code === 'BUDGET_EXCEEDED' && <p>本次分析已达到调用上限，请在事实补充后重新发起分析。</p>}
        </div>
      </details>}

      <LaborRuleResults decisions={decisions} />
    </div>
    {error && <p className="dh-matter-error">{error}</p>}
  </section>;
}
