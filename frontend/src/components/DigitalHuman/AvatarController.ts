import { adaptAvatarState, type AvatarStateInput, type AvatarVisualState } from './AvatarStateAdapter';

// 统一保留数字人视觉状态入口；业务状态仍由现有 Zustand store 管理。
export function resolveAvatarVisualState(input: AvatarStateInput): AvatarVisualState {
  return adaptAvatarState(input);
}
