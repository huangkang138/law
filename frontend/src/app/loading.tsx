export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100">
      <div className="flex flex-col items-center gap-6">
        {/* 加载动画 */}
        <div className="relative">
          <div className="h-20 w-20 rounded-full border-4 border-blue-200 border-t-blue-500 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-sky-400 via-blue-500 to-indigo-500 animate-pulse" />
          </div>
        </div>
        
        {/* 加载文字 */}
        <div className="flex flex-col items-center gap-2">
          <p className="text-xl font-semibold text-blue-600">加载中...</p>
          <p className="text-sm text-blue-400">正在准备页面</p>
        </div>
      </div>
    </div>
  );
}
