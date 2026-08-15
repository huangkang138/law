'use client';

import { CheckCircle2, MapPin, Target } from 'lucide-react';

import type { WorkspaceStep } from './useMatterWorkspace';
import styles from './Workspace.module.css';

interface JurisdictionStageProps {
  matterId: string | null;
  step: WorkspaceStep;
  goal: string;
  onGoalChange: (value: string) => void;
  subdivision: string;
  onSubdivisionChange: (value: string) => void;
  confirmed: boolean;
  onConfirmedChange: (value: boolean) => void;
  jurisdictionLabel: string | null;
  loading: boolean;
  error: string;
  onCreateMatter: () => void;
  onConfirmJurisdiction: () => void;
}

/** 阶段一：目标与法域（创建案件 / 问题目标 / 中国法域与省市确认）。 */
export default function JurisdictionStage({
  matterId, step, goal, onGoalChange, subdivision, onSubdivisionChange,
  confirmed, onConfirmedChange, jurisdictionLabel, loading, error,
  onCreateMatter, onConfirmJurisdiction,
}: JurisdictionStageProps) {
  return (
    <section className={styles.stageSection} aria-label="阶段一：目标与法域">
      <h3 className={styles.stageTitle}><Target size={16} />目标与法域</h3>
      {jurisdictionLabel && <p className="dh-jurisdiction-status"><CheckCircle2 size={14} />已确认法域：{jurisdictionLabel}</p>}

      {(!matterId || step === 'start') && <div className="dh-matter-form">
        <label>你想解决什么问题？</label>
        <textarea value={goal} onChange={(e) => onGoalChange(e.target.value)} placeholder="例如：整理解除劳动合同相关材料" rows={2} />
        <p className={styles.stageHint}>创建案件后，材料、事实、证据、分析与文书都会持续沉淀在这个案件里。</p>
        <button onClick={onCreateMatter} disabled={loading || !goal.trim()}>{loading ? '正在创建…' : '创建案件并继续'}</button>
      </div>}

      {matterId && step === 'jurisdiction' && <div className="dh-matter-form">
        <label><MapPin size={14} />适用法域</label>
        <div className="dh-jurisdiction-row"><span>中国</span><input value={subdivision} onChange={(e) => onSubdivisionChange(e.target.value)} placeholder="省市，可选，如北京" /></div>
        <p className="dh-jurisdiction-help">劳动补偿工具目前只支持中国法域。省市可以不填，只需确认一次。</p>
        <label className="dh-confirm-check"><input type="checkbox" checked={confirmed} onChange={(e) => onConfirmedChange(e.target.checked)} />我确认本案件按中国法域进行初步整理</label>
        <button onClick={onConfirmJurisdiction} disabled={loading || !confirmed}>{loading ? '正在保存…' : '确认中国法域并继续'}</button>
      </div>}

      {matterId && step !== 'start' && step !== 'jurisdiction' && (
        <p className={styles.stageDone}>法域已确认，可在上方切换到「材料整理」继续办理。</p>
      )}
      {error && <p className="dh-matter-error">{error}</p>}
    </section>
  );
}
