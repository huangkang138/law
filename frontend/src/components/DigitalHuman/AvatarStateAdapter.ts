import type { DigitalHumanEmotion } from '@/services/digitalHumanApi';

export type AvatarState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'success' | 'warning';

export interface AvatarVisualState {
  state: AvatarState;
  image: 'idle' | 'thinking' | 'talk_normal' | 'success' | 'serious' | 'error';
}

export interface AvatarStateInput {
  emotion: DigitalHumanEmotion;
  state?: AvatarState;
  isLoading?: boolean;
  voiceSpeaking?: boolean;
  // 为后续局部嘴型覆盖预留；完整 PNG 阶段不改变原图。
  mouthOpen?: boolean;
}

const STATE_IMAGES: Record<Exclude<AvatarState, 'warning'>, AvatarVisualState['image']> = {
  idle: 'idle',
  listening: 'idle',
  thinking: 'thinking',
  speaking: 'talk_normal',
  success: 'success',
};

export function adaptAvatarState({
  emotion,
  state,
  isLoading = false,
  voiceSpeaking = false,
}: AvatarStateInput): AvatarVisualState {
  if (state) {
    return state === 'warning'
      ? { state, image: emotion === 'error' ? 'error' : 'serious' }
      : { state, image: STATE_IMAGES[state] };
  }
  if (voiceSpeaking) return { state: 'speaking', image: 'talk_normal' };
  if (isLoading || emotion === 'thinking') return { state: 'thinking', image: 'thinking' };
  if (emotion === 'success') return { state: 'success', image: 'success' };
  if (emotion === 'error') return { state: 'warning', image: 'error' };
  if (emotion === 'serious') return { state: 'warning', image: 'serious' };
  return { state: 'idle', image: 'idle' };
}
