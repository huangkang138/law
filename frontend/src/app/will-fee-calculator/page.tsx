'use client';

import { useState, useEffect } from 'react';
import { ScrollText, Plus, Trash2, Pin, Edit, MoreHorizontal, Settings } from 'lucide-react';
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

export default function WillFeeCalculatorPage() {
  const [form, setForm] = useState({ will_type: 'notarized', estate_value: '' });
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/will-fee`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }, 5000);
      const data = await res.json();
      if (data.success) {
        // 计算过程
        const estateValue = parseFloat(form.estate_value) || 0;
        const willType = form.will_type;
        
        let notaryFee = 0;
        let attorneyFee = 0;
        let steps: string[] = [];
        let rules: string[] = [];
        let legalBasis: string[] = [];
        let formula = '';
        
        if (willType === 'notarized') {
          // 公证遗嘱费用计算
          if (estateValue <= 200000) {
            notaryFee = 500;
            formula = '公证费 = 固定费用 500元';
            steps = [
              `遗嘱类型: 公证遗嘱`,
              `遗产价值: ¥${estateValue.toLocaleString()}`,
              `收费档次: 20万元以下`,
              `公证费: ¥500`
            ];
          } else if (estateValue <= 500000) {
            notaryFee = 500 + (estateValue - 200000) * 0.003;
            formula = '公证费 = 500元 + (遗产价值 - 20万元) × 0.3%';
            steps = [
              `遗嘱类型: 公证遗嘱`,
              `遗产价值: ¥${estateValue.toLocaleString()}`,
              `收费档次: 20万-50万元`,
              `基础费用: ¥500`,
              `超额部分: ¥${(estateValue - 200000).toLocaleString()}`,
              `超额费用: ¥${(estateValue - 200000).toLocaleString()} × 0.3% = ¥${((estateValue - 200000) * 0.003).toLocaleString()}`,
              `公证费: ¥500 + ¥${((estateValue - 200000) * 0.003).toLocaleString()} = ¥${notaryFee.toLocaleString()}`
            ];
          } else if (estateValue <= 1000000) {
            notaryFee = 500 + 300000 * 0.003 + (estateValue - 500000) * 0.002;
            formula = '公证费 = 500元 + 30万元 × 0.3% + (遗产价值 - 50万元) × 0.2%';
            steps = [
              `遗嘱类型: 公证遗嘱`,
              `遗产价值: ¥${estateValue.toLocaleString()}`,
              `收费档次: 50万-100万元`,
              `第一段（20万元以下）: ¥500`,
              `第二段（20万-50万元）: ¥300,000 × 0.3% = ¥900`,
              `第三段（50万-100万元）: ¥${(estateValue - 500000).toLocaleString()} × 0.2% = ¥${((estateValue - 500000) * 0.002).toLocaleString()}`,
              `公证费: ¥500 + ¥900 + ¥${((estateValue - 500000) * 0.002).toLocaleString()} = ¥${notaryFee.toLocaleString()}`
            ];
          } else {
            notaryFee = 500 + 300000 * 0.003 + 500000 * 0.002 + (estateValue - 1000000) * 0.001;
            formula = '公证费 = 500元 + 30万元 × 0.3% + 50万元 × 0.2% + (遗产价值 - 100万元) × 0.1%';
            steps = [
              `遗嘱类型: 公证遗嘱`,
              `遗产价值: ¥${estateValue.toLocaleString()}`,
              `收费档次: 100万元以上`,
              `第一段（20万元以下）: ¥500`,
              `第二段（20万-50万元）: ¥300,000 × 0.3% = ¥900`,
              `第三段（50万-100万元）: ¥500,000 × 0.2% = ¥1,000`,
              `第四段（100万元以上）: ¥${(estateValue - 1000000).toLocaleString()} × 0.1% = ¥${((estateValue - 1000000) * 0.001).toLocaleString()}`,
              `公证费: ¥500 + ¥900 + ¥1,000 + ¥${((estateValue - 1000000) * 0.001).toLocaleString()} = ¥${notaryFee.toLocaleString()}`
            ];
          }
          attorneyFee = 3000;
          rules = [
            '1. 公证遗嘱费用按照遗产价值分段累计计算',
            '2. 不超过20万元的，收取500元',
            '3. 超过20万元至50万元的部分，按照0.3%收取',
            '4. 超过50万元至100万元的部分，按照0.2%收取',
            '5. 超过100万元的部分，按照0.1%收取',
            '6. 公证遗嘱需要公证员见证，具有最高法律效力',
            '7. 律师费一般为固定费用3000-10000元'
          ];
          legalBasis = [
            '《公证法》',
            '《民法典》继承编',
            '《公证程序规则》'
          ];
        } else if (willType === 'self_written') {
          // 自书遗嘱费用计算
          notaryFee = 0;
          attorneyFee = 2000;
          formula = '费用 = 律师咨询费（固定）';
          steps = [
            `遗嘱类型: 自书遗嘱`,
            `遗产价值: ¥${estateValue.toLocaleString()}`,
            `公证费: ¥0（自书遗嘱无需公证）`,
            `律师咨询费: ¥2,000`
          ];
          rules = [
            '1. 自书遗嘱由立遗嘱人亲笔书写、签名，注明年、月、日',
            '2. 自书遗嘱无需公证，但建议咨询律师确保合法性',
            '3. 自书遗嘱需要立遗嘱人具有完全民事行为能力',
            '4. 自书遗嘱内容必须真实、合法',
            '5. 律师咨询费一般为2000-5000元'
          ];
          legalBasis = [
            '《民法典》第一千一百三十四条',
            '《民法典》继承编',
            '《律师服务收费管理办法》'
          ];
        } else {
          // 律师见证遗嘱费用计算
          if (estateValue <= 200000) {
            notaryFee = 0;
            attorneyFee = 5000;
            formula = '费用 = 律师见证费（固定）';
            steps = [
              `遗嘱类型: 律师见证遗嘱`,
              `遗产价值: ¥${estateValue.toLocaleString()}`,
              `公证费: ¥0（律师见证无需公证）`,
              `律师见证费: ¥5,000`
            ];
          } else if (estateValue <= 500000) {
            notaryFee = 0;
            attorneyFee = 5000 + (estateValue - 200000) * 0.005;
            formula = '费用 = 5000元 + (遗产价值 - 20万元) × 0.5%';
            steps = [
              `遗嘱类型: 律师见证遗嘱`,
              `遗产价值: ¥${estateValue.toLocaleString()}`,
              `收费档次: 20万-50万元`,
              `基础费用: ¥5,000`,
              `超额部分: ¥${(estateValue - 200000).toLocaleString()}`,
              `超额费用: ¥${(estateValue - 200000).toLocaleString()} × 0.5% = ¥${((estateValue - 200000) * 0.005).toLocaleString()}`,
              `律师见证费: ¥5,000 + ¥${((estateValue - 200000) * 0.005).toLocaleString()} = ¥${attorneyFee.toLocaleString()}`
            ];
          } else if (estateValue <= 1000000) {
            notaryFee = 0;
            attorneyFee = 5000 + 300000 * 0.005 + (estateValue - 500000) * 0.004;
            formula = '费用 = 5000元 + 30万元 × 0.5% + (遗产价值 - 50万元) × 0.4%';
            steps = [
              `遗嘱类型: 律师见证遗嘱`,
              `遗产价值: ¥${estateValue.toLocaleString()}`,
              `收费档次: 50万-100万元`,
              `第一段（20万元以下）: ¥5,000`,
              `第二段（20万-50万元）: ¥300,000 × 0.5% = ¥1,500`,
              `第三段（50万-100万元）: ¥${(estateValue - 500000).toLocaleString()} × 0.4% = ¥${((estateValue - 500000) * 0.004).toLocaleString()}`,
              `律师见证费: ¥5,000 + ¥1,500 + ¥${((estateValue - 500000) * 0.004).toLocaleString()} = ¥${attorneyFee.toLocaleString()}`
            ];
          } else {
            notaryFee = 0;
            attorneyFee = 5000 + 300000 * 0.005 + 500000 * 0.004 + (estateValue - 1000000) * 0.003;
            formula = '费用 = 5000元 + 30万元 × 0.5% + 50万元 × 0.4% + (遗产价值 - 100万元) × 0.3%';
            steps = [
              `遗嘱类型: 律师见证遗嘱`,
              `遗产价值: ¥${estateValue.toLocaleString()}`,
              `收费档次: 100万元以上`,
              `第一段（20万元以下）: ¥5,000`,
              `第二段（20万-50万元）: ¥300,000 × 0.5% = ¥1,500`,
              `第三段（50万-100万元）: ¥500,000 × 0.4% = ¥2,000`,
              `第四段（100万元以上）: ¥${(estateValue - 1000000).toLocaleString()} × 0.3% = ¥${((estateValue - 1000000) * 0.003).toLocaleString()}`,
              `律师见证费: ¥5,000 + ¥1,500 + ¥2,000 + ¥${((estateValue - 1000000) * 0.003).toLocaleString()} = ¥${attorneyFee.toLocaleString()}`
            ];
          }
          rules = [
            '1. 律师见证遗嘱由律师见证立遗嘱人签署遗嘱',
            '2. 律师见证遗嘱具有较高法律效力',
            '3. 律师见证费按照遗产价值分段累计计算',
            '4. 不超过20万元的，收取5000元',
            '5. 超过20万元至50万元的部分，按照0.5%收取',
            '6. 超过50万元至100万元的部分，按照0.4%收取',
            '7. 超过100万元的部分，按照0.3%收取'
          ];
          legalBasis = [
            '《民法典》第一千一百三十五条',
            '《律师服务收费管理办法》',
            '《律师见证业务规则》'
          ];
        }
        
        const totalFee = notaryFee + attorneyFee;
        
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
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/will-fee`);
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

  const willTypes = [
    { value: 'notarized', label: '公证遗嘱' },
    { value: 'self_written', label: '自书遗嘱' },
    { value: 'attorney_witness', label: '律师见证' }
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
              onClick={() => { setResult(null); setForm({ will_type: 'notarized', estate_value: '' }); }}
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
                      {willTypes.find(t => t.value === item.will_type)?.label}
                    </p>
                    <p className="text-xs text-sky-600">
                      ¥{parseFloat(item.estate_value).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sky-700 flex-shrink-0">¥{parseFloat(item.total_fee).toLocaleString()}</span>
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
                      handleStartEdit(idx.toString(), willTypes.find(t => t.value === item.will_type)?.label || '遗嘱费用计算');
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
              <h1 className="text-2xl font-bold text-sky-700 mb-1">遗嘱费用计算器</h1>
              <p className="text-sm text-gray-700">计算遗嘱公证及相关费用</p>
              <div className="h-1 w-24 bg-gradient-to-r from-sky-500 to-blue-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="flex-1 flex flex-col gap-4">
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-sky-200/50 shadow-xl shadow-sky-200/20 p-4">
                <h2 className="text-xl font-bold text-sky-800 mb-4 flex items-center gap-2">
                  <ScrollText size={20} className="text-sky-600" />
                  计算遗嘱费用
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-sky-700 mb-2">遗嘱类型</label>
                    <select
                      value={form.will_type}
                      onChange={(e) => setForm({ ...form, will_type: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 focus:border-transparent outline-none transition-all"
                    >
                      {willTypes.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-sky-700 mb-2">遗产价值 (元)</label>
                    <input
                      type="number"
                      value={form.estate_value}
                      onChange={(e) => setForm({ ...form, estate_value: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 focus:border-transparent outline-none transition-all"
                      placeholder="请输入遗产价值"
                    />
                  </div>

                  <button
                    onClick={calculate}
                    disabled={loading}
                    className="w-full py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold rounded-xl hover:from-sky-600 hover:to-blue-700 transition-all duration-300 shadow-lg shadow-sky-300/30 disabled:opacity-50"
                  >
                    {loading ? '计算中...' : '开始计算'}
                  </button>
                </div>
              </div>

              {result && (
                <div className="flex-1 bg-gradient-to-br from-sky-50 to-blue-50 rounded-2xl border border-sky-200 p-4">
                  <h3 className="text-xl font-bold text-sky-800 mb-4">费用明细</h3>
                  <div className="space-y-3 mb-4">
                    <div className="flex justify-between">
                      <span className="text-sky-600">公证费</span>
                      <span className="font-semibold">¥{result.notary_fee?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sky-600">律师费</span>
                      <span className="font-semibold">¥{result.attorney_fee?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between pt-3 border-t border-sky-300">
                      <span className="text-sky-700 font-bold">总计</span>
                      <span className="font-bold text-sky-800">¥{result.total_fee?.toLocaleString()}</span>
                    </div>
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
