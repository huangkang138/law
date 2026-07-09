'use client';

import { useState, useEffect } from 'react';
import { Briefcase, Plus, Trash2, Pin, Edit, MoreHorizontal, Settings } from 'lucide-react';
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

export default function WorkInjuryCalculatorPage() {
  const [form, setForm] = useState({ injury_level: '10', monthly_salary: '' });
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/work-injury`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }, 5000);
      const data = await res.json();
      if (data.success) {
        // 计算过程
        const injuryLevel = parseInt(form.injury_level) || 10;
        const monthlySalary = parseFloat(form.monthly_salary) || 0;
        
        // 一次性伤残补助金计算
        const compensationRates = [27, 25, 23, 21, 18, 16, 13, 11, 9, 7]; // 1-10级对应的月数
        const lumpSumCompensation = monthlySalary * compensationRates[injuryLevel - 1];
        
        // 医疗费（假设）
        const medicalTreatment = 5000;
        
        // 住院伙食补助费（假设）
        const hospitalFood = 30 * 15; // 30元/天 × 15天
        
        // 交通费（假设）
        const transportation = 800;
        
        // 护理费（假设）
        const careFee = 120 * 30; // 120元/天 × 30天
        
        const totalCompensation = lumpSumCompensation + medicalTreatment + hospitalFood + transportation + careFee;
        
        // 添加计算过程到结果中
        const resultWithCalculation = {
          ...data.data,
          calculation: {
            formula: '工伤赔偿总额 = 一次性伤残补助金 + 医疗费 + 住院伙食补助费 + 交通费 + 护理费',
            steps: [
              `伤残等级: ${injuryLevel}级`,
              `本人月工资: ¥${monthlySalary.toLocaleString()}`,
              `一次性伤残补助金系数: ${compensationRates[injuryLevel - 1]}个月`,
              `一次性伤残补助金: ¥${monthlySalary.toLocaleString()} × ${compensationRates[injuryLevel - 1]}个月 = ¥${lumpSumCompensation.toLocaleString()}`,
              `医疗费: ¥${medicalTreatment.toLocaleString()}（根据实际医疗费用结算）`,
              `住院伙食补助费: 30元/天 × 15天 = ¥${hospitalFood.toLocaleString()}`,
              `交通费: ¥${transportation.toLocaleString()}（根据实际交通费用）`,
              `护理费: 120元/天 × 30天 = ¥${careFee.toLocaleString()}`,
              `赔偿总额: ¥${lumpSumCompensation.toLocaleString()} + ¥${medicalTreatment.toLocaleString()} + ¥${hospitalFood.toLocaleString()} + ¥${transportation.toLocaleString()} + ¥${careFee.toLocaleString()} = ¥${totalCompensation.toLocaleString()}`
            ],
            rules: [
              '1. 一次性伤残补助金：根据伤残等级，按本人工资的一定月数计算',
              '2. 一级伤残为27个月，二级为25个月，三级为23个月，四级为21个月',
              '3. 五级伤残为18个月，六级为16个月，七级为13个月，八级为11个月',
              '4. 九级伤残为9个月，十级伤残为7个月',
              '5. 医疗费：符合工伤保险诊疗项目目录、药品目录、住院服务标准的费用',
              '6. 住院伙食补助费：按照统筹地区人民政府规定的标准支付',
              '7. 交通费：经医疗机构出具证明，报经办机构同意，工伤职工到统筹地区以外就医所需的交通费用',
              '8. 护理费：生活不能自理的工伤职工在停工留薪期需要护理的，由所在单位负责'
            ],
            legalBasis: [
              '《工伤保险条例》第三十五条、第三十六条、第三十七条',
              '《工伤认定办法》',
              '《工伤保险待遇标准》'
            ]
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
      const res = await fetchWithTimeout(`${API_BASE}/legal-tools/work-injury`);
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
              onClick={() => { setResult(null); setForm({ injury_level: '10', monthly_salary: '' }); }}
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
                  <span className="text-sm text-sky-700">{item.injury_level}级伤残</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sky-700">¥{parseFloat(item.total_compensation).toLocaleString()}</span>
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
                      handleStartEdit(idx.toString(), `${item.injury_level}级伤残`);
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
              <h1 className="text-2xl font-bold text-sky-700 mb-1">工伤赔偿计算器</h1>
              <p className="text-sm text-gray-700">根据《工伤保险条例》计算工伤赔偿金额</p>
              <div className="h-1 w-24 bg-gradient-to-r from-sky-500 to-blue-500 mx-auto rounded-full mt-2" />
            </div>

            <div className="flex-1 flex flex-col gap-4">
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-sky-200/50 shadow-xl shadow-sky-200/20 p-4">
                <h2 className="text-xl font-bold text-sky-800 mb-4 flex items-center gap-2">
                  <Briefcase size={20} className="text-sky-600" />
                  计算工伤赔偿
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-sky-700 mb-2">伤残等级 (1-10级)</label>
                    <select
                      value={form.injury_level}
                      onChange={(e) => setForm({ ...form, injury_level: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 focus:border-transparent outline-none transition-all"
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
                        <option key={n} value={n}>{n}级伤残</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-sky-700 mb-2">本人月工资 (元)</label>
                    <input
                      type="number"
                      value={form.monthly_salary}
                      onChange={(e) => setForm({ ...form, monthly_salary: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl border border-sky-200 bg-white/80 focus:ring-2 focus:ring-sky-400 focus:border-transparent outline-none transition-all"
                      placeholder="请输入月工资"
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
                  <h3 className="text-xl font-bold text-sky-800 mb-4">计算结果</h3>
                  <div className="text-center mb-4">
                    <p className="text-sm text-sky-600 mb-2">赔偿总额</p>
                    <p className="text-4xl font-bold text-sky-700">¥{result.total_compensation?.toLocaleString()}</p>
                  </div>
                  {result.details && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                      {Object.entries(result.details).map(([key, value]: any) => (
                        <div key={key} className="p-3 bg-white rounded-lg text-center">
                          <p className="text-xs text-sky-600">
                            {key === 'lump_sum_compensation' && '一次性伤残补助金'}
                            {key === 'medical_treatment' && '医疗费'}
                            {key === 'hospital_food' && '住院伙食补助'}
                            {key === 'transportation' && '交通费'}
                            {key === 'care_fee' && '护理费'}
                          </p>
                          <p className="font-bold text-sky-700">¥{value.toLocaleString()}</p>
                        </div>
                      ))}
                    </div>
                  )}
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
