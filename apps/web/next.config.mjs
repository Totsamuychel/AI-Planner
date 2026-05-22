/** @type {import('next').NextConfig} */

// When GITHUB_PAGES=true the app is built as a static export for GitHub
// Pages (a UI-only demo shell — there is no backend in that deployment).
// Otherwise it runs normally with the API rewrite for local/Docker use.
const isPages = process.env.GITHUB_PAGES === 'true';

const nextConfig = {
  reactStrictMode: true,
  ...(isPages
    ? {
        output: 'export',
        basePath: '/AI-Planner',
        images: { unoptimized: true },
      }
    : {
        async rewrites() {
          const api = process.env.API_INTERNAL_URL || 'http://api:8000';
          return [{ source: '/api/backend/:path*', destination: `${api}/:path*` }];
        },
      }),
};

export default nextConfig;
