'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ConversationMessageContentProps {
  content: string;
  role: 'user' | 'assistant';
  streaming?: boolean;
  compact?: boolean;
}

/**
 * 数字人消息正文的唯一渲染入口：主聊天与工作台侧边共用。
 * 仅 assistant 消息渲染 Markdown（react-markdown + remark-gfm），
 * 用户消息保持纯文本；不启用 rehypeRaw，不使用 dangerouslySetInnerHTML。
 */
export default function ConversationMessageContent({
  content,
  role,
  streaming = false,
  compact = false,
}: ConversationMessageContentProps) {
  const className = [
    'dh-msg-content',
    compact ? 'dh-msg-content-compact' : '',
    streaming ? 'dh-msg-content-streaming' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={className}>
      {role === 'assistant' ? (
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      ) : (
        <p>{content}</p>
      )}
      <style jsx>{`
        .dh-msg-content {
          font-size: 14px;
          line-height: 1.65;
          color: inherit;
          word-break: break-word;
        }

        .dh-msg-content :global(p) {
          margin: 0 0 6px;
          white-space: pre-wrap;
        }

        .dh-msg-content :global(p:last-child) {
          margin-bottom: 0;
        }

        .dh-msg-content :global(ul),
        .dh-msg-content :global(ol) {
          margin: 4px 0 8px;
          padding-left: 18px;
        }

        .dh-msg-content :global(li) {
          margin: 2px 0;
          white-space: pre-wrap;
        }

        .dh-msg-content :global(li > p) {
          margin: 0;
        }

        .dh-msg-content :global(strong) {
          font-weight: 700;
        }

        .dh-msg-content :global(code) {
          padding: 1px 4px;
          background: rgba(96, 165, 250, .14);
          border-radius: 4px;
          font-size: .92em;
        }

        .dh-msg-content-compact {
          font-size: 11px;
          line-height: 1.55;
          color: #304e6d;
          overflow-wrap: anywhere;
        }

        .dh-msg-content-compact :global(p) {
          margin: 0 0 4px;
        }

        .dh-msg-content-compact :global(ul),
        .dh-msg-content-compact :global(ol) {
          margin: 3px 0 5px;
          padding-left: 15px;
        }

        .dh-msg-content-compact :global(li) {
          margin: 1px 0;
        }

        .dh-msg-content-streaming::after {
          content: '';
          display: inline-block;
          width: 2px;
          height: 1em;
          margin-left: 2px;
          vertical-align: -2px;
          background: #60a5fa;
          animation: dh-msg-caret .9s ease-in-out infinite;
        }

        @keyframes dh-msg-caret {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
