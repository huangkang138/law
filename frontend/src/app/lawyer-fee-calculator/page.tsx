'use client';

import { useState, useEffect } from 'react';
import { Users, Plus, Trash2, Pin, Edit, MoreHorizontal, Settings } from 'lucide-react';
import Link from 'next/link';

const API_BASE = '/api';

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

export default function LawyerFeeCalculatorPage() {
  const [form, setForm] = useState({ case_type: 'civil', amount: '', fee_method: 'percentage' });
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/lawyer-fee`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }, 5000);
      const data = await res.json();
      if (data.success) {
        // 计算过程
        const amount = parseFloat(form.amount) || 0;
        const caseType = form.case_type;
        const feeMethod = form.fee_method;
        
        let fee = 0;
        let steps: string[] = [];
        let rules: string[] = [];
        let legalBasis: string[] = [];
        let formula = '';
        
        if (caseType === 'civil') {
          // 民事案件律师费计算
          if (feeMethod === 'percentage') {
            if (amount <= 100000) {
              fee = amount * 0.05;
              formula = '律师费 = 标的金额 × 5%';
              steps = [
                `案件类型: 民事案件`,
                `收费方式: 按比例收费`,
                `标的金额: ¥${amount.toLocaleString()}`,
                `收费比例: 5%（标的额10万元以下）`,
                `律师费: ¥${amount.toLocaleString()} × 5% = ¥${fee.toLocaleString()}`
              ];
            } else if (amount <= 500000) {
              fee = 100000 * 0.05 + (amount - 100000) * 0.04;
              formula = '律师费 = 10万元 × 5% + (标的金额 - 10万元) × 4%';
              steps = [
                `案件类型: 民事案件`,
                `收费方式: 按比例收费`,
                `标的金额: ¥${amount.toLocaleString()}`,
                `第一段（10万元以下）: ¥100,000 × 5% = ¥5,000`,
                `第二段（10万-50万元）: ¥${(amount - 100000).toLocaleString()} × 4% = ¥${((amount - 100000) * 0.04).toLocaleString()}`,
                `律师费: ¥5,000 + ¥${((amount - 100000) * 0.04).toLocaleString()} = ¥${fee.toLocaleString()}`
              ];
            } else if (amount <= 1000000) {
              fee = 100000 * 0.05 + 400000 * 0.04 + (amount - 500000) * 0.03;
              formula = '律师费 = 10万元 × 5% + 40万元 × 4% + (标的金额 - 50万元) × 3%';
              steps = [
                `案件类型: 民事案件`,
                `收费方式: 按比例收费`,
                `标的金额: ¥${amount.toLocaleString()}`,
                `第一段（10万元以下）: ¥100,000 × 5% = ¥5,000`,
                `第二段（10万-50万元）: ¥400,000 × 4% = ¥16,000`,
                `第三段（50万-100万元）: ¥${(amount - 500000).toLocaleString()} × 3% = ¥${((amount - 500000) * 0.03).toLocaleString()}`,
                `律师费: ¥5,000 + ¥16,000 + ¥${((amount - 500000) * 0.03).toLocaleString()} = ¥${fee.toLocaleString()}`
              ];
            } else {
              fee = 100000 * 0.05 + 400000 * 0.04 + 500000 * 0.03 + (amount - 1000000) * 0.02;
              formula = '律师费 = 10万元 × 5% + 40万元 × 4% + 50万元 × 3% + (标的金额 - 100万元) × 2%';
              steps = [
                `案件类型: 民事案件`,
                `收费方式: 按比例收费`,
                `标的金额: ¥${amount.toLocaleString()}`,
                `第一段（10万元以下）: ¥100,000 × 5% = ¥5,000`,
                `第二段（10万-50万元）: ¥400,000 × 4% = ¥16,000`,
                `第三段（50万-100万元）: ¥500,000 × 3% = ¥15,000`,
                `第四段（100万元以上）: ¥${(amount - 1000000).toLocaleString()} × 2% = ¥${((amount - 1000000) * 0.02).toLocaleString()}`,
                `律师费: ¥5,000 + ¥16,000 + ¥15,000 + ¥${((amount - 1000000) * 0.02).toLocaleString()} = ¥${fee.toLocaleString()}`
              ];
            }
          } else {
            fee = 3000;
            formula = '律师费 = 固定费用';
            steps = [
              `案件类型: 民事案件`,
              `收费方式: 固定收费`,
              `固定费用: ¥3,000`
            ];
          }
          rules = [
            '1. 民事案件律师服务费实行政府指导价和市场调节价相结合',
            '2. 标的额10万元以下部分，按5%收取',
            '3. 标的额10万-50万元部分，按4%收取',
            '4. 标的额50万-100万元部分，按3%收取',
            '5. 标的额100万元以上部分，按2%收取',
            '6. 简单民事案件可采取固定收费方式，一般为3000-10000元'
          ];
          legalBasis = [
            '《律师服务收费管理办法》',
            '《律师服务收费标准》',
            '《民法典》'
          ];
        } else if (caseType === 'criminal') {
          // 刑事案件律师费计算
          if (feeMethod === 'percentage') {
            fee = amount * 0.08;
            formula = '律师费 = 标的金额 × 8%';
            steps = [
              `案件类型: 刑事案件`,
              `收费方式: 按比例收费`,
              `标的金额: ¥${amount.toLocaleString()}`,
              `收费比例: 8%`,
              `律师费: ¥${amount.toLocaleString()} × 8% = ¥${fee.toLocaleString()}`
            ];
          } else {
            fee = 5000;
            formula = '律师费 = 固定费用';
            steps = [
              `案件类型: 刑事案件`,
              `收费方式: 固定收费`,
              `固定费用: ¥5,000`
            ];
          }
          rules = [
            '1. 刑事案件律师服务费实行政府指导价',
            '2. 侦查阶段、审查起诉阶段、审判阶段分别收费',
            '3. 一般按标的金额的8%收取',
            '4. 简单刑事案件可采取固定收费方式，一般为5000-20000元'
          ];
          legalBasis = [
            '《律师服务收费管理办法》',
            '《刑事诉讼法》',
            '《律师执业管理办法》'
          ];
        } else {
          // 行政案件律师费计算
          if (feeMethod === 'percentage') {
            fee = amount * 0.06;
            formula = '律师费 = 标的金额 × 6%';
            steps = [
              `案件类型: 行政案件`,
              `收费方式: 按比例收费`,
              `标的金额: ¥${amount.toLocaleString()}`,
              `收费比例: 6%`,
              `律师费: ¥${amount.toLocaleString()} × 6% = ¥${fee.toLocaleString()}`
            ];
          } else {
            fee = 4000;
            formula = '律师费 = 固定费用';
            steps = [
              `案件类型: 行政案件`,
              `收费方式: 固定收费`,
              `固定费用: ¥4,000`
            ];
          }
          rules = [
            '1. 行政案件律师服务费实行政府指导价',
            '2. 一般按标的金额的6%收取',
            '3. 简单行政案件可采取固定收费方式，一般为4000-15000元'
          ];
          legalBasis = [
            '《律师服务收费管理办法》',
            '《行政诉讼法》',
            '《律师执业管理办法》'
          ];
        }
        
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
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/lawyer-fee`);
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

  const caseTypes = [
    { value: 'civil', label: '民事案件' },
    { value: 'criminal', label: '刑事案件' },
    { value: 'administrative', label: '行政案件' }
  ];

  const feeMethods = [
    { value: 'percentage', label: '按比例收费' },
    { value: 'fixed', label: '固定收费' }
  ];

  return (
    <div className="fixed top-20 left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 text-foreground flex">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="relative z-10 w-64 h-full bg-white/80 backdrop-blur-md border-r border-sky-200 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">历史记录</h2>
            <button
              onClick={() => { setResult(null); setForm({ case_type: 'civil', amount: '', fee_method: 'percentage' }); }}
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
                      {caseTypes.find(t => t.value === item.case_type)?.label}
                    </p>
                    <p className="text-xs text-sky-600">
                      {item.fee_method === 'percentage' ? '按比例' : '固定'}
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
                      handleStartEdit(idx.toString(), caseTypes.find(t => t.value === item.case_type)?.label || '计算记录');
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
        <div className="p-3 border-t border-sky-200 flex-shrink-0">
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
              <h1 className="text-2xl font-bold text-sky-700 mb-1">律师费计算器</h1>
              <p className="text-sm text-gray-700">根据行业标准计算律师服务费用</p>
              <div className="h-1 w-24 bg-gradient-to-r from-sky-500 to-blue-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="flex-1 flex flex-col gap-4">
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-sky-200/50 shadow-xl shadow-sky-200/20 p-4">
                <h2 className="text-xl font-bold text-sky-800 mb-4 flex items-center gap-2">
                  <Users size={20} className="text-sky-600" />
                  计算律师费
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-sky-700 mb-2">案件类型</label>
                    <select
                      value={form.case_type}
                      onChange={(e) => setForm({ ...form, case_type: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 focus:border-transparent outline-none transition-all"
                    >
                      {caseTypes.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-sky-700 mb-2">收费方式</label>
                    <select
                      value={form.fee_method}
                      onChange={(e) => setForm({ ...form, fee_method: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 focus:border-transparent outline-none transition-all"
                    >
                      {feeMethods.map(m => (
                        <option key={m.value} value={m.value}>{m.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-sky-700 mb-2">案件标的金额 (元)</label>
                    <input
                      type="number"
                      value={form.amount}
                      onChange={(e) => setForm({ ...form, amount: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 focus:border-transparent outline-none transition-all"
                      placeholder="请输入金额"
                    />
                  </div>

                  <button
                    onClick={calculate}
                    disabled={loading}
                    className="w-full py-3 bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-semibold rounded-xl hover:from-sky-600 hover:to-indigo-700 transition-all duration-300 shadow-lg shadow-sky-300/30 disabled:opacity-50"
                  >
                    {loading ? '计算中...' : '开始计算'}
                  </button>
                </div>
              </div>

              {result && (
                <div className="flex-1 bg-gradient-to-br from-sky-50 to-indigo-50 rounded-2xl border border-sky-200 p-4">
                  <h3 className="text-xl font-bold text-sky-800 mb-4">计算结果</h3>
                  <div className="text-center mb-4">
                    <p className="text-sm text-sky-600 mb-2">预估律师费用</p>
                    <p className="text-4xl font-bold text-sky-700">¥{result.fee?.toLocaleString()}</p>
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