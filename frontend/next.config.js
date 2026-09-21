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

  // Optimized public assets have content hashes in their filenames.
  async headers() {
    return [{
      source: '/optimized/:path*',
      headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }],
    }]
  },

  // 启用React严格模式
  reactStrictMode: true,

  // 优化包体积
  swcMinify: true,

  // 开发环境可通过 Next 代理访问后端；生产环境由 Nginx 负责 /api 转发。
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8001'}/api/:path*`,
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
