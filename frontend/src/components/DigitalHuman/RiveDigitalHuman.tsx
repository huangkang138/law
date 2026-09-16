'use client';

import { useEffect, useRef, useState } from 'react';
import {
  Alignment,
  Fit,
  Layout,
  RuntimeLoader,
  useRive,
  useViewModelInstanceBoolean,
  useViewModelInstanceNumber,
  useViewModelInstanceTrigger,
} from '@rive-app/react-webgl2';

import type { AvatarVisualState } from './AvatarStateAdapter';

const RIVE_SRC = '/digital-human/law-xiaozhi/law-xiaozhi.riv';
const RIVE_WASM_SRC = '/digital-human/law-xiaozhi/rive.wasm';
const RIVE_ARTBOARD = 'Artboard 1';
const RIVE_STATE_MACHINE = 'AvatarStateMachine';
const RIVE_VIEW_MODEL = 'ViewModel1';

// The values are the numeric states authored by the Rive ViewModel.
const EXPRESSION_VALUES = {
  normal: 1,
  think: 2,
  serious: 3,
  happy: 4,
  surprise: 5,
} as const;

const RIVE_LAYOUT = new Layout({ fit: Fit.Contain, alignment: Alignment.BottomCenter });

RuntimeLoader.setWasmUrl(RIVE_WASM_SRC);
RuntimeLoader.setWasmFallbackUrl(null);

interface RiveDigitalHumanProps {
  visualState: AvatarVisualState;
  voiceSpeaking: boolean;
  visible: boolean;
  onReady: () => void;
  onError: (error: unknown) => void;
}

function expressionForState(image: AvatarVisualState['image']): number {
  switch (image) {
    case 'thinking':
      return EXPRESSION_VALUES.think;
    case 'serious':
    case 'error':
      return EXPRESSION_VALUES.serious;
    case 'success':
      return EXPRESSION_VALUES.happy;
    default:
      return EXPRESSION_VALUES.normal;
  }
}

export default function RiveDigitalHuman({
  visualState,
  voiceSpeaking,
  visible,
  onReady,
  onError,
}: RiveDigitalHumanProps) {
  const [failed, setFailed] = useState(false);
  const readyReported = useRef(false);
  const blinkRef = useRef<() => void>(() => undefined);
  const { rive, RiveComponent } = useRive(
    visible && !failed
      ? {
          src: RIVE_SRC,
          artboard: RIVE_ARTBOARD,
          stateMachine: RIVE_STATE_MACHINE,
          autoplay: true,
          autoBind: true,
          enableRiveAssetCDN: false,
          layout: RIVE_LAYOUT,
          onLoadError: (error) => {
            setFailed(true);
            onError(error);
          },
        }
      : null,
    {
      shouldResizeCanvasToContainer: true,
      shouldUseIntersectionObserver: false,
    },
  );
  // autoBind 已把编辑器默认 ViewModel 实例绑定到当前 Rive 实例；直接读取它，
  // 不再通过 useViewModelInstance(useDefault) 二次创建默认实例。
  const viewModelInstance = rive?.viewModelInstance ?? null;
  const { setValue: setExpression } = useViewModelInstanceNumber('expression', viewModelInstance);
  const { setValue: setSpeaking } = useViewModelInstanceBoolean('speaking', viewModelInstance);
  const { trigger: triggerBlink } = useViewModelInstanceTrigger('blink', viewModelInstance);

  blinkRef.current = triggerBlink;

  useEffect(() => {
    if (!visible) {
      readyReported.current = false;
      return;
    }
    if (!rive || !viewModelInstance) return;

    const expression = viewModelInstance.number('expression');
    const speaking = viewModelInstance.boolean('speaking');
    const blink = viewModelInstance.trigger('blink');
    if (!expression || !speaking || !blink) {
      const error = new Error(`${RIVE_VIEW_MODEL} contract is incomplete or has unexpected property types`);
      setFailed(true);
      onError(error);
      return;
    }

    if (!readyReported.current) {
      readyReported.current = true;
      onReady();
    }
  }, [onError, onReady, rive, viewModelInstance, visible]);

  useEffect(() => {
    if (!visible || !viewModelInstance) return;
    setExpression(expressionForState(visualState.image));
    setSpeaking(voiceSpeaking);
  }, [setExpression, setSpeaking, viewModelInstance, visible, visualState.image, voiceSpeaking]);

  useEffect(() => {
    if (!visible || !viewModelInstance) return;
    const timer = window.setInterval(() => blinkRef.current(), 4200);
    return () => window.clearInterval(timer);
  }, [viewModelInstance, visible]);

  if (!visible || failed) return null;

  return (
    <div className="dh-rive-layer" aria-hidden="true">
      <RiveComponent className="dh-rive-canvas" />
    </div>
  );
}
