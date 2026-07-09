'use client';

import { useState, useRef, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Upload, FileText, AlertTriangle, CheckCircle, Loader2, AlertCircle, Sparkles, Crown, Shield, BookOpen, Plus, MessageSquare, Trash2, Pin, Edit, MoreHorizontal, Settings, ExternalLink, Star } from 'lucide-react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ScaleIcon from '@/components/ScaleIcon';
import { uploadDocument, reviewContract, ContractReviewResponse, RiskLevel, getContractDetails, startContractReviewStream, getContractReviewStream, getContractHistory, deleteContract, updateContractFilename, createFavorite } from '@/lib/api';
import { useContractStore } from '@/store/contractStore';
import { showAlert } from '@/components/AlertDialog';

function ContractPageContent() {
  const { currentSessionId, sessions, createSession, deleteSession, renameSession, togglePin, setCurrentSession, setReviewResult: setStoreReviewResult, getSortedSessions } = useContractStore();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [contractId, setContractId] = useState<string>('');
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [reviewResult, setReviewResult] = useState<ContractReviewResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [currentSummary, setCurrentSummary] = useState('');
  const [currentRisks, setCurrentRisks] = useState<ContractReviewResponse['risks']>([]);
  const [loadingText, setLoadingText] = useState('');
  const [isDisplayingSummary, setIsDisplayingSummary] = useState(false);
  const [displayedRiskCount, setDisplayedRiskCount] = useState(0);
  const [currentRiskIndex, setCurrentRiskIndex] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (currentSessionId) {
      const currentSession = sessions.find(s => s.id === currentSessionId);
      if (currentSession?.reviewResult) {
        setReviewResult(currentSession.reviewResult);
        if (currentSession.reviewResult.risks) {
          setDisplayedRiskCount(currentSession.reviewResult.risks.length);
        }
      }
    } else {
      setReviewResult(null);
      setDisplayedRiskCount(0);
    }
  }, [currentSessionId, sessions]);

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const history = await getContractHistory();
      if (history?.documents) {
        // 先清空现有会话，避免重复加载
        sessions.forEach(session => {
          if (session.contractId) {
            deleteSession(session.id);
          }
        });
        // 重新加载所有历史记录
        history.documents.forEach((doc: any) => {
          const sessionId = createSession(doc.filename, doc.id);
          if (doc.review_result) {
            setStoreReviewResult(sessionId, doc.review_result);
          }
        });
      }
    } catch (err) {
      console.error('加载历史记录失败:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleNewContract = () => {
    setFile(null);
    setUploadResult(null);
    setReviewResult(null);
    setThinkingSteps([]);
    setError('');
    setCurrentSession('');
  };

  const handleSwitchSession = (sessionId: string) => {
    setCurrentSession(sessionId);
    const session = sessions.find(s => s.id === sessionId);
    if (session?.contractId) {
      loadContractDetails(session.contractId);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    const session = sessions.find(s => s.id === sessionId);
    if (session?.contractId) {
      try {
        await deleteContract(session.contractId);
      } catch (err) {
        console.error('删除合同失败:', err);
      }
    }
    deleteSession(sessionId);
    if (currentSessionId === sessionId) {
      setReviewResult(null);
    }
  };

  const handleTogglePin = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    togglePin(sessionId);
    setActiveMenuId(null);
  };

  const handleStartEdit = (sessionId: string, currentTitle: string) => {
    setEditingSessionId(sessionId);
    setEditTitle(currentTitle);
    setActiveMenuId(null);
  };

  const handleSaveEdit = () => {
    if (editingSessionId && editTitle.trim()) {
      renameSession(editingSessionId, editTitle.trim());
      setEditingSessionId(null);
      setEditTitle('');
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditTitle('');
  };

  const handleToggleMenu = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setActiveMenuId(activeMenuId === sessionId ? null : sessionId);
  };

  const handleFavorite = async () => {
    if (!reviewResult || !contractId) return;
    
    try {
      const title = `合同审查: ${sessions.find(s => s.contractId === contractId)?.customFilename || sessions.find(s => s.contractId === contractId)?.filename || '未命名合同'}`;
      const content = reviewResult.overall_summary || '合同审查结果';
      
      await createFavorite({
        title,
        content,
        source_type: 'contract',
        source_id: contractId
      });
      
      showAlert('收藏成功！', 'success');
    } catch (err) {
      console.error('收藏失败:', err);
      showAlert('收藏失败，请稍后重试', 'error');
    }
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

  const loadContractDetails = async (id: string) => {
    setReviewing(true);
    setError('');
    setThinkingSteps([]);
    setLoadingText('🔍 正在加载历史审查结果...');

    try {
      const result = await getContractDetails(id);
      setContractId(id);
      setReviewResult(result);
      setThinkingSteps(['✅ 历史审查结果已加载']);
      
      if (result.risks || result.contract?.risks) {
        const risks = result.risks || result.contract?.risks || [];
        const validRisks = risks.filter((risk: any) => {
          const hasRiskExplanation = risk.risk_explanation && risk.risk_explanation.trim() !== '';
          const hasOriginalClause = risk.original_clause && risk.original_clause.trim() !== '';
          const hasReviseSuggestion = risk.revise_suggestion && risk.revise_suggestion.trim() !== '';
          const hasLegalBasis = risk.legal_basis && risk.legal_basis.length > 0 && risk.legal_basis.some((b: any) => b && b.trim() !== '');
          
          return hasRiskExplanation || hasOriginalClause || hasReviseSuggestion || hasLegalBasis;
        });
        
        setDisplayedRiskCount(validRisks.length);
        setCurrentRiskIndex(validRisks.length > 0 ? 0 : 0);
      }
    } catch (err: any) {
      setError(err.message || '加载历史记录失败');
      setThinkingSteps([`❌ 加载失败: ${err.message}`]);
    } finally {
      setReviewing(false);
      setLoadingText('');
    }
  };

  const DEMO_CONTRACT_TEXT = `
劳动合同

甲方（用人单位）：某某科技有限公司
乙方（劳动者）：张三

第一条 合同期限
本合同为固定期限劳动合同，期限为三年，自2024年1月1日起至2026年12月31日止。试用期为六个月。

第二条 工作内容和工作地点
1. 乙方同意根据甲方工作需要，从事软件开发工作。
2. **甲方有权根据业务需要单方面调整乙方的工作岗位和工作地点，乙方必须无条件服从。**
3. 工作地点：甲方指定的任何办公场所。

第三条 工作时间和休息休假
1. 实行标准工时制，每周工作五天，每天工作八小时。
2. **因工作需要，乙方应当服从甲方安排的加班，周末和节假日加班不另行支付加班费。**
3. 乙方每年享有带薪年休假5天。

第四条 劳动报酬
1. 乙方月工资为人民币8000元（税前）。
2. **试用期内不缴纳社会保险和住房公积金。**
3. **工资发放时间由甲方根据经营状况决定，可能延迟发放。**

第五条 社会保险和福利待遇
1. 甲方依法为乙方缴纳社会保险（试用期除外）。
2. **乙方因工负伤的，医疗费用由乙方自行承担50%。**

第六条 劳动纪律
1. 乙方应当遵守甲方的规章制度。
2. **乙方不得拒绝甲方安排的任何工作任务，否则视为严重违反劳动纪律。**
3. **乙方每月迟到或早退累计超过3次，甲方有权扣除当月全部工资。**

第七条 保密和竞业限制
1. **乙方在职期间及离职后五年内，不得从事与甲方相同或相似的业务。**
2. **违反竞业限制的，乙方应当向甲方支付违约金人民币50万元。**

第八条 合同的解除和终止
1. **乙方提前解除合同的，应当提前三个月书面通知甲方，并支付违约金人民币10万元。**
2. **甲方可以随时解除本合同，无需支付任何经济补偿。**

第九条 其他
1. 本合同一式两份，甲乙双方各执一份。
2. 本合同自双方签字盖章之日起生效。

甲方（盖章）：某某科技有限公司
乙方（签字）：张三
日期：2024年1月1日
  `.trim();

  const handleDemoContract = async () => {
    setError('');
    setThinkingSteps([]);
    setReviewResult(null);
    setCurrentSummary('');
    setCurrentRisks([]);
    setLoadingText('');
    
    const demoContractId = `demo_contract_${Date.now()}`;
    const sessionId = createSession('高风险劳动合同示例', demoContractId);
    setContractId(demoContractId);
    setUploadResult({
      success: true,
      message: '示例合同已加载',
      contract_id: demoContractId,
      chunk_count: 1,
      text_length: DEMO_CONTRACT_TEXT.length
    });
    
    setTimeout(() => {
      handleDemoReview(demoContractId, sessionId);
    }, 500);
  };

  const handleDemoReview = async (demoId: string, sessionId: string) => {
    setReviewing(true);
    setError('');
    setThinkingSteps([]);
    setReviewResult(null);
    setCurrentSummary('');
    setCurrentRisks([]);
    setLoadingText('🔍 正在分析合同结构...');
    setIsDisplayingSummary(false);
    setDisplayedRiskCount(0);

    try {
      const startResponse = await startContractReviewStream(undefined, DEMO_CONTRACT_TEXT);
      const streamSessionId = startResponse.session_id;
      
      const eventSource = getContractReviewStream(streamSessionId);
      
      let finalResult: any = null;
      let currentRisksData: any[] = [];
      let overallSummaryText = '';
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'connected':
              console.log('已连接到流式输出');
              break;
              
            case 'thinking':
              setThinkingSteps(prev => [...prev, data.data.step]);
              setLoadingText(data.data.step.substring(2));
              break;
              
            case 'overall_summary':
              overallSummaryText = data.data.text;
              setReviewResult({
                overall_summary: overallSummaryText,
                overall_summary_structured: data.data.structured,
                risks: [],
                is_image_based: false
              } as any);
              setIsDisplayingSummary(true);
              displaySummary(overallSummaryText);
              break;
              
            case 'risk':
              currentRisksData.push(data.data);
              setCurrentRisks(currentRisksData);
              setDisplayedRiskCount(currentRisksData.length);
              break;
              
            case 'completed':
              finalResult = data.data;
              setReviewResult(finalResult);
              setStoreReviewResult(sessionId, finalResult);
              setThinkingSteps(prev => [...prev, `✅ 审查完成，发现 ${finalResult.risks.length} 个风险项`]);
              setReviewing(false);
              setLoadingText('');
              setIsDisplayingSummary(false);
              eventSource.close();
              break;
              
            case 'error':
              setError(data.data.error);
              setThinkingSteps(prev => [...prev, `❌ 审查失败: ${data.data.error}`]);
              setReviewing(false);
              setLoadingText('');
              eventSource.close();
              break;
          }
        } catch (e) {
          console.error('解析流式数据失败:', e);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE连接错误:', error);
        setError('流式连接失败');
        setReviewing(false);
        eventSource.close();
      };
      
    } catch (err: any) {
      let errorMsg = err.message || '审查失败';
      
      if (errorMsg.includes('Rate limit') || errorMsg.includes('rate_limit_exceeded')) {
        errorMsg = 'API 速率限制：今日配额已用完。请等待约 10 分钟后重试，或更换 API Key。';
      } else if (errorMsg.includes('Failed to fetch')) {
        errorMsg = '无法连接到服务器，请确保后端服务已启动';
      }
      
      setError(errorMsg);
      setThinkingSteps(prev => [...prev, `❌ 审查失败: ${errorMsg}`]);
      setReviewing(false);
      setLoadingText('');
      setIsDisplayingSummary(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'image/jpeg',
      'image/jpg',
      'image/png'
    ];
    
    const fileExtension = selectedFile.name.toLowerCase().split('.').pop();
    const isValidExtension = ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png'].includes(fileExtension || '');
    
    if (!validTypes.includes(selectedFile.type) && !isValidExtension) {
      setError('仅支持 PDF、Word 文档和图像文件（JPG/PNG）');
      return;
    }

    setFile(selectedFile);
    setError('');
    setUploadResult(null);
    setReviewResult(null);
    setThinkingSteps([]);
    setCurrentSummary('');
    setCurrentRisks([]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError('');
    setThinkingSteps([]);

    try {
      const result = await uploadDocument(file);
      setUploadResult(result);
      setContractId(result.contract_id);
      const sessionId = createSession(file.name, result.contract_id);
    } catch (err: any) {
      setError(err.message || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleReview = async () => {
    if (!contractId) return;

    setReviewing(true);
    setError('');
    setThinkingSteps([]);
    setReviewResult(null);
    setCurrentSummary('');
    setCurrentRisks([]);
    setLoadingText('🔍 正在分析合同结构...');
    setIsDisplayingSummary(false);
    setDisplayedRiskCount(0);

    try {
      const startResponse = await startContractReviewStream(contractId);
      const sessionId = startResponse.session_id;
      
      const eventSource = getContractReviewStream(sessionId);
      
      let finalResult: any = null;
      let currentRisksData: any[] = [];
      let overallSummaryText = '';
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'connected':
              console.log('已连接到流式输出');
              break;
              
            case 'thinking':
              setThinkingSteps(prev => [...prev, data.data.step]);
              setLoadingText(data.data.step.substring(2));
              break;
              
            case 'overall_summary':
              overallSummaryText = data.data.text;
              setReviewResult({
                overall_summary: overallSummaryText,
                overall_summary_structured: data.data.structured,
                risks: [],
                is_image_based: false
              } as any);
              setIsDisplayingSummary(true);
              displaySummary(overallSummaryText);
              break;
              
            case 'risk':
              currentRisksData.push(data.data);
              setCurrentRisks(currentRisksData);
              setDisplayedRiskCount(currentRisksData.length);
              break;
              
            case 'completed':
              finalResult = data.data;
              setReviewResult(finalResult);
              if (currentSessionId) {
                setStoreReviewResult(currentSessionId, finalResult);
              }
              setThinkingSteps(prev => [...prev, `✅ 审查完成，发现 ${finalResult.risks.length} 个风险项`]);
              setReviewing(false);
              setLoadingText('');
              setIsDisplayingSummary(false);
              eventSource.close();
              break;
              
            case 'error':
              setError(data.data.error);
              setThinkingSteps(prev => [...prev, `❌ 审查失败: ${data.data.error}`]);
              setReviewing(false);
              setLoadingText('');
              eventSource.close();
              break;
          }
        } catch (e) {
          console.error('解析流式数据失败:', e);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE连接错误:', error);
        setError('流式连接失败');
        setReviewing(false);
        eventSource.close();
      };
      
    } catch (err: any) {
      let errorMsg = err.message || '审查失败';
      
      if (errorMsg.includes('Rate limit') || errorMsg.includes('rate_limit_exceeded')) {
        errorMsg = 'API 速率限制：今日配额已用完。请等待约 10 分钟后重试，或更换 API Key。';
      } else if (errorMsg.includes('Failed to fetch')) {
        errorMsg = '无法连接到服务器，请确保后端服务已启动';
      }
      
      setError(errorMsg);
      setThinkingSteps(prev => [...prev, `❌ 审查失败: ${errorMsg}`]);
      setReviewing(false);
      setLoadingText('');
      setIsDisplayingSummary(false);
    }
  };

  const displaySummary = async (content: string) => {
    setCurrentSummary('');
    
    let accumulatedText = '';
    const chunkSize = 2;
    
    for (let i = 0; i < content.length; i += chunkSize) {
      accumulatedText += content.slice(i, i + chunkSize);
      setCurrentSummary(accumulatedText);
      const delay = Math.random() * 30 + 20;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  };

  const getRiskStyle = (level: string | RiskLevel) => {
    const levelLower = (typeof level === 'string' ? level : level).toLowerCase();
    
    if (levelLower.includes('high') || levelLower.includes('高')) {
      return {
        bg: 'bg-red-50 dark:bg-red-950/20',
        border: 'border-red-200 dark:border-red-900/50',
        text: 'text-red-700 dark:text-red-400',
        badge: 'bg-red-500',
        icon: '🚨',
      };
    } else if (levelLower.includes('medium') || levelLower.includes('中')) {
      return {
        bg: 'bg-yellow-50 dark:bg-yellow-950/20',
        border: 'border-yellow-200 dark:border-yellow-900/50',
        text: 'text-yellow-700 dark:text-yellow-400',
        badge: 'bg-yellow-500',
        icon: '⚠️',
      };
    } else if (levelLower.includes('low') || levelLower.includes('低')) {
      return {
        bg: 'bg-blue-50 dark:bg-blue-950/20',
        border: 'border-blue-200 dark:border-blue-900/50',
        text: 'text-blue-700 dark:text-blue-400',
        badge: 'bg-blue-500',
        icon: 'ℹ️',
      };
    } else {
      return {
        bg: 'bg-yellow-50 dark:bg-yellow-950/20',
        border: 'border-yellow-200 dark:border-yellow-900/50',
        text: 'text-yellow-700 dark:text-yellow-400',
        badge: 'bg-yellow-500',
        icon: '⚠️',
      };
    }
  };

  const getRiskLevelText = (level: string) => {
    const levelLower = level?.toLowerCase() || '';
    if (levelLower.includes('high') || levelLower.includes('高')) return '高';
    if (levelLower.includes('medium') || levelLower.includes('中')) return '中等';
    if (levelLower.includes('low') || levelLower.includes('低')) return '低';
    return level || '中等';
  };

  return (
    <div className="fixed top-20 left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground flex">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="relative z-10 w-64 h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-r border-sky-200 dark:border-sky-900/30 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 dark:border-sky-900/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800 dark:text-sky-300">审查记录</h2>
            <button
              onClick={handleNewContract}
              className="p-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white transition-colors"
              title="新建审查"
            >
              <Plus size={18} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {historyLoading && (
            <div className="text-center py-4">
              <Loader2 size={20} className="mx-auto animate-spin text-sky-500" />
              <p className="text-sm text-gray-500 mt-2">加载中...</p>
            </div>
          )}
          {getSortedSessions().map((session) => (
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
                    {session.customFilename || session.filename}
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
                      handleStartEdit(session.id, session.customFilename || session.filename);
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
          {!historyLoading && sessions.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <p className="text-sm">暂无审查记录</p>
              <p className="text-xs mt-1">点击上方 + 开始新审查</p>
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
          <div className="w-full mx-auto px-4 pt-4 pb-4 h-full flex flex-col">
            <div className="text-center mb-4">
              <h1 className="text-2xl font-bold text-sky-700 dark:text-sky-300 mb-1">智能合同审查</h1>
              <p className="text-sm text-gray-700 dark:text-gray-300">精准定位高风险条款，逐句穿透法律依据</p>
              <div className="h-1 w-24 bg-gradient-to-r from-amber-500 to-orange-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="mb-4 flex flex-wrap items-center justify-center gap-2">
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

            {!currentSessionId && !file && !uploadResult && !reviewResult && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="mb-6 relative inline-block">
                    <div className="absolute inset-0 rounded-full bg-gradient-to-br from-sky-600/30 via-amber-600/30 to-red-600/30 blur-2xl animate-pulse-slow" />
                    <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 shadow-2xl border-2 border-sky-400 mx-auto">
                      <ScaleIcon size={40} className="text-white" withFire={true} />
                    </div>
                  </div>
                  <h2 className="mb-3 text-2xl font-bold text-sky-800 dark:text-sky-300">开始新的合同审查</h2>
                  <p className="mb-6 text-center text-gray-700 dark:text-gray-300 max-w-md">
                    上传合同文档，AI 将为您深度分析合同条款，识别潜在风险
                  </p>
                  <button
                    onClick={() => document.getElementById('file-input')?.click()}
                    className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-amber-600 to-orange-600 px-6 py-3 text-white font-medium shadow-lg hover:shadow-xl hover:shadow-amber-500/30 transition-all border border-sky-400/50"
                  >
                    <Upload size={20} />
                    上传合同文档
                  </button>
                  <input
                    id="file-input"
                    type="file"
                    accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
                    onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                    className="hidden"
                  />
                  <div className="mt-6">
                    <button
                      onClick={handleDemoContract}
                      className="text-sm text-sky-600 hover:text-sky-700 underline"
                    >
                      或体验示例合同审查 →
                    </button>
                  </div>
                </div>
              </div>
            )}

            {(currentSessionId || file || uploadResult || reviewResult) && (
            <div className="flex-1 flex flex-col gap-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="rounded-2xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 p-4 backdrop-blur-sm">
                  <h2 className="mb-4 flex items-center gap-2 text-xl font-semibold text-sky-700 dark:text-sky-300">
                    <Upload size={20} className="text-sky-600 dark:text-sky-400" />
                    上传合同文档
                  </h2>

                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('file-input')?.click()}
                    className={`
                      cursor-pointer rounded-2xl border-2 border-dashed p-6 text-center transition-smooth
                      ${isDragging 
                        ? 'border-sky-500 bg-sky-500/10' 
                        : 'border-sky-500/30 hover:border-sky-500/60 hover:bg-sky-500/5'
                      }
                    `}
                  >
                    <FileText size={40} className="mx-auto mb-3 text-sky-600/60 dark:text-sky-400/60" />
                    <p className="mb-2 font-medium text-sky-700 dark:text-sky-300">
                      拖拽文件到此处，或点击选择文件
                    </p>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      支持 PDF、Word、图像（JPG/PNG）
                    </p>
                    <input
                      id="file-input"
                      type="file"
                      accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
                      onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                      className="hidden"
                    />
                  </div>

                  {file && (
                    <div className="mt-4 flex items-center justify-between rounded-xl border border-sky-500/30 bg-white/60 dark:bg-gray-700/40 p-3 backdrop-blur-sm">
                      <div className="flex items-center gap-3">
                        <FileText size={18} className="text-sky-600 dark:text-sky-400" />
                        <div>
                          <p className="text-sm font-medium text-sky-700 dark:text-sky-300">{file.name}</p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {(file.size / 1024).toFixed(2)} KB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={handleUpload}
                        disabled={uploading}
                        className="rounded-lg bg-gradient-to-br from-amber-600 to-orange-600 px-4 py-2 text-sm font-medium text-white transition-all hover:shadow-xl hover:shadow-amber-500/30 disabled:cursor-not-allowed disabled:opacity-50 border border-sky-400/50"
                      >
                        {uploading ? (
                          <span className="flex items-center gap-2">
                            <Loader2 size={16} className="animate-spin" />
                            上传中...
                          </span>
                        ) : (
                          <span>开始上传</span>
                        )}
                      </button>
                    </div>
                  )}

                  {!file && !uploadResult && (
                    <div className="mt-4 border-t border-sky-500/30 pt-4">
                      <button
                        onClick={handleDemoContract}
                        className="w-full rounded-2xl border-2 border-dashed border-sky-500/30 bg-gradient-to-r from-amber-50 to-blue-100 dark:from-gray-800 dark:to-gray-700 p-4 text-left transition-all hover:border-sky-500/60 hover:shadow-2xl hover:shadow-amber-500/20"
                      >
                        <div className="flex items-center gap-3">
                          <div className="relative flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 shadow-lg border border-sky-400/50">
                            <ScaleIcon size={20} className="text-white" />
                          </div>
                          <div className="flex-1">
                            <h3 className="mb-1 font-semibold text-sky-700 dark:text-sky-300 text-sm">✨ 一键体验：审查《高风险劳动合同示例》</h3>
                            <p className="text-xs text-gray-700 dark:text-gray-300">
                              无需上传文件，立即体验 AI 合同审查功能
                            </p>
                          </div>
                        </div>
                      </button>
                    </div>
                  )}

                  {uploadResult && (
                    <div className="mt-4 rounded-xl border border-green-500/30 bg-green-50 dark:bg-green-900/20 p-3 backdrop-blur-sm">
                      <div className="flex items-start gap-3">
                        <CheckCircle size={18} className="mt-0.5 flex-shrink-0 text-green-400" />
                        <div className="flex-1">
                          <p className="mb-2 font-medium text-green-700 dark:text-green-400 text-sm">文件已成功入库</p>
                          <div className="space-y-1 text-xs text-green-600 dark:text-green-300">
                            <p>Contract ID: <span className="font-mono">{uploadResult.contract_id}</span></p>
                          </div>
                        </div>
                      </div>
                      
                      <button
                        onClick={handleReview}
                        disabled={reviewing}
                        className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-amber-600 to-orange-600 px-6 py-3 font-medium text-white shadow-2xl transition-all hover:shadow-xl hover:shadow-amber-500/30 disabled:cursor-not-allowed disabled:opacity-50 border border-sky-400/50"
                      >
                        {reviewing ? (
                          <span className="flex items-center gap-2">
                            <Loader2 size={20} className="animate-spin" />
                            AI 正在进行深度审查...
                          </span>
                        ) : (
                          <span className="flex items-center gap-2">
                            <ScaleIcon size={20} />
                            开始深度审查
                          </span>
                        )}
                      </button>
                    </div>
                  )}

                  {error && (
                    <div className="mt-4 flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-50 dark:bg-red-900/20 p-3 backdrop-blur-sm">
                      <AlertCircle size={18} className="mt-0.5 flex-shrink-0 text-red-600 dark:text-red-400" />
                      <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                    </div>
                  )}
                </div>

                <div className="rounded-2xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm overflow-hidden flex flex-col">
                  <div className="flex items-center justify-between border-b border-sky-500/30 bg-white/90 dark:bg-gray-900/90 px-4 py-2 flex-shrink-0">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1.5">
                        <div className="h-3 w-3 rounded-full bg-red-500"></div>
                        <div className="h-3 w-3 rounded-full bg-yellow-500"></div>
                        <div className="h-3 w-3 rounded-full bg-green-500"></div>
                      </div>
                      <span className="text-sm text-gray-700 dark:text-gray-200 ml-2">法惠民生 AI 分析终端</span>
                    </div>
                    {reviewing && (
                      <div className="flex items-center gap-2 text-xs text-sky-600 dark:text-sky-400">
                        <div className="h-2 w-2 rounded-full bg-sky-600 animate-pulse"></div>
                        分析中...
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1 overflow-y-auto p-4 font-mono text-sm text-gray-700 dark:text-gray-200 space-y-1">
                    {thinkingSteps.length === 0 && (
                      <div className="text-gray-500 dark:text-gray-400 italic">等待处理...</div>
                    )}
                    {thinkingSteps.map((step, index) => (
                      <div key={index} className="leading-relaxed">
                        {step}
                      </div>
                    ))}
                    {reviewing && (
                      <div className="flex items-center gap-2 text-sky-600 dark:text-sky-400">
                        <Loader2 size={14} className="animate-spin" />
                        <span className="animate-pulse">思考中...</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {(reviewResult || isDisplayingSummary || displayedRiskCount > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(reviewResult?.overall_summary || currentSummary) && (
                    <div className="rounded-2xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 p-4 backdrop-blur-sm">
                      <h2 className="mb-4 flex items-center gap-2 text-xl font-semibold text-sky-700 dark:text-sky-300">
                        <AlertTriangle size={20} className="text-sky-500" />
                        整体风险评估
                      </h2>
                      <div className="prose prose-sm dark:prose-invert max-h-[250px] max-w-none overflow-y-auto pr-2">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {isDisplayingSummary ? currentSummary : (currentSummary || reviewResult?.overall_summary)}
                        </ReactMarkdown>
                      </div>
                      <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-t border-sky-500/30 pt-4">
                        <div className="grid grid-cols-2 gap-4 w-full md:w-auto">
                          <div className="text-center">
                            <div className="mb-1 text-3xl font-bold text-red-600 dark:text-red-400">{(displayedRiskCount || reviewResult?.risks?.length || 0)}</div>
                            <div className="text-sm text-gray-700 dark:text-gray-300">风险项</div>
                          </div>
                          <div className="text-center">
                            <div className="mb-1 text-3xl font-bold text-sky-600 dark:text-sky-400">
                              {reviewResult?.is_image_based ? '图像' : '文本'}
                            </div>
                            <div className="text-sm text-gray-700 dark:text-gray-300">识别模式</div>
                          </div>
                        </div>
                        <button
                          onClick={handleFavorite}
                          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-br from-amber-600 to-orange-600 text-white rounded-lg hover:shadow-lg transition-all hover:scale-105"
                        >
                          <Star size={16} />
                          <span className="text-sm font-medium">收藏结果</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {displayedRiskCount > 0 && (
                    <div className="rounded-2xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 p-4 backdrop-blur-sm space-y-4">
                      <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold text-sky-700 dark:text-sky-300">风险详情</h2>
                        {displayedRiskCount > 0 && (
                          <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                            <span>{currentRiskIndex + 1}</span>
                            <span>/</span>
                            <span>{displayedRiskCount}</span>
                          </div>
                        )}
                      </div>
                      
                      {(() => {
                        const risks = currentRisks.length > 0 ? currentRisks : (reviewResult?.risks || []);
                        
                        const validRisks = risks.filter((risk: any) => {
                          const hasValidContent = 
                            (risk.original_clause && risk.original_clause.trim() !== '') ||
                            (risk.risk_explanation && risk.risk_explanation.trim() !== '') ||
                            (risk.revise_suggestion && risk.revise_suggestion.trim() !== '') ||
                            (risk.legal_basis && risk.legal_basis.length > 0);
                          return hasValidContent;
                        });
                        
                        const currentIndex = Math.min(currentRiskIndex, validRisks.length - 1);
                        const risk = validRisks[currentIndex];
                        
                        if (!risk) return null;
                        
                        const style = getRiskStyle(risk.risk_level);
                        
                        return (
                          <div className="relative">
                            <button
                              onClick={() => setCurrentRiskIndex(Math.max(0, currentRiskIndex - 1))}
                              disabled={currentRiskIndex <= 0}
                              className={`absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 bg-white dark:bg-gray-800 shadow-lg transition-all hover:scale-110 disabled:cursor-not-allowed disabled:opacity-30 ${style.border}`}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-sky-600 dark:text-sky-400">
                                <polyline points="15 18 9 12 15 6"></polyline>
                              </svg>
                            </button>
                            
                            <button
                              onClick={() => setCurrentRiskIndex(Math.min(validRisks.length - 1, currentRiskIndex + 1))}
                              disabled={currentRiskIndex >= validRisks.length - 1}
                              className={`absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 bg-white dark:bg-gray-800 shadow-lg transition-all hover:scale-110 disabled:cursor-not-allowed disabled:opacity-30 ${style.border}`}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-sky-600 dark:text-sky-400">
                                <polyline points="9 18 15 12 9 6"></polyline>
                              </svg>
                            </button>
                            
                            <div className={`mx-12 h-[350px] overflow-y-auto space-y-4 rounded-2xl border p-4 ${style.bg} ${style.border} backdrop-blur-sm`}>
                              <div className="flex items-center justify-between">
                                <span className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold text-white ${style.badge}`}>
                                  <span>{style.icon}</span>
                                  {getRiskLevelText(risk.risk_level)}
                                </span>
                                <div className="flex items-center gap-2">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">置信度</span>
                                  <span className={`text-lg font-bold ${style.text}`}>
                                    {risk.confidence_score ? `${Math.round(risk.confidence_score * 100)}%` : '85%'}
                                  </span>
                                </div>
                              </div>

                              {risk.original_clause && risk.original_clause.trim() !== '' && (
                                <div className="space-y-2">
                                  <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    <span className="text-lg">📜</span>
                                    原文条款
                                  </h4>
                                  <div className="rounded-xl bg-white/60 dark:bg-gray-700/40 p-3 text-sm leading-relaxed border border-sky-500/30">
                                    <p className="whitespace-pre-wrap">{risk.original_text_quote || risk.original_clause}</p>
                                  </div>
                                </div>
                              )}

                              {risk.risk_explanation && risk.risk_explanation.trim() !== '' && (
                                <div className="space-y-2">
                                  <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    <span className="text-lg">⚠️</span>
                                    风险说明
                                  </h4>
                                  <div className="rounded-xl bg-white/60 dark:bg-gray-700/40 p-3 text-sm leading-relaxed border border-sky-500/30 prose prose-sm dark:prose-invert">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                      {risk.risk_explanation}
                                    </ReactMarkdown>
                                  </div>
                                </div>
                              )}

                              {risk.legal_basis && risk.legal_basis.length > 0 && (
                                <div className="space-y-2">
                                  <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    <span className="text-lg">📚</span>
                                    法律依据
                                  </h4>
                                  <div className="space-y-2">
                                    {risk.legal_basis.filter((b: string) => b && b.trim() !== '').map((basis: string, i: number) => (
                                      <div key={i} className="rounded-xl bg-white/60 dark:bg-gray-700/40 p-3 text-sm leading-relaxed border border-sky-500/30">
                                        {risk.legal_basis_links && risk.legal_basis_links[i] ? (
                                          <a 
                                            href={risk.legal_basis_links[i]} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-2 text-sky-600 hover:text-sky-700"
                                          >
                                            {basis}
                                            <ExternalLink size={14} />
                                          </a>
                                        ) : (
                                          <p>{basis}</p>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {risk.revise_suggestion && risk.revise_suggestion.trim() !== '' && (
                                <div className="space-y-2">
                                  <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    <span className="text-lg">✏️</span>
                                    修改建议
                                  </h4>
                                  <div className="rounded-xl bg-white/60 dark:bg-gray-700/40 p-3 text-sm leading-relaxed border border-sky-500/30 prose prose-sm dark:prose-invert">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                      {risk.revise_suggestion}
                                    </ReactMarkdown>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  )}
                </div>
              )}
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
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">重命名合同</h3>
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
                placeholder="输入新的合同名称"
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

export default dynamic(() => Promise.resolve(ContractPageContent), {
  ssr: false,
});
