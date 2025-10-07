#!/usr/bin/env python3
"""
Concurrency Test Script for QuikScribe Google Bot
Tests multiple concurrent meetings to verify scalability
"""

import asyncio
import aiohttp
import time
import json
import random
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConcurrencyTester:
    def __init__(self, base_url: str = "http://localhost:3000", max_concurrent: int = 10):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.coordinator_url = f"{base_url}/api/coordinator"
        self.active_meetings = []
        self.results = []
        
    async def start_meeting(self, session: aiohttp.ClientSession, meeting_id: str, uuid: str) -> Dict:
        """Start a single meeting"""
        try:
            payload = {
                "meetingId": meeting_id,
                "uuid": uuid,
                "duration": random.randint(1, 5),  # Random duration 1-5 minutes
                "recordType": random.choice(["AUDIO", "VIDEO"])
            }
            
            start_time = time.time()
            async with session.post(f"{self.coordinator_url}/meeting/start", json=payload) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Meeting {meeting_id} started on port {result.get('port')}")
                    return {
                        "meeting_id": meeting_id,
                        "status": "started",
                        "port": result.get('port'),
                        "response_time": response_time,
                        "success": True
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to start meeting {meeting_id}: {response.status} - {error_text}")
                    return {
                        "meeting_id": meeting_id,
                        "status": "failed",
                        "error": error_text,
                        "response_time": response_time,
                        "success": False
                    }
                    
        except Exception as e:
            logger.error(f"❌ Exception starting meeting {meeting_id}: {str(e)}")
            return {
                "meeting_id": meeting_id,
                "status": "exception",
                "error": str(e),
                "success": False
            }
    
    async def stop_meeting(self, session: aiohttp.ClientSession, meeting_id: str) -> Dict:
        """Stop a single meeting"""
        try:
            start_time = time.time()
            async with session.post(f"{self.coordinator_url}/meeting/stop", json={"meetingId": meeting_id}) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"🛑 Meeting {meeting_id} stopped")
                    return {
                        "meeting_id": meeting_id,
                        "status": "stopped",
                        "response_time": response_time,
                        "success": True
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to stop meeting {meeting_id}: {response.status} - {error_text}")
                    return {
                        "meeting_id": meeting_id,
                        "status": "stop_failed",
                        "error": error_text,
                        "response_time": response_time,
                        "success": False
                    }
                    
        except Exception as e:
            logger.error(f"❌ Exception stopping meeting {meeting_id}: {str(e)}")
            return {
                "meeting_id": meeting_id,
                "status": "stop_exception",
                "error": str(e),
                "success": False
            }
    
    async def get_meeting_status(self, session: aiohttp.ClientSession, meeting_id: str) -> Dict:
        """Get status of a single meeting"""
        try:
            async with session.get(f"{self.coordinator_url}/meeting/{meeting_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "meeting_id": meeting_id,
                        "status": "active",
                        "port": result.get('port'),
                        "uptime": result.get('uptime'),
                        "success": True
                    }
                else:
                    return {
                        "meeting_id": meeting_id,
                        "status": "not_found",
                        "success": False
                    }
        except Exception as e:
            return {
                "meeting_id": meeting_id,
                "status": "status_error",
                "error": str(e),
                "success": False
            }
    
    async def get_all_meetings(self, session: aiohttp.ClientSession) -> Dict:
        """Get status of all active meetings"""
        try:
            async with session.get(f"{self.coordinator_url}/meetings") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Failed to get meetings: {response.status}"}
        except Exception as e:
            return {"error": f"Exception getting meetings: {str(e)}"}
    
    async def run_concurrency_test(self, num_meetings: int, delay_between: float = 0.5):
        """Run the main concurrency test"""
        logger.info(f"🚀 Starting concurrency test with {num_meetings} meetings")
        logger.info(f"📊 Max concurrent meetings: {self.max_concurrent}")
        logger.info(f"⏱️  Delay between starts: {delay_between}s")
        
        async with aiohttp.ClientSession() as session:
            # Test 1: Start meetings sequentially
            logger.info("\n📈 Phase 1: Starting meetings sequentially...")
            start_tasks = []
            
            for i in range(num_meetings):
                meeting_id = f"test-meeting-{i+1:03d}"
                uuid = f"test-uuid-{i+1:03d}"
                
                task = asyncio.create_task(self.start_meeting(session, meeting_id, uuid))
                start_tasks.append(task)
                
                # Add delay between starts
                if i < num_meetings - 1:
                    await asyncio.sleep(delay_between)
            
            # Wait for all meetings to start
            start_results = await asyncio.gather(*start_tasks)
            successful_starts = [r for r in start_results if r['success']]
            
            logger.info(f"✅ Successfully started {len(successful_starts)} out of {num_meetings} meetings")
            
            # Test 2: Check all meetings status
            logger.info("\n🔍 Phase 2: Checking meeting statuses...")
            status_tasks = []
            for result in successful_starts:
                if result['success']:
                    task = asyncio.create_task(self.get_meeting_status(session, result['meeting_id']))
                    status_tasks.append(task)
            
            if status_tasks:
                status_results = await asyncio.gather(*status_tasks)
                active_meetings = [r for r in status_results if r['success']]
                logger.info(f"📊 {len(active_meetings)} meetings are currently active")
            
            # Test 3: Get overall system status
            logger.info("\n📊 Phase 3: Getting system status...")
            system_status = await self.get_all_meetings(session)
            if 'error' not in system_status:
                logger.info(f"📈 System Status: {json.dumps(system_status, indent=2)}")
            
            # Test 4: Stop all meetings
            logger.info("\n🛑 Phase 4: Stopping all meetings...")
            stop_tasks = []
            for result in successful_starts:
                if result['success']:
                    task = asyncio.create_task(self.stop_meeting(session, result['meeting_id']))
                    stop_tasks.append(task)
            
            if stop_tasks:
                stop_results = await asyncio.gather(*stop_tasks)
                successful_stops = [r for r in stop_results if r['success']]
                logger.info(f"🛑 Successfully stopped {len(successful_stops)} meetings")
            
            # Store results
            self.results = {
                "test_config": {
                    "num_meetings": num_meetings,
                    "max_concurrent": self.max_concurrent,
                    "delay_between": delay_between
                },
                "start_results": start_results,
                "status_results": status_results if 'status_results' in locals() else [],
                "stop_results": stop_results if 'stop_results' in locals() else [],
                "system_status": system_status
            }
            
            return self.results
    
    def print_summary(self):
        """Print a summary of test results"""
        if not self.results:
            logger.warning("No test results to summarize")
            return
        
        config = self.results["test_config"]
        start_results = self.results["start_results"]
        stop_results = self.results["stop_results"]
        
        successful_starts = [r for r in start_results if r['success']]
        successful_stops = [r for r in stop_results if r['success']]
        
        # Calculate statistics
        avg_start_time = sum(r['response_time'] for r in successful_starts) / len(successful_starts) if successful_starts else 0
        avg_stop_time = sum(r['response_time'] for r in successful_stops) / len(successful_stops) if successful_stops else 0
        
        logger.info("\n" + "="*60)
        logger.info("📊 CONCURRENCY TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"🎯 Test Configuration:")
        logger.info(f"   • Total meetings: {config['num_meetings']}")
        logger.info(f"   • Max concurrent: {config['max_concurrent']}")
        logger.info(f"   • Delay between starts: {config['delay_between']}s")
        logger.info("")
        logger.info(f"📈 Results:")
        logger.info(f"   • Meetings started: {len(successful_starts)}/{len(start_results)} ({len(successful_starts)/len(start_results)*100:.1f}%)")
        logger.info(f"   • Meetings stopped: {len(successful_stops)}/{len(stop_results)} ({len(successful_stops)/len(stop_results)*100:.1f}%)")
        logger.info(f"   • Average start time: {avg_start_time:.3f}s")
        logger.info(f"   • Average stop time: {avg_stop_time:.3f}s")
        logger.info("")
        
        if successful_starts:
            ports_used = [r['port'] for r in successful_starts if 'port' in r]
            logger.info(f"🔌 Ports used: {sorted(ports_used)}")
        
        logger.info("="*60)

async def main():
    """Main test function"""
    logger.info("🧪 QuikScribe Concurrency Test")
    logger.info("Make sure your Docker services are running first!")
    
    # Create tester instance
    tester = ConcurrencyTester(max_concurrent=10)
    
    try:
        # Run the test
        await tester.run_concurrency_test(
            num_meetings=8,  # Test with 8 meetings
            delay_between=0.5  # 0.5 second delay between starts
        )
        
        # Print summary
        tester.print_summary()
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        logger.error("Make sure your Docker services are running and accessible")

if __name__ == "__main__":
    asyncio.run(main())
