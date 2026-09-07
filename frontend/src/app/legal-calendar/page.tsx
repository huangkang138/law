'use client';

import { useState, useEffect } from 'react';
import { Calendar, Clock, CheckCircle2, AlertCircle, Plus, History, Trash2, Pin, Edit, MoreHorizontal } from 'lucide-react';

const API_BASE = '/api';

export default function LegalCalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [deadlines, setDeadlines] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const [newDeadline, setNewDeadline] = useState({
    title: '',
    deadline_date: '',
    type: 'filing',
    description: ''
  });

  const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeout = 3000) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const res = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      return res;
    } catch (e) {
      clearTimeout(timeoutId);
      throw e;
    }
  };

  const loadDeadlines = async () => {
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/calendar/events`, {}, 3000);
      const data = await res.json();
      if (data.success) {
        setDeadlines(data.data);
        setHistory(data.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const addDeadline = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/calendar/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newDeadline.title,
          event_type: newDeadline.type,
          date: newDeadline.deadline_date,
          description: newDeadline.description,
          is_reminder: true
        })
      }, 5000);
      const data = await res.json();
      if (data.success) {
        loadDeadlines();
        setNewDeadline({ title: '', deadline_date: '', type: 'filing', description: '' });
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const deleteDeadline = async (id: string) => {
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/calendar/events/${id}`, {
        method: 'DELETE'
      }, 3000);
      const data = await res.json();
      if (data.success) loadDeadlines();
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadDeadlines();
  }, []);

  const handleToggleMenu = (e: React.MouseEvent, itemId: string) => {
    e.stopPropagation();
    setActiveMenuId(activeMenuId === itemId ? null : itemId);
  };

  const handleTogglePin = (e: React.MouseEvent, itemId: string) => {
    e.stopPropagation();
    // 这里可以添加置顶逻辑
    setActiveMenuId(null);
  };

  const handleStartEdit = (itemId: string, currentTitle: string) => {
    setEditingItemId(itemId);
    setEditTitle(currentTitle);
    setActiveMenuId(null);
  };

  const handleSaveEdit = () => {
    if (editingItemId && editTitle.trim()) {
      // 这里可以添加编辑逻辑
      setEditingItemId(null);
      setEditTitle('');
    }
  };

  const handleCancelEdit = () => {
    setEditingItemId(null);
    setEditTitle('');
  };

  const handleDelete = (e: React.MouseEvent, itemId: string) => {
    e.stopPropagation();
    // 这里可以添加删除逻辑
    setActiveMenuId(null);
  };

  const renderCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();

    const days = [];
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-20 p-1" />);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const hasDeadline = deadlines.some(d => 
        new Date(d.date).toDateString() === date.toDateString()
      );
      const isToday = date.toDateString() === today.toDateString();
      const isSelected = selectedDate && selectedDate.toDateString() === date.toDateString();

      days.push(
        <div
          key={day}
          onClick={() => setSelectedDate(date)}
          className={`h-20 p-1 cursor-pointer transition-all duration-200 ${
            isSelected
              ? 'bg-blue-500/20 rounded-lg'
              : isToday
              ? 'bg-amber-100/50 rounded-lg'
              : 'hover:bg-blue-50/50 rounded-lg'
          }`}
        >
          <div className={`text-sm font-medium ${isToday ? 'text-amber-700' : 'text-blue-700'}`}>
            {day}
          </div>
          {hasDeadline && (
            <div className="mt-1 flex gap-1">
              <div className="w-2 h-2 rounded-full bg-red-500" />
            </div>
          )}
        </div>
      );
    }

    return days;
  };

  const selectedDeadlines = selectedDate ? deadlines.filter(d => 
    new Date(d.date).toDateString() === selectedDate.toDateString()
  ) : [];

  return (
    <div className="fixed top-20 left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 text-foreground flex">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="relative z-10 w-64 h-full bg-white/80 backdrop-blur-md border-r border-sky-200 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">历史记录</h2>
            <button
              onClick={() => { setSelectedDate(null); }}
              className="p-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white transition-colors"
              title="新建"
            >
              <Plus size={18} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {history.length > 0 ? history.slice(0, 10).map((item, idx) => (
            <div key={idx} className="relative">
              <div className="p-3 bg-sky-50/50 rounded-xl border border-sky-200/50">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm font-medium text-sky-700">{item.title}</p>
                    <p className="text-xs text-sky-600">
                      {new Date(item.date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.event_type === 'filing' && <AlertCircle size={14} className="text-red-500 flex-shrink-0" />}
                    {item.event_type === 'hearing' && <Clock size={14} className="text-amber-500 flex-shrink-0" />}
                    {item.event_type === 'other' && <CheckCircle2 size={14} className="text-green-500 flex-shrink-0" />}
                    <button
                      onClick={(e) => handleToggleMenu(e, idx.toString())}
                      className="p-1 rounded text-gray-400 hover:text-gray-600 transition-colors"
                      title="更多操作"
                    >
                      <MoreHorizontal size={14} />
                    </button>
                  </div>
                </div>
              </div>
              
              {activeMenuId === idx.toString() && (
                <div className="absolute right-0 top-full mt-1 z-50 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[120px]">
                  <button
                    onClick={(e) => handleTogglePin(e, idx.toString())}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                  >
                    <Pin size={14} />
                    置顶
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartEdit(idx.toString(), item.title);
                    }}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                  >
                    <Edit size={14} />
                    编辑
                  </button>
                  <button
                    onClick={(e) => handleDelete(e, idx.toString())}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2 text-red-500"
                  >
                    <Trash2 size={14} />
                    删除
                  </button>
                </div>
              )}
            </div>
          )) : (
            <div className="text-center py-8 text-sky-600/60">
              <p className="text-sm">暂无历史记录</p>
            </div>
          )}
        </div>
      </div>

      <div className="relative z-10 flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <div className="flex-1 w-full overflow-y-auto overflow-x-hidden">
          <div className="w-full mx-auto px-4 pt-4 pb-4 h-full flex flex-col">
            <div className="text-center mb-4">
              <h1 className="text-2xl font-bold text-sky-700 mb-1">法律日历</h1>
              <p className="text-sm text-gray-700">管理您的重要法律截止日期和提醒</p>
              <div className="h-1 w-24 bg-gradient-to-r from-sky-500 to-blue-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="flex-1 flex flex-col gap-4">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1">
                <div className="lg:col-span-2 bg-white/70 backdrop-blur-xl rounded-2xl border border-sky-200/50 shadow-xl shadow-sky-200/20 p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-sky-800 flex items-center gap-2">
                      <Calendar size={20} className="text-sky-600" />
                      {currentDate.getFullYear()}年{currentDate.getMonth() + 1}月
                    </h2>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))}
                        className="px-3 py-1 rounded-lg bg-sky-100 text-sky-700 hover:bg-sky-200 transition-colors"
                      >
                        上月
                      </button>
                      <button
                        onClick={() => setCurrentDate(new Date())}
                        className="px-3 py-1 rounded-lg bg-sky-500 text-white hover:bg-sky-600 transition-colors"
                      >
                        今天
                      </button>
                      <button
                        onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))}
                        className="px-3 py-1 rounded-lg bg-sky-100 text-sky-700 hover:bg-sky-200 transition-colors"
                      >
                        下月
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-7 gap-1">
                    {['日', '一', '二', '三', '四', '五', '六'].map((day, i) => (
                      <div key={i} className="text-center text-sm font-medium text-sky-600 py-2">
                        {day}
                      </div>
                    ))}
                    {renderCalendar()}
                  </div>
                </div>

                <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-sky-200/50 shadow-xl shadow-sky-200/20 p-4 flex flex-col gap-4">
                  <h3 className="text-lg font-bold text-sky-800">添加提醒</h3>
                  <form onSubmit={addDeadline} className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-sky-700 mb-1">标题</label>
                      <input
                        type="text"
                        value={newDeadline.title}
                        onChange={(e) => setNewDeadline({ ...newDeadline, title: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 outline-none"
                        placeholder="请输入标题"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-sky-700 mb-1">日期</label>
                      <input
                        type="date"
                        value={newDeadline.deadline_date}
                        onChange={(e) => setNewDeadline({ ...newDeadline, deadline_date: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 outline-none"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-sky-700 mb-1">类型</label>
                      <select
                        value={newDeadline.type}
                        onChange={(e) => setNewDeadline({ ...newDeadline, type: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 outline-none"
                      >
                        <option value="filing">立案</option>
                        <option value="hearing">听证</option>
                        <option value="other">其他</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-sky-700 mb-1">备注</label>
                      <textarea
                        value={newDeadline.description}
                        onChange={(e) => setNewDeadline({ ...newDeadline, description: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 outline-none"
                        rows={3}
                        placeholder="请输入备注"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full py-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold rounded-lg hover:from-sky-600 hover:to-blue-700 transition-all disabled:opacity-50"
                    >
                      {loading ? '添加中...' : '添加提醒'}
                    </button>
                  </form>

                  {selectedDeadlines.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-sky-700 mb-2">
                        当日提醒
                      </h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {selectedDeadlines.map((deadline) => (
                          <div key={deadline.id} className="p-3 bg-sky-50 rounded-lg border border-sky-200 flex justify-between items-start">
                            <div>
                              <p className="font-medium text-sky-800">{deadline.title}</p>
                              {deadline.description && (
                                <p className="text-xs text-sky-600 mt-1">{deadline.description}</p>
                              )}
                            </div>
                            <button
                              onClick={() => deleteDeadline(deadline.id)}
                              className="text-red-500 hover:text-red-700"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}