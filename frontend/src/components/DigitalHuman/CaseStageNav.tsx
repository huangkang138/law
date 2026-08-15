'use client';

import { CASE_STAGE_LABELS, CaseStage } from '@/store/digitalHumanStore';
import styles from './Workspace.module.css';

const STAGE_ORDER: CaseStage[] = ['jurisdiction', 'material', 'facts', 'analysis'];

interface CaseStageNavProps {
  activeStage: CaseStage;
  onSelect: (stage: CaseStage) => void;
  materialCount: number | null;
  factCount: number | null;
  hasRun: boolean;
}

/** 四阶段进度导航：顶部只展示流程进度，主体一次只展示当前阶段。 */
export default function CaseStageNav({
  activeStage, onSelect, materialCount, factCount, hasRun,
}: CaseStageNavProps) {
  return (
    <nav className={styles.stageNav} aria-label="案件办理阶段">
      {STAGE_ORDER.map((stage, index) => {
        const active = stage === activeStage;
        const badge = stage === 'material' && materialCount !== null
          ? `${materialCount}份`
          : stage === 'facts' && factCount !== null
            ? `${factCount}条`
            : stage === 'analysis' && hasRun
              ? '执行中'
              : null;
        return (
          <button
            key={stage}
            type="button"
            className={`${styles.stageNavItem} ${active ? styles.stageNavItemActive : ''}`}
            onClick={() => onSelect(stage)}
            aria-current={active ? 'step' : undefined}
          >
            <span className={styles.stageNavIndex}>{index + 1}</span>
            {CASE_STAGE_LABELS[stage]}
            {badge && <small className={styles.stageNavBadge}>{badge}</small>}
          </button>
        );
      })}
    </nav>
  );
}
