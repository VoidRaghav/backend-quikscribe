#!/usr/bin/env python3
"""
Test script to demonstrate dynamic port allocation for concurrent meetings
"""
import time
import threading
from app.modules.google_meeting_bot.docker_container import DockerContainerManager

def test_concurrent_meetings():
    """Test starting multiple meeting bots concurrently."""
    
    print("🚀 Testing Dynamic Port Allocation for Concurrent Meetings")
    print("=" * 60)
    
    # Initialize Docker manager
    try:
        docker_manager = DockerContainerManager()
        print("✅ Docker manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Docker manager: {e}")
        return
    
    # Test data
    test_meetings = [
        {"user_id": "user1", "meeting_url": "https://meet.google.com/abc-def-ghi", "duration": 30},
        {"user_id": "user2", "meeting_url": "https://meet.google.com/jkl-mno-pqr", "duration": 45},
        {"user_id": "user3", "meeting_url": "https://meet.google.com/stu-vwx-yz", "duration": 60},
        {"user_id": "user4", "meeting_url": "https://meet.google.com/123-456-789", "duration": 90},
    ]
    
    def start_meeting_bot(meeting_data):
        """Start a meeting bot in a separate thread."""
        try:
            print(f"🔄 Starting meeting bot for user {meeting_data['user_id']}...")
            
            container_info = docker_manager.start_meeting_bot(
                meeting_url=meeting_data['meeting_url'],
                user_id=meeting_data['user_id'],
                duration=meeting_data['duration']
            )
            
            print(f"✅ Meeting bot started for {meeting_data['user_id']}:")
            print(f"   Container ID: {container_info['container_id'][:12]}...")
            print(f"   Port: {container_info['port']}")
            print(f"   Status: {container_info['status']}")
            
            return container_info
            
        except Exception as e:
            print(f"❌ Failed to start meeting bot for {meeting_data['user_id']}: {e}")
            return None
    
    # Start all meeting bots concurrently
    print("\n🔄 Starting all meeting bots concurrently...")
    threads = []
    results = []
    
    for meeting_data in test_meetings:
        thread = threading.Thread(target=lambda m=meeting_data: results.append(start_meeting_bot(m)))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Display results
    print("\n📊 Results Summary:")
    print("=" * 40)
    
    successful_starts = [r for r in results if r is not None]
    failed_starts = len(test_meetings) - len(successful_starts)
    
    print(f"✅ Successful starts: {len(successful_starts)}")
    print(f"❌ Failed starts: {failed_starts}")
    
    if successful_starts:
        print("\n🔍 Container Details:")
        for result in successful_starts:
            print(f"   User: {result['user_id']}")
            print(f"   Port: {result['port']}")
            print(f"   Container: {result['container_id'][:12]}...")
            print(f"   Status: {result['status']}")
            print()
    
    # Show port usage statistics
    print("📈 Port Usage Statistics:")
    stats = docker_manager.get_port_usage_stats()
    print(f"   Total ports available: {stats['total_ports_available']}")
    print(f"   Ports in use: {stats['ports_in_use']}")
    print(f"   Ports available: {stats['ports_available']}")
    print(f"   Active containers: {stats['active_containers']}")
    print(f"   Port range: {stats['port_range']}")
    
    # Cleanup after a delay
    print("\n⏳ Waiting 10 seconds before cleanup...")
    time.sleep(10)
    
    print("\n🧹 Cleaning up containers...")
    for result in successful_starts:
        if result and result['container_id']:
            try:
                success = docker_manager.stop_meeting_bot(result['container_id'])
                if success:
                    print(f"✅ Stopped container for {result['user_id']}")
                else:
                    print(f"❌ Failed to stop container for {result['user_id']}")
            except Exception as e:
                print(f"❌ Error stopping container for {result['user_id']}: {e}")
    
    # Final statistics
    print("\n📊 Final Port Usage Statistics:")
    final_stats = docker_manager.get_port_usage_stats()
    print(f"   Ports in use: {final_stats['ports_in_use']}")
    print(f"   Active containers: {final_stats['active_containers']}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_concurrent_meetings()
