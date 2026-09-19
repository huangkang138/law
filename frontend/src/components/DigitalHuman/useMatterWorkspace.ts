'use client';

// 案件工作台统一逻辑容器：持有全部业务 state 与跨阶段动作（原
// DigitalHumanMatterWorkspace 的内容按用户约束原样搬移，不重构业务状态架构），
// 由 CaseWorkspaceShell 调用一次，四个 Stage 组件只接收 props 做展示。

import { ChangeEvent, useEffect, useRef, useState } from 'react';

import { exportAsPDF, exportAsWord } from '@/lib/exportUtils';

import {
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
import { CaseStage, useDigitalHumanStore } from '@/store/digitalHumanStore';
import LaborDisputeForm, {
  EMPTY_LABOR_DISPUTE_FORM,
  LaborDisputeFormValue,
  buildLaborDisputePayload,
  findMissingLaborDisputeFacts,
  laborFactLabel,
  mergeLaborSuggestions,
} from './LaborDisputeForm';

// 供展示组件（AnalysisDocumentStage）复用，避免各 Stage 直连表单工具。
export { humanizeLaborMessage } from './LaborDisputeForm';

export type WorkspaceStep = 'start' | 'jurisdiction' | 'material' | 'result';
export type MaterialKind = 'text' | 'document' | 'image' | 'media';

export const MATERIAL_OPTIONS: Array<{ kind: MaterialKind; label: string; accept: string; hint: string }> = [
  { kind: 'text', label: '粘贴文字', accept: '.txt,text/plain', hint: '粘贴聊天记录、工资说明等文字' },
  { kind: 'document', label: 'Word / PDF', accept: '.docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document', hint: '劳动合同、工资单、解除通知' },
  { kind: 'image', label: '图片', accept: '.png,.jpg,.jpeg,image/png,image/jpeg', hint: '聊天截图、考勤或转账截图' },
  { kind: 'media', label: '音频 / 视频', accept: '.mp3,.wav,.m4a,.mp4,.mov,.avi,audio/*,video/*', hint: '录音或包含有效声音的视频' },
];

export function laborStepStatusLabel(
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

export function matterStatusLabel(
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

// 按案件状态推导默认阶段（仅在案件变化/恢复时使用，用户手动切换优先）。
export function deriveCaseStage(
  jurisdictionConfirmed: boolean,
  workflowStatus: LaborDisputeWorkflow['status'] | null,
): CaseStage {
  if (!jurisdictionConfirmed) return 'jurisdiction';
  switch (workflowStatus) {
    case 'awaiting_draft_approval':
    case 'completed':
    case 'blocked_authority':
      return 'analysis';
    case 'awaiting_information':
      return 'facts';
    default:
      return 'material';
  }
}

export interface MatterWorkspaceFlow {
  matterId: string | null;
  step: WorkspaceStep;
  goal: string;
  setGoal: (value: string) => void;
  subdivision: string;
  setSubdivision: (value: string) => void;
  confirmed: boolean;
  setConfirmed: (value: boolean) => void;
  filename: string;
  setFilename: (value: string) => void;
  text: string;
  setText: (value: string) => void;
  mediaType: string;
  materialKind: MaterialKind;
  switchMaterialKind: (kind: MaterialKind) => void;
  selectedFile: File | null;
  result: MatterAnalysisResult | null;
  expandedFact: string | null;
  setExpandedFact: (id: string | null) => void;
  loading: boolean;
  error: string;
  matters: DigitalHumanMatterSummary[];
  mattersError: string;
  matterStatuses: Record<string, LaborDisputeWorkflow['status'] | null>;
  statusesLoading: boolean;
  salary: string;
  setSalary: (value: string) => void;
  years: string;
  setYears: (value: string) => void;
  months: string;
  setMonths: (value: string) => void;
  laborResult: LaborCompensationResult | null;
  jurisdictionLabel: string | null;
  laborFacts: LaborDisputeFormValue;
  setLaborFacts: (value: LaborDisputeFormValue) => void;
  laborDraft: LaborDisputeDraft | null;
  laborSuggestions: LaborFactSuggestions | null;
  suggestionDecision: 'pending' | 'adopted' | 'dismissed';
  setSuggestionDecision: (value: 'pending' | 'adopted' | 'dismissed') => void;
  authorityCatalog: LaborAuthorityCatalog | null;
  workflowStatus: LaborDisputeWorkflow['status'] | null;
  runtimeAnalysis: LaborAnalysisResult | undefined;
  verifiedAuthorities: NonNullable<LaborAnalysisResult['authorities']>;
  clientMissingLaborFacts: string[];
  refreshMatters: () => Promise<void>;
  createMatter: () => Promise<void>;
  confirmJurisdiction: () => Promise<void>;
  selectFile: (event: ChangeEvent<HTMLInputElement>) => void;
  organizeFile: () => Promise<void>;
  analyze: () => Promise<void>;
  calculateLabor: () => Promise<void>;
  runLaborWorkflow: () => Promise<void>;
  approveLaborDraft: () => Promise<void>;
  retryLaborAuthorities: () => Promise<void>;
  exportLaborDraft: (format: 'word' | 'pdf') => Promise<void>;
  adoptMaterialSuggestions: () => void;
  restoreMatter: (matter: DigitalHumanMatterSummary) => Promise<void>;
  startNewMatter: () => Promise<void>;
  removeMatter: (matterIdToDelete: string) => Promise<void>;
}

export function useMatterWorkspace(): MatterWorkspaceFlow {
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
    setActiveStage,
    workspaceVersion,
  } = useDigitalHumanStore();
  const [step, setStep] = useState<WorkspaceStep>('start');
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
  const [workflowStatus, setWorkflowStatus] = useState<LaborDisputeWorkflow['status'] | null>(null);
  // 侧栏案件状态缓存：批量并行、按 matterId 缓存、只补缺失，避免逐行 N+1。
  const [matterStatuses, setMatterStatuses] = useState<Record<string, LaborDisputeWorkflow['status'] | null>>({});
  const [statusesLoading, setStatusesLoading] = useState(false);

  const confirmedRef = useRef(false);
  const sidebarTab = useDigitalHumanStore((state) => state.sidebarTab);
  const workspaceGoalDraft = useDigitalHumanStore((state) => state.workspaceGoalDraft);

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
      confirmedRef.current = false;
      setActiveStage('jurisdiction');
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
        confirmedRef.current = true;
        setJurisdictionLabel(`中国${area ? ` / ${area}` : ''}`);
        setStep((current) => current === 'result' ? current : 'material');
      } else {
        setConfirmed(false);
        confirmedRef.current = false;
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
      // 案件变化/恢复时按权威状态推导默认阶段；用户手动切换优先。
      setActiveStage(deriveCaseStage(confirmedRef.current, workflow.status));
    }).catch(() => { if (active) setWorkflowStatus(null); });
    return () => { active = false; };
  }, [matterId]);
  useEffect(() => {
    void getLaborAuthorityCatalog().then(setAuthorityCatalog).catch(() => setAuthorityCatalog(null));
  }, []);

  // 聊天入口"从当前对话创建案件"预填目标：只做一次，用后即清。
  useEffect(() => {
    if (workspaceGoalDraft && !matterId && step === 'start') {
      setGoal(workspaceGoalDraft);
      useDigitalHumanStore.getState().setWorkspaceGoalDraft(null);
    }
  }, [workspaceGoalDraft, matterId, step]);

  // 侧栏"案件"页打开时批量补齐案件状态（并行 + 缓存 + 只补缺失）。
  useEffect(() => {
    if (sidebarTab !== 'matters') return;
    const missing = matters.filter((matter) => !(matter.matter_id in matterStatuses));
    if (!missing.length) return;
    let active = true;
    setStatusesLoading(true);
    void Promise.allSettled(
      missing.map((matter) => getLaborDisputeWorkflow(matter.matter_id)),
    ).then((results) => {
      if (!active) return;
      setMatterStatuses((current) => {
        const next = { ...current };
        missing.forEach((matter, index) => {
          const settled = results[index];
          next[matter.matter_id] = settled.status === 'fulfilled' ? settled.value.status : null;
        });
        return next;
      });
      setStatusesLoading(false);
    });
    return () => { active = false; };
  }, [sidebarTab, matters, matterStatuses]);

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
      setActiveStage('material');
    }
    catch (err) { setError(err instanceof Error ? err.message : '确认法域失败'); }
    finally { setLoading(false); }
  };

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setSelectedFile(file); setFilename(file.name); setText(''); setError('');
  };

  const switchMaterialKind = (kind: MaterialKind) => {
    setMaterialKind(kind); setSelectedFile(null); setFilename(''); setText('');
    setMediaType(kind === 'text' ? 'text/plain' : 'application/octet-stream'); setError('');
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
      setActiveStage('facts');
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
      setActiveStage('analysis');
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
    const draftFilename = laborDraft.title.replace(/[\\/:*?"<>|]/g, '_');
    try {
      if (format === 'word') {
        await exportAsWord(laborDraft.content, { title: laborDraft.title, filename: draftFilename });
      } else {
        await exportAsPDF(laborDraft.content, { title: laborDraft.title, filename: draftFilename });
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
        setSubdivision(area); setConfirmed(true); confirmedRef.current = true;
        setJurisdictionLabel(`中国${area ? ` / ${area}` : ''}`);
        setStep('material');
        setActiveStage('material');
      } else {
        setConfirmed(false); confirmedRef.current = false;
        setJurisdictionLabel(null); setStep('jurisdiction');
        setActiveStage('jurisdiction');
      }
      setResult(null); setLaborResult(null);
      setLaborSuggestions(null); setSuggestionDecision('pending');
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
    setError('');
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
  const claimTypes = Array.isArray(laborFacts.claim_types)
    ? laborFacts.claim_types.map(String)
    : String(laborFacts.claim_types || '').split(/[、,，]/).filter(Boolean);
  const relevantAuthorityIds = new Set([
    'npc-labor-arbitration-law-27',
    'mohrss-arbitration-rules-26-28',
    ...(claimTypes.some((item) => ['欠薪', '加班费'].includes(item)) ? ['samr-labor-law-wages'] : []),
    ...(claimTypes.some((item) => ['欠薪', '违法解除', '解除', '赔偿金', '经济补偿'].includes(item))
      ? ['samr-labor-contract-law-substantive']
      : []),
  ]);
  const catalogAuthorities = authorityCatalog?.authorities.filter(
    (authority) => !authority.external_id || relevantAuthorityIds.has(authority.external_id),
  ) || [];
  const verifiedAuthorities = catalogAuthorities.length > 0
    ? catalogAuthorities
    : runtimeAnalysis?.authorities || [];
  const clientMissingLaborFacts = findMissingLaborDisputeFacts(laborFacts, salary);

  return {
    matterId,
    step,
    goal, setGoal,
    subdivision, setSubdivision,
    confirmed, setConfirmed,
    filename, setFilename,
    text, setText,
    mediaType,
    materialKind, switchMaterialKind,
    selectedFile,
    result,
    expandedFact, setExpandedFact,
    loading,
    error,
    matters,
    mattersError,
    matterStatuses,
    statusesLoading,
    salary, setSalary,
    years, setYears,
    months, setMonths,
    laborResult,
    jurisdictionLabel,
    laborFacts, setLaborFacts,
    laborDraft,
    laborSuggestions,
    suggestionDecision, setSuggestionDecision,
    authorityCatalog,
    workflowStatus,
    runtimeAnalysis,
    verifiedAuthorities,
    clientMissingLaborFacts,
    refreshMatters,
    createMatter,
    confirmJurisdiction,
    selectFile,
    organizeFile,
    analyze,
    calculateLabor,
    runLaborWorkflow,
    approveLaborDraft,
    retryLaborAuthorities,
    exportLaborDraft,
    adoptMaterialSuggestions,
    restoreMatter,
    startNewMatter,
    removeMatter,
  };
}
