import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // Avoid Next.js dev warning when opening the app with 127.0.0.1
    allowedDevOrigins: [
      "http://localhost:3000",
      "http://127.0.0.1:3000",
    ],
  },
};

export default nextConfig;
