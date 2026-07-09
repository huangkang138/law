'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, History, Sparkles, Crown, Shield, BookOpen, Plus, MessageSquare, Trash2, Pin, Edit, MoreHorizontal, Settings, Star } from 'lucide-react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChatMessage, getLegalChatSessionDetails, createFavorite } from '@/lib/api';
import { useChatStore } from '@/store/chatStore';
import html2canvas from 'html2canvas';
import ScaleIcon from '@/components/ScaleIcon';
import DownloadDropdown from '@/components/DownloadDropdown';
import { exportAsImage, exportAsPDF, exportAsWord } from '@/lib/exportUtils';
import { useRouter, useSearchParams } from 'next/navigation';
import { AlertDialog, showAlert } from '@/components/AlertDialog';

const QUICK_PROMPTS = [
  '解析劳动合同风险',
  '计算法定解除赔偿金',
  '试用期权益保护',
  '竞业限制条款审查',
];

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [currentRole, setCurrentRole] = useState<'user' | 'assistant' | null>(null);
  const [loadingText, setLoadingText] = useState('');
  const [mounted, setMounted] = useState(false);
  const [scrollY, setScrollY] = useState(0);
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [favoritedMessages, setFavoritedMessages] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const { currentSessionId, sessions, addMessage, createSession, setCurrentSession, deleteSession, renameSession, togglePin, getSortedSessions } = useChatStore();

  useEffect(() => {
    setMounted(true);
    
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 处理从历史记录跳转过来的sessionId参数
  useEffect(() => {
    const sessionId = searchParams.get('sessionId');
    if (sessionId) {
      loadChatSessionDetails(sessionId);
    } else {
      // 直接访问页面时，重置为无会话状态
      setCurrentSession('');
      setLocalMessages([]);
    }
  }, [searchParams, setCurrentSession]);

  const loadChatSessionDetails = async (sessionId: string) => {
    try {
      const details = await getLegalChatSessionDetails(sessionId);
      if (details.messages && details.messages.length > 0) {
        // 检查本地是否已有该会话
        const existingSession = sessions.find(s => s.id === sessionId);
        if (!existingSession) {
          // 如果本地没有，创建一个新会话
          const newSessionId = createSession(details.title || '历史会话');
          // 添加消息到新会话
          details.messages.forEach((msg: any) => {
            addMessage(newSessionId, msg.role, msg.content);
          });
          setCurrentSession(newSessionId);
        } else {
          // 如果本地已有，直接设置为当前会话
          setCurrentSession(sessionId);
        }
      }
    } catch (error) {
      console.error('加载历史会话失败:', error);
    }
  };

  // 修复"僵尸对话"Bug：检查当前会话是否还存在
  useEffect(() => {
    if (currentSessionId) {
      const currentSession = sessions.find(s => s.id === currentSessionId);
      if (!currentSession) {
        // 会话已被删除，重置为空状态
        setLocalMessages([]);
        setCurrentSession('');
      } else {
        // 加载会话消息
        setLocalMessages(currentSession.messages.map(m => ({
          role: m.role,
          content: m.content
        })));
      }
    } else {
      // 没有当前会话，显示空状态
      setLocalMessages([]);
    }
  }, [currentSessionId, sessions, setCurrentSession]);

  // 自动滚动到底部 - 只在用户发送消息时滚动，AI回答时不滚动
  useEffect(() => {
    if (shouldScrollToBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      setShouldScrollToBottom(false);
    }
  }, [shouldScrollToBottom]);

  const handleSend = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    // 如果没有当前会话，创建一个
    let sessionId = currentSessionId;
    if (!sessionId) {
      sessionId = createSession(messageText.slice(0, 30));
    }

    const userMessage: Message = { role: 'user', content: messageText };
    setLocalMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setShouldScrollToBottom(true); // 用户发送消息时滚动到底部

    // 保存到 store
    addMessage(sessionId, 'user', messageText);

    try {
      // 显示加载提示
      setLoadingText('🔍 正在分析您的问题...');
      setCurrentRole('assistant');
      setCurrentMessage('');

      const response = await sendChatMessage({
        question: messageText,
        session_id: sessionId,
      });

      // 逐字显示AI回答
      setLoadingText('✍️ 正在生成专业回答...');
      const displayMessage = async (content: string) => {
        setCurrentRole('assistant');
        setCurrentMessage('');
        
        let accumulatedMessage = '';
        const chunkSize = 1; // 每次显示1个字符
        
        for (let i = 0; i < content.length; i += chunkSize) {
          accumulatedMessage += content.slice(i, i + chunkSize);
          setCurrentMessage(accumulatedMessage);
          await new Promise(resolve => setTimeout(resolve, 20)); // 20ms 延迟
        }
        
        // 显示完成后添加到消息列表
        setLocalMessages((prev) => [...prev, { role: 'assistant', content }]);
        setCurrentMessage('');
        setCurrentRole(null);
        setLoadingText('');
      };

      await displayMessage(response.answer);
      
      // 保存到 store
      addMessage(sessionId, 'assistant', response.answer);
    } catch (error: any) {
      let errorMsg = error.message || '处理您的问题时出现错误';
      
      // 特殊处理速率限制错误
      if (errorMsg.includes('Rate limit') || errorMsg.includes('rate_limit_exceeded')) {
        errorMsg = '⚠️ API 速率限制：今日配额已用完\n\n请等待约 10 分钟后重试，或前往设置页面更换 API Key。\n\n提示：Groq 免费版每天有 100,000 tokens 限制。';
      } else if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
        errorMsg = '⚠️ 网络连接失败\n\n请检查：\n1. 后端服务是否已启动（http://localhost:8001）\n2. 网络连接是否正常';
      }
      
      const errorMessage: Message = { 
        role: 'assistant', 
        content: `抱歉，${errorMsg}` 
      };
      setLocalMessages((prev) => [...prev, errorMessage]);
      
      // 保存到 store
      addMessage(sessionId, 'assistant', `抱歉，${errorMsg}`);
    } finally {
      setLoading(false);
      setLoadingText('');
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    handleSend(prompt);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDownloadImage = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (!lastMessage) return;

    try {
      await exportAsImage(lastMessage.content, { title: '普法问答' });
    } catch (error) {
      console.error('导出图片失败:', error);
      showAlert('导出图片失败，请重试', 'error');
    }
  };

  const handleDownloadPDF = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (!lastMessage) return;

    try {
      await exportAsPDF(lastMessage.content, { title: '普法问答' });
    } catch (error) {
      console.error('导出PDF失败:', error);
      showAlert('导出PDF失败，请重试', 'error');
    }
  };

  const handleDownloadWord = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (!lastMessage) return;

    try {
      await exportAsWord(lastMessage.content, { title: '普法问答' });
    } catch (error) {
      console.error('导出Word失败:', error);
      showAlert('导出Word失败，请重试', 'error');
    }
  };

  const handleFavorite = async (content: string, index: number) => {
    try {
      if (favoritedMessages.has(index)) {
        // 取消收藏逻辑
        // 这里需要调用删除收藏的API，但是我们需要知道收藏的ID
        // 由于我们没有存储收藏ID，这里暂时只更新UI状态
        setFavoritedMessages(prev => {
          const newSet = new Set(prev);
          newSet.delete(index);
          return newSet;
        });
        await showAlert('取消收藏成功', 'success');
      } else {
        // 添加收藏
        const title = `普法问答收藏 ${new Date().toLocaleString('zh-CN')}`;
        await createFavorite({
          title,
          content,
          source_type: 'legal',
          source_id: currentSessionId || undefined
        });
        setFavoritedMessages(prev => new Set(prev).add(index));
        await showAlert('收藏成功', 'success');
      }
    } catch (error: any) {
      await showAlert('操作失败: ' + error.message, 'error');
    }
  };

  // 新建对话 - 只在当前有聊天记录时才创建新会话
  const handleNewChat = () => {
    // 如果当前会话有消息记录，才创建新会话
    if (localMessages.length > 0) {
      const newSessionId = createSession('新对话');
      setCurrentSession(newSessionId);
      setLocalMessages([]);
    }
    // 如果当前没有消息，不做任何操作（保持当前空状态）
  };

  // 切换会话
  const handleSwitchSession = (sessionId: string) => {
    setCurrentSession(sessionId);
  };

  // 删除会话
  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    deleteSession(sessionId);
    if (currentSessionId === sessionId) {
      setLocalMessages([]);
    }
  };

  // 置顶/取消置顶
  const handleTogglePin = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    togglePin(sessionId);
    setActiveMenuId(null);
  };

  // 开始编辑 - 打开弹窗
  const handleStartEdit = (sessionId: string, currentTitle: string) => {
    setEditingSessionId(sessionId);
    setEditTitle(currentTitle);
    setActiveMenuId(null);
  };

  // 保存编辑
  const handleSaveEdit = () => {
    if (editingSessionId && editTitle.trim()) {
      renameSession(editingSessionId, editTitle.trim());
      setEditingSessionId(null);
      setEditTitle('');
    }
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditTitle('');
  };

  // 切换菜单显示
  const handleToggleMenu = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setActiveMenuId(activeMenuId === sessionId ? null : sessionId);
  };

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = () => {
      setActiveMenuId(null);
    };

    if (activeMenuId) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [activeMenuId]);

  return (
    <div className="fixed top-20 left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground flex">
      {/* 星空光晕效果 */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      {/* 左侧边栏 - 聊天记录 - 固定不动 */}
      <div className="relative z-10 w-64 h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-r border-sky-200 dark:border-sky-900/30 flex flex-col flex-shrink-0 overflow-hidden">
        {/* 边栏标题 */}
        <div className="p-4 border-b border-sky-200 dark:border-sky-900/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800 dark:text-sky-300">聊天记录</h2>
            <button
              onClick={handleNewChat}
              className="p-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white transition-colors"
              title="新建对话"
            >
              <Plus size={18} />
            </button>
          </div>
        </div>

        {/* 会话列表 - 可滚动 */}
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
                <MessageSquare size={16} className="text-gray-500 dark:text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                    {session.customTitle || session.originalTitle}
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

              {/* 下拉菜单 */}
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
                      handleStartEdit(session.id, session.customTitle || session.originalTitle);
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
              <p className="text-sm">暂无聊天记录</p>
              <p className="text-xs mt-1">点击上方 + 开始新对话</p>
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

      {/* 主聊天区域 - 固定布局 */}
      <div className="relative z-10 flex-1 flex flex-col h-full overflow-hidden min-w-0">
        {/* 主聊天内容 - 唯一可滚动区域 */}
        <div className="flex-1 w-full overflow-y-auto overflow-x-hidden">
          <div className="w-full max-w-4xl mx-auto px-4 pt-8 pb-4">
            {/* 页面标题 */}
            <div className="text-center mb-4 animate-fadeIn">
              <h1 className="text-2xl font-bold text-sky-700 dark:text-sky-300 mb-1">普法问答</h1>
              <p className="text-sm text-gray-700 dark:text-gray-300">智能法律咨询，专业解答您的法律问题</p>
              <div className="h-1 w-24 bg-gradient-to-r from-amber-500 to-orange-500 mx-auto rounded-full mt-2" />
            </div>

            {/* 核心价值观标签 */}
            <div className="mb-6 flex flex-wrap items-center justify-center gap-2 animate-fadeIn" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Crown size={14} className="text-sky-600 dark:text-sky-400" />
                <span className="text-xs text-sky-800 dark:text-sky-300">公平正义</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Shield size={14} className="text-red-600 dark:text-red-400" />
                <span className="text-xs text-red-800 dark:text-red-300">服务民生</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Sparkles size={14} className="text-sky-600 dark:text-sky-400" />
                <span className="text-xs text-sky-800 dark:text-sky-300">智能高效</span>
              </div>
            </div>

            {localMessages.length === 0 ? (
              // Empty State - 优雅的初始状态
              <div className="flex flex-col items-center justify-center py-6 animate-fadeIn">
                <div className="mb-4 relative">
                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-sky-600/30 via-amber-600/30 to-red-600/30 blur-2xl animate-pulse-slow" />
                  <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 shadow-2xl border-2 border-sky-400">
                    <ScaleIcon size={32} className="text-white" withFire={true} />
                  </div>
                </div>
                <h2 className="mb-2 text-xl font-bold text-sky-800 dark:text-sky-300">洞察法理，捍卫权益</h2>
                <p className="mb-4 text-center text-sm text-gray-700 dark:text-gray-300">
                  选择下方快捷指令，或直接输入您的问题
                </p>

                {/* Quick Prompts */}
                <div className="grid w-full max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
                  {QUICK_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => handleQuickPrompt(prompt)}
                      className="group relative overflow-hidden rounded-xl border border-sky-500/30 bg-white/60 dark:bg-gray-800/60 p-3 backdrop-blur-sm transition-all hover:scale-105 hover:border-sky-500/60 hover:shadow-lg hover:shadow-amber-500/20"
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-amber-600/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                      <div className="relative">
                        <div className="flex items-center gap-2">
                          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-amber-600 to-orange-600 shadow-lg border border-sky-400/50">
                            <BookOpen size={16} className="text-white" />
                          </div>
                          <span className="text-sm font-medium text-gray-800 dark:text-sky-300">{prompt}</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              // Messages - 对话气泡流
              <div ref={chatContainerRef} className="space-y-3">
                {/* Header with History Button */}
                <div className="flex items-center justify-between rounded-xl border border-sky-500/30 bg-white/60 dark:bg-gray-800/60 p-3 backdrop-blur-sm">
                  <div className="flex items-center gap-2">
                    <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 shadow-lg border border-sky-400/50">
                      <ScaleIcon size={20} className="text-white" />
                    </div>
                    <h2 className="text-lg font-bold text-gray-800 dark:text-sky-300">普法问答</h2>
                  </div>
                  <div className="flex items-center gap-1">
                    <DownloadDropdown
                      onDownloadImage={handleDownloadImage}
                      onDownloadPDF={handleDownloadPDF}
                      onDownloadWord={handleDownloadWord}
                      theme="amber"
                      buttonText="导出"
                      buttonClassName="flex items-center gap-1 rounded-lg border border-sky-500/30 bg-white/40 dark:bg-gray-700/40 px-2 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 transition-all hover:bg-sky-500/20 hover:border-sky-500/60 no-print"
                    />
                    <button
                      onClick={() => router.push('/history')}
                      className="flex items-center gap-1 rounded-lg border border-sky-500/30 bg-white/40 dark:bg-gray-700/40 px-2 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 transition-all hover:bg-sky-500/20 hover:border-sky-500/60"
                    >
                      <History size={14} className="text-sky-600 dark:text-sky-400" />
                      历史记录
                    </button>
                  </div>
                </div>

                {localMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                  >
                    {/* AI Avatar */}
                    {message.role === 'assistant' && (
                      <div className="mr-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 border border-sky-400/50">
                        <ScaleIcon size={16} className="text-white" />
                      </div>
                    )}

                    {/* Message Bubble */}
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

                    {/* Favorite Button for AI Messages */}
                    {message.role === 'assistant' && (
                      <button
                        onClick={() => handleFavorite(message.content, index)}
                        className={`ml-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-colors ${
                          favoritedMessages.has(index)
                            ? 'bg-sky-500/20 hover:bg-sky-500/30'
                            : 'bg-sky-100 dark:bg-sky-900/30 hover:bg-sky-200 dark:hover:bg-sky-800/50'
                        }`}
                        title={favoritedMessages.has(index) ? "取消收藏" : "收藏"}
                      >
                        <Star 
                          size={16} 
                          className={`transition-colors ${
                            favoritedMessages.has(index)
                              ? 'text-sky-500 dark:text-sky-400 fill-sky-500 dark:fill-sky-400'
                              : 'text-sky-600 dark:text-sky-400'
                          }`} 
                        />
                      </button>
                    )}

                    {/* User Avatar (optional) */}
                    {message.role === 'user' && (
                      <div className="ml-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-700 to-red-800 border border-sky-400/50">
                        <span className="text-xs font-medium text-white">你</span>
                      </div>
                    )}
                  </div>
                ))}

                {/* 当前正在显示的消息 */}
                {currentMessage && currentRole && (
                  <div className={`flex ${currentRole === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                    {/* AI Avatar */}
                    {currentRole === 'assistant' && (
                      <div className="mr-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 border border-sky-400/50">
                        <ScaleIcon size={16} className="text-white" />
                      </div>
                    )}

                    {/* Message Bubble */}
                    <div className="max-w-[80%] rounded-xl px-3 py-2 bg-white/80 dark:bg-gray-800/80 border border-sky-500/30 text-gray-800 dark:text-gray-200 backdrop-blur-sm">
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {currentMessage}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}

                {/* Loading State */}
                {loadingText && (
                  <div className="flex justify-start animate-fadeIn">
                    <div className="mr-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 border border-sky-400/50">
                      <ScaleIcon size={16} className="text-white" />
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

        {/* Input Area - 固定在底部，不随滚动 */}
        <div className="flex-shrink-0 w-full border-t border-sky-500/30 backdrop-blur-md bg-white/95 dark:bg-gray-900/95">
          <div className="mx-auto w-full max-w-4xl px-4 py-3">
            <div className="flex items-end gap-2 rounded-xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 p-2 backdrop-blur-sm">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入您的法律问题..."
                rows={1}
                className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-gray-800 dark:text-gray-200 outline-none placeholder:text-gray-500 dark:placeholder:text-gray-400"
                style={{ maxHeight: '200px' }}
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="rounded-lg bg-gradient-to-br from-amber-600 to-orange-600 p-2.5 text-white transition-all hover:shadow-lg hover:shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed border border-sky-400/50"
              >
                <Send size={18} />
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-gray-500 dark:text-gray-400">
              内容由 AI 生成，仅供参考，不构成专业法律建议
            </p>
          </div>
        </div>
      </div>

      {/* 编辑弹窗 */}
      {editingSessionId && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div 
            className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">重命名对话</h3>
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
                placeholder="输入新的对话名称"
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
