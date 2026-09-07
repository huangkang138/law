'use client';

import { useState, useEffect, useRef } from 'react';
import { Plus, Database, Search, Edit, Trash2, ChevronLeft, ChevronRight, X, CheckSquare } from 'lucide-react';
import Link from 'next/link';
import { useDataCache } from '@/hooks/useDataCache';

interface Graph {
  id: string;
  name: string;
  description: string;
  node_count: number;
  created_at: string;
}

export default function KnowledgeGraphsPage() {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newGraph, setNewGraph] = useState({ name: '', description: '' });
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState<'success' | 'error' | 'info'>('info');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showBatchDeleteDialog, setShowBatchDeleteDialog] = useState(false);
  const [batchMode, setBatchMode] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingGraph, setEditingGraph] = useState<Graph | null>(null);
  
  // 数据缓存
  const { getCachedData, setCachedData, clearCache } = useDataCache<Graph[]>('knowledge-graphs-list');

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

  // 加载图谱列表
  const loadGraphs = async () => {
    // 检查缓存
    const cached = getCachedData();
    if (cached) {
      setGraphs(cached);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/knowledge-graphs');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setGraphs(data.graphs || []);
          // 缓存数据
          setCachedData(data.graphs || []);
        }
      }
    } catch (error) {
      console.error('加载图谱列表失败:', error);
      showToastMessage('加载失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 创建图谱
  const handleCreateGraph = async () => {
    if (!newGraph.name.trim()) {
      showToastMessage('请输入图谱名称', 'error');
      return;
    }

    try {
      const response = await fetch('/api/knowledge-graphs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newGraph),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowCreateDialog(false);
          setNewGraph({ name: '', description: '' });
          // 清除缓存
          clearCache();
          loadGraphs();
          showToastMessage('创建成功', 'success');
        } else {
          showToastMessage('创建失败', 'error');
        }
      } else {
        showToastMessage('创建失败', 'error');
      }
    } catch (error) {
      console.error('创建图谱失败:', error);
      showToastMessage('创建失败', 'error');
    }
  };

  // 打开编辑对话框
  const openEditDialog = (graph: Graph) => {
    setEditingGraph(graph);
    setShowEditDialog(true);
  };

  // 编辑图谱
  const handleEditGraph = async () => {
    if (!editingGraph || !editingGraph.name.trim()) {
      showToastMessage('请输入图谱名称', 'error');
      return;
    }

    try {
      const response = await fetch(`/api/knowledge-graphs/${editingGraph.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: editingGraph.name,
          description: editingGraph.description,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowEditDialog(false);
          setEditingGraph(null);
          // 清除缓存
          clearCache();
          loadGraphs();
          showToastMessage('更新成功', 'success');
        } else {
          showToastMessage(data.error || '更新失败', 'error');
        }
      } else {
        showToastMessage('更新失败', 'error');
      }
    } catch (error) {
      console.error('更新图谱失败:', error);
      showToastMessage('更新失败', 'error');
    }
  };

  // 删除图谱
  const handleDeleteGraph = async (graphId: string) => {
    if (!confirm('确定要删除这个图谱吗？')) {
      return;
    }

    try {
      const response = await fetch(`/api/knowledge-graphs/${graphId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          // 清除缓存
          clearCache();
          loadGraphs();
          showToastMessage('删除成功', 'success');
        } else {
          showToastMessage(data.error || '删除失败', 'error');
        }
      } else {
        showToastMessage('删除失败', 'error');
      }
    } catch (error) {
      console.error('删除图谱失败:', error);
      showToastMessage('删除失败', 'error');
    }
  };

  // 批量删除图谱
  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) {
      showToastMessage('请选择要删除的图谱', 'error');
      return;
    }

    try {
      const response = await fetch('/api/knowledge-graphs/batch-delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ graph_ids: Array.from(selectedIds) }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowBatchDeleteDialog(false);
          setSelectedIds(new Set());
          loadGraphs();
          showToastMessage(data.message, 'success');
        } else {
          showToastMessage(data.error || '批量删除失败', 'error');
        }
      } else {
        showToastMessage('批量删除失败', 'error');
      }
    } catch (error) {
      console.error('批量删除图谱失败:', error);
      showToastMessage('批量删除失败', 'error');
    }
  };

  // 全选/取消全选
  const handleSelectAll = () => {
    if (selectedIds.size === currentGraphs.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(currentGraphs.map(g => g.id)));
    }
  };

  // 选择/取消选择单个图谱
  const handleSelectOne = (id: string) => {
    const newSelectedIds = new Set(selectedIds);
    if (newSelectedIds.has(id)) {
      newSelectedIds.delete(id);
    } else {
      newSelectedIds.add(id);
    }
    setSelectedIds(newSelectedIds);
  };

  // 计算分页
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentGraphs = graphs.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(graphs.length / itemsPerPage);

  // 初始化加载数据
  useEffect(() => {
    loadGraphs();
  }, []);

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 via-violet-50 to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* 顶部工具栏 */}
      <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-violet-200 dark:border-violet-900/30 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="text-violet-600" size={28} />
            <h1 className="text-2xl font-bold text-slate-800 dark:text-violet-300">法律图谱管理</h1>
          </div>
          
          <button 
            onClick={() => setShowCreateDialog(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700 text-white rounded-lg transition-all text-sm font-medium shadow-md hover:shadow-lg"
          >
            <Plus size={16} />
            创建图谱
          </button>
        </div>
      </div>

      {/* 主内容区域 */}
      <div className="flex-1 overflow-auto p-6">
        {/* 工具栏 */}
        <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2 bg-white/90 dark:bg-slate-800/90 border border-violet-200 dark:border-violet-800/50 rounded-lg px-4 py-2 w-80 shadow-sm">
              <Search size={18} className="text-violet-500" />
              <input
                type="text"
                placeholder="搜索图谱..."
                className="bg-transparent border-none focus:outline-none text-sm w-full text-slate-800 dark:text-slate-200"
              />
            </div>
            {batchMode ? (
              <>
                <button 
                  onClick={() => setShowBatchDeleteDialog(true)}
                  disabled={selectedIds.size === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                >
                  <Trash2 size={16} />
                  删除选中 ({selectedIds.size})
                </button>
                <button 
                  onClick={() => { setBatchMode(false); setSelectedIds(new Set()); }}
                  className="flex items-center gap-2 px-4 py-2 bg-white/90 dark:bg-slate-800/90 border border-violet-200 dark:border-violet-800/50 hover:bg-violet-50 dark:hover:bg-violet-900/20 text-slate-700 dark:text-slate-300 rounded-lg transition-colors text-sm font-medium shadow-sm"
                >
                  取消
                </button>
              </>
            ) : (
              <button 
                onClick={() => setBatchMode(true)}
                className="flex items-center gap-2 px-4 py-2 bg-white/90 dark:bg-slate-800/90 border border-violet-200 dark:border-violet-800/50 hover:bg-violet-50 dark:hover:bg-violet-900/20 text-slate-700 dark:text-slate-300 rounded-lg transition-colors text-sm font-medium shadow-sm"
              >
                <CheckSquare size={16} className="text-violet-500" />
                批量操作
              </button>
            )}
          </div>
        </div>

        {/* 图谱列表 */}
        <div className="bg-white/90 dark:bg-slate-800/90 backdrop-blur-md rounded-xl shadow-md border border-violet-200/50 dark:border-violet-800/30 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead className="bg-gradient-to-r from-violet-50 to-blue-50 dark:from-violet-900/20 dark:to-blue-900/20 border-b border-violet-200 dark:border-violet-800/30">
                <tr>
                  {batchMode && (
                    <th className="px-4 py-4 text-center text-xs font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider w-12">
                      <input
                        type="checkbox"
                        checked={currentGraphs.length > 0 && selectedIds.size === currentGraphs.length}
                        onChange={handleSelectAll}
                        className="w-4 h-4 rounded border-violet-300 text-violet-600 focus:ring-violet-500 mx-auto"
                      />
                    </th>
                  )}
                  <th className="px-6 py-4 text-left text-xs font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider">
                    图谱名称
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider">
                    描述
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider">
                    节点数
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider">
                    创建时间
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-violet-100 dark:divide-violet-800/30">
                {loading ? (
                  <tr>
                    <td colSpan={batchMode ? 6 : 5} className="px-6 py-12 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600 mx-auto mb-4"></div>
                      <p className="text-slate-600 dark:text-slate-400">加载中...</p>
                    </td>
                  </tr>
                ) : graphs.length === 0 ? (
                  <tr>
                    <td colSpan={batchMode ? 6 : 5} className="px-6 py-12 text-center">
                      <p className="text-slate-500 dark:text-slate-400">暂无数据</p>
                    </td>
                  </tr>
                ) : (
                  currentGraphs.map((graph) => (
                    <tr key={graph.id} className={`hover:bg-violet-50/50 dark:hover:bg-violet-900/10 transition-colors ${selectedIds.has(graph.id) ? 'bg-violet-100 dark:bg-violet-900/20' : ''}`}>
                      {batchMode && (
                        <td className="px-4 py-4 text-center whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedIds.has(graph.id)}
                            onChange={() => handleSelectOne(graph.id)}
                            className="w-4 h-4 rounded border-violet-300 text-violet-600 focus:ring-violet-500 mx-auto"
                          />
                        </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link 
                          href={`/knowledge-graph?id=${graph.id}`}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium transition-colors"
                        >
                          {graph.name}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-slate-600 dark:text-slate-400 text-sm">{graph.description || '无描述'}</p>
                      </td>
                      <td className="px-6 py-4 text-center whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-violet-100 dark:bg-violet-900/30 text-violet-800 dark:text-violet-300">
                          {graph.node_count}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center whitespace-nowrap">
                        <span className="text-slate-500 dark:text-slate-400 text-sm">
                          {new Date(graph.created_at).toLocaleString()}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center whitespace-nowrap text-sm font-medium">
                        <div className="flex justify-center gap-3">
                          <Link 
                            href={`/knowledge-graph?id=${graph.id}`}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                          >
                            查看
                          </Link>
                          <button 
                            onClick={() => openEditDialog(graph)}
                            className="text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-300 transition-colors"
                          >
                            编辑
                          </button>
                          <button 
                            onClick={() => handleDeleteGraph(graph.id)}
                            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 transition-colors"
                          >
                            删除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* 分页 */}
          {!loading && graphs.length > 0 && (
            <div className="px-6 py-4 border-t border-violet-200/50 dark:border-violet-800/30 flex flex-wrap items-center justify-between gap-4">
              <div className="text-sm text-slate-600 dark:text-slate-400">
                共 {graphs.length} 条
              </div>
              <div className="flex items-center gap-3">
                <select 
                  className="border border-violet-200 dark:border-violet-800/50 rounded-lg px-3 py-2 text-sm bg-white/90 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  value={itemsPerPage}
                  onChange={(e) => {/* 实现每页条数选择 */}}
                >
                  <option value="10">10条/页</option>
                  <option value="20">20条/页</option>
                  <option value="50">50条/页</option>
                </select>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="p-2 rounded-lg bg-white/90 dark:bg-slate-800/90 border border-violet-200/50 dark:border-violet-800/30 hover:bg-violet-50 dark:hover:bg-violet-900/20 disabled:opacity-50 transition-colors"
                  >
                    <ChevronLeft size={16} className="text-violet-600 dark:text-violet-400" />
                  </button>
                  <span className="px-3 py-2 text-sm font-medium bg-white/90 dark:bg-slate-800/90 border border-violet-200/50 dark:border-violet-800/30 rounded-lg">{currentPage}</span>
                  <button 
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="p-2 rounded-lg bg-white/90 dark:bg-slate-800/90 border border-violet-200/50 dark:border-violet-800/30 hover:bg-violet-50 dark:hover:bg-violet-900/20 disabled:opacity-50 transition-colors"
                  >
                    <ChevronRight size={16} className="text-violet-600 dark:text-violet-400" />
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">前往</span>
                  <input 
                    type="number" 
                    min="1" 
                    max={totalPages}
                    value={currentPage}
                    onChange={(e) => {
                      const page = parseInt(e.target.value);
                      if (page >= 1 && page <= totalPages) {
                        setCurrentPage(page);
                      }
                    }}
                    className="w-16 border border-violet-200/50 dark:border-violet-800/30 rounded-lg px-3 py-2 text-sm bg-white/90 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                  <span className="text-sm text-slate-600 dark:text-slate-400">页</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 创建图谱对话框 */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-xl shadow-xl w-full max-w-md mx-4 border border-violet-200 dark:border-violet-800/30">
            <div className="p-6 border-b border-violet-200/50 dark:border-violet-800/30 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-slate-800 dark:text-violet-300">创建知识图谱</h2>
              <button onClick={() => setShowCreateDialog(false)} className="text-slate-500 dark:text-slate-400 hover:text-violet-600 dark:hover:text-violet-400">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">图谱名称</label>
                <input
                  type="text"
                  value={newGraph.name}
                  onChange={(e) => setNewGraph({ ...newGraph, name: e.target.value })}
                  placeholder="输入图谱名称"
                  className="w-full px-4 py-3 rounded-lg border border-violet-200 dark:border-violet-800/50 bg-white/90 dark:bg-slate-700/90 focus:outline-none focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-slate-200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">图谱描述</label>
                <textarea
                  value={newGraph.description}
                  onChange={(e) => setNewGraph({ ...newGraph, description: e.target.value })}
                  placeholder="输入图谱描述"
                  rows={4}
                  className="w-full px-4 py-3 rounded-lg border border-violet-200 dark:border-violet-800/50 bg-white/90 dark:bg-slate-700/90 focus:outline-none focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-slate-200"
                />
              </div>
            </div>
            <div className="p-6 border-t border-violet-200/50 dark:border-violet-800/30 flex justify-end gap-3">
              <button 
                onClick={() => setShowCreateDialog(false)}
                className="px-4 py-2.5 bg-white/90 dark:bg-slate-800/90 border border-violet-200 dark:border-violet-800/50 hover:bg-violet-50 dark:hover:bg-violet-900/20 text-slate-700 dark:text-slate-300 rounded-lg transition-colors"
              >
                取消
              </button>
              <button 
                onClick={handleCreateGraph}
                className="px-4 py-2.5 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700 text-white rounded-lg transition-colors shadow-md"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑图谱对话框 */}
      {showEditDialog && editingGraph && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-xl shadow-xl w-full max-w-md mx-4 border border-violet-200 dark:border-violet-800/30">
            <div className="p-6 border-b border-violet-200/50 dark:border-violet-800/30 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-slate-800 dark:text-violet-300">编辑知识图谱</h2>
              <button onClick={() => { setShowEditDialog(false); setEditingGraph(null); }} className="text-slate-500 dark:text-slate-400 hover:text-violet-600 dark:hover:text-violet-400">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">图谱名称</label>
                <input
                  type="text"
                  value={editingGraph.name}
                  onChange={(e) => setEditingGraph({ ...editingGraph, name: e.target.value })}
                  placeholder="输入图谱名称"
                  className="w-full px-4 py-3 rounded-lg border border-violet-200 dark:border-violet-800/50 bg-white/90 dark:bg-slate-700/90 focus:outline-none focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-slate-200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">图谱描述</label>
                <textarea
                  value={editingGraph.description}
                  onChange={(e) => setEditingGraph({ ...editingGraph, description: e.target.value })}
                  placeholder="输入图谱描述"
                  rows={4}
                  className="w-full px-4 py-3 rounded-lg border border-violet-200 dark:border-violet-800/50 bg-white/90 dark:bg-slate-700/90 focus:outline-none focus:ring-2 focus:ring-violet-500 text-slate-800 dark:text-slate-200"
                />
              </div>
            </div>
            <div className="p-6 border-t border-violet-200/50 dark:border-violet-800/30 flex justify-end gap-3">
              <button 
                onClick={() => { setShowEditDialog(false); setEditingGraph(null); }}
                className="px-4 py-2.5 bg-white/90 dark:bg-slate-800/90 border border-violet-200 dark:border-violet-800/50 hover:bg-violet-50 dark:hover:bg-violet-900/20 text-slate-700 dark:text-slate-300 rounded-lg transition-colors"
              >
                取消
              </button>
              <button 
                onClick={handleEditGraph}
                className="px-4 py-2.5 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700 text-white rounded-lg transition-colors shadow-md"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 批量删除确认对话框 */}
      {showBatchDeleteDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-xl shadow-xl w-full max-w-md mx-4 border border-violet-200 dark:border-violet-800/30">
            <div className="p-6 border-b border-violet-200/50 dark:border-violet-800/30 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-slate-800 dark:text-violet-300">确认删除</h2>
              <button onClick={() => setShowBatchDeleteDialog(false)} className="text-slate-500 dark:text-slate-400 hover:text-violet-600 dark:hover:text-violet-400">
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              <p className="text-slate-700 dark:text-slate-300">
                确定要删除选中的 <span className="font-bold text-red-600 dark:text-red-400">{selectedIds.size}</span> 个图谱吗？
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">此操作不可撤销，图谱中的所有节点和关系都将被删除。</p>
            </div>
            <div className="p-6 border-t border-violet-200/50 dark:border-violet-800/30 flex justify-end gap-3">
              <button 
                onClick={() => setShowBatchDeleteDialog(false)}
                className="px-4 py-2.5 bg-white/90 dark:bg-slate-800/90 border border-violet-200 dark:border-violet-800/50 hover:bg-violet-50 dark:hover:bg-violet-900/20 text-slate-700 dark:text-slate-300 rounded-lg transition-colors"
              >
                取消
              </button>
              <button 
                onClick={handleBatchDelete}
                className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors shadow-md"
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast消息 */}
      {showToast && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all transform translate-x-0 opacity-100 ${toastType === 'success' ? 'bg-green-500 text-white' : toastType === 'error' ? 'bg-red-500 text-white' : 'bg-violet-600 text-white'}`}>
          {toastMessage}
        </div>
      )}
    </div>
  );
}