'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, History, Sparkles, Crown, Shield, BookOpen, Plus, MessageSquare, Trash2, Pin, Edit, MoreHorizontal, FileText, Loader2, Upload, Image, File, Mic, ChevronRight, Copy, CheckCircle, Clock, Settings } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ScaleIcon from '@/components/ScaleIcon';
import DownloadDropdown from '@/components/DownloadDropdown';
import { exportAsImage, exportAsPDF, exportAsWord } from '@/lib/exportUtils';
import { useRouter } from 'next/navigation';
import { useDataCache } from '@/hooks/useDataCache';
import { showAlert } from '@/components/AlertDialog';

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
  type: 'legal-opinion';
  documentId?: number;
}

const API_BASE = 'http://localhost:8001';

const COURTS = [
  '最高人民法院',
  '北京市高级人民法院',
  '上海市高级人民法院',
  '广东省高级人民法院',
  '江苏省高级人民法院',
  '浙江省高级人民法院',
];

const RECOMMENDED_CASES = [
  { name: '民间借贷', description: '借款纠纷、利息计算、担保责任等常见问题', icon: Crown },
  { name: '交通事故', description: '责任认定、赔偿标准、保险理赔等法律分析', icon: Shield },
  { name: '劳动争议', description: '劳动合同、工资福利、工伤赔偿等纠纷处理', icon: Sparkles },
  { name: '房产纠纷', description: '房屋买卖、租赁、产权确认等法律问题', icon: BookOpen },
];

export default function LegalOpinionPage() {
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
  const [currentStep, setCurrentStep] = useState(1);
  const [caseSummary, setCaseSummary] = useState('');
  const [analysisFocus, setAnalysisFocus] = useState('');
  const [selectedCourt, setSelectedCourt] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [caseOrganized, setCaseOrganized] = useState('');
  const [currentRole, setCurrentRole] = useState<'user' | 'assistant' | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
  // 数据缓存
  const { getCachedData, setCachedData, clearCache } = useDataCache<SearchSession[]>('legal-opinion-sessions');

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
      const response = await fetch(`${API_BASE}/api/document/list?type=legal-opinion`);
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
          type: 'legal-opinion',
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

  const handleNextStep = async () => {
    if (currentStep === 4) return;
    
    if (currentStep === 1 && !caseSummary.trim()) {
      showAlert('请输入案情概要', 'warning');
      return;
    }
    
    if (currentStep === 2) {
      setCaseOrganized('系统已自动梳理案情，包括：当事人信息、时间线、争议焦点、证据清单等关键要素。');
    }
    
    if (currentStep === 3 && !analysisFocus.trim()) {
      showAlert('请输入分析重点', 'warning');
      return;
    }
    
    setCurrentStep(currentStep + 1);
    
    if (currentStep === 3) {
      await handleGenerateOpinion();
    }
  };

  const handlePreviousStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleGenerateOpinion = async () => {
    setLoading(true);
    setLoadingText('🔍 正在分析案情...');

    try {
      const combinedInput = `案情概要：${caseSummary}\n分析重点：${analysisFocus}\n承办法院：${selectedCourt}`;
      
      const userMessage: Message = { 
        role: 'user', 
        content: combinedInput 
      };
      setLocalMessages((prev) => [...prev, userMessage]);
      setShouldScrollToBottom(true);

      setLoadingText('📝 正在生成法律意见...');
      
      const response = await fetch(`${API_BASE}/api/document/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: combinedInput,
          type: 'legal-opinion',
          title: caseSummary.substring(0, 30),
          details: {
            case_summary: caseSummary,
            analysis_focus: analysisFocus,
            selected_court: selectedCourt
          }
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
            type: 'legal-opinion',
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
      console.error('生成法律意见失败:', error);
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

  const handleNewChat = () => {
    if (localMessages.length > 0) {
      setCurrentSessionId('');
      setLocalMessages([]);
      setCurrentStep(1);
      setCaseSummary('');
      setAnalysisFocus('');
      setSelectedCourt('');
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
      setCurrentStep(4);
    }
  };

  const handleQuickCase = (caseType: string) => {
    setCaseSummary(`请帮我分析一起${caseType}案件，具体情况如下：[请在此处描述您的具体案情]`);
  };

  const getSortedSessions = () => {
    return [...sessions].sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });
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
        await exportAsImage(lastMessage.content, { title: '法律意见' });
      } catch (error) {
        console.error('导出图片失败:', error);
      }
    }
  };

  const handleDownloadPDF = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      try {
        await exportAsPDF(lastMessage.content, { title: '法律意见' });
      } catch (error) {
        console.error('导出PDF失败:', error);
      }
    }
  };

  const handleDownloadWord = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      try {
        await exportAsWord(lastMessage.content, { title: '法律意见' });
      } catch (error) {
        console.error('导出Word失败:', error);
      }
    }
  };

  return (
    <div className="fixed top-20 left-0 right-0 bottom-0 bg-gradient-to-br from-slate-50 via-violet-50 to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 text-foreground flex overflow-hidden">
      <div
        className="absolute inset-0 opacity-5 pointer-events-none"
        style={{
          background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
        }}
      />

      <div className="relative z-10 w-64 h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-r border-violet-200 dark:border-violet-900/30 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-violet-200 dark:border-violet-900/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800 dark:text-violet-300">分析记录</h2>
            <button
              onClick={handleNewChat}
              className="p-2 rounded-lg bg-violet-500 hover:bg-violet-600 text-white transition-colors"
              title="新建分析"
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
                    ? 'bg-violet-100 dark:bg-violet-900/30 border border-violet-300 dark:border-violet-700'
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
                    <Pin size={14} className={session.isPinned ? 'text-violet-500 fill-current' : ''} />
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
              <p className="text-sm">暂无分析记录</p>
              <p className="text-xs mt-1">点击上方 + 开始新分析</p>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-violet-200 dark:border-violet-900/30">
          <button
            onClick={() => router.push('/settings')}
            className="w-full flex items-center justify-center gap-2 p-3 rounded-lg bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/30 text-violet-700 dark:text-violet-300 transition-colors"
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
                    <div className="w-4 h-4 rounded-full bg-violet-500 animate-pulse" />
                    <div className="w-4 h-4 rounded-full bg-sky-500 animate-pulse" style={{ animationDelay: '0.2s' }} />
                    <div className="w-4 h-4 rounded-full bg-orange-500 animate-pulse" style={{ animationDelay: '0.4s' }} />
                  </div>
                  <h1 className="text-5xl font-bold bg-gradient-to-r from-violet-700 via-amber-600 to-blue-600 bg-clip-text text-transparent mb-4">
                    专业法律意见，深度分析
                  </h1>
                  <div className="inline-flex items-center gap-3 bg-gradient-to-r from-violet-100 to-blue-100 dark:from-violet-900/30 dark:to-blue-900/30 rounded-full px-6 py-3 text-sm font-semibold text-violet-700 dark:text-violet-200 shadow-xl shadow-violet-500/10">
                    <Sparkles size={20} className="text-violet-500" />
                    智能分析，精准判断
                  </div>
                </div>

                <div className="flex items-center justify-center gap-3 mb-10 overflow-x-auto pb-3">
                  <div className="flex items-center gap-1.5 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-2 backdrop-blur-sm">
                    <Crown size={16} className="text-violet-600 dark:text-violet-400" />
                    <span className="text-xs text-violet-800 dark:text-violet-300 font-semibold">AI智能</span>
                  </div>
                  <div className="flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-4 py-2 backdrop-blur-sm">
                    <Shield size={16} className="text-sky-600 dark:text-sky-400" />
                    <span className="text-xs text-sky-800 dark:text-sky-300 font-semibold">专业分析</span>
                  </div>
                  <div className="flex items-center gap-1.5 rounded-full border border-orange-500/30 bg-orange-500/10 px-4 py-2 backdrop-blur-sm">
                    <BookOpen size={16} className="text-orange-600 dark:text-orange-400" />
                    <span className="text-xs text-orange-800 dark:text-orange-300 font-semibold">深度洞察</span>
                  </div>
                </div>

                {/* 流程图 */}
                <div className="w-full max-w-5xl mb-6">
                  <div className="relative">
                    {/* 流程连接线 */}
                    <div className="absolute left-0 right-0 top-1/2 transform -translate-y-1/2 h-1 bg-violet-200 dark:bg-violet-900/30 z-0"></div>
                    <div className={`absolute left-0 top-1/2 transform -translate-y-1/2 h-1 bg-gradient-to-r from-violet-500 via-amber-500 to-blue-600 z-10 transition-all duration-800 ease-in-out`} style={{ width: `${((currentStep - 1) / 3) * 100}%` }}></div>
                    
                    {/* 流程节点 */}
                    <div className="flex items-center justify-between relative z-20">
                      {[1, 2, 3, 4].map((step) => {
                        const isActive = step <= currentStep;
                        return (
                          <div key={step} className="flex flex-col items-center gap-3">
                            <div className={`relative flex h-11 w-11 items-center justify-center rounded-full shadow-xl transition-all duration-300 ${isActive ? 'bg-gradient-to-br from-violet-600 via-amber-600 to-blue-600 border-3 border-violet-400 text-white shadow-violet-500/30 scale-105' : 'bg-white/80 dark:bg-slate-800/80 border-3 border-violet-500/30 text-slate-500 dark:text-slate-400'}`}>
                              {isActive && (
                                <div className="absolute inset-0 rounded-full bg-violet-500/20 animate-ping"></div>
                              )}
                              <span className="relative z-10 font-bold text-lg">{step}</span>
                            </div>
                            <div className={`text-center transition-all duration-300 ${isActive ? 'text-violet-700 dark:text-violet-400 font-semibold' : 'text-slate-600 dark:text-slate-400'}`}>
                              <p className="text-xs">{step === 1 ? '输入案情' : step === 2 ? '案情梳理' : step === 3 ? '分析争议' : '法律意见'}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <div className="w-full max-w-4xl">
                  <div className="rounded-3xl border border-violet-200/50 dark:border-violet-800/50 bg-white/90 dark:bg-slate-800/90 p-8 backdrop-blur-2xl shadow-2xl hover:shadow-violet-500/20 transition-all duration-500">
                    {currentStep === 1 && (
                      <div>
                        <div className="flex items-center gap-4 mb-6">
                          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center shadow-xl shadow-violet-500/30">
                            <MessageSquare size={28} className="text-white" />
                          </div>
                          <div>
                            <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200">案情概要</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400">请详细描述您的案情内容</p>
                          </div>
                        </div>
                        <p className="text-base text-slate-600 dark:text-slate-400 mb-6">
                          请输入具体的案情内容，包括参与各方主体、案发时间、地点、具体事项、纠纷金额、各方争议焦点等，您说明的越具体，分析就越精准～
                        </p>
                        <div className="relative mb-6">
                          <textarea
                            value={caseSummary}
                            onChange={(e) => setCaseSummary(e.target.value)}
                            placeholder="请输入案情概要..."
                            rows={6}
                            className="w-full resize-none rounded-2xl border-2 border-violet-200/50 dark:border-violet-800/50 bg-white/70 dark:bg-slate-700/70 px-6 py-5 text-base text-slate-800 dark:text-slate-200 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-all focus:border-violet-500 focus:ring-4 focus:ring-violet-500/20"
                            style={{ maxHeight: '400px' }}
                          />
                          <div className="absolute bottom-5 right-5 text-xs text-slate-400 dark:text-slate-500 bg-white/90 dark:bg-slate-800/90 px-3 py-1.5 rounded-lg">
                            {caseSummary.length}/5000
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 mt-4">
                          <button className="flex items-center gap-3 rounded-xl border-2 border-violet-200/50 dark:border-violet-800/50 bg-white/60 dark:bg-slate-700/60 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-violet-500/10 hover:border-violet-500/50 hover:shadow-lg">
                            <Image size={20} className="text-violet-600 dark:text-violet-400" />
                            上传图片
                          </button>
                          <button className="flex items-center gap-3 rounded-xl border-2 border-violet-200/50 dark:border-violet-800/50 bg-white/60 dark:bg-slate-700/60 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-violet-500/10 hover:border-violet-500/50 hover:shadow-lg">
                            <File size={20} className="text-violet-600 dark:text-violet-400" />
                            上传文档
                          </button>
                          <button className="flex items-center gap-3 rounded-xl border-2 border-violet-200/50 dark:border-violet-800/50 bg-white/60 dark:bg-slate-700/60 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-violet-500/10 hover:border-violet-500/50 hover:shadow-lg">
                            <Mic size={20} className="text-violet-600 dark:text-violet-400" />
                            语音输入
                          </button>
                        </div>
                      </div>
                    )}

                    {currentStep === 2 && (
                      <div>
                        <div className="flex items-center gap-4 mb-6">
                          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center shadow-xl shadow-violet-500/30">
                            <BookOpen size={28} className="text-white" />
                          </div>
                          <div>
                            <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200">案情梳理</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400">系统正在梳理您的案情</p>
                          </div>
                        </div>
                        <div className="space-y-4">
                          <div className="flex items-center gap-4 p-5 bg-gradient-to-r from-violet-50 to-white dark:from-violet-900/20 dark:to-slate-800/80 rounded-2xl border border-violet-300/50 shadow-lg hover:shadow-xl transition-all">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-blue-600 text-white text-base font-bold shadow-lg">1</div>
                            <div className="flex-1">
                              <p className="text-base font-semibold text-slate-800 dark:text-slate-200">当事人信息</p>
                              <p className="text-sm text-slate-600 dark:text-slate-400">原告、被告、第三人等基本信息</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4 p-5 bg-gradient-to-r from-violet-50 to-white dark:from-violet-900/20 dark:to-slate-800/80 rounded-2xl border border-violet-300/50 shadow-lg hover:shadow-xl transition-all">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-blue-600 text-white text-base font-bold shadow-lg">2</div>
                            <div className="flex-1">
                              <p className="text-base font-semibold text-slate-800 dark:text-slate-200">时间线梳理</p>
                              <p className="text-sm text-slate-600 dark:text-slate-400">关键时间节点和事件顺序</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4 p-5 bg-gradient-to-r from-violet-50 to-white dark:from-violet-900/20 dark:to-slate-800/80 rounded-2xl border border-violet-300/50 shadow-lg hover:shadow-xl transition-all">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-blue-600 text-white text-base font-bold shadow-lg">3</div>
                            <div className="flex-1">
                              <p className="text-base font-semibold text-slate-800 dark:text-slate-200">争议焦点</p>
                              <p className="text-sm text-slate-600 dark:text-slate-400">核心争议问题和法律关系</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4 p-5 bg-gradient-to-r from-violet-50 to-white dark:from-violet-900/20 dark:to-slate-800/80 rounded-2xl border border-violet-300/50 shadow-lg hover:shadow-xl transition-all">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-blue-600 text-white text-base font-bold shadow-lg">4</div>
                            <div className="flex-1">
                              <p className="text-base font-semibold text-slate-800 dark:text-slate-200">证据清单</p>
                              <p className="text-sm text-slate-600 dark:text-slate-400">相关证据材料和证明力分析</p>
                            </div>
                          </div>
                        </div>
                        {caseOrganized && (
                          <div className="mt-6 p-5 bg-gradient-to-r from-green-50 to-white dark:from-green-900/20 dark:to-slate-800/80 rounded-2xl border border-green-400/30 shadow-lg">
                            <div className="flex items-center gap-3 mb-3">
                              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-500 text-white text-base font-bold">✓</div>
                              <p className="text-base font-semibold text-green-700 dark:text-green-400">案情梳理完成</p>
                            </div>
                            <p className="text-base text-green-700 dark:text-green-400">{caseOrganized}</p>
                          </div>
                        )}
                      </div>
                    )}

                    {currentStep === 3 && (
                      <div>
                        <div className="flex items-center gap-4 mb-6">
                          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center shadow-xl shadow-violet-500/30">
                            <Sparkles size={28} className="text-white" />
                          </div>
                          <div>
                            <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200">分析重点</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400">请输入您最关注的核心问题</p>
                          </div>
                        </div>
                        <p className="text-base text-slate-600 dark:text-slate-400 mb-6">
                          请输入您最关注的核心问题，我们会针对核心问题进行解答
                        </p>
                        <div className="relative mb-6">
                          <textarea
                            value={analysisFocus}
                            onChange={(e) => setAnalysisFocus(e.target.value)}
                            placeholder="请输入分析重点..."
                            rows={3}
                            className="w-full resize-none rounded-2xl border-2 border-violet-200/50 dark:border-violet-800/50 bg-white/70 dark:bg-slate-700/70 px-6 py-5 text-base text-slate-800 dark:text-slate-200 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-all focus:border-violet-500 focus:ring-4 focus:ring-violet-500/20"
                            style={{ maxHeight: '200px' }}
                          />
                          <div className="absolute bottom-5 right-5 text-xs text-slate-400 dark:text-slate-500 bg-white/90 dark:bg-slate-800/90 px-3 py-1.5 rounded-lg">
                            {analysisFocus.length}/2000
                          </div>
                        </div>
                        
                        <div className="mb-6">
                          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 mb-3">承办法院/法官</h3>
                          <select
                            value={selectedCourt}
                            onChange={(e) => setSelectedCourt(e.target.value)}
                            className="w-full rounded-2xl border-2 border-violet-200/50 dark:border-violet-800/50 bg-white/70 dark:bg-slate-700/70 px-5 py-3 text-sm text-slate-800 dark:text-slate-200 outline-none transition-all focus:border-violet-500 focus:ring-4 focus:ring-violet-500/20"
                          >
                            <option value="">请选择法院</option>
                            {COURTS.map((court) => (
                              <option key={court} value={court}>{court}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    )}

                    {currentStep === 4 && (
                      <div>
                        <div className="flex items-center gap-4 mb-6">
                          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center shadow-xl shadow-violet-500/30">
                            <ScaleIcon size={28} className="text-white" />
                          </div>
                          <div>
                            <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200">生成法律意见</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400">点击下方按钮开始生成</p>
                          </div>
                        </div>
                        {loadingText && (
                          <div className="flex items-center gap-4 p-5 bg-violet-50 dark:bg-violet-900/20 rounded-2xl border border-violet-300/50 shadow-lg">
                            <div className="h-3 w-3 animate-pulse rounded-full bg-violet-600"></div>
                            <div className="h-3 w-3 animate-pulse rounded-full bg-violet-600" style={{ animationDelay: '0.2s' }}></div>
                            <div className="h-3 w-3 animate-pulse rounded-full bg-violet-600" style={{ animationDelay: '0.4s' }}></div>
                            <span className="text-base text-violet-700 dark:text-violet-400 font-semibold">{loadingText}</span>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between mt-10">
                      <button
                        onClick={handlePreviousStep}
                        disabled={currentStep === 1}
                        className="flex items-center gap-3 rounded-xl border-2 border-violet-200/50 dark:border-violet-800/50 bg-white/70 dark:bg-slate-800/70 px-8 py-4 text-base font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-violet-500/10 hover:border-violet-500/50 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ChevronRight size={20} className="transform rotate-180" />
                        上一步
                      </button>
                      <button
                        onClick={handleNextStep}
                        disabled={loading || (currentStep === 1 && !caseSummary.trim()) || (currentStep === 3 && !analysisFocus.trim())}
                        className="rounded-xl bg-gradient-to-r from-violet-600 via-amber-600 to-blue-600 px-8 py-3 text-white font-bold transition-all hover:shadow-2xl hover:shadow-violet-500/40 disabled:opacity-50 disabled:cursor-not-allowed border-2 border-white/30 flex items-center gap-3 hover:scale-[1.02] active:scale-[0.98]"
                      >
                        {loading ? <Loader2 size={20} className="animate-spin" /> : (currentStep === 4 ? '生成意见' : '下一步')}
                        {currentStep !== 4 && <ChevronRight size={18} />}
                      </button>
                    </div>
                  </div>
                  
                  <div className="mt-6">
                    <div className="flex items-center gap-3 mb-4">
                      <Crown size={20} className="text-violet-500" />
                      <h4 className="text-lg font-bold text-slate-800 dark:text-slate-200">常见案件类型</h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                      {RECOMMENDED_CASES.map((caseItem) => {
                        const Icon = caseItem.icon;
                        return (
                          <button
                            key={caseItem.name}
                            onClick={() => handleQuickCase(caseItem.name)}
                            className="group relative overflow-hidden rounded-xl border-2 border-violet-200/50 dark:border-violet-800/50 bg-white/80 dark:bg-slate-800/80 p-4 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:border-violet-500/50 hover:shadow-xl"
                          >
                            <div className="absolute inset-0 bg-gradient-to-br from-violet-500/15 via-amber-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                            <div className="relative">
                              <div className="flex items-center gap-3 mb-2">
                                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center shadow-lg">
                                  <Icon size={20} className="text-white" />
                                </div>
                                <span className="font-bold text-slate-800 dark:text-violet-200 text-sm">{caseItem.name}</span>
                              </div>
                              <p className="text-xs text-slate-600 dark:text-slate-400">{caseItem.description}</p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div ref={chatContainerRef} className="space-y-6">
                <div className="flex items-center justify-between rounded-3xl border border-violet-200/50 dark:border-violet-800/50 bg-white/90 dark:bg-slate-800/90 p-5 backdrop-blur-2xl shadow-xl mb-6">
                  <div className="flex items-center gap-4">
                    <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 shadow-2xl border-2 border-white/30">
                      <ScaleIcon size={22} className="text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-slate-800 dark:text-violet-200">法律意见</h2>
                      <p className="text-sm text-slate-500 dark:text-slate-400">AI智能专业分析</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-3 rounded-xl border border-violet-200/50 dark:border-violet-800/50 bg-white/70 dark:bg-slate-700/70 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-violet-500/10 hover:border-violet-500/50 hover:shadow-lg"
                    >
                      {copied ? <CheckCircle size={18} className="text-green-500" /> : <Copy size={18} />}
                      {copied ? '已复制' : '复制'}
                    </button>
                    <DownloadDropdown
                      onDownloadImage={handleDownloadImage}
                      onDownloadPDF={handleDownloadPDF}
                      onDownloadWord={handleDownloadWord}
                      theme="violet"
                    />
                    <button
                      onClick={() => router.push('/history')}
                      className="flex items-center gap-3 rounded-xl border border-violet-200/50 dark:border-violet-800/50 bg-white/70 dark:bg-slate-700/70 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-violet-500/10 hover:border-violet-500/50 hover:shadow-lg"
                    >
                      <History size={18} className="text-violet-600 dark:text-violet-400" />
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
                      <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 border-2 border-white/30 shadow-xl">
                        <ScaleIcon size={24} className="text-white" />
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] rounded-3xl px-7 py-6 backdrop-blur-2xl shadow-xl ${
                        message.role === 'user'
                          ? 'bg-gradient-to-br from-violet-500/25 to-blue-500/25 border border-violet-400/40 text-slate-800 dark:text-violet-200'
                          : 'bg-white/95 dark:bg-slate-800/95 border border-violet-200/50 dark:border-violet-800/50 text-slate-800 dark:text-slate-200'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <p className="text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      ) : (
                        <div className="prose prose-lg dark:prose-invert max-w-none prose-headings:text-violet-700 dark:prose-headings:text-violet-400 prose-strong:text-slate-800 dark:prose-strong:text-slate-200">
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
                    <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 border-2 border-white/30 shadow-xl">
                      <ScaleIcon size={24} className="text-white" />
                    </div>
                    <div className="max-w-[85%] rounded-3xl px-7 py-6 bg-white/95 dark:bg-slate-800/95 border border-violet-200/50 dark:border-violet-800/50 backdrop-blur-2xl shadow-xl">
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
                    <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 border-2 border-white/30 shadow-xl">
                      {loading ? <Loader2 size={24} className="text-white animate-spin" /> : <ScaleIcon size={24} className="text-white" />}
                    </div>
                    <div className="max-w-[85%] rounded-3xl border border-violet-200/50 dark:border-violet-800/50 bg-white/90 dark:bg-slate-800/90 px-7 py-6 backdrop-blur-2xl shadow-xl">
                      <div className="flex items-center gap-3">
                        <div className="h-3 w-3 animate-pulse rounded-full bg-violet-600"></div>
                        <div className="h-3 w-3 animate-pulse rounded-full bg-violet-600" style={{ animationDelay: '0.2s' }}></div>
                        <div className="h-3 w-3 animate-pulse rounded-full bg-violet-600" style={{ animationDelay: '0.4s' }}></div>
                        <span className="text-sm text-violet-700 dark:text-violet-300 font-semibold">{loadingText}</span>
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
                className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-br from-violet-600 to-orange-600 text-white hover:shadow-lg hover:shadow-violet-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-violet-400/50"
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
