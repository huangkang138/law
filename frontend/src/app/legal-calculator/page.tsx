'use client';

import { useState, useEffect } from 'react';
import { Calculator, DollarSign, Users, Car, History, Plus, FileText, Trash2, Pin, Edit, MoreHorizontal, Settings } from 'lucide-react';
import Link from 'next/link';

const API_BASE = '/api';

export default function LegalCalculatorPage() {
  const [activeTab, setActiveTab] = useState('interest');
  const [results, setResults] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const [interestForm, setInterestForm] = useState({ principal: '', annual_rate: '', days: '' });
  const [laborForm, setLaborForm] = useState({ monthly_salary: '', years: '', months: '' });
  const [trafficForm, setTrafficForm] = useState({ medical_expense: '', lost_income: '', disability_level: '10' });

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

  const calculateInterest = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/interest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(interestForm)
      }, 5000);
      const data = await res.json();
      if (data.success) {
        // 计算过程
        const principal = parseFloat(interestForm.principal) || 0;
        const annualRate = parseFloat(interestForm.annual_rate) || 0;
        const days = parseFloat(interestForm.days) || 0;
        const dailyRate = annualRate / 100 / 365;
        const interest = principal * dailyRate * days;
        const totalAmount = principal + interest;
        
        // 添加计算过程到结果中
        const resultWithCalculation = {
          ...data.data,
          calculation: {
            formula: '利息 = 本金 × 年利率 ÷ 365 × 天数',
            steps: [
              `本金: ¥${principal.toLocaleString()}`,
              `年利率: ${annualRate}%`,
              `天数: ${days}天`,
              `日利率: ${(dailyRate * 100).toFixed(6)}%`,
              `利息计算: ¥${principal.toLocaleString()} × ${(dailyRate * 100).toFixed(6)}% × ${days}天 = ¥${interest.toFixed(2)}`,
              `本息合计: ¥${principal.toLocaleString()} + ¥${interest.toFixed(2)} = ¥${totalAmount.toFixed(2)}`
            ],
            rules: [
              '1. 利息计算采用单利计算方式',
              '2. 一年按365天计算',
              '3. 计算公式适用于一般借贷利息计算',
              '4. 实际利息可能受法律规定的最高利率限制'
            ]
          }
        };
        setResults(resultWithCalculation);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const calculateLabor = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/labor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(laborForm)
      }, 5000);
      const data = await res.json();
      if (data.success) {
        // 计算过程
        const monthlySalary = parseFloat(laborForm.monthly_salary) || 0;
        const years = parseFloat(laborForm.years) || 0;
        const months = parseFloat(laborForm.months) || 0;
        const totalMonths = years * 12 + months;
        const compensation = monthlySalary * totalMonths;
        
        // 添加计算过程到结果中
        const resultWithCalculation = {
          ...data.data,
          calculation: {
            formula: '经济补偿金 = 月工资 × (工作年限 × 12 + 额外月份)',
            steps: [
              `月工资: ¥${monthlySalary.toLocaleString()}`,
              `工作年限: ${years}年`,
              `额外月份: ${months}个月`,
              `总月份数: ${years}年 × 12个月/年 + ${months}个月 = ${totalMonths}个月`,
              `经济补偿金: ¥${monthlySalary.toLocaleString()} × ${totalMonths}个月 = ¥${compensation.toFixed(2)}`
            ],
            rules: [
              '1. 经济补偿金按劳动者在本单位工作的年限计算',
              '2. 每满一年支付一个月工资的标准向劳动者支付',
              '3. 六个月以上不满一年的，按一年计算',
              '4. 不满六个月的，向劳动者支付半个月工资的经济补偿',
              '5. 月工资是指劳动者在劳动合同解除或者终止前十二个月的平均工资'
            ]
          }
        };
        setResults(resultWithCalculation);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const calculateTraffic = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/traffic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trafficForm)
      }, 5000);
      const data = await res.json();
      if (data.success) {
        // 计算过程
        const medicalExpense = parseFloat(trafficForm.medical_expense) || 0;
        const lostIncome = parseFloat(trafficForm.lost_income) || 0;
        const disabilityLevel = parseInt(trafficForm.disability_level) || 10;
        
        // 伤残赔偿金计算（假设按城镇居民人均可支配收入计算）
        const disabilityRate = (11 - disabilityLevel) * 10 / 100;
        const disabilityCompensation = 49283 * 20 * disabilityRate; // 假设2023年城镇居民人均可支配收入为49283元
        
        // 其他费用估算
        const nutritionFee = 30 * 90; // 营养费：30元/天 × 90天
        const careFee = 120 * 90; // 护理费：120元/天 × 90天
        const transportationFee = 1000; // 交通费：1000元
        const mentalDamage = 5000 * (11 - disabilityLevel); // 精神损害抚慰金：根据伤残等级
        
        const totalCompensation = medicalExpense + lostIncome + disabilityCompensation + nutritionFee + careFee + transportationFee + mentalDamage;
        
        // 添加计算过程到结果中
        const resultWithCalculation = {
          ...data.data,
          calculation: {
            formula: '总赔偿 = 医疗费 + 误工费 + 伤残赔偿金 + 营养费 + 护理费 + 交通费 + 精神损害抚慰金',
            steps: [
              `医疗费: ¥${medicalExpense.toLocaleString()}`,
              `误工费: ¥${lostIncome.toLocaleString()}`,
              `伤残等级: ${disabilityLevel}级`,
              `伤残赔偿系数: ${disabilityRate * 100}%`,
              `伤残赔偿金: 49283元/年 × 20年 × ${disabilityRate * 100}% = ¥${disabilityCompensation.toFixed(2)}`,
              `营养费: 30元/天 × 90天 = ¥${nutritionFee.toFixed(2)}`,
              `护理费: 120元/天 × 90天 = ¥${careFee.toFixed(2)}`,
              `交通费: ¥${transportationFee.toFixed(2)}`,
              `精神损害抚慰金: ¥${mentalDamage.toFixed(2)}`,
              `总赔偿: ¥${totalCompensation.toFixed(2)}`
            ],
            rules: [
              '1. 医疗费：根据医疗机构出具的医药费、住院费等收款凭证确定',
              '2. 误工费：根据受害人的误工时间和收入状况确定',
              '3. 伤残赔偿金：根据伤残等级，按照受诉法院所在地上一年度城镇居民人均可支配收入标准计算',
              '4. 营养费：根据受害人伤残情况参照医疗机构的意见确定',
              '5. 护理费：根据护理人员的收入状况和护理人数、护理期限确定',
              '6. 交通费：根据受害人及其必要的陪护人员因就医或者转院治疗实际发生的费用计算',
              '7. 精神损害抚慰金：根据侵权人的过错程度、侵权行为所造成的后果等因素确定'
            ]
          }
        };
        setResults(resultWithCalculation);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const loadHistory = async () => {
    try {
      const endpoints = {
        interest: '/legal-tools/interest',
        labor: '/legal-tools/labor',
        traffic: '/legal-tools/traffic'
      };
      const res = await fetchWithTimeout(`${API_BASE}${endpoints[activeTab as keyof typeof endpoints]}`, {}, 3000);
      const data = await res.json();
      if (data.success) setHistory(data.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    setResults(null);
    const timer = setTimeout(() => {
      loadHistory();
    }, 500);
    return () => clearTimeout(timer);
  }, [activeTab]);

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

  const tabNames: Record<string, string> = {
    interest: '利息计算',
    labor: '劳动补偿',
    traffic: '交通事故'
  };

  return (
    <div className="fixed business-page-shell left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 text-foreground flex">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="relative z-10 w-64 h-full bg-white/80 backdrop-blur-md border-r border-sky-200 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">历史记录</h2>
            <button
              onClick={() => { setResults(null); setActiveTab('interest'); }}
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
              <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-200/50">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-blue-600">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-blue-700">
                      {item.interest && `¥${item.interest}`}
                      {item.compensation && `¥${item.compensation}`}
                      {item.total_compensation && `¥${item.total_compensation}`}
                    </span>
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
                      handleStartEdit(idx.toString(), '计算记录');
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
              <h1 className="text-2xl font-bold text-sky-700 mb-1">法律计算器</h1>
              <p className="text-sm text-gray-700">专业的法律相关费用和赔偿计算工具</p>
              <div className="h-1 w-24 bg-gradient-to-r from-sky-500 to-blue-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="flex-1 flex flex-col gap-4">
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-blue-200/50 shadow-xl shadow-blue-200/20 p-4">
                <div className="flex border-b border-blue-200/50 mb-4">
                  {[
                    { id: 'interest', name: '利息计算', icon: DollarSign },
                    { id: 'labor', name: '劳动补偿', icon: Users },
                    { id: 'traffic', name: '交通事故', icon: Car }
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 font-medium transition-all duration-300 ${
                          activeTab === tab.id
                            ? 'bg-gradient-to-r from-blue-400/20 to-indigo-400/10 text-blue-700 border-b-2 border-blue-500'
                            : 'text-blue-600/60 hover:text-blue-700 hover:bg-blue-50/50'
                        }`}
                      >
                        <Icon size={18} />
                        <span className="text-sm">{tab.name}</span>
                      </button>
                    );
                  })}
                </div>

                <div className="space-y-4">
                  {activeTab === 'interest' && (
                    <div className="space-y-4">
                      <h2 className="text-xl font-bold text-blue-800 flex items-center gap-2">
                        <DollarSign size={20} className="text-blue-600" />
                        利息计算
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">本金 (元)</label>
                          <input
                            type="number"
                            value={interestForm.principal}
                            onChange={(e) => setInterestForm({ ...interestForm, principal: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                            placeholder="请输入本金"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">年利率 (%)</label>
                          <input
                            type="number"
                            step="0.01"
                            value={interestForm.annual_rate}
                            onChange={(e) => setInterestForm({ ...interestForm, annual_rate: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                            placeholder="请输入年利率"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">天数</label>
                          <input
                            type="number"
                            value={interestForm.days}
                            onChange={(e) => setInterestForm({ ...interestForm, days: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                            placeholder="请输入天数"
                          />
                        </div>
                      </div>
                      <button
                        onClick={calculateInterest}
                        disabled={loading}
                        className="w-full py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 shadow-lg shadow-blue-300/30 disabled:opacity-50"
                      >
                        {loading ? '计算中...' : '开始计算'}
                      </button>
                    </div>
                  )}

                  {activeTab === 'labor' && (
                    <div className="space-y-4">
                      <h2 className="text-xl font-bold text-blue-800 flex items-center gap-2">
                        <Users size={20} className="text-blue-600" />
                        劳动补偿金计算
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">月工资 (元)</label>
                          <input
                            type="number"
                            value={laborForm.monthly_salary}
                            onChange={(e) => setLaborForm({ ...laborForm, monthly_salary: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                            placeholder="请输入月工资"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">工作年限 (年)</label>
                          <input
                            type="number"
                            value={laborForm.years}
                            onChange={(e) => setLaborForm({ ...laborForm, years: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                            placeholder="请输入工作年数"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">额外月份</label>
                          <input
                            type="number"
                            value={laborForm.months}
                            onChange={(e) => setLaborForm({ ...laborForm, months: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                            placeholder="额外月份数"
                          />
                        </div>
                      </div>
                      <button
                        onClick={calculateLabor}
                        disabled={loading}
                        className="w-full py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 shadow-lg shadow-blue-300/30 disabled:opacity-50"
                      >
                        {loading ? '计算中...' : '开始计算'}
                      </button>
                    </div>
                  )}

                  {activeTab === 'traffic' && (
                    <div className="space-y-4">
                      <h2 className="text-xl font-bold text-blue-800 flex items-center gap-2">
                        <Car size={20} className="text-blue-600" />
                        交通事故赔偿计算
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">医疗费 (元)</label>
                          <input
                            type="number"
                            value={trafficForm.medical_expense}
                            onChange={(e) => setTrafficForm({ ...trafficForm, medical_expense: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                            placeholder="请输入医疗费"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">误工费 (元)</label>
                          <input
                            type="number"
                            value={trafficForm.lost_income}
                            onChange={(e) => setTrafficForm({ ...trafficForm, lost_income: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                            placeholder="请输入误工费"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-blue-700 mb-2">伤残等级 (1-10)</label>
                          <select
                            value={trafficForm.disability_level}
                            onChange={(e) => setTrafficForm({ ...trafficForm, disability_level: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl border border-blue-200 bg-white/80 focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition-all"
                          >
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                              <option key={n} value={n}>{n}级</option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <button
                        onClick={calculateTraffic}
                        disabled={loading}
                        className="w-full py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 shadow-lg shadow-blue-300/30 disabled:opacity-50"
                      >
                        {loading ? '计算中...' : '开始计算'}
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {results && (
                <div className="flex-1 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border border-blue-200 p-4">
                  <h3 className="text-xl font-bold text-blue-800 mb-4 flex items-center gap-2">
                    <Calculator size={20} />
                    计算结果
                  </h3>
                  {activeTab === 'interest' && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 bg-white rounded-xl">
                          <p className="text-sm text-blue-600">利息金额</p>
                          <p className="text-2xl font-bold text-blue-700">¥{results.interest?.toLocaleString()}</p>
                        </div>
                        <div className="p-4 bg-white rounded-xl">
                          <p className="text-sm text-blue-600">本息合计</p>
                          <p className="text-2xl font-bold text-indigo-700">¥{results.total_amount?.toLocaleString()}</p>
                        </div>
                      </div>
                      {results.calculation && (
                        <div className="space-y-4">
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算公式</h4>
                            <p className="text-blue-800 font-medium">{results.calculation.formula}</p>
                          </div>
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算过程</h4>
                            <ul className="space-y-2 text-blue-800">
                              {results.calculation.steps.map((step: string, index: number) => (
                                <li key={index} className="flex items-start gap-2">
                                  <span className="text-blue-500 font-bold">{index + 1}.</span>
                                  <span>{step}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算细则</h4>
                            <ul className="space-y-2 text-blue-800">
                              {results.calculation.rules.map((rule: string, index: number) => (
                                <li key={index} className="flex items-start gap-2">
                                  <span className="text-blue-500 font-bold">•</span>
                                  <span>{rule}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {activeTab === 'labor' && (
                    <div className="space-y-4">
                      <div className="p-4 bg-white rounded-xl">
                        <p className="text-sm text-blue-600">经济补偿金</p>
                        <p className="text-3xl font-bold text-blue-700">¥{results.compensation?.toLocaleString()}</p>
                      </div>
                      {results.calculation && (
                        <div className="space-y-4">
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算公式</h4>
                            <p className="text-blue-800 font-medium">{results.calculation.formula}</p>
                          </div>
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算过程</h4>
                            <ul className="space-y-2 text-blue-800">
                              {results.calculation.steps.map((step: string, index: number) => (
                                <li key={index} className="flex items-start gap-2">
                                  <span className="text-blue-500 font-bold">{index + 1}.</span>
                                  <span>{step}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算细则</h4>
                            <ul className="space-y-2 text-blue-800">
                              {results.calculation.rules.map((rule: string, index: number) => (
                                <li key={index} className="flex items-start gap-2">
                                  <span className="text-blue-500 font-bold">•</span>
                                  <span>{rule}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {activeTab === 'traffic' && (
                    <div className="space-y-4">
                      <div className="p-4 bg-white rounded-xl">
                        <p className="text-sm text-blue-600">赔偿总额</p>
                        <p className="text-3xl font-bold text-blue-700">¥{results.total_compensation?.toLocaleString()}</p>
                      </div>
                      {results.details && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {Object.entries(results.details).map(([key, value]: any) => (
                            <div key={key} className="p-3 bg-white rounded-lg text-center">
                              <p className="text-xs text-blue-600">
                                {key === 'medical_expense' && '医疗费'}
                                {key === 'lost_income' && '误工费'}
                                {key === 'disability_compensation' && '伤残赔偿'}
                                {key === 'nutrition_fee' && '营养费'}
                                {key === 'care_fee' && '护理费'}
                                {key === 'transportation_fee' && '交通费'}
                                {key === 'mental_damage' && '精神损害'}
                              </p>
                              <p className="font-bold text-blue-700">¥{value.toLocaleString()}</p>
                            </div>
                          ))}
                        </div>
                      )}
                      {results.calculation && (
                        <div className="space-y-4">
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算公式</h4>
                            <p className="text-blue-800 font-medium">{results.calculation.formula}</p>
                          </div>
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算过程</h4>
                            <ul className="space-y-2 text-blue-800">
                              {results.calculation.steps.map((step: string, index: number) => (
                                <li key={index} className="flex items-start gap-2">
                                  <span className="text-blue-500 font-bold">{index + 1}.</span>
                                  <span>{step}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div className="p-4 bg-white rounded-xl">
                            <h4 className="text-lg font-semibold text-blue-700 mb-2">计算细则</h4>
                            <ul className="space-y-2 text-blue-800">
                              {results.calculation.rules.map((rule: string, index: number) => (
                                <li key={index} className="flex items-start gap-2">
                                  <span className="text-blue-500 font-bold">•</span>
                                  <span>{rule}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}
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