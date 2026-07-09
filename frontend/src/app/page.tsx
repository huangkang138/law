'use client';

import { FileText, MessageSquare, Shield, Zap, Sparkles, Star, Crown, BookOpen, Network, Settings, FileSearch, Scale, Gavel, GitBranch, BookMarked, FolderOpen, FileCheck, ClipboardList } from 'lucide-react';
import ScaleIcon from '@/components/ScaleIcon';
import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';

export default function HomePage() {
  const [mounted, setMounted] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="relative min-h-screen">
      {/* 固定背景层 */}
      <div className="fixed inset-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100">
        {/* 星空背景效果 */}
        <div className="absolute inset-0 overflow-hidden">
          {mounted && [...Array(80)].map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full bg-gradient-to-r from-sky-300 via-blue-400 to-indigo-400 animate-pulse"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                width: `${Math.random() * 4 + 1}px`,
                height: `${Math.random() * 4 + 1}px`,
                opacity: Math.random() * 0.6 + 0.2,
                animationDelay: `${Math.random() * 3}s`,
                animationDuration: `${2 + Math.random() * 3}s`,
              }}
            />
          ))}
        </div>

        {/* 星空光晕效果 */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      {/* 可滚动内容层 */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-4 pb-20 -mt-8">
        {/* 顶部装饰 - 蓝色装饰线 */}
        <div className="fixed top-0 left-0 right-0 h-4 bg-gradient-to-r from-sky-300 via-blue-400 to-indigo-300 z-50" />
        <div className="fixed top-4 left-0 right-0 h-1 bg-blue-300 z-50" />

        {/* 中央Logo + 环绕标题 */}
        <div className="mb-16 animate-float mt-12" ref={heroRef}>
          <div className="relative w-64 h-64 mx-auto">
            {/* 外层蓝色光环 */}
            <div className="absolute inset-0 animate-spin-slow">
              <div className="h-64 w-64 rounded-full border-2 border-dashed border-blue-400/60" />
            </div>
            <div className="absolute inset-0 animate-spin-reverse">
              <div className="h-64 w-64 rounded-full border-2 border-dotted border-sky-300/40" />
            </div>
            
            {/* Logo容器 */}
            <div className="absolute top-6 left-6 right-6 bottom-14 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-sky-400/30 via-blue-500/30 to-indigo-400/30 blur-2xl animate-pulse-slow" />
              <div className="relative flex h-40 w-40 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 shadow-2xl border-2 border-blue-300">
                <ScaleIcon size={112} className="text-white" withFire={false} />
              </div>
            </div>
            
            {/* 环绕文字 - 法惠民生（下半圆四个方位） */}
            {/* 法 - 左下 */}
            <div className="absolute -bottom-2 -left-20 animate-fadeIn" style={{ animationDelay: '0.2s' }}>
              <span className="text-7xl md:text-8xl font-black bg-gradient-to-br from-sky-400 via-blue-500 to-indigo-500 bg-clip-text text-transparent drop-shadow-lg"
                style={{ textShadow: '0 0 40px rgba(96, 165, 250, 0.6)' }}>
                法
              </span>
            </div>
            
            {/* 惠 - 左中下 */}
            <div className="absolute -bottom-16 left-4 animate-fadeIn" style={{ animationDelay: '0.4s' }}>
              <span className="text-7xl md:text-8xl font-black bg-gradient-to-br from-sky-400 via-blue-500 to-indigo-500 bg-clip-text text-transparent drop-shadow-lg"
                style={{ textShadow: '0 0 40px rgba(96, 165, 250, 0.6)' }}>
                惠
              </span>
            </div>
            
            {/* 民 - 右中下 */}
            <div className="absolute -bottom-16 right-4 animate-fadeIn" style={{ animationDelay: '0.6s' }}>
              <span className="text-7xl md:text-8xl font-black bg-gradient-to-br from-sky-400 via-blue-500 to-indigo-500 bg-clip-text text-transparent drop-shadow-lg"
                style={{ textShadow: '0 0 40px rgba(96, 165, 250, 0.6)' }}>
                民
              </span>
            </div>
            
            {/* 生 - 右下 */}
            <div className="absolute -bottom-2 -right-20 animate-fadeIn" style={{ animationDelay: '0.8s' }}>
              <span className="text-7xl md:text-8xl font-black bg-gradient-to-br from-sky-400 via-blue-500 to-indigo-500 bg-clip-text text-transparent drop-shadow-lg"
                style={{ textShadow: '0 0 40px rgba(96, 165, 250, 0.6)' }}>
                生
              </span>
            </div>
          </div>
        </div>

        {/* 副标题 */}
        <div className="text-center mb-8 animate-fadeIn">
          <div className="relative">
            <p className="text-xl md:text-2xl text-blue-700/90 font-light tracking-widest">
              <span className="inline-block animate-fadeIn-up" style={{ animationDelay: '1s' }}>基</span>
              <span className="inline-block animate-fadeIn-up" style={{ animationDelay: '1.1s' }}>于</span>
              <span className="inline-block animate-fadeIn-up" style={{ animationDelay: '1.2s' }}>腾</span>
              <span className="inline-block animate-fadeIn-up" style={{ animationDelay: '1.3s' }}>讯</span>
              <span className="inline-block animate-fadeIn-up" style={{ animationDelay: '1.4s' }}>开</span>
              <span className="inline-block animate-fadeIn-up" style={{ animationDelay: '1.5s' }}>悟</span>
              <span className="inline-block animate-fadeIn-up mx-2" style={{ animationDelay: '1.6s' }}>的</span>
              <span className="inline-block animate-fadeIn-up text-blue-500 font-medium" style={{ animationDelay: '1.7s' }}>智</span>
              <span className="inline-block animate-fadeIn-up text-blue-500 font-medium" style={{ animationDelay: '1.8s' }}>能</span>
              <span className="inline-block animate-fadeIn-up text-blue-500 font-medium" style={{ animationDelay: '1.9s' }}>法</span>
              <span className="inline-block animate-fadeIn-up text-blue-500 font-medium" style={{ animationDelay: '2s' }}>务</span>
              <span className="inline-block animate-fadeIn-up text-blue-500 font-medium" style={{ animationDelay: '2.1s' }}>服</span>
              <span className="inline-block animate-fadeIn-up text-blue-500 font-medium" style={{ animationDelay: '2.2s' }}>务</span>
              <span className="inline-block animate-fadeIn-up text-blue-500 font-medium" style={{ animationDelay: '2.3s' }}>平</span>
              <span className="inline-block animate-fadeIn-up text-blue-500 font-medium" style={{ animationDelay: '2.4s' }}>台</span>
            </p>
            
            {/* 副标题装饰线 */}
            <div className="flex items-center justify-center gap-4 mt-4">
              <div className="w-16 h-px bg-gradient-to-r from-transparent to-blue-400/60" />
              <div className="w-2 h-2 rotate-45 bg-blue-400/80" />
              <div className="w-24 h-px bg-gradient-to-r from-blue-400/60 via-blue-400 to-blue-400/60" />
              <div className="w-2 h-2 rotate-45 bg-blue-400/80" />
              <div className="w-16 h-px bg-gradient-to-l from-transparent to-blue-400/60" />
            </div>
          </div>
        </div>

        {/* 核心价值观标签 */}
        <div className="mb-10 flex flex-wrap items-center justify-center gap-4 animate-fadeIn" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center gap-2 rounded-full border border-blue-400/30 bg-blue-400/10 px-4 py-2 backdrop-blur-sm">
            <Crown size={16} className="text-blue-500" />
            <span className="text-sm text-blue-600">公平正义</span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-400/10 px-4 py-2 backdrop-blur-sm">
            <Shield size={16} className="text-sky-500" />
            <span className="text-sm text-sky-600">服务民生</span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-400/10 px-4 py-2 backdrop-blur-sm">
            <Star size={16} className="text-indigo-500" />
            <span className="text-sm text-indigo-600">智能高效</span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-blue-400/30 bg-blue-400/10 px-4 py-2 backdrop-blur-sm">
            <BookOpen size={16} className="text-blue-500" />
            <span className="text-sm text-blue-600">专业权威</span>
          </div>
        </div>

        {/* 主要功能卡片区域 - 同一行 */}
        <div className="w-full max-w-6xl mx-auto mb-12 animate-fadeIn" style={{ animationDelay: '0.4s' }}>
          <div className="flex justify-center flex-wrap gap-6">
            <Link href="/knowledge-graph">
              <div className="group relative overflow-hidden rounded-2xl border border-blue-400/30 bg-white/70 p-6 backdrop-blur-sm transition-all hover:scale-105 hover:border-blue-400/60 hover:shadow-2xl hover:shadow-blue-300/20 w-52 h-52 flex flex-col">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                <div className="relative flex-1 flex flex-col">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-500 shadow-lg border border-blue-300/50">
                    <Network className="text-white" size={24} />
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-blue-700">图谱管理</h3>
                  <p className="text-sm text-blue-800 flex-1">
                    法律知识图谱可视化，智能分析关联
                  </p>
                </div>
              </div>
            </Link>

            <Link href="/chat">
              <div className="group relative overflow-hidden rounded-2xl border border-blue-400/30 bg-white/70 p-6 backdrop-blur-sm transition-all hover:scale-105 hover:border-blue-400/60 hover:shadow-2xl hover:shadow-blue-300/20 w-52 h-52 flex flex-col">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                <div className="relative flex-1 flex flex-col">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-500 shadow-lg border border-blue-300/50">
                    <MessageSquare className="text-white" size={24} />
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-blue-700">普法问答</h3>
                  <p className="text-sm text-blue-800 flex-1">
                    智能法律咨询，支持多轮对话
                  </p>
                </div>
              </div>
            </Link>

            <Link href="/contract">
              <div className="group relative overflow-hidden rounded-2xl border border-blue-400/30 bg-white/70 p-6 backdrop-blur-sm transition-all hover:scale-105 hover:border-blue-400/60 hover:shadow-2xl hover:shadow-blue-300/20 w-52 h-52 flex flex-col">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                <div className="relative flex-1 flex flex-col">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-500 shadow-lg border border-blue-300/50">
                    <FileText className="text-white" size={24} />
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-blue-700">合同审查</h3>
                  <p className="text-sm text-blue-800 flex-1">
                    AI 深度审查合同条款，识别风险
                  </p>
                </div>
              </div>
            </Link>

            <Link href="/debate">
              <div className="group relative overflow-hidden rounded-2xl border border-blue-400/30 bg-white/70 p-6 backdrop-blur-sm transition-all hover:scale-105 hover:border-blue-400/60 hover:shadow-2xl hover:shadow-blue-300/20 w-52 h-52 flex flex-col">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400/10 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                <div className="relative flex-1 flex flex-col">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-500 shadow-lg border border-blue-300/50">
                    <Shield className="text-white" size={24} />
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-blue-700">模拟法庭</h3>
                  <p className="text-sm text-blue-800 flex-1">
                    多智能体辩论，预测胜诉概率
                  </p>
                </div>
              </div>
            </Link>
          </div>
        </div>

        {/* 核心优势 */}
        <div className="max-w-4xl mx-auto mb-16 animate-fadeIn" style={{ animationDelay: '0.6s' }}>
          <h2 className="text-3xl font-bold text-center text-blue-600 mb-8">核心优势</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-start gap-4 p-4 rounded-xl bg-white/50 border border-blue-300/30">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
                <Zap size={20} className="text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-blue-700 mb-2">腾讯开悟 AI 技术</h3>
                <p className="text-sm text-blue-800">
                  基于腾讯开悟大模型，提供专业、准确的法律分析和推理
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-xl bg-white/50 border border-blue-300/30">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center">
                <Sparkles size={20} className="text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-blue-700 mb-2">多智能体协作</h3>
                <p className="text-sm text-blue-800">
                  法官、原告律师、被告律师多智能体协同，模拟真实法庭场景
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 底部装饰 */}
        <div className="mt-auto">
          <div className="h-1 w-48 bg-gradient-to-r from-sky-300 to-indigo-400 mx-auto rounded-full mb-4" />
          <div className="text-center text-blue-700 text-sm">
            © 2026 法惠民生智能法务服务平台 | 基于腾讯开悟 AI 技术
          </div>
        </div>
      </div>
    </div>
  );
}