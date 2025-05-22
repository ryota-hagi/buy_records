export interface CollectTask {
  platform: string;
  keyword: string;
  limit?: number;
}

export interface CollectResult {
  platform: string;
  keyword: string;
  items: any;
}

import { searchEbayItems } from './ebay';

async function collectFromEbay(task: CollectTask) {
  const { keyword, limit = 10 } = task;
  const result = await searchEbayItems(keyword, limit);
  return result;
}

export async function runCollectors(tasks: CollectTask[]): Promise<CollectResult[]> {
  const promises = tasks.map(async (task) => {
    switch (task.platform) {
      case 'ebay':
        const items = await collectFromEbay(task);
        return { platform: task.platform, keyword: task.keyword, items } as CollectResult;
      default:
        return { platform: task.platform, keyword: task.keyword, items: [] } as CollectResult;
    }
  });
  return Promise.all(promises);
}
