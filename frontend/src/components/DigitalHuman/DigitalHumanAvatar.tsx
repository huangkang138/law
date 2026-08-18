'use client';

import Image from 'next/image';
import { useEffect, useState, type CSSProperties } from 'react';

import type { DigitalHumanEmotion } from '@/services/digitalHumanApi';

import { resolveAvatarVisualState } from './AvatarController';
import type { AvatarState } from './AvatarStateAdapter';

interface DigitalHumanAvatarProps {
  emotion: DigitalHumanEmotion;
  state?: AvatarState;
  size?: 'small' | 'large';
  isLoading?: boolean;
  voiceSpeaking?: boolean;
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
  isLoading,
  voiceSpeaking,
  mouthOpen = false,
}: DigitalHumanAvatarProps) {
  const isSmall = size === 'small';
  const pixelSize = isSmall ? 96 : 148;
  const visualState = resolveAvatarVisualState({ emotion, state, isLoading, voiceSpeaking, mouthOpen });
  const [current, setCurrent] = useState(visualState);
  const [previous, setPrevious] = useState<typeof visualState | null>(null);

  useEffect(() => {
    if (current.image === visualState.image) return;
    setPrevious(current);
    setCurrent(visualState);
    const timer = window.setTimeout(() => setPrevious(null), 280);
    return () => window.clearTimeout(timer);
  }, [current, visualState]);

  const criticalStyle = {
    position: 'relative',
    width: `var(--dh-avatar-size, ${pixelSize}px)`,
    height: `var(--dh-avatar-size, ${pixelSize}px)`,
    overflow: 'hidden',
    flex: 'none',
    borderRadius: '9999px',
  } as CSSProperties;

  return (
    <div
      className={`dh-avatar ${isSmall ? 'dh-avatar-small' : 'dh-avatar-large'} ${
        current.state === 'thinking' ? 'dh-avatar-thinking' : ''
      } dh-avatar-state-${current.state}`}
      style={criticalStyle}
      aria-label={EMOTION_LABELS[current.image]}
    >
      {previous && (
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
      <span className="dh-avatar-shine" aria-hidden="true" />
    </div>
  );
}

export { EMOTION_LABELS };
