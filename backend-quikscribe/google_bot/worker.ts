import Redis from 'ioredis';
import { Meeting } from './Meeting';

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

      const m = new Meeting(meetingId);
      await m.joinMeeting();
      console.log(`[worker] meeting ${meetingId} finished.`);
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
