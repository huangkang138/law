'use client';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';
import AnalysisDocumentStage from './AnalysisDocumentStage';
import FactEvidenceStage from './FactEvidenceStage';
import JurisdictionStage from './JurisdictionStage';
import MaterialStage from './MaterialStage';
import { MatterWorkspaceFlow } from './useMatterWorkspace';
import styles from './Workspace.module.css';

interface CaseStageContentProps {
  flow: MatterWorkspaceFlow;
}

/**
 * 阶段内容分发层：阶段切换只切换渲染的 Stage 组件（其余不挂载）。
 * 业务 state 全部来自统一逻辑容器 useMatterWorkspace（shell 调用一次），
 * 这里仅把每个 Stage 需要的 props 显式传递下去。
 */
export default function CaseStageContent({ flow }: CaseStageContentProps) {
  const activeStage = useDigitalHumanStore((state) => state.activeStage);
  const setActiveStage = useDigitalHumanStore((state) => state.setActiveStage);
  const laborRun = useDigitalHumanStore((state) => state.currentAgentRun);

  return (
    <div className={styles.stageContent}>
      {activeStage === 'jurisdiction' && (
        <JurisdictionStage
          matterId={flow.matterId ?? null}
          step={flow.step}
          goal={flow.goal}
          onGoalChange={flow.setGoal}
          subdivision={flow.subdivision}
          onSubdivisionChange={flow.setSubdivision}
          confirmed={flow.confirmed}
          onConfirmedChange={flow.setConfirmed}
          jurisdictionLabel={flow.jurisdictionLabel}
          loading={flow.loading}
          error={flow.error}
          onCreateMatter={() => void flow.createMatter()}
          onConfirmJurisdiction={() => void flow.confirmJurisdiction()}
        />
      )}
      {activeStage === 'material' && (
        <MaterialStage
          matterId={flow.matterId ?? null}
          materialKind={flow.materialKind}
          onSwitchMaterialKind={flow.switchMaterialKind}
          selectedFile={flow.selectedFile}
          filename={flow.filename}
          onFilenameChange={flow.setFilename}
          text={flow.text}
          onTextChange={flow.setText}
          loading={flow.loading}
          error={flow.error}
          result={flow.result}
          onSelectFile={flow.selectFile}
          onOrganize={() => void flow.organizeFile()}
          onAnalyze={() => void flow.analyze()}
          onOpenFacts={() => setActiveStage('facts')}
        />
      )}
      {activeStage === 'facts' && (
        <FactEvidenceStage
          matterId={flow.matterId ?? null}
          result={flow.result}
          expandedFact={flow.expandedFact}
          onExpandedFactChange={flow.setExpandedFact}
          laborSuggestions={flow.laborSuggestions}
          suggestionDecision={flow.suggestionDecision}
          onSuggestionDecisionChange={flow.setSuggestionDecision}
          laborFacts={flow.laborFacts}
          onLaborFactsChange={flow.setLaborFacts}
          salary={flow.salary}
          onSalaryChange={flow.setSalary}
          missingFacts={flow.clientMissingLaborFacts}
          loading={flow.loading}
          error={flow.error}
          laborRun={laborRun}
          onAdoptSuggestions={flow.adoptMaterialSuggestions}
          onRunWorkflow={() => void flow.runLaborWorkflow()}
        />
      )}
      {activeStage === 'analysis' && (
        <AnalysisDocumentStage
          matterId={flow.matterId ?? null}
          laborRun={laborRun}
          workflowStatus={flow.workflowStatus}
          runtimeAnalysis={flow.runtimeAnalysis}
          verifiedAuthorities={flow.verifiedAuthorities}
          authorityCatalog={flow.authorityCatalog}
          laborDraft={flow.laborDraft}
          laborResult={flow.laborResult}
          salary={flow.salary}
          onSalaryChange={flow.setSalary}
          years={flow.years}
          onYearsChange={flow.setYears}
          months={flow.months}
          onMonthsChange={flow.setMonths}
          loading={flow.loading}
          error={flow.error}
          result={flow.result}
          onCalculate={() => void flow.calculateLabor()}
          onRetryAuthorities={() => void flow.retryLaborAuthorities()}
          onApprove={() => void flow.approveLaborDraft()}
          onExport={(format) => void flow.exportLaborDraft(format)}
        />
      )}
    </div>
  );
}
