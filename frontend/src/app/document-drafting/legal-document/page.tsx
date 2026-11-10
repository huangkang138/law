'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, History, Sparkles, Crown, Shield, BookOpen, Plus, MessageSquare, Trash2, Pin, FileText, Loader2, Upload, File, Copy, CheckCircle, ArrowRight, Zap, FileCheck, Clock, Settings } from 'lucide-react';
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
  type: 'legal-document';
  documentId?: number;
}

const API_BASE = '';

const DOCUMENT_TEMPLATES = [
  { id: 'free', name: '自由起草', desc: '灵活起草各类法律文书', icon: Sparkles },
  { id: 'civil-complaint', name: '民事起诉状', desc: '高效生成民事起诉状', icon: FileText },
  { id: 'civil-answer', name: '民事答辩状(一审)', desc: '针对性回应原告诉讼请求', icon: Shield },
  { id: 'civil-agent', name: '民事代理词(一审)', desc: '全面梳理代理意见', icon: Crown },
  { id: 'civil-counterclaim', name: '民事反诉状', desc: '精准构建反诉文书', icon: Zap },
  { id: 'administrative-complaint', name: '行政起诉状', desc: '高效生成行政起诉状', icon: BookOpen },
];

const DOCUMENT_CATEGORIES = ['全部', '一审文书', '二审文书', '再审文书', '执行文书', '客户向文书', '保全文书', '合同/协议'];

export default function LegalDocumentPage() {
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
  const [activeTab, setActiveTab] = useState('ai');
  const [selectedTemplate, setSelectedTemplate] = useState('侵害商业秘密纠纷起诉状');
  const [caseSummary, setCaseSummary] = useState('');
  const [currentRole, setCurrentRole] = useState<'user' | 'assistant' | null>(null);
  const [copied, setCopied] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [converting, setConverting] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // 数据缓存
  const { getCachedData, setCachedData, clearCache } = useDataCache<SearchSession[]>('legal-document-sessions');

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
      console.log('开始加载会话...');
      const response = await fetch(`${API_BASE}/api/document/list?type=legal-document`);
      console.log('响应状态:', response.status);
      console.log('响应状态文本:', response.statusText);
      
      const responseText = await response.text();
      console.log('响应文本:', responseText);
      
      const data = JSON.parse(responseText);
      console.log('解析后的数据:', data);
      
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
          type: 'legal-document',
          documentId: draft.id
        }));
        setSessions(mappedSessions);
        // 缓存数据
        setCachedData(mappedSessions);
        console.log('会话加载成功:', mappedSessions);
      } else {
        console.error('API返回失败:', data.error);
      }
    } catch (error) {
      console.error('加载会话失败:', error);
      if (error instanceof SyntaxError) {
        console.error('JSON解析错误:', error.message);
      }
    }
  };

  const handleSend = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    setLoading(true);
    setLoadingText('📄 正在分析文书需求...');
    
    try {
      let sessionId = currentSessionId;
      if (!sessionId) {
        sessionId = Date.now().toString();
      }

      const userMessage: Message = { role: 'user', content: messageText };
      setLocalMessages((prev) => [...prev, userMessage]);
      setInput('');
      setShouldScrollToBottom(true);

      setLoadingText('✍️ 正在起草文书...');
      
      const response = await fetch(`${API_BASE}/api/document/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: messageText,
          type: 'legal-document',
          title: messageText.substring(0, 30),
          details: {
            template_type: selectedTemplate,
            case_summary: caseSummary
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
            type: 'legal-document',
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

  const handleNewChat = () => {
    setCurrentSessionId('');
    setLocalMessages([]);
    setInput('');
    setSelectedTemplate('');
    setCaseSummary('');
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
    const newTitle = prompt('编辑会话名称:', session.title);
    if (newTitle && session.documentId) {
      try {
        await fetch(`${API_BASE}/api/document/${session.documentId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ custom_title: newTitle })
        });
        
        setSessions(prev => prev.map(s => 
          s.id === session.id 
            ? { ...s, title: newTitle, customTitle: newTitle }
            : s
        ));
      } catch (error) {
        console.error('编辑会话失败:', error);
      }
    }
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
  };

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

  const handleConvert = async () => {
    if (!selectedFile) return;

    setConverting(true);

    try {
      // 模拟文件上传和转换过程
      await new Promise(resolve => setTimeout(resolve, 2000));

      // 根据选择的模板生成转换结果
      let conversionResult = '';
      
      switch (selectedTemplate) {
        case '侵害商业秘密纠纷起诉状':
          conversionResult = `# ${selectedTemplate}

## 当事人信息
- 原告：[公司名称/个人姓名]
- 法定代表人：[姓名]
- 住所：[地址]
- 被告：[公司名称/个人姓名]
- 法定代表人：[姓名]
- 住所：[地址]

## 诉讼请求
1. 判令被告立即停止侵犯原告商业秘密的行为
2. 判令被告赔偿原告经济损失及合理维权费用共计人民币[具体金额]元
3. 判令被告在[相关媒体]上公开道歉，消除影响
4. 判令被告承担本案全部诉讼费用

## 事实与理由
- **商业秘密内容**：[技术信息/经营信息具体内容]
- **保密措施**：[原告采取的保密措施]
- **侵权行为**：[被告具体侵权行为]
- **损害后果**：[原告遭受的损失情况]
- **法律依据**：《中华人民共和国反不正当竞争法》第九条

## 证据清单
1. [证据名称]：[证明内容]
2. [证据名称]：[证明内容]
3. [证据名称]：[证明内容]
4. [证据名称]：[证明内容]`;
          break;
        case '侵害植物新品种权纠纷起诉状':
          conversionResult = `# ${selectedTemplate}

## 当事人信息
- 原告：[品种权人名称]
- 法定代表人：[姓名]
- 住所：[地址]
- 被告：[侵权方名称]
- 法定代表人：[姓名]
- 住所：[地址]

## 诉讼请求
1. 判令被告立即停止侵犯原告植物新品种权的行为
2. 判令被告赔偿原告经济损失及合理维权费用共计人民币[具体金额]元
3. 判令被告销毁侵权繁殖材料
4. 判令被告承担本案全部诉讼费用

## 事实与理由
- **品种权信息**：品种名称[具体名称]，品种权号[具体号码]
- **侵权行为**：[被告具体侵权行为]
- **损害后果**：[原告遭受的损失情况]
- **法律依据**：《中华人民共和国植物新品种保护条例》

## 证据清单
1. [证据名称]：[证明内容]
2. [证据名称]：[证明内容]
3. [证据名称]：[证明内容]
4. [证据名称]：[证明内容]`;
          break;
        case '商标撤销复审行政纠纷起诉状':
          conversionResult = `# ${selectedTemplate}

## 当事人信息
- 原告：[申请人名称]
- 法定代表人：[姓名]
- 住所：[地址]
- 被告：国家知识产权局
- 住所地：北京市海淀区蓟门桥西土城路6号

## 诉讼请求
1. 撤销被告作出的[具体文号]商标撤销复审决定
2. 判令被告重新作出决定，维持原告商标注册
3. 判令被告承担本案诉讼费用

## 事实与理由
- **商标信息**：商标名称[具体名称]，注册号[具体号码]
- **争议情况**：[具体争议内容]
- **复审理由**：[原告复审理由]
- **法律依据**：《中华人民共和国商标法》

## 证据清单
1. [证据名称]：[证明内容]
2. [证据名称]：[证明内容]
3. [证据名称]：[证明内容]
4. [证据名称]：[证明内容]`;
          break;
        case '商标无效行政纠纷起诉状':
          conversionResult = `# ${selectedTemplate}

## 当事人信息
- 原告：[申请人名称]
- 法定代表人：[姓名]
- 住所：[地址]
- 被告：国家知识产权局
- 住所地：北京市海淀区蓟门桥西土城路6号

## 诉讼请求
1. 撤销被告作出的[具体文号]商标无效宣告裁定
2. 判令被告重新作出决定，维持原告商标注册
3. 判令被告承担本案诉讼费用

## 事实与理由
- **商标信息**：商标名称[具体名称]，注册号[具体号码]
- **无效宣告情况**：[具体无效宣告内容]
- **答辩理由**：[原告答辩理由]
- **法律依据**：《中华人民共和国商标法》

## 证据清单
1. [证据名称]：[证明内容]
2. [证据名称]：[证明内容]
3. [证据名称]：[证明内容]
4. [证据名称]：[证明内容]`;
          break;
        default:
          conversionResult = `# 要素式文书

## 当事人信息
- 原告：[从文件中提取]
- 被告：[从文件中提取]

## 诉讼请求
- [从文件中提取]

## 事实与理由
- [从文件中提取]

## 证据清单
- [从文件中提取]`;
      }

      // 创建新会话
      const sessionId = Date.now().toString();
      const newSession: SearchSession = {
        id: sessionId,
        title: `要素式转换：${selectedFile.name}`,
        originalTitle: `要素式转换：${selectedFile.name}`,
        updatedAt: new Date().toISOString(),
        isPinned: false,
        messages: [
          { role: 'user', content: `转换文件：${selectedFile.name}` },
          { role: 'assistant', content: conversionResult }
        ],
        type: 'legal-document'
      };

      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(sessionId);
      setLocalMessages([
        { role: 'user', content: `转换文件：${selectedFile.name}` },
        { role: 'assistant', content: conversionResult }
      ]);

      // 导出转换后的文件
      setTimeout(async () => {
        try {
          const exportFilename = selectedFile.name.replace(/\.[^/.]+$/, "") + "_要素式";
          await exportAsWord(conversionResult, {
            title: '要素式文书',
            filename: exportFilename
          });
        } catch (error) {
          console.error('导出文件失败:', error);
        }
      }, 500);

    } catch (error) {
      console.error('转换失败:', error);
      // 显示错误信息
      const errorSession: SearchSession = {
        id: Date.now().toString(),
        title: '转换失败',
        originalTitle: '转换失败',
        updatedAt: new Date().toISOString(),
        isPinned: false,
        messages: [
          { role: 'user', content: `转换文件：${selectedFile.name}` },
          { role: 'assistant', content: '# 转换失败\n\n文件转换过程中出现错误，请重试。' }
        ],
        type: 'legal-document'
      };

      setSessions(prev => [errorSession, ...prev]);
      setCurrentSessionId(errorSession.id);
      setLocalMessages([
        { role: 'user', content: `转换文件：${selectedFile.name}` },
        { role: 'assistant', content: '# 转换失败\n\n文件转换过程中出现错误，请重试。' }
      ]);
    } finally {
      setConverting(false);
      setSelectedFile(null);
    }
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
        await exportAsImage(lastMessage.content, { title: '法律文书' });
      } catch (error) {
        console.error('导出图片失败:', error);
      }
    }
  };

  const handleDownloadPDF = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      try {
        await exportAsPDF(lastMessage.content, { title: '法律文书' });
      } catch (error) {
        console.error('导出PDF失败:', error);
      }
    }
  };

  const handleDownloadWord = async () => {
    const lastMessage = localMessages.filter(m => m.role === 'assistant').pop();
    if (lastMessage) {
      try {
        await exportAsWord(lastMessage.content, { title: '法律文书' });
      } catch (error) {
        console.error('导出Word失败:', error);
      }
    }
  };

  return (
    <div className="fixed business-page-shell left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 text-foreground flex overflow-hidden">
      <div className="relative z-10 w-64 h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-r border-sky-200 dark:border-sky-900/30 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 dark:border-sky-900/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800 dark:text-sky-300">起草记录</h2>
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
          {getSortedSessions().map((session) => (
            <div
              key={session.id}
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
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => handleTogglePin(e, session.id)}
                  className={`p-1 rounded transition-colors ${
                    session.isPinned ? 'text-sky-500' : 'text-gray-400 hover:text-sky-500'
                  }`}
                  title={session.isPinned ? '取消置顶' : '置顶'}
                >
                  <Pin size={14} className={session.isPinned ? 'fill-current' : ''} />
                </button>
                <button
                  onClick={(e) => handleEditSession(e, session)}
                  className="p-1 rounded text-gray-400 hover:text-blue-500 transition-colors"
                  title="编辑"
                >
                  ✏️
                </button>
                <button
                  onClick={(e) => handleDeleteSession(e, session.id)}
                  className="p-1 rounded text-gray-400 hover:text-red-500 transition-colors"
                  title="删除"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
          {sessions.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <p className="text-sm">暂无起草记录</p>
              <p className="text-xs mt-1">点击上方 + 开始新起草</p>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-sky-200 dark:border-sky-900/30">
          <button
            onClick={() => router.push('/settings')}
            className="w-full flex items-center justify-center gap-2 p-3 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-700 dark:text-sky-300 transition-colors"
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
                    <div className="w-4 h-4 rounded-full bg-sky-400 animate-pulse" />
                    <div className="w-4 h-4 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: '0.2s' }} />
                    <div className="w-4 h-4 rounded-full bg-indigo-400 animate-pulse" style={{ animationDelay: '0.4s' }} />
                  </div>
                  <h1 className="text-5xl font-bold bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
                    复杂文书，简单生成
                  </h1>
                  <div className="inline-flex items-center gap-3 bg-gradient-to-r from-sky-100 to-blue-100 dark:from-sky-900/30 dark:to-blue-900/30 rounded-full px-6 py-3 text-sm font-semibold text-sky-700 dark:text-sky-200 shadow-xl shadow-sky-500/10">
                    <Sparkles size={20} className="text-sky-500" />
                    1分钟上手文书起草
                  </div>
                </div>

                <div className="flex items-center justify-center gap-4 mb-10 overflow-x-auto pb-3 w-full">
                  {[
                    { id: 'ai', name: 'AI智能文书起草', icon: Sparkles },
                    { id: 'element', name: '要素式文书起草', icon: BookOpen },
                    { id: 'convert', name: '要素式文书转换', icon: ArrowRight }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-7 py-4 rounded-2xl border-2 transition-all duration-300 flex items-center gap-3 font-semibold ${
                        activeTab === tab.id 
                          ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white border-transparent shadow-2xl shadow-sky-500/30 scale-105' 
                          : 'bg-white/80 dark:bg-slate-800/80 border-sky-200/50 dark:border-sky-800/50 text-slate-700 dark:text-slate-300 hover:border-sky-400/50 dark:hover:border-sky-600/50 hover:bg-sky-50/50 dark:hover:bg-sky-900/20'
                      }`}
                    >
                      <tab.icon size={20} />
                      {tab.name}
                    </button>
                  ))}
                </div>

                <div className="w-full max-w-5xl">
                  {activeTab === 'ai' && (
                    <div className="rounded-3xl border border-sky-200/50 dark:border-sky-800/50 bg-white/90 dark:bg-slate-800/90 p-6 backdrop-blur-2xl shadow-2xl hover:shadow-sky-500/20 transition-all duration-500">
                      <div className="mb-6">
                        <div className="flex items-center gap-4 mb-4">
                          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center shadow-xl shadow-sky-500/30">
                            <MessageSquare size={24} className="text-white" />
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200">AI智能起草</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400">描述您的需求，AI为您生成专业文书</p>
                          </div>
                        </div>
                        <div className="relative">
                          <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="请详细描述您的文书起草需求，例如：我需要一份民间借贷纠纷的民事起诉状，原告是张三，被告是李四，借款金额50万元..."
                            rows={6}
                            className="w-full resize-none rounded-2xl border-2 border-sky-200/50 dark:border-sky-800/50 bg-white/70 dark:bg-slate-700/70 px-6 py-5 text-base text-slate-800 dark:text-slate-200 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-all focus:border-sky-500 focus:ring-4 focus:ring-sky-500/20"
                            style={{ maxHeight: '400px' }}
                          />
                          <div className="absolute bottom-5 right-5 text-xs text-slate-400 dark:text-slate-500 bg-white/90 dark:bg-slate-800/90 px-3 py-1.5 rounded-lg">
                            {input.length}/5000
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <button className="flex items-center gap-3 rounded-xl border-2 border-sky-200/50 dark:border-sky-800/50 bg-white/60 dark:bg-slate-700/60 px-4 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-sky-500/10 hover:border-sky-500/50 hover:shadow-xl">
                            <Upload size={18} className="text-sky-600 dark:text-sky-400" />
                            相关材料
                          </button>
                        </div>
                        <button
                          onClick={() => handleSend()}
                          disabled={!input.trim() || loading}
                          className="rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-8 py-3 text-white font-bold transition-all hover:shadow-2xl hover:shadow-sky-500/40 disabled:opacity-50 disabled:cursor-not-allowed border-2 border-white/30 flex items-center gap-3 hover:scale-[1.02] active:scale-[0.98]"
                        >
                          {loading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                          开始起草
                        </button>
                      </div>
                      
                      <div className="mt-6">
                        <div className="flex items-center gap-3 mb-4">
                          <Crown size={20} className="text-sky-500" />
                          <h4 className="text-lg font-bold text-slate-800 dark:text-slate-200">快速模板</h4>
                        </div>
                        <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
                          {DOCUMENT_CATEGORIES.map((category) => (
                            <button
                              key={category}
                              className="px-4 py-1.5 rounded-full border border-sky-200/50 dark:border-sky-800/50 text-slate-700 dark:text-slate-400 text-xs font-medium whitespace-nowrap hover:bg-sky-500/10 hover:border-sky-500/50 transition-all"
                            >
                              {category}
                            </button>
                          ))}
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {DOCUMENT_TEMPLATES.map((template) => {
                            const Icon = template.icon;
                            return (
                              <button
                                key={template.id}
                                onClick={() => handleSend(template.name)}
                                className="group relative overflow-hidden rounded-2xl border-2 border-sky-200/50 dark:border-sky-800/50 bg-white/80 dark:bg-slate-800/80 p-4 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:border-sky-500/50 hover:shadow-2xl hover:shadow-sky-500/20"
                              >
                                <div className="absolute inset-0 bg-gradient-to-br from-sky-500/15 via-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                                <div className="relative">
                                  <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center shadow-xl">
                                      <Icon size={20} className="text-white" />
                                    </div>
                                    <span className="font-bold text-sm text-slate-800 dark:text-sky-200">{template.name}</span>
                                  </div>
                                  <p className="text-xs text-slate-600 dark:text-slate-400">{template.desc}</p>
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'element' && (
                    <div className="rounded-3xl border border-sky-200/50 dark:border-sky-800/50 bg-white/90 dark:bg-slate-800/90 p-8 backdrop-blur-2xl shadow-2xl">
                      <div className="flex items-center gap-4 mb-8">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center shadow-xl">
                          <BookOpen size={28} className="text-white" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200">要素式文书起草</h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400">选择模板，填写要素，快速生成</p>
                        </div>
                      </div>
                      <div className="space-y-8">
                        <select
                          value={selectedTemplate}
                          onChange={(e) => setSelectedTemplate(e.target.value)}
                          className="w-full rounded-xl border-2 border-sky-200/50 dark:border-sky-800/50 bg-white/70 dark:bg-slate-700/70 px-6 py-5 text-base text-slate-800 dark:text-slate-200 outline-none transition-all focus:border-sky-500 focus:ring-4 focus:ring-sky-500/20"
                        >
                          <option value="">请选择要素式文书模板</option>
                          <option value="civil-complaint">民事起诉状</option>
                          <option value="administrative-complaint">行政起诉状</option>
                          <option value="criminal-complaint">刑事自诉状</option>
                        </select>
                        <div className="relative">
                          <textarea
                            value={caseSummary}
                            onChange={(e) => setCaseSummary(e.target.value)}
                            placeholder="请您选择要素式文书模板，并输入完整的案情概要..."
                            rows={7}
                            className="w-full resize-none rounded-xl border-2 border-sky-200/50 dark:border-sky-800/50 bg-white/70 dark:bg-slate-700/70 px-6 py-5 text-base text-slate-800 dark:text-slate-200 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-all focus:border-sky-500 focus:ring-4 focus:ring-sky-500/20"
                            style={{ maxHeight: '350px' }}
                          />
                          <div className="absolute bottom-5 right-5 text-xs text-slate-400 dark:text-slate-500 bg-white/90 dark:bg-slate-800/90 px-3 py-1.5 rounded-lg">
                            {caseSummary.length}/5000
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <button className="flex items-center gap-3 rounded-xl border-2 border-sky-200/50 dark:border-sky-800/50 bg-white/60 dark:bg-slate-700/60 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-sky-500/10">
                              <File size={20} className="text-sky-600 dark:text-sky-400" />
                              模板
                            </button>
                            <button className="flex items-center gap-3 rounded-xl border-2 border-sky-200/50 dark:border-sky-800/50 bg-white/60 dark:bg-slate-700/60 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-sky-500/10">
                              <Upload size={20} className="text-sky-600 dark:text-sky-400" />
                              上传
                            </button>
                          </div>
                          <button
                            onClick={() => {
                              if (selectedTemplate && caseSummary.trim()) {
                                handleSend(`要素式文书起草：${selectedTemplate}\n案情概要：${caseSummary}`);
                              } else {
                                showAlert('请选择模板并输入案情概要', 'warning');
                              }
                            }}
                            disabled={!selectedTemplate || !caseSummary.trim() || loading}
                            className="rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-10 py-4 text-white font-bold transition-all hover:shadow-2xl hover:shadow-sky-500/40 disabled:opacity-50 disabled:cursor-not-allowed border-2 border-white/30 flex items-center gap-4"
                          >
                            {loading ? <Loader2 size={24} className="animate-spin" /> : <Send size={24} />}
                            开始起草
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'convert' && (
                    <div className="rounded-3xl border border-sky-200/50 dark:border-sky-800/50 bg-white/90 dark:bg-slate-800/90 p-10 backdrop-blur-2xl shadow-2xl">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                        <div 
                          className={`border-2 border-dashed border-sky-300/50 dark:border-sky-700/50 rounded-3xl p-10 text-center transition-all ${selectedFile ? 'bg-gradient-to-br from-sky-100/50 to-blue-100/50 dark:from-sky-900/30 dark:to-blue-900/30 border-sky-400/50' : 'bg-gradient-to-br from-sky-50/30 to-blue-50/30 dark:from-sky-900/20 dark:to-blue-900/20'}`}
                          onClick={() => fileInputRef.current?.click()}
                        >
                          <input
                            ref={fileInputRef}
                            type="file"
                            accept=".doc,.docx"
                            onChange={(e) => {
                              if (e.target.files && e.target.files[0]) {
                                setSelectedFile(e.target.files[0]);
                              }
                            }}
                            className="hidden"
                          />
                          <div className="flex flex-col items-center justify-center">
                            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-sky-100 via-blue-100 to-indigo-100 dark:from-sky-900/30 dark:to-blue-900/30 flex items-center justify-center mb-6 shadow-lg">
                              <FileText size={48} className="text-sky-500 dark:text-sky-400" />
                            </div>
                            {selectedFile ? (
                              <>
                                <p className="text-lg font-semibold text-sky-700 dark:text-sky-200 mb-3">
                                  {selectedFile.name}
                                </p>
                                <p className="text-sm text-slate-600 dark:text-slate-400 mb-5">
                                  {Math.round(selectedFile.size / 1024)} KB
                                </p>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedFile(null);
                                  }}
                                  className="text-sm text-red-600 dark:text-red-400 hover:underline"
                                >
                                  重新选择
                                </button>
                              </>
                            ) : (
                              <>
                                <p className="text-lg font-semibold text-sky-700 dark:text-sky-200 mb-3">
                                  请点击或拖拽上传您的起诉状
                                </p>
                                <p className="text-sm text-slate-600 dark:text-slate-400 mb-5">
                                  我将会为您转化为要素式起诉状
                                </p>
                                <p className="text-xs text-slate-400 dark:text-slate-500">
                                  支持doc、docx格式，文件最大50 MB
                                </p>
                              </>
                            )}
                          </div>
                        </div>
                        <div>
                          <input
                            type="text"
                            placeholder="搜索要转换的要素式文书模板"
                            className="w-full rounded-xl border-2 border-sky-200/50 dark:border-sky-800/50 bg-white/70 dark:bg-slate-700/70 px-6 py-5 text-base text-slate-800 dark:text-slate-200 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 mb-6 transition-all focus:border-sky-500 focus:ring-4 focus:ring-sky-500/20"
                          />
                          <div className="space-y-4 max-h-96 overflow-y-auto p-2">
                            {['侵害商业秘密纠纷起诉状', '侵害植物新品种权纠纷起诉状', '商标撤销复审行政纠纷起诉状', '商标无效行政纠纷起诉状'].map((template) => (
                              <div
                                key={template}
                                className={`flex items-center gap-4 p-5 rounded-xl cursor-pointer transition-all ${selectedTemplate === template ? 'bg-sky-100/50 dark:bg-sky-900/20 border-2 border-sky-300/50' : 'bg-white/70 dark:bg-slate-800/70 border-2 border-transparent hover:border-sky-300/50'}`}
                                onClick={() => setSelectedTemplate(template)}
                              >
                                <input 
                                  type="radio" 
                                  name="template" 
                                  checked={selectedTemplate === template} 
                                  onChange={() => setSelectedTemplate(template)}
                                  className="text-sky-500 w-6 h-6"
                                />
                                <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{template}</span>
                              </div>
                            ))}
                          </div>
                          <button
                            onClick={() => handleConvert()}
                            disabled={!selectedFile || converting}
                            className="mt-6 w-full rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-10 py-4 text-white font-bold transition-all hover:shadow-2xl hover:shadow-sky-500/40 disabled:opacity-50 disabled:cursor-not-allowed border-2 border-white/30 flex items-center justify-center gap-4"
                          >
                            {converting ? <Loader2 size={24} className="animate-spin" /> : <ArrowRight size={24} />}
                            {converting ? '转换中...' : '开始转换'}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div ref={chatContainerRef} className="space-y-6">
                <div className="flex items-center justify-between rounded-3xl border border-sky-200/50 dark:border-sky-800/50 bg-white/90 dark:bg-slate-800/90 p-6 backdrop-blur-2xl shadow-xl mb-8">
                  <div className="flex items-center gap-5">
                    <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-blue-500 shadow-2xl border-2 border-white/30">
                      <ScaleIcon size={28} className="text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-slate-800 dark:text-sky-200">文书起草</h2>
                      <p className="text-sm text-slate-500 dark:text-slate-400">AI智能生成专业法律文书</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-3 rounded-xl border border-sky-200/50 dark:border-sky-800/50 bg-white/70 dark:bg-slate-700/70 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-sky-500/10 hover:border-sky-500/50 hover:shadow-lg"
                    >
                      {copied ? <CheckCircle size={18} className="text-green-500" /> : <Copy size={18} />}
                      {copied ? '已复制' : '复制'}
                    </button>
                    <DownloadDropdown
                      onDownloadImage={handleDownloadImage}
                      onDownloadPDF={handleDownloadPDF}
                      onDownloadWord={handleDownloadWord}
                      theme="blue"
                    />
                    <button
                      onClick={() => router.push('/history')}
                      className="flex items-center gap-3 rounded-xl border border-sky-200/50 dark:border-sky-800/50 bg-white/70 dark:bg-slate-700/70 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all hover:bg-sky-500/10 hover:border-sky-500/50 hover:shadow-lg"
                    >
                      <History size={18} className="text-sky-600 dark:text-sky-400" />
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
                      <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-blue-500 border-2 border-white/30 shadow-xl">
                        <ScaleIcon size={24} className="text-white" />
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] rounded-3xl px-7 py-6 backdrop-blur-2xl shadow-xl ${
                        message.role === 'user'
                          ? 'bg-gradient-to-br from-sky-500/25 to-blue-500/25 border border-sky-400/40 text-slate-800 dark:text-sky-200'
                          : 'bg-white/95 dark:bg-slate-800/95 border border-sky-200/50 dark:border-sky-800/50 text-slate-800 dark:text-slate-200'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <p className="text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      ) : (
                        <div className="prose prose-lg dark:prose-invert max-w-none prose-headings:text-sky-700 dark:prose-headings:text-sky-400 prose-strong:text-slate-800 dark:prose-strong:text-slate-200">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>

                    {message.role === 'user' && (
                      <div className="ml-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-400 to-indigo-500 border-2 border-white/30 shadow-xl">
                        <MessageSquare size={24} className="text-white" />
                      </div>
                    )}
                  </div>
                ))}

                {currentMessage && (
                  <div className="flex justify-start animate-fadeIn">
                    <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-blue-500 border-2 border-white/30 shadow-xl">
                      <ScaleIcon size={24} className="text-white" />
                    </div>
                    <div className="max-w-[85%] rounded-3xl px-7 py-6 bg-white/95 dark:bg-slate-800/95 border border-sky-200/50 dark:border-sky-800/50 backdrop-blur-2xl shadow-xl">
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
                    <div className="mr-5 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500 to-blue-600 border-2 border-white/30 shadow-xl">
                      {loading ? <Loader2 size={24} className="text-white animate-spin" /> : <ScaleIcon size={24} className="text-white" />}
                    </div>
                    <div className="max-w-[85%] rounded-3xl border border-sky-200/50 dark:border-sky-800/50 bg-white/90 dark:bg-slate-800/90 px-7 py-6 backdrop-blur-2xl shadow-xl">
                      <div className="flex items-center gap-3">
                        <div className="h-3 w-3 animate-pulse rounded-full bg-sky-600"></div>
                        <div className="h-3 w-3 animate-pulse rounded-full bg-sky-600" style={{ animationDelay: '0.2s' }}></div>
                        <div className="h-3 w-3 animate-pulse rounded-full bg-sky-600" style={{ animationDelay: '0.4s' }}></div>
                        <span className="text-sm text-sky-700 dark:text-sky-300 font-semibold">{loadingText}</span>
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
    </div>
  );
}