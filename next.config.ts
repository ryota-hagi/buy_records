import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  serverExternalPackages: ['@supabase/supabase-js'],
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.externals.push('@supabase/supabase-js');
    }
    return config;
  },
  env: {
    SKIP_ENV_VALIDATION: '1',
  },
};

export default nextConfig;
