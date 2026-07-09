export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen pt-20">
      <div className="flex flex-col items-center gap-4">
        <div className="h-16 w-16 rounded-full border-4 border-blue-200 border-t-blue-500 animate-spin" />
        <p className="text-lg text-blue-600">加载中...</p>
      </div>
    </div>
  );
}
