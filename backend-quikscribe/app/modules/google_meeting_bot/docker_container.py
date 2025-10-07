"""
Enhanced Docker Container Manager with Dynamic Port Support
Enables concurrent meetings by assigning unique ports to each container
"""
import docker
import random
import time
import uuid
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DockerContainerManager:
    """Manages Docker containers with dynamic port allocation for concurrent meetings."""
    
    def __init__(self):
        """Initialize Docker client and port tracking."""
        try:
            self.client = docker.from_env()
            self.used_ports = set()
            self.container_map = {}  # container_id -> meeting_info
            self.port_range = (3001, 3999)  # Port range for meeting bots
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise
    
    def get_available_port(self) -> int:
        """Get an available port in the specified range."""
        available_ports = []
        
        for port in range(self.port_range[0], self.port_range[1] + 1):
            if port not in self.used_ports:
                # Check if port is actually available on host
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    
                    if result != 0:  # Port is available
                        available_ports.append(port)
                except Exception:
                    continue
        
        if not available_ports:
            raise Exception(f"No available ports found in range {self.port_range}")
        
        # Choose a random available port for better distribution
        chosen_port = random.choice(available_ports)
        self.used_ports.add(chosen_port)
        logger.info(f"Allocated port {chosen_port} for new meeting bot")
        
        return chosen_port
    
    def start_meeting_bot(self, meeting_url: str, user_id: str, duration: int = 60) -> Dict:
        """Start a new meeting bot with dynamic port allocation."""
        
        try:
            # Generate unique identifiers
            meeting_uuid = str(uuid.uuid4())
            dynamic_port = self.get_available_port()
            container_name = f"meeting-bot-{user_id}-{int(time.time())}-{dynamic_port}"
            
            logger.info(f"Starting meeting bot: {container_name} on port {dynamic_port}")
            
            # Start container with dynamic port mapping
            container = self.client.containers.run(
                image="meeting-bot:latest",  # Your bot image name
                name=container_name,
                environment={
                    'UUID': meeting_uuid,
                    'MEETING_ID': meeting_url,
                    'USER_ID': user_id,
                    'DURATION': str(duration),
                    'DYNAMIC_PORT': str(dynamic_port)  # ✅ PASS DYNAMIC PORT
                },
                ports={f'{dynamic_port}/tcp': dynamic_port},  # ✅ MAP DYNAMIC PORT
                detach=True,
                remove=True,
                network_mode="bridge"  # Use bridge network for port mapping
            )
            
            # Store container information
            container_info = {
                'container_id': container.id,
                'container_name': container_name,
                'port': dynamic_port,
                'meeting_uuid': meeting_uuid,
                'user_id': user_id,
                'meeting_url': meeting_url,
                'status': 'starting',
                'started_at': time.time()
            }
            
            self.container_map[container.id] = container_info
            logger.info(f"Meeting bot started successfully: {container.id} on port {dynamic_port}")
            
            return container_info
            
        except Exception as e:
            logger.error(f"Failed to start meeting bot: {e}")
            # Release port if allocation failed
            if 'dynamic_port' in locals():
                self.used_ports.discard(dynamic_port)
            raise
    
    def stop_meeting_bot(self, container_id: str) -> bool:
        """Stop a specific meeting bot and release its port."""
        try:
            if container_id in self.container_map:
                container_info = self.container_map[container_id]
                port = container_info['port']
                
                # Stop the container
                container = self.client.containers.get(container_id)
                container.stop(timeout=10)
                
                # Release the port
                self.used_ports.discard(port)
                
                # Remove from tracking
                del self.container_map[container_id]
                
                logger.info(f"Meeting bot stopped: {container_id}, port {port} released")
                return True
            else:
                logger.warning(f"Container {container_id} not found in tracking map")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping meeting bot {container_id}: {e}")
            return False
    
    def get_meeting_bot_status(self, container_id: str) -> Optional[Dict]:
        """Get the status of a specific meeting bot."""
        try:
            if container_id not in self.container_map:
                return None
            
            container_info = self.container_map[container_id]
            container = self.client.containers.get(container_id)
            
            # Get container status
            container_status = container.status
            container_info['docker_status'] = container_status
            container_info['running'] = container_status == 'running'
            
            # Update status based on Docker container state
            if container_status == 'running':
                container_info['status'] = 'running'
            elif container_status == 'exited':
                container_info['status'] = 'stopped'
            elif container_status == 'created':
                container_info['status'] = 'starting'
            
            return container_info
            
        except Exception as e:
            logger.error(f"Error getting meeting bot status {container_id}: {e}")
            return None
    
    def get_all_meeting_bots(self) -> List[Dict]:
        """Get status of all meeting bots."""
        try:
            active_bots = []
            for container_id in list(self.container_map.keys()):
                status = self.get_meeting_bot_status(container_id)
                if status:
                    active_bots.append(status)
                else:
                    # Remove dead containers from tracking
                    del self.container_map[container_id]
            
            return active_bots
            
        except Exception as e:
            logger.error(f"Error getting all meeting bots: {e}")
            return []
    
    def cleanup_dead_containers(self):
        """Clean up containers that are no longer running."""
        try:
            dead_containers = []
            
            for container_id, container_info in self.container_map.items():
                try:
                    container = self.client.containers.get(container_id)
                    if container.status == 'exited':
                        dead_containers.append(container_id)
                        # Release port
                        self.used_ports.discard(container_info['port'])
                except Exception:
                    # Container no longer exists
                    dead_containers.append(container_id)
                    if container_id in self.container_map:
                        self.used_ports.discard(self.container_map[container_id]['port'])
            
            # Remove dead containers from tracking
            for container_id in dead_containers:
                if container_id in self.container_map:
                    del self.container_map[container_id]
                    logger.info(f"Cleaned up dead container: {container_id}")
            
            return len(dead_containers)
            
        except Exception as e:
            logger.error(f"Error cleaning up dead containers: {e}")
            return 0
    
    def get_port_usage_stats(self) -> Dict:
        """Get statistics about port usage."""
        return {
            'total_ports_available': self.port_range[1] - self.port_range[0] + 1,
            'ports_in_use': len(self.used_ports),
            'ports_available': (self.port_range[1] - self.port_range[0] + 1) - len(self.used_ports),
            'active_containers': len(self.container_map),
            'port_range': self.port_range
        }

# OLD CODE - COMMENTED OUT FOR REFERENCE:
"""
import asyncio
import subprocess
from pydantic import BaseModel
import logging
import sys

logger = logging.getLogger(__name__)

def run_subprocess(cmd):
    # Run a subprocess command and return stdout, stderr and return code.
    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return process.stdout, process.stderr, process.returncode
    except Exception as e:
        return "", str(e), 1

async def run_command_async(cmd):
    # Run a command asynchronously using asyncio.to_thread.
    return await asyncio.to_thread(run_subprocess, cmd)

async def check_docker_availability():
    # Check if Docker is available and running.
    try:
        stdout, stderr, returncode = await run_command_async(["docker", "--version"])
        
        if returncode == 0:
            version = stdout.strip()
            logger.info(f"Docker is available: {version}")
            return True, version
        else:
            logger.error(f"Docker version check failed: {stderr}")
            return False, stderr
    except FileNotFoundError:
        logger.error("Docker command not found. Is Docker installed?")
        return False, "Docker command not found"
    except Exception as e:
        logger.error(f"Exception checking Docker availability: {e}")
        return False, str(e)

async def check_docker_daemon():
    # Check if Docker daemon is running.
    try:
        stdout, stderr, returncode = await run_command_async(["docker", "info"])
        
        if returncode == 0:
            logger.info("Docker daemon is running")
            return True, "Docker daemon is running"
        else:
            logger.error(f"Docker daemon check failed: {stderr}")
            return False, stderr
    except Exception as e:
        logger.error(f"Exception checking Docker daemon: {e}")
        return False, str(e)

async def list_docker_images():
    # List available Docker images.
    try:
        stdout, stderr, returncode = await run_command_async(
            ["docker", "images", "--format", "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}"]
        )
        
        if returncode == 0:
            images = stdout.strip()
            logger.info(f"Available Docker images:\n{images}")
            return True, images
        else:
            logger.error(f"Failed to list Docker images: {stderr}")
            return False, stderr
    except Exception as e:
        logger.error(f"Exception listing Docker images: {e}")
        return False, str(e)

async def build_docker_image():
    # Build Docker image asynchronously.
    try:
        stdout, stderr, returncode = await run_command_async(
            ["docker", "build", "-t", "google-meeting-bot", "."]
        )
        
        if returncode == 0:
            logger.info("Docker image built successfully")
            return True
        else:
            logger.error(f"Error building Docker image: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Exception while building Docker image: {e}")
        return False

class MeetingDetails(BaseModel):
    meeting_id: str
    port: int
    name: str
    duration: int
    uuid: str
    image_name: str

async def check_image_exists(image_name: str):
    # Check if a Docker image exists, ignoring case sensitivity.
    try:
        # List all images
        stdout, stderr, returncode = await run_command_async(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"])
        
        if returncode != 0:
            logger.error(f"Failed to list Docker images: {stderr}")
            return False, None
        
        # Split the output into lines and check each line
        images = stdout.strip().split('\n')
        for image in images: # Corrected from 'lines' to 'images'
            # Compare case-insensitively
            if image.lower() == image_name.lower() or image.split(':')[0].lower() == image_name.lower():
                logger.info(f"Found matching image: {image}")
                return True, image
        
        return False, None
    except Exception as e:
        logger.error(f"Exception checking image existence: {e}")
        return False, None

async def run_docker_container(meeting_details: MeetingDetails):
    # Run Docker container asynchronously.
    try:
        logger.info(f"Attempting to start Docker container with image: {meeting_details.image_name}")
        
        # First check if Docker is running
        stdout, stderr, returncode = await run_command_async(["docker", "info"])
        
        if returncode != 0:
            logger.error(f"Docker is not running or not accessible: {stderr}")
            return None
        
        # Check if image exists (case-insensitive)
        image_exists, actual_image_name = await check_image_exists(meeting_details.image_name)
        
        if not image_exists:
            logger.error(f"Docker image '{meeting_details.image_name}' not found")
            logger.info("Available Docker images:")
            images_stdout, _, _ = await run_command_async(["docker", "images"])
            logger.info(f"Docker images:\n{images_stdout}")
            return None
        
        # Use the actual image name with correct case
        image_to_use = actual_image_name or meeting_details.image_name
        if ':' not in image_to_use:
            image_to_use = f"{image_to_use}:latest"
        
        cmd = [
            "docker", "run", "-d",  # Run in detached mode
            "-p", f"{meeting_details.port}:3000",
            "-e", f"MEETING_ID={meeting_details.meeting_id}",
            "-e", f"NAME={meeting_details.name}",
            "-e", f"DURATION={meeting_details.duration}",
            "-e", f"UUID={meeting_details.uuid}",
            "--name", f"meeting-bot-{meeting_details.uuid}",  # Container name for easy management
            image_to_use
        ]
        
        logger.info(f"Running Docker command: {' '.join(cmd)}")
        
        stdout, stderr, returncode = await run_command_async(cmd)
        
        if returncode == 0:
            container_id = stdout.strip()
            logger.info(f"Docker container started successfully: {container_id}")
            return container_id
        else:
            logger.error(f"Error running Docker container: {stderr}")
            logger.error(f"Docker command that failed: {' '.join(cmd)}")
            return None
    except Exception as e:
        logger.error(f"Exception while running Docker container: {e}", exc_info=True)
        return None

async def stop_docker_container(container_name: str):
    # Stop Docker container asynchronously.
    try:
        stdout, stderr, returncode = await run_command_async(["docker", "stop", container_name])
        
        if returncode == 0:
            logger.info(f"Docker container stopped successfully: {container_name}")
            return True
        else:
            logger.error(f"Error stopping Docker container: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Exception while stopping Docker container: {e}")
        return False

if __name__ == "__main__":
    async def test():
        meeting_details = MeetingDetails(
            meeting_id="dyv-rdph-czs", 
            name="QuikScribe Bot", 
            port=3000,
            duration=30, 
            uuid="1234567890", 
            image_name="google_meet_bot_image_v1"
        )
        await run_docker_container(meeting_details)
    
    asyncio.run(test())
""" 