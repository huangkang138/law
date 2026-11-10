'use client';

import { useState, useEffect, useRef } from 'react';
import { Bot, Home, FileText, X, ChevronLeft, ChevronRight, ArrowRight, GitMerge, GitBranch, ThumbsUp } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Agent {
  id: string;
  name: string;
  description: string;
  avatar: string;
  agent_type: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  is_preset: boolean;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface AgentNode {
  agent: Agent;
  id: string;
  position: { x: number; y: number };
  isDragging: boolean;
}

interface Connection {
  source: string;
  target: string;
}

interface ExecutionGroup {
  id: string;
  nodes: string[];
  type: 'serial' | 'parallel';
  votes: Record<string, number>;
}

const AGENT_TYPES = [
  { value: 'legal', label: '法律咨询' },
  { value: 'contract', label: '合同审查' },
  { value: 'case-analysis', label: '案情分析' },
  { value: 'debate', label: '辩论代理' },
  { value: 'document', label: '文书起草' },
  { value: 'calculator', label: '法律计算器' },
  { value: 'knowledge-graph', label: '知识图谱' },
  { value: 'dispute-organize', label: '争议整理' },
  { value: 'similar-documents', label: '相似文档' },
  { value: 'legal-calendar', label: '法律日历' },
  { value: 'limitation', label: '诉讼时效' },
  { value: 'case-explanation', label: '案件解释' },
  { value: 'custom', label: '自定义' },
];

export default function AgentsOverviewPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [nodes, setNodes] = useState<AgentNode[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [executionGroups, setExecutionGroups] = useState<ExecutionGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [draggedNode, setDraggedNode] = useState<string | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

  useEffect(() => {
    loadAgents();
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const checkMobile = () => {
    setIsMobile(window.innerWidth < 768);
    if (window.innerWidth < 768) {
      setShowSidebar(false);
    } else {
      setShowSidebar(true);
    }
  };

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/agents?user_id=anonymous`);
      const data = await response.json();
      if (data.success) {
        setAgents(data.data);
      }
    } catch (error) {
      console.error('加载智能体失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (e: React.DragEvent, agent: Agent) => {
    e.dataTransfer.setData('agent', JSON.stringify(agent));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const agentData = e.dataTransfer.getData('agent');
    if (agentData) {
      const agent = JSON.parse(agentData);
      const rect = canvasRef.current?.getBoundingClientRect();
      if (rect) {
        const newNode: AgentNode = {
          agent,
          id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, // 确保唯一ID
          position: {
            x: e.clientX - rect.left - 75, // 75 is half of node width
            y: e.clientY - rect.top - 40,  // 40 is half of node height
          },
          isDragging: false,
        };
        setNodes([...nodes, newNode]);
        
        // Create execution group for this node
        const newGroup: ExecutionGroup = {
          id: `group-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, // 确保唯一ID
          nodes: [newNode.id],
          type: 'serial',
          votes: {},
        };
        setExecutionGroups([...executionGroups, newGroup]);
      }
    }
  };

  const handleNodeDragStart = (e: React.DragEvent, nodeId: string) => {
    e.dataTransfer.setData('nodeId', nodeId);
    setNodes(nodes.map(node => 
      node.id === nodeId ? { ...node, isDragging: true } : node
    ));
  };

  const handleNodeDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleNodeDrop = (e: React.DragEvent, targetNodeId: string) => {
    e.preventDefault();
    const draggedNodeId = e.dataTransfer.getData('nodeId');
    if (draggedNodeId && draggedNodeId !== targetNodeId) {
      // Check if connection already exists
      const connectionExists = connections.some(
        conn => (conn.source === draggedNodeId && conn.target === targetNodeId) || 
                (conn.source === targetNodeId && conn.target === draggedNodeId)
      );
      
      if (!connectionExists) {
        setConnections([...connections, { source: draggedNodeId, target: targetNodeId }]);
      }
    }
    setNodes(nodes.map(node => ({ ...node, isDragging: false })));
  };

  const removeNode = (nodeId: string) => {
    setNodes(nodes.filter(node => node.id !== nodeId));
    setConnections(connections.filter(
      conn => conn.source !== nodeId && conn.target !== nodeId
    ));
    setExecutionGroups(executionGroups.filter(
      group => !group.nodes.includes(nodeId)
    ));
  };

  const updateNodePosition = (nodeId: string, x: number, y: number) => {
    setNodes(nodes.map(node => 
      node.id === nodeId ? { ...node, position: { x, y } } : node
    ));
  };

  const toggleExecutionType = (groupId: string) => {
    setExecutionGroups(executionGroups.map(group => 
      group.id === groupId 
        ? { 
            ...group, 
            type: group.type === 'serial' ? 'parallel' : 'serial',
            votes: group.type === 'serial' ? {} : group.votes
          } 
        : group
    ));
  };

  const castVote = (groupId: string, nodeId: string) => {
    setExecutionGroups(executionGroups.map(group => {
      if (group.id === groupId) {
        const newVotes = { ...group.votes };
        newVotes[nodeId] = (newVotes[nodeId] || 0) + 1;
        return { ...group, votes: newVotes };
      }
      return group;
    }));
  };

  const getCombinedPrompt = () => {
    if (nodes.length === 0) return '';
    
    let combinedPrompt = '你是一个综合性的AI法律助手，拥有以下所有智能体的能力：\n\n';
    
    nodes.forEach((node, index) => {
      combinedPrompt += `${index + 1}. ${node.agent.name} (${AGENT_TYPES.find(t => t.value === node.agent.agent_type)?.label || node.agent.agent_type})\n`;
      combinedPrompt += `   描述：${node.agent.description || '暂无描述'}\n\n`;
    });
    
    combinedPrompt += '请综合运用以上所有智能体的能力，为用户提供全面、专业的法律服务。';
    
    return combinedPrompt;
  };

  const getExecutionFlow = () => {
    if (executionGroups.length === 0) return '暂无执行流程';
    
    let flow = '执行流程：\n\n';
    executionGroups.forEach((group, index) => {
      flow += `${index + 1}. 组 ${index + 1} (${group.type === 'serial' ? '串行' : '并行'})\n`;
      group.nodes.forEach(nodeId => {
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          flow += `   - ${node.agent.name}`;
          if (group.type === 'parallel' && group.votes[nodeId]) {
            flow += ` (${group.votes[nodeId]} 票)`;
          }
          flow += '\n';
        }
      });
      flow += '\n';
    });
    
    return flow;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 text-foreground relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 min-h-[calc(100dvh_-_var(--business-page-top))] flex flex-col">
        {/* 顶部导航 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {isMobile && (
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="p-2 rounded-lg bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800"
              >
                {showSidebar ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </button>
            )}
            <h1 className="text-2xl font-bold font-serif text-sky-900 dark:text-sky-100 flex items-center gap-2">
              <FileText className="w-6 h-6" />
              智能体总览
            </h1>
          </div>
          <button
            onClick={() => router.push('/agents')}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 rounded-lg border border-sky-200 dark:border-sky-800 hover:bg-sky-50 dark:hover:bg-gray-700 transition-smooth"
          >
            <Bot className="w-4 h-4" />
            管理智能体
          </button>
        </div>

        <div className="flex flex-1 gap-6 overflow-hidden">
          {/* 左侧智能体列表 */}
          {(showSidebar || !isMobile) && (
            <div className="w-80 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-4 overflow-y-auto">
              <h2 className="text-lg font-semibold text-sky-900 dark:text-sky-100 mb-4">智能体列表</h2>
              
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
                </div>
              ) : agents.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sky-700 dark:text-sky-300">还没有智能体</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {agents.map((agent) => (
                    <div
                      key={agent.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, agent)}
                      className="p-3 bg-sky-50 dark:bg-sky-900/20 rounded-lg border border-sky-200 dark:border-sky-800 hover:bg-sky-100 dark:hover:bg-sky-900/30 transition-smooth cursor-move"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{agent.avatar || '🤖'}</span>
                        <div className="flex-1">
                          <h3 className="text-sm font-medium text-sky-900 dark:text-sky-100">{agent.name}</h3>
                          <span className="text-xs px-2 py-0.5 bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 rounded-full">
                            {AGENT_TYPES.find(t => t.value === agent.agent_type)?.label || agent.agent_type}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 右侧可视化大屏 */}
          <div className="flex-1 flex flex-col gap-4">
            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-6 flex-1 overflow-hidden">
              <h2 className="text-lg font-semibold text-sky-900 dark:text-sky-100 mb-4">智能体可视化大屏</h2>
              
              <div 
                ref={canvasRef}
                className="border-2 border-dashed border-sky-300 dark:border-sky-700 rounded-xl p-4 h-full relative overflow-auto"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                {nodes.length === 0 ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <p className="text-sky-500 dark:text-sky-400 mb-2">从左侧拖拽智能体到此处</p>
                      <p className="text-xs text-sky-400 dark:text-sky-500">拖拽后将创建智能体的合体版本</p>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* 绘制连接线 */}
                    <svg className="absolute top-0 left-0 w-full h-full pointer-events-none z-1">
                      {connections.map((connection, index) => {
                        const sourceNode = nodes.find(n => n.id === connection.source);
                        const targetNode = nodes.find(n => n.id === connection.target);
                        
                        if (sourceNode && targetNode) {
                          const sourceX = sourceNode.position.x + 150; // 150 is node width
                          const sourceY = sourceNode.position.y + 40;  // 40 is half of node height
                          const targetX = targetNode.position.x;
                          const targetY = targetNode.position.y + 40;
                          
                          return (
                            <g key={index}>
                              <line
                                x1={sourceX}
                                y1={sourceY}
                                x2={targetX}
                                y2={targetY}
                                stroke="#3b82f6"
                                strokeWidth="2"
                                strokeDasharray="5,5"
                              />
                              <path
                                d={`M ${targetX} ${targetY} L ${targetX - 10} ${targetY - 5} L ${targetX - 10} ${targetY + 5} Z`}
                                fill="#3b82f6"
                              />
                            </g>
                          );
                        }
                        return null;
                      })}
                    </svg>
                    
                    {/* 绘制智能体节点 */}
                    {nodes.map((node) => (
                      <div
                        key={node.id}
                        className="absolute bg-white dark:bg-gray-800 rounded-lg border-2 border-sky-300 dark:border-sky-700 shadow-md p-4 w-50 transition-all duration-200 hover:shadow-lg"
                        style={{
                          left: `${node.position.x}px`,
                          top: `${node.position.y}px`,
                          transform: node.isDragging ? 'scale(1.05)' : 'scale(1)',
                          zIndex: node.isDragging ? 100 : 20,
                        }}
                        draggable
                        onDragStart={(e) => handleNodeDragStart(e, node.id)}
                        onDragOver={handleNodeDragOver}
                        onDrop={(e) => handleNodeDrop(e, node.id)}
                        onMouseDown={(e) => {
                          if (e.button === 0) { // Left mouse button
                            let startX = e.clientX;
                            let startY = e.clientY;
                            let startNodeX = node.position.x;
                            let startNodeY = node.position.y;
                            
                            const handleMouseMove = (moveEvent: MouseEvent) => {
                              const deltaX = moveEvent.clientX - startX;
                              const deltaY = moveEvent.clientY - startY;
                              updateNodePosition(node.id, startNodeX + deltaX, startNodeY + deltaY);
                            };
                            
                            const handleMouseUp = () => {
                              document.removeEventListener('mousemove', handleMouseMove);
                              document.removeEventListener('mouseup', handleMouseUp);
                            };
                            
                            document.addEventListener('mousemove', handleMouseMove);
                            document.addEventListener('mouseup', handleMouseUp);
                          }
                        }}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{node.agent.avatar || '🤖'}</span>
                            <div>
                              <h3 className="text-sm font-medium text-sky-900 dark:text-sky-100">{node.agent.name}</h3>
                              <span className="text-xs px-2 py-0.5 bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300 rounded-full">
                                {AGENT_TYPES.find(t => t.value === node.agent.agent_type)?.label || node.agent.agent_type}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => removeNode(node.id)}
                            className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                        <p className="text-xs text-sky-700 dark:text-sky-300 mb-3 line-clamp-2">
                          {node.agent.description || '暂无描述'}
                        </p>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
            
            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-4">
              <h3 className="text-sm font-medium text-sky-900 dark:text-sky-100 mb-3">执行配置</h3>
              
              {executionGroups.length > 0 ? (
                <div className="space-y-3 max-h-48 overflow-y-auto pr-2">
                  {executionGroups.map((group) => (
                    <div key={group.id} className="p-3 bg-sky-50 dark:bg-sky-900/20 rounded-lg border border-sky-200 dark:border-sky-800">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-sky-900 dark:text-sky-100">
                          执行组 {executionGroups.indexOf(group) + 1}
                        </h4>
                        <button
                          onClick={() => toggleExecutionType(group.id)}
                          className="flex items-center gap-1 px-2 py-1 bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 rounded-lg border border-sky-200 dark:border-sky-800 hover:bg-sky-50 dark:hover:bg-gray-700 transition-smooth text-xs"
                        >
                          {group.type === 'serial' ? (
                            <>
                              <GitMerge className="w-3 h-3" />
                              切换为并行
                            </>
                          ) : (
                            <>
                              <GitBranch className="w-3 h-3" />
                              切换为串行
                            </>
                          )}
                        </button>
                      </div>
                      
                      <div className="flex flex-wrap gap-2 mb-2">
                        {group.nodes.map(nodeId => {
                          const node = nodes.find(n => n.id === nodeId);
                          if (node) {
                            return (
                              <div key={nodeId} className="flex items-center gap-2 px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-xs">
                                <span>{node.agent.avatar || '🤖'}</span>
                                <span>{node.agent.name}</span>
                                {group.type === 'parallel' && (
                                  <button
                                    onClick={() => castVote(group.id, nodeId)}
                                    className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200"
                                  >
                                    <ThumbsUp className="w-3 h-3" />
                                    <span>{group.votes[nodeId] || 0}</span>
                                  </button>
                                )}
                              </div>
                            );
                          }
                          return null;
                        })}
                      </div>
                      
                      <div className="text-xs text-sky-600 dark:text-sky-400">
                        {group.type === 'serial' 
                          ? '串行执行：智能体将按顺序依次执行'
                          : '并行执行：智能体将同时执行，采用投票机制选择最佳结果'
                        }
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-sky-700 dark:text-sky-300">请从左侧拖拽智能体到可视化大屏</p>
              )}
            </div>
            
            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl border border-sky-200 dark:border-sky-900/30 shadow-lg p-4">
              <h3 className="text-sm font-medium text-sky-900 dark:text-sky-100 mb-3">执行流程</h3>
              <div className="font-mono text-xs text-sky-800 dark:text-sky-200 bg-white/50 dark:bg-gray-800/50 p-3 rounded-lg overflow-auto max-h-24">
                {getExecutionFlow()}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-sky-700 dark:text-sky-300 rounded-lg border border-sky-200 dark:border-sky-800 hover:bg-sky-50 dark:hover:bg-gray-700 transition-smooth"
          >
            <Home className="w-4 h-4" />
            返回上一页面
          </button>
        </div>
      </div>
    </div>
  );
}
