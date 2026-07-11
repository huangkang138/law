'use client';

import { MessageCircleMore } from 'lucide-react';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';

import DigitalHumanAvatar from './DigitalHumanAvatar';
import DigitalHumanChat from './DigitalHumanChat';

export default function DigitalHumanFloat() {
  const { emotion, isOpen, open } = useDigitalHumanStore();

  return (
    <div className="dh-root">
      {isOpen ? (
        <DigitalHumanChat />
      ) : (
        <div className="dh-launcher-wrap">
          <div className="dh-invite" aria-hidden="true">
            <MessageCircleMore size={17} />
            有法律问题？问问法小助
          </div>
          <button type="button" className="dh-launcher" onClick={open} aria-label="打开法小助数字人助手">
            <DigitalHumanAvatar emotion={emotion} size="small" />
            <span className="dh-launcher-status" aria-hidden="true" />
          </button>
        </div>
      )}

      <style jsx global>{`
        .dh-root {
          position: fixed;
          right: 24px;
          bottom: 24px;
          z-index: 9999;
          font-family: var(--font-sans), system-ui, sans-serif;
        }

        .dh-launcher-wrap {
          display: flex;
          align-items: center;
          gap: 12px;
          animation: dh-rise-in 420ms cubic-bezier(.2,.8,.2,1) both;
        }

        .dh-invite {
          display: flex;
          align-items: center;
          gap: 7px;
          padding: 10px 14px;
          color: #1e4f8f;
          background: rgba(255, 255, 255, .94);
          border: 1px solid rgba(96, 165, 250, .35);
          border-radius: 12px;
          box-shadow: 0 10px 28px rgba(30, 64, 175, .13);
          backdrop-filter: blur(12px);
          font-size: 13px;
          font-weight: 600;
          white-space: nowrap;
        }

        .dh-launcher {
          position: relative;
          width: 100px;
          height: 100px;
          padding: 0;
          overflow: visible;
          border: 2px solid rgba(255, 255, 255, .96);
          border-radius: 50%;
          background: #fff;
          box-shadow: 0 16px 36px rgba(30, 64, 175, .26), 0 0 0 5px rgba(96, 165, 250, .14);
          cursor: pointer;
          animation: dh-float 4.2s ease-in-out infinite;
          transition: box-shadow 180ms ease, transform 180ms ease;
        }

        .dh-launcher:hover {
          box-shadow: 0 20px 42px rgba(30, 64, 175, .32), 0 0 0 7px rgba(96, 165, 250, .18);
        }

        .dh-launcher:focus-visible,
        .dh-panel button:focus-visible,
        .dh-panel textarea:focus-visible {
          outline: 3px solid rgba(37, 99, 235, .35);
          outline-offset: 2px;
        }

        .dh-launcher-status {
          position: absolute;
          right: 4px;
          bottom: 10px;
          width: 15px;
          height: 15px;
          border: 3px solid white;
          border-radius: 50%;
          background: #22c55e;
          box-shadow: 0 2px 8px rgba(34, 197, 94, .4);
        }

        .dh-avatar {
          position: relative;
          overflow: hidden;
          flex: none;
          border-radius: 50%;
          background: #fff;
        }

        .dh-avatar-small {
          width: 96px;
          height: 96px;
        }

        .dh-avatar-large {
          width: 148px;
          height: 148px;
          border: 1px solid rgba(147, 197, 253, .38);
          box-shadow: 0 12px 30px rgba(37, 99, 235, .16);
        }

        .dh-avatar-image {
          object-fit: cover;
          transform: scale(1.12);
          animation: dh-avatar-change 360ms cubic-bezier(.2,.8,.2,1) both;
        }

        .dh-avatar-shine {
          position: absolute;
          inset: 0;
          border-radius: inherit;
          box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .8);
          pointer-events: none;
        }

        .dh-avatar-thinking {
          animation: dh-think-pulse 1.4s ease-in-out infinite;
        }

        .dh-panel {
          width: min(384px, calc(100vw - 32px));
          height: min(650px, calc(100vh - 112px));
          display: grid;
          grid-template-rows: auto auto minmax(0, 1fr) auto auto;
          overflow: hidden;
          color: #18324f;
          background: rgba(249, 252, 255, .97);
          border: 1px solid rgba(96, 165, 250, .3);
          border-radius: 22px;
          box-shadow: 0 26px 70px rgba(30, 64, 175, .22), 0 4px 18px rgba(15, 23, 42, .1);
          backdrop-filter: blur(18px);
          animation: dh-panel-in 320ms cubic-bezier(.2,.8,.2,1) both;
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

        .dh-portrait-stage {
          position: relative;
          height: 162px;
          display: grid;
          place-items: center;
          overflow: hidden;
          background: linear-gradient(180deg, rgba(239, 246, 255, .86), rgba(255, 255, 255, .72));
          border-bottom: 1px solid rgba(147, 197, 253, .2);
        }

        .dh-portrait-halo {
          position: absolute;
          width: 210px;
          height: 82px;
          bottom: 13px;
          border-radius: 50%;
          background: rgba(96, 165, 250, .14);
          filter: blur(16px);
          animation: dh-halo 2.6s ease-in-out infinite;
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

        @keyframes dh-think-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.025); }
        }

        @keyframes dh-halo {
          0%, 100% { opacity: .65; transform: scale(.95); }
          50% { opacity: 1; transform: scale(1.08); }
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
            right: 12px;
            bottom: 12px;
          }

          .dh-invite {
            display: none;
          }

          .dh-launcher,
          .dh-avatar-small {
            width: 82px;
            height: 82px;
          }

          .dh-panel {
            width: calc(100vw - 24px);
            height: min(650px, calc(100dvh - 92px));
            border-radius: 18px;
          }

          .dh-portrait-stage {
            height: 132px;
          }

          .dh-avatar-large {
            width: 120px;
            height: 120px;
          }
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
