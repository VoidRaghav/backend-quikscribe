const express = require('express');
const Redis = require('ioredis');
const { spawn } = require('child_process');
const path = require('path');

class MeetingCoordinator {
    constructor() {
        this.app = express();
        this.redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');
        this.activeMeetings = new Map();
        this.portPool = new Set();
        this.maxConcurrentMeetings = parseInt(process.env.MAX_CONCURRENT_MEETINGS) || 10;
        this.portStart = parseInt(process.env.DYNAMIC_PORT_START) || 3002;
        this.portEnd = parseInt(process.env.DYNAMIC_PORT_END) || 3012;
        this.mode = (process.env.COORDINATOR_MODE || 'spawn').toLowerCase(); // 'queue' or 'spawn'
        this.queueName = process.env.MEETING_QUEUE || 'meeting:queue';

        this.initializePortPool();
        this.setupMiddleware();
        this.setupRoutes();
        this.setupCleanup();
    }

    initializePortPool() {
        for (let port = this.portStart; port <= this.portEnd; port++) {
            this.portPool.add(port);
        }
    }

    setupMiddleware() {
        this.app.use(express.json());
        this.app.use(express.urlencoded({ extended: true }));
    }

    setupRoutes() {
        // Start a new meeting
        this.app.post('/meeting/start', async (req, res) => {
            try {
                const { meetingId, uuid, duration, recordType } = req.body;

                if (!meetingId || !uuid) {
                    return res.status(400).json({
                        error: 'meetingId and uuid are required'
                    });
                }

                // In queue mode, we just enqueue and return
                if (this.mode === 'queue') {
                    await this.redis.lpush(this.queueName, JSON.stringify({ meetingId, uuid, duration, recordType }));
                    console.log(`📥 Queued meeting ${meetingId} (uuid=${uuid}) on ${this.queueName}`);
                    return res.json({ success: true, queued: true, meetingId, queue: this.queueName });
                }

                // spawn mode: prevent duplicate meetings in-memory
                if (this.activeMeetings.has(meetingId)) {
                    return res.status(409).json({
                        error: 'Meeting already in progress',
                        existingMeeting: this.activeMeetings.get(meetingId)
                    });
                }

                // Check capacity
                if (this.activeMeetings.size >= this.maxConcurrentMeetings) {
                    return res.status(503).json({
                        error: 'Maximum concurrent meetings reached',
                        maxConcurrent: this.maxConcurrentMeetings,
                        current: this.activeMeetings.size
                    });
                }

                // Get available port (only used in spawn mode)
                const port = this.getAvailablePort();
                if (!port) {
                    return res.status(503).json({ error: 'No available ports for new meeting' });
                }

                // Start Google Bot instance
                const botProcess = await this.startGoogleBot(meetingId, uuid, port, duration, recordType);

                // Store meeting info
                const meetingInfo = {
                    meetingId,
                    uuid,
                    port,
                    process: botProcess,
                    startTime: new Date(),
                    duration: duration || 1,
                    recordType: recordType || 'VIDEO'
                };

                this.activeMeetings.set(meetingId, meetingInfo);
                this.portPool.delete(port);

                // Store in Redis for persistence
                await this.redis.hset(
                    'active_meetings',
                    meetingId,
                    JSON.stringify(meetingInfo)
                );

                console.log(`✅ Meeting ${meetingId} started on port ${port}`);

                res.json({
                    success: true,
                    meetingId,
                    port,
                    message: 'Meeting started successfully',
                    meetingInfo: {
                        port,
                        startTime: meetingInfo.startTime,
                        duration: meetingInfo.duration,
                        recordType: meetingInfo.recordType
                    }
                });

            } catch (error) {
                console.error('❌ Error starting meeting:', error);
                res.status(500).json({
                    error: 'Failed to start meeting',
                    details: error.message
                });
            }
        });

        // Stop a meeting
        this.app.post('/meeting/stop', async (req, res) => {
            try {
                const { meetingId } = req.body;

                if (!meetingId) {
                    return res.status(400).json({
                        error: 'meetingId is required'
                    });
                }

                if (this.mode === 'queue') {
                    // Not supported in queue mode (workers are short-lived per job)
                    return res.status(501).json({ error: 'Stop not implemented in queue mode' });
                }

                const meeting = this.activeMeetings.get(meetingId);
                if (!meeting) {
                    return res.status(404).json({
                        error: 'Meeting not found'
                    });
                }

                // Stop the bot process
                await this.stopGoogleBot(meeting);

                // Clean up
                this.activeMeetings.delete(meetingId);
                this.portPool.add(meeting.port);

                // Remove from Redis
                await this.redis.hdel('active_meetings', meetingId);

                console.log(`🛑 Meeting ${meetingId} stopped on port ${meeting.port}`);

                res.json({
                    success: true,
                    message: 'Meeting stopped successfully',
                    meetingId,
                    port: meeting.port
                });

            } catch (error) {
                console.error('❌ Error stopping meeting:', error);
                res.status(500).json({
                    error: 'Failed to stop meeting',
                    details: error.message
                });
            }
        });

        // Get meeting status
        this.app.get('/meeting/:meetingId', async (req, res) => {
            try {
                const { meetingId } = req.params;
                const meeting = this.activeMeetings.get(meetingId);

                if (!meeting) {
                    return res.status(404).json({
                        error: 'Meeting not found'
                    });
                }

                res.json({
                    meetingId,
                    status: 'active',
                    port: meeting.port,
                    startTime: meeting.startTime,
                    duration: meeting.duration,
                    recordType: meeting.recordType,
                    uptime: Date.now() - meeting.startTime.getTime()
                });

            } catch (error) {
                console.error('❌ Error getting meeting status:', error);
                res.status(500).json({
                    error: 'Failed to get meeting status',
                    details: error.message
                });
            }
        });

        // List all active meetings
        this.app.get('/meetings', async (req, res) => {
            try {
                if (this.mode === 'queue') {
                    const len = await this.redis.llen(this.queueName);
                    return res.json({
                        mode: this.mode,
                        queued: len,
                        activeMeetings: [],
                        total: 0,
                        maxConcurrent: this.maxConcurrentMeetings,
                    });
                }
                const meetings = Array.from(this.activeMeetings.entries()).map(([meetingId, meeting]) => ({
                    meetingId,
                    port: meeting.port,
                    startTime: meeting.startTime,
                    duration: meeting.duration,
                    recordType: meeting.recordType,
                    uptime: Date.now() - meeting.startTime.getTime()
                }));

                res.json({
                    activeMeetings: meetings,
                    total: meetings.length,
                    maxConcurrent: this.maxConcurrentMeetings,
                    availablePorts: this.portPool.size
                });

            } catch (error) {
                console.error('❌ Error listing meetings:', error);
                res.status(500).json({
                    error: 'Failed to list meetings',
                    details: error.message
                });
            }
        });

        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                activeMeetings: this.activeMeetings.size,
                maxConcurrent: this.maxConcurrentMeetings,
                availablePorts: this.portPool.size,
                uptime: process.uptime()
            });
        });
    }

    getAvailablePort() {
        return Array.from(this.portPool)[0] || null;
    }

    async startGoogleBot(meetingId, uuid, port, duration, recordType) {
        return new Promise((resolve, reject) => {
            const env = {
                ...process.env,
                MEETING_ID: meetingId,
                UUID: uuid,
                DYNAMIC_PORT: port.toString(),
                DURATION: duration?.toString() || '1',
                RECORD_TYPE: recordType || 'VIDEO'
            };

            const botProcess = spawn('bun', ['run', 'index.ts'], {
                cwd: '/app',
                env,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            // Handle process events
            botProcess.on('error', (error) => {
                console.error(`❌ Bot process error for meeting ${meetingId}:`, error);
                reject(error);
            });

            botProcess.on('exit', (code) => {
                console.log(`🔄 Bot process exited for meeting ${meetingId} with code ${code}`);
                this.cleanupMeeting(meetingId);
            });

            // Wait a bit to ensure process starts
            setTimeout(() => {
                if (botProcess.killed) {
                    reject(new Error('Bot process failed to start'));
                } else {
                    resolve(botProcess);
                }
            }, 2000);
        });
    }

    async stopGoogleBot(meeting) {
        return new Promise((resolve) => {
            if (meeting.process && !meeting.process.killed) {
                meeting.process.kill('SIGTERM');

                // Force kill after 5 seconds if needed
                setTimeout(() => {
                    if (!meeting.process.killed) {
                        meeting.process.kill('SIGKILL');
                    }
                }, 5000);
            }
            resolve();
        });
    }

    cleanupMeeting(meetingId) {
        const meeting = this.activeMeetings.get(meetingId);
        if (meeting) {
            this.portPool.add(meeting.port);
            this.activeMeetings.delete(meetingId);
            this.redis.hdel('active_meetings', meetingId);
            console.log(`🧹 Cleaned up meeting ${meetingId}`);
        }
    }

    setupCleanup() {
        // Cleanup on process exit
        process.on('SIGINT', () => this.shutdown());
        process.on('SIGTERM', () => this.shutdown());

        // Periodic cleanup check
        setInterval(() => {
            this.activeMeetings.forEach((meeting, meetingId) => {
                const uptime = Date.now() - meeting.startTime.getTime();
                const maxDuration = meeting.duration * 60 * 1000; // Convert to milliseconds

                if (uptime > maxDuration) {
                    console.log(`⏰ Meeting ${meetingId} exceeded duration, stopping...`);
                    this.stopGoogleBot(meeting);
                    this.cleanupMeeting(meetingId);
                }
            });
        }, 30000); // Check every 30 seconds
    }

    async shutdown() {
        console.log('🛑 Shutting down Meeting Coordinator...');

        // Stop all active meetings
        for (const [meetingId, meeting] of this.activeMeetings) {
            await this.stopGoogleBot(meeting);
            this.cleanupMeeting(meetingId);
        }

        // Close Redis connection
        await this.redis.quit();

        process.exit(0);
    }

    start() {
        const port = process.env.COORDINATOR_PORT || 3001;
        this.app.listen(port, () => {
            console.log(`🚀 Meeting Coordinator started on port ${port}`);
            console.log(`📊 Max concurrent meetings: ${this.maxConcurrentMeetings}`);
            console.log(`🔌 Port range: ${this.portStart}-${this.portEnd}`);
        });
    }
}

// Start the coordinator
const coordinator = new MeetingCoordinator();
coordinator.start();
