/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@layapa/ui', '@layapa/shared-types'],
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
