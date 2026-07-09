'use client';

import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Download, Image, FileText, File, X } from 'lucide-react';

interface DownloadDropdownProps {
  onDownloadImage: () => void;
  onDownloadPDF: () => void;
  onDownloadWord: () => void;
  buttonText?: string;
  buttonClassName?: string;
  disabled?: boolean;
  theme?: 'amber' | 'violet' | 'rose' | 'blue' | 'green';
}

const themeConfig = {
  amber: {
    border: 'border-amber-200/50 dark:border-amber-800/50',
    hover: 'hover:bg-amber-500/10 hover:border-amber-500/50',
    menuBorder: 'border-amber-200/50 dark:border-amber-800/50',
    itemHover: 'hover:bg-amber-500/10',
    iconColor: 'text-amber-600 dark:text-amber-400',
    primary: 'text-amber-600 dark:text-amber-400',
  },
  violet: {
    border: 'border-violet-200/50 dark:border-violet-800/50',
    hover: 'hover:bg-violet-500/10 hover:border-violet-500/50',
    menuBorder: 'border-violet-200/50 dark:border-violet-800/50',
    itemHover: 'hover:bg-violet-500/10',
    iconColor: 'text-violet-600 dark:text-violet-400',
    primary: 'text-violet-600 dark:text-violet-400',
  },
  rose: {
    border: 'border-rose-200/50 dark:border-rose-800/50',
    hover: 'hover:bg-rose-500/10 hover:border-rose-500/50',
    menuBorder: 'border-rose-200/50 dark:border-rose-800/50',
    itemHover: 'hover:bg-rose-500/10',
    iconColor: 'text-rose-600 dark:text-rose-400',
    primary: 'text-rose-600 dark:text-rose-400',
  },
  blue: {
    border: 'border-blue-200/50 dark:border-blue-800/50',
    hover: 'hover:bg-blue-500/10 hover:border-blue-500/50',
    menuBorder: 'border-blue-200/50 dark:border-blue-800/50',
    itemHover: 'hover:bg-blue-500/10',
    iconColor: 'text-blue-600 dark:text-blue-400',
    primary: 'text-blue-600 dark:text-blue-400',
  },
  green: {
    border: 'border-green-200/50 dark:border-green-800/50',
    hover: 'hover:bg-green-500/10 hover:border-green-500/50',
    menuBorder: 'border-green-200/50 dark:border-green-800/50',
    itemHover: 'hover:bg-green-500/10',
    iconColor: 'text-green-600 dark:text-green-400',
    primary: 'text-green-600 dark:text-green-400',
  },
};

export default function DownloadDropdown({
  onDownloadImage,
  onDownloadPDF,
  onDownloadWord,
  buttonText = '下载',
  buttonClassName = '',
  disabled = false,
  theme = 'amber',
}: DownloadDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const themeStyles = themeConfig[theme] || themeConfig.blue;

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDownload = (type: 'image' | 'pdf' | 'word') => {
    setIsOpen(false);
    if (type === 'image') {
      onDownloadImage();
    } else if (type === 'pdf') {
      onDownloadPDF();
    } else {
      onDownloadWord();
    }
  };

  const defaultButtonClass = `flex items-center gap-3 rounded-xl ${themeStyles.border} bg-white/70 dark:bg-slate-700/70 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition-all ${themeStyles.hover} hover:shadow-lg`;

  return (
    <>
      <div className="inline-block">
        <button
          className={buttonClassName || defaultButtonClass}
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
        >
          <Download size={18} />
          {buttonText}
        </button>
      </div>

      {isOpen && createPortal(
        <>
          {/* 背景遮罩 */}
          <div 
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
            onClick={() => setIsOpen(false)}
          />
          
          {/* 弹窗 */}
          <div
            ref={dropdownRef}
            className={`fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 rounded-2xl border ${themeStyles.menuBorder} bg-white dark:bg-slate-800 shadow-2xl z-50 overflow-hidden`}
          >
            {/* 弹窗头部 */}
            <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className={`text-lg font-semibold ${themeStyles.primary}`}>选择下载格式</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                title="关闭"
              >
                <X size={20} className="text-slate-500 dark:text-slate-400" />
              </button>
            </div>
            
            {/* 弹窗内容 */}
            <div className="py-2">
              <button
                onClick={() => handleDownload('image')}
                className={`w-full flex items-center gap-3 px-5 py-4 text-sm text-slate-700 dark:text-slate-300 transition-all ${themeStyles.itemHover}`}
              >
                <Image size={18} className={themeStyles.iconColor} />
                <span>下载图片</span>
              </button>
              <button
                onClick={() => handleDownload('pdf')}
                className={`w-full flex items-center gap-3 px-5 py-4 text-sm text-slate-700 dark:text-slate-300 transition-all ${themeStyles.itemHover}`}
              >
                <FileText size={18} className={themeStyles.iconColor} />
                <span>下载PDF</span>
              </button>
              <button
                onClick={() => handleDownload('word')}
                className={`w-full flex items-center gap-3 px-5 py-4 text-sm text-slate-700 dark:text-slate-300 transition-all ${themeStyles.itemHover}`}
              >
                <File size={18} className={themeStyles.iconColor} />
                <span>下载Word</span>
              </button>
            </div>
          </div>
        </>,
        document.body
      )}
    </>
  );
}
