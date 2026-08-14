import { AlertCircle, CheckCircle2, Clock3 } from 'lucide-react';

import { ConversationPresentation } from '@/services/digitalHumanApi';

interface ConversationPresenterCardProps {
  presentation: ConversationPresentation | null;
  isLoading: boolean;
  error: string;
}

export default function ConversationPresenterCard({
  presentation,
  isLoading,
  error,
}: ConversationPresenterCardProps) {
  if (error) {
    return (
      <section className="dh-presenter-card dh-presenter-error">
        <AlertCircle size={16} />
        <div><strong>案件状态暂时无法读取</strong><p>{error}</p></div>
      </section>
    );
  }
  if (isLoading) {
    return (
      <section className="dh-presenter-card">
        <Clock3 size={16} />
        <div><strong>正在恢复案件状态</strong><p>请稍候，聊天记录不会中断。</p></div>
      </section>
    );
  }
  if (!presentation) {
    return (
      <section className="dh-presenter-card">
        <Clock3 size={16} />
        <div><strong>还没有当前案件</strong><p>先在对话中说明目标，或在左侧新建案件。</p></div>
      </section>
    );
  }
  const completed = presentation.state_key === 'completed';
  return (
    <section className={`dh-presenter-card ${completed ? 'dh-presenter-completed' : ''}`}>
      {completed ? <CheckCircle2 size={16} /> : <Clock3 size={16} />}
      <div>
        <strong>{presentation.headline}</strong>
        <p>{presentation.summary}</p>
        {presentation.next_action.type !== 'none' && (
          <span>{presentation.next_action.label}</span>
        )}
      </div>
    </section>
  );
}
