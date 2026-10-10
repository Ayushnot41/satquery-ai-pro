const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8010';
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    // Resolve canonical imagery before legacy public/ placeholders shadow it.
    return {beforeFiles: [
      { source: '/app', destination: '/' },
      { source: '/assets/demo-live-weather.png', destination: `${backend}/assets/demo-flood-post-sar.png` },
      { source: '/assets/demo-past-baseline.png', destination: `${backend}/assets/demo-flood-pre-optical.png` },
      ...['api', 'static', 'assets'].map(path => ({source: `/${path}/:path*`, destination: `${backend}/${path}/:path*`})),
      ...['console', 'legacy', 'preview-3d', 'preview-hud'].map(path => ({source: `/${path}`, destination: `${backend}/${path}`})),
    ]};
  },
  async headers() {
    return [{source:'/:path*', headers:[
      {key:'X-Content-Type-Options', value:'nosniff'},
      {key:'Referrer-Policy', value:'strict-origin-when-cross-origin'},
      {key:'X-Frame-Options', value:'SAMEORIGIN'},
      {key:'Permissions-Policy', value:'camera=(), payment=()'},
    ]}];
  },
};
export default nextConfig;
