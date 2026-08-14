'use client';

import { ChangeEvent, useEffect, useRef, useState } from 'react';
import { Calculator, CheckCircle2, ChevronDown, ChevronUp, Download, FileSearch, FileText, History, MapPin, Plus, Trash2, Upload } from 'lucide-react';

import { exportAsPDF, exportAsWord } from '@/lib/exportUtils';

import {
  LocatedLegalFact,
  DigitalHumanAgentRun,
  DigitalHumanMatterSummary,
  LaborCompensationResult,
  LaborAnalysisResult,
  LaborDisputeDraft,
  LaborDisputeWorkflow,
  LaborFactSuggestions,
  LaborAuthorityCatalog,
  MatterAnalysisResult,
  organizeMatterMaterial,
  addMatterMaterial,
  analyzeMatterMaterial,
  confirmMatterJurisdiction,
  createDigitalHumanMatter,
  getDigitalHumanMatters,
  getDigitalHumanMatter,
  deleteDigitalHumanMatter,
  calculateMatterLaborCompensation,
  startLaborDisputeAgentRun,
  continueLaborDisputeAgentRun,
  getLaborDisputeFactSuggestions,
  getLaborDisputeWorkflow,
  getLaborAuthorityCatalog,
} from '@/services/digitalHumanApi';
import { useDigitalHumanStore } from '@/store/digitalHumanStore';
import LaborDisputeForm, {
  EMPTY_LABOR_DISPUTE_FORM,
  LaborDisputeFormValue,
  buildLaborDisputePayload,
  findMissingLaborDisputeFacts,
  humanizeLaborMessage,
  laborFactLabel,
  mergeLaborSuggestions,
} from './LaborDisputeForm';
import LaborRuleResults from './LaborRuleResults';

type Step = 'start' | 'jurisdiction' | 'material' | 'result';
type MaterialKind = 'text' | 'document' | 'image' | 'media';

const MATERIAL_OPTIONS: Array<{ kind: MaterialKind; label: string; accept: string; hint: string }> = [
  { kind: 'text', label: '粘贴文字', accept: '.txt,text/plain', hint: '粘贴聊天记录、工资说明等文字' },
  { kind: 'document', label: 'Word / PDF', accept: '.docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document', hint: '劳动合同、工资单、解除通知' },
  { kind: 'image', label: '图片', accept: '.png,.jpg,.jpeg,image/png,image/jpeg', hint: '聊天截图、考勤或转账截图' },
  { kind: 'media', label: '音频 / 视频', accept: '.mp3,.wav,.m4a,.mp4,.mov,.avi,audio/*,video/*', hint: '录音或包含有效声音的视频' },
];

function laborStepStatusLabel(
  item: DigitalHumanAgentRun['steps'][number],
  run: DigitalHumanAgentRun,
): string {
  const data = item.observation?.data as { missing_facts?: unknown } | undefined;
  const missingFacts = Array.isArray(data?.missing_facts)
    ? data.missing_facts.filter((value): value is string => typeof value === 'string')
    : [];
  if (item.status === 'completed' && missingFacts.length > 0) {
    return `初步整理完成（仍缺：${missingFacts.map(laborFactLabel).join('、')}）`;
  }
  if (
    item.status === 'failed'
    && run.status === 'awaiting_information'
    && run.current_step_id === item.id
  ) {
    return '等待补充事实';
  }
  return ({
    pending: '待执行', running: '执行中', completed: '已完成',
    failed: '失败', skipped: '已跳过', cancelled: '已取消',
  } as Record<string, string>)[item.status] || item.status;
}

function matterStatusLabel(
  runStatus: DigitalHumanAgentRun['status'] | undefined,
  workflowStatus: LaborDisputeWorkflow['status'] | null,
): string {
  const status = runStatus || workflowStatus;
  if (status === 'completed') return '分析已完成';
  if (status === 'awaiting_approval' || status === 'awaiting_draft_approval') return '等待确认草稿';
  if (status === 'awaiting_information') return '等待补充信息';
  if (status === 'blocked_authority') return '等待法源恢复';
  return status ? '正在处理中' : '待添加材料';
}

export default function DigitalHumanMatterWorkspace() {
  const pendingCreate = useRef<{
    goal: string;
    sessionId: string | null;
    key: string;
  } | null>(null);
  const {
    currentMatterId: matterId,
    currentAgentRun: laborRun,
    applyWorkspaceContext,
    ensureWorkspaceSession,
    sessionId,
    loadSession,
    refreshWorkspace,
    selectCurrentMatter,
    setCurrentAgentRun,
    workspaceVersion,
  } = useDigitalHumanStore();
  const [step, setStep] = useState<Step>('start');
  const [goal, setGoal] = useState('');
  const [subdivision, setSubdivision] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [filename, setFilename] = useState('');
  const [text, setText] = useState('');
  const [mediaType, setMediaType] = useState('text/plain');
  const [materialKind, setMaterialKind] = useState<MaterialKind>('text');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<MatterAnalysisResult | null>(null);
  const [expandedFact, setExpandedFact] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [matters, setMatters] = useState<DigitalHumanMatterSummary[]>([]);
  const [mattersError, setMattersError] = useState('');
  const [salary, setSalary] = useState('');
  const [years, setYears] = useState('');
  const [months, setMonths] = useState('0');
  const [laborResult, setLaborResult] = useState<LaborCompensationResult | null>(null);
  const [jurisdictionLabel, setJurisdictionLabel] = useState<string | null>(null);
  const [laborFacts, setLaborFacts] = useState<LaborDisputeFormValue>({ ...EMPTY_LABOR_DISPUTE_FORM });
  const [laborDraft, setLaborDraft] = useState<LaborDisputeDraft | null>(null);
  const [laborSuggestions, setLaborSuggestions] = useState<LaborFactSuggestions | null>(null);
  const [suggestionDecision, setSuggestionDecision] = useState<'pending' | 'adopted' | 'dismissed'>('pending');
  const [authorityCatalog, setAuthorityCatalog] = useState<LaborAuthorityCatalog | null>(null);
  const [caseListOpen, setCaseListOpen] = useState(false);
  const [workflowStatus, setWorkflowStatus] = useState<LaborDisputeWorkflow['status'] | null>(null);

  const refreshMatters = async () => {
    try {
      setMatters(await getDigitalHumanMatters());
      setMattersError('');
    } catch (err) {
      setMattersError(err instanceof Error ? `案件记录读取失败：${err.message}` : '案件记录读取失败，请稍后重试');
    }
  };

  useEffect(() => { void refreshMatters(); }, []);
  useEffect(() => {
    if (!matterId) {
      setStep('start');
      setJurisdictionLabel(null);
      setWorkflowStatus(null);
      return;
    }
    let active = true;
    void getDigitalHumanMatter(matterId).then((detail) => {
      if (!active) return;
      setGoal(detail.goal);
      if (detail.jurisdiction?.confirmed_by_user) {
        const area = detail.jurisdiction.subdivision_code?.replace(/^CN-/, '') || '';
        setSubdivision(area);
        setConfirmed(true);
        setJurisdictionLabel(`中国${area ? ` / ${area}` : ''}`);
        setStep((current) => current === 'result' ? current : 'material');
      } else {
        setConfirmed(false);
        setJurisdictionLabel(null);
        setStep('jurisdiction');
      }
    }).catch((err) => {
      if (active) setError(err instanceof Error ? err.message : '当前案件读取失败');
    });
    void getLaborDisputeWorkflow(matterId).then((workflow) => {
      if (!active) return;
      setWorkflowStatus(workflow.status);
      setLaborFacts((current) => mergeLaborSuggestions(current, workflow.facts));
      if (workflow.facts.monthly_salary !== undefined && workflow.facts.monthly_salary !== null) {
        setSalary(String(workflow.facts.monthly_salary));
      }
    }).catch(() => { if (active) setWorkflowStatus(null); });
    return () => { active = false; };
  }, [matterId]);
  useEffect(() => {
    void getLaborAuthorityCatalog().then(setAuthorityCatalog).catch(() => setAuthorityCatalog(null));
  }, []);

  const createMatter = async () => {
    if (!goal.trim()) return;
    setLoading(true); setError('');
    try {
      const normalizedGoal = goal.trim();
      const activeSessionId = sessionId || await ensureWorkspaceSession();
      if (
        !pendingCreate.current
        || pendingCreate.current.goal !== normalizedGoal
        || pendingCreate.current.sessionId !== activeSessionId
      ) {
        pendingCreate.current = {
          goal: normalizedGoal,
          sessionId: activeSessionId,
          key: `dhm_${crypto.randomUUID()}`,
        };
      }
      const matter = await createDigitalHumanMatter(
        normalizedGoal,
        activeSessionId,
        workspaceVersion,
        pendingCreate.current.key,
      );
      if (!matter.workspace || !applyWorkspaceContext(matter.workspace)) {
        throw new Error('案件已创建，但工作区状态恢复失败，请刷新后继续');
      }
      pendingCreate.current = null;
      setLaborFacts({ ...EMPTY_LABOR_DISPUTE_FORM }); setSalary(''); setLaborDraft(null);
      setWorkflowStatus(null);
      setStep('jurisdiction'); void refreshMatters();
    } catch (err) { setError(err instanceof Error ? err.message : '创建案件失败'); }
    finally { setLoading(false); }
  };

  const confirmJurisdiction = async () => {
    if (!matterId || !confirmed) return;
    setLoading(true); setError('');
    try {
      const jurisdictionPayload = {
        country_code: 'CN', subdivision_code: subdivision.trim() || null,
        effective_at: new Date().toISOString(), confirmed_by_user: true,
      };
      if (laborRun?.matter_id === matterId && laborRun.status === 'awaiting_jurisdiction') {
        setCurrentAgentRun(await continueLaborDisputeAgentRun(
          laborRun.run_id, 'confirm_jurisdiction', jurisdictionPayload,
        ));
      } else {
        await confirmMatterJurisdiction(matterId, subdivision.trim());
      }
      setJurisdictionLabel(`中国${subdivision.trim() ? ` / ${subdivision.trim()}` : ''}`);
      setStep('material');
    }
    catch (err) { setError(err instanceof Error ? err.message : '确认法域失败'); }
    finally { setLoading(false); }
  };

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setSelectedFile(file); setFilename(file.name); setText(''); setError('');
  };

  const organizeFile = async () => {
    if (!matterId || !selectedFile) return;
    setLoading(true); setError('');
    try {
      const organized = await organizeMatterMaterial(matterId, selectedFile);
      setFilename(organized.filename); setMediaType(organized.media_type); setText(organized.text);
    } catch (err) { setError(err instanceof Error ? err.message : '材料识别失败'); }
    finally { setLoading(false); }
  };

  const analyze = async () => {
    if (!matterId || !text.trim()) return;
    setLoading(true); setError('');
    try {
      const material = await addMatterMaterial(matterId, filename || '手动录入材料.txt', text.trim(), mediaType);
      setResult(await analyzeMatterMaterial(matterId, material.document_id));
      const suggestions = await getLaborDisputeFactSuggestions(matterId);
      setLaborSuggestions(suggestions); setSuggestionDecision('pending');
      setAuthorityCatalog(await getLaborAuthorityCatalog());
      setStep('result');
    } catch (err) { setError(err instanceof Error ? err.message : '材料分析失败'); }
    finally { setLoading(false); }
  };

  const calculateLabor = async () => {
    if (!matterId) return;
    setLoading(true); setError('');
    try {
      setLaborResult(await calculateMatterLaborCompensation(
        matterId, Number(salary), Number(years), Number(months),
      ));
    } catch (err) { setError(err instanceof Error ? err.message : '补偿估算失败'); }
    finally { setLoading(false); }
  };

  const runLaborWorkflow = async () => {
    if (!matterId) return;
    setLoading(true); setError('');
    try {
      const facts = buildLaborDisputePayload(laborFacts, salary);
      const isDraftRun = laborRun?.template_id === 'labor_arbitration_application'
        || laborRun?.task_type === 'labor_arbitration_application'
        || laborRun?.task_type === 'cn_labor_dispute';
      if (laborRun?.matter_id === matterId && laborRun.status === 'awaiting_information' && isDraftRun) {
        setCurrentAgentRun(await continueLaborDisputeAgentRun(laborRun.run_id, 'provide_information', facts));
      } else {
        setCurrentAgentRun(await startLaborDisputeAgentRun(matterId, facts, 'labor_arbitration_application'));
      }
    } catch (err) { setError(err instanceof Error ? err.message : '劳动纠纷分析失败'); }
    finally { setLoading(false); }
  };

  const approveLaborDraft = async () => {
    if (!laborRun) return;
    setLoading(true); setError('');
    try {
      const completed = await continueLaborDisputeAgentRun(laborRun.run_id, 'approve', { approved: true });
      setCurrentAgentRun(completed);
      const draft = completed.final_output?.draft_labor_arbitration_application as LaborDisputeDraft | undefined;
      if (draft) setLaborDraft(draft);
    }
    catch (err) { setError(err instanceof Error ? err.message : '草稿生成失败'); }
    finally { setLoading(false); }
  };

  const retryLaborAuthorities = async () => {
    if (!laborRun) return;
    setLoading(true); setError('');
    try {
      setCurrentAgentRun(await continueLaborDisputeAgentRun(laborRun.run_id, 'retry_authority'));
    } catch (err) { setError(err instanceof Error ? err.message : '法律来源同步或验证失败'); }
    finally { setLoading(false); }
  };

  const exportLaborDraft = async (format: 'word' | 'pdf') => {
    if (!laborDraft) return;
    setError('');
    const filename = laborDraft.title.replace(/[\\/:*?"<>|]/g, '_');
    try {
      if (format === 'word') {
        await exportAsWord(laborDraft.content, { title: laborDraft.title, filename });
      } else {
        await exportAsPDF(laborDraft.content, { title: laborDraft.title, filename });
      }
    } catch {
      setError(`${format === 'word' ? 'Word' : 'PDF'} 导出失败，请稍后重试`);
    }
  };

  const adoptMaterialSuggestions = () => {
    if (!laborSuggestions) return;
    const suggested = laborSuggestions.suggested_facts;
    setLaborFacts((current) => mergeLaborSuggestions(current, suggested));
    if (suggested.monthly_salary) setSalary(String(suggested.monthly_salary));
    setSuggestionDecision('adopted');
  };

  const restoreMatter = async (matter: DigitalHumanMatterSummary) => {
    setLoading(true); setError('');
    try {
      const detail = await getDigitalHumanMatter(matter.matter_id);
      if (detail.session_id && detail.session_id !== sessionId) {
        const loaded = await loadSession(detail.session_id);
        if (!loaded) throw new Error('目标案件所属会话恢复失败');
      }
      await selectCurrentMatter(detail.matter_id);
      setGoal(detail.goal);
      if (detail.jurisdiction?.confirmed_by_user) {
        const area = detail.jurisdiction.subdivision_code?.replace(/^CN-/, '') || '';
        setSubdivision(area); setConfirmed(true); setJurisdictionLabel(`中国${area ? ` / ${area}` : ''}`);
        setStep('material');
      } else {
        setConfirmed(false); setJurisdictionLabel(null); setStep('jurisdiction');
      }
      setResult(null); setLaborResult(null);
      setLaborSuggestions(null); setSuggestionDecision('pending');
      setCaseListOpen(false);
    } catch (err) { setError(err instanceof Error ? err.message : '恢复案件失败'); }
    finally { setLoading(false); }
  };

  const startNewMatter = async () => {
    await selectCurrentMatter(null);
    setStep('start'); setGoal(''); setSubdivision(''); setConfirmed(false);
    setFilename(''); setText(''); setResult(null); setExpandedFact(null);
    setMaterialKind('text'); setMediaType('text/plain'); setSelectedFile(null);
    setSalary(''); setYears(''); setMonths('0'); setLaborResult(null);
    setJurisdictionLabel(null); setLaborFacts({ ...EMPTY_LABOR_DISPUTE_FORM });
    setLaborDraft(null); setLaborSuggestions(null); setSuggestionDecision('pending');
    setWorkflowStatus(null);
    setError(''); setCaseListOpen(false);
  };

  const removeMatter = async (matterIdToDelete: string) => {
    await deleteDigitalHumanMatter(matterIdToDelete);
    if (matterId === matterIdToDelete) {
      const restored = sessionId ? await refreshWorkspace(sessionId) : true;
      if (!restored && sessionId) await loadSession(sessionId);
      setResult(null);
    }
    await refreshMatters();
  };

  const runtimeAnalysis = (
    laborRun?.final_output?.analyze_labor_dispute
    || laborRun?.final_output?.analyze_labor_case
  ) as LaborAnalysisResult | undefined;
  const verifiedAuthorities = runtimeAnalysis?.authorities || [];
  const clientMissingLaborFacts = findMissingLaborDisputeFacts(laborFacts, salary);

  return (
    <section className="dh-matter-workspace" aria-label="案件材料工作区">
      <div className="dh-matter-topbar">
        <div className="dh-matter-heading"><FileSearch size={17} /><div><strong>案件工作台</strong><small>材料、事实与法源</small></div></div>
        <div className="dh-matter-actions"><button type="button" onClick={() => setCaseListOpen((open) => !open)} aria-expanded={caseListOpen}><History size={14} />历史案件{matters.length ? `（${matters.length}）` : ''}</button><button type="button" className="primary" onClick={() => void startNewMatter()}><Plus size={14} />新建案件</button></div>
      </div>
      {mattersError && <p className="dh-matter-error">{mattersError} <button type="button" onClick={() => void refreshMatters()}>重新读取</button></p>}
      {caseListOpen && <section className="dh-case-browser" aria-label="历史案件列表"><div><strong>历史案件</strong><button type="button" onClick={() => setCaseListOpen(false)}>收起</button></div>{matters.length === 0 ? <p>暂无历史案件</p> : matters.map((matter) => <article key={matter.matter_id}><button type="button" onClick={() => void restoreMatter(matter)}><span>{matter.title}</span><small>{matter.matter_id === matterId ? '当前案件' : '继续处理'}</small></button><button type="button" aria-label={`删除案件：${matter.title}`} onClick={() => void removeMatter(matter.matter_id)}><Trash2 size={13} /></button></article>)}</section>}
      {matterId && <section className="dh-current-case"><div><span>当前案件</span><strong>{goal}</strong></div><em>{matterStatusLabel(laborRun?.status, workflowStatus)}</em></section>}
      {jurisdictionLabel && <p className="dh-jurisdiction-status"><CheckCircle2 size={14} />已确认法域：{jurisdictionLabel}</p>}
      <div className="dh-matter-steps">
        {['创建案件', '确认法域', '添加材料', '查看分析'].map((label, index) => {
          const current = ['start', 'jurisdiction', 'material', 'result'].indexOf(step);
          return <span key={label} className={index <= current ? 'active' : ''}>{index + 1}<em>{label}</em></span>;
        })}
      </div>

      {step === 'start' && <div className="dh-matter-form">
        <label>你想解决什么问题？</label>
        <textarea value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="例如：整理解除劳动合同相关材料" rows={2} />
        <button onClick={() => void createMatter()} disabled={loading || !goal.trim()}>{loading ? '正在创建…' : '开始材料分析'}</button>
      </div>}

      {step === 'jurisdiction' && <div className="dh-matter-form">
        <label><MapPin size={14} />适用法域</label>
        <div className="dh-jurisdiction-row"><span>中国</span><input value={subdivision} onChange={(e) => setSubdivision(e.target.value)} placeholder="省市，可选，如北京" /></div>
        <p className="dh-jurisdiction-help">劳动补偿工具目前只支持中国法域。省市可以不填，只需确认一次。</p>
        <label className="dh-confirm-check"><input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />我确认本案件按中国法域进行初步整理</label>
        <button onClick={() => void confirmJurisdiction()} disabled={loading || !confirmed}>{loading ? '正在保存…' : '确认中国法域并继续'}</button>
      </div>}

      {step === 'material' && <div className="dh-matter-form">
        <label>添加并整理案件材料</label>
        <p className="dh-material-help">你只需提供原始材料，智能体负责识别和整理。识别文字会显示在下方，你可以修改，确认后才写入当前仲裁案件。</p>
        <div className="dh-material-kinds" role="tablist" aria-label="材料格式">
          {MATERIAL_OPTIONS.map((option) => <button
            type="button" role="tab" aria-selected={materialKind === option.kind}
            className={materialKind === option.kind ? 'active' : ''} key={option.kind}
            onClick={() => {
              setMaterialKind(option.kind); setSelectedFile(null); setFilename(''); setText('');
              setMediaType(option.kind === 'text' ? 'text/plain' : 'application/octet-stream'); setError('');
            }}
          >{option.label}</button>)}
        </div>
        {materialKind === 'text' ? <>
          <input value={filename} onChange={(e) => setFilename(e.target.value)} placeholder="材料名称（可选），例如：与财务的聊天记录" />
          <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder={MATERIAL_OPTIONS[0].hint} rows={7} />
        </> : <>
          <label className="dh-file-picker"><Upload size={15} />{selectedFile ? `已选择：${selectedFile.name}` : `选择${MATERIAL_OPTIONS.find((item) => item.kind === materialKind)?.label}材料`}
            <input type="file" accept={MATERIAL_OPTIONS.find((item) => item.kind === materialKind)?.accept} onChange={selectFile} />
          </label>
          <small className="dh-material-format-hint">{MATERIAL_OPTIONS.find((item) => item.kind === materialKind)?.hint}，单个文件不超过 25MB。</small>
          <button type="button" onClick={() => void organizeFile()} disabled={loading || !selectedFile}>{loading ? '正在识别整理…' : '识别并整理材料'}</button>
          {text && <div className="dh-material-preview">
            <label><CheckCircle2 size={14} />智能体整理稿（请核对，可直接修改）</label>
            <input value={filename} onChange={(e) => setFilename(e.target.value)} aria-label="材料名称" />
            <textarea value={text} onChange={(e) => setText(e.target.value)} rows={9} />
          </div>}
        </>}
        <button onClick={() => void analyze()} disabled={loading || !text.trim()}>{loading ? '处理中…' : '确认整理稿并进入仲裁分析'}</button>
      </div>}

      {step === 'result' && result && <div className="dh-analysis-result">
        <div className="dh-result-summary"><span><b>{result.facts.length}</b>条事实</span><span><b>{result.timeline.length}</b>个时间点</span><span><b>{result.checklist.available.length}</b>份材料</span><span><b>{verifiedAuthorities.length || '待'}</b>校验法源</span></div>
        <h4>事实出处</h4>
        {result.facts.length === 0 ? <p className="dh-result-empty">未识别到带日期、金额或“事实：”标记的句子。</p> : result.facts.map((fact: LocatedLegalFact) => <article key={fact.fact_id} className="dh-fact-item">
          <button onClick={() => setExpandedFact(expandedFact === fact.fact_id ? null : fact.fact_id)}><span><CheckCircle2 size={14} />{fact.fact_text}</span>{expandedFact === fact.fact_id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</button>
          {expandedFact === fact.fact_id && <div><p>来源：{result.checklist.available.find((item) => item.document_id === fact.material_ref.document_id)?.filename || '当前材料'}</p><p>位置：第 {fact.material_ref.start_offset + 1}–{fact.material_ref.end_offset} 字</p><blockquote>“{fact.material_ref.quote}”</blockquote></div>}
        </article>)}
        {result.timeline.length > 0 && <><h4>时间线</h4>{result.timeline.map((item) => <p className="dh-timeline-item" key={`${item.fact_id}-${item.date}`}><time>{item.date}</time>{item.event}</p>)}</>}
        <section className="dh-source-notice">
          <strong>官方法源库：{authorityCatalog?.status === 'ready' ? `已就绪（${authorityCatalog.count} 条）` : authorityCatalog?.status === 'degraded' ? '部分可用，确定性结论仍受限' : '暂不可用'}</strong>
          <p>系统不是临时上网搜索。它先把白名单内的官方条款保存到法源库，再按案件法域、日期和争议主题筛选；找不到有效依据就停止生成。</p>
          {authorityCatalog?.governance.pending_review_count ? <p>有 {authorityCatalog.governance.pending_review_count} 组官网正文变化正在等待法律专业人员复核，复核前不会作为确定依据。</p> : null}
          {authorityCatalog && (authorityCatalog.governance.stale_count || authorityCatalog.governance.missing_count || authorityCatalog.governance.failed_count) ? <p>当前过期 {authorityCatalog.governance.stale_count} 组、缺失 {authorityCatalog.governance.missing_count} 组、失败 {authorityCatalog.governance.failed_count} 组。</p> : null}
          {authorityCatalog?.authorities.map((item) => <p key={item.authority_id}>• <a href={item.source_url} target="_blank" rel="noreferrer">{item.title} {item.provision || ''}</a> · {item.issuing_body} · 版本 {item.version}</p>)}
        </section>
        <div className="dh-labor-tool">
          <h4><Calculator size={14} />功能一：劳动补偿快速估算</h4>
          <p>只计算一个参考金额，不生成仲裁材料。依次填写月工资、完整工作年数和额外月数。</p>
          <div className="dh-labor-tool-inputs"><input type="number" min="0" value={salary} onChange={(e) => setSalary(e.target.value)} placeholder="月工资" /><input type="number" min="0" value={years} onChange={(e) => setYears(e.target.value)} placeholder="工作年数" /><input type="number" min="0" max="11" value={months} onChange={(e) => setMonths(e.target.value)} placeholder="额外月数" /></div>
          <button onClick={() => void calculateLabor()} disabled={loading || !salary || !years}>{loading ? '计算中…' : '计算参考补偿金额'}</button>
          {laborResult && <section><strong>估算结果：¥{laborResult.compensation.toLocaleString()}</strong><p>{laborResult.calculation}</p><small>{laborResult.warning}</small></section>}
        </div>
        <div className="dh-labor-tool">
          <h4>功能二：生成劳动仲裁申请书</h4>
          <p>核对材料和确认事实，检查证据、仲裁时效及官方法源；通过后征求你的确认，再生成申请书草稿。</p>
          {laborSuggestions?.fields.length && suggestionDecision === 'pending' ? <section className="dh-suggestion-card">
            <strong>已从材料中提取 {laborSuggestions.fields.length} 项候选信息</strong>
            <small>{laborSuggestions.warning}</small>
            {laborSuggestions.fields.map((item) => <details key={item.field}>
              <summary>{item.label}：{Array.isArray(item.value) ? item.value.join('、') : item.value}</summary>
              <blockquote>{item.sources[0]?.quote}</blockquote>
            </details>)}
            <div><button type="button" onClick={adoptMaterialSuggestions}>采用材料建议</button><button type="button" onClick={() => setSuggestionDecision('dismissed')}>暂不采用，我自己填写</button></div>
          </section> : null}
          {suggestionDecision === 'adopted' && <p className="dh-suggestion-status"><CheckCircle2 size={14} />已采用材料建议，下面字段仍可修改</p>}
          <LaborDisputeForm
            value={laborFacts}
            monthlySalary={salary}
            missingFacts={clientMissingLaborFacts}
            disabled={loading || laborRun?.status === 'awaiting_approval'}
            onChange={setLaborFacts}
            onMonthlySalaryChange={setSalary}
          />
          <button onClick={() => void runLaborWorkflow()} disabled={loading || clientMissingLaborFacts.length > 0 || laborRun?.status === 'blocked_authority' || laborRun?.status === 'awaiting_approval'}>{loading ? '分析中…' : clientMissingLaborFacts.length > 0 ? `还需填写 ${clientMissingLaborFacts.length} 项必填信息` : laborRun?.status === 'failed' ? '重新开始新的分析任务' : '检查证据、期限和法源'}</button>
          {laborRun && <section><strong>Agent 状态：{({ planning: '正在规划', awaiting_jurisdiction: '等待确认法域', awaiting_information: '等待补充事实', executing: '正在执行', verifying: '正在校验', retrying: '正在重试', awaiting_approval: '等待你确认生成草稿', blocked_authority: '缺少有效法源，已暂停', replanning: '正在重新规划', human_handoff: '需要人工处理', completed: '已完成', failed: '任务失败', cancelled: '已取消' } as Record<string, string>)[laborRun.status] || laborRun.status}</strong>{laborRun.steps.map((item) => <p key={item.id}>• {item.name}：{laborStepStatusLabel(item, laborRun)}</p>)}{laborRun.error_code === 'BUDGET_EXCEEDED' && <p className="dh-source-notice">这个旧任务重复执行次数过多，已达到工具调用上限。请点击“重新开始新的分析任务”，系统会创建新任务，不影响案件材料。</p>}</section>}
          {laborRun?.questions.length ? <section><strong>还需要补充</strong>{laborRun.questions.map((question) => <p key={question}>• {question}</p>)}</section> : null}
          {laborRun?.blocked_reason && <p className="dh-source-notice">{humanizeLaborMessage(laborRun.blocked_reason)}</p>}
          <LaborRuleResults decisions={runtimeAnalysis?.rule_decisions || []} />
          {runtimeAnalysis?.deadline && <section><strong>初步期限：{runtimeAnalysis.deadline.estimated_deadline || '劳动关系终止后另行起算'}</strong>{runtimeAnalysis.deadline.assumptions.map((item) => <small key={item}>{item}</small>)}{runtimeAnalysis.deadline.warnings.map((item) => <small key={item}>{item}</small>)}</section>}
          {verifiedAuthorities.length > 0 && <section><strong>已验证法律来源（{verifiedAuthorities.length}）</strong>{verifiedAuthorities.map((item) => <p key={item.authority_id}>• <a href={item.source_url} target="_blank" rel="noreferrer">{item.title} {item.provision || ''}</a> · {item.issuing_body} · 版本 {item.version}</p>)}</section>}
          {laborRun?.status === 'blocked_authority' && <button onClick={() => void retryLaborAuthorities()} disabled={loading}>{loading ? '正在同步并验证…' : '同步并重新验证法律来源'}</button>}
          {laborRun?.status === 'awaiting_approval' && <button onClick={() => void approveLaborDraft()} disabled={loading}>{laborRun.approval?.prompt || '确认并生成仲裁申请书草稿'}</button>}
          {laborDraft && <section className="dh-draft-result"><strong>{laborDraft.title}</strong><pre className="dh-draft-preview">{laborDraft.content}</pre><div className="dh-draft-actions"><button type="button" onClick={() => void exportLaborDraft('word')}><Download size={14} />导出 Word</button><button type="button" onClick={() => void exportLaborDraft('pdf')}><FileText size={14} />导出 PDF</button></div><small>导出文件仍是待复核草稿，不代表已向仲裁机构提交。</small></section>}
        </div>
        <p className="dh-result-warning">{result.checklist.warning}</p>
        <button className="dh-secondary-button" onClick={() => { setStep('material'); setResult(null); }}>继续添加材料</button>
      </div>}
      {error && <p className="dh-matter-error">{error}</p>}
    </section>
  );
}
