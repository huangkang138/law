'use client';

import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, MessageSquare, Loader2, CheckCircle, AlertCircle, Bot, Settings, Home, Sparkles, Save, X, Upload, FileText } from 'lucide-react';
import DownloadDropdown from '@/components/DownloadDropdown';
import { exportAsImage, exportAsPDF, exportAsWord } from '@/lib/exportUtils';
import { useRouter } from 'next/navigation';

interface Agent {
  id: string;
  name: string;
  description: string;
  avatar: string;
  agent_type: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  is_preset: boolean;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface AgentFormData {
  name: string;
  description: string;
  avatar: string;
  system_prompt: string;
  agent_type: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  is_active: boolean;
}

const AVATAR_OPTIONS = ['⚖️', '🤖', '👨‍⚖️', '👩‍⚖️', '📚', '🔍', '⚔️', '✍️', '💼', '🎯', '🛡️', '💡'];

const AGENT_TYPES = [
  { value: 'legal', label: '法律咨询' },
  { value: 'contract', label: '合同审查' },
  { value: 'case-analysis', label: '案情分析' },
  { value: 'debate', label: '辩论代理' },
  { value: 'document', label: '文书起草' },
  { value: 'calculator', label: '法律计算器' },
  { value: 'knowledge-graph', label: '知识图谱' },
  { value: 'dispute-organize', label: '争议整理' },
  { value: 'similar-documents', label: '相似文档' },
  { value: 'legal-calendar', label: '法律日历' },
  { value: 'limitation', label: '诉讼时效' },
  { value: 'case-explanation', label: '案件解释' },
  { value: 'custom', label: '自定义' },
];

const PRESET_PROMPTS = {
  legal: `你是一个专业的法律咨询助手，专注于中国法律体系。

**重要原则：**
1. 使用通俗易懂的语言，避免复杂的法律术语，或在使用时提供清晰解释
2. 你提供的是一般性法律信息，不是专业法律建议
3. 始终建议用户在重要事项上咨询专业律师
4. 保持友好、耐心的态度
5. 如果不确定，诚实地说明，不要编造信息

**你的能力：**
- 解释常见法律概念和条款
- 回答基本的法律问题
- 分析简单合同的关键条款
- 提供法律程序的基本指导

**免责声明：**
⚠️ 本助手提供的信息仅供参考，不构成专业法律建议。如遇具体法律问题，请咨询持牌律师。

请始终保持专业、友好，帮助用户理解法律知识。`,
  contract: `你是一名专业的合同审查专家，精通各类合同的法律风险识别。

**你的职责：**
1. 仔细审查合同的每一条款
2. 识别合同中的法律风险和不公平条款
3. 提供具体的修改建议
4. 评估合同的整体风险等级（0-100分）
5. 指出需要特别关注的关键条款

**审查要点：**
- 合同条款的合法性和合规性
- 权利义务的平衡性
- 违约责任的明确性
- 争议解决条款的合理性
- 保密条款和保护措施

**输出格式：**
请以清晰的结构输出审查结果，包括：
1. 风险评分
2. 主要风险点
3. 具体修改建议
4. 法律依据

请始终保持专业、客观，帮助用户识别和规避合同风险。`,
  'case-analysis': `你是一位资深的案情分析专家，擅长从案件描述中提取关键法律要素。

**你的能力：**
1. 准确理解案件的基本事实
2. 识别案件的争议焦点
3. 提取相关的法律要素
4. 分析案件的法律关系
5. 提供初步的法律分析

**分析框架：**
- 案件基本事实梳理
- 当事人身份和关系
- 争议焦点识别
- 相关法律条文
- 法律关系分析
- 初步法律意见

请始终保持客观、准确，为后续的法律程序提供有力支持。`,
  debate: `你是一名专业的辩论代理，擅长在法庭上进行有力的辩论。

**你的职责：**
1. 根据案件事实构建有力的论点
2. 针对对方观点进行有效反驳
3. 引用相关法律条文支持你的论点
4. 逻辑清晰，条理分明
5. 语言专业，表达准确

**辩论技巧：**
- 事实清楚，证据确凿
- 法律依据充分
- 逻辑推理严密
- 语言表达有力
- 应对灵活机智

请始终保持专业水准，为当事人争取最大利益。`,
  document: `你是一名专业的法律文书起草专家，精通各类法律文书的撰写。

**你的能力：**
1. 起草各类法律文书（起诉状、答辩状、合同、协议等）
2. 确保文书格式规范、内容完整
3. 语言准确、逻辑清晰
4. 符合法律要求和实务惯例
5. 根据用户需求定制化起草

**起草原则：**
1. 格式规范，符合法律文书标准
2. 内容完整，涵盖必要要素
3. 语言准确，避免歧义
4. 逻辑清晰，条理分明
5. 专业规范，符合实务要求

请根据用户的具体需求，起草专业、规范的法律文书。`,
  calculator: `你是一名专业的法律计算器助手，精通各类法律费用的计算。

**你的能力：**
1. 计算诉讼费用（包括案件受理费、申请费等）
2. 计算律师费用
3. 计算仲裁费用
4. 计算鉴定费用
5. 计算保全费用
6. 计算执行费用
7. 计算公告费用
8. 计算工伤赔偿费用
9. 计算合同违约金

**计算原则：**
1. 根据最新的法律法规和收费标准
2. 准确计算各项费用
3. 提供详细的计算过程
4. 说明费用计算的依据
5. 提供相关的法律条文参考

请根据用户提供的具体情况，准确计算相关法律费用。`,
  'knowledge-graph': `你是一名专业的法律知识图谱分析专家，擅长构建和分析法律知识图谱。

**你的能力：**
1. 构建法律概念之间的关联关系
2. 分析法律条文之间的逻辑关系
3. 识别案件中的关键法律要素
4. 可视化法律知识结构
5. 提供知识图谱的深度分析

**分析框架：**
- 法律概念识别
- 关联关系构建
- 层次结构分析
- 路径推理
- 知识补全

请始终保持专业、准确，帮助用户理解复杂的法律知识结构。`,
  'dispute-organize': `你是一名专业的争议整理专家，擅长梳理和整理复杂的法律争议。

**你的能力：**
1. 识别案件中的核心争议点
2. 梳理争议的逻辑关系
3. 分析各方的立场和论据
4. 整理争议的证据链
5. 提供争议解决的思路

**整理框架：**
- 争议点识别
- 争议分类整理
- 证据链梳理
- 法律关系分析
- 解决方案建议

请始终保持客观、清晰，帮助用户理清复杂的法律争议。`,
  'similar-documents': `你是一名专业的相似文档分析专家，擅长识别和比较相似的法律文档。

**你的能力：**
1. 识别相似的法律文书
2. 比较文档的异同点
3. 分析相似案例的判决结果
4. 提供参考判例
5. 总结相似文档的共性

**分析框架：**
- 文档特征提取
- 相似度计算
- 差异分析
- 判例参考
- 风险提示

请始终保持专业、准确，帮助用户找到有价值的参考文档。`,
  'legal-calendar': `你是一名专业的法律日历助手，精通各类法律时效和重要日期。

**你的能力：**
1. 计算诉讼时效
2. 提醒重要的法律期限
3. 计算各种法定期间
4. 提供法律日历管理
5. 提醒重要的法律程序节点

**提醒内容：**
- 诉讼时效到期提醒
- 上诉期限提醒
- 举证期限提醒
- 执行期限提醒
- 其他法定期限提醒

请始终保持准确、及时，帮助用户避免错过重要的法律期限。`,
  limitation: `你是一名专业的诉讼时效专家，精通各类诉讼时效的计算和适用。

**你的能力：**
1. 计算各类案件的诉讼时效
2. 识别诉讼时效的中断和中止
3. 分析时效的特殊规定
4. 提供时效保护的建议
5. 解答时效相关的法律问题

**时效类型：**
- 普通诉讼时效（3年）
- 特殊诉讼时效
- 最长诉讼时效（20年）
- 时效中断和中止
- 时效的起算点

请始终保持专业、准确，帮助用户正确理解和适用诉讼时效。`,
  'case-explanation': `你是一名专业的案件解释专家，擅长解释复杂的法律案件和判决。

**你的能力：**
1. 解释复杂的法律判决
2. 分析判决的法律依据
3. 解释判决的推理过程
4. 提供案件的背景信息
5. 解答案件相关的法律问题

**解释框架：**
- 案件背景介绍
- 争议焦点分析
- 法律依据解释
- 判决逻辑梳理
- 案件意义总结

请始终保持专业、清晰，帮助用户理解复杂的法律案件。`,
  custom: `你是一个专业的AI助手，请根据用户的需求提供专业、准确、友好的服务。

请始终保持专业、耐心，帮助用户解决问题。`,
};

const EXAMPLE_PROMPTS = {
  'case-analysis': [
    '张三在超市偷了价值5000元的商品',
    '李四在公共场合殴打他人',
    '王五醉酒驾驶机动车',
    '赵六故意损坏他人财物',
  ],
  'debate': [
    '一起房屋租赁合同纠纷，房东要求提前解除合同',
    '一起交通事故责任认定纠纷',
    '一起劳动争议，员工要求支付加班费',
    '一起民间借贷纠纷，借款人拒绝还款',
  ],
  'document': [
    '民事起诉状',
    '离婚协议书',
    '劳动合同',
    '法律意见书',
  ],
};

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [showChatModal, setShowChatModal] = useState(false);
  const [chatAgent, setChatAgent] = useState<Agent | null>(null);
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [showExamples, setShowExamples] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [filterType, setFilterType] = useState<string>('all');

  const [formData, setFormData] = useState<AgentFormData>({
    name: '',
    description: '',
    avatar: '🤖',
    system_prompt: '',
    agent_type: 'custom',
    temperature: 70,
    max_tokens: 2000,
    top_p: 90,
    is_active: true,
  });

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/agents?user_id=anonymous`);
      const data = await response.json();
      if (data.success) {
        setAgents(data.data);
      }
    } catch (error) {
      console.error('加载智能体失败:', error);
      setMessage({ type: 'error', text: '加载智能体失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAgent = async () => {
    if (!formData.name.trim() || !formData.system_prompt.trim()) {
      setMessage({ type: 'error', text: '请填写名称和系统提示词' });
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          user_id: 'anonymous',
        }),
      });

      const data = await response.json();
      if (data.success) {
        setMessage({ type: 'success', text: '智能体创建成功' });
        setShowCreateModal(false);
        resetFormData();
        loadAgents();
      } else {
        setMessage({ type: 'error', text: data.error || '创建失败' });
      }
    } catch (error) {
      console.error('创建智能体失败:', error);
      setMessage({ type: 'error', text: '创建智能体失败' });
    }
  };

  const handleUpdateAgent = async () => {
    if (!editingAgent) return;

    try {
      const response = await fetch(`${API_BASE}/api/agents/${editingAgent.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      if (data.success) {
        setMessage({ type: 'success', text: '智能体更新成功' });
        setEditingAgent(null);
        resetFormData();
        loadAgents();
      } else {
        setMessage({ type: 'error', text: data.error || '更新失败' });
      }
    } catch (error) {
      console.error('更新智能体失败:', error);
      setMessage({ type: 'error', text: '更新智能体失败' });
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm('确定要删除这个智能体吗？')) return;

    try {
      const response = await fetch(`${API_BASE}/api/agents/${agentId}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      if (data.success) {
        setMessage({ type: 'success', text: '智能体删除成功' });
        loadAgents();
      } else {
        setMessage({ type: 'error', text: data.error || '删除失败' });
      }
    } catch (error) {
      console.error('删除智能体失败:', error);
      setMessage({ type: 'error', text: '删除智能体失败' });
    }
  };

  const handleChat = async () => {
    if (!chatAgent || !chatMessage.trim()) return;

    try {
      setChatLoading(true);
      const response = await fetch(`${API_BASE}/api/agents/${chatAgent.id}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: chatMessage,
        }),
      });

      const data = await response.json();
      if (data.success) {
        setChatResponse(data.data.response);
      } else {
        setMessage({ type: 'error', text: data.error || '对话失败' });
      }
    } catch (error) {
      console.error('对话失败:', error);
      setMessage({ type: 'error', text: '对话失败' });
    } finally {
      setChatLoading(false);
    }
  };

  const handleInitPresets = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/agents/init-presets`, {
        method: 'POST',
      });

      const data = await response.json();
      if (data.success) {
        setMessage({ type: 'success', text: data.message || '预设智能体初始化成功' });
        loadAgents();
      } else {
        setMessage({ type: 'error', text: data.error || '初始化失败' });
      }
    } catch (error) {
      console.error('初始化预设智能体失败:', error);
      setMessage({ type: 'error', text: '初始化预设智能体失败' });
    }
  };

  const resetFormData = () => {
    setFormData({
      name: '',
      description: '',
      avatar: '🤖',
      system_prompt: '',
      agent_type: 'custom',
      temperature: 70,
      max_tokens: 2000,
      top_p: 90,
      is_active: true,
    });
  };

  const openCreateModal = () => {
    resetFormData();
    setShowCreateModal(true);
  };

  const openEditModal = (agent: Agent) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      description: agent.description || '',
      avatar: agent.avatar || '🤖',
      system_prompt: '',  // 不加载预设智能体的系统提示词
      agent_type: agent.agent_type,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
      top_p: agent.top_p,
      is_active: agent.is_active,
    });
  };

  const openChatModal = (agent: Agent) => {
    setChatAgent(agent);
    setChatMessage('');
    setChatResponse('');
    setUploadedFile(null);
    setShowExamples(false);
    setShowChatModal(true);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploadingFile(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/api/document/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        setUploadedFile(file);
        setChatMessage(`已上传文件: ${file.name}\n\n请审查这份合同...`);
        setMessage({ type: 'success', text: '文件上传成功' });
      } else {
        setMessage({ type: 'error', text: data.error || '文件上传失败' });
      }
    } catch (error) {
      console.error('文件上传失败:', error);
      setMessage({ type: 'error', text: '文件上传失败' });
    } finally {
      setUploadingFile(false);
    }
  };

  const handleExampleClick = (example: string) => {
    setChatMessage(example);
    setShowExamples(false);
  };

  const handleDownloadImage = async () => {
    if (!chatResponse) return;

    try {
      await exportAsImage(chatResponse, { title: chatAgent?.name || '法律文书' });
      setMessage({ type: 'success', text: '导出图片成功' });
    } catch (error) {
      console.error('导出图片失败:', error);
      setMessage({ type: 'error', text: '导出图片失败' });
    }
  };

  const handleDownloadPDF = async () => {
    if (!chatResponse) return;

    try {
      await exportAsPDF(chatResponse, { title: chatAgent?.name || '法律文书' });
      setMessage({ type: 'success', text: '导出PDF成功' });
    } catch (error) {
      console.error('导出PDF失败:', error);
      setMessage({ type: 'error', text: '导出PDF失败' });
    }
  };

  const handleDownloadWord = async () => {
    if (!chatResponse) return;

    try {
      await exportAsWord(chatResponse, { title: chatAgent?.name || '法律文书' });
      setMessage({ type: 'success', text: '导出Word成功' });
    } catch (error) {
      console.error('导出Word失败:', error);
      setMessage({ type: 'error', text: '导出Word失败' });
    }
  };

  const handleAgentTypeChange = (type: string) => {
    setFormData({
      ...formData,
      agent_type: type,
      system_prompt: PRESET_PROMPTS[type as keyof typeof PRESET_PROMPTS] || '',
    });
  };

  const filteredAgents = filterType === 'all' 
    ? agents 
    : agents.filter(agent => agent.agent_type === filterType);

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold font-serif text-sky-900 dark:text-sky-100 flex items-center gap-3">
              <Bot className="w-8 h-8" />
              智能体管理
            </h1>
            <p className="mt-2 text-sky-700 dark:text-sky-300">
              创建和管理您的AI智能体，定制专属的法律助手
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleInitPresets}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 rounded-lg border border-sky-200 dark:border-sky-800 hover:bg-sky-50 dark:hover:bg-gray-700 transition-smooth"
            >
              <Sparkles className="w-4 h-4" />
              初始化预设智能体
            </button>
            <button
              onClick={openCreateModal}
              className="flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-smooth"
            >
              <Plus className="w-4 h-4" />
              创建智能体
            </button>
            <button
              onClick={() => router.push('/agents/overview')}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-smooth"
            >
              <FileText className="w-4 h-4" />
              总览
            </button>
          </div>
        </div>

        {message && (
          <div
            className={`mb-6 rounded-md p-4 flex items-start gap-2 ${
              message.type === 'success'
                ? 'bg-green-50 text-green-900 border border-green-200 dark:bg-green-950/30 dark:text-green-200 dark:border-green-800/50'
                : 'bg-red-50 text-red-900 border border-red-200 dark:bg-red-950/30 dark:text-red-200 dark:border-red-800/50'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle size={20} className="mt-0.5 flex-shrink-0 text-green-600 dark:text-green-400" />
            ) : (
              <AlertCircle size={20} className="mt-0.5 flex-shrink-0 text-red-600 dark:text-red-400" />
            )}
            <p>{message.text}</p>
          </div>
        )}

        <div className="mb-6">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setFilterType('all')}
              className={`px-4 py-2 rounded-lg transition-smooth ${
                filterType === 'all'
                  ? 'bg-sky-600 text-white'
                  : 'bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 hover:bg-sky-50 dark:hover:bg-gray-700'
              }`}
            >
              全部
            </button>
            {AGENT_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => setFilterType(type.value)}
                className={`px-4 py-2 rounded-lg transition-smooth ${
                  filterType === type.value
                    ? 'bg-sky-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 hover:bg-sky-50 dark:hover:bg-gray-700'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-sky-600" />
          </div>
        ) : filteredAgents.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="w-16 h-16 mx-auto text-sky-300 dark:text-sky-700 mb-4" />
            <p className="text-sky-700 dark:text-sky-300 mb-4">还没有智能体，点击上方按钮创建一个吧！</p>
            <button
              onClick={handleInitPresets}
              className="px-6 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-smooth"
            >
              初始化预设智能体
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAgents.map((agent) => (
              <div
                key={agent.id}
                className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-6 hover:shadow-xl transition-smooth"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-4xl">{agent.avatar || '🤖'}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-sky-900 dark:text-sky-100">
                        {agent.name}
                      </h3>
                      <span className="text-xs px-2 py-1 bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 rounded-full">
                        {AGENT_TYPES.find(t => t.value === agent.agent_type)?.label || agent.agent_type}
                      </span>
                    </div>
                  </div>
                  {agent.is_preset && (
                    <span className="text-xs px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full">
                      预设
                    </span>
                  )}
                </div>

                <p className="text-sm text-sky-700 dark:text-sky-300 mb-4 line-clamp-2">
                  {agent.description || '暂无描述'}
                </p>

                <div className="flex items-center gap-4 text-xs text-sky-600 dark:text-sky-400 mb-4">
                  <span>使用次数: {agent.usage_count}</span>
                  <span>温度: {agent.temperature}</span>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => openChatModal(agent)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-smooth text-sm"
                  >
                    <MessageSquare className="w-4 h-4" />
                    对话
                  </button>
                  {!agent.is_preset && (
                    <>
                      <button
                        onClick={() => openEditModal(agent)}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 rounded-lg hover:bg-sky-200 dark:hover:bg-sky-900/50 transition-smooth text-sm"
                      >
                        <Edit2 className="w-4 h-4" />
                        编辑
                      </button>
                      <button
                        onClick={() => handleDeleteAgent(agent.id)}
                        className="px-3 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-smooth"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8">
          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 rounded-lg border border-sky-200 dark:border-sky-800 hover:bg-sky-50 dark:hover:bg-gray-700 transition-smooth"
          >
            <Home className="w-4 h-4" />
            返回上一页面
          </button>
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-sky-200 dark:border-sky-800">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-sky-900 dark:text-sky-100 flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  创建智能体
                </h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-200"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  智能体名称 *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="输入智能体名称"
                  className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  智能体描述
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="描述这个智能体的功能和用途"
                  rows={2}
                  className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  智能体头像
                </label>
                <div className="flex gap-2 flex-wrap">
                  {AVATAR_OPTIONS.map((avatar) => (
                    <button
                      key={avatar}
                      onClick={() => setFormData({ ...formData, avatar })}
                      className={`w-10 h-10 rounded-lg border-2 transition-smooth ${
                        formData.avatar === avatar
                          ? 'border-sky-600 bg-sky-100 dark:bg-sky-900/30'
                          : 'border-sky-200 dark:border-sky-800 hover:border-sky-400'
                      }`}
                    >
                      {avatar}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  智能体类型
                </label>
                <select
                  value={formData.agent_type}
                  onChange={(e) => handleAgentTypeChange(e.target.value)}
                  className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  {AGENT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  系统提示词 *
                </label>
                <textarea
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  placeholder="输入系统提示词，定义智能体的角色和行为"
                  rows={8}
                  className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono text-sm"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                    温度 (0-100)
                  </label>
                  <input
                    type="number"
                    value={formData.temperature}
                    onChange={(e) => setFormData({ ...formData, temperature: parseInt(e.target.value) })}
                    min="0"
                    max="100"
                    className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                    最大Token数
                  </label>
                  <input
                    type="number"
                    value={formData.max_tokens}
                    onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                    min="512"
                    max="8192"
                    className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                    Top P (0-100)
                  </label>
                  <input
                    type="number"
                    value={formData.top_p}
                    onChange={(e) => setFormData({ ...formData, top_p: parseInt(e.target.value) })}
                    min="0"
                    max="100"
                    className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-sky-600 rounded focus:ring-sky-500"
                />
                <label htmlFor="is_active" className="text-sm text-sky-900 dark:text-sky-100">
                  启用此智能体
                </label>
              </div>
            </div>

            <div className="p-6 border-t border-sky-200 dark:border-sky-800 flex gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-sky-200 dark:border-sky-800 text-sky-700 dark:text-sky-300 rounded-lg hover:bg-sky-50 dark:hover:bg-gray-800 transition-smooth"
              >
                取消
              </button>
              <button
                onClick={handleCreateAgent}
                className="flex-1 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-smooth flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                创建智能体
              </button>
            </div>
          </div>
        </div>
      )}

      {editingAgent && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-sky-200 dark:border-sky-800">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-sky-900 dark:text-sky-100 flex items-center gap-2">
                  <Edit2 className="w-5 h-5" />
                  编辑智能体
                </h2>
                <button
                  onClick={() => setEditingAgent(null)}
                  className="text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-200"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  智能体名称
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  智能体描述
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                  className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  智能体头像
                </label>
                <div className="flex gap-2 flex-wrap">
                  {AVATAR_OPTIONS.map((avatar) => (
                    <button
                      key={avatar}
                      onClick={() => setFormData({ ...formData, avatar })}
                      className={`w-10 h-10 rounded-lg border-2 transition-smooth ${
                        formData.avatar === avatar
                          ? 'border-sky-600 bg-sky-100 dark:bg-sky-900/30'
                          : 'border-sky-200 dark:border-sky-800 hover:border-sky-400'
                      }`}
                    >
                      {avatar}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  系统提示词
                </label>
                <textarea
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  placeholder="输入系统提示词，定义智能体的角色和行为"
                  rows={8}
                  className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono text-sm"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                    温度 (0-100)
                  </label>
                  <input
                    type="number"
                    value={formData.temperature}
                    onChange={(e) => setFormData({ ...formData, temperature: parseInt(e.target.value) })}
                    min="0"
                    max="100"
                    className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                    最大Token数
                  </label>
                  <input
                    type="number"
                    value={formData.max_tokens}
                    onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                    min="512"
                    max="8192"
                    className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                    Top P (0-100)
                  </label>
                  <input
                    type="number"
                    value={formData.top_p}
                    onChange={(e) => setFormData({ ...formData, top_p: parseInt(e.target.value) })}
                    min="0"
                    max="100"
                    className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit_is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-sky-600 rounded focus:ring-sky-500"
                />
                <label htmlFor="edit_is_active" className="text-sm text-sky-900 dark:text-sky-100">
                  启用此智能体
                </label>
              </div>
            </div>

            <div className="p-6 border-t border-sky-200 dark:border-sky-800 flex gap-3">
              <button
                onClick={() => setEditingAgent(null)}
                className="flex-1 px-4 py-2 border border-sky-200 dark:border-sky-800 text-sky-700 dark:text-sky-300 rounded-lg hover:bg-sky-50 dark:hover:bg-gray-800 transition-smooth"
              >
                取消
              </button>
              <button
                onClick={handleUpdateAgent}
                className="flex-1 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-smooth flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                保存修改
              </button>
            </div>
          </div>
        </div>
      )}

      {showChatModal && chatAgent && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-sky-200 dark:border-sky-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{chatAgent.avatar || '🤖'}</span>
                  <div>
                    <h2 className="text-xl font-bold text-sky-900 dark:text-sky-100">
                      {chatAgent.name}
                    </h2>
                    <p className="text-sm text-sky-600 dark:text-sky-400">
                      {chatAgent.description || '暂无描述'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowChatModal(false)}
                  className="text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-200"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              {chatAgent.agent_type === 'contract' && (
                <div>
                  <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                    上传合同文件
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="file"
                      id="file-upload"
                      accept=".doc,.docx,.pdf,.txt"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <label
                      htmlFor="file-upload"
                      className="flex-1 px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 hover:bg-sky-50 dark:hover:bg-gray-700 transition-smooth cursor-pointer flex items-center justify-center gap-2"
                    >
                      {uploadingFile ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          上传中...
                        </>
                      ) : uploadedFile ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          {uploadedFile.name}
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          选择文件
                        </>
                      )}
                    </label>
                  </div>
                </div>
              )}

              {(chatAgent.agent_type === 'case-analysis' || chatAgent.agent_type === 'debate' || chatAgent.agent_type === 'document') && (
                <div>
                  <button
                    onClick={() => setShowExamples(!showExamples)}
                    className="text-sm text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-200 flex items-center gap-1"
                  >
                    <Sparkles className="w-4 h-4" />
                    {showExamples ? '隐藏示例' : '查看示例'}
                  </button>
                  {showExamples && EXAMPLE_PROMPTS[chatAgent.agent_type as keyof typeof EXAMPLE_PROMPTS] && (
                    <div className="mt-2 space-y-2">
                      {EXAMPLE_PROMPTS[chatAgent.agent_type as keyof typeof EXAMPLE_PROMPTS]?.map((example, index) => (
                        <button
                          key={index}
                          onClick={() => handleExampleClick(example)}
                          className="block w-full text-left px-3 py-2 text-sm bg-sky-50 dark:bg-sky-900/20 text-sky-700 dark:text-sky-300 rounded-lg hover:bg-sky-100 dark:hover:bg-sky-900/30 transition-smooth"
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-sky-900 dark:text-sky-100 mb-2">
                  您的问题
                </label>
                <textarea
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  placeholder="输入您的问题..."
                  rows={4}
                  className="w-full px-4 py-2 border border-sky-200 dark:border-sky-800 rounded-lg bg-white dark:bg-gray-800 text-sky-900 dark:text-sky-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <button
                onClick={handleChat}
                disabled={chatLoading || !chatMessage.trim()}
                className="w-full px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-smooth disabled:cursor-not-allowed disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {chatLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    思考中...
                  </>
                ) : (
                  <>
                    <MessageSquare className="w-4 h-4" />
                    发送消息
                  </>
                )}
              </button>

              {chatResponse && (
                <div className="mt-4 p-4 bg-sky-50 dark:bg-sky-900/20 rounded-lg border border-sky-200 dark:border-sky-800">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-sky-900 dark:text-sky-100">
                      智能体回复
                    </h3>
                    {chatAgent.agent_type === 'document' && (
                      <DownloadDropdown
                        onDownloadImage={handleDownloadImage}
                        onDownloadPDF={handleDownloadPDF}
                        onDownloadWord={handleDownloadWord}
                        buttonText="导出文件"
                        buttonClassName="text-sm text-sky-600 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-200 flex items-center gap-1"
                        theme="blue"
                      />
                    )}
                  </div>
                  <p className="text-sm text-sky-700 dark:text-sky-300 whitespace-pre-wrap">
                    {chatResponse}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}