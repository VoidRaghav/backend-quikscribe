import Redis from 'ioredis';
import { Meeting } from './Meeting';

// Normalize Meet URL: if a full URL is provided use as-is; otherwise
// treat input as a code and prepend the canonical Meet base URL.
function normalizeMeetUrl(input: string): string {
  const trimmed = (input || '').trim();
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  const code = trimmed
    .replace(/^https?:\/\/(www\.)?meet\.google\.com\//i, '')
    .replace(/^meet\.google\.com\//i, '')
    .replace(/^\/+/, '');
  return `https://meet.google.com/${code}`;
}

// Poll Selenium Grid status endpoint until it becomes ready.
async function waitForSeleniumReady(url = 'http://localhost:4444/status', timeoutMs = 120_000, intervalMs = 2000): Promise<void> {
  const start = Date.now();
  // Node 18+ has global fetch; if unavailable, consider adding a lightweight HTTP request.
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url, { method: 'GET' } as any);
      if (res && (res as any).ok) {
        return;
      }
    } catch (_) {
      // ignore and retry
    }
    console.log(`[worker] waiting for Selenium at ${url} ...`);
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`Selenium not ready after ${Math.floor(timeoutMs / 1000)}s at ${url}`);
}

async function runWorker() {
  const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
  const queueName = process.env.MEETING_QUEUE || 'meeting:queue';
  const idleExitSecs = Number(process.env.WORKER_IDLE_EXIT_SECS || '60');
  const recordType = (process.env.RECORD_TYPE as 'AUDIO' | 'VIDEO') || 'VIDEO';

  const redis = new Redis(redisUrl);
  let idleAccum = 0;

  console.log(`[worker] started. queue=${queueName} redis=${redisUrl}`);

  while (true) {
    // Block for up to 15s
    const res = await redis.brpop(queueName, 15);
    if (!res) {
      idleAccum += 15;
      if (idleAccum >= idleExitSecs) {
        console.log(`[worker] idle for ${idleExitSecs}s. exiting.`);
        break;
      }
      continue;
    }
    idleAccum = 0;

    const [, payload] = res; // [list, value]
    try {
      const job = JSON.parse(payload);
      const meetingId: string = job.meetingId;
      const durationMin: number = Number(job.duration || 1);
      const uuid: string = job.uuid;
      const type: 'AUDIO' | 'VIDEO' = (job.recordType as any) || recordType;

      process.env.RECORD_TYPE = type;
      process.env.DURATION = String(durationMin);
      process.env.UUID = uuid;
      process.env.MEETING_ID = meetingId;

      // Normalize URL and ensure Selenium is ready before joining
      const meetUrl = normalizeMeetUrl(meetingId);
      console.log(`Opening Meet URL: ${meetUrl}`);
      await waitForSeleniumReady('http://localhost:4444/status', 120_000, 2000);

      const m = new Meeting(meetUrl);
      await m.joinMeeting();
      console.log(`[worker] meeting ${meetUrl} finished.`);
    } catch (err) {
      console.error(`[worker] error processing job:`, err);
    }
  }

  await redis.quit();
}

runWorker().catch((e) => {
  console.error('[worker] fatal error', e);
  process.exit(1);
});
