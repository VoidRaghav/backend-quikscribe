import { Meeting } from "./Meeting";
import express, { Request, Response } from "express";  // NEW: Express import for dynamic port support
// import app from "./server";  // OLD: Single app import

function startProcess() {       
    const UUID = process.env.UUID;
    const MEETING_ID = process.env.MEETING_ID;
    const DYNAMIC_PORT = process.env.DYNAMIC_PORT || 3000; // ✅ DYNAMIC PORT
    
    if (!UUID || !MEETING_ID) {
        console.log("UUID and meeting id are required fields");
        process.exit(0);
    }

    const newMeeting = new Meeting(process.env.MEETING_ID!);
    const app = express();  // NEW: Create Express app instance

    // Simple health endpoint for readiness/liveness
    app.get('/health', (_req: Request, res: Response) => {
        res.send('ok');
    });

    app.post(`/${UUID}/meeting/pause`, async (_req: Request, res: Response) => {
        await newMeeting.pauseRecording();
        res.send("Paused");
    });

    app.post(`/${UUID}/meeting/resume`, async (_req: Request, res: Response) => {
        await newMeeting.resumeRecording();
        res.send("Resume");
    });

    app.post(`/${UUID}/meeting/stop`, async (_req: Request, res: Response) => {
        await newMeeting.stopRecording();
        res.send("Stopped");
    });

    // ✅ DYNAMIC PORT BINDING
    app.listen(DYNAMIC_PORT, async () => {
        console.log(`Bot server started on dynamic port ${DYNAMIC_PORT}`);
        console.log(`Meeting ID: ${MEETING_ID}`);
        console.log(`UUID: ${UUID}`);
        
        await newMeeting.joinMeeting();
        console.log("Meeting finished");
        process.exit(0);
    });

    // OLD CODE - COMMENTED OUT FOR REFERENCE:
    /*
    app.post(`/${UUID}/meeting/pause`, async (req, res) => {
        await newMeeting.pauseRecording();
        res.send("Paused");
    })

    app.post(`/${UUID}/meeting/resume`, async (req, res) => {
        await newMeeting.resumeRecording();
        res.send("Resume");
    })

    app.listen(3000, async () => {  // OLD: Fixed port 3000
        console.log("server started");
        await newMeeting.joinMeeting();
        console.log("meeting finished");
        process.exit(0);
    })
    */
}

startProcess();