import path from "node:path";
import type { NextConfig } from "next";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

const nextConfig: NextConfig = {
  basePath: basePath,
  assetPrefix: basePath,
  output: "standalone",
  turbopack: {
    root: path.resolve("./"),
  },
  outputFileTracingRoot: path.resolve("./"),
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "yamareco.org",
      },
      {
        protocol: "https",
        hostname: "yamareco.info",
      },
      {
        protocol: "https",
        hostname: "imgu.web.nhk",
      },
    ],
  },
};

export default nextConfig;
