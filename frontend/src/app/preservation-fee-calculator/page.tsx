'use client';

import { useState, useEffect } from 'react';
import { Shield, Plus, Trash2, Pin, Edit, MoreHorizontal, Settings } from 'lucide-react';
import Link from 'next/link';

const API_BASE = 'http://localhost:8001/api';

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

export default function PreservationFeeCalculatorPage() {
  const [form, setForm] = useState({ preservation_amount: '' });
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/preservation-fee`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }, 5000);
      const data = await res.json();
      if (data.success) {
        // 计算过程
        const preservationAmount = parseFloat(form.preservation_amount) || 0;
        
        let fee = 0;
        let steps: string[] = [];
        let rules: string[] = [];
        let legalBasis: string[] = [];
        let formula = '';
        
        if (preservationAmount <= 1000) {
          fee = 30;
          formula = '保全费 = 固定费用 30元';
          steps = [
            `保全金额: ¥${preservationAmount.toLocaleString()}`,
            `收费档次: 1000元以下`,
            `保全费: ¥30`
          ];
        } else if (preservationAmount <= 10000) {
          fee = 30 + (preservationAmount - 1000) * 0.01;
          formula = '保全费 = 30元 + (保全金额 - 1000元) × 1%';
          steps = [
            `保全金额: ¥${preservationAmount.toLocaleString()}`,
            `收费档次: 1000元-1万元`,
            `基础费用: ¥30`,
            `超额部分: ¥${(preservationAmount - 1000).toLocaleString()}`,
            `超额费用: ¥${(preservationAmount - 1000).toLocaleString()} × 1% = ¥${((preservationAmount - 1000) * 0.01).toLocaleString()}`,
            `保全费: ¥30 + ¥${((preservationAmount - 1000) * 0.01).toLocaleString()} = ¥${fee.toLocaleString()}`
          ];
        } else if (preservationAmount <= 100000) {
          fee = 30 + 9000 * 0.01 + (preservationAmount - 10000) * 0.005;
          formula = '保全费 = 30元 + 9000元 × 1% + (保全金额 - 1万元) × 0.5%';
          steps = [
            `保全金额: ¥${preservationAmount.toLocaleString()}`,
            `收费档次: 1万-10万元`,
            `第一段（1000元以下）: ¥30`,
            `第二段（1000元-1万元）: ¥9,000 × 1% = ¥90`,
            `第三段（1万-10万元）: ¥${(preservationAmount - 10000).toLocaleString()} × 0.5% = ¥${((preservationAmount - 10000) * 0.005).toLocaleString()}`,
            `保全费: ¥30 + ¥90 + ¥${((preservationAmount - 10000) * 0.005).toLocaleString()} = ¥${fee.toLocaleString()}`
          ];
        } else {
          fee = 30 + 9000 * 0.01 + 90000 * 0.005 + (preservationAmount - 100000) * 0.001;
          formula = '保全费 = 30元 + 9000元 × 1% + 9万元 × 0.5% + (保全金额 - 10万元) × 0.1%';
          steps = [
            `保全金额: ¥${preservationAmount.toLocaleString()}`,
            `收费档次: 10万元以上`,
            `第一段（1000元以下）: ¥30`,
            `第二段（1000元-1万元）: ¥9,000 × 1% = ¥90`,
            `第三段（1万-10万元）: ¥90,000 × 0.5% = ¥450`,
            `第四段（10万元以上）: ¥${(preservationAmount - 100000).toLocaleString()} × 0.1% = ¥${((preservationAmount - 100000) * 0.001).toLocaleString()}`,
            `保全费: ¥30 + ¥90 + ¥450 + ¥${((preservationAmount - 100000) * 0.001).toLocaleString()} = ¥${fee.toLocaleString()}`
          ];
        }
        
        // 保全费最高不超过5000元
        fee = Math.min(fee, 5000);
        
        rules = [
          '1. 财产保全申请费按照保全金额分段累计计算',
          '2. 不超过1000元的，每件交纳30元',
          '3. 超过1000元至1万元的部分，按照1%交纳',
          '4. 超过1万元至10万元的部分，按照0.5%交纳',
          '5. 超过10万元的部分，按照0.1%交纳',
          '6. 财产保全申请费最高不超过5000元',
          '7. 申请财产保全需要提供担保',
          '8. 担保金额一般为保全金额的100%'
        ];
        
        legalBasis = [
          '《诉讼费用交纳办法》第十四条',
          '《民事诉讼法》第一百零一条',
          '《最高人民法院关于人民法院办理财产保全案件若干问题的规定》'
        ];
        
        // 添加计算过程到结果中
        const resultWithCalculation = {
          ...data.data,
          calculation: {
            formula,
            steps,
            rules,
            legalBasis
          }
        };
        setResult(resultWithCalculation);
        loadHistory();
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const loadHistory = async () => {
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/preservation-fee`);
      const data = await res.json();
      if (data.success) setHistory(data.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadHistory();
    }, 500);
    return () => clearTimeout(timer);
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

  return (
    <div className="fixed top-20 left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 text-foreground flex">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="relative z-10 w-64 h-full bg-white/80 backdrop-blur-md border-r border-sky-200 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">历史记录</h2>
            <button
              onClick={() => { setResult(null); setForm({ preservation_amount: '' }); }}
              className="p-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white transition-colors"
              title="新建计算"
            >
              <Plus size={18} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {history.length > 0 ? history.map((item, idx) => (
            <div key={idx} className="relative">
              <div className="p-3 bg-sky-50/50 rounded-xl border border-sky-200/50">
                <div className="flex justify-between items-center">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-sky-700 truncate">
                      保全费计算
                    </p>
                    <p className="text-xs text-sky-600">
                      ¥{parseFloat(item.preservation_amount).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sky-700 flex-shrink-0">¥{parseFloat(item.fee).toLocaleString()}</span>
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
                      handleStartEdit(idx.toString(), '保全费计算');
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
            <div className="text-center py-8 text-blue-600/60">
              <p className="text-sm">暂无历史记录</p>
            </div>
          )}
        </div>

        {/* 设置按钮 */}
        <div className="p-3 border-t border-blue-200 flex-shrink-0">
          <Link
            href="/settings"
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
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
              <h1 className="text-2xl font-bold text-sky-700 mb-1">保全费计算器</h1>
              <p className="text-sm text-gray-700">计算财产保全申请费用</p>
              <div className="h-1 w-24 bg-gradient-to-r from-sky-500 to-blue-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="flex-1 flex flex-col gap-4">
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-sky-200/50 shadow-xl shadow-sky-200/20 p-4">
                <h2 className="text-xl font-bold text-sky-800 mb-4 flex items-center gap-2">
                  <Shield size={20} className="text-sky-600" />
                  计算保全费
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-sky-700 mb-2">保全金额 (元)</label>
                    <input
                      type="number"
                      value={form.preservation_amount}
                      onChange={(e) => setForm({ ...form, preservation_amount: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 focus:border-transparent outline-none transition-all"
                      placeholder="请输入保全金额"
                    />
                  </div>

                  <button
                    onClick={calculate}
                    disabled={loading}
                    className="w-full py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all duration-300 shadow-lg shadow-blue-300/30 disabled:opacity-50"
                  >
                    {loading ? '计算中...' : '开始计算'}
                  </button>
                </div>
              </div>

              {result && (
                <div className="flex-1 bg-gradient-to-br from-sky-50 to-blue-50 rounded-2xl border border-sky-200 p-4">
                  <h3 className="text-xl font-bold text-sky-800 mb-4">计算结果</h3>
                  <div className="text-center mb-4">
                    <p className="text-sm text-sky-600 mb-2">应缴保全费</p>
                    <p className="text-4xl font-bold text-sky-700">¥{result.fee?.toLocaleString()}</p>
                    <p className="text-xs text-sky-600 mt-2">最高不超过5000元</p>
                  </div>
                  {result.calculation && (
                    <div className="space-y-4">
                      <div className="p-4 bg-white rounded-xl">
                        <h4 className="text-lg font-semibold text-sky-700 mb-2">计算公式</h4>
                        <p className="text-sky-800 font-medium">{result.calculation.formula}</p>
                      </div>
                      <div className="p-4 bg-white rounded-xl">
                        <h4 className="text-lg font-semibold text-sky-700 mb-2">计算过程</h4>
                        <ul className="space-y-2 text-sky-800">
                          {result.calculation.steps.map((step: string, index: number) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-sky-500 font-bold">{index + 1}.</span>
                              <span>{step}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="p-4 bg-white rounded-xl">
                        <h4 className="text-lg font-semibold text-sky-700 mb-2">计算细则</h4>
                        <ul className="space-y-2 text-sky-800">
                          {result.calculation.rules.map((rule: string, index: number) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-sky-500 font-bold">•</span>
                              <span>{rule}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="p-4 bg-white rounded-xl">
                        <h4 className="text-lg font-semibold text-sky-700 mb-2">法律依据</h4>
                        <ul className="space-y-2 text-sky-800">
                          {result.calculation.legalBasis.map((basis: string, index: number) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-sky-500 font-bold">{index + 1}.</span>
                              <span>{basis}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
