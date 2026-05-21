/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
  },
  async rewrites() {
    const api = process.env.API_INTERNAL_URL || 'http://api:8000';
    return [{ source: '/api/backend/:path*', destination: `${api}/:path*` }];
  },
};

export default nextConfig;
