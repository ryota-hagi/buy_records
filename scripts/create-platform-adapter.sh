#!/bin/bash

# プラットフォームアダプター作成スクリプト
# 使用方法: ./create-platform-adapter.sh <platform-name> <platform-code>

if [ $# -ne 2 ]; then
    echo "Usage: $0 <platform-name> <platform-code>"
    echo "Example: $0 'Yahoo Auction' yahoo-auction"
    exit 1
fi

PLATFORM_NAME=$1
PLATFORM_CODE=$2
PLATFORM_CLASS=$(echo $PLATFORM_CODE | sed 's/-/_/g' | sed 's/\b\(.\)/\u\1/g')Adapter

# ディレクトリ作成
PLATFORM_DIR="src/platforms/adapters/$PLATFORM_CODE"
mkdir -p $PLATFORM_DIR

# アダプターファイル作成
cat > "$PLATFORM_DIR/${PLATFORM_CODE}.adapter.ts" << EOF
/**
 * ${PLATFORM_NAME} Platform Adapter
 */

import { PlatformAdapter, PlatformSearchResult, ApiLimits, HealthCheckResult } from '../../interfaces/platform-adapter';
import { SearchRequest, SearchType } from '../../../search/interfaces/search-request';
import { SearchResult } from '../../../search/interfaces/search-response';

export class ${PLATFORM_CLASS} implements PlatformAdapter {
  name = '${PLATFORM_NAME}';
  code = '${PLATFORM_CODE}';
  supportedSearchTypes = [
    SearchType.PRODUCT_NAME,
    SearchType.JAN_CODE
  ];
  supportedRegions = ['JP'];
  
  constructor(private config?: any) {}
  
  async search(request: SearchRequest): Promise<PlatformSearchResult> {
    // TODO: Implement search logic
    console.log(\`Searching on \${this.name} with query:\`, request);
    
    return {
      results: [],
      metadata: {
        totalFound: 0,
        searchTime: 0,
        searchMethod: 'api'
      }
    };
  }
  
  async validateCredentials(): Promise<boolean> {
    // TODO: Implement credential validation
    return true;
  }
  
  getApiLimits(): ApiLimits {
    return {
      requestsPerMinute: 60,
      requestsPerDay: 10000,
      maxResultsPerRequest: 50
    };
  }
  
  async healthCheck(): Promise<HealthCheckResult> {
    // TODO: Implement health check
    return {
      status: 'healthy',
      latency: 0
    };
  }
}
EOF

# 設定ファイル作成
cat > "$PLATFORM_DIR/${PLATFORM_CODE}.config.ts" << EOF
/**
 * ${PLATFORM_NAME} Configuration
 */

export const ${PLATFORM_CODE.toUpperCase().replace(/-/g, '_')}_CONFIG = {
  apiEndpoint: process.env.${PLATFORM_CODE.toUpperCase().replace(/-/g, '_')}_API_ENDPOINT || '',
  apiKey: process.env.${PLATFORM_CODE.toUpperCase().replace(/-/g, '_')}_API_KEY || '',
  timeout: 30000,
  retryAttempts: 3
};
EOF

# テストファイル作成
cat > "$PLATFORM_DIR/${PLATFORM_CODE}.test.ts" << EOF
/**
 * ${PLATFORM_NAME} Adapter Tests
 */

import { ${PLATFORM_CLASS} } from './${PLATFORM_CODE}.adapter';
import { SearchType } from '../../../search/interfaces/search-request';

describe('${PLATFORM_CLASS}', () => {
  let adapter: ${PLATFORM_CLASS};
  
  beforeEach(() => {
    adapter = new ${PLATFORM_CLASS}();
  });
  
  describe('search', () => {
    it('should return empty results for now', async () => {
      const result = await adapter.search({
        type: SearchType.PRODUCT_NAME,
        productName: 'test product'
      });
      
      expect(result.results).toEqual([]);
      expect(result.metadata.totalFound).toBe(0);
    });
  });
  
  describe('validateCredentials', () => {
    it('should return true', async () => {
      const isValid = await adapter.validateCredentials();
      expect(isValid).toBe(true);
    });
  });
  
  describe('healthCheck', () => {
    it('should return healthy status', async () => {
      const health = await adapter.healthCheck();
      expect(health.status).toBe('healthy');
    });
  });
});
EOF

# 登録ファイル作成
cat > "$PLATFORM_DIR/register.ts" << EOF
/**
 * ${PLATFORM_NAME} Registration
 */

import { PlatformRegistry } from '../../registry/platform-registry';
import { ${PLATFORM_CLASS} } from './${PLATFORM_CODE}.adapter';
import { ${PLATFORM_CODE.toUpperCase().replace(/-/g, '_')}_CONFIG } from './${PLATFORM_CODE}.config';

export function register${PLATFORM_CLASS}() {
  const registry = PlatformRegistry.getInstance();
  
  registry.register({
    adapter: new ${PLATFORM_CLASS}(${PLATFORM_CODE.toUpperCase().replace(/-/g, '_')}_CONFIG),
    priority: {
      code: '${PLATFORM_CODE}',
      priority: 10, // TODO: Set appropriate priority
      enabled: false // TODO: Enable when ready
    },
    metadata: {
      addedDate: new Date(),
      version: '1.0.0',
      documentation: 'https://github.com/ryota-hagi/buy_records/docs/platforms/${PLATFORM_CODE}.md'
    }
  });
}
EOF

echo "✅ Platform adapter created successfully!"
echo ""
echo "📁 Created files:"
echo "  - $PLATFORM_DIR/${PLATFORM_CODE}.adapter.ts"
echo "  - $PLATFORM_DIR/${PLATFORM_CODE}.config.ts"
echo "  - $PLATFORM_DIR/${PLATFORM_CODE}.test.ts"
echo "  - $PLATFORM_DIR/register.ts"
echo ""
echo "📝 Next steps:"
echo "  1. Implement the search() method in ${PLATFORM_CODE}.adapter.ts"
echo "  2. Add environment variables to .env:"
echo "     - ${PLATFORM_CODE.toUpperCase().replace(/-/g, '_')}_API_KEY"
echo "     - ${PLATFORM_CODE.toUpperCase().replace(/-/g, '_')}_API_ENDPOINT"
echo "  3. Register the adapter in src/platforms/index.ts"
echo "  4. Write tests and documentation"
echo "  5. Set priority and enable in register.ts"
EOF