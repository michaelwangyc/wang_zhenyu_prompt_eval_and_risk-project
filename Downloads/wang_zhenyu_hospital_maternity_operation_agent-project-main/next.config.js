/** @type {import('next').NextConfig} */
const nextConfig = {
  // Performance optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production', // Remove console.log in production
  },

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.michaelwangyc.me',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'yq-img-cdn.michaelwangyc.me',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.michaelwangyc.me',
        pathname: '/**',
      },
    ],
  },

  rewrites: async () => {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/api/:path*"
            : "/api/",
      },
      {
        source: "/docs",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/docs"
            : "/api/docs",
      },
      {
        source: "/openapi.json",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/openapi.json"
            : "/api/openapi.json",
      },
    ];
  },

  // Reduce bundle size
  productionBrowserSourceMaps: false,
};

module.exports = nextConfig;
