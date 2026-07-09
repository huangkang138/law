"use client";

import React, { useState, useEffect } from 'react';

interface UMLDiagramResponse {
  success: boolean;
  data?: {
    id: string;
    diagram_type: string;
    output_format: string;
    access_url: string;
    created_at: string;
  };
  message?: string;
}

interface UMLDiagramHistory {
  id: string;
  diagram_type: string;
  output_format: string;
  access_url: string;
  created_at: string;
}

const UMLDiagramPage: React.FC = () => {
  const [diagramType, setDiagramType] = useState<string>('plantuml');
  const [outputFormat, setOutputFormat] = useState<string>('svg');
  const [diagramSource, setDiagramSource] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<boolean>(false);
  const [resultUrl, setResultUrl] = useState<string>('');
  const [history, setHistory] = useState<UMLDiagramHistory[]>([]);

  // 加载历史记录
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/legal-tools/uml-diagram');
      const data = await response.json();
      if (data.success) {
        setHistory(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);
    setResultUrl('');

    try {
      const response = await fetch('/api/legal-tools/uml-diagram', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          diagram_type: diagramType,
          diagram_source: diagramSource,
          output_format: outputFormat,
        }),
      });

      const data: UMLDiagramResponse = await response.json();

      if (data.success && data.data) {
        setSuccess(true);
        setResultUrl(data.data.access_url);
        // 重新加载历史记录
        fetchHistory();
      } else {
        setError(data.message || '生成图表失败');
      }
    } catch (error) {
      setError('生成图表失败，请检查网络连接');
      console.error('Error generating diagram:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const response = await fetch(`/api/legal-tools/uml-diagram/${id}`, {
        method: 'DELETE',
      });
      const data = await response.json();
      if (data.success) {
        // 重新加载历史记录
        fetchHistory();
      }
    } catch (error) {
      console.error('Error deleting diagram:', error);
    }
  };

  // 示例代码
  const examples = {
    plantuml: {
      sequence: `@startuml
actor User
participant "Service A" as A
participant "Service B" as B
User -> A: request
A -> B: forward
B --> A: response
A --> User: result
@enduml`,
      class: `@startuml
class User {
  +String name
  +String email
  +login()
  +logout()
}
class Order {
  +int id
  +Date date
  +submit()
}
User "1" -- "*" Order
@enduml`,
      activity: `@startuml
start
:输入数据;
if (数据有效?) then (yes)
  :处理数据;
  :保存结果;
else (no)
  :显示错误;
endif
stop
@enduml`,
    },
    mermaid: {
      flowchart: `graph TD
    A[开始] --> B[输入数据]
    B --> C{数据有效?}
    C -->|是| D[处理数据]
    C -->|否| E[显示错误]
    D --> F[保存结果]
    E --> G[结束]
    F --> G`,
      sequence: `sequenceDiagram
    participant User
    participant Server
    participant Database
    User->>Server: 请求数据
    Server->>Database: 查询数据
    Database-->>Server: 返回数据
    Server-->>User: 显示数据`,
    },
    graphviz: {
      graph: `digraph G {
    rankdir=LR;
    A [label="开始"];
    B [label="处理"];
    C [label="结束"];
    A -> B;
    B -> C;
}`
    },
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-center text-[#8B0000]">
        UML 图表生成工具
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 左侧：图表生成表单 */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">生成图表</h2>
            
            {error && (
              <div className="bg-red-100 text-red-700 p-3 rounded mb-4">
                {error}
              </div>
            )}
            
            {success && resultUrl && (
              <div className="bg-green-100 text-green-700 p-3 rounded mb-4">
                图表生成成功！
              </div>
            )}

            <form onSubmit={handleGenerate}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  图表类型
                </label>
                <select
                  value={diagramType}
                  onChange={(e) => setDiagramType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#8B0000]"
                >
                  <option value="plantuml">PlantUML (UML 图表)</option>
                  <option value="mermaid">Mermaid (流程图)</option>
                  <option value="graphviz">Graphviz (图形)</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  输出格式
                </label>
                <select
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#8B0000]"
                >
                  <option value="svg">SVG (矢量图)</option>
                  <option value="png">PNG (图片)</option>
                  <option value="pdf">PDF (文档)</option>
                  <option value="jpeg">JPEG (压缩图片)</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  图表源代码
                </label>
                <textarea
                  value={diagramSource}
                  onChange={(e) => setDiagramSource(e.target.value)}
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#8B0000] font-mono text-sm"
                  placeholder="输入图表源代码..."
                />
              </div>

              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">示例代码</h3>
                <div className="grid grid-cols-2 gap-2">
                  {diagramType === 'plantuml' && (
                    <>
                      <button
                        type="button"
                        onClick={() => setDiagramSource(examples.plantuml.sequence)}
                        className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                      >
                        序列图
                      </button>
                      <button
                        type="button"
                        onClick={() => setDiagramSource(examples.plantuml.class)}
                        className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                      >
                        类图
                      </button>
                      <button
                        type="button"
                        onClick={() => setDiagramSource(examples.plantuml.activity)}
                        className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                      >
                        活动图
                      </button>
                    </>
                  )}
                  {diagramType === 'mermaid' && (
                    <>
                      <button
                        type="button"
                        onClick={() => setDiagramSource(examples.mermaid.flowchart)}
                        className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                      >
                        流程图
                      </button>
                      <button
                        type="button"
                        onClick={() => setDiagramSource(examples.mermaid.sequence)}
                        className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                      >
                        序列图
                      </button>
                    </>
                  )}
                  {diagramType === 'graphviz' && (
                    <button
                      type="button"
                      onClick={() => setDiagramSource(examples.graphviz.graph)}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                    >
                      示例图
                    </button>
                  )}
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !diagramSource}
                className="w-full bg-[#8B0000] text-white py-2 px-4 rounded-md hover:bg-[#6B0000] disabled:bg-gray-400 transition-colors"
              >
                {loading ? '生成中...' : '生成图表'}
              </button>
            </form>
          </div>

          {/* 结果显示 */}
          {success && resultUrl && (
            <div className="mt-6 bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">生成结果</h2>
              <div className="flex flex-col items-center">
                {outputFormat === 'svg' ? (
                  <iframe
                    src={resultUrl}
                    className="border border-gray-200 rounded w-full max-w-2xl h-96"
                    title="UML Diagram"
                  />
                ) : (
                  <img
                    src={resultUrl}
                    alt="UML Diagram"
                    className="border border-gray-200 rounded max-w-full h-auto"
                  />
                )}
                <a
                  href={resultUrl}
                  download
                  className="mt-4 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                >
                  下载图表
                </a>
              </div>
            </div>
          )}
        </div>

        {/* 右侧：历史记录 */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">历史记录</h2>
            {history.length === 0 ? (
              <p className="text-gray-500">暂无历史记录</p>
            ) : (
              <div className="space-y-4">
                {history.map((item) => (
                  <div key={item.id} className="border border-gray-200 rounded p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">
                        {item.diagram_type.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <a
                        href={item.access_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#8B0000] hover:underline text-sm"
                      >
                        查看图表
                      </a>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UMLDiagramPage;