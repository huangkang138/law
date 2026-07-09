/** @type {import('next').NextConfig} */
const nextConfig = {
  // 禁用 Vercel 开发工具栏
  devIndicators: {
    buildActivity: false,
    appIsrStatus: false,
  },

  // 图片优化配置
  images: {
    unoptimized: true,
  },

  // 压缩输出
  compress: true,

  // 启用React严格模式
  reactStrictMode: true,

  // 优化包体积
  swcMinify: true,

  // 配置rewrites
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/api/:path*',
      },
    ]
  },

  // 自定义webpack配置
  webpack: (config, { dev, isServer }) => {
    // 开发模式下优化
    if (dev) {
      config.optimization = {
        ...config.optimization,
        removeAvailableModules: false,
        removeEmptyChunks: false,
        splitChunks: false,
      }
    }
    return config
  },
}

module.exports = nextConfig
