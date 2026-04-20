import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "";

/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingRoot: __dirname,
  async rewrites() {
    if (!BACKEND_URL) return [];
    // Proxy /backend/* → backend root. Avoids CORS when the browser calls
    // the API from the Fairway frontend's own domain.
    return [
      { source: "/backend/:path*", destination: `${BACKEND_URL}/:path*` },
    ];
  },
};

export default nextConfig;
