'use client';

import Image from 'next/image';
import dynamic from 'next/dynamic';
import { useEffect, useState, type CSSProperties } from 'react';

import type { DigitalHumanEmotion } from '@/services/digitalHumanApi';

import { resolveAvatarVisualState } from './AvatarController';
import type { AvatarState } from './AvatarStateAdapter';
const RiveDigitalHuman = dynamic(() => import('./RiveDigitalHuman'), { ssr: false });

interface DigitalHumanAvatarProps {
  emotion: DigitalHumanEmotion;
  state?: AvatarState;
  size?: 'small' | 'large';
  variant?: 'launcher' | 'portrait' | 'compact';
  isLoading?: boolean;
  voiceSpeaking?: boolean;
  visible?: boolean;
  useLegacyImageFallback?: boolean;
  useLoadingPlaceholder?: boolean;
  // 保留给后续的局部嘴型覆盖；当前完整 PNG 不叠加任何 AI 拆层素材。
  mouthOpen?: boolean;
}

const EMOTION_LABELS: Record<DigitalHumanEmotion, string> = {
  idle: '随时为你服务',
  welcome: '你好，我是法小助',
  thinking: '正在认真思考',
  talk_normal: '正在为你解答',
  serious: '这件事需要认真对待',
  success: '很高兴帮到你',
  error: '遇到了一点问题',
  handoff: '带你去合适的功能',
};

export default function DigitalHumanAvatar({
  emotion,
  state,
  size = 'large',
  variant = 'portrait',
  isLoading,
  voiceSpeaking,
  visible = true,
  useLegacyImageFallback = true,
  useLoadingPlaceholder = false,
  mouthOpen = false,
}: DigitalHumanAvatarProps) {
  const isSmall = size === 'small';
  const pixelSize = isSmall ? 96 : 148;
  const visualState = resolveAvatarVisualState({ emotion, state, isLoading, voiceSpeaking, mouthOpen });
  const [current, setCurrent] = useState(visualState);
  const [previous, setPrevious] = useState<typeof visualState | null>(null);
  const [riveReady, setRiveReady] = useState(false);

  useEffect(() => {
    if (current.image === visualState.image) return;
    setPrevious(current);
    setCurrent(visualState);
    const timer = window.setTimeout(() => setPrevious(null), 280);
    return () => window.clearTimeout(timer);
  }, [current, visualState]);

  useEffect(() => {
    if (!visible) setRiveReady(false);
  }, [visible]);

  const criticalStyle = {
    position: 'relative',
    flex: 'none',
  } as CSSProperties;

  // 聊天和工作台双挂载时，非活动实例不能保留 PNG 回退节点。
  if (!visible) return null;

  return (
    <div
      className={`dh-avatar dh-avatar-${variant} ${isSmall ? 'dh-avatar-small' : 'dh-avatar-large'} ${
        current.state === 'thinking' ? 'dh-avatar-thinking' : ''
      } dh-avatar-state-${current.state} ${riveReady ? 'dh-avatar-rive-ready' : 'dh-avatar-rive-pending'}`}
      style={criticalStyle}
      aria-label={EMOTION_LABELS[current.image]}
    >
      {useLoadingPlaceholder && (
        <Image
          src="/optimized/avatar-placeholder-3ac3781e.webp"
          alt=""
          aria-hidden="true"
          fill
          priority
          sizes="(max-width: 640px) 320px, 560px"
          className="dh-avatar-image dh-avatar-placeholder"
        />
      )}
      {useLegacyImageFallback && !riveReady && previous && (
        <Image
          key={`previous-${previous.image}`}
          src={`/digital-human/first-gen/${previous.image}.png`}
          alt=""
          aria-hidden="true"
          width={pixelSize}
          height={pixelSize}
          sizes={isSmall ? '104px' : '148px'}
          className="dh-avatar-image dh-avatar-image-outgoing"
        />
      )}
      {useLegacyImageFallback && !riveReady && (
        <Image
          key={`current-${current.image}`}
          src={`/digital-human/first-gen/${current.image}.png`}
          alt={`法小助：${EMOTION_LABELS[current.image]}`}
          width={pixelSize}
          height={pixelSize}
          priority={current.image === 'idle'}
          sizes={isSmall ? '104px' : '148px'}
          className="dh-avatar-image dh-avatar-image-current"
        />
      )}
      <RiveDigitalHuman
        emotion={emotion}
        visualState={current}
        voiceSpeaking={voiceSpeaking ?? false}
        visible={visible}
        onReady={() => setRiveReady(true)}
        onError={() => setRiveReady(false)}
      />
    </div>
  );
}

export { EMOTION_LABELS };
