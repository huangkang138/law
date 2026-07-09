'use client';

import { useState, useRef, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { 
  FileText, 
  Upload, 
  Mic, 
  FileAudio, 
  Video, 
  Camera, 
  Type,
  Send,
  Sparkles,
  Shield,
  Zap,
  AlertCircle,
  CheckCircle,
  X,
  Loader2,
  Scale,
  Target,
  Lightbulb,
  Star,
  ChevronRight,
  FileCheck,
  Clock,
  MapPin,
  Users,
  Briefcase,
  Settings,
  Trash2,
  Pin,
  Edit,
  MoreHorizontal,
  DollarSign,
  MessageSquare,
  AlertTriangle,
  Plus
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { organizeDispute, organizeDisputeWithFiles } from '@/lib/api';
import { useDisputeStore } from '@/store/disputeStore';
import Link from 'next/link';

interface OrganizedData {
  title?: string;
  parties?: { name: string; role: string; contact?: string }[];
  event_time?: string;
  event_description?: string;
  demands?: string;
  evidence_list?: { name: string; type: string; description: string }[];
}

function DisputeOrganizePageContent() {
  const { currentSessionId, sessions, createSession, deleteSession, renameSession, togglePin, setCurrentSession, setOrganizedData: setStoreOrganizedData, getSortedSessions } = useDisputeStore();
  const [inputType, setInputType] = useState<'text' | 'voice' | 'audio' | 'video' | 'image'>('text');
  const [inputContent, setInputContent] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isInputActive, setIsInputActive] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [organizedData, setOrganizedData] = useState<OrganizedData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [useAlternativeMode, setUseAlternativeMode] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isRealtimeTranscribing, setIsRealtimeTranscribing] = useState(false);
  const [realtimeTranscript, setRealtimeTranscript] = useState('');
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const lastFinalTranscriptRef = useRef('');

  useEffect(() => {
    if (currentSessionId) {
      const currentSession = sessions.find(s => s.id === currentSessionId);
      if (currentSession?.organizedData) {
        setOrganizedData(currentSession.organizedData);
      }
    } else {
      setOrganizedData(null);
    }
  }, [currentSessionId, sessions]);

  useEffect(() => {
    if (isRecording) {
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    }
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, [isRecording]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startSpeechRecognition = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('浏览器不支持语音识别');
      return false;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'zh-CN';
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
          setInputContent(lastFinalTranscriptRef.current);
          setRealtimeTranscript(lastFinalTranscriptRef.current);
        } else if (interimTranscript) {
          setRealtimeTranscript(lastFinalTranscriptRef.current + interimTranscript);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('语音识别错误:', event.error);
        if (event.error === 'not-allowed') {
          setError('无法访问麦克风，请检查权限设置');
        }
      };

      recognition.onend = () => {
        if (isRealtimeTranscribing && !useAlternativeMode) {
          try {
            recognition.start();
          } catch (e) {
            console.warn('重新启动语音识别失败:', e);
          }
        }
      };

      recognition.start();
      recognitionRef.current = recognition;
      return true;
    } catch (error) {
      console.error('启动语音识别失败:', error);
      return false;
    }
  };

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
  };

  const startRecording = async () => {
    try {
      lastFinalTranscriptRef.current = '';
      setRealtimeTranscript('');
      
      if (!useAlternativeMode) {
        const success = startSpeechRecognition();
        if (!success) {
          setError('浏览器不支持实时语音识别，请切换到备用模式');
          return;
        }
        setIsRealtimeTranscribing(true);
        setIsRecording(true);
        setRecordingTime(0);
      } else {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          setAudioBlob(audioBlob);
          stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        setIsRecording(true);
        setRecordingTime(0);
      }
    } catch (error) {
      console.error('启动录音失败:', error);
      setError('无法访问麦克风，请检查权限设置');
    }
  };

  const stopRecording = () => {
    if (useAlternativeMode && mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    } else {
      stopSpeechRecognition();
      setIsRealtimeTranscribing(false);
    }
    setIsRecording(false);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      setUploadedFiles(prev => [...prev, ...Array.from(files)]);
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleAnalyze = async () => {
    if (!inputContent.trim() && uploadedFiles.length === 0 && !audioBlob) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      let result;
      if (uploadedFiles.length > 0) {
        const formData = new FormData();
        formData.append('input_content', inputContent);
        formData.append('input_type', inputType);
        uploadedFiles.forEach((file, index) => {
          formData.append(`files`, file);
        });
        result = await organizeDisputeWithFiles(formData);
      } else if (audioBlob) {
        const formData = new FormData();
        formData.append('input_content', inputContent);
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('input_type', 'audio');
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/dispute/organize-with-files`, {
          method: 'POST',
          body: formData,
        });
        result = await response.json();
      } else {
        result = await organizeDispute({ input_content: inputContent, input_type: inputType });
      }

      if (result.success) {
        const sessionId = currentSessionId || createSession(inputContent.substring(0, 30) + '...');
        setOrganizedData(result.organized_data);
        setStoreOrganizedData(sessionId, result.organized_data);
      } else {
        setError(result.error || '整理失败');
      }
    } catch (err: any) {
      setError(err.message || '网络错误');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setInputContent('');
    setUploadedFiles([]);
    setAudioBlob(null);
    setOrganizedData(null);
    setError(null);
    setRecordingTime(0);
    setRealtimeTranscript('');
    lastFinalTranscriptRef.current = '';
    setCurrentSession(null);
    setIsInputActive(false);
  };

  const handleInputTypeChange = (type: 'text' | 'voice' | 'audio' | 'video' | 'image') => {
    setInputType(type);
    // 清空相关内容
    setInputContent('');
    setUploadedFiles([]);
    setAudioBlob(null);
    setOrganizedData(null);
    setError(null);
    setRecordingTime(0);
    setRealtimeTranscript('');
    lastFinalTranscriptRef.current = '';
  };

  const handleNewSession = () => {
    handleReset();
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    const session = sessions.find(s => s.id === sessionId);
    if (session?.disputeId) {
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/dispute/${session.disputeId}`, {
          method: 'DELETE',
        });
      } catch (err) {
        console.error('删除纠纷失败:', err);
      }
    }
    deleteSession(sessionId);
    if (currentSessionId === sessionId) {
      setOrganizedData(null);
    }
  };

  const handleTogglePin = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    togglePin(sessionId);
    setActiveMenuId(null);
  };

  const handleEditSession = (e: React.MouseEvent, session: any) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitle(session.customTitle || session.title);
    setActiveMenuId(null);
  };

  const handleSaveEdit = () => {
    if (editingSessionId && editTitle.trim()) {
      renameSession(editingSessionId, editTitle.trim());
      setEditingSessionId(null);
      setEditTitle('');
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditTitle('');
  };

  const handleToggleMenu = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setActiveMenuId(activeMenuId === sessionId ? null : sessionId);
  };

  useEffect(() => {
    const handleClickOutside = () => {
      setActiveMenuId(null);
    };

    if (activeMenuId) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [activeMenuId]);

  const handleSwitchSession = (sessionId: string) => {
    setCurrentSession(sessionId);
    const session = sessions.find(s => s.id === sessionId);
    if (session?.organizedData) {
      setOrganizedData(session.organizedData);
    }
  };

  const inputTypes = [
    { type: 'text', icon: Type, label: '文字' },
    { type: 'voice', icon: Mic, label: '语音' },
    { type: 'audio', icon: FileAudio, label: '音频' },
    { type: 'video', icon: Video, label: '视频' },
    { type: 'image', icon: Camera, label: '图片' },
  ] as const;

  const sortedSessions = getSortedSessions();

  return (
    <div className="fixed top-20 left-0 right-0 bottom-0 bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground flex">
      {/* 左侧边栏 - 纠纷记录 */}
      <div className="relative z-10 w-64 h-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-r border-sky-200 dark:border-sky-900/30 flex flex-col flex-shrink-0 overflow-hidden">
        <div className="p-4 border-b border-sky-200 dark:border-sky-900/30">
          <button
            onClick={handleNewSession}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-xl font-medium hover:from-sky-600 hover:to-blue-700 transition-all shadow-lg"
          >
            <Plus size={18} />
            新建纠纷整理
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
          {sortedSessions.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              <FileText size={32} className="mx-auto mb-2 opacity-50" />
              <p className="text-sm">暂无纠纷记录</p>
            </div>
          ) : (
            <div className="space-y-1">
              {sortedSessions.map((session) => (
                <div
                  key={session.id}
                  className="relative"
                >
                  <div
                    onClick={() => handleSwitchSession(session.id)}
                    className={`group flex items-center gap-2 p-3 rounded-xl cursor-pointer transition-all ${
                      currentSessionId === session.id
                        ? 'bg-sky-100 dark:bg-sky-900/30 border border-sky-300 dark:border-sky-700'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent'
                    }`}
                  >
                    <FileText size={16} className="text-gray-500 dark:text-gray-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                        {session.customTitle || session.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(session.updatedAt).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => handleToggleMenu(e, session.id)}
                        className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        title="更多操作"
                      >
                        <MoreHorizontal size={14} />
                      </button>
                    </div>
                  </div>

                  {activeMenuId === session.id && (
                    <div className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 min-w-[120px]">
                      <button
                        onClick={(e) => handleTogglePin(e, session.id)}
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                      >
                        <Pin size={14} className={session.isPinned ? 'text-sky-500 fill-current' : ''} />
                        {session.isPinned ? '取消置顶' : '置顶'}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditSession(e, session);
                        }}
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                      >
                        <Edit size={14} />
                        编辑
                      </button>
                      <button
                        onClick={(e) => handleDeleteSession(e, session.id)}
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-red-500"
                      >
                        <Trash2 size={14} />
                        删除
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 设置按钮 */}
        <div className="p-3 border-t border-sky-200 dark:border-sky-900/30 flex-shrink-0">
          <Link
            href="/settings"
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Settings size={18} />
            <span className="text-sm font-medium">设置</span>
          </Link>
        </div>
      </div>

      {/* 右侧内容区域 */}
      <div className="relative z-10 flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <div className="flex-1 w-full overflow-y-auto overflow-x-hidden">
          <div className="w-full mx-auto px-4 pt-4 pb-4 h-full flex flex-col">
            {/* 页面标题 */}
            <div className="text-center mb-4">
              <h1 className="text-2xl font-bold text-sky-700 dark:text-sky-300 mb-1">纠纷整理</h1>
              <p className="text-sm text-gray-700 dark:text-gray-300">智能整理纠纷信息，提取关键要素</p>
              <div className="h-1 w-24 bg-gradient-to-r from-amber-500 to-orange-500 mx-auto rounded-full mt-2" />
            </div>

            {/* 功能标签 */}
            <div className="mb-4 flex flex-wrap items-center justify-center gap-2">
              <div className="flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Sparkles size={14} className="text-sky-600 dark:text-sky-400" />
                <span className="text-xs text-sky-800 dark:text-sky-300">智能分析</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Shield size={14} className="text-red-600 dark:text-red-400" />
                <span className="text-xs text-red-800 dark:text-red-300">证据提取</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 backdrop-blur-sm">
                <Zap size={14} className="text-sky-600 dark:text-sky-400" />
                <span className="text-xs text-sky-800 dark:text-sky-300">快速整理</span>
              </div>
            </div>

            {/* 空状态 */}
            {!currentSessionId && !isInputActive && uploadedFiles.length === 0 && !audioBlob && !organizedData && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="mb-6 relative inline-block">
                    <div className="absolute inset-0 rounded-full bg-gradient-to-br from-sky-600/30 via-amber-600/30 to-red-600/30 blur-2xl animate-pulse-slow" />
                    <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-orange-600 shadow-2xl border-2 border-sky-400 mx-auto">
                      <Scale size={40} className="text-white" />
                    </div>
                  </div>
                  <h2 className="mb-3 text-2xl font-bold text-sky-800 dark:text-sky-300">开始新的纠纷整理</h2>
                  <p className="mb-6 text-center text-gray-700 dark:text-gray-300 max-w-md">
                    输入纠纷描述，AI 将为您智能整理关键信息
                  </p>
                  <button
                      onClick={() => setIsInputActive(true)}
                      className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-amber-600 to-orange-600 px-6 py-2 text-white font-medium shadow-lg hover:shadow-xl hover:shadow-amber-500/30 transition-all border border-sky-400/50"
                    >
                      <Plus size={18} />
                      开始整理
                    </button>
                </div>
              </div>
            )}

            {/* 主内容区域 - 上下布局 */}
            {(currentSessionId || isInputActive || inputContent || uploadedFiles.length > 0 || audioBlob || organizedData) && (
              <div className="flex-1 flex flex-col gap-4 min-h-0">
                {/* 上半部分 - 输入区域 */}
                <div className="h-[50%] flex flex-col">
                  <div className="flex-1 rounded-2xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 p-3 backdrop-blur-sm flex flex-col overflow-hidden">
                    {/* 输入类型选择 */}
                    <div className="flex items-center gap-1.5 mb-3 flex-shrink-0 flex-wrap">
                      {inputTypes.map(({ type, icon: Icon, label }) => (
                        <button
                          key={type}
                          onClick={() => handleInputTypeChange(type)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-medium transition-all ${
                            inputType === type
                              ? 'bg-sky-500 text-white'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                          }`}
                        >
                          <Icon size={16} />
                          {label}
                        </button>
                      ))}
                    </div>

                    {/* 输入内容区域 */}
                    <div className="flex-1 overflow-y-auto">
                      {inputType === 'text' && (
                        <textarea
                          value={inputContent}
                          onChange={(e) => setInputContent(e.target.value)}
                          placeholder="请详细描述您的纠纷情况...&#10;&#10;例如：&#10;• 纠纷涉及的人员：张三、李四&#10;• 发生时间：2024年1月15日&#10;• 事件经过：张三向李四借款10万元，约定2024年6月15日还款，但到期后张三未还款&#10;• 您的诉求：要求张三归还借款本金及利息&#10;• 证据材料：借条、转账记录、聊天记录"
                          className="w-full h-full p-4 bg-white/80 dark:bg-gray-900/80 border-2 border-sky-500/20 rounded-xl text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-sky-400/50 resize-none text-sm leading-relaxed"
                        />
                      )}

                      {inputType === 'voice' && (
                        <div className="flex h-full gap-4">
                          {/* 左侧录音控制区域 */}
                          <div className="w-1/3 flex flex-col items-center justify-center">
                            {!isRecording && !audioBlob && (
                              <button onClick={startRecording} className="group relative flex flex-col items-center gap-2">
                                <div className="relative">
                                  <div className="absolute inset-0 bg-red-500/30 rounded-full animate-ping" />
                                  <div className="relative flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-sky-500 to-indigo-600 shadow-lg group-hover:scale-110 transition-transform">
                                    <Mic size={24} className="text-white" />
                                  </div>
                                </div>
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">点击开始录音</span>
                              </button>
                            )}

                            {isRecording && (
                              <div className="flex flex-col items-center gap-3">
                                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-red-500 animate-pulse">
                                  <Mic size={24} className="text-white" />
                                </div>
                                <button onClick={stopRecording} className="px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-full text-sm">
                                  停止录音
                                </button>
                              </div>
                            )}

                            {audioBlob && !isRecording && (
                              <div className="flex flex-col items-center gap-3">
                                <CheckCircle size={36} className="text-green-500" />
                                <span className="text-sm text-green-600 dark:text-green-400">录音完成</span>
                                <audio src={URL.createObjectURL(audioBlob)} controls className="w-full" />
                                <button onClick={() => { setAudioBlob(null); setRecordingTime(0); }} className="text-sm text-gray-500 hover:text-gray-700">
                                  重新录制
                                </button>
                              </div>
                            )}
                          </div>
                          
                          {/* 右侧语音输入内容显示区域 */}
                          <div className="flex-1 p-4 bg-white/80 dark:bg-gray-900/80 border-2 border-sky-500/20 rounded-xl text-gray-800 dark:text-gray-200 text-base leading-relaxed overflow-y-auto">
                            {realtimeTranscript || (
                              <div className="text-gray-400 dark:text-gray-600 italic">
                                {isRecording ? '正在识别语音...' : '语音输入内容将显示在这里'}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {(inputType === 'audio' || inputType === 'video' || inputType === 'image') && (
                        <div className="flex h-full gap-4">
                          {/* 左侧上传控制区域 */}
                          <div className="w-1/3 flex flex-col items-center justify-center">
                            <div
                              onClick={() => fileInputRef.current?.click()}
                              className="border-2 border-dashed border-sky-500/30 rounded-xl p-4 text-center cursor-pointer hover:border-sky-500/50 hover:bg-sky-500/5 transition-all w-full flex flex-col items-center justify-center"
                            >
                              <Upload size={32} className="mx-auto text-sky-500/50 mb-2" />
                              <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">点击或拖拽文件上传</p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                                {inputType === 'audio' && '支持 MP3, WAV, M4A'}
                                {inputType === 'video' && '支持 MP4, AVI, MOV'}
                                {inputType === 'image' && '支持 JPG, PNG, GIF'}
                              </p>
                              <input
                                ref={fileInputRef}
                                type="file"
                                accept={inputType === 'audio' ? 'audio/*' : inputType === 'video' ? 'video/*' : 'image/*'}
                                multiple
                                onChange={handleFileUpload}
                                className="hidden"
                              />
                            </div>
                          </div>
                          
                          {/* 右侧上传内容显示区域 */}
                          <div className="flex-1 p-4 bg-white/80 dark:bg-gray-900/80 border-2 border-sky-500/20 rounded-xl text-gray-800 dark:text-gray-200 text-base leading-relaxed overflow-y-auto">
                            {uploadedFiles.length > 0 ? (
                              <div className="space-y-3">
                                {uploadedFiles.map((file, index) => (
                                  <div key={index} className="flex items-center justify-between p-2 bg-white/50 dark:bg-gray-700/50 rounded-lg border border-sky-500/20">
                                    <span className="text-sm text-gray-800 dark:text-gray-200 truncate">{file.name}</span>
                                    <button onClick={() => removeFile(index)} className="text-red-500 hover:text-red-600">
                                      <X size={16} />
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-gray-400 dark:text-gray-600 italic">
                                上传的文件将显示在这里
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-sky-500/20 flex-shrink-0">
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {inputContent.length} 字
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleReset}
                          className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                        >
                          重置
                        </button>
                        <button
                          onClick={handleAnalyze}
                          disabled={isAnalyzing || (!inputContent.trim() && uploadedFiles.length === 0 && !audioBlob)}
                          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-xl text-sm font-medium hover:from-sky-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                          {isAnalyzing ? (
                            <>
                              <Loader2 size={16} className="animate-spin" />
                              分析中...
                            </>
                          ) : (
                            <>
                              <Sparkles size={16} />
                              开始整理
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 下半部分 - 结果显示区域 */}
                <div className="h-1/2 flex flex-col">
                  <div className="flex-1 rounded-2xl border border-sky-500/30 bg-white/80 dark:bg-gray-800/80 p-4 backdrop-blur-sm flex flex-col overflow-hidden">
                    <div className="flex items-center justify-between mb-4 flex-shrink-0">
                      <h2 className="text-lg font-semibold text-sky-700 dark:text-sky-300">整理结果</h2>
                      {organizedData && (
                        <button
                          onClick={handleReset}
                          className="text-sm text-sky-600 hover:text-sky-700"
                        >
                          重新整理
                        </button>
                      )}
                    </div>

                    <div className="flex-1 overflow-y-auto">
                      {error && (
                        <div className="p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-xl flex items-center gap-3 text-red-700 dark:text-red-300 mb-4">
                          <AlertCircle size={20} />
                          <span>{error}</span>
                        </div>
                      )}

                      {!organizedData && !error && (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
                          <FileText size={48} className="mb-3 opacity-50" />
                          <p>整理结果将在此显示</p>
                        </div>
                      )}

                      {organizedData && (
                        <div className="space-y-4">
                          {organizedData.title && (
                            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                              <div className="flex items-center gap-2 mb-2">
                                <Scale size={16} className="text-sky-500" />
                                <h3 className="font-medium text-gray-800 dark:text-gray-200">纠纷标题</h3>
                              </div>
                              <p className="text-sm text-gray-700 dark:text-gray-300">{organizedData.title}</p>
                            </div>
                          )}

                          {organizedData.parties && organizedData.parties.length > 0 && (
                            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                              <div className="flex items-center gap-2 mb-2">
                                <Users size={16} className="text-blue-500" />
                                <h3 className="font-medium text-gray-800 dark:text-gray-200">当事人信息</h3>
                              </div>
                              <div className="space-y-2">
                                {organizedData.parties.map((party, index) => (
                                  <div key={index} className="flex items-center gap-4 p-2 bg-white/50 dark:bg-gray-700/50 rounded-lg">
                                    <div>
                                      <p className="font-medium text-gray-800 dark:text-gray-200">{party.name}</p>
                                      <p className="text-xs text-gray-500 dark:text-gray-400">{party.role}</p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {organizedData.event_time && (
                            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                              <div className="flex items-center gap-2 mb-2">
                                <Clock size={16} className="text-green-500" />
                                <h3 className="font-medium text-gray-800 dark:text-gray-200">事件时间</h3>
                              </div>
                              <p className="text-sm text-gray-700 dark:text-gray-300">{organizedData.event_time}</p>
                            </div>
                          )}

                          {organizedData.event_description && (
                            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                              <div className="flex items-center gap-2 mb-2">
                                <Target size={16} className="text-purple-500" />
                                <h3 className="font-medium text-gray-800 dark:text-gray-200">事件描述</h3>
                              </div>
                              <div className="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {organizedData.event_description}
                                </ReactMarkdown>
                              </div>
                            </div>
                          )}

                          {organizedData.demands && (
                            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                              <div className="flex items-center gap-2 mb-2">
                                <Star size={16} className="text-yellow-500" />
                                <h3 className="font-medium text-gray-800 dark:text-gray-200">诉求</h3>
                              </div>
                              <div className="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {organizedData.demands}
                                </ReactMarkdown>
                              </div>
                            </div>
                          )}

                          {organizedData.evidence_list && organizedData.evidence_list.length > 0 && (
                            <div className="p-4 bg-white/50 dark:bg-gray-700/50 rounded-xl border border-sky-500/20">
                              <div className="flex items-center gap-2 mb-2">
                                <FileCheck size={16} className="text-orange-500" />
                                <h3 className="font-medium text-gray-800 dark:text-gray-200">证据清单</h3>
                              </div>
                              <div className="space-y-2">
                                {organizedData.evidence_list.map((evidence, index) => (
                                  <div key={index} className="p-2 bg-white/50 dark:bg-gray-700/50 rounded-lg">
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="font-medium text-gray-800 dark:text-gray-200">{evidence.name}</span>
                                      <span className="text-xs px-2 py-0.5 bg-sky-500/20 text-sky-600 dark:text-sky-400 rounded-full">{evidence.type}</span>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">{evidence.description}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {editingSessionId && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div 
            className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">重命名会话</h3>
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSaveEdit();
                  } else if (e.key === 'Escape') {
                    handleCancelEdit();
                  }
                }}
                placeholder="输入新的会话名称"
                className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                autoFocus
              />
            </div>
            <div className="flex gap-3 px-6 pb-6">
              <button
                onClick={handleCancelEdit}
                className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={!editTitle.trim()}
                className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-br from-amber-600 to-orange-600 text-white hover:shadow-lg hover:shadow-amber-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-sky-400/50"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default dynamic(() => Promise.resolve(DisputeOrganizePageContent), {
  ssr: false,
});
