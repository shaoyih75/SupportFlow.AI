import type { NextConfig } from "next";

// Where Next.js forwards /api/* requests. The browser only ever talks to Next.js,
// so a single Cloudflare tunnel on port 3000 is enough for remote access.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Allow the dev server to be opened through a Cloudflare quick tunnel.
  allowedDevOrigins: ["*.trycloudflare.com"],
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
  },
};

export default nextConfig;
