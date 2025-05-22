import { NextRequest, NextResponse } from 'next/server';
import { runCollectors } from '@/lib/collector';
import { collectTasks } from '@/lib/collectConfig';

export async function GET(request: NextRequest) {
  try {
    const results = await runCollectors(collectTasks);
    return NextResponse.json({ results });
  } catch (error) {
    console.error('Error running collectors:', error);
    return NextResponse.json({ error: 'Failed to collect data' }, { status: 500 });
  }
}
