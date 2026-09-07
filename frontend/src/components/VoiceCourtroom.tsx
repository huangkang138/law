'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff, Send, Volume2, SkipForward, X, Loader2, Gavel, User, Bot, Play, Pause, Settings } from 'lucide-react';

const cn = (...classes: (string | undefined | null | false)[]) => {
  return classes.filter(Boolean).join(' ');
};

interface VoiceCourtroomProps {
  sessionId: string;
  userRole: 'plaintiff' | 'defendant' | 'auto';
  caseDescription?: string;
  onEnd: () => void;
}

interface Message {
  id: string;
  role: 'plaintiff' | 'defendant' | 'judge';
  content: string;
  is_user?: boolean;
  timestamp: number;
}

type CourtPhase = 'opening' | 'plaintiff_statement' | 'defendant_statement' | 'debate' | 'closing' | 'verdict' | 'ended';

export function VoiceCourtroom({ sessionId, userRole, caseDescription = '', onEnd }: VoiceCourtroomProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voiceSpeed, setVoiceSpeed] = useState(1);
  const voiceSpeedRef = useRef(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [currentSpeakingId, setCurrentSpeakingId] = useState<string | null>(null);
  const [isUserTurn, setIsUserTurn] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState<'connecting' | 'ready' | 'speaking' | 'listening' | 'processing' | 'ended'>('connecting');
  const [courtPhase, setCourtPhase] = useState<CourtPhase>('opening');
  const [currentSpeaker, setCurrentSpeaker] = useState<'plaintiff' | 'defendant' | 'judge' | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const speechSynthesisRef = useRef<SpeechSynthesis | null>(null);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const messageQueueRef = useRef<Message[]>([]);
  const isProcessingQueueRef = useRef(false);
  const processSpeechQueueRef = useRef<(() => void) | null>(null);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const lastFinalTranscriptRef = useRef('');
  
  const wsRef = useRef<WebSocket | null>(null);
  const connectionIdRef = useRef<number>(0);

  const getRoleName = (role: 'plaintiff' | 'defendant' | 'judge') => {
    switch (role) {
      case 'plaintiff': return '原告';
      case 'defendant': return '被告';
      case 'judge': return '法官';
    }
  };

  const getRoleColor = (role: 'plaintiff' | 'defendant' | 'judge') => {
    switch (role) {
      case 'plaintiff': return 'text-blue-400';
      case 'defendant': return 'text-red-400';
      case 'judge': return 'text-amber-400';
    }
  };

  const getRoleBgColor = (role: 'plaintiff' | 'defendant' | 'judge') => {
    switch (role) {
      case 'plaintiff': return 'bg-blue-500/20 border-blue-500/30';
      case 'defendant': return 'bg-red-500/20 border-red-500/30';
      case 'judge': return 'bg-amber-500/20 border-amber-500/30';
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      speechSynthesisRef.current = window.speechSynthesis;
      
      // 预检查语音识别支持
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        console.log('[VoiceCourtroom] 浏览器支持语音识别');
      } else {
        console.warn('[VoiceCourtroom] 浏览器不支持语音识别');
      }
    }
    
    return () => {
      if (speechSynthesisRef.current) {
        speechSynthesisRef.current.cancel();
      }
    };
  }, []);

  useEffect(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    const currentConnectionId = ++connectionIdRef.current;
    const encodedCaseDescription = encodeURIComponent(caseDescription);
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/courtroom/ws/${sessionId}?user_role=${userRole}&case_description=${encodedCaseDescription}`;
    
    console.log('[VoiceCourtroom] 连接 WebSocket:', wsUrl, 'connectionId:', currentConnectionId);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      if (connectionIdRef.current !== currentConnectionId) {
        console.log('[VoiceCourtroom] 旧连接已打开，关闭它');
        ws.close();
        return;
      }
      console.log('[VoiceCourtroom] WebSocket 连接成功');
      setStatus('ready');
    };
    
    ws.onmessage = (event) => {
      if (connectionIdRef.current !== currentConnectionId) {
        console.log('[VoiceCourtroom] 忽略旧连接的消息');
        return;
      }
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('[VoiceCourtroom] 解析消息失败:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('[VoiceCourtroom] WebSocket 错误:', error);
    };
    
    ws.onclose = () => {
      console.log('[VoiceCourtroom] WebSocket 连接关闭, connectionId:', currentConnectionId);
    };
    
    return () => {
      if (connectionIdRef.current === currentConnectionId) {
        console.log('[VoiceCourtroom] 清理当前连接, connectionId:', currentConnectionId);
        ws.close();
        wsRef.current = null;
      }
      stopRecording();
    };
  }, [sessionId, userRole, caseDescription]);

  // 用于存储待显示的用户发言提示
  const pendingUserTurnRef = useRef<{user_role: string, message: string} | null>(null);
  // 用于存储 checkAndShowUserTurn 函数的引用，避免循环依赖
  const checkAndShowUserTurnRef = useRef<(() => void) | null>(null);
  // 用于存储已处理的消息ID，避免重复处理
  const processedMessageIdsRef = useRef<Set<string>>(new Set());
  
  // 消息处理函数
  const handleWebSocketMessage = useCallback((data: any) => {
    console.log('[VoiceCourtroom] 收到消息:', data);
    
    // 对于 user_turn 消息，不进行去重，确保用户输入框能够正常显示
    if (data.type === 'user_turn') {
      console.log('[VoiceCourtroom] 处理 user_turn 消息:', data);
      // 存储用户发言提示
      pendingUserTurnRef.current = {
        user_role: data.user_role,
        message: data.message
      };
      // 立即检查是否可以显示用户输入框
      checkAndShowUserTurnRef.current?.();
      return;
    }
    
    // 对于 message 类型的消息，使用内容和角色的组合作为唯一标识
    if (data.type === 'message') {
      // 避免重复添加用户自己的消息
      if (data.is_user) {
        console.log('[VoiceCourtroom] 跳过用户自己的消息，避免重复');
        return;
      }
      
      // 生成基于内容和角色的唯一标识，去除空白字符和换行符以提高去重效果
      const cleanContent = data.content.replace(/\s+/g, '').substring(0, 200);
      const messageKey = `${data.role}-${cleanContent}`;
      
      // 避免重复处理相同的消息
      if (processedMessageIdsRef.current.has(messageKey)) {
        console.log('[VoiceCourtroom] 跳过重复消息');
        return;
      }
      
      // 标记消息为已处理
      processedMessageIdsRef.current.add(messageKey);
      
      console.log('[VoiceCourtroom] 添加消息到列表:', data.role, data.is_user);
      const newMessage: Message = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: data.role,
        content: data.content,
        is_user: data.is_user || false,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, newMessage]);
      if (!data.is_user) {
        messageQueueRef.current.push(newMessage);
        processSpeechQueueRef.current?.();
      }
      return;
    }
    
    // 其他类型的消息
    switch (data.type) {
      case 'phase_change':
        setCourtPhase(data.phase);
        break;
      case 'session_end':
        setStatus('ended');
        setCourtPhase('ended');
        break;
      case 'error':
        console.error('服务器错误:', data.message);
        break;
    }
  }, []);
  
  // 检查是否可以显示用户输入框
  const checkAndShowUserTurn = useCallback(() => {
    // 直接检查语音合成状态，而不是依赖状态变量
    const isSpeaking = speechSynthesisRef.current?.speaking || false;
    console.log('[VoiceCourtroom] checkAndShowUserTurn:', { 
      hasPending: !!pendingUserTurnRef.current, 
      isSpeaking, 
      currentSpeakingId,
      isPlaying
    });
    
    if (pendingUserTurnRef.current) {
      // 即使有语音正在播放，也显示用户输入框
      // 这样可以确保用户能够及时看到输入框，不会错过发言机会
      console.log('[VoiceCourtroom] 显示用户输入框');
      setIsUserTurn(true);
      setStatus('listening');
      setCurrentSpeaker(pendingUserTurnRef.current.user_role as any || (userRole === 'plaintiff' ? 'plaintiff' : 'defendant'));
      pendingUserTurnRef.current = null;
    }
  }, [userRole]);
  
  // 更新 checkAndShowUserTurnRef 的引用
  useEffect(() => {
    checkAndShowUserTurnRef.current = checkAndShowUserTurn as () => void;
  }, [checkAndShowUserTurn]);

  const addMessage = useCallback((role: 'plaintiff' | 'defendant' | 'judge', content: string, isUser: boolean = false) => {
    console.log('[VoiceCourtroom] addMessage:', { role, isUser, content: content.substring(0, 50) });
    const newMessage: Message = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role,
      content,
      is_user: isUser,
      timestamp: Date.now()
    };

    setMessages(prev => {
      const updated = [...prev, newMessage];
      console.log('[VoiceCourtroom] 消息列表更新:', updated.length, '条消息');
      return updated;
    });

    if (!isUser) {
      messageQueueRef.current.push(newMessage);
      processSpeechQueueRef.current?.();
    }
  }, []);

  const getVoiceForRole = useCallback((role: 'plaintiff' | 'defendant' | 'judge') => {
    if (!speechSynthesisRef.current) return null;
    const voices = speechSynthesisRef.current.getVoices();
    const chineseVoices = voices.filter(v => v.lang.includes('zh') || v.lang.includes('cmn'));
    
    if (chineseVoices.length === 0) return null;
    
    // 优先尝试选择不同的语音
    if (role === 'judge') {
      // 法官：优先选择男性声音或低沉的声音
      const maleVoices = chineseVoices.filter(v => 
        v.name.includes('男') || 
        v.name.includes('male') || 
        v.name.includes('Yun') ||
        v.name.includes('Jia') ||
        v.name.includes('Kang')
      );
      return maleVoices[0] || chineseVoices[0];
    } else if (role === 'plaintiff') {
      // 原告：优先选择女性声音
      const femaleVoices = chineseVoices.filter(v => 
        v.name.includes('女') || 
        v.name.includes('female') ||
        v.name.includes('Xia') ||
        v.name.includes('Yan') ||
        v.name.includes('Xiao')
      );
      return femaleVoices[0] || chineseVoices[Math.min(1, chineseVoices.length - 1)];
    } else {
      // 被告：选择另一种声音
      const otherVoices = chineseVoices.filter(v => 
        v.name.includes('Mei') ||
        v.name.includes('Tian') ||
        v.name.includes('Ling')
      );
      return otherVoices[0] || chineseVoices[Math.min(2, chineseVoices.length - 1)];
    }
  }, []);

  const filterText = (text: string): string => {
    return text
      .replace(/【[^】]*】/g, '')
      .replace(/\[[^\]]*\]/g, '')
      .replace(/（[^）]*）/g, '')
      .replace(/\([^)]*\)/g, '')
      .replace(/审判长[：:]\s*/g, '')
      .replace(/原告[：:]\s*/g, '')
      .replace(/被告[：:]\s*/g, '')
      .replace(/法官[：:]\s*/g, '')
      .replace(/(?:[\u2700-\u27bf]|(?:\ud83c[\udde6-\uddff]){2}|[\ud800-\udbff][\udc00-\udfff]|[\u0023-\u0039]\ufe0f?\u20e3|\u3299|\u3297|\u303d|\u3030|\u24c2|\ud83c[\udd70-\udd71]|\ud83c[\udd7e-\udd7f]|\ud83c\udd8e|\ud83c[\udd91-\udd9a]|\ud83c[\udde6-\uddff]|[\ud83c[\ude01-\ude02]|\ud83c\ude1a|\ud83c\ude2f|[\ud83c[\ude32-\ude3a]|[\ud83c[\ude50-\ude51]|\u203c|\u2049|[\u25aa-\u25ab]|\u25b6|\u25c0|[\u25fb-\u25fe]|\u00a9|\u00ae|\u2122|\u2139|\ud83c\udc04|[\u2600-\u26FF]|\u2b05|\u2b06|\u2b07|\u2b1b|\u2b1c|\u2b50|\u2b55|\u231a|\u231b|\u2328|\u23cf|[\u23e9-\u23f3]|[\u23f8-\u23fa]|\ud83c\udccf|\u2934|\u2935|[\u2190-\u21ff])/g, '')
      .replace(/[⚖️]/g, '')
      .replace(/[*+#@]/g, '')
      .replace(/[-]{2,}/g, '')
      .replace(/[•·]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  };

  const processSpeechQueue = useCallback(() => {
    if (isProcessingQueueRef.current || isPaused) return;

    const speakNext = () => {
      if (messageQueueRef.current.length === 0) {
        isProcessingQueueRef.current = false;
        setIsPlaying(false);
        setCurrentSpeakingId(null);
        // 队列播放完毕后检查是否应该显示用户输入框
        setTimeout(() => checkAndShowUserTurnRef.current?.(), 300);
        return;
      }

      isProcessingQueueRef.current = true;
      const message = messageQueueRef.current.shift()!;

      speakMessage(message, () => {
        setTimeout(() => speakNext(), 500);
      });
    };

    if (!isProcessingQueueRef.current) {
      setIsPlaying(true);
      speakNext();
    }
  }, [isPaused]);

  // 将 processSpeechQueue 保存到 ref，供其他函数使用
  processSpeechQueueRef.current = processSpeechQueue;

  const speakMessage = useCallback((message: Message, onComplete: () => void) => {
    if (!speechSynthesisRef.current) {
      onComplete();
      return;
    }
    
    const cleanContent = filterText(message.content);
    if (!cleanContent) {
      onComplete();
      return;
    }
    
    speechSynthesisRef.current.cancel();
    
    const utterance = new SpeechSynthesisUtterance(cleanContent);
    
    // 根据角色设置不同的语音参数 - 增大差异
    let roleConfig;
    switch (message.role) {
      case 'judge':
        // 法官：更低沉、更慢、更有权威感
        roleConfig = {
          pitch: 0.7,       // 更低音调
          rate: voiceSpeedRef.current * 0.8,   // 更慢
          volume: 1.1       // 稍大音量
        };
        break;
      case 'plaintiff':
        // 原告：正常音调，正常语速
        roleConfig = {
          pitch: 1.0,       // 标准音调
          rate: voiceSpeedRef.current * 1.2,
          volume: 1
        };
        break;
      case 'defendant':
        // 被告：更高音调，更快
        roleConfig = {
          pitch: 1.3,       // 更高音调
          rate: voiceSpeedRef.current * 1.35,  // 更快
          volume: 0.95      // 稍小音量
        };
        break;
    }

    // 限制语速范围在 0.1 到 10 之间（浏览器TTS的限制）
    const clampedRate = Math.max(0.1, Math.min(10, roleConfig.rate));

    console.log(`[VoiceCourtroom] 播放语音: role=${message.role}, voiceSpeed=${voiceSpeedRef.current}, finalRate=${clampedRate}`);
    
    utterance.rate = clampedRate;
    utterance.pitch = roleConfig.pitch;
    utterance.volume = roleConfig.volume;
    utterance.lang = 'zh-CN';
    
    const voice = getVoiceForRole(message.role);
    if (voice) {
      utterance.voice = voice;
    }
    
    utterance.onstart = () => {
      setCurrentSpeakingId(message.id);
      setCurrentSpeaker(message.role);
      setStatus('speaking');
    };
    
    utterance.onend = () => {
      setCurrentSpeakingId(null);
      setStatus('ready');
      onComplete();
      // 语音播放结束后检查是否应该显示用户输入框
      setTimeout(() => checkAndShowUserTurnRef.current?.(), 100);
    };
    
    utterance.onerror = () => {
      setCurrentSpeakingId(null);
      setStatus('ready');
      onComplete();
      // 语音播放出错后也检查是否应该显示用户输入框
      setTimeout(() => checkAndShowUserTurnRef.current?.(), 100);
    };
    
    currentUtteranceRef.current = utterance;
    speechSynthesisRef.current.speak(utterance);
  }, [getVoiceForRole]);

  const togglePause = useCallback(() => {
    if (!speechSynthesisRef.current) return;
    
    if (isPaused) {
      speechSynthesisRef.current.resume();
      setIsPaused(false);
      processSpeechQueue();
    } else {
      speechSynthesisRef.current.pause();
      setIsPaused(true);
    }
  }, [isPaused, processSpeechQueue]);

  const skipCurrent = useCallback(() => {
    if (speechSynthesisRef.current) {
      speechSynthesisRef.current.cancel();
    }
  }, []);

  const startSpeechRecognition = useCallback(() => {
    console.log('[VoiceCourtroom] 启动语音识别');
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('[VoiceCourtroom] 浏览器不支持语音识别');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'zh-CN';
      // 减少语音识别的延迟
      recognition.maxAlternatives = 1;
      
      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const result = event.results[i];
          const transcript = result[0].transcript;

          if (result.isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          lastFinalTranscriptRef.current += finalTranscript;
          setUserInput(lastFinalTranscriptRef.current);
        } else if (interimTranscript) {
          setUserInput(lastFinalTranscriptRef.current + interimTranscript);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('[VoiceCourtroom] 语音识别错误:', event.error);
      };

      recognition.onend = () => {
        if (isRecording) {
          try {
            recognition.start();
          } catch (e) {
            console.warn('[VoiceCourtroom] 重新启动语音识别失败:', e);
          }
        }
      };

      // 立即启动语音识别
      recognition.start();
      recognitionRef.current = recognition;
    } catch (error) {
      console.error('[VoiceCourtroom] 启动语音识别失败:', error);
    }
  }, [isRecording]);

  const monitorAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const checkLevel = () => {
      if (!isRecording || !analyserRef.current) return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(Math.min(100, average * 2));
      
      requestAnimationFrame(checkLevel);
    };
    
    checkLevel();
  }, [isRecording]);

  const startRecording = useCallback(async () => {
    try {
      setUserInput('');
      lastFinalTranscriptRef.current = '';

      // 1. 立即启动语音识别，不需要等待音频流设置完成
      startSpeechRecognition();

      // 2. 并行获取音频流，用于音频可视化
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      audioContextRef.current = new AudioContextClass();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;

      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);

      mediaRecorderRef.current = new MediaRecorder(stream);
      mediaRecorderRef.current.start();
      setIsRecording(true);

      // 3. 启动音频电平监控
      monitorAudioLevel();

    } catch (error) {
      console.error('[VoiceCourtroom] 启动录音失败:', error);
    }
  }, [startSpeechRecognition, monitorAudioLevel]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
    
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
  }, [isRecording]);

  const submitUserInput = useCallback(() => {
    if (!userInput.trim()) return;

    // 立即在本地显示用户输入的内容
    const messageId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const userMessage: Message = {
      id: messageId,
      role: userRole === 'plaintiff' ? 'plaintiff' : 'defendant',
      content: userInput,
      is_user: true,
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, userMessage]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('[VoiceCourtroom] 发送用户输入:', userInput);
      const userInputData = {
        type: 'user_input',
        content: userInput,
        id: messageId
      };
      console.log('[VoiceCourtroom] 发送数据:', userInputData);
      wsRef.current.send(JSON.stringify(userInputData));
    } else {
      console.error('[VoiceCourtroom] WebSocket 连接未打开，无法发送用户输入');
      // 尝试重新连接
      const encodedCaseDescription = encodeURIComponent(caseDescription);
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/api/courtroom/ws/${sessionId}?user_role=${userRole}&case_description=${encodedCaseDescription}`;
      const newWs = new WebSocket(wsUrl);
      newWs.onopen = () => {
        console.log('[VoiceCourtroom] WebSocket 重新连接成功，发送用户输入');
        const userInputData = {
          type: 'user_input',
          content: userInput,
          id: messageId
        };
        console.log('[VoiceCourtroom] 发送数据:', userInputData);
        newWs.send(JSON.stringify(userInputData));
        wsRef.current = newWs;
      };
      if (wsRef.current) {
        newWs.onmessage = wsRef.current.onmessage || null;
        newWs.onerror = wsRef.current.onerror || null;
        newWs.onclose = wsRef.current.onclose || null;
      }
    }

    setUserInput('');
    setIsUserTurn(false);
    stopRecording();
  }, [userInput, stopRecording, userRole, sessionId, caseDescription]);

  const skipTurn = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('[VoiceCourtroom] 发送跳过发言');
      wsRef.current.send(JSON.stringify({
        type: 'skip_turn'
      }));
    } else {
      console.error('[VoiceCourtroom] WebSocket 连接未打开，无法发送跳过发言');
      // 尝试重新连接
      const encodedCaseDescription = encodeURIComponent(caseDescription);
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/api/courtroom/ws/${sessionId}?user_role=${userRole}&case_description=${encodedCaseDescription}`;
      const newWs = new WebSocket(wsUrl);
      newWs.onopen = () => {
        console.log('[VoiceCourtroom] WebSocket 重新连接成功，发送跳过发言');
        newWs.send(JSON.stringify({
          type: 'skip_turn'
        }));
        wsRef.current = newWs;
      };
      if (wsRef.current) {
        newWs.onmessage = wsRef.current.onmessage || null;
        newWs.onerror = wsRef.current.onerror || null;
        newWs.onclose = wsRef.current.onclose || null;
      }
    }
    
    setUserInput('');
    setIsUserTurn(false);
    stopRecording();
  }, [stopRecording, sessionId, userRole, caseDescription]);

  const endSession = useCallback(() => {
    // 立即停止所有语音播放
    if (speechSynthesisRef.current) {
      speechSynthesisRef.current.cancel();
    }
    
    // 清空消息队列
    messageQueueRef.current = [];
    isProcessingQueueRef.current = false;
    setIsPlaying(false);
    setCurrentSpeakingId(null);
    
    // 关闭WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'end_session'
      }));
      wsRef.current.close();
    }
    
    stopRecording();
    onEnd();
  }, [stopRecording, onEnd]);

  const changeSpeed = useCallback((newSpeed: number) => {
    setVoiceSpeed(newSpeed);
    voiceSpeedRef.current = newSpeed;  // 同步更新 ref
    setShowSpeedMenu(false);
    
    // 只更新速度设置，不重新播放当前语音
    // 下一条语音会使用新的速度
  }, []);

  const speedOptions = [0.5, 0.75, 1, 1.25, 1.5, 2];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Gavel className="text-amber-400" size={24} />
            <span className="text-white font-bold text-lg">语音模拟法庭</span>
          </div>
          
          <div className="h-6 w-px bg-slate-600" />
          
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              status === 'connecting' ? "bg-yellow-500 animate-pulse" :
              status === 'listening' ? "bg-green-500 animate-pulse" :
              status === 'speaking' ? "bg-blue-500 animate-pulse" :
              status === 'ended' ? "bg-red-500" :
              "bg-slate-500"
            )} />
            <span className="text-slate-300 text-sm">
              {status === 'connecting' ? '连接中...' :
               status === 'listening' ? '请发言' :
               status === 'speaking' ? '正在播放' :
               status === 'ended' ? '已结束' :
               '就绪'}
            </span>
          </div>
          
          {currentSpeaker && status === 'speaking' && (
            <div className={cn("px-3 py-1 rounded-full text-sm", getRoleColor(currentSpeaker), getRoleBgColor(currentSpeaker), "border")}>
              {getRoleName(currentSpeaker)}发言中
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setShowSpeedMenu(!showSpeedMenu)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            >
              <Settings size={16} />
              <span className="text-sm">{voiceSpeed}x</span>
            </button>
            
            {showSpeedMenu && (
              <div className="absolute right-0 top-full mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 py-1 min-w-[80px]">
                {speedOptions.map(speed => (
                  <button
                    key={speed}
                    onClick={() => changeSpeed(speed)}
                    className={cn(
                      "w-full px-4 py-2 text-sm text-left transition-colors",
                      voiceSpeed === speed ? "text-amber-400 bg-slate-700" : "text-slate-300 hover:bg-slate-700"
                    )}
                  >
                    {speed}x
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <button
            onClick={skipCurrent}
            disabled={!isPlaying}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            <SkipForward size={16} />
            <span className="text-sm">跳过</span>
          </button>
          
          <button
            onClick={endSession}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-slate-700 transition-colors"
          >
            <X size={16} />
            <span className="text-sm">结束</span>
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="flex-1 flex items-center justify-center p-8 bg-[url('/images/法院.jpg')] bg-cover bg-center">
          <div className="flex items-center gap-16">
            <div className={cn(
              "flex flex-col items-center gap-4 transition-all duration-300",
              currentSpeaker === 'plaintiff' ? "scale-110" : "opacity-60"
            )} style={{ transform: 'translateX(-80px)' }}>
              <div className={cn(
                "w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300",
                currentSpeaker === 'plaintiff' 
                  ? "bg-blue-500 shadow-lg shadow-blue-500/50" 
                  : "bg-blue-500/30"
              )}>
                <User size={40} className="text-white" />
              </div>
              <span className={cn(
                "text-lg font-medium transition-colors",
                currentSpeaker === 'plaintiff' ? "text-blue-400" : "text-slate-400"
              )}>
                原告
                {userRole === 'plaintiff' && <span className="text-xs ml-1 text-amber-400">(您)</span>}
              </span>
            </div>
            
            <div className={cn(
              "flex flex-col items-center gap-4 transition-all duration-300",
              currentSpeaker === 'judge' ? "scale-110" : "opacity-60"
            )} style={{ transform: 'translateY(-140px)' }}>
              <div className={cn(
                "w-28 h-28 rounded-full flex items-center justify-center transition-all duration-300",
                currentSpeaker === 'judge' 
                  ? "bg-amber-500 shadow-lg shadow-amber-500/50" 
                  : "bg-amber-500/30"
              )}>
                <Gavel size={48} className="text-white" />
              </div>
              <span className={cn(
                "text-xl font-bold transition-colors",
                currentSpeaker === 'judge' ? "text-amber-400" : "text-slate-400"
              )}>
                法官
              </span>
            </div>
            
            <div className={cn(
              "flex flex-col items-center gap-4 transition-all duration-300",
              currentSpeaker === 'defendant' ? "scale-110" : "opacity-60"
            )} style={{ transform: 'translateX(80px)' }}>
              <div className={cn(
                "w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300",
                currentSpeaker === 'defendant' 
                  ? "bg-red-500 shadow-lg shadow-red-500/50" 
                  : "bg-red-500/30"
              )}>
                <Bot size={40} className="text-white" />
              </div>
              <span className={cn(
                "text-lg font-medium transition-colors",
                currentSpeaker === 'defendant' ? "text-red-400" : "text-slate-400"
              )}>
                被告
                {userRole === 'defendant' && <span className="text-xs ml-1 text-amber-400">(您)</span>}
              </span>
            </div>
          </div>
        </div>

        <div className="h-64 border-t border-slate-700/50 bg-slate-900/80 backdrop-blur-sm flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700/30">
            <span className="text-slate-400 text-sm font-medium">对话记录</span>
            <span className="text-slate-500 text-xs">{messages.length} 条消息</span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-500 text-sm">
                等待庭审开始...
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-2 p-2 rounded-lg transition-colors",
                    currentSpeakingId === message.id ? "bg-slate-700/50" : ""
                  )}
                >
                  <div className={cn(
                    "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs",
                    message.role === 'plaintiff' ? "bg-blue-500/30 text-blue-400" :
                    message.role === 'defendant' ? "bg-red-500/30 text-red-400" :
                    "bg-amber-500/30 text-amber-400"
                  )}>
                    {message.role === 'plaintiff' ? '原' : message.role === 'defendant' ? '被' : '法'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={cn("text-sm font-medium", getRoleColor(message.role))}>
                        {getRoleName(message.role)}
                        {message.is_user && <span className="text-amber-400 ml-1">(您)</span>}
                      </span>
                    </div>
                    <p className="text-slate-300 text-sm break-words">{message.content}</p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {isUserTurn && (
        <div className="border-t border-slate-700/50 bg-slate-900/90 backdrop-blur-sm p-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center gap-3 mb-3">
              <div className={cn(
                "px-3 py-1 rounded-full text-sm",
                userRole === 'plaintiff' ? "bg-blue-500/20 text-blue-400" : "bg-red-500/20 text-red-400"
              )}>
                轮到您发言
              </div>
              {isRecording && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-red-400 text-sm">录音中</span>
                </div>
              )}
            </div>
            
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <textarea
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  placeholder="输入您的发言内容，或点击麦克风进行语音输入..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 resize-none focus:outline-none focus:border-amber-500/50"
                  rows={2}
                />
                
                {isRecording && (
                  <div className="absolute bottom-2 right-2 flex items-center gap-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className="w-1 bg-amber-400 rounded-full transition-all"
                        style={{
                          height: `${Math.random() * 16 + 4}px`,
                          opacity: audioLevel > i * 20 ? 1 : 0.3
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <div className="relative group">
                  <button
                    onClick={isRecording ? stopRecording : startRecording}
                    className={cn(
                      "flex items-center justify-center w-12 h-12 rounded-xl transition-colors",
                      isRecording 
                        ? "bg-red-500 hover:bg-red-600 text-white" 
                        : "bg-slate-700 hover:bg-slate-600 text-slate-300"
                    )}
                  >
                    {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
                  </button>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-slate-200 text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    {isRecording ? '停止录音' : '语音输入'}
                  </div>
                </div>
                
                <div className="relative group">
                  <button
                    onClick={submitUserInput}
                    disabled={!userInput.trim()}
                    className="flex items-center justify-center w-12 h-12 rounded-xl bg-amber-500 hover:bg-amber-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send size={20} />
                  </button>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-slate-200 text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    发送消息
                  </div>
                </div>
                
                <div className="relative group">
                  <button
                    onClick={skipTurn}
                    className="flex items-center justify-center w-12 h-12 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
                  >
                    <SkipForward size={20} />
                  </button>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-slate-200 text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    跳过发言
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {status === 'ended' && (
        <div className="border-t border-slate-700/50 bg-slate-900/90 backdrop-blur-sm p-4">
          <div className="max-w-3xl mx-auto text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Gavel className="text-amber-400" size={24} />
              <span className="text-white font-bold text-lg">庭审结束</span>
            </div>
            <p className="text-slate-400 text-sm">感谢参与本次模拟法庭</p>
          </div>
        </div>
      )}
    </div>
  );
}