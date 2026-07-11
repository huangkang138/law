'use client';

import Image from 'next/image';

import type { DigitalHumanEmotion } from '@/services/digitalHumanApi';

interface DigitalHumanAvatarProps {
  emotion: DigitalHumanEmotion;
  size?: 'small' | 'large';
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
  size = 'large',
}: DigitalHumanAvatarProps) {
  const isSmall = size === 'small';

  return (
    <div
      className={`dh-avatar ${isSmall ? 'dh-avatar-small' : 'dh-avatar-large'} ${
        emotion === 'thinking' ? 'dh-avatar-thinking' : ''
      }`}
      aria-label={EMOTION_LABELS[emotion]}
    >
      <Image
        key={emotion}
        src={`/digital-human/first-gen/${emotion}.png`}
        alt={`法小助：${EMOTION_LABELS[emotion]}`}
        fill
        priority={emotion === 'idle'}
        sizes={isSmall ? '104px' : '148px'}
        className="dh-avatar-image"
      />
      <span className="dh-avatar-shine" aria-hidden="true" />
    </div>
  );
}

export { EMOTION_LABELS };
