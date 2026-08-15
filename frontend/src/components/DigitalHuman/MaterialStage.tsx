'use client';

import { ChangeEvent } from 'react';
import { CheckCircle2, ChevronRight, FileStack, Upload } from 'lucide-react';

import type { MatterAnalysisResult } from '@/services/digitalHumanApi';
import { MATERIAL_OPTIONS, MaterialKind } from './useMatterWorkspace';
import styles from './Workspace.module.css';

interface MaterialStageProps {
  matterId: string | null;
  materialKind: MaterialKind;
  onSwitchMaterialKind: (kind: MaterialKind) => void;
  selectedFile: File | null;
  filename: string;
  onFilenameChange: (value: string) => void;
  text: string;
  onTextChange: (value: string) => void;
  loading: boolean;
  error: string;
  result: MatterAnalysisResult | null;
  onSelectFile: (event: ChangeEvent<HTMLInputElement>) => void;
  onOrganize: () => void;
  onAnalyze: () => void;
  onOpenFacts: () => void;
}

/** 阶段二：材料整理（文字/Word/PDF/图片/音视频上传、整理稿、已有与缺失材料）。 */
export default function MaterialStage({
  matterId, materialKind, onSwitchMaterialKind, selectedFile, filename,
  onFilenameChange, text, onTextChange, loading, error, result,
  onSelectFile, onOrganize, onAnalyze, onOpenFacts,
}: MaterialStageProps) {
  return (
    <section className={styles.stageSection} aria-label="阶段二：材料整理">
      <h3 className={styles.stageTitle}><FileStack size={16} />材料整理</h3>
      {!matterId ? (
        <p className={styles.stageHint}>先在「目标与法域」创建或选择案件，再添加材料。</p>
      ) : (
        <div className="dh-matter-form">
          <p className="dh-material-help">你只需提供原始材料，智能体负责识别和整理。识别文字会显示在下方，你可以修改，确认后才写入当前仲裁案件。</p>
          <div className="dh-material-kinds" role="tablist" aria-label="材料格式">
            {MATERIAL_OPTIONS.map((option) => <button
              type="button" role="tab" aria-selected={materialKind === option.kind}
              className={materialKind === option.kind ? 'active' : ''} key={option.kind}
              onClick={() => onSwitchMaterialKind(option.kind)}
            >{option.label}</button>)}
          </div>
          {materialKind === 'text' ? <>
            <input value={filename} onChange={(e) => onFilenameChange(e.target.value)} placeholder="材料名称（可选），例如：与财务的聊天记录" />
            <textarea value={text} onChange={(e) => onTextChange(e.target.value)} placeholder={MATERIAL_OPTIONS[0].hint} rows={7} />
          </> : <>
            <label className="dh-file-picker"><Upload size={15} />{selectedFile ? `已选择：${selectedFile.name}` : `选择${MATERIAL_OPTIONS.find((item) => item.kind === materialKind)?.label}材料`}
              <input type="file" accept={MATERIAL_OPTIONS.find((item) => item.kind === materialKind)?.accept} onChange={onSelectFile} />
            </label>
            <small className="dh-material-format-hint">{MATERIAL_OPTIONS.find((item) => item.kind === materialKind)?.hint}，单个文件不超过 25MB。</small>
            <button type="button" onClick={onOrganize} disabled={loading || !selectedFile}>{loading ? '正在识别整理…' : '识别并整理材料'}</button>
            {text && <div className="dh-material-preview">
              <label><CheckCircle2 size={14} />智能体整理稿（请核对，可直接修改）</label>
              <input value={filename} onChange={(e) => onFilenameChange(e.target.value)} aria-label="材料名称" />
              <textarea value={text} onChange={(e) => onTextChange(e.target.value)} rows={9} />
            </div>}
          </>}
          <button onClick={onAnalyze} disabled={loading || !text.trim()}>{loading ? '处理中…' : '确认整理稿并进入仲裁分析'}</button>
        </div>
      )}

      {result && (
        <div className={styles.stagePanel}>
          <div className="dh-result-summary">
            <span><b>{result.facts.length}</b>条事实</span>
            <span><b>{result.timeline.length}</b>个时间点</span>
            <span><b>{result.checklist.available.length}</b>份材料</span>
            <span><b>{result.checklist.missing.length}</b>项缺失</span>
          </div>
          <h4 className={styles.panelTitle}>已有材料</h4>
          {result.checklist.available.length === 0
            ? <p className={styles.panelEmpty}>暂未识别到材料记录。</p>
            : result.checklist.available.map((item) => (
              <p className={styles.panelLine} key={item.document_id}>✓ {item.filename}</p>
            ))}
          <h4 className={styles.panelTitle}>缺失材料 / 建议补充</h4>
          {result.checklist.missing.length === 0
            ? <p className={styles.panelLineOk}>当前材料已覆盖识别清单，暂无缺口提示。</p>
            : result.checklist.missing.map((item) => (
              <p className={styles.panelLineWarn} key={item}>⚠ {item}</p>
            ))}
          <button className={styles.panelAction} onClick={onOpenFacts}>查看事实与证据<ChevronRight size={14} /></button>
        </div>
      )}
      {error && <p className="dh-matter-error">{error}</p>}
    </section>
  );
}
