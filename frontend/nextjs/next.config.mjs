import withPWAInit from "@ducanh2912/next-pwa";

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        hostname: 'www.google.com',
      },
      {
        hostname: 'www.google-analytics.com',
      },
      {
        hostname: 'localhost',
      }
    ],
  },
  // Proxy /outputs requests to the backend server for generated images
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    return [
      {
        source: '/outputs/:path*',
        destination: `${backendUrl}/outputs/:path*`,
      },
    ];
  },
};

const withPWA = withPWAInit({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
});

export default withPWA(nextConfig);
