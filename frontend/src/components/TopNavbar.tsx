'use client';

import { useState, useEffect, useRef } from 'react';
import { Menu, X, Home, MessageSquare, FileText, Shield, Settings, Brain, Scale, FolderOpen, History, Network, LayoutGrid, ChevronDown, Calculator, Calendar, Coins, Briefcase, Clock, Users, FileCheck, ShieldAlert, Gavel, FileSpreadsheet, Award, Landmark, ScrollText } from 'lucide-react';
import ScaleIcon from '@/components/ScaleIcon';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';

import type { LucideIcon } from 'lucide-react';

interface MenuItem {
  name: string;
  href: string;
  icon: LucideIcon;
  children?: { name: string; href: string; icon: LucideIcon }[];
}

export default function TopNavbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const dropdownTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  // 处理导航点击
  const handleNavigation = (href: string) => {
    router.push(href);
  };

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (dropdownTimeoutRef.current) {
        clearTimeout(dropdownTimeoutRef.current);
      }
    };
  }, []);

  const handleDropdownMouseEnter = (href: string) => {
    if (dropdownTimeoutRef.current) {
      clearTimeout(dropdownTimeoutRef.current);
      dropdownTimeoutRef.current = null;
    }
    setHoveredItem(href);
    setOpenDropdown(href);
  };

  const handleDropdownMouseLeave = () => {
    dropdownTimeoutRef.current = setTimeout(() => {
      setHoveredItem(null);
      setOpenDropdown(null);
    }, 300);
  };

  const menuItems: MenuItem[] = [
    { name: '首页', href: '/', icon: Home },
    { name: '普法问答', href: '/chat', icon: MessageSquare },
    { name: '合同审查', href: '/contract', icon: FileText },
    {
      name: '法律检索',
      href: '/legal-search',
      icon: Scale,
      children: [
        { name: '法律案情推断', href: '/case-analysis', icon: Brain },
        { name: '相似法律文书', href: '/similar-documents', icon: FileText },
        { name: '相似案件解释', href: '/case-explanation', icon: Brain },
        { name: '法律意见咨询', href: '/document-drafting/legal-opinion', icon: FileText },
      ]
    },
    {
      name: '纠纷管理',
      href: '/dispute-management',
      icon: LayoutGrid,
      children: [
        { name: '纠纷整理', href: '/dispute-organize', icon: FolderOpen },
        { name: '纠纷中心', href: '/dispute-center', icon: LayoutGrid },
      ]
    },
    {
      name: '文件起草',
      href: '/document-drafting',
      icon: FileText,
      children: [
        { name: '文书起草', href: '/document-drafting/legal-document', icon: FileText },
        { name: '合同起草', href: '/document-drafting/contract-drafting', icon: FileText },
      ]
    },
    { name: '模拟法庭', href: '/debate', icon: Shield },
    { name: '法律图谱', href: '/knowledge-graphs', icon: Network },
    {
      name: '辅助工具',
      href: '/legal-tools',
      icon: Calculator,
      children: [
        { name: '法律计算器', href: '/legal-calculator', icon: Calculator },
        { name: '法律日历', href: '/legal-calendar', icon: Calendar },
        { name: '诉讼费计算器', href: '/court-fee-calculator', icon: Coins },
        { name: '工伤赔偿计算', href: '/work-injury-calculator', icon: Briefcase },
        { name: '律师费计算器', href: '/lawyer-fee-calculator', icon: Users },
        { name: '诉讼时效查询', href: '/limitation-checker', icon: Clock },
        { name: '合同违约金计算', href: '/contract-penalty-calculator', icon: FileCheck },
        { name: '保全费计算器', href: '/preservation-fee-calculator', icon: ShieldAlert },
        { name: '执行费计算器', href: '/execution-fee-calculator', icon: Gavel },
        { name: '遗嘱费用计算', href: '/will-fee-calculator', icon: FileSpreadsheet },
        { name: '公告费计算器', href: '/announcement-fee-calculator', icon: Award },
        { name: '鉴定费计算器', href: '/appraisal-fee-calculator', icon: Landmark },
        { name: '仲裁费计算器', href: '/arbitration-fee-calculator', icon: ScrollText },
      ]
    },
    { name: '历史记录', href: '/history', icon: History },
  ];

  const isActive = (href: string) => pathname === href;
  const isChildActive = (children?: { href: string }[]) => {
    return children?.some(child => pathname === child.href) || false;
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-gradient-to-r from-sky-100/95 via-blue-100/95 to-indigo-100/95 backdrop-blur-xl shadow-2xl shadow-blue-200/30'
          : 'bg-gradient-to-r from-sky-100/90 via-blue-100/90 to-indigo-100/90 backdrop-blur-md'
      }`}
    >
      {/* 顶部蓝色装饰线 */}
      <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-blue-400 to-transparent opacity-80" />

      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-4 flex-shrink-0 group">
            <div className="relative">
              <div className="h-12 w-12 rounded-full bg-gradient-to-br from-sky-400 via-blue-500 to-indigo-500 flex items-center justify-center border-2 border-blue-300/80 shadow-lg shadow-blue-200/50 group-hover:shadow-blue-300/30 group-hover:scale-105 transition-all duration-300">
                <ScaleIcon size={36} className="text-white" withFire={false} />
              </div>
              <div className="absolute inset-0 rounded-full bg-blue-400/20 blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 bg-clip-text text-transparent tracking-wider">
                法惠民生
              </h1>
              <p className="text-sm text-blue-600/70 tracking-widest">智能法务服务平台</p>
            </div>
          </Link>

          {/* Desktop Menu - 大气排版 */}
          <nav className="hidden xl:flex items-center gap-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const itemIsActive = isActive(item.href) || isChildActive(item.children);
              const isHovered = hoveredItem === item.href;
              const isDropdownOpen = openDropdown === item.href;

              if (item.children) {
                // 下拉菜单项
                return (
                  <div
                    key={item.name}
                    className="relative"
                    onMouseEnter={() => handleDropdownMouseEnter(item.href)}
                    onMouseLeave={handleDropdownMouseLeave}
                  >
                    <button
                      onClick={() => setOpenDropdown(isDropdownOpen ? null : item.href)}
                      className={`relative flex items-center gap-1.5 px-3 py-2 rounded-xl transition-all duration-300 whitespace-nowrap overflow-hidden ${
                        itemIsActive
                          ? 'bg-gradient-to-r from-blue-400/30 to-indigo-400/20 text-blue-700 shadow-lg shadow-blue-300/20 border border-blue-400/50'
                          : 'text-blue-700/90 hover:text-blue-800 border border-transparent hover:border-blue-400/30'
                      }`}
                    >
                      {/* 背景光效 */}
                      <div
                        className={`absolute inset-0 bg-gradient-to-r from-blue-400/10 to-transparent transition-opacity duration-300 ${
                          isHovered ? 'opacity-100' : 'opacity-0'
                        }`}
                      />

                      {/* 图标容器 */}
                      <div
                        className={`relative flex items-center justify-center w-6 h-6 rounded-lg transition-all duration-300 ${
                          itemIsActive
                            ? 'bg-blue-400/20'
                            : isHovered
                            ? 'bg-blue-400/10 scale-110'
                            : 'bg-transparent'
                        }`}
                      >
                        <Icon
                          size={16}
                          className={`transition-all duration-300 ${
                            itemIsActive ? 'text-blue-600' : isHovered ? 'text-blue-600' : 'text-blue-700/80'
                          }`}
                        />
                      </div>

                      {/* 文字 */}
                      <span
                        className={`relative text-sm font-medium tracking-wide transition-all duration-300 ${
                          itemIsActive ? 'text-blue-800' : ''
                        }`}
                      >
                        {item.name}
                      </span>

                      {/* 下拉箭头 */}
                      <ChevronDown
                        size={12}
                        className={`relative transition-transform duration-300 ${
                          isDropdownOpen ? 'rotate-180' : ''
                        }`}
                      />

                      {/* 底部下划线动画 */}
                      <div
                        className={`absolute bottom-1 left-4 right-4 h-0.5 bg-gradient-to-r from-transparent via-blue-400 to-transparent transition-all duration-300 ${
                          itemIsActive ? 'opacity-100 scale-x-100' : isHovered ? 'opacity-70 scale-x-75' : 'opacity-0 scale-x-0'
                        }`}
                      />
                    </button>

                    {/* 下拉菜单 */}
                    {isDropdownOpen && (
                      <div 
                        className="absolute top-full left-0 mt-1 w-48 py-2 bg-gradient-to-b from-sky-50/95 to-blue-50/95 rounded-xl border border-blue-300/30 backdrop-blur-xl shadow-2xl z-50"
                        onMouseEnter={() => handleDropdownMouseEnter(item.href)}
                        onMouseLeave={handleDropdownMouseLeave}
                      >
                        {item.children.map((child) => {
                          const ChildIcon = child.icon;
                          const childIsActive = isActive(child.href);
                          const isSmallText = child.name === '合同违约金计算';
                          return (
                            <button
                              key={child.href}
                              onClick={() => handleNavigation(child.href)}
                              className={`flex items-center gap-3 px-4 py-3 mx-2 rounded-lg transition-all duration-200 cursor-pointer ${
                                childIsActive
                                  ? 'bg-blue-400/20 text-blue-700'
                                  : 'text-blue-700/80 hover:bg-blue-300/10 hover:text-blue-800'
                              }`}
                            >
                              <ChildIcon size={16} className={childIsActive ? 'text-blue-600' : 'text-blue-600/70'} />
                              <span className={`font-medium ${isSmallText ? 'text-xs' : 'text-sm'}`}>{child.name}</span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              }

              // 普通菜单项
              return (
                <button
                  key={item.href}
                  onClick={() => handleNavigation(item.href)}
                  onMouseEnter={() => setHoveredItem(item.href)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={`relative flex items-center gap-1.5 px-3 py-2 rounded-xl transition-all duration-300 whitespace-nowrap overflow-hidden cursor-pointer ${
                    itemIsActive
                      ? 'bg-gradient-to-r from-blue-400/30 to-indigo-400/20 text-blue-700 shadow-lg shadow-blue-300/20 border border-blue-400/50'
                      : 'text-blue-700/90 hover:text-blue-800 border border-transparent hover:border-blue-400/30'
                  }`}
                >
                  {/* 背景光效 */}
                  <div
                    className={`absolute inset-0 bg-gradient-to-r from-blue-400/10 to-transparent transition-opacity duration-300 ${
                      isHovered ? 'opacity-100' : 'opacity-0'
                    }`}
                  />

                  {/* 图标容器 */}
                  <div
                    className={`relative flex items-center justify-center w-6 h-6 rounded-lg transition-all duration-300 ${
                      itemIsActive
                        ? 'bg-blue-400/20'
                        : isHovered
                        ? 'bg-blue-400/10 scale-110'
                        : 'bg-transparent'
                    }`}
                  >
                    <Icon
                      size={16}
                      className={`transition-all duration-300 ${
                        itemIsActive ? 'text-blue-600' : isHovered ? 'text-blue-600' : 'text-blue-700/80'
                      }`}
                    />
                  </div>

                  {/* 文字 */}
                  <span
                    className={`relative text-sm font-medium tracking-wide transition-all duration-300 ${
                      itemIsActive ? 'text-blue-800' : ''
                    }`}
                  >
                    {item.name}
                  </span>

                  {/* 底部下划线动画 */}
                  <div
                    className={`absolute bottom-1 left-4 right-4 h-0.5 bg-gradient-to-r from-transparent via-blue-400 to-transparent transition-all duration-300 ${
                      itemIsActive ? 'opacity-100 scale-x-100' : isHovered ? 'opacity-70 scale-x-75' : 'opacity-0 scale-x-0'
                    }`}
                  />
                </button>
              );
            })}
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="xl:hidden text-blue-600 hover:text-blue-700 transition-colors p-2 rounded-lg hover:bg-blue-400/10"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="xl:hidden mt-6 bg-gradient-to-b from-sky-50/95 to-blue-50/95 rounded-2xl border border-blue-300/30 backdrop-blur-xl shadow-2xl max-h-[80vh] overflow-y-auto">
            <nav className="flex flex-col p-4 gap-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const itemIsActive = isActive(item.href) || isChildActive(item.children);

                if (item.children) {
                  return (
                    <div key={item.name} className="flex flex-col gap-1">
                      <div className={`flex items-center gap-4 px-5 py-4 rounded-xl ${
                        itemIsActive
                          ? 'bg-gradient-to-r from-blue-400/30 to-indigo-400/20 text-blue-700 border border-blue-400/50'
                          : 'text-blue-700/90'
                      }`}>
                        <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${itemIsActive ? 'bg-blue-400/20' : 'bg-blue-400/5'}`}>
                          <Icon size={22} className={itemIsActive ? 'text-blue-600' : 'text-blue-600/70'} />
                        </div>
                        <span className="text-base font-medium">{item.name}</span>
                      </div>
                      <div className="pl-8 flex flex-col gap-1">
                        {item.children.map((child) => {
                          const ChildIcon = child.icon;
                          const childIsActive = isActive(child.href);
                          const isSmallText = child.name === '合同违约金计算';
                          return (
                            <button
                              key={child.href}
                              onClick={() => {
                                handleNavigation(child.href);
                                setIsMobileMenuOpen(false);
                              }}
                              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 cursor-pointer ${
                                childIsActive
                                  ? 'bg-blue-400/20 text-blue-700'
                                  : 'text-blue-700/80 hover:bg-blue-300/10 hover:text-blue-800'
                              }`}
                            >
                              <ChildIcon size={18} className={childIsActive ? 'text-blue-600' : 'text-blue-600/70'} />
                              <span className={`font-medium ${isSmallText ? 'text-xs' : 'text-sm'}`}>{child.name}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                }

                return (
                  <button
                    key={item.href}
                    onClick={() => {
                      handleNavigation(item.href);
                      setIsMobileMenuOpen(false);
                    }}
                    className={`flex items-center gap-4 px-5 py-4 rounded-xl transition-all duration-300 cursor-pointer ${
                    itemIsActive
                      ? 'bg-gradient-to-r from-blue-400/30 to-indigo-400/20 text-blue-700 border border-blue-400/50'
                      : 'text-blue-700/90 hover:bg-blue-300/10 hover:text-blue-800'
                  }`}
                >
                  <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${itemIsActive ? 'bg-blue-400/20' : 'bg-blue-400/5'}`}>
                    <Icon size={22} className={itemIsActive ? 'text-blue-600' : 'text-blue-600/70'} />
                  </div>
                    <span className="text-base font-medium">{item.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        )}
      </div>

      {/* 底部装饰线 */}
      <div className="h-0.5 w-full bg-gradient-to-r from-blue-200 via-blue-400/50 to-blue-200" />
    </header>
  );
}
