import type { NextConfig } from 'next';

const apiOrigin = process.env.API_PROXY_TARGET || 'http://localhost:8000';

const nextConfig: NextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  async redirects() {
    return [
      { source: '/credara-enterprise-ui-v11.html', destination: '/', permanent: true },
      { source: '/credara-ui.html', destination: '/', permanent: true },
      { source: '/:path*.html', destination: '/', permanent: true },
    ];
  },
  async rewrites() {
    return [{ source: '/api/v1/:path*', destination: `${apiOrigin}/api/v1/:path*` }];
  },
};

export default nextConfig;
