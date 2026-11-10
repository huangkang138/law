'use client';

import { useState, useEffect } from 'react';
import { Coins, Plus, Trash2, Pin, Edit, MoreHorizontal, Settings } from 'lucide-react';
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

export default function CourtFeeCalculatorPage() {
  const [form, setForm] = useState({ case_type: 'property', amount: '' });
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/court-fee`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }, 5000);
      const data = await res.json();
      if (data.success) {
        // 计算过程
        const amount = parseFloat(form.amount) || 0;
        const caseType = form.case_type;
        
        let fee = 0;
        let steps: string[] = [];
        let rules: string[] = [];
        let legalBasis: string[] = [];
        let formula = '';
        
        if (caseType === 'property') {
          // 财产案件诉讼费计算
          if (amount <= 10000) {
            fee = 50;
            formula = '诉讼费 = 固定费用 50元';
            steps = [
              `案件类型: 财产案件`,
              `诉讼请求金额: ¥${amount.toLocaleString()}`,
              `收费档次: 1万元以下`,
              `案件受理费: ¥50`
            ];
          } else if (amount <= 100000) {
            fee = 50 + (amount - 10000) * 0.025;
            formula = '诉讼费 = 50元 + (诉讼请求金额 - 1万元) × 2.5%';
            steps = [
              `案件类型: 财产案件`,
              `诉讼请求金额: ¥${amount.toLocaleString()}`,
              `收费档次: 1万-10万元`,
              `基础费用: ¥50`,
              `超额部分: ¥${(amount - 10000).toLocaleString()}`,
              `超额费用: ¥${(amount - 10000).toLocaleString()} × 2.5% = ¥${((amount - 10000) * 0.025).toLocaleString()}`,
              `案件受理费: ¥50 + ¥${((amount - 10000) * 0.025).toLocaleString()} = ¥${fee.toLocaleString()}`
            ];
          } else if (amount <= 200000) {
            fee = 50 + 90000 * 0.025 + (amount - 100000) * 0.02;
            formula = '诉讼费 = 50元 + 9万元 × 2.5% + (诉讼请求金额 - 10万元) × 2%';
            steps = [
              `案件类型: 财产案件`,
              `诉讼请求金额: ¥${amount.toLocaleString()}`,
              `收费档次: 10万-20万元`,
              `第一段（1万元以下）: ¥50`,
              `第二段（1万-10万元）: ¥90,000 × 2.5% = ¥2,250`,
              `第三段（10万-20万元）: ¥${(amount - 100000).toLocaleString()} × 2% = ¥${((amount - 100000) * 0.02).toLocaleString()}`,
              `案件受理费: ¥50 + ¥2,250 + ¥${((amount - 100000) * 0.02).toLocaleString()} = ¥${fee.toLocaleString()}`
            ];
          } else if (amount <= 500000) {
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + (amount - 200000) * 0.015;
            formula = '诉讼费 = 50元 + 9万元 × 2.5% + 10万元 × 2% + (诉讼请求金额 - 20万元) × 1.5%';
            steps = [
              `案件类型: 财产案件`,
              `诉讼请求金额: ¥${amount.toLocaleString()}`,
              `收费档次: 20万-50万元`,
              `第一段（1万元以下）: ¥50`,
              `第二段（1万-10万元）: ¥90,000 × 2.5% = ¥2,250`,
              `第三段（10万-20万元）: ¥100,000 × 2% = ¥2,000`,
              `第四段（20万-50万元）: ¥${(amount - 200000).toLocaleString()} × 1.5% = ¥${((amount - 200000) * 0.015).toLocaleString()}`,
              `案件受理费: ¥50 + ¥2,250 + ¥2,000 + ¥${((amount - 200000) * 0.015).toLocaleString()} = ¥${fee.toLocaleString()}`
            ];
          } else if (amount <= 1000000) {
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + 300000 * 0.015 + (amount - 500000) * 0.01;
            formula = '诉讼费 = 50元 + 9万元 × 2.5% + 10万元 × 2% + 30万元 × 1.5% + (诉讼请求金额 - 50万元) × 1%';
            steps = [
              `案件类型: 财产案件`,
              `诉讼请求金额: ¥${amount.toLocaleString()}`,
              `收费档次: 50万-100万元`,
              `第一段（1万元以下）: ¥50`,
              `第二段（1万-10万元）: ¥90,000 × 2.5% = ¥2,250`,
              `第三段（10万-20万元）: ¥100,000 × 2% = ¥2,000`,
              `第四段（20万-50万元）: ¥300,000 × 1.5% = ¥4,500`,
              `第五段（50万-100万元）: ¥${(amount - 500000).toLocaleString()} × 1% = ¥${((amount - 500000) * 0.01).toLocaleString()}`,
              `案件受理费: ¥50 + ¥2,250 + ¥2,000 + ¥4,500 + ¥${((amount - 500000) * 0.01).toLocaleString()} = ¥${fee.toLocaleString()}`
            ];
          } else if (amount <= 2000000) {
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + 300000 * 0.015 + 500000 * 0.01 + (amount - 1000000) * 0.009;
            formula = '诉讼费 = 50元 + 9万元 × 2.5% + 10万元 × 2% + 30万元 × 1.5% + 50万元 × 1% + (诉讼请求金额 - 100万元) × 0.9%';
            steps = [
              `案件类型: 财产案件`,
              `诉讼请求金额: ¥${amount.toLocaleString()}`,
              `收费档次: 100万-200万元`,
              `第一段（1万元以下）: ¥50`,
              `第二段（1万-10万元）: ¥90,000 × 2.5% = ¥2,250`,
              `第三段（10万-20万元）: ¥100,000 × 2% = ¥2,000`,
              `第四段（20万-50万元）: ¥300,000 × 1.5% = ¥4,500`,
              `第五段（50万-100万元）: ¥500,000 × 1% = ¥5,000`,
              `第六段（100万-200万元）: ¥${(amount - 1000000).toLocaleString()} × 0.9% = ¥${((amount - 1000000) * 0.009).toLocaleString()}`,
              `案件受理费: ¥50 + ¥2,250 + ¥2,000 + ¥4,500 + ¥5,000 + ¥${((amount - 1000000) * 0.009).toLocaleString()} = ¥${fee.toLocaleString()}`
            ];
          } else {
            fee = 50 + 90000 * 0.025 + 100000 * 0.02 + 300000 * 0.015 + 500000 * 0.01 + 1000000 * 0.009 + (amount - 2000000) * 0.008;
            formula = '诉讼费 = 50元 + 9万元 × 2.5% + 10万元 × 2% + 30万元 × 1.5% + 50万元 × 1% + 100万元 × 0.9% + (诉讼请求金额 - 200万元) × 0.8%';
            steps = [
              `案件类型: 财产案件`,
              `诉讼请求金额: ¥${amount.toLocaleString()}`,
              `收费档次: 200万元以上`,
              `第一段（1万元以下）: ¥50`,
              `第二段（1万-10万元）: ¥90,000 × 2.5% = ¥2,250`,
              `第三段（10万-20万元）: ¥100,000 × 2% = ¥2,000`,
              `第四段（20万-50万元）: ¥300,000 × 1.5% = ¥4,500`,
              `第五段（50万-100万元）: ¥500,000 × 1% = ¥5,000`,
              `第六段（100万-200万元）: ¥1,000,000 × 0.9% = ¥9,000`,
              `第七段（200万元以上）: ¥${(amount - 2000000).toLocaleString()} × 0.8% = ¥${((amount - 2000000) * 0.008).toLocaleString()}`,
              `案件受理费: ¥50 + ¥2,250 + ¥2,000 + ¥4,500 + ¥5,000 + ¥9,000 + ¥${((amount - 2000000) * 0.008).toLocaleString()} = ¥${fee.toLocaleString()}`
            ];
          }
          rules = [
            '1. 财产案件根据诉讼请求的金额或者价额，按比例分段累计交纳',
            '2. 不超过1万元的，每件交纳50元',
            '3. 超过1万元至10万元的部分，按照2.5%交纳',
            '4. 超过10万元至20万元的部分，按照2%交纳',
            '5. 超过20万元至50万元的部分，按照1.5%交纳',
            '6. 超过50万元至100万元的部分，按照1%交纳',
            '7. 超过100万元至200万元的部分，按照0.9%交纳',
            '8. 超过200万元的部分，按照0.8%交纳',
            '9. 诉讼费最高不超过诉讼请求金额的4%'
          ];
          legalBasis = [
            '《诉讼费用交纳办法》第十三条',
            '《民事诉讼法》',
            '《最高人民法院关于适用〈诉讼费用交纳办法〉的通知》'
          ];
        } else if (caseType === 'divorce') {
          // 离婚案件诉讼费计算
          if (amount <= 200000) {
            fee = 300;
            formula = '诉讼费 = 固定费用 300元';
            steps = [
              `案件类型: 离婚案件`,
              `财产分割金额: ¥${amount.toLocaleString()}`,
              `收费档次: 20万元以下`,
              `案件受理费: ¥300`
            ];
          } else {
            fee = 300 + (amount - 200000) * 0.005;
            formula = '诉讼费 = 300元 + (财产分割金额 - 20万元) × 0.5%';
            steps = [
              `案件类型: 离婚案件`,
              `财产分割金额: ¥${amount.toLocaleString()}`,
              `收费档次: 20万元以上`,
              `基础费用: ¥300`,
              `超额部分: ¥${(amount - 200000).toLocaleString()}`,
              `超额费用: ¥${(amount - 200000).toLocaleString()} × 0.5% = ¥${((amount - 200000) * 0.005).toLocaleString()}`,
              `案件受理费: ¥300 + ¥${((amount - 200000) * 0.005).toLocaleString()} = ¥${fee.toLocaleString()}`
            ];
          }
          rules = [
            '1. 离婚案件每件交纳50元至300元',
            '2. 涉及财产分割，财产总额不超过20万元的，不另行交纳',
            '3. 超过20万元的部分，按照0.5%交纳',
            '4. 离婚案件诉讼费用由原告预交，最终由败诉方承担'
          ];
          legalBasis = [
            '《诉讼费用交纳办法》第十四条',
            '《婚姻法》',
            '《民事诉讼法》'
          ];
        } else if (caseType === 'labor') {
          // 劳动争议案件诉讼费计算
          fee = 10;
          formula = '诉讼费 = 固定费用 10元';
          steps = [
            `案件类型: 劳动争议案件`,
            `诉讼请求金额: ¥${amount.toLocaleString()}`,
            `案件受理费: ¥10`
          ];
          rules = [
            '1. 劳动争议案件每件交纳10元',
            '2. 劳动争议案件不按标的额收费',
            '3. 劳动争议案件诉讼费用由败诉方承担',
            '4. 劳动争议案件可申请缓交、减交或免交诉讼费'
          ];
          legalBasis = [
            '《诉讼费用交纳办法》第十五条',
            '《劳动争议调解仲裁法》',
            '《民事诉讼法》'
          ];
        } else {
          // 其他非财产案件诉讼费计算
          fee = 50;
          formula = '诉讼费 = 固定费用 50元';
          steps = [
            `案件类型: 其他非财产案件`,
            `案件受理费: ¥50`
          ];
          rules = [
            '1. 其他非财产案件每件交纳50元至100元',
            '2. 非财产案件不按标的额收费',
            '3. 具体收费标准由各省、自治区、直辖市确定'
          ];
          legalBasis = [
            '《诉讼费用交纳办法》第十六条',
            '《民事诉讼法》'
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
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/court-fee`);
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
    { value: 'property', label: '财产案件' },
    { value: 'divorce', label: '离婚案件' },
    { value: 'labor', label: '劳动争议案件' },
    { value: 'other', label: '其他非财产案件' }
  ];

  return (
    <div className="fixed business-page-shell left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 text-foreground flex">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="relative z-10 w-64 h-full bg-white/80 backdrop-blur-md border-r border-sky-200 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">历史记录</h2>
            <button
              onClick={() => { setResult(null); setForm({ case_type: 'property', amount: '' }); }}
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
                      标的: ¥{parseFloat(item.amount).toLocaleString()}
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
              <h1 className="text-2xl font-bold text-sky-700 mb-1">诉讼费用计算器</h1>
              <p className="text-sm text-gray-700">根据《诉讼费用交纳办法》计算案件受理费</p>
              <div className="h-1 w-24 bg-gradient-to-r from-sky-500 to-blue-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="flex-1 flex flex-col gap-4">
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-sky-200/50 shadow-xl shadow-sky-200/20 p-4">
                <h2 className="text-xl font-bold text-sky-800 mb-4 flex items-center gap-2">
                  <Coins size={20} className="text-sky-600" />
                  计算诉讼费
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
                    <label className="block text-sm font-medium text-sky-700 mb-2">诉讼请求金额 (元)</label>
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
                    <p className="text-sm text-sky-600 mb-2">应交纳案件受理费</p>
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