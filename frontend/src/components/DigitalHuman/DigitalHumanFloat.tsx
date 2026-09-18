'use client';

import { useEffect, useRef, useState } from 'react';
import { MessageCircleMore } from 'lucide-react';
import { usePathname } from 'next/navigation';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';

import CaseWorkspaceShell from './CaseWorkspaceShell';
import DigitalHumanAvatar from './DigitalHumanAvatar';
import DigitalHumanChat from './DigitalHumanChat';

export default function DigitalHumanFloat() {
  const pathname = usePathname();
  const previousPathname = useRef(pathname);
  const { close, emotion, isOpen, isLoading, open, voiceSpeaking, workspaceOpen } = useDigitalHumanStore();
  // 工作台挂载生命周期：
  // - 聊天 ↔ 工作台切换（isOpen 不变）：双挂载 + CSS 隐藏，草稿/在途上传/滚动位置不丢；
  // - 收起整个面板（isOpen=false）：工作台随面板卸载（与重构前行为一致），
  //   下次进入工作台全新挂载并按案件状态重新推导阶段，不留隐藏 DOM 与无效请求。
  const [workspaceMounted, setWorkspaceMounted] = useState(false);

  useEffect(() => {
    if (previousPathname.current === pathname) return;
    previousPathname.current = pathname;
    // 根布局不会随页面路由卸载；离开当前页面时必须主动收起全屏工作台，
    // 否则目标页面虽然已加载，仍会被 position: fixed 的工作台覆盖。
    close();
  }, [close, pathname]);

  useEffect(() => {
    if (!isOpen) {
      setWorkspaceMounted(false);
    } else if (workspaceOpen) {
      setWorkspaceMounted(true);
    }
  }, [isOpen, workspaceOpen]);

  // /chat 自己承载完整交流页；只有用户从真实案件数据入口打开工作台时，
  // 才恢复挂载工作台壳，避免右下角重复聊天入口。
  if (pathname === '/chat' && !workspaceOpen) return null;

  return (
    <div className="dh-root">
      {isOpen ? (
        <>
          <div className={workspaceOpen ? 'dh-chat-hidden' : ''}>
            <DigitalHumanChat avatarVisible={!workspaceOpen} />
          </div>
          {(workspaceOpen || workspaceMounted) && (
            <div className={workspaceOpen ? '' : 'dh-chat-hidden'}>
              <CaseWorkspaceShell visible={workspaceOpen} />
            </div>
          )}
        </>
      ) : (
        <div className="dh-launcher-wrap">
          <button type="button" className="dh-invite" onClick={open} aria-label="打开法小助数字人助手">
            有法律问题？ 问问我
          </button>
          <button type="button" className="dh-launcher" onClick={open} aria-label="打开法小助数字人助手">
            <DigitalHumanAvatar
              emotion={emotion}
              isLoading={isLoading}
              voiceSpeaking={voiceSpeaking}
              size="small"
              variant="launcher"
              useLegacyImageFallback={false}
            />
            <span className="dh-launcher-status" aria-hidden="true" />
          </button>
          <button type="button" className="dh-launcher-cta" onClick={open}>
            <MessageCircleMore size={17} aria-hidden="true" />
            <span>问问法小助</span>
          </button>
        </div>
      )}

      <style jsx global>{`
        .dh-root {
          position: fixed;
          right: 24px;
          bottom: 18px;
          z-index: 40;
          font-family: var(--font-sans), system-ui, sans-serif;
        }

        .dh-launcher-wrap {
          position: relative;
          width: 184px;
          height: 210px;
          animation: dh-rise-in 420ms cubic-bezier(.2,.8,.2,1) both;
          transition: transform 180ms ease;
        }

        .dh-launcher-wrap:hover {
          transform: translateY(-2px);
        }

        .dh-invite {
          position: absolute;
          top: 0;
          left: 0;
          z-index: 3;
          display: flex;
          align-items: center;
          width: 150px;
          min-height: 40px;
          padding: 8px 14px;
          color: #1858a8;
          background: rgba(255, 255, 255, .97);
          border: 1px solid rgba(147, 197, 253, .3);
          border-radius: 18px;
          box-shadow: 0 5px 14px rgba(37, 99, 235, .1);
          font-size: 13px;
          font-family: inherit;
          font-weight: 650;
          line-height: 1.35;
          text-decoration: none;
          white-space: nowrap;
          cursor: pointer;
        }

        .dh-invite::after {
          content: '';
          position: absolute;
          right: 20px;
          bottom: -8px;
          width: 0;
          height: 0;
          border-top: 10px solid rgba(255, 255, 255, .97);
          border-left: 9px solid transparent;
        }

        .dh-launcher {
          position: absolute;
          top: 42px;
          left: 41px;
          z-index: 1;
          width: 118px;
          height: 150px;
          padding: 0;
          overflow: visible;
          border: 0;
          border-radius: 0;
          background: transparent;
          filter: drop-shadow(0 10px 14px rgba(30, 64, 175, .12));
          cursor: pointer;
          text-decoration: none;
          transition: filter 180ms ease;
        }

        .dh-launcher::before {
          content: '';
          position: absolute;
          left: 50%;
          top: 54%;
          width: 126px;
          height: 126px;
          border-radius: 50%;
          background: rgba(219, 238, 255, .58);
          transform: translate(-50%, -50%);
        }

        .dh-launcher:hover {
          filter: drop-shadow(0 12px 17px rgba(30, 64, 175, .18));
        }

        .dh-invite:focus-visible,
        .dh-launcher:focus-visible,
        .dh-launcher-cta:focus-visible,
        .dh-panel button:focus-visible,
        .dh-panel textarea:focus-visible {
          outline: 3px solid rgba(37, 99, 235, .35);
          outline-offset: 2px;
        }

        .dh-launcher-status {
          position: absolute;
          right: 4px;
          top: 72px;
          z-index: 2;
          width: 12px;
          height: 12px;
          border: 2px solid rgba(255, 255, 255, .95);
          border-radius: 50%;
          background: #22c55e;
          box-shadow: 0 2px 6px rgba(34, 197, 94, .28);
        }

        .dh-launcher-cta {
          position: absolute;
          left: 22px;
          bottom: 0;
          z-index: 3;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          width: 146px;
          height: 40px;
          padding: 0 18px;
          color: #fff;
          background: linear-gradient(100deg, #3b82f6 0%, #38bdf8 100%);
          border: 0;
          border-radius: 999px;
          box-shadow: 0 7px 16px rgba(37, 99, 235, .2);
          font-size: 14px;
          font-family: inherit;
          font-weight: 650;
          line-height: 1;
          text-decoration: none;
          white-space: nowrap;
          cursor: pointer;
          transition: background 180ms ease, box-shadow 180ms ease;
        }

        .dh-launcher-cta:hover {
          background: linear-gradient(100deg, #2563eb 0%, #0ea5e9 100%);
          box-shadow: 0 8px 18px rgba(37, 99, 235, .25);
        }

        .dh-avatar {
          position: relative;
          flex: none;
          width: 148px;
          height: 174px;
        }

        .dh-avatar-small {
          width: 86px;
          height: 108px;
        }

        .dh-avatar-large {
          width: 148px;
          height: 174px;
        }

        .dh-avatar-launcher {
          width: 118px;
          height: 150px;
          overflow: hidden;
        }

        .dh-avatar-launcher .dh-rive-layer {
          inset: auto;
          top: 0;
          left: 50%;
          width: 180px;
          height: 228px;
          transform: translateX(-50%);
          mix-blend-mode: multiply;
        }

        .dh-avatar-launcher .dh-avatar-image {
          inset: auto;
          top: 0;
          left: 50%;
          width: 150px;
          height: 190px;
          transform: translateX(-50%);
        }

        .dh-avatar-portrait {
          width: 142px;
          height: 172px;
        }

        .dh-avatar-compact {
          width: 70px;
          height: 86px;
        }

        .dh-avatar-image {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: contain;
          transform: none;
        }

        .dh-avatar-image-current {
          z-index: 1;
          animation: dh-avatar-crossfade-in 280ms ease-out both;
        }

        .dh-avatar-image-outgoing {
          z-index: 0;
          animation: dh-avatar-crossfade-out 280ms ease-in both;
        }

        .dh-rive-layer {
          position: absolute;
          inset: 0;
          z-index: 1;
          pointer-events: none;
        }

        .dh-rive-canvas {
          display: block;
          width: 100%;
          height: 100%;
        }

        .dh-avatar-thinking,
        .dh-avatar-state-idle,
        .dh-avatar-state-thinking,
        .dh-avatar-state-speaking,
        .dh-avatar-state-success,
        .dh-avatar-state-warning {
          animation: none;
        }

        .dh-panel {
          width: min(384px, calc(100vw - 32px));
          height: min(650px, calc(100vh - 112px));
          display: grid;
          grid-template-rows: auto auto minmax(0, 1fr);
          overflow: hidden;
          color: #18324f;
          background: rgba(249, 252, 255, .97);
          border: 1px solid rgba(96, 165, 250, .3);
          border-radius: 22px;
          box-shadow: 0 26px 70px rgba(30, 64, 175, .22), 0 4px 18px rgba(15, 23, 42, .1);
          backdrop-filter: blur(18px);
          animation: dh-panel-in 320ms cubic-bezier(.2,.8,.2,1) both;
        }

        .dh-panel-body {
          min-height: 0;
          display: grid;
          grid-template-rows: minmax(0, 1fr) auto;
        }

        .dh-chat-column {
          min-width: 0;
          min-height: 0;
          display: grid;
          grid-template-rows: auto minmax(0, 1fr) auto auto;
        }

        .dh-workspace-column {
          min-width: 0;
          min-height: 0;
        }

        .dh-panel-expanded {
          width: min(920px, calc(100vw - 48px));
          height: min(760px, calc(100vh - 64px));
          grid-template-rows: auto minmax(0, 1fr);
        }

        .dh-panel-expanded .dh-panel-body {
          grid-template-columns: minmax(0, 1fr);
          grid-template-rows: minmax(0, 1fr);
        }

        .dh-panel-expanded .dh-chat-column {
          display: none;
        }

        .dh-panel-expanded .dh-history-section {
          display: none;
        }

        .dh-panel-expanded .dh-workspace-column {
          overflow-y: auto;
          padding: 20px 24px 24px;
          background: rgba(248, 251, 255, .86);
        }

        /* 视图切换隐藏层：聊天与工作台双挂载，仅 CSS 控制可见性。 */
        .dh-chat-hidden {
          display: none;
        }

        .dh-panel-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 18px 12px;
          background: rgba(239, 246, 255, .88);
          border-bottom: 1px solid rgba(147, 197, 253, .28);
        }

        .dh-title-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .dh-title-row h2 {
          margin: 0;
          color: #123d72;
          font-family: var(--font-sans), system-ui, sans-serif;
          font-size: 17px;
          font-weight: 750;
          letter-spacing: .02em;
        }

        .dh-panel-header p {
          margin: 3px 0 0;
          color: #5e7796;
          font-size: 12px;
          line-height: 1.4;
        }

        .dh-online-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #22c55e;
          box-shadow: 0 0 0 3px rgba(34, 197, 94, .13);
        }

        .dh-header-actions {
          display: flex;
          gap: 5px;
        }

        .dh-header-actions button {
          width: 34px;
          height: 34px;
          display: grid;
          place-items: center;
          padding: 0;
          color: #4f6f96;
          background: transparent;
          border: 0;
          border-radius: 9px;
          cursor: pointer;
          transition: color 160ms ease, background 160ms ease;
        }

        .dh-header-actions button:hover {
          color: #1d4ed8;
          background: rgba(147, 197, 253, .18);
        }

        .dh-header-actions .dh-workspace-switch {
          width: auto;
          grid-auto-flow: column;
          gap: 6px;
          padding: 0 10px;
          color: #245995;
          background: rgba(255, 255, 255, .72);
          border: 1px solid rgba(147, 197, 253, .42);
          font-size: 12px;
          font-weight: 700;
          white-space: nowrap;
        }

        .dh-panel-expanded .dh-workspace-switch {
          color: #1d4ed8;
          background: #fff;
          border-color: rgba(96, 165, 250, .48);
        }

        .dh-history-section {
          position: relative;
          z-index: 6;
        }

        .dh-session-bar {
          display: flex;
          gap: 8px;
          padding: 8px 16px;
          background: rgba(248, 250, 252, .92);
          border-bottom: 1px solid rgba(147, 197, 253, .2);
        }

        .dh-history-toggle {
          flex: 1;
          display: flex !important;
          align-items: center;
          justify-content: flex-start !important;
          gap: 7px;
          width: auto !important;
          padding: 7px 9px !important;
          color: #334155;
          background: white;
          border: 1px solid #dbeafe;
          border-radius: 8px;
          font-size: 12px;
        }

        .dh-history-toggle span {
          flex: 1;
          overflow: hidden;
          text-align: left;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .dh-history-toggle svg:last-child {
          transition: transform 160ms ease;
        }

        .dh-chevron-open {
          transform: rotate(180deg);
        }

        .dh-session-bar button {
          display: grid;
          place-items: center;
          width: 30px;
          color: #64748b;
          background: white;
          border: 1px solid #dbeafe;
          border-radius: 8px;
          cursor: pointer;
        }

        .dh-history-list {
          position: absolute;
          top: calc(100% - 1px);
          right: 12px;
          left: 12px;
          max-height: 220px;
          overflow-y: auto;
          padding: 7px;
          background: rgba(255, 255, 255, .98);
          border: 1px solid #dbeafe;
          border-radius: 0 0 12px 12px;
          box-shadow: 0 16px 30px rgba(30, 64, 175, .16);
        }

        .dh-history-list > p {
          margin: 0;
          padding: 12px;
          color: #7b8da4;
          font-size: 12px;
          text-align: center;
        }

        .dh-history-error {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          padding: 10px;
          color: #9a3412;
          background: #fff7ed;
          border-radius: 8px;
          font-size: 11px;
        }

        .dh-history-error button {
          flex: none;
          width: auto;
          padding: 5px 7px;
          color: #9a3412;
          background: #fff;
          border: 1px solid #fed7aa;
          border-radius: 7px;
          cursor: pointer;
        }

        .dh-history-item {
          display: flex;
          align-items: center;
          gap: 5px;
          margin-bottom: 4px;
          border-radius: 8px;
        }

        .dh-history-item:last-child {
          margin-bottom: 0;
        }

        .dh-history-current {
          background: #eff6ff;
        }

        .dh-history-select {
          min-width: 0;
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 2px;
          padding: 8px 9px;
          color: #294866;
          background: transparent;
          border: 0;
          cursor: pointer;
        }

        .dh-history-select span {
          width: 100%;
          overflow: hidden;
          font-size: 13px;
          font-weight: 650;
          text-align: left;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .dh-history-select small {
          color: #7b8da4;
          font-size: 10px;
        }

        .dh-history-delete {
          flex: none;
          width: 30px !important;
          height: 30px !important;
          color: #94a3b8 !important;
          background: transparent !important;
          border: 0 !important;
        }

        .dh-history-delete:hover {
          color: #dc2626 !important;
          background: #fef2f2 !important;
        }

        .dh-portrait-stage {
          position: relative;
          height: 162px;
          display: grid;
          place-items: center;
          overflow: hidden;
          background: linear-gradient(180deg, rgba(239, 246, 255, .86), rgba(255, 255, 255, .72));
          border-bottom: 1px solid rgba(147, 197, 253, .2);
        }

        .dh-messages {
          min-height: 0;
          overflow-y: auto;
          padding: 16px;
          scroll-behavior: smooth;
          background: rgba(255, 255, 255, .72);
        }

        .dh-message-row {
          display: flex;
          margin-bottom: 12px;
          animation: dh-message-in 240ms ease-out both;
        }

        .dh-message-user {
          justify-content: flex-end;
        }

        .dh-message-bubble {
          max-width: 84%;
          padding: 10px 12px;
          border-radius: 14px;
          box-shadow: 0 3px 10px rgba(30, 64, 175, .07);
        }

        .dh-message-bubble p {
          margin: 0;
          font-size: 14px;
          line-height: 1.65;
          white-space: pre-wrap;
          word-break: break-word;
        }

        .dh-message-assistant .dh-message-bubble {
          color: #294866;
          background: #fff;
          border: 1px solid rgba(147, 197, 253, .32);
          border-bottom-left-radius: 4px;
        }

        .dh-message-user .dh-message-bubble {
          color: #fff;
          background: #2563b8;
          border-bottom-right-radius: 4px;
        }

        .dh-route-button {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-top: 9px;
          padding: 8px 10px;
          color: #174b8c;
          background: #eff6ff;
          border: 1px solid #bfdbfe;
          border-radius: 9px;
          font-size: 13px;
          font-weight: 650;
          cursor: pointer;
          transition: background 160ms ease, transform 160ms ease;
        }

        .dh-route-button:hover {
          background: #dbeafe;
          transform: translateX(2px);
        }

        .dh-typing {
          display: flex;
          align-items: center;
          gap: 5px;
          min-width: 52px;
          min-height: 38px;
        }

        .dh-typing span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #60a5fa;
          animation: dh-dot 1.15s ease-in-out infinite;
        }

        .dh-typing span:nth-child(2) { animation-delay: 120ms; }
        .dh-typing span:nth-child(3) { animation-delay: 240ms; }

        .dh-composer {
          display: flex;
          align-items: flex-end;
          gap: 9px;
          padding: 12px 14px 7px;
          background: #fff;
          border-top: 1px solid rgba(147, 197, 253, .25);
        }

        .dh-composer textarea {
          min-height: 42px;
          max-height: 92px;
          flex: 1;
          resize: none;
          padding: 10px 12px;
          color: #203c5b;
          background: #f7fbff;
          border: 1px solid #cbdff5;
          border-radius: 12px;
          font: inherit;
          font-size: 14px;
          line-height: 20px;
        }

        .dh-composer textarea::placeholder {
          color: #8196ad;
        }

        .dh-send-button {
          width: 42px;
          height: 42px;
          display: grid;
          place-items: center;
          flex: none;
          padding: 0;
          color: #fff;
          background: #2563b8;
          border: 0;
          border-radius: 12px;
          box-shadow: 0 6px 14px rgba(37, 99, 184, .22);
          cursor: pointer;
          transition: background 160ms ease, transform 160ms ease, opacity 160ms ease;
        }

        .dh-send-button:hover:not(:disabled) {
          background: #1d4f98;
          transform: translateY(-1px);
        }

        .dh-send-button:disabled {
          opacity: .45;
          cursor: not-allowed;
        }

        .dh-disclaimer {
          margin: 0;
          padding: 0 14px 10px;
          color: #8a9caf;
          background: #fff;
          font-size: 10px;
          line-height: 1.4;
          text-align: center;
        }

        .dh-stream-fallback-hint {
          margin: 0;
          padding: 6px 14px 0;
          color: #b45309;
          background: #fff;
          font-size: 11px;
          line-height: 1.5;
          text-align: center;
        }

        .dh-workspace-layout {
          min-width: 0;
          min-height: 0;
          display: grid;
          grid-template-columns: minmax(0, 1fr) 268px;
          overflow: hidden;
        }

        .dh-companion-column {
          min-width: 0;
          min-height: 0;
          border-left: 1px solid rgba(147, 197, 253, .32);
          background: rgba(239, 246, 255, .72);
        }

        .dh-companion {
          height: 100%;
          min-height: 0;
          display: grid;
          grid-template-rows: auto auto minmax(0, 1fr) auto auto;
          gap: 12px;
          padding: 16px 14px 12px;
        }

        .dh-companion-avatar {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .dh-companion-avatar .dh-avatar-small {
          width: 56px;
          height: 70px;
        }

        .dh-companion-avatar div {
          display: grid;
          gap: 2px;
        }

        .dh-companion-avatar strong {
          color: #183b66;
          font-size: 15px;
        }

        .dh-companion-avatar small {
          color: #66809e;
          font-size: 11px;
        }

        .dh-presenter-card {
          display: flex;
          align-items: flex-start;
          gap: 9px;
          padding: 11px;
          color: #244b75;
          background: rgba(255, 255, 255, .88);
          border: 1px solid rgba(147, 197, 253, .38);
          border-radius: 13px;
        }

        .dh-presenter-card svg {
          flex: none;
          margin-top: 2px;
          color: #3b82f6;
        }

        .dh-presenter-card div {
          min-width: 0;
        }

        .dh-presenter-card strong {
          display: block;
          color: #183b66;
          font-size: 12px;
          line-height: 1.45;
        }

        .dh-presenter-card p {
          margin: 4px 0 0;
          color: #617a96;
          font-size: 11px;
          line-height: 1.55;
        }

        .dh-presenter-card span {
          display: inline-block;
          margin-top: 7px;
          padding: 3px 7px;
          color: #2563eb;
          background: #eff6ff;
          border-radius: 999px;
          font-size: 10px;
          font-weight: 700;
        }

        .dh-presenter-completed {
          border-color: rgba(52, 211, 153, .38);
          background: rgba(236, 253, 245, .9);
        }

        .dh-presenter-completed svg {
          color: #059669;
        }

        .dh-presenter-error {
          border-color: rgba(248, 113, 113, .34);
          background: rgba(254, 242, 242, .92);
        }

        .dh-presenter-error svg {
          color: #dc2626;
        }

        .dh-companion-messages {
          min-height: 0;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding-right: 2px;
        }

        .dh-companion-message {
          padding: 8px 9px;
          background: rgba(255, 255, 255, .82);
          border-radius: 11px;
        }

        .dh-companion-message.user {
          margin-left: 18px;
          background: rgba(219, 234, 254, .86);
        }

        .dh-companion-message span {
          display: block;
          margin-bottom: 3px;
          color: #7690aa;
          font-size: 9px;
          font-weight: 700;
        }

        .dh-companion-message p,
        .dh-companion-thinking {
          margin: 0;
          color: #304e6d;
          font-size: 11px;
          line-height: 1.55;
          white-space: pre-wrap;
          overflow-wrap: anywhere;
        }

        .dh-companion-thinking {
          color: #6b82a0;
        }

        .dh-companion-composer {
          padding: 8px;
          border: 1px solid rgba(147, 197, 253, .34);
          border-radius: 13px;
        }

        .dh-companion-composer textarea {
          min-height: 34px;
          font-size: 11px;
        }

        .dh-companion-hint {
          margin: 0;
          color: #7890aa;
          font-size: 9px;
          line-height: 1.4;
          text-align: center;
        }

        .dh-mic-button,
        .dh-voice-toggle {
          width: 42px;
          height: 42px;
          display: grid;
          place-items: center;
          flex: none;
          padding: 0;
          color: #2563b8;
          background: #fff;
          border: 1px solid #cbdff5;
          border-radius: 12px;
          cursor: pointer;
          transition: background 160ms ease, color 160ms ease, border-color 160ms ease;
        }

        .dh-mic-button:hover:not(:disabled),
        .dh-voice-toggle:hover {
          background: #eff6ff;
          border-color: #93c5fd;
        }

        .dh-mic-button:disabled {
          opacity: .45;
          cursor: not-allowed;
        }

        .dh-mic-button-active,
        .dh-mic-button-active:hover:not(:disabled) {
          color: #fff;
          background: #dc2626;
          border-color: #dc2626;
        }

        .dh-voice-toggle-on,
        .dh-voice-toggle-on:hover {
          color: #fff;
          background: #2563b8;
          border-color: #2563b8;
        }

        .dh-stt-error-hint {
          margin: 0;
          padding: 6px 14px 0;
          color: #b45309;
          background: #fff;
          font-size: 11px;
          line-height: 1.5;
          text-align: center;
        }

        .dh-speak-button {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          margin-top: 8px;
          padding: 5px 9px;
          color: #4773a5;
          background: #f7fbff;
          border: 1px solid #cbdff5;
          border-radius: 8px;
          cursor: pointer;
          transition: background 160ms ease, color 160ms ease, border-color 160ms ease;
        }

        .dh-speak-button:hover {
          background: #eff6ff;
          border-color: #93c5fd;
        }

        .dh-speak-button-active,
        .dh-speak-button-active:hover {
          color: #b45309;
          background: #fffbeb;
          border-color: #fcd34d;
        }

        .dh-companion-message-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
          margin-bottom: 3px;
        }

        .dh-companion-message-head span {
          margin-bottom: 0;
        }

        .dh-companion-speak {
          display: grid;
          place-items: center;
          flex: none;
          width: 20px;
          height: 20px;
          padding: 0;
          color: #4773a5;
          background: transparent;
          border: 1px solid transparent;
          border-radius: 6px;
          cursor: pointer;
          transition: background 160ms ease, color 160ms ease, border-color 160ms ease;
        }

        .dh-companion-speak:hover {
          background: #eff6ff;
          border-color: #bfdbfe;
        }

        .dh-companion-speak-active,
        .dh-companion-speak-active:hover {
          color: #b45309;
          background: #fffbeb;
          border-color: #fcd34d;
        }

        .dh-companion-composer .dh-mic-button,
        .dh-companion-composer .dh-voice-toggle {
          width: 34px;
          height: 34px;
          border-radius: 10px;
        }

        @keyframes dh-float {
          0%, 100% { transform: translateY(0) rotate(0); }
          50% { transform: translateY(-8px) rotate(.6deg); }
        }

        @keyframes dh-rise-in {
          from { opacity: 0; transform: translateY(14px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes dh-panel-in {
          from { opacity: 0; transform: translateY(16px) scale(.96); transform-origin: bottom right; }
          to { opacity: 1; transform: translateY(0) scale(1); transform-origin: bottom right; }
        }

        @keyframes dh-avatar-change {
          from { opacity: 0; transform: scale(1.08); }
          to { opacity: 1; transform: scale(1.12); }
        }

        @keyframes dh-avatar-crossfade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes dh-avatar-crossfade-out {
          from { opacity: 1; }
          to { opacity: 0; }
        }

        @keyframes dh-avatar-idle {
          0%, 100% { transform: translateY(0) scale(1); }
          50% { transform: translateY(-1px) scale(1.008); }
        }

        @keyframes dh-avatar-thinking-sway {
          0%, 100% { transform: rotate(0deg); }
          35% { transform: rotate(-0.7deg); }
          70% { transform: rotate(0.7deg); }
        }

        @keyframes dh-avatar-speaking {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-1.5px); }
        }

        @keyframes dh-avatar-success {
          0% { transform: scale(1); }
          45% { transform: scale(1.035); }
          100% { transform: scale(1); }
        }

        @keyframes dh-think-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.025); }
        }

        @keyframes dh-message-in {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes dh-dot {
          0%, 60%, 100% { transform: translateY(0); opacity: .45; }
          30% { transform: translateY(-4px); opacity: 1; }
        }

        @media (max-width: 640px) {
          .dh-root {
            right: 16px;
            bottom: 16px;
          }

          .dh-launcher-wrap {
            width: 174px;
            height: 200px;
          }

          .dh-launcher {
            left: 38px;
            width: 112px;
            height: 142px;
          }

          .dh-avatar-launcher {
            width: 112px;
            height: 142px;
          }

          .dh-avatar-launcher .dh-rive-layer {
            width: 170px;
            height: 216px;
          }

          .dh-avatar-launcher .dh-avatar-image {
            width: 142px;
            height: 180px;
          }

          .dh-launcher-cta {
            left: 18px;
            width: 144px;
          }

          .dh-panel {
            width: calc(100vw - 24px);
            height: min(650px, calc(100dvh - 92px));
            border-radius: 18px;
          }

          .dh-panel-expanded {
            width: calc(100vw - 24px);
            height: calc(100dvh - 24px);
          }

          .dh-panel-expanded .dh-panel-body {
            grid-template-columns: 1fr;
            grid-template-rows: minmax(0, 1fr);
          }

          .dh-panel-expanded .dh-chat-column {
            display: none;
          }

          .dh-panel-expanded .dh-workspace-column {
            padding: 14px;
          }

          .dh-workspace-layout {
            grid-template-columns: 1fr;
            grid-template-rows: minmax(0, 1fr) auto;
            overflow-y: auto;
          }

          .dh-companion-column {
            min-height: 260px;
            border-top: 1px solid rgba(147, 197, 253, .32);
            border-left: 0;
          }

          .dh-companion {
            height: 260px;
            grid-template-columns: auto minmax(0, 1fr);
            grid-template-rows: auto minmax(0, 1fr) auto;
          }

          .dh-companion-avatar {
            grid-column: 1;
          }

          .dh-presenter-card {
            grid-column: 2;
          }

          .dh-companion-messages {
            grid-column: 1 / -1;
          }

          .dh-companion-composer {
            grid-column: 1 / -1;
          }

          .dh-companion-hint {
            display: none;
          }

          .dh-portrait-stage {
            height: 132px;
          }

          .dh-avatar-large {
            width: 120px;
            height: 148px;
          }

          .dh-avatar-portrait { width: 118px; height: 146px; }
          .dh-avatar-compact { width: 62px; height: 78px; }
        }

        @media (prefers-reduced-motion: reduce) {
          .dh-root *,
          .dh-root *::before,
          .dh-root *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
          }
        }
      `}</style>
    </div>
  );
}
