'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Star,
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
  Calendar,
  Tag,
  Sparkles,
  ChevronLeft,
  X,
  Settings,
  History
} from 'lucide-react';
import Link from 'next/link';
import { AlertDialog, showAlert, showConfirm } from '@/components/AlertDialog';
import {
  getFavorites,
  deleteFavorite,
  updateFavoriteTitle,
  createFavorite
} from '@/lib/api';
import ScaleIcon from '@/components/ScaleIcon';

interface FavoriteItem {
  id: string;
  title: string;
  content: string;
  source_type: 'legal' | 'contract' | 'debate' | 'case-analysis' | 'similar-documents' | 'dispute' | 'evidence' | 'protection' | 'document' | 'prediction' | 'reminder' | 'warning';
  source_id?: string;
  created_at: string;
  updated_at: string;
}

type FavoriteType = 'all' | 'legal' | 'contract' | 'debate' | 'case-analysis' | 'similar-documents' | 'dispute' | 'evidence' | 'protection' | 'document' | 'prediction' | 'reminder' | 'warning';

export default function FavoritesPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<FavoriteType>('all');
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    // 页面加载时获取所有收藏数据
    loadFavorites();
  }, []);

  // 切换标签页时不需要重新加载数据，只需要重新过滤显示
  useEffect(() => {
    setCurrentPage(1);
    setSearchTerm('');
  }, [activeTab]);

  const loadFavorites = async () => {
    setLoading(true);
    setError('');
    setSelectedItems([]);
    setEditingItem(null);
    setCurrentPage(1);

    try {
      const data = await getFavorites();
      setFavorites(data.favorites || []);
    } catch (err: any) {
      setError(err.message || '加载收藏失败');
    } finally {
      setLoading(false);
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
    const currentFavorites = getFilteredFavorites();
    if (currentFavorites.length > 0) {
      if (selectedItems.length === currentFavorites.length) {
        setSelectedItems([]);
      } else {
        setSelectedItems(currentFavorites.map((item: any) => item.id));
      }
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedItems.length > 0) {
      const confirmed = await showConfirm(`确定要删除选中的 ${selectedItems.length} 条收藏吗？`, '确认删除');
      if (confirmed) {
        try {
          for (const id of selectedItems) {
            await deleteFavorite(id);
          }
          setSelectedItems([]);
          loadFavorites();
        } catch (error: any) {
          await showAlert('删除失败: ' + error.message, 'error');
        }
      }
    }
  };

  const handleDeleteItem = async (id: string) => {
    const confirmed = await showConfirm('确定要删除这条收藏吗？', '确认删除');
    if (confirmed) {
      try {
        await deleteFavorite(id);
        loadFavorites();
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
        await updateFavoriteTitle(id, editTitle.trim());
        setEditingItem(null);
        setEditTitle('');
        loadFavorites();
      } catch (error: any) {
        await showAlert('更新失败: ' + error.message, 'error');
      }
    }
  };

  const handleViewItem = (item: FavoriteItem) => {
    switch (item.source_type) {
      case 'legal':
        if (item.source_id) {
          router.push(`/chat?sessionId=${item.source_id}`);
        }
        break;
      case 'contract':
        if (item.source_id) {
          router.push(`/contract?id=${item.source_id}`);
        }
        break;
      case 'debate':
        if (item.source_id) {
          router.push(`/debate?session=${item.source_id}`);
        }
        break;
      case 'case-analysis':
        if (item.source_id) {
          router.push(`/case-analysis?id=${item.source_id}`);
        }
        break;
      case 'similar-documents':
        if (item.source_id) {
          router.push(`/similar-documents?id=${item.source_id}`);
        }
        break;
      case 'dispute':
        if (item.source_id) {
          router.push(`/dispute-organize?id=${item.source_id}`);
        }
        break;
      case 'evidence':
      case 'protection':
        router.push(`/dispute-center`);
        break;
      case 'document':
        if (item.source_id) {
          router.push(`/contract?id=${item.source_id}`);
        }
        break;
      case 'prediction':
        if (item.source_id) {
          router.push(`/case-analysis?id=${item.source_id}`);
        }
        break;
      case 'reminder':
      case 'warning':
        router.push(`/dispute-center`);
        break;
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

  const getTodayCount = (items: FavoriteItem[]) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return items.filter(item => {
      const itemDate = new Date(item.created_at);
      return itemDate >= today;
    }).length;
  };

  const getMonthCount = (items: FavoriteItem[]) => {
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    return items.filter(item => new Date(item.created_at) >= monthAgo).length;
  };

  const getFilteredFavorites = () => {
    let items = [...favorites];

    if (activeTab !== 'all') {
      items = items.filter(item => item.source_type === activeTab);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      items = items.filter(item => 
        item.title.toLowerCase().includes(term) || 
        item.content.toLowerCase().includes(term)
      );
    }

    return items;
  };

  const sidebarTabs = [
    { id: 'all' as FavoriteType, name: '全部收藏', icon: Star },
    { id: 'legal' as FavoriteType, name: '普法问答', icon: FileText },
    { id: 'contract' as FavoriteType, name: '合同审查', icon: FileText },
    { id: 'debate' as FavoriteType, name: '模拟法庭', icon: Scale },
    { id: 'case-analysis' as FavoriteType, name: '案情推断', icon: Brain },
    { id: 'similar-documents' as FavoriteType, name: '相似文书', icon: FileSearch },
    { id: 'dispute' as FavoriteType, name: '纠纷整理', icon: FolderOpen },
    { id: 'evidence' as FavoriteType, name: '取证存证', icon: Shield },
    { id: 'protection' as FavoriteType, name: '维权路径', icon: Route },
    { id: 'document' as FavoriteType, name: '文书生成', icon: FileText },
    { id: 'prediction' as FavoriteType, name: '案件预判', icon: TrendingUp },
    { id: 'reminder' as FavoriteType, name: '流程提醒', icon: Bell },
    { id: 'warning' as FavoriteType, name: '避坑提醒', icon: WarningIcon },
  ];

  const filteredItems = getFilteredFavorites();
  const totalCount = filteredItems.length;
  const todayCount = getTodayCount(filteredItems);
  const monthCount = getMonthCount(filteredItems);

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
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="flex h-screen">
        <div className={`${sidebarOpen ? 'w-80' : 'w-20'} flex-shrink-0 transition-all duration-300 h-screen sticky top-0`}>
          <div className="h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-r border-sky-200 dark:border-sky-900/30 shadow-lg overflow-hidden flex flex-col">
            <div className="p-5 border-b border-sky-200 dark:border-sky-900/30">
              <div className="flex items-center gap-4">
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-500 flex-shrink-0">
                  <Star size={24} className="text-white" />
                </div>
                {sidebarOpen && (
                  <div>
                    <h1 className="text-xl font-bold text-sky-800 dark:text-sky-300">我的收藏</h1>
                    <p className="text-sm text-sky-600 dark:text-sky-400">查看所有收藏内容</p>
                  </div>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
              {sidebarTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                const count = tab.id === 'all' 
                  ? favorites.length 
                  : favorites.filter(f => f.source_type === tab.id).length;

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

            <div className="p-3 border-t border-sky-200 dark:border-sky-900/30">
              <Link
                href="/settings"
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-sky-700 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30"
              >
                <Settings size={20} className="flex-shrink-0" />
                {sidebarOpen && <span className="text-sm font-medium flex-1 text-left">设置</span>}
              </Link>
            </div>

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

        <div className="flex-1 min-w-0 overflow-y-auto">
          <div className="p-8">
            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-6 mb-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-500 shadow-lg">
                    {ActiveIcon && <ActiveIcon size={28} className="text-white" />}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-sky-800 dark:text-sky-300">{activeTabObj?.name}</h2>
                    <p className="text-sm text-sky-600 dark:text-sky-400 mt-1">查看和管理您的{activeTabObj?.name}</p>
                  </div>
                </div>
                <Link
                  href="/history"
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-sky-500 to-indigo-500 text-white rounded-lg hover:shadow-lg transition-all hover:scale-105"
                >
                  <History size={18} />
                  <span className="text-sm font-medium">历史记录</span>
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-sky-50 to-blue-100 dark:from-sky-900/20 dark:to-blue-800/20 rounded-xl p-4 border border-sky-200 dark:border-sky-800">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-sky-500/20 flex items-center justify-center">
                      <Star size={20} className="text-sky-600 dark:text-sky-400" />
                    </div>
                    <div>
                      <p className="text-sm text-sky-600 dark:text-sky-400">总收藏数</p>
                      <p className="text-2xl font-bold text-sky-800 dark:text-sky-300">{totalCount}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-800/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <Calendar size={20} className="text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <p className="text-sm text-blue-600 dark:text-blue-400">今日新增</p>
                      <p className="text-2xl font-bold text-blue-800 dark:text-blue-300">{todayCount}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-indigo-50 to-purple-100 dark:from-indigo-900/20 dark:to-purple-800/20 rounded-xl p-4 border border-indigo-200 dark:border-indigo-800">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                      <Clock size={20} className="text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div>
                      <p className="text-sm text-indigo-600 dark:text-indigo-400">本月记录</p>
                      <p className="text-2xl font-bold text-indigo-800 dark:text-indigo-300">{monthCount}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-4 mb-6">
              <div className="flex items-center gap-3">
                <div className="relative w-64">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-sky-400" />
                  <input
                    type="text"
                    placeholder="搜索收藏..."
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full pl-9 pr-3 py-2 bg-sky-50 dark:bg-gray-800 border border-sky-300 dark:border-sky-700 rounded-lg text-sm text-sky-800 dark:text-sky-200 placeholder-sky-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    <Star size={40} className="text-sky-500" />
                  </div>
                  <p className="text-sky-800 dark:text-sky-300 text-lg mb-2">暂无收藏</p>
                  <p className="text-sky-600 dark:text-sky-400">点击AI回答旁边的收藏按钮来收藏内容</p>
                </div>
              ) : (
                <>
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
                        共 {filteredItems.length} 条收藏
                        {totalPages > 1 && `，第 ${currentPage}/${totalPages} 页`}
                      </span>
                    </div>
                    {totalPages > 1 && (
                      <span className="text-xs text-sky-400">
                        显示 {startIndex + 1}-{Math.min(endIndex, filteredItems.length)} 条
                      </span>
                    )}
                  </div>

                  <div className="divide-y divide-sky-200 dark:divide-sky-900/30">
                    {paginatedItems.map((item: FavoriteItem) => (
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
                                  className="flex-1 px-3 py-1.5 bg-white dark:bg-gray-800 border border-sky-300 dark:border-sky-700 rounded-lg text-sm text-sky-800 dark:text-sky-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                                <div className="flex-1 min-w-0">
                                  <h3 className="text-sm font-medium text-sky-800 dark:text-sky-300 truncate">
                                    {item.title}
                                  </h3>
                                  <p className="text-xs text-sky-600 dark:text-sky-400 mt-1 line-clamp-2">
                                    {item.content}
                                  </p>
                                </div>
                              </>
                            )}
                          </div>

                          <div className="flex items-center gap-2 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleViewItem(item)}
                              className="p-2 text-sky-600 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30 rounded-lg transition-colors"
                              title="查看"
                            >
                              <Search size={16} />
                            </button>
                            <button
                              onClick={() => handleStartEdit(item.id, item.title)}
                              className="p-2 text-sky-600 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/30 rounded-lg transition-colors"
                              title="编辑"
                            >
                              <Edit size={16} />
                            </button>
                            <button
                              onClick={() => handleDeleteItem(item.id)}
                              className="p-2 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                              title="删除"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {totalPages > 1 && (
                    <div className="px-4 py-3 border-t border-sky-200 dark:border-sky-900/30 bg-sky-50/50 dark:bg-sky-900/20 flex items-center justify-center gap-2">
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="px-3 py-1.5 text-sm text-sky-700 dark:text-sky-400 hover:bg-sky-200 dark:hover:bg-sky-800 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        上一页
                      </button>
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                        const showPage = totalPages <= 7 || 
                          page === 1 || 
                          page === totalPages || 
                          (page >= currentPage - 1 && page <= currentPage + 1);
                        
                        if (!showPage) {
                          if (page === currentPage - 2 || page === currentPage + 2) {
                            return <span key={page} className="text-sky-400">...</span>;
                          }
                          return null;
                        }

                        return (
                          <button
                            key={page}
                            onClick={() => handlePageChange(page)}
                            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                              currentPage === page
                                ? 'bg-sky-500 text-white'
                                : 'text-sky-700 dark:text-sky-400 hover:bg-sky-200 dark:hover:bg-sky-800'
                            }`}
                          >
                            {page}
                          </button>
                        );
                      })}
                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className="px-3 py-1.5 text-sm text-sky-700 dark:text-sky-400 hover:bg-sky-200 dark:hover:bg-sky-800 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
