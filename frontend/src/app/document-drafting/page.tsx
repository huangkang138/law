'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, History, Sparkles, Crown, Shield, BookOpen, Plus, MessageSquare, Trash2, Pin, Edit, MoreHorizontal, FileText, Loader2, Settings } from 'lucide-react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ScaleIcon from '@/components/ScaleIcon';
import { useRouter } from 'next/navigation';
import { useDataCache } from '@/hooks/useDataCache';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface SearchSession {
  id: string;
  title: string;
  originalTitle: string;
  customTitle?: string;
  updatedAt: string;
  isPinned: boolean;
  messages: Message[];
  type: 'legal-document' | 'contract-drafting' | 'legal-opinion';
}

const QUICK_PROMPTS = [
  '民事起诉状',
  '离婚协议书',
  '劳动合同',
  '法律意见书',
];

export default function DocumentDraftingPage() {
  const router = useRouter();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [loadingText, setLoadingText] = useState('');
  const [mounted, setMounted] = useState(false);
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
  // 数据缓存
  const { getCachedData, setCachedData } = useDataCache<SearchSession[]>('document-drafting-sessions');

  useEffect(() => {
    setMounted(true);
    // 从缓存加载会话
    const cached = getCachedData();
    if (cached) {
      setSessions(cached);
    }
  }, []);
  
  // 保存会话到缓存
  useEffect(() => {
    if (sessions.length > 0) {
      setCachedData(sessions);
    }
  }, [sessions]);

  useEffect(() => {
    if (shouldScrollToBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      setShouldScrollToBottom(false);
    }
  }, [shouldScrollToBottom]);

  const handleSend = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    let sessionId = currentSessionId;
    if (!sessionId) {
      sessionId = Date.now().toString();
      const newSession: SearchSession = {
        id: sessionId,
        title: messageText.substring(0, 30),
        originalTitle: messageText,
        updatedAt: new Date().toISOString(),
        isPinned: false,
        messages: [],
        type: 'legal-document',
      };
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(sessionId);
    }

    const userMessage: Message = { role: 'user', content: messageText };
    setLocalMessages((prev) => [...prev, userMessage]);
    setSessions(prev => prev.map(s => 
      s.id === sessionId 
        ? { ...s, messages: [...s.messages, userMessage], updatedAt: new Date().toISOString() }
        : s
    ));
    setInput('');
    setLoading(true);
    setShouldScrollToBottom(true);

    try {
      setLoadingText('📄 正在分析需求...');

      // 模拟API调用，实际项目中需要替换为真实的后端API
      await new Promise(resolve => setTimeout(resolve, 1000));

      setLoadingText('✍️ 正在起草文书...');
      await new Promise(resolve => setTimeout(resolve, 2000));

      const responseContent = `# 文书起草结果

## 起草内容

根据您的需求，已为您起草了相关文书。

### 文书类型
通用法律文书

### 主要内容
- 当事人信息
- 事实描述
- 法律依据
- 具体诉求

### 注意事项
1. 请核对文书中的个人信息
2. 确认所有事实描述准确无误
3. 如需修改，请告知具体修改内容

## 下一步
您可以：
- 查看完整文书
- 下载文书文件
- 继续修改完善`;

      setCurrentRole('assistant');
      setCurrentMessage('');
      
      let accumulatedMessage = '';
      const chunkSize = 1;
      
      for (let i = 0; i < responseContent.length; i += chunkSize) {
        accumulatedMessage += responseContent.slice(i, i + chunkSize);
        setCurrentMessage(accumulatedMessage);
        await new Promise(resolve => setTimeout(resolve, 20));
      }
      
      const assistantMessage: Message = { role: 'assistant', content: responseContent };
      setLocalMessages((prev) => [...prev, assistantMessage]);
      setSessions(prev => prev.map(s => 
        s.id === sessionId 
          ? { ...s, messages: [...s.messages, assistantMessage] }
          : s
      ));
      setCurrentMessage('');
      setCurrentRole(null);
      setLoadingText('');
    } catch (error) {
      console.error('起草失败:', error);
      const errorMessage: Message = { 
        role: 'assistant', 
        content: '抱歉，网络错误，请检查连接后重试' 
      };
      setLocalMessages((prev) => [...prev, errorMessage]);
      setSessions(prev => prev.map(s => 
        s.id === sessionId 
          ? { ...s, messages: [...s.messages, errorMessage] }
          : s
      ));
    } finally {
      setLoading(false);
      setLoadingText('');
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    handleSend(prompt);
  };

  const handleNewChat = () => {
    if (localMessages.length > 0) {
      setCurrentSessionId('');
      setLocalMessages([]);
    }
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      handleNewChat();
    }
  };

  const handleEditSession = (e: React.MouseEvent, session: SearchSession) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitle(session.customTitle || session.title);
    setActiveMenuId(null);
  };

  const handleSaveEdit = () => {
    if (editingSessionId && editTitle.trim()) {
      setSessions(prev => prev.map(s => 
        s.id === editingSessionId 
          ? { ...s, title: editTitle.trim(), customTitle: editTitle.trim() }
          : s
      ));
      setEditingSessionId(null);
      setEditTitle('');
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditTitle('');
  };

  const handleTogglePin = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setSessions(prev => prev.map(s => 
      s.id === sessionId 
        ? { ...s, isPinned: !s.isPinned }
        : s
    ));
    setActiveMenuId(null);
  };

  const handleToggleMenu = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setActiveMenuId(activeMenuId === sessionId ? null : sessionId);
  };

  useEffect(() => {
    const handleClickOutside = () => {
      setActiveMenuId(null);
    };

    if (activeMenuId) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [activeMenuId]);

  const handleSwitchSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setLocalMessages(session.messages);
    }
  };

  const getSortedSessions = () => {
    return [...sessions].sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });
  };

  const [currentRole, setCurrentRole] = useState<'user' | 'assistant' | null>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed business-page-shell left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground flex">
      {/* 星空光晕效果 */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="relative z-10 w-64 h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-r border-sky-200 dark:border-sky-900/30 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 dark:border-sky-900/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800 dark:text-sky-300">历史起草</h2>
            <button
              onClick={handleNewChat}
              className="p-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white transition-colors"
              title="新建起草"
            >
              <Plus size={18} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {mounted && getSortedSessions().map((session) => (
            <div
              key={session.id}
              className="relative"
            >
              <div
                onClick={() => handleSwitchSession(session.id)}
                className={`group flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all ${
                  currentSessionId === session.id
                    ? 'bg-sky-100 dark:bg-sky-900/30 border border-sky-300 dark:border-sky-700'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent'
                }`}
              >
                <FileText size={16} className="text-gray-500 dark:text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                    {session.customTitle || session.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(session.updatedAt).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => handleToggleMenu(e, session.id)}
                    className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                    title="更多操作"
                  >
                    <MoreHorizontal size={14} />
                  </button>
                </div>
              </div>

              {activeMenuId === session.id && (
                <div className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 min-w-[120px]">
                  <button
                    onClick={(e) => handleTogglePin(e, session.id)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  >
                    <Pin size={14} className={session.isPinned ? 'text-sky-500 fill-current' : ''} />
                    {session.isPinned ? '取消置顶' : '置顶'}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditSession(e, session);
                    }}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  >
                    <Edit size={14} />
                    编辑
                  </button>
                  <button
                    onClick={(e) => handleDeleteSession(e, session.id)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-red-500"
                  >
                    <Trash2 size={14} />
                    删除
                  </button>
                </div>
              )}
            </div>
          ))}
          {mounted && sessions.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <p className="text-sm">暂无起草记录</p>
              <p className="text-xs mt-1">点击上方 + 开始新起草</p>
            </div>
          )}
        </div>

        {/* 设置按钮 */}
        <div className="p-3 border-t border-sky-200 dark:border-sky-900/30 flex-shrink-0">
          <Link
            href="/settings"
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Settings size={18} />
            <span className="text-sm font-medium">设置</span>
          </Link>
        </div>
      </div>

      <div className="relative z-10 flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <div className="flex-1 w-full overflow-y-auto overflow-x-hidden">
          <div className="w-full max-w-4xl mx-auto px-4 pt-8 pb-4">
            <div className="text-center mb-4 animate-fadeIn">
              <h1 className="text-2xl font-bold text-sky-700 dark:text-sky-300 mb-1">文件起草</h1>
              <p className="text-sm text-gray-700 dark:text-gray-300">智能文书起草，快速生成专业法律文件</p>
              <div className="h-1 w-24 bg-gradient-to-r from-sky-500 to-blue-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="mb-6 flex flex-wrap items-center justify-center gap-2 animate-fadeIn">
              <div className="flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Crown size={14} className="text-sky-600 dark:text-sky-400" />
                <span className="text-xs text-sky-800 dark:text-sky-300">AI智能起草</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Shield size={14} className="text-red-600 dark:text-red-400" />
                <span className="text-xs text-red-800 dark:text-red-300">专业模板</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Sparkles size={14} className="text-sky-600 dark:text-sky-400" />
                <span className="text-xs text-sky-800 dark:text-sky-300">快速生成</span>
              </div>
            </div>

            {localMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-6 animate-fadeIn">
                <div className="mb-4 relative">
                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-sky-600/30 via-amber-600/30 to-indigo-600/30 blur-2xl animate-pulse-slow" />
                  <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-sky-600 to-blue-600 shadow-2xl border-2 border-sky-400">
                    <FileText size={32} className="text-white" />
                  </div>
                </div>
                <h2 className="mb-2 text-xl font-bold text-sky-800 dark:text-sky-300">智能文件起草</h2>
                <p className="mb-4 text-center text-sm text-gray-700 dark:text-gray-300">
                  输入文书类型和要求，AI将为您自动起草专业法律文件
                </p>

                <div className="grid w-full max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
                  {QUICK_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => handleQuickPrompt(prompt)}
                      className="group relative overflow-hidden rounded-xl border border-sky-500/30 bg-white/60 dark:bg-gray-800/60 p-3 backdrop-blur-sm transition-all hover:scale-105 hover:border-sky-500/60 hover:shadow-lg hover:shadow-amber-500/20"
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-sky-600/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                      <div className="relative">
                        <div className="flex items-center gap-2">
                          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-sky-600 to-blue-600 shadow-lg border border-sky-400/50">
                            <FileText size={16} className="text-white" />
                          </div>
                          <span className="text-sm font-medium text-gray-800 dark:text-sky-300">{prompt}</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div ref={chatContainerRef} className="space-y-3">
                <div className="flex items-center justify-between rounded-xl border border-sky-500/30 bg-white/60 dark:bg-gray-800/60 p-3 backdrop-blur-sm">
                  <div className="flex items-center gap-2">
                    <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-sky-600 to-blue-600 shadow-lg border border-sky-400/50">
                      <FileText size={20} className="text-white" />
                    </div>
                    <h2 className="text-lg font-bold text-gray-800 dark:text-sky-300">文件起草</h2>
                  </div>
                  <button
                    onClick={() => router.push('/history')}
                    className="flex items-center gap-1 rounded-lg border border-sky-500/30 bg-white/40 dark:bg-gray-700/40 px-2 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 transition-all hover:bg-sky-500/20 hover:border-sky-500/60"
                  >
                    <History size={14} className="text-sky-600 dark:text-sky-400" />
                    历史记录
                  </button>
                </div>

                {localMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                  >
                    {message.role === 'assistant' && (
                      <div className="mr-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-600 to-blue-600 border border-sky-400/50">
                        <FileText size={16} className="text-white" />
                      </div>
                    )}

                    <div
                      className={`max-w-[80%] rounded-xl px-3 py-2 backdrop-blur-sm ${
                        message.role === 'user'
                          ? 'bg-sky-500/20 border border-sky-500/30 text-gray-800 dark:text-sky-300'
                          : 'bg-white/80 dark:bg-gray-800/80 border border-sky-500/30 text-gray-800 dark:text-gray-200'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      ) : (
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {currentMessage && (
                  <div className="flex justify-start animate-fadeIn">
                    <div className="mr-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-600 to-blue-600 border border-sky-400/50">
                      <FileText size={16} className="text-white" />
                    </div>
                    <div className="max-w-[80%] rounded-xl px-3 py-2 bg-white/80 dark:bg-gray-800/80 border border-sky-500/30 text-gray-800 dark:text-gray-200 backdrop-blur-sm">
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {currentMessage}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}

                {loadingText && (
                  <div className="flex justify-start animate-fadeIn">
                    <div className="mr-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-600 to-blue-600 border border-sky-400/50">
                      {loading ? <Loader2 size={16} className="text-white animate-spin" /> : <FileText size={16} className="text-white" />}
                    </div>
                    <div className="max-w-[80%] rounded-xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 px-3 py-2 text-gray-800 dark:text-gray-200 backdrop-blur-sm">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 animate-pulse rounded-full bg-sky-600"></div>
                        <div className="h-2 w-2 animate-pulse rounded-full bg-sky-600" style={{ animationDelay: '0.2s' }}></div>
                        <div className="h-2 w-2 animate-pulse rounded-full bg-sky-600" style={{ animationDelay: '0.4s' }}></div>
                        <span className="text-xs text-sky-700 dark:text-sky-400">{loadingText}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        <div className="flex-shrink-0 w-full border-t border-sky-500/30 backdrop-blur-md bg-white/95 dark:bg-gray-900/95">
          <div className="mx-auto w-full max-w-4xl px-4 py-3">
            <div className="flex items-end gap-2 rounded-xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 p-2 backdrop-blur-sm">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入文书类型和要求，AI将为您起草..."
                rows={1}
                className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-gray-800 dark:text-gray-200 outline-none placeholder:text-gray-500 dark:placeholder:text-gray-400"
                style={{ maxHeight: '200px' }}
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="rounded-lg bg-gradient-to-br from-sky-600 to-blue-600 p-2.5 text-white transition-all hover:shadow-lg hover:shadow-sky-500/30 disabled:opacity-50 disabled:cursor-not-allowed border border-sky-400/50"
              >
                {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-gray-500 dark:text-gray-400">
              内容由 AI 生成，仅供参考，不构成专业法律建议
            </p>
          </div>
        </div>
      </div>

      {editingSessionId && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div 
            className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">重命名会话</h3>
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSaveEdit();
                  } else if (e.key === 'Escape') {
                    handleCancelEdit();
                  }
                }}
                placeholder="输入新的会话名称"
                className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                autoFocus
              />
            </div>
            <div className="flex gap-3 px-6 pb-6">
              <button
                onClick={handleCancelEdit}
                className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={!editTitle.trim()}
                className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-br from-amber-600 to-orange-600 text-white hover:shadow-lg hover:shadow-amber-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-sky-400/50"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
