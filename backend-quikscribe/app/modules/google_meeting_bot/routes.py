"""
Google Meeting Bot Routes with Dynamic Port Support
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
import os
import uuid as _uuid

# Kubernetes client for Job creation (no-Redis option)
try:
    from kubernetes import client as k8s_client, config as k8s_config
except Exception:  # pragma: no cover
    k8s_client = None
    k8s_config = None
import logging

from app.modules.auth.repository import get_current_user
from app.modules.google_meeting_bot.docker_container import DockerContainerManager
from app.modules.google_meeting_bot.schemas import MeetingStartRequest, MeetingResponse, MeetingStatusResponse
from app.modules.google_meeting_bot.models import User_google_meeting_data
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy-init Docker container manager to avoid startup failures when Docker isn't available in container
docker_manager: Optional[DockerContainerManager] = None

def get_docker_manager() -> DockerContainerManager:
    global docker_manager
    if docker_manager is None:
        try:
            docker_manager = DockerContainerManager()
        except Exception as e:
            logger.warning(f"Docker client unavailable: {e}")
            raise HTTPException(status_code=503, detail="Docker is not available in backend container")
    return docker_manager

@router.post("/meeting-url", response_model=MeetingResponse)
async def start_meeting_bot(
    request: MeetingStartRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new meeting bot with dynamic port allocation."""
    
    try:
        logger.info(f"Starting meeting bot for user {current_user.id} with URL: {request.meeting_url}")
        
        # Start meeting bot in Docker with dynamic port
        container_info = get_docker_manager().start_meeting_bot(
            meeting_url=request.meeting_url,
            user_id=current_user.id,
            duration=request.duration
        )
        
        # Store meeting data in database
        meeting_data = User_google_meeting_data(
            id=container_info['meeting_uuid'],
            user_id=current_user.id,
            meeting_id=container_info['meeting_uuid'],
            meeting_url=str(request.meeting_url),
            meeting_duration=request.duration,
            container_id=container_info['container_id'],
            port=container_info['port'],
            status='starting',
            bot_logs=f"Bot started on port {container_info['port']}"
        )
        
        db.add(meeting_data)
        db.commit()
        db.refresh(meeting_data)
        
        logger.info(f"Meeting bot started successfully: {container_info['container_id']} on port {container_info['port']}")
        
        return MeetingResponse(
            message="Meeting bot started successfully",
            meeting_id=container_info['meeting_uuid'],
            container_id=container_info['container_id'],
            port=container_info['port'],
            status="starting"
        )
        
    except Exception as e:
        logger.error(f"Failed to start meeting bot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start meeting bot: {str(e)}")

@router.get("/my-meetings", response_model=List[MeetingStatusResponse])
async def get_user_meetings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user's meetings with real-time status from Docker."""
    
    try:
        # Get meetings from database
        meetings = db.query(User_google_meeting_data).filter(
            User_google_meeting_data.user_id == current_user.id
        ).all()
        
        # Update status from Docker containers
        for meeting in meetings:
            if meeting.container_id:
                container_status = get_docker_manager().get_meeting_bot_status(meeting.container_id)
                if container_status:
                    meeting.status = container_status['status']
                    meeting.port = container_status['port']
                    # Update database with current status
                    db.commit()
        
        return meetings
        
    except Exception as e:
        logger.error(f"Failed to get user meetings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get meetings: {str(e)}")

@router.post("/meeting/{meeting_id}/pause")
async def pause_meeting(
    meeting_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause a specific meeting recording."""
    
    try:
        # Get meeting from database
        meeting = db.query(User_google_meeting_data).filter(
            User_google_meeting_data.id == meeting_id,
            User_google_meeting_data.user_id == current_user.id
        ).first()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.container_id:
            # Send pause command to bot via HTTP
            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"http://localhost:{meeting.port}/{meeting_id}/meeting/pause",
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        meeting.status = "paused"
                        db.commit()
                        return {"message": "Meeting paused successfully"}
                    else:
                        raise HTTPException(status_code=400, detail="Failed to pause meeting")
            except Exception as e:
                logger.error(f"Failed to pause meeting: {e}")
                raise HTTPException(status_code=500, detail="Failed to pause meeting")
        
        raise HTTPException(status_code=400, detail="Meeting bot not running")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause meeting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause meeting: {str(e)}")

@router.post("/meeting/{meeting_id}/resume")
async def resume_meeting(
    meeting_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume a specific meeting recording."""
    
    try:
        # Get meeting from database
        meeting = db.query(User_google_meeting_data).filter(
            User_google_meeting_data.id == meeting_id,
            User_google_meeting_data.user_id == current_user.id
        ).first()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.container_id:
            # Send resume command to bot via HTTP
            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"http://localhost:{meeting.port}/{meeting_id}/meeting/resume",
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        meeting.status = "running"
                        db.commit()
                        return {"message": "Meeting resumed successfully"}
                    else:
                        raise HTTPException(status_code=400, detail="Failed to resume meeting")
            except Exception as e:
                logger.error(f"Failed to resume meeting: {e}")
                raise HTTPException(status_code=500, detail="Failed to resume meeting")
        
        raise HTTPException(status_code=400, detail="Meeting bot not running")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume meeting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume meeting: {str(e)}")

@router.post("/meeting/{meeting_id}/stop")
async def stop_meeting(
    meeting_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop a specific meeting bot."""
    
    try:
        # Get meeting from database
        meeting = db.query(User_google_meeting_data).filter(
            User_google_meeting_data.id == meeting_id,
            User_google_meeting_data.user_id == current_user.id
        ).first()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting.container_id:
            # Stop Docker container
            success = get_docker_manager().stop_meeting_bot(meeting.container_id)
            if success:
                # Update database
                meeting.status = "stopped"
                meeting.container_id = None
                meeting.port = None
                db.commit()
                return {"message": "Meeting stopped successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to stop meeting bot")
        
        raise HTTPException(status_code=400, detail="Meeting bot not running")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop meeting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop meeting: {str(e)}")

@router.get("/meeting-bots/status")
async def get_meeting_bots_status(
    current_user = Depends(get_current_user)
):
    """Get status of all meeting bots (admin function)."""
    
    try:
        # Get all active meeting bots
        active_bots = get_docker_manager().get_all_meeting_bots()
        
        # Get port usage statistics
        port_stats = get_docker_manager().get_port_usage_stats()
        
        return {
            "active_bots": active_bots,
            "port_statistics": port_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get meeting bots status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/meeting-bots/cleanup")
async def cleanup_meeting_bots(
    current_user = Depends(get_current_user)
):
    """Clean up dead meeting bot containers."""
    
    try:
        cleaned_count = get_docker_manager().cleanup_dead_containers()
        return {"message": f"Cleaned up {cleaned_count} dead containers"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup meeting bots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")

# =============================
# K8s Job-based triggering (no Redis)
# =============================
from pydantic import BaseModel, Field

DEFAULT_NAMESPACE = os.getenv("JOB_NAMESPACE", "quikscribe")

def _load_k8s_config():
    if k8s_config is None:
        raise HTTPException(status_code=500, detail="Kubernetes client not available in backend image")
    try:
        try:
            k8s_config.load_incluster_config()
        except Exception:
            k8s_config.load_kube_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load Kubernetes config: {e}")

def _bot_image_from_env() -> str:
    img = os.getenv("BOT_IMAGE") or os.getenv("DOCKER_IMAGE_NAME")
    if not img or ":" not in img:
        raise HTTPException(status_code=500, detail=(
            "BOT_IMAGE not configured. Set BOT_IMAGE env to your ECR image, e.g. "
            "266735817130.dkr.ecr.us-east-1.amazonaws.com/quikscribe-google-bot:latest"
        ))
    return img

class K8sMeetingRequest(BaseModel):
    meetingId: str = Field(..., description="Google Meet ID or full URL")
    duration: int = Field(1, description="Duration in minutes")
    uuid: Optional[str] = Field(None, description="Override UUID (optional)")
    recordType: Optional[str] = Field("VIDEO", description="VIDEO or AUDIO")

class BatchRequest(BaseModel):
    count: int = Field(5, gt=0, le=100)
    baseMeetingId: str
    duration: int = 1
    recordType: Optional[str] = "VIDEO"

def _build_job_spec(meeting_id: str, uuid_val: str, duration_min: int, record_type: str, image: str):
    annotations = {"meeting/id": meeting_id, "meeting/uuid": uuid_val}

    bot_env = [
        k8s_client.V1EnvVar(name="MEETING_ID", value=str(meeting_id)),
        k8s_client.V1EnvVar(name="UUID", value=str(uuid_val)),
        k8s_client.V1EnvVar(name="RECORD_TYPE", value=str(record_type or "VIDEO")),
        k8s_client.V1EnvVar(name="DURATION", value=str(duration_min)),
        k8s_client.V1EnvVar(name="DYNAMIC_PORT", value="3000"),
        k8s_client.V1EnvVar(name="DISPLAY", value=":99.0"),
        k8s_client.V1EnvVar(name="SELENIUM_URL", value="http://localhost:4444/wd/hub"),
    ]

    volumes = [
        k8s_client.V1Volume(name="x11-socket", empty_dir=k8s_client.V1EmptyDirVolumeSource()),
        k8s_client.V1Volume(name="segments", empty_dir=k8s_client.V1EmptyDirVolumeSource()),
    ]
    mounts_bot = [
        k8s_client.V1VolumeMount(name="x11-socket", mount_path="/tmp/.X11-unix"),
        k8s_client.V1VolumeMount(name="segments", mount_path="/app/segments"),
    ]
    mounts_sel = [
        k8s_client.V1VolumeMount(name="x11-socket", mount_path="/tmp/.X11-unix"),
    ]

    bot_container = k8s_client.V1Container(
    name="worker",
    image=image,
    image_pull_policy="IfNotPresent",
    # Small delay to allow Selenium sidecar to become ready
    command=["sh", "-lc", "sleep 12; exec bun run index.ts"],
    env=bot_env,
    volume_mounts=mounts_bot,
    resources=k8s_client.V1ResourceRequirements(
        requests={"cpu": "250m", "memory": "512Mi"},
        limits={"cpu": "750m", "memory": "1.5Gi"},
    ),
)
    selenium_container = k8s_client.V1Container(
    name="selenium",
    image="selenium/standalone-chrome:123.0",
    image_pull_policy="IfNotPresent",
    env=[
        k8s_client.V1EnvVar(name="SE_OPTS", value="--session-timeout 300"),
        k8s_client.V1EnvVar(name="DISPLAY", value=":99.0"),
    ],
    ports=[k8s_client.V1ContainerPort(container_port=4444, name="selenium")],
    volume_mounts=mounts_sel,
    # Probes to ensure Selenium is really up before the worker starts using it
    startup_probe=k8s_client.V1Probe(
        http_get=k8s_client.V1HTTPGetAction(path="/status", port=4444),
        initial_delay_seconds=3,
        period_seconds=5,
        timeout_seconds=3,
        failure_threshold=24,  # up to ~2 minutes
    ),
    readiness_probe=k8s_client.V1Probe(
        http_get=k8s_client.V1HTTPGetAction(path="/status", port=4444),
        initial_delay_seconds=5,
        period_seconds=5,
        timeout_seconds=3,
        failure_threshold=6,
    ),
    resources=k8s_client.V1ResourceRequirements(
        requests={"cpu": "500m", "memory": "512Mi"},
        limits={"cpu": "1500m", "memory": "2Gi"},
    ),
)

    pod_spec = k8s_client.V1PodSpec(
        restart_policy="Never",
        containers=[bot_container, selenium_container],
        volumes=volumes,
    )

    pod_meta = k8s_client.V1ObjectMeta(
        name=f"bot-{uuid_val[:8]}",
        labels={"app": "quikscribe-job-bot"},
        annotations=annotations,
    )

    template = k8s_client.V1PodTemplateSpec(metadata=pod_meta, spec=pod_spec)
    job_spec = k8s_client.V1JobSpec(template=template, backoff_limit=0, ttl_seconds_after_finished=1800)
    job_meta = k8s_client.V1ObjectMeta(name=f"bot-job-{uuid_val[:8]}", labels={"app": "quikscribe-job-bot"})
    job = k8s_client.V1Job(api_version="batch/v1", kind="Job", metadata=job_meta, spec=job_spec)
    return job

@router.post("/k8s/meeting")
async def start_meeting_job(payload: K8sMeetingRequest, current_user = Depends(get_current_user)):
    """Create a Kubernetes Job that launches one meeting bot (no Redis)."""
    _load_k8s_config()
    batch = k8s_client.BatchV1Api()
    namespace = DEFAULT_NAMESPACE
    image = _bot_image_from_env()

    uuid_val = payload.uuid or str(_uuid.uuid4())
    job = _build_job_spec(
        meeting_id=payload.meetingId,
        uuid_val=uuid_val,
        duration_min=int(payload.duration or 1),
        record_type=(payload.recordType or "VIDEO"),
        image=image,
    )

    try:
        resp = batch.create_namespaced_job(namespace=namespace, body=job)
        return {"message": "job created", "job": resp.metadata.name, "uuid": uuid_val}
    except Exception as e:
        logger.exception("Failed to create job")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {e}")

@router.post("/k8s/meetings/batch")
async def start_batch_jobs(payload: BatchRequest, current_user = Depends(get_current_user)):
    """Create N jobs for the same meeting template (demo concurrency)."""
    _load_k8s_config()
    batch = k8s_client.BatchV1Api()
    namespace = DEFAULT_NAMESPACE
    image = _bot_image_from_env()

    created = []
    for _ in range(int(payload.count)):
        uuid_val = str(_uuid.uuid4())
        job = _build_job_spec(
            meeting_id=payload.baseMeetingId,
            uuid_val=uuid_val,
            duration_min=int(payload.duration or 1),
            record_type=(payload.recordType or "VIDEO"),
            image=image,
        )
        try:
            resp = batch.create_namespaced_job(namespace=namespace, body=job)
            created.append(resp.metadata.name)
        except Exception as e:
            logger.error(f"Failed to create one job: {e}")
    return {"message": "batch created", "count": len(created), "jobs": created}

# OLD CODE - COMMENTED OUT FOR REFERENCE:
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import logging
from app.modules.google_meeting_bot.docker_container import run_docker_container, MeetingDetails
from app.modules.google_meeting_bot.models import User_google_meeting_data
from app.core.database import get_db
from typing import Optional
from app.modules.auth.models import User
from app.modules.auth.repository import get_current_active_user
import uuid
from app.core.config import get_settings
from sqlalchemy.orm import Session
import socket

api_router = APIRouter()
logger = logging.getLogger(__name__)

# Dynamic port range for better scalability
PORT_RANGE_START = 3000
PORT_RANGE_END = 4000  # Supports up to 1000 concurrent meetings

def get_open_port() -> Optional[int]:
    # Get an available port from the dynamic range.
    for port in range(PORT_RANGE_START, PORT_RANGE_END):
        if not is_port_in_use(port):
            return port
    return None

def is_port_in_use(port: int) -> bool:
    # Check if a port is currently in use.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_port_from_database(db: Session) -> Optional[int]:
    # Get an available port that's not already assigned in database.
    # Get all active ports from database
    active_meetings = db.query(User_google_meeting_data).filter(
        User_google_meeting_data.status == "active"
    ).all()
    used_ports = {meeting.port for meeting in active_meetings if meeting.port is not None}
    
    # Find available port not in database and not in system use
    for port in range(PORT_RANGE_START, PORT_RANGE_END):
        if port not in used_ports and not is_port_in_use(port):
            return port
    return None

class MeetingRequest(BaseModel):
    meeting_url: str
    duration: Optional[int] = 30

class MeetingResponse(BaseModel):
    message: str
    meeting_id: str
    container_id: Optional[str] = None
    port: Optional[int] = None

@api_router.post("/meeting-url", response_model=MeetingResponse)
async def submit_meeting_url(
    meeting_details: MeetingRequest, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Submit a meeting URL to start the bot.
    # Requires authentication.
    try:
        logger.info(f"User {current_user.username} submitted meeting URL: {meeting_details.meeting_url}")
        
        # Extract meeting ID from URL
        meeting_id = meeting_details.meeting_url.split("/")[-1]
        if not meeting_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting URL format"
            )
        
        # Generate unique meeting UUID
        uuid_meeting = str(uuid.uuid4())
        
        # Get available port using database-aware method
        available_port = get_port_from_database(db)
        if available_port is None:
            # Fallback to basic port check
            available_port = get_open_port()
            if available_port is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="No available ports for meeting bot"
                )
        
        # Set default duration if not provided
        duration = meeting_details.duration or 30
        
        # Prepare meeting details for Docker
        meeting_details_docker = MeetingDetails(
            meeting_id=meeting_id,
            port=available_port,
            name=str(current_user.username),
            duration=duration,
            uuid=uuid_meeting,
            image_name=get_settings().docker_image_name
        )
        
        # Start Docker container
        container_id = await run_docker_container(meeting_details_docker)
        if container_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start meeting bot container"
            )
        
        # Save meeting data to database
        user_google_meeting_data = User_google_meeting_data(
            id=uuid_meeting,
            user_id=current_user.id,
            meeting_id=meeting_id,
            meeting_url=meeting_details.meeting_url,
            meeting_duration=duration,
            container_id=container_id,
            port=available_port,
            status="active"
        )
        
        db.add(user_google_meeting_data)
        db.commit()
        db.refresh(user_google_meeting_data)
        
        logger.info(f"Meeting bot started successfully for user {current_user.username}")
        
        return MeetingResponse(
            message="Meeting bot started successfully",
            meeting_id=uuid_meeting,
            container_id=container_id,
            port=available_port
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing meeting URL: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing meeting URL"
        )

@api_router.get("/my-meetings")
async def get_my_meetings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get all meetings for the current user.
    meetings = db.query(User_google_meeting_data).filter(
        User_google_meeting_data.user_id == current_user.id
    ).all()
    
    return {
        "meetings": meetings,
        "count": len(meetings)
    }

@api_router.post("/meeting/{meeting_uuid}/pause")
async def pause_meeting(
    meeting_uuid: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Pause a meeting recording.
    # Get meeting details
    meeting = db.query(User_google_meeting_data).filter(
        User_google_meeting_data.id == meeting_uuid,
        User_google_meeting_data.user_id == current_user.id,
        User_google_meeting_data.status == "active"
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or not active"
        )
    
    try:
        # Make HTTP request to container's pause endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:{meeting.port}/{meeting_uuid}/meeting/pause",
                timeout=10.0
            )
            if response.status_code == 200:
                return {"message": "Meeting paused successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to pause meeting"
                )
    except Exception as e:
        logger.error(f"Error pausing meeting {meeting_uuid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error communicating with meeting bot"
        )

@api_router.post("/meeting/{meeting_uuid}/resume")
async def resume_meeting(
    meeting_uuid: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Resume a meeting recording.
    # Get meeting details
    meeting = db.query(User_google_meeting_data).filter(
        User_google_meeting_data.id == meeting_uuid,
        User_google_meeting_data.user_id == current_user.id,
        User_google_meeting_data.status == "active"
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or not active"
        )
    
    try:
        # Make HTTP request to container's resume endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:{meeting.port}/{meeting_uuid}/meeting/resume",
                timeout=10.0
            )
            if response.status_code == 200:
                return {"message": "Meeting resumed successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to resume meeting"
                )
    except Exception as e:
        logger.error(f"Error resuming meeting {meeting_uuid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error communicating with meeting bot"
        )

@api_router.post("/meeting/{meeting_uuid}/stop")
async def stop_meeting(
    meeting_uuid: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Stop a meeting recording.
    from app.modules.google_meeting_bot.docker_container import stop_docker_container
    
    # Get meeting details
    meeting = db.query(User_google_meeting_data).filter(
        User_google_meeting_data.id == meeting_uuid,
        User_google_meeting_data.user_id == current_user.id,
        User_google_meeting_data.status == "active"
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found or not active"
        )
    
    try:
        # Stop the Docker container
        container_name = f"meeting-bot-{meeting_uuid}"
        success = await stop_docker_container(container_name)
        
        if success:
            # Update meeting status in database
            db.query(User_google_meeting_data).filter(
                User_google_meeting_data.id == meeting_uuid
            ).update({"status": "stopped"})
            db.commit()
            return {"message": "Meeting stopped successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop meeting container"
            )
    except Exception as e:
        logger.error(f"Error stopping meeting {meeting_uuid}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error stopping meeting"
        )
"""
