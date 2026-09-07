'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { 
  FileText, ArrowRight, Loader2, Mic, Camera, Type,
  Shield, Route, FileCheck, TrendingUp, Bell, AlertTriangle,
  CheckCircle, ChevronRight, Plus, Trash2, Pin, Check,
  Edit, MoreHorizontal, Settings, ChevronLeft
} from 'lucide-react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useDisputeCenterStore } from '@/store/disputeCenterStore';

const STEPS = [
  { id: 'organize', name: '纠纷整理', icon: FileText, description: '整理纠纷信息' },
  { id: 'evidence', name: '取证存证', icon: Shield, description: '收集和存证证据' },
  { id: 'protection', name: '维权路径', icon: Route, description: '规划维权路径' },
  { id: 'document', name: '文书生成', icon: FileCheck, description: '生成法律文书' },
  { id: 'prediction', name: '案件预判', icon: TrendingUp, description: '分析胜诉概率' },
  { id: 'reminder', name: '流程提醒', icon: Bell, description: '设置时间提醒' },
  { id: 'warning', name: '避坑提醒', icon: AlertTriangle, description: '总结风险教训' },
];

function DisputeCenterPageContent() {
  const searchParams = useSearchParams();
  const { currentSessionId, sessions, createSession, deleteSession, renameSession, togglePin, setCurrentSession, updateSessionData, getSortedSessions } = useDisputeCenterStore();
  const [currentStep, setCurrentStep] = useState(0);
  const [disputeId, setDisputeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeStepResult, setActiveStepResult] = useState<number | null>(null);
  
  // 各步骤的数据状态
  const [inputContent, setInputContent] = useState('');
  const [organizedData, setOrganizedData] = useState<any>(null);
  const [evidenceData, setEvidenceData] = useState<any>(null);
  const [protectionData, setProtectionData] = useState<any>(null);
  const [documentData, setDocumentData] = useState<any>(null);
  const [predictionData, setPredictionData] = useState<any>(null);
  const [reminderData, setReminderData] = useState<any>(null);
  const [warningData, setWarningData] = useState<any>(null);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // 取证存证表单
  const [evidenceName, setEvidenceName] = useState('');
  const [evidenceType, setEvidenceType] = useState('');
  const [evidenceContent, setEvidenceContent] = useState('');

  // 文书生成
  const [documentType, setDocumentType] = useState('起诉状');

  useEffect(() => {
    // 检查 URL 中是否有 id 参数
    const idParam = searchParams.get('id');
    if (idParam) {
      // 查找对应的会话
      const session = sessions.find(s => s.id === idParam);
      if (session) {
        setCurrentSession(idParam);
        // 直接设置会话数据
        setCurrentStep(session.currentStep || 0);
        setOrganizedData(session.organizedData);
        setEvidenceData(session.evidenceData);
        setProtectionData(session.protectionData);
        setDocumentData(session.documentData);
        setPredictionData(session.predictionData);
        setReminderData(session.reminderData);
        setWarningData(session.warningData);
        setDisputeId(session.disputeId || null);
      } else {
        // 如果没有找到对应的会话，创建一个新会话
        resetAllData();
        createSession('新纠纷');
      }
    } else if (currentSessionId) {
      const currentSession = sessions.find(s => s.id === currentSessionId);
      if (currentSession) {
        setCurrentStep(currentSession.currentStep || 0);
        setOrganizedData(currentSession.organizedData);
        setEvidenceData(currentSession.evidenceData);
        setProtectionData(currentSession.protectionData);
        setDocumentData(currentSession.documentData);
        setPredictionData(currentSession.predictionData);
        setReminderData(currentSession.reminderData);
        setWarningData(currentSession.warningData);
        setDisputeId(currentSession.disputeId || null);
      }
    } else {
      resetAllData();
      // 自动创建新会话
      createSession('新纠纷');
    }
  }, [currentSessionId, sessions, createSession, setCurrentSession, searchParams]);

  const resetAllData = () => {
    setCurrentStep(0);
    setDisputeId(null);
    setInputContent('');
    setOrganizedData(null);
    setEvidenceData(null);
    setProtectionData(null);
    setDocumentData(null);
    setPredictionData(null);
    setReminderData(null);
    setWarningData(null);
    setError(null);
    setEvidenceName('');
    setEvidenceType('');
    setEvidenceContent('');
  };

  // 步骤1: 纠纷整理
  const handleOrganize = async () => {
    if (!inputContent.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/dispute/organize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_content: inputContent, input_type: 'text' }),
      });
      const data = await response.json();
      if (data.success) {
        setOrganizedData(data.organized_data);
        setDisputeId(data.dispute_id);
        setCurrentStep(1);
        const sessionId = currentSessionId || createSession(inputContent.substring(0, 30) + '...', data.dispute_id);
        updateSessionData(sessionId, { organizedData: data.organized_data, currentStep: 1, disputeId: data.dispute_id });
      } else {
        setError(data.error || '整理失败');
      }
    } catch (err) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 步骤2: 取证存证
  const handleCollectEvidence = async () => {
    if (!evidenceName.trim() || !disputeId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/evidence/collect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          dispute_id: disputeId,
          evidence_name: evidenceName,
          evidence_type: evidenceType,
          evidence_content: evidenceContent
        }),
      });
      const data = await response.json();
      if (data.success) {
        setEvidenceData(data);
        setCurrentStep(2);
        if (currentSessionId) {
          updateSessionData(currentSessionId, { evidenceData: data, currentStep: 2 });
        }
      } else {
        setError(data.error || '取证失败');
      }
    } catch (err) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 步骤3: 维权路径规划
  const handlePlanProtection = async () => {
    if (!disputeId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/protection/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dispute_id: disputeId }),
      });
      const data = await response.json();
      if (data.success) {
        setProtectionData(data.plan_data);
        setCurrentStep(3);
        if (currentSessionId) {
          updateSessionData(currentSessionId, { protectionData: data.plan_data, currentStep: 3 });
        }
      } else {
        setError(data.error || '规划失败');
      }
    } catch (err) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 步骤4: 文书生成
  const handleGenerateDocument = async () => {
    if (!disputeId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/document/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          dispute_id: disputeId,
          document_type: documentType
        }),
      });
      const data = await response.json();
      if (data.success) {
        setDocumentData(data);
        setCurrentStep(4);
        if (currentSessionId) {
          updateSessionData(currentSessionId, { documentData: data, currentStep: 4 });
        }
      } else {
        setError(data.error || '生成失败');
      }
    } catch (err) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 步骤5: 案件预判
  const handleAnalyzePrediction = async () => {
    if (!disputeId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/prediction/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dispute_id: disputeId }),
      });
      const data = await response.json();
      if (data.success) {
        setPredictionData(data.prediction_data);
        setCurrentStep(5);
        if (currentSessionId) {
          updateSessionData(currentSessionId, { predictionData: data.prediction_data, currentStep: 5 });
        }
      } else {
        setError(data.error || '分析失败');
      }
    } catch (err) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 步骤6: 流程提醒
  const handleCreateReminder = async () => {
    if (!disputeId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/reminder/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dispute_id: disputeId }),
      });
      const data = await response.json();
      if (data.success) {
        setReminderData(data.reminders);
        setCurrentStep(6);
        if (currentSessionId) {
          updateSessionData(currentSessionId, { reminderData: data.reminders, currentStep: 6 });
        }
      } else {
        setError(data.error || '创建失败');
      }
    } catch (err) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 步骤7: 避坑提醒
  const handleAnalyzeWarning = async () => {
    if (!disputeId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/warning/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dispute_id: disputeId }),
      });
      const data = await response.json();
      if (data.success) {
        setWarningData(data.warning_data);
        if (currentSessionId) {
          updateSessionData(currentSessionId, { warningData: data.warning_data });
        }
      } else {
        setError(data.error || '分析失败');
      }
    } catch (err) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = () => {
    setCurrentSession(null);
    resetAllData();
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    e.preventDefault();
    
    if (!confirm('确定要删除这个纠纷记录吗？')) {
      return;
    }
    
    const session = sessions.find(s => s.id === sessionId);
    if (session?.disputeId) {
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/dispute/${session.disputeId}`, {
          method: 'DELETE',
        });
      } catch (err) {
        console.error('删除纠纷失败:', err);
      }
    }
    deleteSession(sessionId);
    if (currentSessionId === sessionId) {
      resetAllData();
    }
  };

  const handleTogglePin = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    togglePin(sessionId);
    setActiveMenuId(null);
  };

  const handleEditSession = (e: React.MouseEvent, session: any) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitle(session.customTitle || session.title);
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
    setCurrentSession(sessionId);
  };

  const sortedSessions = getSortedSessions();

  const renderInputContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">证据名称</label>
              <input
                type="text"
                value={evidenceName}
                onChange={(e) => setEvidenceName(e.target.value)}
                placeholder="例如：聊天记录截图"
                className="w-full p-3 bg-white/80 dark:bg-gray-900/80 border-2 border-sky-500/20 rounded-xl text-gray-800 dark:text-gray-200 focus:outline-none focus:border-sky-400/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">证据类型</label>
              <select
                value={evidenceType}
                onChange={(e) => setEvidenceType(e.target.value)}
                className="w-full p-3 bg-white/80 dark:bg-gray-900/80 border-2 border-sky-500/20 rounded-xl text-gray-800 dark:text-gray-200 focus:outline-none focus:border-sky-400/50"
              >
                <option value="">请选择</option>
                <option value="书证">书证</option>
                <option value="物证">物证</option>
                <option value="电子数据">电子数据</option>
                <option value="证人证言">证人证言</option>
                <option value="视听资料">视听资料</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">证据内容</label>
              <textarea
                value={evidenceContent}
                onChange={(e) => setEvidenceContent(e.target.value)}
                placeholder="描述证据的具体内容..."
                className="w-full h-32 p-3 bg-white/80 dark:bg-gray-900/80 border-2 border-sky-500/20 rounded-xl text-gray-800 dark:text-gray-200 focus:outline-none focus:border-sky-400/50 resize-none"
              />
            </div>
            
            {/* 取证提示信息 */}
            <div className="bg-sky-50 dark:bg-sky-900/20 rounded-lg p-3 border border-sky-200 dark:border-sky-800">
              <h4 className="text-xs font-semibold text-sky-700 dark:text-sky-300 mb-2">💡 取证指导</h4>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• <strong>书证：</strong>合同、协议、收据、发票等书面材料</li>
                <li>• <strong>电子数据：</strong>聊天记录、转账记录、邮件、截图等</li>
                <li>• <strong>视听资料：</strong>录音、录像、照片等</li>
                <li>• <strong>证人证言：</strong>知情人的书面或口头证词</li>
                <li>• <strong>物证：</strong>与案件相关的实物证据</li>
              </ul>
            </div>
            
            {/* 已收集证据统计 */}
            {evidenceData && evidenceData.collected && evidenceData.collected.length > 0 && (
              <div className="bg-white/50 dark:bg-gray-700/30 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">📊 已收集证据</h4>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  已收集 {evidenceData.collected.length} 项证据，待补充 {evidenceData.missing ? evidenceData.missing.length : 0} 项
                </div>
              </div>
            )}
            
            <button
              onClick={handleCollectEvidence}
              disabled={loading || !evidenceName.trim()}
              className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-xl hover:from-sky-600 hover:to-blue-700 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <Shield size={18} />}
              {loading ? '处理中...' : '提交取证指导'}
            </button>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <div className="bg-sky-50 dark:bg-sky-900/20 rounded-lg p-3 border border-sky-200 dark:border-sky-800">
              <h4 className="text-xs font-semibold text-sky-700 dark:text-sky-300 mb-2">🛡️ 维权路径规划</h4>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                根据您的案件情况，系统将为您规划最优的维权路径，包括：
              </p>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 多种解决方案对比（协商、调解、仲裁、诉讼）</li>
                <li>• 每种方案的优缺点分析</li>
                <li>• 预计时间和成本评估</li>
                <li>• 推荐的最佳维权策略</li>
                <li>• 具体执行步骤和时间节点</li>
              </ul>
            </div>
            
            {/* 案件基础信息预览 */}
            {organizedData && (
              <div className="bg-white/50 dark:bg-gray-700/30 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">📋 案件基础信息</h4>
                <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                  <p><strong>纠纷类型：</strong>{organizedData.case_type || '未分类'}</p>
                  <p><strong>涉及金额：</strong>{organizedData.amount || '未明确'}</p>
                  <p><strong>当事人：</strong>{organizedData.parties ? organizedData.parties.length : 0} 方</p>
                </div>
              </div>
            )}
            
            <button
              onClick={handlePlanProtection}
              disabled={loading}
              className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-xl hover:from-sky-600 hover:to-blue-700 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <Route size={18} />}
              {loading ? '规划中...' : '开始规划维权路径'}
            </button>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">文书类型</label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full p-3 bg-white/80 dark:bg-gray-900/80 border-2 border-sky-500/20 rounded-xl text-gray-800 dark:text-gray-200 focus:outline-none focus:border-sky-400/50"
              >
                <option value="起诉状">起诉状</option>
                <option value="仲裁申请书">仲裁申请书</option>
                <option value="答辩状">答辩状</option>
                <option value="上诉状">上诉状</option>
                <option value="强制执行申请书">强制执行申请书</option>
              </select>
            </div>
            
            {/* 文书类型说明 */}
            <div className="bg-sky-50 dark:bg-sky-900/20 rounded-lg p-3 border border-sky-200 dark:border-sky-800">
              <h4 className="text-xs font-semibold text-sky-700 dark:text-sky-300 mb-2">📝 文书类型说明</h4>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• <strong>起诉状：</strong>向法院提起民事诉讼的正式文书</li>
                <li>• <strong>仲裁申请书：</strong>向仲裁机构申请仲裁的文书</li>
                <li>• <strong>答辩状：</strong>被告针对原告起诉的回应文书</li>
                <li>• <strong>上诉状：</strong>对一审判决不服提起上诉的文书</li>
                <li>• <strong>强制执行申请书：</strong>申请法院强制执行的文书</li>
              </ul>
            </div>
            
            {/* 已生成文书统计 */}
            {documentData && documentData.documents && documentData.documents.length > 0 && (
              <div className="bg-white/50 dark:bg-gray-700/30 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">📊 已生成文书</h4>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  已生成 {documentData.documents.length} 份文书，当前选择：{documentType}
                </div>
              </div>
            )}
            
            <button
              onClick={handleGenerateDocument}
              disabled={loading}
              className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-xl hover:from-sky-600 hover:to-blue-700 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <FileCheck size={18} />}
              {loading ? '生成中...' : '生成文书'}
            </button>
          </div>
        );

      case 4:
        return (
          <div className="space-y-4">
            <div className="bg-sky-50 dark:bg-sky-900/20 rounded-lg p-3 border border-sky-200 dark:border-sky-800">
              <h4 className="text-xs font-semibold text-sky-700 dark:text-sky-300 mb-2">📈 案件预测分析</h4>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                基于您的案件信息和历史案例数据，系统将为您提供：
              </p>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 胜诉概率评估和依据分析</li>
                <li>• 可能的判决结果预测</li>
                <li>• 案件风险点和薄弱环节识别</li>
                <li>• 类似案例参考和判例分析</li>
                <li>• 提高胜诉率的策略建议</li>
              </ul>
            </div>
            
            {/* 案件分析基础 */}
            {organizedData && (
              <div className="bg-white/50 dark:bg-gray-700/30 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">📋 分析基础</h4>
                <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                  <p><strong>证据完整度：</strong>{evidenceData && evidenceData.collected ? `${evidenceData.collected.length} 项证据已收集` : '待收集'}</p>
                  <p><strong>维权路径：</strong>{protectionData && protectionData.recommended_path ? protectionData.recommended_path.name : '待规划'}</p>
                  <p><strong>案件复杂度：</strong>{organizedData.complexity || '中等'}</p>
                </div>
              </div>
            )}
            
            <button
              onClick={handleAnalyzePrediction}
              disabled={loading}
              className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-xl hover:from-sky-600 hover:to-blue-700 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <TrendingUp size={18} />}
              {loading ? '分析中...' : '开始分析'}
            </button>
          </div>
        );

      case 5:
        return (
          <div className="space-y-4">
            <div className="bg-sky-50 dark:bg-sky-900/20 rounded-lg p-3 border border-sky-200 dark:border-sky-800">
              <h4 className="text-xs font-semibold text-sky-700 dark:text-sky-300 mb-2">🔔 流程提醒创建</h4>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                系统将为您生成完整的案件流程提醒，包括：
              </p>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 关键时间节点提醒（起诉时效、举证期限等）</li>
                <li>• 各阶段需要准备的材料和手续</li>
                <li>• 开庭、调解等重要日程提醒</li>
                <li>• 费用缴纳时间节点</li>
                <li>• 判决执行相关提醒</li>
              </ul>
            </div>
            
            {/* 流程基础信息 */}
            {protectionData && protectionData.recommended_path && (
              <div className="bg-white/50 dark:bg-gray-700/30 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">📋 流程基础</h4>
                <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                  <p><strong>推荐路径：</strong>{protectionData.recommended_path.name}</p>
                  <p><strong>预计时长：</strong>{protectionData.recommended_path.estimated_time || '待评估'}</p>
                  <p><strong>主要阶段：</strong>{protectionData.recommended_path.steps ? protectionData.recommended_path.steps.length : 0} 个</p>
                </div>
              </div>
            )}
            
            {/* 已有提醒统计 */}
            {reminderData && reminderData.reminders && reminderData.reminders.length > 0 && (
              <div className="bg-white/50 dark:bg-gray-700/30 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">📊 已创建提醒</h4>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  已创建 {reminderData.reminders.length} 个流程提醒
                </div>
              </div>
            )}
            
            <button
              onClick={handleCreateReminder}
              disabled={loading}
              className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-xl hover:from-sky-600 hover:to-blue-700 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <Bell size={18} />}
              {loading ? '创建中...' : '创建流程提醒'}
            </button>
          </div>
        );

      case 6:
        return (
          <div className="space-y-4">
            <div className="bg-sky-50 dark:bg-sky-900/20 rounded-lg p-3 border border-sky-200 dark:border-sky-800">
              <h4 className="text-xs font-semibold text-sky-700 dark:text-sky-300 mb-2">⚠️ 避坑提醒分析</h4>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                基于您的案件处理过程，系统将为您总结：
              </p>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 案件处理过程中的常见错误和陷阱</li>
                <li>• 证据收集和保存的注意事项</li>
                <li>• 与对方沟通时的禁忌和技巧</li>
                <li>• 法律程序中的关键注意点</li>
                <li>• 类似案件的经验教训总结</li>
              </ul>
            </div>
            
            {/* 避坑分析结果展示 */}
            {warningData && (
              <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3 border border-amber-200 dark:border-amber-800 max-h-64 overflow-y-auto">
                <h4 className="text-xs font-semibold text-amber-700 dark:text-amber-300 mb-2">⚠️ 避坑分析结果</h4>
                
                {/* 风险总结 */}
                {warningData.risk_summary && (
                  <div className="mb-3">
                    <p className="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">风险总结：</p>
                    <p className="text-xs text-gray-700 dark:text-gray-300">{warningData.risk_summary}</p>
                  </div>
                )}
                
                {/* 经验教训 */}
                {warningData.lessons_learned && warningData.lessons_learned.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">经验教训：</p>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1">
                      {warningData.lessons_learned.slice(0, 3).map((lesson: string, index: number) => (
                        <li key={index}>• {lesson}</li>
                      ))}
                      {warningData.lessons_learned.length > 3 && (
                        <li className="text-gray-500">... 还有 {warningData.lessons_learned.length - 3} 条</li>
                      )}
                    </ul>
                  </div>
                )}
                
                {/* 预防建议 */}
                {warningData.prevention_suggestions && warningData.prevention_suggestions.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">预防建议：</p>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1">
                      {warningData.prevention_suggestions.slice(0, 3).map((suggestion: string, index: number) => (
                        <li key={index}>• {suggestion}</li>
                      ))}
                      {warningData.prevention_suggestions.length > 3 && (
                        <li className="text-gray-500">... 还有 {warningData.prevention_suggestions.length - 3} 条</li>
                      )}
                    </ul>
                  </div>
                )}
                
                {/* 后续检查项 */}
                {warningData.future_check_items && warningData.future_check_items.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">后续检查：</p>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1">
                      {warningData.future_check_items.slice(0, 3).map((item: string, index: number) => (
                        <li key={index}>• {item}</li>
                      ))}
                      {warningData.future_check_items.length > 3 && (
                        <li className="text-gray-500">... 还有 {warningData.future_check_items.length - 3} 条</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}
            
            <button
              onClick={handleAnalyzeWarning}
              disabled={loading}
              className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-xl hover:from-sky-600 hover:to-blue-700 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <AlertTriangle size={18} />}
              {loading ? '分析中...' : warningData ? '重新分析' : '开始分析'}
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  const renderResultContent = () => {
    if (error) {
      return (
        <div className="p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-xl flex items-center gap-3 text-red-700 dark:text-red-300">
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      );
    }

    switch (currentStep) {
      case 0:
        if (!organizedData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <FileText size={48} className="mb-3 opacity-50" />
              <p>整理结果将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">整理结果</h3>
            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                {organizedData.title && <h4 className="text-gray-800 dark:text-gray-200">{organizedData.title}</h4>}
                {organizedData.event_description && <p className="text-gray-700 dark:text-gray-300">{organizedData.event_description}</p>}
                {organizedData.demands && <p className="text-gray-700 dark:text-gray-300"><strong>诉求：</strong>{organizedData.demands}</p>}
              </div>
            </div>
          </div>
        );

      case 1:
        if (!evidenceData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <Shield size={48} className="mb-3 opacity-50" />
              <p>取证指导将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">取证指导</h3>
            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20 max-h-[300px] overflow-y-auto">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {evidenceData.guidance}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        );

      case 2:
        if (!protectionData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <Route size={48} className="mb-3 opacity-50" />
              <p>维权路径将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">维权路径</h3>
            <div className="flex items-center gap-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl">
              <span className="text-2xl font-bold text-orange-600">{protectionData.success_rate}%</span>
              <span className="text-sm text-gray-700 dark:text-gray-300">预估胜诉率</span>
            </div>
            {protectionData.recommended_path && protectionData.recommended_path.map((step: any, index: number) => (
              <div key={index} className="flex items-start gap-4 p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                <div className="w-8 h-8 rounded-full bg-orange-600 text-white flex items-center justify-center font-bold flex-shrink-0">
                  {step.step}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-800 dark:text-gray-200">{step.action}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{step.description}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>预计时间: {step.estimated_time}</span>
                    <span>预计成本: {step.estimated_cost}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        );

      case 3:
        if (!documentData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <FileCheck size={48} className="mb-3 opacity-50" />
              <p>生成的文书将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">{documentType}</h3>
            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20 max-h-[300px] overflow-y-auto">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {documentData.document_content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        );

      case 4:
        if (!predictionData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <TrendingUp size={48} className="mb-3 opacity-50" />
              <p>案件预判结果将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">预判结果</h3>
            <div className="flex items-center gap-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
              <span className="text-2xl font-bold text-green-600">{predictionData.win_probability}%</span>
              <span className="text-sm text-gray-700 dark:text-gray-300">胜诉概率</span>
            </div>
            {predictionData.predicted_amount && (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <span className="font-medium text-gray-800 dark:text-gray-200">预计赔偿金额：</span>
                <span className="text-blue-600">{predictionData.predicted_amount}</span>
              </div>
            )}
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl">
              <span className="font-medium text-gray-800 dark:text-gray-200">证据完整度：</span>
              <span className="text-yellow-600">{predictionData.evidence_completeness || '待评估'}</span>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
              <span className="font-medium text-gray-800 dark:text-gray-200">维权路径：</span>
              <span className="text-purple-600">{predictionData.rights_protection_path || '待分析'}</span>
            </div>
            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20 max-h-[200px] overflow-y-auto">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <h4 className="text-gray-800 dark:text-gray-200">法院裁判倾向</h4>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {predictionData.court_tendency}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        );

      case 5:
        if (!reminderData || reminderData.length === 0) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <Bell size={48} className="mb-3 opacity-50" />
              <p>流程提醒将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">已创建的提醒</h3>
            <div className="space-y-3">
              {reminderData.map((reminder: any, index: number) => (
                <div key={index} className="flex items-center gap-4 p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                  <Bell className="text-orange-600" size={20} />
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-800 dark:text-gray-200">{reminder.reminder_type}</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      提醒时间: {new Date(reminder.reminder_time).toLocaleString('zh-CN')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 6:
        if (!warningData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <AlertTriangle size={48} className="mb-3 opacity-50" />
              <p>风险总结将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">风险总结与预防建议</h3>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl p-4">
              <h4 className="font-semibold text-yellow-800 dark:text-yellow-300 mb-2">风险总结</h4>
              <p className="text-yellow-700 dark:text-yellow-400">{warningData.risk_summary}</p>
            </div>
            {warningData.lessons_learned && warningData.lessons_learned.length > 0 && (
              <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">经验教训</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  {warningData.lessons_learned.map((lesson: string, index: number) => (
                    <li key={index}>{lesson}</li>
                  ))}
                </ul>
              </div>
            )}
            {warningData.prevention_suggestions && warningData.prevention_suggestions.length > 0 && (
              <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">预防建议</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  {warningData.prevention_suggestions.map((suggestion: string, index: number) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
            {warningData.future_check_items && warningData.future_check_items.length > 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-4">
                <h4 className="font-semibold text-green-800 dark:text-green-300 mb-2">未来注意事项</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-green-700 dark:text-green-400">
                  {warningData.future_check_items.map((item: string, index: number) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  const renderResultContentForStep = (step: number) => {
    if (error) {
      return (
        <div className="p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-xl flex items-center gap-3 text-red-700 dark:text-red-300">
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      );
    }

    switch (step) {
      case 0:
        if (!organizedData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <FileText size={48} className="mb-3 opacity-50" />
              <p>整理结果将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">整理结果</h3>
            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                {organizedData.title && <h4 className="text-gray-800 dark:text-gray-200">{organizedData.title}</h4>}
                {organizedData.event_description && <p className="text-gray-700 dark:text-gray-300">{organizedData.event_description}</p>}
                {organizedData.demands && <p className="text-gray-700 dark:text-gray-300"><strong>诉求：</strong>{organizedData.demands}</p>}
              </div>
            </div>
          </div>
        );

      case 1:
        if (!evidenceData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <Shield size={48} className="mb-3 opacity-50" />
              <p>取证指导将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">取证指导</h3>
            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20 max-h-[300px] overflow-y-auto">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {evidenceData.guidance}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        );

      case 2:
        if (!protectionData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <Route size={48} className="mb-3 opacity-50" />
              <p>维权路径将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">维权路径</h3>
            <div className="flex items-center gap-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl">
              <span className="text-2xl font-bold text-orange-600">{protectionData.success_rate}%</span>
              <span className="text-sm text-gray-700 dark:text-gray-300">预估胜诉率</span>
            </div>
            {protectionData.recommended_path && protectionData.recommended_path.map((step: any, index: number) => (
              <div key={index} className="flex items-start gap-4 p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                <div className="w-8 h-8 rounded-full bg-orange-600 text-white flex items-center justify-center font-bold flex-shrink-0">
                  {step.step}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-800 dark:text-gray-200">{step.action}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{step.description}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>预计时间: {step.estimated_time}</span>
                    <span>预计成本: {step.estimated_cost}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        );

      case 3:
        if (!documentData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <FileCheck size={48} className="mb-3 opacity-50" />
              <p>生成的文书将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">{documentType}</h3>
            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20 max-h-[300px] overflow-y-auto">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {documentData.document_content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        );

      case 4:
        if (!predictionData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <TrendingUp size={48} className="mb-3 opacity-50" />
              <p>案件预判结果将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">预判结果</h3>
            <div className="flex items-center gap-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
              <span className="text-2xl font-bold text-green-600">{predictionData.win_probability}%</span>
              <span className="text-sm text-gray-700 dark:text-gray-300">胜诉概率</span>
            </div>
            {predictionData.predicted_amount && (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <span className="font-medium text-gray-800 dark:text-gray-200">预计赔偿金额：</span>
                <span className="text-blue-600">{predictionData.predicted_amount}</span>
              </div>
            )}
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl">
              <span className="font-medium text-gray-800 dark:text-gray-200">证据完整度：</span>
              <span className="text-yellow-600">{predictionData.evidence_completeness || '待评估'}</span>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
              <span className="font-medium text-gray-800 dark:text-gray-200">维权路径：</span>
              <span className="text-purple-600">{predictionData.rights_protection_path || '待分析'}</span>
            </div>
            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20 max-h-[200px] overflow-y-auto">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <h4 className="text-gray-800 dark:text-gray-200">法院裁判倾向</h4>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {predictionData.court_tendency}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        );

      case 5:
        if (!reminderData || reminderData.length === 0) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <Bell size={48} className="mb-3 opacity-50" />
              <p>流程提醒将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">已创建的提醒</h3>
            <div className="space-y-3">
              {reminderData.map((reminder: any, index: number) => (
                <div key={index} className="flex items-center gap-4 p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                  <Bell className="text-orange-600" size={20} />
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-800 dark:text-gray-200">{reminder.reminder_type}</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      提醒时间: {new Date(reminder.reminder_time).toLocaleString('zh-CN')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 6:
        if (!warningData) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <AlertTriangle size={48} className="mb-3 opacity-50" />
              <p>风险总结将在此显示</p>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">风险总结与预防建议</h3>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl p-4">
              <h4 className="font-semibold text-yellow-800 dark:text-yellow-300 mb-2">风险总结</h4>
              <p className="text-yellow-700 dark:text-yellow-400">{warningData.risk_summary}</p>
            </div>
            {warningData.lessons_learned && warningData.lessons_learned.length > 0 && (
              <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">经验教训</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  {warningData.lessons_learned.map((lesson: string, index: number) => (
                    <li key={index}>{lesson}</li>
                  ))}
                </ul>
              </div>
            )}
            {warningData.prevention_suggestions && warningData.prevention_suggestions.length > 0 && (
              <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">预防建议</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  {warningData.prevention_suggestions.map((suggestion: string, index: number) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
            {warningData.future_check_items && warningData.future_check_items.length > 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-4">
                <h4 className="font-semibold text-green-800 dark:text-green-300 mb-2">未来注意事项</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-green-700 dark:text-green-400">
                  {warningData.future_check_items.map((item: string, index: number) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed top-20 left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground flex">
      {/* 左侧边栏 - 纠纷记录 */}
      <div className="relative z-10 w-64 h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-r border-sky-200 dark:border-sky-900/30 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 dark:border-sky-900/30">
          <button
            onClick={handleNewSession}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-xl font-medium hover:from-sky-600 hover:to-blue-700 transition-all shadow-lg"
          >
            <Plus size={18} />
            新建纠纷处理
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
          {sortedSessions.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              <FileText size={32} className="mx-auto mb-2 opacity-50" />
              <p className="text-sm">暂无纠纷记录</p>
            </div>
          ) : (
            <div className="space-y-1">
              {sortedSessions.map((session) => (
                <div
                  key={session.id}
                  className="relative mb-2"
                >
                  <div
                    onClick={() => handleSwitchSession(session.id)}
                    className={`group flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all shadow-sm hover:shadow-md ${
                      currentSessionId === session.id
                        ? 'bg-gradient-to-r from-sky-100 to-blue-50 dark:from-sky-900/30 dark:to-blue-900/20 border border-sky-300 dark:border-sky-700'
                        : 'bg-white/90 dark:bg-gray-800/90 hover:bg-gray-50 dark:hover:bg-gray-700/80 border border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      currentSessionId === session.id
                        ? 'bg-sky-500/15 text-sky-600 dark:bg-sky-400/20 dark:text-sky-400'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                    }`}>
                      <FileText size={20} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 truncate">
                        {session.customTitle || session.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(session.updatedAt).toLocaleDateString()}
                        </p>
                        {session.isPinned && (
                          <span className="text-xs px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full">
                            置顶
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {currentSessionId === session.id && (
                        <div className="w-6 h-6 rounded-full bg-sky-500/20 flex items-center justify-center flex-shrink-0">
                          <Check size={14} className="text-sky-600 dark:text-sky-400" />
                        </div>
                      )}
                      <button
                        onClick={(e) => handleToggleMenu(e, session.id)}
                        className="p-2 rounded-lg text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-600 dark:hover:text-gray-300 transition-all"
                        title="更多操作"
                      >
                        <MoreHorizontal size={16} />
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

      {/* 右侧内容区域 */}
      <div className="relative z-10 flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <div className="flex-1 w-full overflow-y-auto overflow-x-hidden">
          <div className="w-full mx-auto px-4 pt-4 pb-4 h-full flex flex-col">
            {/* 页面标题 */}
            <div className="text-center mb-4">
              <h1 className="text-2xl font-bold text-sky-700 dark:text-sky-300 mb-1">纠纷处理中心</h1>
              <p className="text-sm text-gray-700 dark:text-gray-300">一站式纠纷处理流程</p>
              <div className="h-1 w-24 bg-gradient-to-r from-amber-500 to-orange-500 mx-auto rounded-full mt-2" />
            </div>

            {/* 步骤导航 */}
            <div className="mb-4 flex items-center justify-center gap-2 flex-wrap">
              {STEPS.map((step, index) => (
                <button
                  key={step.id}
                  onClick={() => index <= currentStep && setCurrentStep(index)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                    index < currentStep
                      ? 'bg-green-500 text-white'
                      : index === currentStep
                        ? 'bg-sky-500 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  } ${index <= currentStep ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                >
                  {index < currentStep ? <CheckCircle size={14} /> : <step.icon size={14} />}
                  <span className="hidden md:inline">{step.name}</span>
                </button>
              ))}
            </div>

            {/* 空状态 */}
            {!currentSessionId && !inputContent && !organizedData && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="mb-6 relative inline-block">
                    <div className="absolute inset-0 rounded-full bg-gradient-to-br from-sky-600/30 via-amber-600/30 to-red-600/30 blur-2xl animate-pulse-slow" />
                    <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 shadow-2xl border-2 border-sky-400 mx-auto">
                      <FileText size={40} className="text-white" />
                    </div>
                  </div>
                  <h2 className="mb-3 text-2xl font-bold text-sky-800 dark:text-sky-300">开始新的纠纷处理</h2>
                  <p className="mb-6 text-center text-gray-700 dark:text-gray-300 max-w-md">
                    一站式纠纷处理流程，从整理到解决
                  </p>
                  <button
                    onClick={() => setInputContent(' ')}
                    className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-amber-600 to-orange-600 px-6 py-3 text-white font-medium shadow-lg hover:shadow-xl hover:shadow-amber-500/30 transition-all border border-sky-400/50"
                  >
                    <Plus size={20} />
                    开始处理
                  </button>
                </div>
              </div>
            )}

            {/* 主内容区域 - 左右布局 */}
            {(currentSessionId || inputContent || organizedData) && (
              <div className="flex-1 flex gap-4 min-h-0">
                {/* 左边区域 - 输入信息 */}
                <div className="w-2/5 flex flex-col">
                  <div className="flex-1 rounded-2xl border border-sky-500/30 bg-white/90 dark:bg-gray-800/90 p-5 backdrop-blur-sm flex flex-col overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
                    <div className="flex items-center gap-3 mb-5 flex-shrink-0 bg-gradient-to-r from-sky-50 to-blue-50 dark:from-sky-900/20 dark:to-blue-900/10 p-3 rounded-xl">
                      {(() => {
                        const step = STEPS[currentStep];
                        const Icon = step.icon;
                        return (
                          <>
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center">
                              <Icon size={20} className="text-white" />
                            </div>
                            <div>
                              <h2 className="text-lg font-semibold text-sky-700 dark:text-sky-300">{step.name}</h2>
                              <p className="text-sm text-gray-600 dark:text-gray-400">{step.description}</p>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                    <div className="flex-1 overflow-y-auto">
                      {currentStep === 0 ? (
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">描述您的纠纷情况</label>
                            <textarea
                              value={inputContent}
                              onChange={(e) => setInputContent(e.target.value)}
                              placeholder="请描述：谁、什么时候、发生了什么事、您想要什么结果、有什么证据..."
                              className="w-full h-64 p-4 bg-white/80 dark:bg-gray-900/80 border-2 border-sky-500/20 rounded-xl text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-sky-400/50 resize-none text-sm leading-relaxed"
                            />
                          </div>
                          
                          {/* 填写提示信息 */}
                          <div className="bg-sky-50 dark:bg-sky-900/20 rounded-lg p-3 border border-sky-200 dark:border-sky-800">
                            <h4 className="text-xs font-semibold text-sky-700 dark:text-sky-300 mb-2">💡 填写提示</h4>
                            <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                              <li>• <strong>当事人信息：</strong>姓名、联系方式、身份（原告/被告）</li>
                              <li>• <strong>时间地点：</strong>纠纷发生的具体时间和地点</li>
                              <li>• <strong>事件经过：</strong>详细描述事情的来龙去脉</li>
                              <li>• <strong>诉求目标：</strong>您希望通过法律途径达到什么目的</li>
                              <li>• <strong>相关证据：</strong>合同、聊天记录、转账凭证等</li>
                            </ul>
                          </div>
                          
                          {/* 案件信息预览 */}
                          {inputContent.trim() && (
                            <div className="bg-white/50 dark:bg-gray-700/30 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                              <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">📊 案件信息预览</h4>
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div className="flex items-center gap-1">
                                  <span className="text-gray-500 dark:text-gray-400">字数：</span>
                                  <span className="font-medium text-sky-600 dark:text-sky-400">{inputContent.length} 字</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <span className="text-gray-500 dark:text-gray-400">预估复杂度：</span>
                                  <span className="font-medium text-sky-600 dark:text-sky-400">
                                    {inputContent.length < 100 ? '简单' : inputContent.length < 300 ? '一般' : '复杂'}
                                  </span>
                                </div>
                              </div>
                              {inputContent.length > 50 && (
                                <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                                  <p className="text-xs text-gray-500 dark:text-gray-400">
                                    已输入足够信息，可以点击"开始整理"按钮
                                  </p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ) : (
                        renderInputContent()
                      )}
                    </div>
                    {currentStep === 0 && (
                      <div className="mt-4 flex-shrink-0">
                        <button
                          onClick={handleOrganize}
                          disabled={loading || !inputContent.trim()}
                          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-xl hover:from-sky-600 hover:to-blue-700 transition-all disabled:opacity-50"
                        >
                          {loading ? <Loader2 className="animate-spin" size={18} /> : <ArrowRight size={18} />}
                          {loading ? '整理中...' : '开始整理'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* 右边区域 - 处理结果 */}
                <div className="w-3/5 flex flex-col">
                  <div className="flex-1 rounded-2xl border border-sky-500/30 bg-white/90 dark:bg-gray-800/90 p-5 backdrop-blur-sm flex flex-col overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
                    <div className="flex items-center justify-between mb-5 flex-shrink-0 bg-gradient-to-r from-sky-50 to-blue-50 dark:from-sky-900/20 dark:to-blue-900/10 p-3 rounded-xl">
                      <h2 className="text-lg font-semibold text-sky-700 dark:text-sky-300">处理结果</h2>
                      {currentStep > 0 && currentStep < STEPS.length - 1 && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => setCurrentStep(currentStep - 1)}
                            className="px-3 py-1.5 text-sm border border-sky-500/30 rounded-lg hover:bg-sky-500/10 transition-colors flex items-center gap-1"
                          >
                            <ChevronLeft size={14} />
                            上一步
                          </button>
                          <button
                            onClick={() => setCurrentStep(currentStep + 1)}
                            className="px-3 py-1.5 text-sm bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-600 hover:to-blue-700 transition-all flex items-center gap-1"
                          >
                            下一步
                            <ChevronRight size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                    
                    {/* 步骤结果卡片区域 */}
                    <div className="mb-5 flex gap-3 overflow-x-auto pb-3 flex-shrink-0">
                      {STEPS.map((step, index) => {
                        const hasData = index === 0 ? !!organizedData : 
                                       index === 1 ? !!evidenceData :
                                       index === 2 ? !!protectionData :
                                       index === 3 ? !!documentData :
                                       index === 4 ? !!predictionData :
                                       index === 5 ? !!reminderData :
                                       index === 6 ? !!warningData : false;
                        
                        return (
                          <button
                            key={step.id}
                            onClick={() => setActiveStepResult(index)}
                            className={`flex-shrink-0 w-1/7 min-w-[120px] p-3 rounded-xl transition-all shadow-sm hover:shadow-md ${hasData ? 
                              activeStepResult === index ? 
                                'bg-gradient-to-r from-sky-100 to-blue-50 dark:from-sky-900/30 dark:to-blue-900/20 border border-sky-400'
                                : 'bg-white/80 dark:bg-gray-700/80 border border-sky-300/30 hover:bg-sky-50 dark:hover:bg-sky-900/20'
                                : 'bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'}`}
                            disabled={!hasData}
                          >
                            <div className="flex flex-col items-center text-center">
                              {(() => {
                                const Icon = step.icon;
                                return (
                                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-2 ${hasData ? (activeStepResult === index ? 'bg-sky-500/15 text-sky-600 dark:bg-sky-400/20 dark:text-sky-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400') : 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500'}`}>
                                    <Icon size={20} />
                                  </div>
                                );
                              })()}
                              <span className={`text-xs font-semibold ${hasData ? (activeStepResult === index ? 'text-sky-700 dark:text-sky-300' : 'text-gray-700 dark:text-gray-300') : 'text-gray-500 dark:text-gray-400'}`}>{step.name}</span>
                              {hasData && (
                                <span className={`mt-1 text-xs px-2 py-0.5 rounded-full ${activeStepResult === index ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-700/50 text-gray-600 dark:text-gray-400'}`}>✓ 已完成</span>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                    
                    <div className="flex-1 overflow-y-auto">
                      {activeStepResult !== null ? (
                        renderResultContentForStep(activeStepResult)
                      ) : (
                        // 默认显示上一个步骤的结果
                        currentStep > 0 ? renderResultContentForStep(currentStep - 1) : (
                          <div className="text-gray-500 dark:text-gray-400 text-center py-8">
                            完成第一步操作后将显示结果
                          </div>
                        )
                      )}
                    </div>
                  </div>
                </div>
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

export default dynamic(() => Promise.resolve(DisputeCenterPageContent), {
  ssr: false,
});