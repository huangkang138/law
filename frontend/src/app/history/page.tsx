'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MessageSquare, 
  FileText, 
  ScaleIcon as Scale,
  Clock,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Trash2,
  Edit,
  CheckSquare,
  Square,
  Search,
  Brain,
  FileSearch,
  FolderOpen,
  Shield,
  Route,
  TrendingUp,
  Bell,
  AlertTriangle as WarningIcon,
  Users,
  Calendar,
  Tag,
  Zap,
  Sparkles,
  ArrowRight,
  Filter,
  MoreVertical,
  Download,
  Eye,
  BarChart3,
  History,
  ChevronLeft,
  X,
  Settings,
  Star
} from 'lucide-react';
import Link from 'next/link';
import { AlertDialog, showAlert, showConfirm } from '@/components/AlertDialog';
import {
  getLegalChatHistory,
  getContractHistory,
  getDebateHistory,
  deleteLegalChatSession,
  updateLegalChatSessionTitle,
  deleteContract,
  updateContractFilename,
  deleteDebateSession,
  updateDebateSessionTitle,
  getCaseAnalysisHistory,
  getSimilarDocumentHistory,
  deleteCaseAnalysis,
  deleteSimilarDocument,
  getDisputeHistory,
  getEvidenceHistory,
  getProtectionHistory,
  getDocumentHistory,
  getPredictionHistory,
  getReminderHistory,
  getWarningHistory,
  deleteDispute,
  deleteEvidence,
  deleteProtection,
  deleteLegalDocument,
  deletePrediction,
  deleteReminder,
  deleteWarning
} from '@/lib/api';
import ScaleIcon from '@/components/ScaleIcon';
import { generateComplaintPDF } from '@/utils/pdfGenerator';
import { useChatStore } from '@/store/chatStore';
import { useDataCache } from '@/hooks/useDataCache';

interface LegalChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface ContractHistoryItem {
  id: string;
  filename: string;
  file_size: number;
  text_length: number;
  overall_summary: string;
  risk_count: number;
  risk_levels: {
    high: number;
    medium: number;
    low: number;
  };
  created_at: string;
  updated_at: string;
}

interface DebateHistoryItem {
  id: string;
  case_id: string;
  case_title: string;
  case_type: string;
  case_description: string;
  current_phase: string;
  is_active: boolean;
  verdict: string;
  debate_turn_count: number;
  created_at: string;
  updated_at: string;
}

interface CaseAnalysisHistoryItem {
  id: string;
  case_description: string;
  analysis_result: string;
  created_at: string;
  updated_at: string;
}

interface SimilarDocumentHistoryItem {
  id: string;
  document_content: string;
  search_result: string;
  created_at: string;
  updated_at: string;
}

interface DisputeHistoryItem {
  id: string;
  title: string;
  event_description: string;
  demands: string;
  created_at: string;
  updated_at: string;
}

interface EvidenceHistoryItem {
  id: string;
  evidence_name: string;
  evidence_type: string;
  is_certified: boolean;
  created_at: string;
}

interface ProtectionHistoryItem {
  id: string;
  dispute_id: string;
  success_rate: number;
  created_at: string;
}

interface DocumentHistoryItem {
  id: string;
  document_type: string;
  created_at: string;
}

interface PredictionHistoryItem {
  id: string;
  win_probability: number;
  created_at: string;
}

interface ReminderHistoryItem {
  id: string;
  reminder_type: string;
  reminder_time: string;
  created_at: string;
}

interface WarningHistoryItem {
  id: string;
  risk_summary: string;
  created_at: string;
}

type HistoryType = 'legal' | 'contract' | 'debate' | 'case-analysis' | 'similar-documents' | 'dispute' | 'evidence' | 'protection' | 'document' | 'prediction' | 'reminder' | 'warning';

export default function HistoryPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<HistoryType>('legal');
  const [legalHistory, setLegalHistory] = useState<LegalChatSession[]>([]);
  const [contractHistory, setContractHistory] = useState<ContractHistoryItem[]>([]);
  const [debateHistory, setDebateHistory] = useState<DebateHistoryItem[]>([]);
  const [caseAnalysisHistory, setCaseAnalysisHistory] = useState<CaseAnalysisHistoryItem[]>([]);
  const [similarDocumentHistory, setSimilarDocumentHistory] = useState<SimilarDocumentHistoryItem[]>([]);
  const [disputeHistory, setDisputeHistory] = useState<DisputeHistoryItem[]>([]);
  const [evidenceHistory, setEvidenceHistory] = useState<EvidenceHistoryItem[]>([]);
  const [protectionHistory, setProtectionHistory] = useState<ProtectionHistoryItem[]>([]);
  const [documentHistory, setDocumentHistory] = useState<DocumentHistoryItem[]>([]);
  const [predictionHistory, setPredictionHistory] = useState<PredictionHistoryItem[]>([]);
  const [reminderHistory, setReminderHistory] = useState<ReminderHistoryItem[]>([]);
  const [warningHistory, setWarningHistory] = useState<WarningHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  
  const { deleteSession, renameSession } = useChatStore();
  
  // 数据缓存
  const { getCachedData, setCachedData, clearCache } = useDataCache<{
    legal: LegalChatSession[];
    contract: ContractHistoryItem[];
    debate: DebateHistoryItem[];
    'case-analysis': CaseAnalysisHistoryItem[];
    'similar-documents': SimilarDocumentHistoryItem[];
    dispute: DisputeHistoryItem[];
    evidence: EvidenceHistoryItem[];
    protection: ProtectionHistoryItem[];
    document: DocumentHistoryItem[];
    prediction: PredictionHistoryItem[];
    reminder: ReminderHistoryItem[];
    warning: WarningHistoryItem[];
  }>('history-data');

  useEffect(() => {
    // 页面加载时获取所有类型的历史记录数据
    loadAllHistory();
  }, []);

  // 切换标签页时重新加载当前类型的数据，确保获取最新记录
  useEffect(() => {
    if (legalHistory.length > 0 || contractHistory.length > 0 || debateHistory.length > 0) {
      loadHistory();
    }
    setCurrentPage(1);
    setSearchTerm('');
  }, [activeTab]);

  // 加载所有类型的历史记录数据
  const loadAllHistory = async () => {
    setLoading(true);
    setError('');

    // 清除缓存，确保获取最新数据
    clearCache();

    try {
      // 并行获取所有类型的历史记录数据
      const [legalData, contractData, debateData, caseAnalysisData, similarDocumentData, disputeData, evidenceData, protectionData, documentData, predictionData, reminderData, warningData] = await Promise.all([
        getLegalChatHistory().catch(() => ({ sessions: [] })),
        getContractHistory().catch(() => ({ documents: [] })),
        getDebateHistory().catch(() => ({ history: [] })),
        getCaseAnalysisHistory().catch(() => ({ history: [] })),
        getSimilarDocumentHistory().catch(() => ({ history: [] })),
        getDisputeHistory().catch(() => ({ history: [] })),
        getEvidenceHistory().catch(() => ({ history: [] })),
        getProtectionHistory().catch(() => ({ history: [] })),
        getDocumentHistory().catch(() => ({ history: [] })),
        getPredictionHistory().catch(() => ({ history: [] })),
        getReminderHistory().catch(() => ({ history: [] })),
        getWarningHistory().catch(() => ({ history: [] }))
      ]);

      // 更新所有历史记录数据
      setLegalHistory(legalData.sessions || []);
      setContractHistory(contractData.documents || []);
      setDebateHistory(debateData.history || []);
      setCaseAnalysisHistory(caseAnalysisData.history || []);
      setSimilarDocumentHistory(similarDocumentData.history || []);
      setDisputeHistory(disputeData.history || []);
      setEvidenceHistory(evidenceData.history || []);
      setProtectionHistory(protectionData.history || []);
      setDocumentHistory(documentData.history || []);
      setPredictionHistory(predictionData.history || []);
      setReminderHistory(reminderData.history || []);
      setWarningHistory(warningData.history || []);
    } catch (err: any) {
      setError(err.message || '加载历史记录失败');
    } finally {
      setLoading(false);
      // 保存到缓存
      setCachedData({
        legal: legalHistory,
        contract: contractHistory,
        debate: debateHistory,
        'case-analysis': caseAnalysisHistory,
        'similar-documents': similarDocumentHistory,
        dispute: disputeHistory,
        evidence: evidenceHistory,
        protection: protectionHistory,
        document: documentHistory,
        prediction: predictionHistory,
        reminder: reminderHistory,
        warning: warningHistory,
      });
    }
  };

  // 加载当前类型的历史记录数据
  const loadHistory = async () => {
    setLoading(true);
    setError('');
    setSelectedItems([]);
    setEditingItem(null);
    setCurrentPage(1);

    try {
      switch (activeTab) {
        case 'legal':
          const legalData = await getLegalChatHistory();
          setLegalHistory(legalData.sessions || []);
          break;
        case 'contract':
          const contractData = await getContractHistory();
          setContractHistory(contractData.documents || []);
          break;
        case 'debate':
          const debateData = await getDebateHistory();
          setDebateHistory(debateData.history || []);
          break;
        case 'case-analysis':
          const caseAnalysisData = await getCaseAnalysisHistory();
          setCaseAnalysisHistory(caseAnalysisData.history || []);
          break;
        case 'similar-documents':
          const similarDocumentData = await getSimilarDocumentHistory();
          setSimilarDocumentHistory(similarDocumentData.history || []);
          break;
        case 'dispute':
          const disputeData = await getDisputeHistory();
          setDisputeHistory(disputeData.history || []);
          break;
        case 'evidence':
          const evidenceData = await getEvidenceHistory();
          setEvidenceHistory(evidenceData.history || []);
          break;
        case 'protection':
          const protectionData = await getProtectionHistory();
          setProtectionHistory(protectionData.history || []);
          break;
        case 'document':
          const documentData = await getDocumentHistory();
          setDocumentHistory(documentData.history || []);
          break;
        case 'prediction':
          const predictionData = await getPredictionHistory();
          setPredictionHistory(predictionData.history || []);
          break;
        case 'reminder':
          const reminderData = await getReminderHistory();
          setReminderHistory(reminderData.history || []);
          break;
        case 'warning':
          const warningData = await getWarningHistory();
          setWarningHistory(warningData.history || []);
          break;
      }
    } catch (err: any) {
      setError(err.message || '加载历史记录失败');
    } finally {
      setLoading(false);
      // 保存到缓存
      setCachedData({
        legal: legalHistory,
        contract: contractHistory,
        debate: debateHistory,
        'case-analysis': caseAnalysisHistory,
        'similar-documents': similarDocumentHistory,
        dispute: disputeHistory,
        evidence: evidenceHistory,
        protection: protectionHistory,
        document: documentHistory,
        prediction: predictionHistory,
        reminder: reminderHistory,
        warning: warningHistory,
      });
    }
  };

  const handleSelectItem = (id: string) => {
    setSelectedItems(prev => {
      if (prev.includes(id)) {
        return prev.filter(item => item !== id);
      } else {
        return [...prev, id];
      }
    });
  };

  const handleSelectAll = () => {
    const currentHistory = 
      activeTab === 'legal' ? legalHistory :
      activeTab === 'contract' ? contractHistory :
      activeTab === 'debate' ? debateHistory :
      activeTab === 'case-analysis' ? caseAnalysisHistory :
      activeTab === 'similar-documents' ? similarDocumentHistory :
      activeTab === 'dispute' ? disputeHistory :
      activeTab === 'evidence' ? evidenceHistory :
      activeTab === 'protection' ? protectionHistory :
      activeTab === 'document' ? documentHistory :
      activeTab === 'prediction' ? predictionHistory :
      activeTab === 'reminder' ? reminderHistory :
      warningHistory;

    if (currentHistory.length > 0) {
      if (selectedItems.length === currentHistory.length) {
        setSelectedItems([]);
      } else {
        setSelectedItems(currentHistory.map((item: any) => item.id));
      }
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedItems.length > 0) {
      const confirmed = await showConfirm(`确定要删除选中的 ${selectedItems.length} 条记录吗？`, '确认删除');
      if (confirmed) {
        try {
          for (const id of selectedItems) {
            if (activeTab === 'legal') {
              await deleteLegalChatSession(id);
            } else if (activeTab === 'contract') {
              await deleteContract(id);
            } else if (activeTab === 'debate') {
              await deleteDebateSession(id);
            } else if (activeTab === 'case-analysis') {
              await deleteCaseAnalysis(id);
            } else if (activeTab === 'similar-documents') {
              await deleteSimilarDocument(id);
            } else if (activeTab === 'dispute') {
              await deleteDispute(id);
            } else if (activeTab === 'evidence') {
              await deleteEvidence(id);
            } else if (activeTab === 'protection') {
              await deleteProtection(id);
            } else if (activeTab === 'document') {
              await deleteLegalDocument(id);
            } else if (activeTab === 'prediction') {
              await deletePrediction(id);
            } else if (activeTab === 'reminder') {
              await deleteReminder(id);
            } else if (activeTab === 'warning') {
              await deleteWarning(id);
            }
          }
          setSelectedItems([]);
          loadHistory();
        } catch (error: any) {
          await showAlert('删除失败: ' + error.message, 'error');
        }
      }
    }
  };

  const handleDeleteItem = async (id: string) => {
    const confirmed = await showConfirm('确定要删除这条记录吗？', '确认删除');
    if (confirmed) {
      try {
        if (activeTab === 'legal') {
          await deleteLegalChatSession(id);
        } else if (activeTab === 'contract') {
          await deleteContract(id);
        } else if (activeTab === 'debate') {
          await deleteDebateSession(id);
        } else if (activeTab === 'case-analysis') {
          await deleteCaseAnalysis(id);
        } else if (activeTab === 'similar-documents') {
          await deleteSimilarDocument(id);
        } else if (activeTab === 'dispute') {
          await deleteDispute(id);
        } else if (activeTab === 'evidence') {
          await deleteEvidence(id);
        } else if (activeTab === 'protection') {
          await deleteProtection(id);
        } else if (activeTab === 'document') {
          await deleteLegalDocument(id);
        } else if (activeTab === 'prediction') {
          await deletePrediction(id);
        } else if (activeTab === 'reminder') {
          await deleteReminder(id);
        } else if (activeTab === 'warning') {
          await deleteWarning(id);
        }
        loadHistory();
      } catch (error: any) {
        await showAlert('删除失败: ' + error.message, 'error');
      }
    }
  };

  const handleStartEdit = (id: string, title: string) => {
    setEditingItem(id);
    setEditTitle(title);
  };

  const handleSaveEdit = async (id: string) => {
    if (editTitle.trim()) {
      try {
        if (activeTab === 'legal') {
          await updateLegalChatSessionTitle(id, editTitle.trim());
        } else if (activeTab === 'contract') {
          await updateContractFilename(id, editTitle.trim());
        } else if (activeTab === 'debate') {
          await updateDebateSessionTitle(id, editTitle.trim());
        }
        setEditingItem(null);
        setEditTitle('');
        loadHistory();
      } catch (error: any) {
        await showAlert('更新失败: ' + error.message, 'error');
      }
    }
  };

  const handleViewItem = (item: any) => {
    switch (activeTab) {
      case 'legal':
        router.push(`/chat?session=${item.id}`);
        break;
      case 'contract':
        router.push(`/contract?id=${item.id}`);
        break;
      case 'debate':
        router.push(`/debate?session=${item.id}`);
        break;
      case 'case-analysis':
        router.push(`/case-analysis?id=${item.id}`);
        break;
      case 'similar-documents':
        router.push(`/similar-documents?id=${item.id}`);
        break;
      case 'dispute':
        router.push(`/dispute-organize?id=${item.id}`);
        break;
      case 'evidence':
        router.push(`/dispute-center`);
        break;
      case 'protection':
        router.push(`/dispute-center`);
        break;
      case 'document':
        router.push(`/contract?id=${item.id}`);
        break;
      case 'prediction':
        router.push(`/case-analysis?id=${item.id}`);
        break;
      case 'reminder':
        router.push(`/dispute-center`);
        break;
      case 'warning':
        router.push(`/dispute-center`);
        break;
    }
  };

  const handleGenerateDebatePDF = async (debate: DebateHistoryItem) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/api/debate/${debate.id}/full-details`);
      
      if (!response.ok) {
        throw new Error('获取庭审详情失败');
      }

      const data = await response.json();
      
      const caseInfo = {
        case_title: debate.case_title,
        case_description: debate.case_description,
        case_type: debate.case_type,
        debate_turns: data.debate_turns || [],
        verdict: data.session?.verdict || debate.verdict
      };
      
      await generateComplaintPDF(caseInfo);
    } catch (error: any) {
      await showAlert('生成PDF失败: ' + error.message, 'error');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const oneDay = 24 * 60 * 60 * 1000;

    if (diff < oneDay) {
      return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (diff < 2 * oneDay) {
      return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (diff < 7 * oneDay) {
      return `${Math.floor(diff / oneDay)} 天前`;
    } else {
      return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' });
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const getTodayCount = (items: any[]) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return items.filter(item => {
      const itemDate = new Date(item.created_at);
      return itemDate >= today;
    }).length;
  };

  const getMonthCount = (items: any[]) => {
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    return items.filter(item => new Date(item.created_at) >= monthAgo).length;
  };

  const getFilteredItems = () => {
    let items: any[] = [];
    
    switch (activeTab) {
      case 'legal':
        items = legalHistory;
        break;
      case 'contract':
        items = contractHistory;
        break;
      case 'debate':
        items = debateHistory;
        break;
      case 'case-analysis':
        items = caseAnalysisHistory;
        break;
      case 'similar-documents':
        items = similarDocumentHistory;
        break;
      case 'dispute':
        items = disputeHistory;
        break;
      case 'evidence':
        items = evidenceHistory;
        break;
      case 'protection':
        items = protectionHistory;
        break;
      case 'document':
        items = documentHistory;
        break;
      case 'prediction':
        items = predictionHistory;
        break;
      case 'reminder':
        items = reminderHistory;
        break;
      case 'warning':
        items = warningHistory;
        break;
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      items = items.filter(item => {
        if (activeTab === 'legal') {
          return item.title.toLowerCase().includes(term);
        } else if (activeTab === 'contract') {
          return item.filename.toLowerCase().includes(term) || 
                 item.overall_summary.toLowerCase().includes(term);
        } else if (activeTab === 'debate') {
          return item.case_title.toLowerCase().includes(term) || 
                 item.case_description.toLowerCase().includes(term);
        } else if (activeTab === 'case-analysis') {
          return item.case_description.toLowerCase().includes(term) || 
                 item.analysis_result.toLowerCase().includes(term);
        } else if (activeTab === 'similar-documents') {
          return item.document_content.toLowerCase().includes(term) || 
                 item.search_result.toLowerCase().includes(term);
        } else if (activeTab === 'dispute') {
          return item.title.toLowerCase().includes(term) || 
                 item.event_description.toLowerCase().includes(term);
        } else if (activeTab === 'evidence') {
          return item.evidence_name.toLowerCase().includes(term);
        } else if (activeTab === 'protection') {
          return true;
        } else if (activeTab === 'document') {
          return item.document_type.toLowerCase().includes(term);
        } else if (activeTab === 'prediction') {
          return true;
        } else if (activeTab === 'reminder') {
          return item.reminder_type.toLowerCase().includes(term);
        } else if (activeTab === 'warning') {
          return item.risk_summary.toLowerCase().includes(term);
        }
        return false;
      });
    }

    return items;
  };

  const sidebarTabs = [
    { id: 'legal' as HistoryType, name: '普法问答', icon: MessageSquare },
    { id: 'contract' as HistoryType, name: '合同审查', icon: FileText },
    { id: 'debate' as HistoryType, name: '模拟法庭', icon: Scale },
    { id: 'case-analysis' as HistoryType, name: '案情推断', icon: Brain },
    { id: 'similar-documents' as HistoryType, name: '相似文书', icon: FileSearch },
    { id: 'dispute' as HistoryType, name: '纠纷整理', icon: FolderOpen },
    { id: 'evidence' as HistoryType, name: '取证存证', icon: Shield },
    { id: 'protection' as HistoryType, name: '维权路径', icon: Route },
    { id: 'document' as HistoryType, name: '文书生成', icon: FileText },
    { id: 'prediction' as HistoryType, name: '案件预判', icon: TrendingUp },
    { id: 'reminder' as HistoryType, name: '流程提醒', icon: Bell },
    { id: 'warning' as HistoryType, name: '避坑提醒', icon: WarningIcon },
  ];

  const getCurrentHistory = () => {
    switch (activeTab) {
      case 'legal': return legalHistory;
      case 'contract': return contractHistory;
      case 'debate': return debateHistory;
      case 'case-analysis': return caseAnalysisHistory;
      case 'similar-documents': return similarDocumentHistory;
      case 'dispute': return disputeHistory;
      case 'evidence': return evidenceHistory;
      case 'protection': return protectionHistory;
      case 'document': return documentHistory;
      case 'prediction': return predictionHistory;
      case 'reminder': return reminderHistory;
      case 'warning': return warningHistory;
    }
  };

  const filteredItems = getFilteredItems();
  const currentHistory = getCurrentHistory();
  const totalCount = currentHistory.length;
  const todayCount = getTodayCount(currentHistory);
  const monthCount = getMonthCount(currentHistory);

  // 分页逻辑
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedItems = filteredItems.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    setSelectedItems([]);
  };

  const activeTabObj = sidebarTabs.find(t => t.id === activeTab);
  const ActiveIcon = activeTabObj?.icon;

  return (
    <div className="bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground relative overflow-hidden">
      {/* 星空光晕效果 */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      {/* 主内容区域 */}
      <div className="flex h-[calc(100dvh_-_var(--business-page-top))] gap-4">
        {/* 左侧侧边栏 - 固定 */}
        <div className={`${sidebarOpen ? 'w-80' : 'w-20'} flex-shrink-0 transition-all duration-300 h-full`}>
          <div className="h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-xl border border-sky-300 dark:border-sky-700 shadow-lg overflow-hidden flex flex-col">
            {/* 侧边栏头部 */}
            <div className="p-5 border-b border-sky-200 dark:border-sky-900/30">
              <div className="flex items-center gap-4">
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-500 flex-shrink-0">
                  <History size={24} className="text-white" />
                </div>
                {sidebarOpen && (
                  <div>
                    <h1 className="text-xl font-bold text-sky-800 dark:text-sky-300">历史记录</h1>
                    <p className="text-sm text-sky-600 dark:text-sky-400">查看所有操作记录</p>
                  </div>
                )}
              </div>
            </div>

            {/* 侧边栏菜单 */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
              {sidebarTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                const count = (() => {
                  switch (tab.id) {
                    case 'legal': return legalHistory.length;
                    case 'contract': return contractHistory.length;
                    case 'debate': return debateHistory.length;
                    case 'case-analysis': return caseAnalysisHistory.length;
                    case 'similar-documents': return similarDocumentHistory.length;
                    case 'dispute': return disputeHistory.length;
                    case 'evidence': return evidenceHistory.length;
                    case 'protection': return protectionHistory.length;
                    case 'document': return documentHistory.length;
                    case 'prediction': return predictionHistory.length;
                    case 'reminder': return reminderHistory.length;
                    case 'warning': return warningHistory.length;
                  }
                })();

                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-r from-sky-500 to-indigo-500 text-white shadow-md'
                        : 'text-sky-700 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30'
                    }`}
                  >
                    <Icon size={20} className="flex-shrink-0" />
                    {sidebarOpen && (
                      <>
                        <span className="text-sm font-medium flex-1 text-left">{tab.name}</span>
                        {count > 0 && (
                          <span className={`text-xs px-2.5 py-1 rounded-full ${
                            isActive ? 'bg-white/20' : 'bg-sky-200 dark:bg-sky-800 text-sky-800 dark:text-sky-200'
                          }`}>
                            {count}
                          </span>
                        )}
                      </>
                    )}
                  </button>
                );
              })}
            </div>

            {/* 设置按钮 */}
            <div className="p-3 border-t border-sky-200 dark:border-sky-900/30">
              <Link
                href="/settings"
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-sky-700 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30"
              >
                <Settings size={20} className="flex-shrink-0" />
                {sidebarOpen && <span className="text-sm font-medium flex-1 text-left">设置</span>}
              </Link>
            </div>

            {/* 收起/展开按钮 */}
            <div className="p-3 border-t border-sky-200 dark:border-sky-900/30">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sky-600 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30 rounded-xl transition-colors"
              >
                {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
                {sidebarOpen && <span className="text-sm">收起侧边栏</span>}
              </button>
            </div>
          </div>
        </div>

        {/* 右侧内容区 - 可滚动 */}
        <div className="flex-1 min-w-0 overflow-y-auto">
          <div className="p-8">
            {/* 页面标题和统计 */}
            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-6 mb-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-500 shadow-lg">
                    {ActiveIcon && <ActiveIcon size={28} className="text-white" />}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-sky-800 dark:text-sky-300">{activeTabObj?.name}</h2>
                    <p className="text-sm text-sky-600 dark:text-sky-400 mt-1">查看和管理您的{activeTabObj?.name}记录</p>
                  </div>
                </div>
                <Link
                  href="/favorites"
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg hover:shadow-lg transition-all hover:scale-105"
                >
                  <Star size={18} />
                  <span className="text-sm font-medium">我的收藏</span>
                </Link>
              </div>

              {/* 统计卡片 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-sky-50 to-blue-100 dark:from-sky-900/20 dark:to-blue-800/20 rounded-xl p-4 border border-sky-200 dark:border-sky-800">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-sky-500/20 flex items-center justify-center">
                      <BarChart3 size={20} className="text-sky-600 dark:text-sky-400" />
                    </div>
                    <div>
                      <p className="text-sm text-sky-600 dark:text-sky-400">总记录数</p>
                      <p className="text-2xl font-bold text-sky-800 dark:text-sky-300">{totalCount}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-sky-50 to-indigo-100 dark:from-sky-900/20 dark:to-indigo-800/20 rounded-xl p-4 border border-red-200 dark:border-red-800">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                      <Calendar size={20} className="text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                      <p className="text-sm text-red-600 dark:text-red-400">今日新增</p>
                      <p className="text-2xl font-bold text-red-800 dark:text-red-300">{todayCount}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-blue-100 dark:from-orange-900/20 dark:to-blue-800/20 rounded-xl p-4 border border-orange-200 dark:border-orange-800">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
                      <Clock size={20} className="text-orange-600 dark:text-orange-400" />
                    </div>
                    <div>
                      <p className="text-sm text-orange-600 dark:text-orange-400">本月记录</p>
                      <p className="text-2xl font-bold text-orange-800 dark:text-orange-300">{monthCount}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 搜索和操作栏 */}
            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-4 mb-6">
              <div className="flex items-center gap-3">
                <div className="relative w-64">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-sky-400" />
                  <input
                    type="text"
                    placeholder="搜索记录..."
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full pl-9 pr-3 py-2 bg-sky-50 dark:bg-gray-800 border border-sky-300 dark:border-sky-700 rounded-lg text-sm text-sky-800 dark:text-sky-200 placeholder-amber-400 focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
                {searchTerm && (
                  <button
                    onClick={() => {
                      setSearchTerm('');
                      setCurrentPage(1);
                    }}
                    className="px-3 py-2 text-sm text-sky-600 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30 rounded-lg transition-colors"
                  >
                    清除
                  </button>
                )}
                {selectedItems.length > 0 && (
                  <button
                    onClick={handleDeleteSelected}
                    className="flex items-center gap-1.5 px-3 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                  >
                    <Trash2 size={14} />
                    <span>删除({selectedItems.length})</span>
                  </button>
                )}
              </div>
            </div>

            {/* 记录列表 */}
            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg overflow-hidden">
              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="animate-spin text-sky-500" size={40} />
                </div>
              ) : error ? (
                <div className="p-8 text-center">
                  <AlertTriangle size={48} className="text-red-500 mx-auto mb-4" />
                  <p className="text-red-600 dark:text-red-400">{error}</p>
                </div>
              ) : filteredItems.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="w-20 h-20 rounded-full bg-sky-100 dark:bg-sky-900/30 flex items-center justify-center mx-auto mb-4">
                    <FolderOpen size={40} className="text-sky-500" />
                  </div>
                  <p className="text-sky-800 dark:text-sky-300 text-lg mb-2">暂无记录</p>
                  <p className="text-sky-600 dark:text-sky-400">开始使用相关功能后，记录将显示在这里</p>
                </div>
              ) : (
                <>
                  {/* 列表头部 */}
                  <div className="px-4 py-3 border-b border-sky-200 dark:border-sky-900/30 bg-sky-50/50 dark:bg-sky-900/20 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <button
                        onClick={() => {
                          const pageItems = paginatedItems.map((i: any) => i.id);
                          const allSelected = pageItems.every((id: string) => selectedItems.includes(id));
                          if (allSelected) {
                            setSelectedItems(prev => prev.filter(id => !pageItems.includes(id)));
                          } else {
                            setSelectedItems(prev => {
                              const combined = [...prev, ...pageItems];
                              const unique = combined.filter((item, index) => combined.indexOf(item) === index);
                              return unique;
                            });
                          }
                        }}
                        className="flex items-center gap-2 text-sky-700 dark:text-sky-400 hover:text-sky-900 dark:hover:text-sky-200 transition-colors"
                      >
                        {paginatedItems.every((item: any) => selectedItems.includes(item.id)) ? (
                          <CheckSquare size={18} />
                        ) : (
                          <Square size={18} />
                        )}
                        <span className="text-sm">
                          {paginatedItems.every((item: any) => selectedItems.includes(item.id)) ? '取消全选' : '全选本页'}
                        </span>
                      </button>
                      <span className="text-sm text-sky-500">
                        共 {filteredItems.length} 条记录
                        {totalPages > 1 && `，第 ${currentPage}/${totalPages} 页`}
                      </span>
                    </div>
                    {totalPages > 1 && (
                      <span className="text-xs text-sky-400">
                        显示 {startIndex + 1}-{Math.min(endIndex, filteredItems.length)} 条
                      </span>
                    )}
                  </div>

                  {/* 列表内容 */}
                  <div className="divide-y divide-amber-200 dark:divide-amber-900/30">
                    {paginatedItems.map((item: any) => (
                      <div
                        key={item.id}
                        className="px-4 py-3 hover:bg-sky-50/50 dark:hover:bg-sky-900/20 transition-colors group"
                      >
                        <div className="flex items-center gap-4">
                          <button
                            onClick={() => handleSelectItem(item.id)}
                            className="flex-shrink-0"
                          >
                            {selectedItems.includes(item.id) ? (
                              <CheckSquare size={18} className="text-sky-600" />
                            ) : (
                              <Square size={18} className="text-sky-400" />
                            )}
                          </button>

                          <div className="flex-1 min-w-0 flex items-center gap-3">
                            {editingItem === item.id ? (
                              <div className="flex items-center gap-2 flex-1">
                                <input
                                  type="text"
                                  value={editTitle}
                                  onChange={(e) => setEditTitle(e.target.value)}
                                  onKeyPress={(e) => e.key === 'Enter' && handleSaveEdit(item.id)}
                                  className="flex-1 px-3 py-1.5 bg-white dark:bg-gray-800 border border-sky-300 dark:border-sky-700 rounded-lg text-sm text-sky-800 dark:text-sky-200 focus:outline-none focus:ring-2 focus:ring-red-500"
                                  autoFocus
                                />
                                <button
                                  onClick={() => handleSaveEdit(item.id)}
                                  className="p-1.5 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                                >
                                  <CheckCircle size={14} />
                                </button>
                                <button
                                  onClick={() => {
                                    setEditingItem(null);
                                    setEditTitle('');
                                  }}
                                  className="p-1.5 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                                >
                                  <X size={14} />
                                </button>
                              </div>
                            ) : (
                              <>
                                <h3 className="text-sm font-medium text-sky-800 dark:text-sky-300 truncate max-w-xs">
                                  {activeTab === 'legal' && item.title}
                                  {activeTab === 'contract' && item.filename}
                                  {activeTab === 'debate' && item.case_title}
                                  {activeTab === 'case-analysis' && item.case_description?.substring(0, 30) + '...'}
                                  {activeTab === 'similar-documents' && item.document_content?.substring(0, 30) + '...'}
                                  {activeTab === 'dispute' && item.title}
                                  {activeTab === 'evidence' && item.evidence_name}
                                  {activeTab === 'protection' && `维权路径 - ${item.id}`}
                                  {activeTab === 'document' && item.document_type}
                                  {activeTab === 'prediction' && `案件预判 - ${item.id}`}
                                  {activeTab === 'reminder' && item.reminder_type}
                                  {activeTab === 'warning' && item.risk_summary?.substring(0, 30) + '...'}
                                </h3>

                                {activeTab === 'contract' && item.risk_levels && (
                                  <div className="flex-shrink-0">
                                    {item.risk_levels.high > 0 ? (
                                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs rounded-full">
                                        <AlertTriangle size={10} />
                                        高风险
                                      </span>
                                    ) : item.risk_levels.medium > 0 ? (
                                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 text-xs rounded-full">
                                        <AlertTriangle size={10} />
                                        中风险
                                      </span>
                                    ) : (
                                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
                                        <CheckCircle size={10} />
                                        低风险
                                      </span>
                                    )}
                                  </div>
                                )}

                                <span className="text-xs text-sky-500 truncate flex-1">
                                  {activeTab === 'legal' && `${item.message_count} 条消息`}
                                  {activeTab === 'contract' && `${formatFileSize(item.file_size)} · ${item.overall_summary?.substring(0, 40)}...`}
                                  {activeTab === 'debate' && `${item.case_type} · ${item.debate_turn_count} 轮辩论`}
                                  {activeTab === 'case-analysis' && item.analysis_result?.substring(0, 40) + '...'}
                                  {activeTab === 'similar-documents' && item.search_result?.substring(0, 40) + '...'}
                                  {activeTab === 'dispute' && item.event_description?.substring(0, 40) + '...'}
                                  {activeTab === 'evidence' && `${item.evidence_type} · ${item.is_certified ? '已认证' : '未认证'}`}
                                  {activeTab === 'protection' && `成功率: ${item.success_rate}%`}
                                  {activeTab === 'document' && `文书类型: ${item.document_type}`}
                                  {activeTab === 'prediction' && `胜诉概率: ${item.win_probability}%`}
                                  {activeTab === 'reminder' && `提醒时间: ${new Date(item.reminder_time).toLocaleString('zh-CN')}`}
                                  {activeTab === 'warning' && item.risk_summary?.substring(0, 40) + '...'}
                                </span>

                                <div className="flex items-center gap-1 text-xs text-sky-400 flex-shrink-0">
                                  <Clock size={12} />
                                  <span>{formatDate(item.created_at)}</span>
                                </div>
                              </>
                            )}
                          </div>

                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                            <button
                              onClick={() => handleViewItem(item)}
                              className="p-1.5 text-sky-600 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30 rounded-lg transition-colors"
                              title="查看详情"
                            >
                              <Eye size={14} />
                            </button>
                            {activeTab === 'debate' && (
                              <button
                                onClick={() => handleGenerateDebatePDF(item)}
                                className="p-1.5 text-purple-600 dark:text-purple-400 hover:bg-purple-100 dark:hover:bg-purple-900/30 rounded-lg transition-colors"
                                title="导出PDF"
                              >
                                <Download size={14} />
                              </button>
                            )}
                            <button
                              onClick={() => handleStartEdit(item.id, activeTab === 'legal' ? item.title : activeTab === 'contract' ? item.filename : activeTab === 'debate' ? item.case_title : '')}
                              className="p-1.5 text-sky-600 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30 rounded-lg transition-colors"
                              title="编辑"
                            >
                              <Edit size={14} />
                            </button>
                            <button
                              onClick={() => handleDeleteItem(item.id)}
                              className="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                              title="删除"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 分页控件 */}
                  {totalPages > 1 && (
                    <div className="px-4 py-4 border-t border-sky-200 dark:border-sky-900/30 bg-sky-50/30 dark:bg-sky-900/10 flex items-center justify-center gap-2">
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="px-3 py-1.5 text-sm rounded-lg border border-sky-300 dark:border-sky-700 text-sky-700 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        上一页
                      </button>

                      <div className="flex items-center gap-1">
                        {Array.from({ length: totalPages }, (_, i) => i + 1)
                          .filter(page => {
                            if (totalPages <= 7) return true;
                            if (page === 1 || page === totalPages) return true;
                            if (page >= currentPage - 1 && page <= currentPage + 1) return true;
                            return false;
                          })
                          .map((page, index, arr) => (
                            <div key={page} className="flex items-center">
                              {index > 0 && arr[index - 1] !== page - 1 && (
                                <span className="px-2 text-sky-400">...</span>
                              )}
                              <button
                                onClick={() => handlePageChange(page)}
                                className={`min-w-[32px] px-3 py-1.5 text-sm rounded-lg transition-colors ${
                                  currentPage === page
                                    ? 'bg-gradient-to-r from-sky-500 to-indigo-500 text-white'
                                    : 'border border-sky-300 dark:border-sky-700 text-sky-700 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30'
                                }`}
                              >
                                {page}
                              </button>
                            </div>
                          ))}
                      </div>

                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className="px-3 py-1.5 text-sm rounded-lg border border-sky-300 dark:border-sky-700 text-sky-700 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        下一页
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
