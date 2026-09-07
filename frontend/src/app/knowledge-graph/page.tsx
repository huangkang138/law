'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { FileText, Search, Filter, Plus, Trash2, Edit, RefreshCw, Database, Network, X, Save, MoreHorizontal, ChevronRight, ChevronLeft, Upload, FileUp, FileDown, Layers, Settings, HelpCircle, Box, LayoutGrid, Home, Gavel, Shield, MessageSquare } from 'lucide-react';
import dynamic from 'next/dynamic';

// 动态导入ForceGraph组件，避免SSR问题，并实现懒加载
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { 
  ssr: false, 
  loading: () => <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto mb-4"></div><p className="text-gray-600">加载3D视图...</p></div>
});
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { 
  ssr: false, 
  loading: () => <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto mb-4"></div><p className="text-gray-600">加载2D视图...</p></div>
});

// 节点类型颜色映射
const nodeTypeColors: Record<string, string> = {
  legal_article: '#3b82f6',      // 法律条款 - 蓝色
  case: '#10b981',              // 案例 - 绿色
  legal_concept: '#f59e0b',      // 法律概念 - 橙色
  legal_subject: '#8b5cf6',      // 法律主体 - 紫色
  legal_procedure: '#ec4899',    // 法律程序 - 粉色
  legal_profession: '#6366f1',   // 法律职业 - 靛蓝色
  legal_institution: '#14b8a6',  // 法律机构 - 青色
  legal_event: '#ef4444',        // 法律事件 - 红色
};

// 节点类型标签映射
const nodeTypeLabels: Record<string, string> = {
  legal_article: '法律条款',
  case: '案例',
  legal_concept: '法律概念',
  legal_subject: '法律主体',
  legal_procedure: '法律程序',
  legal_profession: '法律职业',
  legal_institution: '法律机构',
  legal_event: '法律事件',
};

// 关系类型标签映射
const relationshipTypeLabels: Record<string, string> = {
  cites: '引用',
  contains: '包含',
  involves: '涉及',
  applies_to: '适用',
  belongs_to: '属于',
  performs: '执行',
  relates_to: '相关',
  derives_from: '源自',
  references: '参考',
};

interface Node {
  id: string;
  label: string;
  type: string;
  properties: {
    content: string;
    metadata: Record<string, any>;
  };
}

interface Relationship {
  id: string;
  source: string;
  target: string;
  label: string;
  properties: {
    weight: string;
    description: string;
  };
}

interface GraphData {
  nodes: Node[];
  links: Relationship[];
}

interface Position {
  x: number;
  y: number;
}

export default function KnowledgeGraphPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const graphId = searchParams.get('id') || 'default';
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [nodeTypeFilter, setNodeTypeFilter] = useState('all');
  const [showCreateNodeDialog, setShowCreateNodeDialog] = useState(false);
  const [showCreateRelationshipDialog, setShowCreateRelationshipDialog] = useState(false);
  const [showBuildGraphDialog, setShowBuildGraphDialog] = useState(false);
  const [showEditNodeDialog, setShowEditNodeDialog] = useState(false);
  const [editNode, setEditNode] = useState<Node | null>(null);
  const [newNode, setNewNode] = useState({
    node_type: 'legal_concept',
    name: '',
    content: '',
  });
  const [newRelationship, setNewRelationship] = useState({
    source_node_id: '',
    target_node_id: '',
    relationship_type: 'relates_to',
    description: '',
  });
  const [buildText, setBuildText] = useState('');
  const [showDeleteConfirmDialog, setShowDeleteConfirmDialog] = useState(false);
  const [nodeToDelete, setNodeToDelete] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState<'success' | 'error' | 'info'>('info');
  const [showNodeDetails, setShowNodeDetails] = useState(false);
  const [nodeDetailsPosition, setNodeDetailsPosition] = useState<Position>({ x: 0, y: 0 });
  const [showFileUploadDialog, setShowFileUploadDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('3d');
  const graphContainerRef = useRef<HTMLDivElement>(null);

  // 显示toast消息
  const showToastMessage = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToastMessage(message);
    setToastType(type);
    setShowToast(true);
    
    // 3秒后自动隐藏
    setTimeout(() => {
      setShowToast(false);
    }, 3000);
  };

  // 打开删除确认对话框
  const openDeleteConfirmDialog = (nodeId: string) => {
    setNodeToDelete(nodeId);
    setShowDeleteConfirmDialog(true);
  };

  // 确认删除
  const confirmDelete = async () => {
    if (!nodeToDelete) return;
    
    try {
      const response = await fetch(`/api/knowledge-graph/nodes/${nodeToDelete}?graph_id=${graphId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSelectedNode(null);
          setShowNodeDetails(false);
          // 清除缓存
          delete graphDataCache.current[graphId];
          loadGraphData();
          showToastMessage('删除成功', 'success');
        } else {
          showToastMessage('删除失败', 'error');
        }
      } else {
        showToastMessage('删除失败', 'error');
      }
    } catch (error) {
      console.error('删除节点失败:', error);
      showToastMessage('删除失败', 'error');
    } finally {
      setShowDeleteConfirmDialog(false);
      setNodeToDelete(null);
    }
  };

  // 缓存机制
  const graphDataCache = useRef<Record<string, GraphData>>({});

  // 加载知识图谱数据
  const loadGraphData = async () => {
    // 检查缓存
    if (graphDataCache.current[graphId]) {
      setGraphData(graphDataCache.current[graphId]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/knowledge-graph/structure?graph_id=${graphId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const formattedData = {
            nodes: data.nodes,
            links: data.relationships.map((rel: Relationship) => ({
              ...rel,
              label: relationshipTypeLabels[rel.label] || rel.label
            }))
          };
          // 缓存数据
          graphDataCache.current[graphId] = formattedData;
          setGraphData(formattedData);
        }
      }
    } catch (error) {
      console.error('加载知识图谱数据失败:', error);
      showToastMessage('加载数据失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 搜索节点
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await fetch(`/api/knowledge-graph/search?q=${encodeURIComponent(searchQuery)}&graph_id=${graphId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const searchNodes = data.nodes.map((node: any) => ({
            id: node.id,
            label: node.name,
            type: node.node_type,
            properties: {
              content: node.content,
              metadata: node.metadata_info || {}
            }
          }));
          setGraphData({ nodes: searchNodes, links: [] });
          showToastMessage('搜索成功', 'success');
        } else {
          showToastMessage('搜索失败', 'error');
        }
      } else {
        showToastMessage('搜索失败', 'error');
      }
    } catch (error) {
      console.error('搜索节点失败:', error);
      showToastMessage('搜索失败', 'error');
    }
  };

  // 创建节点
  const handleCreateNode = async () => {
    try {
      const response = await fetch(`/api/knowledge-graph/nodes?graph_id=${graphId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newNode),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowCreateNodeDialog(false);
          setNewNode({ node_type: 'legal_concept', name: '', content: '' });
          // 清除缓存
          delete graphDataCache.current[graphId];
          loadGraphData();
          showToastMessage('创建节点成功', 'success');
        } else {
          showToastMessage('创建节点失败', 'error');
        }
      } else {
        showToastMessage('创建节点失败', 'error');
      }
    } catch (error) {
      console.error('创建节点失败:', error);
      showToastMessage('创建节点失败', 'error');
    }
  };

  // 编辑节点
  const handleEditNode = async () => {
    if (!editNode) return;
    
    try {
      const response = await fetch(`/api/knowledge-graph/nodes/${editNode.id}?graph_id=${graphId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: editNode.label,
          content: editNode.properties.content,
          node_type: editNode.type
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowEditNodeDialog(false);
          setEditNode(null);
          // 清除缓存
          delete graphDataCache.current[graphId];
          loadGraphData();
          showToastMessage('编辑节点成功', 'success');
        } else {
          showToastMessage('编辑节点失败', 'error');
        }
      } else {
        showToastMessage('编辑节点失败', 'error');
      }
    } catch (error) {
      console.error('编辑节点失败:', error);
      showToastMessage('编辑节点失败', 'error');
    }
  };

  // 删除节点 - 现在使用确认对话框
  const handleDeleteNode = (nodeId: string) => {
    openDeleteConfirmDialog(nodeId);
  };

  // 创建关系
  const handleCreateRelationship = async () => {
    try {
      const response = await fetch(`/api/knowledge-graph/relationships?graph_id=${graphId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newRelationship),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowCreateRelationshipDialog(false);
          setNewRelationship({ source_node_id: '', target_node_id: '', relationship_type: 'relates_to', description: '' });
          // 清除缓存
          delete graphDataCache.current[graphId];
          loadGraphData();
          showToastMessage('创建关系成功', 'success');
        } else {
          showToastMessage('创建关系失败', 'error');
        }
      } else {
        showToastMessage('创建关系失败', 'error');
      }
    } catch (error) {
      console.error('创建关系失败:', error);
      showToastMessage('创建关系失败', 'error');
    }
  };

  // 构建知识图谱
  const handleBuildGraph = async () => {
    try {
      const response = await fetch(`/api/knowledge-graph/build?graph_id=${graphId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: buildText }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowBuildGraphDialog(false);
          setBuildText('');
          // 清除缓存
          delete graphDataCache.current[graphId];
          loadGraphData();
          showToastMessage('构建图谱成功', 'success');
        } else {
          showToastMessage('构建图谱失败', 'error');
        }
      } else {
        showToastMessage('构建图谱失败', 'error');
      }
    } catch (error) {
      console.error('构建知识图谱失败:', error);
      showToastMessage('构建图谱失败', 'error');
    }
  };

  // 处理文件选择
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // 上传文件并分析
  const handleFileUpload = async () => {
    if (!selectedFile) {
      showToastMessage('请选择文件', 'error');
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`/api/knowledge-graph/upload?graph_id=${graphId}`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowFileUploadDialog(false);
          setSelectedFile(null);
          // 清除缓存
          delete graphDataCache.current[graphId];
          loadGraphData();
          showToastMessage('文件上传成功并分析完成', 'success');
        } else {
          showToastMessage('文件分析失败', 'error');
        }
      } else {
        showToastMessage('文件上传失败', 'error');
      }
    } catch (error) {
      console.error('文件上传失败:', error);
      showToastMessage('文件上传失败', 'error');
    } finally {
      setUploading(false);
    }
  };

  // 打开编辑对话框
  const openEditDialog = () => {
    if (selectedNode) {
      setEditNode(selectedNode);
      setShowEditNodeDialog(true);
    }
  };

  // 处理节点点击
  const handleNodeClick = (node: Node, event: any) => {
    setSelectedNode(node);
    setShowNodeDetails(true);
    
    // 计算节点详情的位置
    if (graphContainerRef.current) {
      const rect = graphContainerRef.current.getBoundingClientRect();
      const x = event.clientX - rect.left + 20; // 偏移20px
      const y = event.clientY - rect.top + 20;
      setNodeDetailsPosition({ x, y });
    }
  };

  // 过滤节点
  const filteredNodes = nodeTypeFilter === 'all' 
    ? graphData.nodes 
    : graphData.nodes.filter(node => node.type === nodeTypeFilter);

  // 过滤关系 - 确保source和target是节点ID字符串
  const filteredLinks = graphData.links
    .map(link => ({
      ...link,
      source: typeof link.source === 'object' ? (link.source as any).id : link.source,
      target: typeof link.target === 'object' ? (link.target as any).id : link.target
    }))
    .filter(link => 
      filteredNodes.some(node => node.id === link.source) && 
      filteredNodes.some(node => node.id === link.target)
    );

  // 为ForceGraph准备数据副本
  const graphDataForRender = {
    nodes: filteredNodes.map(n => ({ ...n })),
    links: filteredLinks.map(l => ({ ...l }))
  };

  // 初始化加载数据
  useEffect(() => {
    loadGraphData();
  }, []);

  return (
    <div className="h-[calc(100vh-80px)] bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground relative overflow-hidden flex flex-col">
      
      {/* 星空光晕效果 */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      {/* 顶部标题栏 */}
      <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-sky-200 dark:border-sky-900/30 px-4 py-4 shadow-sm flex-shrink-0">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Network className="text-sky-600" size={24} />
            <div>
              <h1 className="text-xl font-bold text-sky-800 dark:text-sky-300">法律知识图谱</h1>
              <p className="text-xs text-gray-600 dark:text-gray-400">可视化法律知识网络，智能分析法律关系</p>
            </div>
          </div>
          <button 
            onClick={() => router.push('/')} 
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-sky-700 dark:text-sky-300 hover:bg-sky-100 dark:hover:bg-sky-900/20 rounded-lg transition-colors border border-sky-200 dark:border-sky-800"
          >
            <ChevronLeft size={14} />
            返回首页
          </button>
        </div>
      </div>

      {/* 工具栏 */}
      <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-sm border-b border-sky-200/50 dark:border-sky-900/20 px-4 py-4 flex-shrink-0">
        <div className="container mx-auto flex flex-wrap items-center justify-between gap-2">
          {/* 左侧：操作按钮 */}
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setShowCreateNodeDialog(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-sky-500 to-blue-500 text-white rounded-lg transition-all hover:shadow-md hover:scale-105 text-sm font-medium"
            >
              <Plus size={14} />
              新增节点
            </button>
            <button 
              onClick={() => setShowCreateRelationshipDialog(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-700 text-white rounded-lg transition-all hover:shadow-md hover:scale-105 text-sm font-medium"
            >
              <Network size={14} />
              新增关系
            </button>
            <button 
              onClick={() => setShowBuildGraphDialog(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-sky-500 to-indigo-700 text-white rounded-lg transition-all hover:shadow-md hover:scale-105 text-sm font-medium"
            >
              <Database size={14} />
              构建图谱
            </button>
            <button 
              onClick={() => router.push('/settings')}
              className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-lg transition-all hover:shadow-md hover:scale-105 text-sm font-medium"
            >
              <Settings size={14} />
              设置
            </button>
            <button 
              onClick={() => setShowFileUploadDialog(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-700 text-white rounded-lg transition-all hover:shadow-md hover:scale-105 text-sm font-medium"
            >
              <Upload size={14} />
              上传分析
            </button>
          </div>

          {/* 右侧：搜索、筛选、视图切换 */}
          <div className="flex items-center gap-2">
            {/* 搜索框 */}
            <div className="flex items-center gap-0 bg-sky-50 dark:bg-gray-800 rounded-lg border border-sky-200 dark:border-sky-800 overflow-hidden">
              <div className="flex items-center gap-2 px-3 py-2">
                <Search size={16} className="text-sky-700 dark:text-sky-400" />
                <input
                  type="text"
                  placeholder="搜索节点..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-transparent border-none focus:outline-none text-sm w-40 text-gray-800 dark:text-gray-200"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
              <button
                onClick={handleSearch}
                className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white text-sm font-medium transition-colors"
              >
                搜索
              </button>
            </div>

            {/* 过滤器 */}
            <select 
              value={nodeTypeFilter} 
              onChange={(e) => setNodeTypeFilter(e.target.value)}
              className="bg-sky-50 dark:bg-gray-800 border border-sky-200 dark:border-sky-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
            >
              <option value="all">全部类型</option>
              <option value="legal_article">法律条款</option>
              <option value="case">案例</option>
              <option value="legal_concept">法律概念</option>
              <option value="legal_subject">法律主体</option>
              <option value="legal_procedure">法律程序</option>
              <option value="legal_profession">法律职业</option>
              <option value="legal_institution">法律机构</option>
              <option value="legal_event">法律事件</option>
            </select>

            {/* 视图切换 */}
            <div className="flex items-center bg-sky-100 dark:bg-gray-800 rounded-lg p-0.5">
              <button 
                onClick={() => setViewMode('2d')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === '2d' ? 'bg-white dark:bg-gray-700 text-sky-700 dark:text-sky-300 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-sky-700 dark:hover:text-sky-300'}`}
                title="2D视图"
              >
                <LayoutGrid size={14} />
                2D
              </button>
              <button 
                onClick={() => setViewMode('3d')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === '3d' ? 'bg-white dark:bg-gray-700 text-sky-700 dark:text-sky-300 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-sky-700 dark:hover:text-sky-300'}`}
                title="3D视图"
              >
                <Box size={14} />
                3D
              </button>
            </div>

            {/* 刷新按钮 */}
            <button 
              onClick={loadGraphData} 
              className="p-2 rounded-lg bg-sky-100 dark:bg-gray-800 hover:bg-sky-200 dark:hover:bg-gray-700 transition-colors"
              title="刷新"
            >
              <RefreshCw size={16} className="text-sky-700 dark:text-sky-400" />
            </button>
          </div>
        </div>
      </div>

      {/* 主内容区域 */}
      <div className="flex-1 px-4 pb-4 relative overflow-hidden">
        {/* 图谱可视化区域 */}
        <div ref={graphContainerRef} className="relative w-full h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border border-sky-200 dark:border-sky-900/30 rounded-2xl shadow-lg overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto mb-4"></div>
                <p className="text-gray-600">加载中...</p>
              </div>
            </div>
          ) : viewMode === '2d' ? (
            <div style={{ width: '100%', height: '100%', backgroundColor: '#ffffff' }}>
              <ForceGraph2D
                graphData={graphDataForRender}
                nodeId="id"
                linkSource="source"
                linkTarget="target"
                nodeAutoColorBy="type"
                nodeColor={(node: any) => nodeTypeColors[node.type] || '#9ca3af'}
                nodeLabel={(node: any) => node.label}
                linkLabel={(link: any) => link.label}
                onNodeClick={(node: any) => {
                  setSelectedNode(node);
                  setShowNodeDetails(true);
                  setNodeDetailsPosition({ x: 400, y: 300 });
                }}
                onBackgroundClick={() => {
                  setSelectedNode(null);
                  setShowNodeDetails(false);
                }}
                nodeCanvasObject={(node: any, ctx: any, globalScale: any) => {
                  const label = node.label;
                  const fontSize = 12 / globalScale;
                  ctx.font = `${fontSize}px Sans-Serif`;
                  const color = nodeTypeColors[node.type] || '#9ca3af';
                  
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false);
                  ctx.fillStyle = color;
                  ctx.fill();
                  ctx.strokeStyle = '#ffffff';
                  ctx.lineWidth = 2;
                  ctx.stroke();
                  
                  ctx.fillStyle = '#333333';
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText(label, node.x, node.y + 16);
                }}
                linkWidth={2}
                linkColor={() => '#999999'}
                linkDirectionalArrowLength={6}
                linkDirectionalArrowRelPos={0.9}
                linkDirectionalArrowColor={() => '#999999'}
                enableNodeDrag={true}
                enablePanInteraction={true}
                d3AlphaDecay={0.02}
                d3VelocityDecay={0.3}
                warmupTicks={200}
              />
            </div>
          ) : (
            <div style={{ width: '100%', height: '100%', backgroundColor: '#ffffff' }}>
              <ForceGraph3D
                graphData={graphDataForRender}
                nodeAutoColorBy="type"
                nodeColor={(node: any) => nodeTypeColors[node.type] || '#9ca3af'}
                nodeLabel={(node: any) => node.label}
                linkLabel={(link: any) => link.label}
                onNodeClick={(node: any, event: any) => handleNodeClick(node, event)}
                onBackgroundClick={() => {
                  setSelectedNode(null);
                  setShowNodeDetails(false);
                }}
                nodeOpacity={0.9}
                linkWidth={2}
                linkOpacity={0.7}
                linkDirectionalArrowLength={6}
                linkDirectionalArrowRelPos={1}
                enableNodeDrag={true}
                enableNavigationControls={true}
                enablePointerInteraction={true}
                backgroundColor="#ffffff"
              />
            </div>
          )}
        </div>

        {/* 统计信息 */}
        <div className="absolute bottom-4 left-4 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-xl shadow-lg border border-sky-200 dark:border-sky-900/30 p-4 z-30">
          <div className="flex gap-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-sky-800 dark:text-sky-300">{graphData.nodes.length}</div>
              <div className="text-xs text-sky-600 dark:text-sky-400 mt-1">节点数量</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-sky-800 dark:text-sky-300">{graphData.links.length}</div>
              <div className="text-xs text-sky-600 dark:text-sky-400 mt-1">关系数量</div>
            </div>
          </div>
        </div>

        {/* 控制提示 */}
        <div className="absolute bottom-4 right-4 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-xl shadow-lg border border-sky-200 dark:border-sky-900/30 p-4 text-xs text-gray-600 dark:text-gray-400 z-30">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <span className="text-sky-600 dark:text-sky-400">🔍</span>
              <span>鼠标滚轮：缩放</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sky-600 dark:text-sky-400">🖱️</span>
              <span>拖拽：移动</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sky-600 dark:text-sky-400">📌</span>
              <span>点击：选择</span>
            </div>
          </div>
        </div>

        {/* 节点详情卡片 - 显示在节点旁边 */}
        {selectedNode && showNodeDetails && (
          <div 
            className="absolute bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-2xl shadow-xl border border-sky-200 dark:border-sky-900/30 p-6 w-96 max-h-[80vh] overflow-y-auto z-20"
            style={{
              top: `${nodeDetailsPosition.y}px`,
              left: `${nodeDetailsPosition.x}px`,
              transform: 'translate(0, -50%)',
              pointerEvents: 'auto'
            }}
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-lg font-bold text-sky-800 dark:text-sky-300">节点详情</h2>
              <button 
                onClick={() => setShowNodeDetails(false)}
                className="text-gray-400 hover:text-sky-600 dark:hover:text-sky-400 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            {/* 节点头部 */}
            <div className="mb-6">
              <span 
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium mb-2"
                style={{ backgroundColor: nodeTypeColors[selectedNode.type] + '20', color: nodeTypeColors[selectedNode.type] }}
              >
                {nodeTypeLabels[selectedNode.type] || selectedNode.type}
              </span>
              <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200">{selectedNode.label}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">ID: {selectedNode.id}</p>
            </div>

            {/* 节点内容 */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-sky-800 dark:text-sky-400 mb-2">内容</h4>
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                {selectedNode.properties.content || '无内容'}
              </p>
            </div>

            {/* 元数据 */}
            {Object.entries(selectedNode.properties.metadata || {}).length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-sky-800 dark:text-sky-400 mb-2">元数据</h4>
                <div className="bg-sky-50 dark:bg-gray-800 rounded-lg p-3 border border-sky-200 dark:border-sky-800">
                  <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {JSON.stringify(selectedNode.properties.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex gap-3 pt-4 border-t border-sky-200 dark:border-sky-900/30">
              <button 
                onClick={openEditDialog}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-sky-500 to-blue-500 text-white rounded-lg transition-all hover:shadow-lg hover:scale-105 text-sm font-medium"
              >
                <Edit size={16} />
                编辑
              </button>
              <button 
                onClick={() => handleDeleteNode(selectedNode.id)}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-700 text-white rounded-lg transition-all hover:shadow-lg hover:scale-105 text-sm font-medium"
              >
                <Trash2 size={16} />
                删除
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 新增节点对话框 */}
      {showCreateNodeDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-2xl shadow-xl w-full max-w-md mx-4 border border-sky-200 dark:border-sky-900/30">
            <div className="p-6 border-b border-sky-200 dark:border-sky-900/30 flex justify-between items-center">
              <h2 className="text-lg font-bold text-sky-800 dark:text-sky-300">新增知识节点</h2>
              <button onClick={() => setShowCreateNodeDialog(false)} className="text-gray-400 hover:text-sky-600 dark:hover:text-sky-400 transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">节点类型</label>
                <select
                  value={newNode.node_type}
                  onChange={(e) => setNewNode({ ...newNode, node_type: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                >
                  <option value="legal_article">法律条款</option>
                  <option value="case">案例</option>
                  <option value="legal_concept">法律概念</option>
                  <option value="legal_subject">法律主体</option>
                  <option value="legal_procedure">法律程序</option>
                  <option value="legal_profession">法律职业</option>
                  <option value="legal_institution">法律机构</option>
                  <option value="legal_event">法律事件</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">节点名称</label>
                <input
                  type="text"
                  value={newNode.name}
                  onChange={(e) => setNewNode({ ...newNode, name: e.target.value })}
                  placeholder="输入节点名称"
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">节点内容</label>
                <textarea
                  value={newNode.content}
                  onChange={(e) => setNewNode({ ...newNode, content: e.target.value })}
                  placeholder="输入节点内容"
                  rows={4}
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                />
              </div>
            </div>
            <div className="p-6 border-t border-sky-200 dark:border-sky-900/30 flex justify-end gap-3">
              <button 
                onClick={() => setShowCreateNodeDialog(false)}
                className="px-5 py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition-colors font-medium"
              >
                取消
              </button>
              <button 
                onClick={handleCreateNode}
                className="px-5 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-500 text-white rounded-lg transition-all hover:shadow-lg hover:scale-105 font-medium"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑节点对话框 */}
      {showEditNodeDialog && editNode && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-2xl shadow-xl w-full max-w-md mx-4 border border-sky-200 dark:border-sky-900/30">
            <div className="p-6 border-b border-sky-200 dark:border-sky-900/30 flex justify-between items-center">
              <h2 className="text-lg font-bold text-sky-800 dark:text-sky-300">编辑知识节点</h2>
              <button onClick={() => setShowEditNodeDialog(false)} className="text-gray-400 hover:text-sky-600 dark:hover:text-sky-400 transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">节点类型</label>
                <select
                  value={editNode.type}
                  onChange={(e) => setEditNode({ ...editNode, type: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                >
                  <option value="legal_article">法律条款</option>
                  <option value="case">案例</option>
                  <option value="legal_concept">法律概念</option>
                  <option value="legal_subject">法律主体</option>
                  <option value="legal_procedure">法律程序</option>
                  <option value="legal_profession">法律职业</option>
                  <option value="legal_institution">法律机构</option>
                  <option value="legal_event">法律事件</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">节点名称</label>
                <input
                  type="text"
                  value={editNode.label}
                  onChange={(e) => setEditNode({ ...editNode, label: e.target.value })}
                  placeholder="输入节点名称"
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">节点内容</label>
                <textarea
                  value={editNode.properties.content}
                  onChange={(e) => setEditNode({ 
                    ...editNode, 
                    properties: { ...editNode.properties, content: e.target.value }
                  })}
                  placeholder="输入节点内容"
                  rows={4}
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                />
              </div>
            </div>
            <div className="p-6 border-t border-sky-200 dark:border-sky-900/30 flex justify-end gap-3">
              <button 
                onClick={() => setShowEditNodeDialog(false)}
                className="px-5 py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition-colors font-medium"
              >
                取消
              </button>
              <button 
                onClick={handleEditNode}
                className="px-5 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-500 text-white rounded-lg transition-all hover:shadow-lg hover:scale-105 font-medium"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 新增关系对话框 */}
      {showCreateRelationshipDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-2xl shadow-xl w-full max-w-md mx-4 border border-sky-200 dark:border-sky-900/30">
            <div className="p-6 border-b border-sky-200 dark:border-sky-900/30 flex justify-between items-center">
              <h2 className="text-lg font-bold text-sky-800 dark:text-sky-300">新增知识关系</h2>
              <button onClick={() => setShowCreateRelationshipDialog(false)} className="text-gray-400 hover:text-sky-600 dark:hover:text-sky-400 transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">源节点</label>
                <select
                  value={newRelationship.source_node_id}
                  onChange={(e) => setNewRelationship({ ...newRelationship, source_node_id: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                >
                  <option value="">选择源节点</option>
                  {graphData.nodes.map(node => (
                    <option key={node.id} value={node.id}>
                      {node.label} ({node.type})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">目标节点</label>
                <select
                  value={newRelationship.target_node_id}
                  onChange={(e) => setNewRelationship({ ...newRelationship, target_node_id: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                >
                  <option value="">选择目标节点</option>
                  {graphData.nodes.map(node => (
                    <option key={node.id} value={node.id}>
                      {node.label} ({node.type})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">关系类型</label>
                <select
                  value={newRelationship.relationship_type}
                  onChange={(e) => setNewRelationship({ ...newRelationship, relationship_type: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                >
                  <option value="cites">引用</option>
                  <option value="contains">包含</option>
                  <option value="involves">涉及</option>
                  <option value="applies_to">适用</option>
                  <option value="belongs_to">属于</option>
                  <option value="performs">执行</option>
                  <option value="relates_to">相关</option>
                  <option value="derives_from">源自</option>
                  <option value="references">参考</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-sky-800 dark:text-sky-400 mb-2">关系描述</label>
                <textarea
                  value={newRelationship.description}
                  onChange={(e) => setNewRelationship({ ...newRelationship, description: e.target.value })}
                  placeholder="输入关系描述"
                  rows={3}
                  className="w-full px-4 py-3 rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500 text-gray-800 dark:text-gray-200"
                />
              </div>
            </div>
            <div className="p-6 border-t border-sky-200 dark:border-sky-900/30 flex justify-end gap-3">
              <button 
                onClick={() => setShowCreateRelationshipDialog(false)}
                className="px-5 py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition-colors font-medium"
              >
                取消
              </button>
              <button 
                onClick={handleCreateRelationship}
                className="px-5 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-500 text-white rounded-lg transition-all hover:shadow-lg hover:scale-105 font-medium"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 构建图谱对话框 */}
      {showBuildGraphDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg mx-4 border border-gray-200">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">构建知识图谱</h2>
              <button onClick={() => setShowBuildGraphDialog(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">法律文本</label>
                <textarea
                  value={buildText}
                  onChange={(e) => setBuildText(e.target.value)}
                  placeholder="输入法律文本，系统将自动提取实体和关系"
                  rows={8}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end gap-2">
              <button 
                onClick={() => setShowBuildGraphDialog(false)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
              >
                取消
              </button>
              <button 
                onClick={handleBuildGraph}
                className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors"
              >
                构建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 文件上传对话框 */}
      {showFileUploadDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md mx-4 border border-gray-200">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">上传文件分析</h2>
              <button onClick={() => setShowFileUploadDialog(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">选择文件</label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  {selectedFile ? (
                    <div className="flex items-center justify-center gap-2">
                      <FileUp size={24} className="text-purple-600" />
                      <span className="text-sm text-gray-700">{selectedFile.name}</span>
                    </div>
                  ) : (
                    <label className="cursor-pointer">
                      <input
                        type="file"
                        accept=".txt,.doc,.docx,.pdf"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                      <div className="flex flex-col items-center gap-2">
                        <Upload size={32} className="text-gray-400" />
                        <p className="text-sm text-gray-600">点击或拖拽文件到此处</p>
                        <p className="text-xs text-gray-500">支持 .txt, .doc, .docx, .pdf 格式</p>
                      </div>
                    </label>
                  )}
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end gap-2">
              <button 
                onClick={() => setShowFileUploadDialog(false)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
                disabled={uploading}
              >
                取消
              </button>
              <button 
                onClick={handleFileUpload}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
                disabled={!selectedFile || uploading}
              >
                {uploading ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    上传中...
                  </div>
                ) : (
                  <span>上传分析</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 删除确认对话框 */}
      {showDeleteConfirmDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md mx-4 border border-gray-200">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">确认删除</h2>
              <button onClick={() => setShowDeleteConfirmDialog(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-gray-700">确定要删除这个节点吗？此操作不可撤销。</p>
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end gap-2">
              <button 
                onClick={() => setShowDeleteConfirmDialog(false)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
              >
                取消
              </button>
              <button 
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast消息组件 */}
      {showToast && (
        <div 
          className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 transition-all duration-300 ${toastType === 'success' ? 'bg-green-500 text-white' : toastType === 'error' ? 'bg-red-500 text-white' : 'bg-blue-500 text-white'}`}
        >
          <div className="text-lg">
            {toastType === 'success' ? '✅' : toastType === 'error' ? '❌' : 'ℹ️'}
          </div>
          <span className="font-medium">{toastMessage}</span>
        </div>
      )}
    </div>
  );
}