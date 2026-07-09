'use client';

import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';

interface AlertDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  onClose: () => void;
  confirmText?: string;
  onConfirm?: () => void;
  cancelText?: string;
  onCancel?: () => void;
  type?: 'info' | 'error' | 'success' | 'warning';
}

export const AlertDialog: React.FC<AlertDialogProps> = ({
  isOpen,
  title,
  message,
  onClose,
  confirmText = '确定',
  onConfirm,
  cancelText,
  onCancel,
  type = 'info'
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      // 防止背景滚动
      document.body.style.overflow = 'hidden';
    }
  }, [isOpen]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      if (typeof onClose === 'function') {
        onClose();
      }
      // 恢复背景滚动
      document.body.style.overflow = '';
    }, 300);
  };

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm();
    }
    handleClose();
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
    handleClose();
  };

  if (!isOpen && !isVisible) {
    return null;
  }

  const getIcon = () => {
    switch (type) {
      case 'error':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-500">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        );
      case 'success':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-500">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="16 11 12 15 8 11"></polyline>
          </svg>
        );
      case 'warning':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-yellow-500">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        );
      default:
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 背景遮罩 */}
      <div 
        className={`fixed inset-0 bg-black/50 transition-opacity duration-300 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
        onClick={handleClose}
      />
      
      {/* 弹窗内容 */}
      <div 
        className={`relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl transition-all duration-300 transform ${isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}
      >
        <div className="flex items-center gap-4 mb-4">
          {getIcon()}
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
        
        <p className="mb-6 text-sm text-muted-foreground">{message}</p>
        
        <div className="flex justify-end gap-3">
          {cancelText && (
            <button
              onClick={handleCancel}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium transition-smooth hover:bg-muted"
            >
              {cancelText}
            </button>
          )}
          <button
            onClick={handleConfirm}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-smooth hover:bg-primary/90"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

// 全局 alert 工具
export const showAlert = (
  message: string,
  type: 'info' | 'error' | 'success' | 'warning' = 'info',
  title: string = type === 'error' ? '错误' : type === 'success' ? '成功' : type === 'warning' ? '警告' : '提示'
) => {
  return new Promise<void>((resolve) => {
    // 创建临时容器
    const container = document.createElement('div');
    document.body.appendChild(container);

    // 渲染弹窗
    const root = ReactDOM.createRoot(container);
    let isClosed = false;
    
    root.render(
      <AlertDialog
        isOpen={true}
        title={title}
        message={message}
        type={type}
        onClose={() => {
          if (!isClosed) {
            isClosed = true;
            try {
              root.unmount();
              if (container.parentNode === document.body) {
                document.body.removeChild(container);
              }
            } catch (error) {
              console.error('清理弹窗容器失败:', error);
            } finally {
              resolve();
            }
          }
        }}
      />
    );
  });
};

// 全局 confirm 工具
export const showConfirm = (
  message: string,
  title: string = '确认',
  confirmText: string = '确认',
  cancelText: string = '取消'
) => {
  return new Promise<boolean>((resolve) => {
    // 创建临时容器
    const container = document.createElement('div');
    document.body.appendChild(container);

    // 渲染弹窗
    const root = ReactDOM.createRoot(container);
    let isClosed = false;
    
    root.render(
      <AlertDialog
        isOpen={true}
        title={title}
        message={message}
        confirmText={confirmText}
        cancelText={cancelText}
        onConfirm={() => {
          if (!isClosed) {
            isClosed = true;
            try {
              root.unmount();
              if (container.parentNode === document.body) {
                document.body.removeChild(container);
              }
            } catch (error) {
              console.error('清理弹窗容器失败:', error);
            } finally {
              resolve(true);
            }
          }
        }}
        onCancel={() => {
          if (!isClosed) {
            isClosed = true;
            try {
              root.unmount();
              if (container.parentNode === document.body) {
                document.body.removeChild(container);
              }
            } catch (error) {
              console.error('清理弹窗容器失败:', error);
            } finally {
              resolve(false);
            }
          }
        }}
        onClose={() => {
          if (!isClosed) {
            isClosed = true;
            try {
              root.unmount();
              if (container.parentNode === document.body) {
                document.body.removeChild(container);
              }
            } catch (error) {
              console.error('清理弹窗容器失败:', error);
            } finally {
              resolve(false);
            }
          }
        }}
      />
    );
  });
};