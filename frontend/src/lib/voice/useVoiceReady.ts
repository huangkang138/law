'use client';

import { useEffect, useState } from 'react';

// 语音能力需在浏览器环境检测；SSR 首帧按不支持渲染，水合后再刷新，
// 避免服务端与客户端首帧结构不一致。
export function useVoiceReady(): boolean {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    setReady(true);
  }, []);
  return ready;
}
