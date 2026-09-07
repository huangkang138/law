'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Loader2, AlertCircle, History, FileText, MessageSquare, Volume2, Play, Pause, SkipForward, X, Mic, MicOff, Send, Users, Gavel, Bot, User, Sparkles, Crown, Shield, BookOpen, Home, Menu, ChevronRight, Settings, Star } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ScaleIcon from '@/components/ScaleIcon';
import { useRouter, useSearchParams } from 'next/navigation';
import { generateComplaintPDF } from '@/utils/pdfGenerator';
import { VoiceCourtroom } from '@/components/VoiceCourtroom';
import { useDataCache } from '@/hooks/useDataCache';
import { createFavorite } from '@/lib/api';
import { showAlert } from '@/components/AlertDialog';

interface Message {
  role: 'plaintiff' | 'defendant' | 'judge';
  content: string;
}

interface ProgressInfo {
  status: 'processing' | 'completed' | 'error';
  progress: number;
  current_step: string;
}

type SimulationMode = 'text' | 'voice';
type ViewMode = 'input' | 'courtroom' | 'text-result';

export default function DebatePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [caseDescription, setCaseDescription] = useState('');
  const [debating, setDebating] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [currentRole, setCurrentRole] = useState<'plaintiff' | 'defendant' | 'judge' | null>(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState<ProgressInfo | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [simulationMode, setSimulationMode] = useState<SimulationMode>('text');
  const [viewMode, setViewMode] = useState<ViewMode>('input');
  
  // 语音模式相关状态
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentVoiceIndex, setCurrentVoiceIndex] = useState(0);
  const [voiceSpeed, setVoiceSpeed] = useState(1);
  const [isVoiceInitialized, setIsVoiceInitialized] = useState(false);
  const [currentSpeakingText, setCurrentSpeakingText] = useState('');
  const [userRole, setUserRole] = useState<'plaintiff' | 'defendant' | 'auto'>('auto');
  const [isUserTurn, setIsUserTurn] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [favoritedMessages, setFavoritedMessages] = useState<Set<number>>(new Set());
  const speechSynthesisRef = useRef<SpeechSynthesis | null>(null);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesRef = useRef<Message[]>([]);
  const isPlayingRef = useRef(false);
  const hasPendingSpeechRef = useRef(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  
  // 同步 messages 到 ref
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // 处理从历史记录跳转过来的sessionId参数
  useEffect(() => {
    const urlSessionId = searchParams.get('sessionId');
    if (urlSessionId) {
      loadDebateDetails(urlSessionId);
    }
  }, [searchParams]);

  const loadDebateDetails = async (id: string) => {
    setDebating(true);
    setError('');
    setMessages([]);
    setCurrentMessage('');
    setCurrentRole(null);
    setProgress({
      status: 'processing',
      progress: 0,
      current_step: '正在加载历史辩论记录...'
    });

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/api/debate/${id}/full-details`);
      
      if (!response.ok) {
        throw new Error('加载历史记录失败');
      }

      const data = await response.json();
      
      if (data.debate_turns && data.debate_turns.length > 0) {
        // 转换数据格式，适配前端需求
        const formattedMessages = data.debate_turns.map((turn: any) => ({
          role: turn.party as 'plaintiff' | 'defendant' | 'judge',
          content: turn.content
        }));
        // 直接设置消息，不需要逐字显示
        setMessages(formattedMessages);
        setSessionId(id);
        setProgress(null);
        setDebating(false);
      }
    } catch (err: any) {
      setError(err.message || '加载历史记录失败');
      setDebating(false);
      setProgress(null);
    }
  };

  useEffect(() => {
    // 只有当有新消息或当前消息更新时才滚动到底部
    // 这样用户可以手动滚动查看历史消息
    if (messages.length > 0 || currentMessage) {
      // 使用setTimeout确保DOM更新后再滚动
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [messages, currentMessage]);

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  // 语音播放相关
  const [voicesLoaded, setVoicesLoaded] = useState(false);
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      speechSynthesisRef.current = window.speechSynthesis;
      
      // 加载语音列表
      const loadVoices = () => {
        const voices = speechSynthesisRef.current?.getVoices() || [];
        console.log('可用语音:', voices.map(v => `${v.name} (${v.lang})`));
        if (voices.length > 0) {
          setVoicesLoaded(true);
        }
      };
      
      loadVoices();
      
      // Chrome需要等待voiceschanged事件
      if (speechSynthesisRef.current) {
        speechSynthesisRef.current.onvoiceschanged = loadVoices;
      }
      
      // 创建音频上下文（用于解锁自动播放）
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      setAudioContext(ctx);
    }
    return () => {
      if (speechSynthesisRef.current) {
        speechSynthesisRef.current.cancel();
      }
      if (audioContext) {
        audioContext.close();
      }
    };
  }, []);

  const exampleCases = [
    '员工张三因拒绝周末加班被公司以严重违反规章制度为由辞退。张三认为公司要求的加班不合理，且未支付加班费，公司辞退行为违法。公司则认为张三多次拒绝工作安排，严重影响工作进度，符合公司规章制度规定的辞退条件。',
    '租客李四租住房屋期间，因楼上漏水导致家具损坏。李四要求房东赔偿损失并减免租金，房东认为漏水是楼上住户责任，与自己无关，拒绝赔偿。李四认为房东有维修义务，应承担连带责任。',
    '外包程序员王五完成项目后，公司以代码质量不达标为由拒绝支付尾款。王五认为已按合同要求完成所有功能，公司应支付全款。公司则认为代码存在多处bug，需要返工，不符合验收标准。',
  ];

  // 获取适合角色的语音
  const getVoiceForRole = (role: 'plaintiff' | 'defendant' | 'judge') => {
    if (!speechSynthesisRef.current) return null;
    const voices = speechSynthesisRef.current.getVoices();
    
    // 优先选择中文语音
    const chineseVoices = voices.filter(v => v.lang.includes('zh') || v.lang.includes('cmn'));
    
    if (chineseVoices.length === 0) {
      console.warn('没有找到中文语音，使用默认语音');
      return null;
    }
    
    console.log(`可用的中文语音: ${chineseVoices.map(v => v.name).join(', ')}`);
    
    // 为不同角色选择不同的语音（如果可用）
    if (role === 'judge') {
      // 法官：选择稳重、成熟的语音
      const judgeVoice = chineseVoices.find(v => v.name.includes('男') || v.name.includes('male'));
      console.log(`法官语音选择: ${judgeVoice ? judgeVoice.name : '默认'}`);
      return judgeVoice || chineseVoices[0];
    } else if (role === 'plaintiff') {
      // 原告：选择积极的语音
      const plaintiffVoice = chineseVoices.find(v => v.name.includes('女') || v.name.includes('female'));
      console.log(`原告语音选择: ${plaintiffVoice ? plaintiffVoice.name : '默认'}`);
      return plaintiffVoice || chineseVoices[0];
    } else {
      // 被告：选择另一种语音
      const defendantVoice = chineseVoices.find(v => !v.name.includes('女') && !v.name.includes('female'));
      console.log(`被告语音选择: ${defendantVoice ? defendantVoice.name : '默认'}`);
      return defendantVoice || chineseVoices[0];
    }
  };

  // 过滤掉表情符号和特殊符号，保留纯文本用于语音
  const filterEmoji = (text: string): string => {
    // 使用正则表达式移除表情符号和特殊符号
    return text
      // 移除所有emoji（使用更兼容的方式）
      .replace(/(?:[\u2700-\u27bf]|(?:\ud83c[\udde6-\uddff]){2}|[\ud800-\udbff][\udc00-\udfff]|[\u0023-\u0039]\ufe0f?\u20e3|\u3299|\u3297|\u303d|\u3030|\u24c2|\ud83c[\udd70-\udd71]|\ud83c[\udd7e-\udd7f]|\ud83c\udd8e|\ud83c[\udd91-\udd9a]|\ud83c[\udde6-\uddff]|[\ud83c[\ude01-\ude02]|\ud83c\ude1a|\ud83c\ude2f|[\ud83c[\ude32-\ude3a]|[\ud83c[\ude50-\ude51]|\u203c|\u2049|[\u25aa-\u25ab]|\u25b6|\u25c0|[\u25fb-\u25fe]|\u00a9|\u00ae|\u2122|\u2139|\ud83c\udc04|[\u2600-\u26FF]|\u2b05|\u2b06|\u2b07|\u2b1b|\u2b1c|\u2b50|\u2b55|\u231a|\u231b|\u2328|\u23cf|[\u23e9-\u23f3]|[\u23f8-\u23fa]|\ud83c\udccf|\u2934|\u2935|[\u2190-\u21ff])/g, '')
      // 移除天平符号和其他常见符号
      .replace(/[⚖]/g, '')
      // 移除星号和其他标识符
      .replace(/[*+#@]/g, '')
      // 清理多余空格
      .replace(/\s+/g, ' ')
      .trim();
  };

  // 语音播放控制
  const speakMessage = useCallback((message: Message, index: number) => {
    if (!speechSynthesisRef.current) {
      console.error('语音合成API不可用');
      return;
    }
    
    // 如果已经在播放，不要中断
    if (isPlayingRef.current) {
      console.log('正在播放语音，跳过新的播放请求');
      return;
    }
    
    // 取消之前的语音
    speechSynthesisRef.current.cancel();
    
    // 解锁音频上下文（浏览器自动播放策略）
    if (audioContext && audioContext.state === 'suspended') {
      audioContext.resume();
    }
    
    // 过滤掉表情符号后再播放
    const cleanContent = filterEmoji(message.content);
    
    if (!cleanContent) {
      console.warn('内容为空，跳过播放');
      // 使用 ref 检查是否有下一条消息
      const currentMessages = messagesRef.current;
      if (index < currentMessages.length - 1) {
        setTimeout(() => {
          speakMessage(currentMessages[index + 1], index + 1);
        }, 800);
      } else {
        setIsPlaying(false);
        isPlayingRef.current = false;
        setCurrentSpeakingText('');
      }
      return;
    }
    
    // 设置当前播放文字
    setCurrentSpeakingText(cleanContent);
    
    const utterance = new SpeechSynthesisUtterance(cleanContent);
    utterance.rate = voiceSpeed;
    utterance.pitch = message.role === 'judge' ? 1.0 : message.role === 'plaintiff' ? 1.05 : 0.95;
    utterance.volume = 1;
    utterance.lang = 'zh-CN';
    
    // 设置声音
    const voice = getVoiceForRole(message.role);
    console.log(`为角色 ${message.role} 选择语音: ${voice ? voice.name : '无'}`);
    if (voice) {
      utterance.voice = voice;
      console.log(`使用语音: ${voice.name} (${voice.lang})`);
    } else {
      console.warn(`没有找到适合角色 ${message.role} 的语音`);
    }
    
    utterance.onstart = () => {
      console.log(`开始播放: ${message.role} - ${cleanContent.substring(0, 30)}...`);
      setIsPlaying(true);
      isPlayingRef.current = true;
      setCurrentVoiceIndex(index);
    };
    
    utterance.onend = () => {
      console.log(`播放结束: ${message.role}`);
      // 先设置为未播放状态
      setIsPlaying(false);
      isPlayingRef.current = false;
      
      // 使用 ref 检查是否有下一条消息
      const currentMessages = messagesRef.current;
      if (index < currentMessages.length - 1) {
        setTimeout(() => {
          speakMessage(currentMessages[index + 1], index + 1);
        }, 800);
      } else {
        // 保留最后一条消息的文字显示
        // 不要清空 currentSpeakingText，让它保持最后一条消息的内容
      }
    };
    
    utterance.onerror = (event) => {
      console.error('语音播放错误:', event);
      setIsPlaying(false);
      isPlayingRef.current = false;
      // 保留最后一条消息的文字显示
      // 不要清空 currentSpeakingText
    };
    
    currentUtteranceRef.current = utterance;
    
    // 确保语音列表已加载
    const voices = speechSynthesisRef.current.getVoices();
    if (voices.length === 0) {
      // 如果语音列表还没加载，等待加载完成后再播放
      speechSynthesisRef.current.onvoiceschanged = () => {
        speechSynthesisRef.current?.speak(utterance);
      };
    } else {
      speechSynthesisRef.current.speak(utterance);
    }
  }, [voiceSpeed, audioContext]);

  const togglePlayPause = () => {
    if (!speechSynthesisRef.current) return;
    
    if (isPlaying) {
      speechSynthesisRef.current.pause();
      setIsPlaying(false);
    } else {
      if (speechSynthesisRef.current.paused) {
        speechSynthesisRef.current.resume();
        setIsPlaying(true);
      } else {
        // 从当前位置开始播放
        const startIndex = currentVoiceIndex < messages.length ? currentVoiceIndex : 0;
        speakMessage(messages[startIndex], startIndex);
      }
    }
  };

  const skipToNext = () => {
    if (!speechSynthesisRef.current) return;
    speechSynthesisRef.current.cancel();
    
    const nextIndex = currentVoiceIndex + 1;
    if (nextIndex < messages.length) {
      speakMessage(messages[nextIndex], nextIndex);
    } else {
      setIsPlaying(false);
      setCurrentVoiceIndex(0);
    }
  };

  const stopVoice = () => {
    if (!speechSynthesisRef.current) return;
    speechSynthesisRef.current.cancel();
    setIsPlaying(false);
    setCurrentVoiceIndex(0);
    setCurrentSpeakingText('');
  };

  // 建立SSE连接
  const setupSSE = useCallback((sid: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const eventSource = new EventSource(`${apiUrl}/api/debate/stream/${sid}`);
    
    // 消息队列，确保按顺序处理
    const messageQueue: Array<{role: 'plaintiff' | 'defendant' | 'judge', content: string}> = [];
    let isProcessing = false;
    
    // 处理消息队列
    const processMessageQueue = async () => {
      if (isProcessing || messageQueue.length === 0) return;
      
      isProcessing = true;
      const message = messageQueue.shift();
      if (message) {
        await displayMessage(message.role, message.content);
      }
      isProcessing = false;
      
      // 处理下一条消息
      if (messageQueue.length > 0) {
        processMessageQueue();
      }
    };
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'connected':
            console.log('SSE连接成功:', data.data.session_id);
            break;
            
          case 'progress':
            setProgress({
              status: 'processing',
              progress: data.data.progress,
              current_step: data.data.step
            });
            break;
            
          case 'message':
            // 将消息加入队列，确保按顺序处理
            messageQueue.push({role: data.data.role, content: data.data.content});
            processMessageQueue();
            break;
            
          case 'user_turn':
            // 轮到用户发言
            console.log('轮到用户发言');
            setIsUserTurn(true);
            break;
            
          case 'complete':
            // 处理完成，保存完整数据
            console.log('辩论完成，获取完整数据:', data.data);
            eventSource.close();
            setDebating(false);
            setProgress(null);
            // 语音模式下标记为已初始化
            if (simulationMode === 'voice') {
              setIsVoiceInitialized(true);
            }
            break;
            
          case 'error':
            // 处理错误
            eventSource.close();
            setError(data.data.error || '处理过程中出现错误');
            setDebating(false);
            setProgress(null);
            break;
        }
      } catch (err) {
        console.error('解析SSE事件错误:', err);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error);
      eventSource.close();
      setError('连接服务器失败，请重试');
      setDebating(false);
      setProgress(null);
    };
    
    // 存储EventSource实例以便清理
    return eventSource;
  }, [simulationMode, messages, speakMessage]);

  // 逐句显示消息
  const displayMessage = async (role: 'plaintiff' | 'defendant' | 'judge', content: string) => {
    // 语音模式下直接添加消息
    if (simulationMode === 'voice') {
      const currentMessages = messagesRef.current;
      const newIndex = currentMessages.length;
      
      // 更新消息列表
      const newMessages = [...currentMessages, { role, content }];
      messagesRef.current = newMessages;
      setMessages(newMessages);
      
      // 如果当前没有在播放，立即开始播放这条新消息
      if (!isPlayingRef.current && !hasPendingSpeechRef.current) {
        hasPendingSpeechRef.current = true;
        // 等待状态更新后再播放
        setTimeout(() => {
          speakMessage({ role, content }, newIndex);
          hasPendingSpeechRef.current = false;
        }, 100);
      }
      // 如果已经在播放，不要中断，让当前语音播放完成后自动播放新消息
      return;
    }
    
    // 文字模式的打字机效果
    setCurrentRole(role);
    setCurrentMessage('');
    
    // 按句子分割（中文句号、问号、感叹号）
    const sentences = content.split(/[。！？]/).filter(s => s.trim());
    let accumulatedMessage = '';
    
    for (let i = 0; i < sentences.length; i++) {
      const sentence = sentences[i];
      // 逐字显示当前句子
      for (let j = 0; j < sentence.length; j++) {
        accumulatedMessage += sentence[j];
        setCurrentMessage(accumulatedMessage);
        // 根据角色调整速度，法官发言更慢一些
        const delay = role === 'judge' ? 50 : 30;
        await new Promise(resolve => setTimeout(resolve, delay)); // 30-50ms 延迟
      }
      // 添加句子结束符
      accumulatedMessage += '。';
      setCurrentMessage(accumulatedMessage);
      // 句子之间的停顿
      await new Promise(resolve => setTimeout(resolve, 800));
    }
    
    // 显示完成后添加到消息列表
    setMessages(prev => [...prev, { role, content }]);
    setCurrentMessage('');
    setCurrentRole(null);
  };

  // 存储EventSource实例
  const eventSourceRef = useRef<EventSource | null>(null);

  // 清理SSE连接
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleDebate = async () => {
    if (!caseDescription.trim() || caseDescription.length < 20) {
      setError('请输入至少20个字符的案情描述');
      return;
    }

    setDebating(true);
    setError('');
    setMessages([]);
    setCurrentMessage('');
    setCurrentRole(null);
    setProgress(null);
    setSessionId(null);
    setCurrentVoiceIndex(0);
    setIsPlaying(false);
    
    // 停止语音
    if (speechSynthesisRef.current) {
      speechSynthesisRef.current.cancel();
    }

    // 清理之前的SSE连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      
      // 第一步：启动模拟法庭
      const response = await fetch(`${apiUrl}/api/analysis/debate/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          case_description: caseDescription,
          case_type: '民事纠纷',
          mode: simulationMode, // 传递模式参数
          user_role: simulationMode === 'voice' ? userRole : 'auto' // 传递用户角色
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`服务器错误 (${response.status}): ${errorText || '请稍后重试'}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      if (!data.session_id) {
        throw new Error('服务器未返回会话ID');
      }

      setSessionId(data.session_id);
      setProgress({
        status: 'processing',
        progress: 100,
        current_step: '模拟法庭已启动'
      });

      // 根据模式切换到不同视图
      if (simulationMode === 'voice') {
        setViewMode('courtroom');
      } else {
        // 文本模式：建立SSE连接
        eventSourceRef.current = setupSSE(data.session_id);
      }
      
    } catch (err: any) {
      console.error('辩论失败:', err);
      
      if (err.message.includes('Failed to fetch')) {
        setError(`无法连接到服务器，请确保后端服务已启动 (${process.env.NEXT_PUBLIC_API_URL || ''})`);
      } else {
        setError(err.message || '辩论模拟失败，请重试');
      }
      
      setDebating(false);
      setProgress(null);
    }
  };

  const getRoleStyle = (role: 'plaintiff' | 'defendant' | 'judge') => {
    switch (role) {
      case 'plaintiff':
        return {
          container: 'justify-start',
          bubble: 'bg-sky-50 border-sky-200 dark:bg-sky-950/20 dark:border-sky-900/50',
          label: 'text-sky-700 dark:text-sky-400',
          icon: '👨‍⚖️',
          name: '原告律师'
        };
      case 'defendant':
        return {
          container: 'justify-end',
          bubble: 'bg-blue-50 border-blue-200 dark:bg-blue-950/20 dark:border-blue-900/50',
          label: 'text-blue-700 dark:text-blue-400',
          icon: '👨‍💼',
          name: '被告律师'
        };
      case 'judge':
        return {
          container: 'justify-center',
          bubble: 'bg-sky-50 border-sky-200 dark:bg-sky-950/20 dark:border-sky-900/50',
          label: 'text-sky-700 dark:text-sky-400',
          icon: '⚖️',
          name: '法官'
        };
    }
  };

  const handleFavorite = async (content: string, role: string, index: number) => {
    try {
      if (favoritedMessages.has(index)) {
        // 取消收藏逻辑
        // 这里需要调用删除收藏的API，但是我们需要知道收藏的ID
        // 由于我们没有存储收藏ID，这里暂时只更新UI状态
        setFavoritedMessages(prev => {
          const newSet = new Set(prev);
          newSet.delete(index);
          return newSet;
        });
        await showAlert('取消收藏成功', 'success');
      } else {
        // 添加收藏
        const title = `模拟法庭收藏 - ${role === 'plaintiff' ? '原告律师' : role === 'defendant' ? '被告律师' : '法官'} ${new Date().toLocaleString('zh-CN')}`;
        await createFavorite({
          title,
          content,
          source_type: 'debate',
          source_id: sessionId || undefined
        });
        setFavoritedMessages(prev => new Set(prev).add(index));
        await showAlert('收藏成功', 'success');
      }
    } catch (error: any) {
      await showAlert('操作失败: ' + error.message, 'error');
    }
  };

  // 渲染沉浸式法庭场景
  const renderCourtroomScene = () => {
    // 如果是实时语音交互模式，使用新的VoiceCourtroom组件
    if (simulationMode === 'voice' && sessionId) {
      return (
        <div className="fixed inset-0 z-50">
          <VoiceCourtroom 
            sessionId={sessionId}
            userRole={userRole}
            caseDescription={caseDescription}
            onEnd={() => {
              setViewMode('input');
              setMessages([]);
              setDebating(false);
              setSessionId(null);
            }}
          />
        </div>
      );
    }
    
    // 原有的播放模式
    const currentMessage = messages[currentVoiceIndex];
    const currentRole = currentMessage?.role;
    
    return (
      <div className="fixed inset-0 z-50 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
        {/* 法庭背景装饰 */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-sky-500 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-blue-500 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-indigo-500 rounded-full blur-3xl"></div>
        </div>
        
        {/* 顶部标题栏 */}
        <div className="relative z-10 flex items-center justify-between px-6 py-4 bg-slate-900/80 backdrop-blur-sm border-b border-slate-700">
          <div className="flex items-center gap-3">
            <Gavel className="w-6 h-6 text-sky-500" />
            <h1 className="text-xl font-bold text-white">AI 模拟法庭</h1>
            <span className="text-sm text-slate-400">|</span>
            <span className="text-sm text-slate-400">语音庭审模式</span>
          </div>
          <button
            onClick={() => {
              stopVoice();
              setViewMode('input');
              setMessages([]);
              setIsVoiceInitialized(false);
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 text-white hover:bg-slate-600 transition-smooth"
          >
            <X size={18} />
            退出庭审
          </button>
        </div>
        
        {/* 法庭场景主体 */}
        <div className="relative z-10 flex flex-col items-center justify-center h-[calc(100vh-80px)] p-6">
          {/* 法官席 - 上方 */}
          <div className={`relative mb-16 transition-all duration-500 ${messages[currentVoiceIndex]?.role === 'judge' ? 'scale-110' : 'scale-100 opacity-70'}`}>
            <div className={`w-48 h-48 rounded-full flex flex-col items-center justify-center border-4 transition-all duration-300 ${
              messages[currentVoiceIndex]?.role === 'judge' 
                ? 'bg-sky-500/20 border-sky-500 shadow-lg shadow-sky-500/50' 
                : 'bg-slate-800 border-slate-600'
            }`}>
              <div className="w-20 h-20 rounded-full bg-sky-600 flex items-center justify-center mb-2">
                <Gavel className="w-10 h-10 text-white" />
              </div>
              <span className="text-white font-bold text-lg">法官</span>
              {messages[currentVoiceIndex]?.role === 'judge' && isPlaying && (
                <div className="absolute -bottom-2 flex gap-1">
                  <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                  <span className="w-2 h-2 bg-sky-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                </div>
              )}
            </div>
          </div>
          
          {/* 中间发言区域 */}
          <div className="w-full max-w-3xl mb-16">
            {/* 如果有正在播放的内容，显示控制和进度 */}
            {currentSpeakingText ? (
              <div className="text-center">
                {/* 进度指示器 */}
                <div className="mt-6 flex items-center justify-center gap-2">
                  {messages.map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setCurrentVoiceIndex(idx);
                        if (isPlaying) {
                          speakMessage(messages[idx], idx);
                        }
                      }}
                      className={`w-3 h-3 rounded-full transition-all duration-300 ${
                        idx === currentVoiceIndex 
                          ? 'bg-sky-500 w-8' 
                          : idx < currentVoiceIndex 
                            ? 'bg-slate-500' 
                            : 'bg-slate-700'
                      }`}
                    />
                  ))}
                </div>
                <p className="mt-2 text-slate-400 text-sm">
                  {currentVoiceIndex + 1} / {messages.length}
                </p>
              </div>
            ) : debating ? (
              <div className="text-center">
                <div className="inline-flex items-center gap-3 px-6 py-4 rounded-xl bg-slate-800/80 border border-slate-600">
                  <Loader2 className="w-6 h-6 text-sky-500 animate-spin" />
                  <span className="text-white">{progress?.current_step || '正在准备庭审...'}</span>
                </div>
                {progress && progress.progress > 0 && (
                  <div className="mt-4 w-64 mx-auto h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-sky-500 to-blue-500 transition-all duration-500" 
                      style={{ width: `${progress.progress}%` }}
                    />
                  </div>
                )}
              </div>
            ) : !isVoiceInitialized ? (
              <div className="text-center">
                <div className="inline-flex flex-col items-center gap-4 px-8 py-6 rounded-xl bg-slate-800/80 border border-slate-600">
                  <Users className="w-12 h-12 text-slate-400" />
                  <p className="text-slate-300">正在生成庭审对话内容...</p>
                </div>
              </div>
            ) : (
              <div className="text-center">
                {/* 进度指示器 */}
                <div className="mt-6 flex items-center justify-center gap-2">
                  {messages.map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setCurrentVoiceIndex(idx);
                        if (isPlaying) {
                          speakMessage(messages[idx], idx);
                        }
                      }}
                      className={`w-3 h-3 rounded-full transition-all duration-300 ${
                        idx === currentVoiceIndex 
                          ? 'bg-sky-500 w-8' 
                          : idx < currentVoiceIndex 
                            ? 'bg-slate-500' 
                            : 'bg-slate-700'
                      }`}
                    />
                  ))}
                </div>
                <p className="mt-2 text-slate-400 text-sm">
                  {currentVoiceIndex + 1} / {messages.length}
                </p>
              </div>
            )}
          </div>
          
          {/* 双方律师席 - 下方 */}
          <div className="flex items-center justify-center gap-32">
            {/* 原告席 - 左侧 */}
            <div className={`relative transition-all duration-500 ${messages[currentVoiceIndex]?.role === 'plaintiff' ? 'scale-110' : 'scale-100 opacity-70'}`}>
              <div className={`w-40 h-40 rounded-full flex flex-col items-center justify-center border-4 transition-all duration-300 ${
                messages[currentVoiceIndex]?.role === 'plaintiff' 
                  ? 'bg-blue-500/20 border-blue-500 shadow-lg shadow-blue-500/50' 
                  : 'bg-slate-800 border-slate-600'
              }`}>
                <div className="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center mb-2">
                  <span className="text-2xl">原</span>
                </div>
                <span className="text-white font-bold">原告律师</span>
                {messages[currentVoiceIndex]?.role === 'plaintiff' && isPlaying && (
                  <div className="absolute -bottom-2 flex gap-1">
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                  </div>
                )}
              </div>
            </div>
            
            {/* 播放控制 - 中间 */}
            {isVoiceInitialized && !debating && (
              <div className="flex flex-col items-center gap-4">
                <button
                  onClick={() => {
                    if (audioContext && audioContext.state === 'suspended') {
                      audioContext.resume();
                    }
                    togglePlayPause();
                  }}
                  className="w-20 h-20 rounded-full bg-gradient-to-r from-sky-500 to-blue-500 flex items-center justify-center shadow-lg shadow-sky-500/30 hover:shadow-sky-500/50 hover:scale-105 transition-all duration-300"
                >
                  {isPlaying ? (
                    <Pause className="w-10 h-10 text-white" />
                  ) : (
                    <Play className="w-10 h-10 text-white ml-1" />
                  )}
                </button>
                <div className="flex items-center gap-2">
                  <button
                    onClick={skipToNext}
                    className="p-3 rounded-full bg-slate-700 text-white hover:bg-slate-600 transition-smooth"
                  >
                    <SkipForward size={20} />
                  </button>
                  <select
                    value={voiceSpeed}
                    onChange={(e) => setVoiceSpeed(Number(e.target.value))}
                    className="px-3 py-2 rounded-full bg-slate-700 text-white text-sm border-none outline-none"
                  >
                    <option value={0.8}>0.8x</option>
                    <option value={1}>1.0x</option>
                    <option value={1.2}>1.2x</option>
                    <option value={1.5}>1.5x</option>
                  </select>
                </div>
              </div>
            )}
            
            {/* 被告席 - 右侧 */}
            <div className={`relative transition-all duration-500 ${messages[currentVoiceIndex]?.role === 'defendant' ? 'scale-110' : 'scale-100 opacity-70'}`}>
              <div className={`w-40 h-40 rounded-full flex flex-col items-center justify-center border-4 transition-all duration-300 ${
                messages[currentVoiceIndex]?.role === 'defendant' 
                  ? 'bg-indigo-500/20 border-indigo-500 shadow-lg shadow-indigo-500/50' 
                  : 'bg-slate-800 border-slate-600'
              }`}>
                <div className="w-16 h-16 rounded-full bg-indigo-600 flex items-center justify-center mb-2">
                  <span className="text-2xl">被</span>
                </div>
                <span className="text-white font-bold">被告律师</span>
                {messages[currentVoiceIndex]?.role === 'defendant' && isPlaying && (
                  <div className="absolute -bottom-2 flex gap-1">
                    <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                    <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
          
          {/* 底部实时文字显示区域 */}
      {currentSpeakingText && (
        <div className="fixed bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-slate-900 via-slate-900/95 to-transparent pt-16 pb-6 px-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-3 mb-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                messages[currentVoiceIndex]?.role === 'judge' ? 'bg-sky-500/20 text-sky-400' :
                messages[currentVoiceIndex]?.role === 'plaintiff' ? 'bg-blue-500/20 text-blue-400' :
                'bg-indigo-500/20 text-indigo-400'
              }`}>
                {messages[currentVoiceIndex]?.role === 'judge' ? '法官' : 
                 messages[currentVoiceIndex]?.role === 'plaintiff' ? '原告律师' : '被告律师'}
              </span>
              {isPlaying && (
                <span className="flex items-center gap-2 text-sm text-green-400">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  正在发言
                </span>
              )}
            </div>
            <div className="max-h-32 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800">
              <p className="text-white text-xl leading-relaxed">
                {currentSpeakingText}
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* 用户输入区域 - 轮到用户发言时显示 */}
      {isUserTurn && (
        <div className="fixed bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-slate-900 via-slate-900/95 to-transparent pt-16 pb-6 px-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-3 mb-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                userRole === 'plaintiff' ? 'bg-blue-500/20 text-blue-400' : 'bg-indigo-500/20 text-indigo-400'
              }`}>
                {userRole === 'plaintiff' ? '原告律师 (你)' : '被告律师 (你)'}
              </span>
              <span className="flex items-center gap-2 text-sm text-purple-400">
                <span className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
                轮到你发言
              </span>
            </div>
            <div className="bg-slate-800/80 border border-slate-600 rounded-lg p-4">
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder={`请输入你的${userRole === 'plaintiff' ? '原告' : '被告'}陈述...`}
                className="w-full h-32 resize-none bg-slate-700 border border-slate-600 rounded-lg p-3 text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <div className="mt-3 flex items-center gap-3">
                <button
                  onClick={() => {
                    // 开始录音
                    navigator.mediaDevices.getUserMedia({ audio: true })
                      .then(stream => {
                        const mediaRecorder = new MediaRecorder(stream);
                        mediaRecorderRef.current = mediaRecorder;
                        audioChunksRef.current = [];
                        mediaRecorder.start();
                        setIsRecording(true);
                        
                        mediaRecorder.ondataavailable = (e) => {
                          if (e.data.size > 0) {
                            audioChunksRef.current.push(e.data);
                          }
                        };
                      })
                      .catch(err => {
                        console.error('无法访问麦克风:', err);
                      });
                  }}
                  disabled={isRecording}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Mic size={16} />
                  {isRecording ? '录音中...' : '开始录音'}
                </button>
                {isRecording && (
                  <button
                    onClick={() => {
                      // 停止录音
                      if (mediaRecorderRef.current) {
                        mediaRecorderRef.current.stop();
                        mediaRecorderRef.current = null;
                        setIsRecording(false);
                        // 这里可以处理录音文件
                      }
                    }}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-700 text-white transition-smooth"
                  >
                    <MicOff size={16} />
                    停止录音
                  </button>
                )}
                <button
                  onClick={() => {
                    // 提交用户输入
                    if (userInput.trim()) {
                      // 发送用户输入到服务器
                      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
                      fetch(`${apiUrl}/api/analysis/debate/user-input`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                          session_id: sessionId,
                          user_role: userRole,
                          content: userInput
                        }),
                      })
                      .then(response => response.json())
                      .then(data => {
                        if (data.success) {
                          // 清空输入
                          setUserInput('');
                          setIsUserTurn(false);
                        }
                      })
                      .catch(err => {
                        console.error('发送用户输入失败:', err);
                      });
                    }
                  }}
                  disabled={!userInput.trim()}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send size={16} />
                  提交发言
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground relative overflow-hidden">
      {/* 星空光晕效果 */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      {/* 沉浸式法庭场景 - 全屏覆盖 */}
      {viewMode === 'courtroom' && renderCourtroomScene()}
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-400 text-sm font-medium mb-2">
              <Gavel size={16} />
              AI 模拟法庭
            </div>
            <h1 className="text-3xl font-bold text-sky-800 dark:text-sky-300">
              多维抗辩推演
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              预判争议焦点与裁判逻辑，提供专业法律参考
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/history')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 text-white font-medium shadow-md hover:shadow-lg transition-all hover:scale-105"
            >
              <History size={16} />
              历史记录
            </button>
            <button
              onClick={() => router.push('/settings')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-medium shadow-md hover:shadow-lg transition-all hover:scale-105"
            >
              <Settings size={16} />
              设置
            </button>
          </div>
        </div>

      {/* 输入区域 */}
      {viewMode === 'input' && (
        <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl shadow-xl border border-sky-200 dark:border-sky-900/30 p-8 mb-8">
          <h2 className="mb-6 flex items-center gap-3 text-2xl font-bold text-sky-800 dark:text-sky-300">
            <ScaleIcon size={24} className="text-red-600" />
            案情描述
          </h2>

          <textarea
            value={caseDescription}
            onChange={(e) => setCaseDescription(e.target.value)}
            placeholder="请详细描述案件情况，包括双方争议焦点、关键事实和证据..."
            className="h-48 w-full resize-none rounded-lg border border-sky-300 dark:border-sky-700 bg-sky-50/50 dark:bg-gray-800 p-4 text-gray-800 dark:text-gray-200 placeholder:text-gray-500 dark:placeholder:text-gray-400 transition-all focus:ring-2 focus:ring-amber-500 focus:border-sky-500"
          />

          {/* 模拟模式选择 */}
          <div className="mt-6 mb-6">
            <p className="mb-3 text-sm font-medium text-sky-800 dark:text-sky-400">选择模拟模式：</p>
            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => setSimulationMode('text')}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg border-2 transition-all ${
                  simulationMode === 'text' 
                    ? 'border-sky-500 bg-sky-50 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 shadow-md' 
                    : 'border-sky-200 dark:border-sky-800 hover:border-sky-400 dark:hover:border-sky-600 hover:bg-sky-50 dark:hover:bg-sky-900/20'
                }`}
              >
                <MessageSquare size={18} />
                <span className="font-medium">对话形式</span>
              </button>
              <button
                onClick={() => setSimulationMode('voice')}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg border-2 transition-all ${
                  simulationMode === 'voice' 
                    ? 'border-red-500 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 shadow-md' 
                    : 'border-sky-200 dark:border-sky-800 hover:border-sky-400 dark:hover:border-sky-600 hover:bg-sky-50 dark:hover:bg-sky-900/20'
                }`}
              >
                <Volume2 size={18} />
                <span className="font-medium">语音形式</span>
              </button>
            </div>
            <p className="mt-3 text-xs text-gray-600 dark:text-gray-400">
              {simulationMode === 'text' 
                ? '对话形式：以文字对话方式展示原告、被告、法官三方的辩论过程' 
                : '语音形式：进入沉浸式法庭场景，三方角色语音对话'}
            </p>
            
            {/* 语音模式角色选择 */}
            {simulationMode === 'voice' && (
              <div className="mt-6 space-y-4">
                <p className="text-sm font-medium text-sky-800 dark:text-sky-400">参与方式：</p>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <button
                    onClick={() => setUserRole('auto')}
                    className={`flex items-center gap-2 px-5 py-3 rounded-lg border-2 transition-all ${
                      userRole === 'auto' 
                        ? 'border-sky-500 bg-sky-50 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 shadow-md' 
                        : 'border-sky-200 dark:border-sky-800 hover:border-sky-400 dark:hover:border-sky-600 hover:bg-sky-50 dark:hover:bg-sky-900/20'
                    }`}
                  >
                    <Bot size={16} />
                    <span className="font-medium">自动模拟</span>
                  </button>
                  <button
                    onClick={() => setUserRole('plaintiff')}
                    className={`flex items-center gap-2 px-5 py-3 rounded-lg border-2 transition-all ${
                      userRole === 'plaintiff' 
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 shadow-md' 
                        : 'border-sky-200 dark:border-sky-800 hover:border-sky-400 dark:hover:border-sky-600 hover:bg-sky-50 dark:hover:bg-sky-900/20'
                    }`}
                  >
                    <User size={16} />
                    <span className="font-medium">我是原告</span>
                  </button>
                  <button
                    onClick={() => setUserRole('defendant')}
                    className={`flex items-center gap-2 px-5 py-3 rounded-lg border-2 transition-all ${
                      userRole === 'defendant' 
                        ? 'border-red-500 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 shadow-md' 
                        : 'border-sky-200 dark:border-sky-800 hover:border-sky-400 dark:hover:border-sky-600 hover:bg-sky-50 dark:hover:bg-sky-900/20'
                    }`}
                  >
                    <User size={16} />
                    <span className="font-medium">我是被告</span>
                  </button>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {userRole === 'auto' ? '系统自动模拟三方对话' : 
                   userRole === 'plaintiff' ? '你作为原告，被告由AI扮演' : 
                   '你作为被告，原告由AI扮演'}
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {caseDescription.length} / 建议至少 100 字符
            </span>
            <button
              onClick={handleDebate}
              disabled={caseDescription.length < 20}
              className="w-full sm:w-auto rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 text-white font-medium py-3 px-8 shadow-lg transition-all hover:shadow-xl hover:scale-105 disabled:cursor-not-allowed disabled:opacity-50 disabled:scale-100"
            >
              {simulationMode === 'text' ? '🎭 开始模拟庭审' : '🔊 开始语音庭审'}
            </button>
          </div>

          {/* 示例案例 */}
          <div className="mt-8 border-t border-sky-200 dark:border-sky-900/30 pt-6">
            <p className="mb-4 text-sm font-medium text-sky-800 dark:text-sky-400">快速填充示例案例：</p>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {exampleCases.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setCaseDescription(example)}
                  className="bg-sky-50 dark:bg-gray-800 border border-sky-200 dark:border-sky-800 rounded-lg p-4 text-left text-sm transition-all hover:bg-sky-100 dark:hover:bg-gray-700 hover:shadow-md"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-r from-sky-500 to-indigo-500 flex items-center justify-center text-white text-xs font-bold">
                      {index + 1}
                    </div>
                    <span className="font-medium text-sky-800 dark:text-sky-300">案例 {index + 1}</span>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 line-clamp-3">{example.substring(0, 80)}...</p>
                </button>
              ))}
            </div>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mt-6 flex items-start gap-3 rounded-lg border border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-900/30 p-4">
              <AlertCircle size={20} className="mt-0.5 flex-shrink-0 text-red-600 dark:text-red-400" />
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}
        </div>
      )}

      {/* 对话模式结果展示 */}
      {simulationMode === 'text' && (debating || messages.length > 0) && (
        <div className="space-y-8">
          {/* 辩论进行中提示 */}
          {debating && progress && (
            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl shadow-lg border border-sky-200 dark:border-sky-900/30 p-6">
              <div className="flex items-center gap-4">
                <Loader2 size={28} className="animate-spin text-sky-500" />
                <div className="flex-1">
                  <p className="font-medium text-sky-800 dark:text-sky-300">AI 法庭正在模拟辩论...</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{progress.current_step}</p>
                  {/* 进度条 */}
                  <div className="mt-4 h-3 w-full rounded-full bg-sky-100 dark:bg-gray-700 overflow-hidden">
                    <div 
                      className="h-full rounded-full bg-gradient-to-r from-sky-500 to-indigo-500 transition-all duration-1000 ease-out"
                      style={{ width: `${progress.progress}%` }}
                    />
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <p className="text-xs text-gray-600 dark:text-gray-400">辩论进度</p>
                    <p className="text-xs font-medium text-sky-800 dark:text-sky-300">{progress.progress}%</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 消息气泡流 */}
          <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl shadow-lg border border-sky-200 dark:border-sky-900/30 p-6">
            <div className="space-y-6">
              {messages.map((message, index) => {
                const style = getRoleStyle(message.role);
                return (
                  <div key={index} className={`flex ${style.container} animate-fadeIn`}>
                    <div className={`max-w-[80%] rounded-lg border p-5 ${style.bubble}`}>
                      <div className="mb-3 flex items-center gap-3">
                        <span className="text-2xl">{style.icon}</span>
                        <span className={`font-semibold ${style.label}`}>{style.name}</span>
                      </div>
                      <div className="prose prose-sm dark:prose-invert max-w-none text-gray-800 dark:text-gray-200">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                    <button
                      onClick={() => handleFavorite(message.content, message.role, index)}
                      className={`ml-2 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-colors ${
                        favoritedMessages.has(index)
                          ? 'bg-sky-500/20 hover:bg-sky-500/30'
                          : 'bg-sky-100 dark:bg-sky-900/30 hover:bg-sky-200 dark:hover:bg-sky-800/50'
                      }`}
                      title={favoritedMessages.has(index) ? "取消收藏" : "收藏"}
                    >
                      <Star 
                        size={16} 
                        className={`transition-colors ${
                          favoritedMessages.has(index)
                            ? 'text-sky-500 dark:text-sky-400 fill-sky-500 dark:fill-sky-400'
                            : 'text-sky-600 dark:text-sky-400'
                        }`} 
                      />
                    </button>
                  </div>
                );
              })}

              {/* 当前正在输入的消息（打字机效果） */}
              {currentRole && currentMessage && (
                <div className={`flex ${getRoleStyle(currentRole).container} animate-fadeIn`}>
                  <div className={`max-w-[80%] rounded-lg border p-5 ${getRoleStyle(currentRole).bubble}`}>
                    <div className="mb-3 flex items-center gap-3">
                      <span className="text-2xl">{getRoleStyle(currentRole).icon}</span>
                      <span className={`font-semibold ${getRoleStyle(currentRole).label}`}>{getRoleStyle(currentRole).name}</span>
                    </div>
                    <div className="prose prose-sm dark:prose-invert max-w-none text-gray-800 dark:text-gray-200">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {currentMessage}
                      </ReactMarkdown>
                      <span className="inline-block h-4 w-1 animate-pulse bg-current" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 重新模拟按钮 */}
          {!debating && messages.length > 0 && (
            <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
              <button
                onClick={() => {
                  setMessages([]);
                  setCaseDescription('');
                  setError('');
                  stopVoice();
                }}
                className="flex-1 sm:flex-none w-full sm:w-auto rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 text-white font-medium py-3 px-8 shadow-lg transition-all hover:shadow-xl hover:scale-105"
              >
                🔄 重新模拟
              </button>
              <button
                onClick={async () => {
                  const caseInfo = {
                    case_title: caseDescription.substring(0, 20) || '民事案件',
                    case_description: caseDescription,
                    case_type: '民事纠纷',
                    debate_turns: messages,
                    verdict: messages.find(m => m.role === 'judge')?.content
                  };
                  await generateComplaintPDF(caseInfo);
                }}
                className="flex-1 sm:flex-none flex items-center justify-center gap-2 w-full sm:w-auto rounded-lg border-2 border-sky-500 text-sky-700 dark:text-sky-300 font-medium py-3 px-8 shadow-md transition-all hover:bg-sky-50 dark:hover:bg-sky-900/20 hover:shadow-lg"
              >
                <FileText size={20} />
                📄 生成起诉状PDF
              </button>
            </div>
          )}
        </div>
      )}
      </main>
    </div>
  );
}