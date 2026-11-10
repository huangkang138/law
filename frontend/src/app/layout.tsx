'use client';

import type { Metadata } from 'next';
import './globals.css';
import TopNavbar from '@/components/TopNavbar';
import DigitalHumanFloat from '@/components/DigitalHuman/DigitalHumanFloat';
import { usePathname } from 'next/navigation';
import { useSettings } from '@/hooks/useSettings';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  useSettings();
  const isHomePage = pathname === '/';

  return (
    <html lang="zh-CN" className="font-medium density-standard">
      <head>
        {/* 预加载所有页面 */}
        <link rel="prefetch" href="/" />
        <link rel="prefetch" href="/chat" />
        <link rel="prefetch" href="/contract" />
        <link rel="prefetch" href="/case-analysis" />
        <link rel="prefetch" href="/similar-documents" />
        <link rel="prefetch" href="/case-explanation" />
        <link rel="prefetch" href="/dispute-organize" />
        <link rel="prefetch" href="/dispute-center" />
        <link rel="prefetch" href="/document-drafting" />
        <link rel="prefetch" href="/document-drafting/legal-document" />
        <link rel="prefetch" href="/document-drafting/contract-drafting" />
        <link rel="prefetch" href="/document-drafting/legal-opinion" />
        <link rel="prefetch" href="/debate" />
        <link rel="prefetch" href="/knowledge-graph" />
        <link rel="prefetch" href="/knowledge-graphs" />
        <link rel="prefetch" href="/history" />
        <link rel="prefetch" href="/settings" />
      </head>
      <body className="font-sans bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100">
        {/* 顶栏导航 */}
        <TopNavbar />

        {/* 主内容区域 */}
        <main className={`flex flex-1 flex-col min-h-screen ${isHomePage ? 'pt-[var(--app-header-height)]' : 'business-main pt-[var(--business-page-top)] overflow-y-auto'}`}>
          {children}
        </main>

        <DigitalHumanFloat />
      </body>
    </html>
  );
}
