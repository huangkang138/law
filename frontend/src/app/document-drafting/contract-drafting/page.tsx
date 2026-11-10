'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, History, Sparkles, Crown, Shield, Plus, MessageSquare, Trash2, Pin, Edit, MoreHorizontal, FileText, Loader2, Upload, Copy, CheckCircle, FileCheck, Clock, HeartHandshake, FileLock, Settings } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ScaleIcon from '@/components/ScaleIcon';
import DownloadDropdown from '@/components/DownloadDropdown';
import { exportAsImage, exportAsPDF, exportAsWord } from '@/lib/exportUtils';
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
  type: 'contract-drafting';
  documentId?: number;
}

const API_BASE = '';

const RECOMMENDED_COMMANDS = [
  { name: '劳动合同', description: '标准劳动合同模板，包含基本条款和双方权利义务', icon: 'HeartHandshake' },
  { name: '租赁合同', description: '房屋租赁合同，明确租金、期限和维修责任', icon: 'FileLock' },
  { name: '买卖合同', description: '商品买卖合同，规范交易流程和付款方式', icon: 'FileCheck' },
  { name: '服务合同', description: '服务提供合同，明确服务内容和质量标准', icon: 'Sparkles' },
  { name: '借款合同', description: '民间借贷合同，规范借款金额、利息和还款方式', icon: 'Crown' },
  { name: '保密协议', description: '商业保密协议，保护商业机密和知识产权', icon: 'Shield' },
];

const CONTRACT_CATEGORIES = [
  '全部',
  '劳动合同',
  '房屋租赁',
  '买卖合同',
  '服务协议',
  '借款担保',
  '知识产权',
  '其他合同',
];

export default function ContractDraftingPage() {
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
  const [currentRole, setCurrentRole] = useState<'user' | 'assistant' | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
  // 数据缓存
  const { getCachedData, setCachedData, clearCache } = useDataCache<SearchSession[]>('contract-drafting-sessions');

  useEffect(() => {
    setMounted(true);
    // 检查缓存
    const cached = getCachedData();
    if (cached) {
      setSessions(cached);
    } else {
      loadSessions();
    }
  }, []);

  useEffect(() => {
    if (shouldScrollToBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      setShouldScrollToBottom(false);
    }
  }, [shouldScrollToBottom]);

  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/document/list?type=contract-drafting`);
      const data = await response.json();
      if (data.success) {
        const mappedSessions: SearchSession[] = data.data.drafts.map((draft: any) => ({
          id: draft.id.toString(),
          title: draft.custom_title || draft.title,
          originalTitle: draft.title,
          customTitle: draft.custom_title,
          updatedAt: draft.updated_at,
          isPinned: draft.is_pinned,
          messages: [
            { role: 'user' as const, content: draft.content },
            { role: 'assistant' as const, content: draft.result || '' }
          ].filter(m => m.content),
          type: 'contract-drafting',
          documentId: draft.id
        }));
        setSessions(mappedSessions);
        // 缓存数据
        setCachedData(mappedSessions);
      }
    } catch (error) {
      console.error('加载会话失败:', error);
    }
  };

  const handleSend = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    setLoading(true);
    setLoadingText('📄 正在分析合同需求...');
    
    try {
      let sessionId = currentSessionId;
      if (!sessionId) {
        sessionId = Date.now().toString();
      }

      const userMessage: Message = { role: 'user', content: messageText };
      setLocalMessages((prev) => [...prev, userMessage]);
      setInput('');
      setShouldScrollToBottom(true);

      setLoadingText('✍️ 正在起草合同...');
      
      const response = await fetch(`${API_BASE}/api/document/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: messageText,
          type: 'contract-drafting',
          title: messageText.substring(0, 30),
          details: {}
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setLoadingText('');
        
        let accumulatedMessage = '';
        const chunkSize = 3;
        
        setCurrentRole('assistant');
        setCurrentMessage('');
        
        for (let i = 0; i < data.data.content.length; i += chunkSize) {
          accumulatedMessage += data.data.content.slice(i, i + chunkSize);
          setCurrentMessage(accumulatedMessage);
          await new Promise(resolve => setTimeout(resolve, 15));
        }
        
        const assistantMessage: Message = { role: 'assistant', content: data.data.content };
        setLocalMessages((prev) => [...prev, assistantMessage]);
        setCurrentMessage('');
        setCurrentRole(null);

        if (!currentSessionId) {
          const newSession: SearchSession = {
            id: data.data.document_id.toString(),
            title: data.data.title,
            originalTitle: data.data.title,
            updatedAt: data.data.created_at,
            isPinned: false,
            messages: [userMessage, assistantMessage],
            type: 'contract-drafting',
            documentId: data.data.document_id
          };
          setSessions(prev => [newSession, ...prev]);
          setCurrentSessionId(newSession.id);
        } else {
          await loadSessions();
        }
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('起草失败:', error);
      const errorMessage: Message = { 
        role: 'assistant', 
        content: '抱歉，网络错误，请检查连接后重试' 
      };
      setLocalMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setLoadingText('');
    }
  };

  const handleQuickCommand = (command: string) => {
    handleSend(command);
  };

  const handleNewChat = () => {
    if (localMessages.length > 0) {
      setCurrentSessionId('');
      setLocalMessages([]);
      setInput('');
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    
    try {
      const session = sessions.find(s => s.id === sessionId);
      if (session?.documentId) {
        await fetch(`${API_BASE}/api/document/${session.documentId}`, { method: 'DELETE' });
      }
      
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        handleNewChat();
      }
    } catch (error) {
      console.error('删除会话失败:', error);
    }
  };

  const handleEditSession = async (e: React.MouseEvent, session: SearchSession) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitle(session.customTitle || session.title);
    setActiveMenuId(null);
  };

  const handleSaveEdit = async () => {
    if (editingSessionId && editTitle.trim()) {
      const session = sessions.find(s => s.id === editingSessionId);
      if (session?.documentId) {
        try {
          await fetch(`${API_BASE}/api/document/${session.documentId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ custom_title: editTitle.trim() })
          });
          
          setSessions(prev => prev.map(s => 
            s.id === editingSessionId 
              ? { ...s, title: editTitle.trim(), customTitle: editTitle.trim() }
              : s
          ));
        } catch (error) {
          console.error('编辑会话失败:', error);
        }
      }
      setEditingSessionId(null);
      setEditTitle('');
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditTitle('');
  };

  const handleTogglePin = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    
    try {
      const session = sessions.find(s => s.id === sessionId);
      if (session?.documentId) {
        await fetch(`${API_BASE}/api/document/${session.documentId}/toggle-pin`, { method: 'POST' });
      }
      
      setSessions(prev => prev.map(s => 
        s.id === sessionId 
          ? { ...s, isPinned: !s.isPinned }
          : s
      ));
    } catch (error) {
      console.error('切换置顶失败:', error);
    }
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      await navigator.clipboard.writeText(lastMessage.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadImage = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      try {
        await exportAsImage(lastMessage.content, { title: '合同' });
      } catch (error) {
        console.error('导出图片失败:', error);
      }
    }
  };

  const handleDownloadPDF = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      try {
        await exportAsPDF(lastMessage.content, { title: '合同' });
      } catch (error) {
        console.error('导出PDF失败:', error);
      }
    }
  };

  const handleDownloadWord = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      try {
        await exportAsWord(lastMessage.content, { title: '合同' });
      } catch (error) {
        console.error('导出Word失败:', error);
      }
    }
  };

  return (
    <div className="fixed business-page-shell left-0 right-0 bottom-0 bg-gradient-to-br from-slate-50 via-rose-50 to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 text-foreground flex overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center opacity-5 pointer-events-none"
        style={{
          backgroundImage: `url('https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=合同签署 专业背景 金色装饰 高清摄影&image_size=landscape_16_9')`,
        }}
      />

      <div className="relative z-10 w-64 h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-r border-rose-200 dark:border-rose-900/30 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-rose-200 dark:border-rose-900/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800 dark:text-rose-300">起草记录</h2>
            <button
              onClick={handleNewChat}
              className="p-2 rounded-lg bg-rose-500 hover:bg-rose-600 text-white transition-colors"
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
                    ? 'bg-rose-100 dark:bg-rose-900/30 border border-rose-300 dark:border-rose-700'
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
                    <Pin size={14} className={session.isPinned ? 'text-rose-500 fill-current' : ''} />
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
        
        <div className="p-4 border-t border-rose-200 dark:border-rose-900/30">
          <button
            onClick={() => router.push('/settings')}
            className="w-full flex items-center justify-center gap-2 p-3 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-700 dark:text-rose-300 transition-colors"
          >
            <Settings size={16} />
            <span className="text-sm font-medium">设置</span>
          </button>
        </div>
      </div>

      <div className="relative z-10 flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <div className="flex-1 w-full overflow-y-auto overflow-x-hidden">
          <div className="w-full max-w-6xl mx-auto px-8 pt-10 pb-8">
            {localMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-6 animate-fadeIn">
                <div className="text-center mb-10">
                  <div className="inline-flex items-center gap-3 mb-6">
                    <div className="w-4 h-4 rounded-full bg-rose-500 animate-pulse" />
                    <div className="w-4 h-4 rounded-full bg-sky-500 animate-pulse" style={{ animationDelay: '0.2s' }} />
                    <div className="w-4 h-4 rounded-full bg-orange-500 animate-pulse" style={{ animationDelay: '0.4s' }} />
                  </div>
                  <h1 className="text-5xl font-bold bg-gradient-to-r from-rose-700 via-amber-600 to-blue-600 bg-clip-text text-transparent mb-4">
                    专业合同，快速生成
                  </h1>
                  <div className="inline-flex items-center gap-3 bg-gradient-to-r from-rose-100 to-blue-100 dark:from-rose-900/30 dark:to-blue-900/30 rounded-full px-6 py-3 text-sm font-semibold text-rose-700 dark:text-rose-200 shadow-xl shadow-rose-500/10">
                    <Sparkles size={20} className="text-rose-500" />
                    1分钟上手合同起草
                  </div>
                </div>

                <div className="flex items-center justify-center gap-3 mb-10 overflow-x-auto pb-3">
                  <div className="flex items-center gap-1.5 rounded-full border border-rose-500/30 bg-rose-500/10 px-4 py-2 backdrop-blur-sm">
                    <Crown size={16} className="text-rose-600 dark:text-rose-400" />
                    <span className="text-xs text-rose-800 dark:text-rose-300 font-semibold">AI智能</span>
                  </div>
                  <div className="flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-4 py-2 backdrop-blur-sm">
                    <Shield size={16} className="text-sky-600 dark:text-sky-400" />
                    <span className="text-xs text-sky-800 dark:text-sky-300 font-semibold">专业模板</span>
                  </div>
                  <div className="flex items-center gap-1.5 rounded-full border border-orange-500/30 bg-orange-500/10 px-4 py-2 backdrop-blur-sm">
                    <Sparkles size={16} className="text-orange-600 dark:text-orange-400" />
                    <span className="text-xs text-orange-800 dark:text-orange-300 font-semibold">快速生成</span>
                  </div>
                </div>

                <div className="w-full max-w-5xl">
                  <div className="rounded-3xl border border-rose-200/50 dark:border-rose-800/50 bg-white/90 dark:bg-slate-800/90 p-6 backdrop-blur-2xl shadow-2xl hover:shadow-rose-500/20 transition-all duration-500">
                    <div className="mb-6">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-rose-500 to-blue-600 flex items-center justify-center shadow-xl shadow-rose-500/30">
                          <MessageSquare size={24} className="text-white" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200">AI智能起草合同</h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400">描述您的需求，AI为您生成专业合同</p>
                        </div>
                      </div>
                      <div className="relative">
                        <textarea
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={handleKeyDown}
                          placeholder="请输入合同背景与目的，例如：我需要一份房屋租赁合同，甲方是业主，乙方是租客，租期一年，月租金5000元..."
                          rows={6}
                          className="w-full resize-none rounded-2xl border-2 border-rose-200/50 dark:border-rose-800/50 bg-white/70 dark:bg-slate-700/70 px-6 py-5 text-base text-slate-800 dark:text-slate-200 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-all focus:border-rose-500 focus:ring-4 focus:ring-rose-500/20"
                          style={{ maxHeight: '400px' }}
                        />
                        <div className="absolute bottom-5 right-5 text-xs text-slate-400 dark:text-slate-500 bg-white/90 dark:bg-slate-800/90 px-3 py-1.5 rounded-lg">
                          {input.length}/5000
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <button className="flex items-center gap-3 rounded-xl border-2 border-rose-200/50 dark:border-rose-800/50 bg-white/60 dark:bg-slate-700/60 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-rose-500/10 hover:border-rose-500/50 hover:shadow-xl">
                          <Upload size={20} className="text-rose-600 dark:text-rose-400" />
                          相关材料
                        </button>
                      </div>
                      <button
                        onClick={() => handleSend()}
                        disabled={input.trim().length === 0 || loading}
                        className="rounded-xl bg-gradient-to-r from-rose-600 via-amber-600 to-blue-600 px-8 py-3 text-white font-bold transition-all hover:shadow-2xl hover:shadow-rose-500/40 disabled:opacity-50 disabled:cursor-not-allowed border-2 border-white/30 flex items-center gap-3 hover:scale-[1.02] active:scale-[0.98]"
                      >
                        {loading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                        开始起草
                      </button>
                    </div>
                    
                    <div className="mt-6">
                      <div className="flex items-center gap-3 mb-4">
                        <Crown size={20} className="text-rose-500" />
                        <h4 className="text-lg font-bold text-slate-800 dark:text-slate-200">推荐模板</h4>
                      </div>
                      <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
                        {CONTRACT_CATEGORIES.map((category) => (
                          <button
                            key={category}
                            className="px-4 py-1.5 rounded-full border border-rose-200/50 dark:border-rose-800/50 text-slate-700 dark:text-slate-400 text-xs font-medium whitespace-nowrap hover:bg-rose-500/10 hover:border-rose-500/50 transition-all"
                          >
                            {category}
                          </button>
                        ))}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {RECOMMENDED_COMMANDS.map((command) => {
                          // 图标映射
                          const iconMap: Record<string, React.ReactNode> = {
                            'HeartHandshake': <HeartHandshake size={20} className="text-white" />,
                            'FileLock': <FileLock size={20} className="text-white" />,
                            'FileCheck': <FileCheck size={20} className="text-white" />,
                            'Sparkles': <Sparkles size={20} className="text-white" />,
                            'Crown': <Crown size={20} className="text-white" />,
                            'Shield': <Shield size={20} className="text-white" />
                          };
                          
                          const icon = iconMap[command.icon as keyof typeof iconMap] || <Sparkles size={20} className="text-white" />;
                          
                          return (
                            <button
                              key={command.name}
                              onClick={() => handleQuickCommand(command.name)}
                              className="group relative overflow-hidden rounded-2xl border-2 border-rose-200/50 dark:border-rose-800/50 bg-white/80 dark:bg-slate-800/80 p-4 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:border-rose-500/50 hover:shadow-2xl hover:shadow-rose-500/20"
                            >
                              <div className="absolute inset-0 bg-gradient-to-br from-rose-500/15 via-amber-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                              <div className="relative">
                                <div className="flex items-center gap-3 mb-3">
                                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-blue-600 flex items-center justify-center shadow-xl">
                                    {icon}
                                  </div>
                                  <span className="font-bold text-sm text-slate-800 dark:text-rose-200">{command.name}</span>
                                </div>
                                <p className="text-xs text-slate-600 dark:text-slate-400">{command.description}</p>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div ref={chatContainerRef} className="space-y-6">
                <div className="flex items-center justify-between rounded-3xl border border-rose-200/50 dark:border-rose-800/50 bg-white/90 dark:bg-slate-800/90 p-6 backdrop-blur-2xl shadow-xl mb-8">
                  <div className="flex items-center gap-5">
                    <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500 to-blue-600 shadow-2xl border-2 border-white/30">
                      <ScaleIcon size={28} className="text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-slate-800 dark:text-rose-200">合同起草</h2>
                      <p className="text-sm text-slate-500 dark:text-slate-400">AI智能生成专业合同</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-3 rounded-xl border border-rose-200/50 dark:border-rose-800/50 bg-white/70 dark:bg-slate-700/70 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-rose-500/10 hover:border-rose-500/50 hover:shadow-lg"
                    >
                      {copied ? <CheckCircle size={18} className="text-green-500" /> : <Copy size={18} />}
                      {copied ? '已复制' : '复制'}
                    </button>
                    <DownloadDropdown
                      onDownloadImage={handleDownloadImage}
                      onDownloadPDF={handleDownloadPDF}
                      onDownloadWord={handleDownloadWord}
                      theme="rose"
                    />
                    <button
                      onClick={() => router.push('/history')}
                      className="flex items-center gap-3 rounded-xl border border-rose-200/50 dark:border-rose-800/50 bg-white/70 dark:bg-slate-700/70 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-rose-500/10 hover:border-rose-500/50 hover:shadow-lg"
                    >
                      <History size={18} className="text-rose-600 dark:text-rose-400" />
                      历史记录
                    </button>
                  </div>
                </div>

                {localMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                  >
                    {message.role === 'assistant' && (
                      <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500 to-blue-600 border-2 border-white/30 shadow-xl">
                        <ScaleIcon size={24} className="text-white" />
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] rounded-3xl px-7 py-6 backdrop-blur-2xl shadow-xl ${
                        message.role === 'user'
                          ? 'bg-gradient-to-br from-rose-500/25 to-blue-500/25 border border-rose-400/40 text-slate-800 dark:text-rose-200'
                          : 'bg-white/95 dark:bg-slate-800/95 border border-rose-200/50 dark:border-rose-800/50 text-slate-800 dark:text-slate-200'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <p className="text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      ) : (
                        <div className="prose prose-lg dark:prose-invert max-w-none prose-headings:text-rose-700 dark:prose-headings:text-rose-400 prose-strong:text-slate-800 dark:prose-strong:text-slate-200">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>

                    {message.role === 'user' && (
                      <div className="ml-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-slate-500 to-slate-600 border-2 border-white/30 shadow-xl">
                        <MessageSquare size={24} className="text-white" />
                      </div>
                    )}
                  </div>
                ))}

                {currentMessage && (
                  <div className="flex justify-start animate-fadeIn">
                    <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500 to-blue-600 border-2 border-white/30 shadow-xl">
                      <ScaleIcon size={24} className="text-white" />
                    </div>
                    <div className="max-w-[85%] rounded-3xl px-7 py-6 bg-white/95 dark:bg-slate-800/95 border border-rose-200/50 dark:border-rose-800/50 backdrop-blur-2xl shadow-xl">
                      <div className="prose prose-lg dark:prose-invert max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {currentMessage}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}

                {loadingText && (
                  <div className="flex justify-start animate-fadeIn">
                    <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500 to-blue-600 border-2 border-white/30 shadow-xl">
                      {loading ? <Loader2 size={24} className="text-white animate-spin" /> : <ScaleIcon size={24} className="text-white" />}
                    </div>
                    <div className="max-w-[85%] rounded-3xl border border-rose-200/50 dark:border-rose-800/50 bg-white/90 dark:bg-slate-800/90 px-7 py-6 backdrop-blur-2xl shadow-xl">
                      <div className="flex items-center gap-3">
                        <div className="h-3 w-3 animate-pulse rounded-full bg-rose-600"></div>
                        <div className="h-3 w-3 animate-pulse rounded-full bg-rose-600" style={{ animationDelay: '0.2s' }}></div>
                        <div className="h-3 w-3 animate-pulse rounded-full bg-rose-600" style={{ animationDelay: '0.4s' }}></div>
                        <span className="text-sm text-rose-700 dark:text-rose-300 font-semibold">{loadingText}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
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
                className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-br from-rose-600 to-orange-600 text-white hover:shadow-lg hover:shadow-rose-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-rose-400/50"
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