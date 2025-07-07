"""
Advanced Scheduling System for AI Socials.

This module provides comprehensive scheduling functionality using APScheduler
with job persistence, recovery, and management capabilities.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from enum import Enum

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.job import Job

from config import get_config
from utils.exceptions import (
    SchedulingError,
    handle_exception,
    retry_on_exception,
    RetryConfig
)


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MISSED = "missed"


class JobType(Enum):
    """Types of scheduled jobs."""
    CONTENT_GENERATION = "content_generation"
    INSTAGRAM_PUBLISHING = "instagram_publishing"
    CONTENT_REVIEW = "content_review"
    MAINTENANCE = "maintenance"


class ScheduledJob:
    """Represents a scheduled job with metadata."""

    def __init__(
            self,
            job_id: str,
            job_type: JobType,
            function: Callable,
            args: tuple = (),
            kwargs: Dict[str, Any] = None,
            trigger_type: str = "interval",
            trigger_args: Dict[str, Any] = None,
            metadata: Dict[str, Any] = None
    ):
        self.job_id = job_id
        self.job_type = job_type
        self.function = function
        self.args = args
        self.kwargs = kwargs or {}
        self.trigger_type = trigger_type
        self.trigger_args = trigger_args or {}
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.status = JobStatus.PENDING
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.error_count = 0
        self.last_error = None


class ContentScheduler:
    """Advanced scheduler for AI Socials."""

    def __init__(self):
        """Initialize the scheduler with configuration."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.scheduler = None
        self.jobs: Dict[str, ScheduledJob] = {}
        self.job_history: List[Dict[str, Any]] = []
        self._initialize_scheduler()

    def _initialize_scheduler(self):
        """Initialize APScheduler with proper configuration."""
        try:
            # Create data directory for job persistence
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)

            # Configure job store for persistence
            jobstores = {
                'default': SQLAlchemyJobStore(url=f'sqlite:///{data_dir}/jobs.sqlite')
            }

            # Configure executors
            executors = {
                'default': ThreadPoolExecutor(max_workers=3),
            }

            # Job defaults
            job_defaults = {
                'coalesce': True,  # Combine multiple pending executions
                'max_instances': 1,  # Only one instance of each job at a time
                'misfire_grace_time': 300  # 5 minutes grace time for missed jobs
            }

            # Create scheduler
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='UTC'
            )

            # Add event listeners
            self.scheduler.add_listener(
                self._job_executed_listener,
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED
            )

            self.logger.info("Scheduler initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize scheduler: {str(e)}")
            raise SchedulingError(
                "Failed to initialize scheduler",
                original_exception=e
            )

    def _job_executed_listener(self, event):
        """Handle job execution events."""
        job_id = event.job_id

        if job_id in self.jobs:
            scheduled_job = self.jobs[job_id]

            if event.exception:
                # Job failed
                scheduled_job.status = JobStatus.FAILED
                scheduled_job.error_count += 1
                scheduled_job.last_error = str(event.exception)

                self.logger.error(
                    f"Job {job_id} failed: {event.exception}",
                    extra={'extra_data': {
                        'job_id': job_id,
                        'job_type': scheduled_job.job_type.value,
                        'error_count': scheduled_job.error_count
                    }}
                )

                # Handle job failure
                self._handle_job_failure(scheduled_job, event.exception)

            else:
                # Job completed successfully
                scheduled_job.status = JobStatus.COMPLETED
                scheduled_job.run_count += 1
                scheduled_job.last_run = datetime.now()

                self.logger.info(
                    f"Job {job_id} completed successfully",
                    extra={'extra_data': {
                        'job_id': job_id,
                        'job_type': scheduled_job.job_type.value,
                        'run_count': scheduled_job.run_count
                    }}
                )

            # Add to history
            self.job_history.append({
                'job_id': job_id,
                'job_type': scheduled_job.job_type.value,
                'status': scheduled_job.status.value,
                'executed_at': datetime.now().isoformat(),
                'duration': getattr(event, 'duration', None),
                'exception': str(event.exception) if event.exception else None
            })

            # Keep only last 1000 history entries
            if len(self.job_history) > 1000:
                self.job_history = self.job_history[-1000:]

    def _handle_job_failure(self, scheduled_job: ScheduledJob, exception: Exception):
        """Handle job failure with retry logic."""
        max_retries = 3

        if scheduled_job.error_count <= max_retries:
            # Schedule retry with exponential backoff
            retry_delay = min(60 * (2 ** scheduled_job.error_count), 3600)  # Max 1 hour
            retry_time = datetime.now() + timedelta(seconds=retry_delay)

            self.logger.info(
                f"Scheduling retry for job {scheduled_job.job_id} in {retry_delay} seconds",
                extra={'extra_data': {
                    'job_id': scheduled_job.job_id,
                    'retry_attempt': scheduled_job.error_count,
                    'retry_time': retry_time.isoformat()
                }}
            )

            # Schedule one-time retry
            self.scheduler.add_job(
                func=scheduled_job.function,
                args=scheduled_job.args,
                kwargs=scheduled_job.kwargs,
                trigger='date',
                run_date=retry_time,
                id=f"{scheduled_job.job_id}_retry_{scheduled_job.error_count}",
                replace_existing=True
            )
        else:
            self.logger.error(
                f"Job {scheduled_job.job_id} exceeded maximum retries ({max_retries})",
                extra={'extra_data': {
                    'job_id': scheduled_job.job_id,
                    'job_type': scheduled_job.job_type.value,
                    'total_errors': scheduled_job.error_count
                }}
            )

    @log_execution_time
    def add_job(
            self,
            function: Callable,
            job_type: JobType,
            trigger_type: str = "interval",
            job_id: Optional[str] = None,
            **trigger_args
    ) -> str:
        """Add a new scheduled job.

        Args:
            function: Function to execute
            job_type: Type of job
            trigger_type: APScheduler trigger type (interval, cron, date)
            job_id: Optional custom job ID
            **trigger_args: Trigger-specific arguments

        Returns:
            Job ID

        Raises:
            SchedulingError: If job scheduling fails
        """
        try:
            if job_id is None:
                job_id = f"{job_type.value}_{uuid.uuid4().hex[:8]}"

            # Validate trigger arguments
            self._validate_trigger_args(trigger_type, trigger_args)

            # Create scheduled job
            scheduled_job = ScheduledJob(
                job_id=job_id,
                job_type=job_type,
                function=function,
                trigger_type=trigger_type,
                trigger_args=trigger_args
            )

            # Add to APScheduler
            job = self.scheduler.add_job(
                func=function,
                trigger=trigger_type,
                id=job_id,
                replace_existing=True,
                **trigger_args
            )

            # Store job metadata
            self.jobs[job_id] = scheduled_job
            scheduled_job.next_run = job.next_run_time

            self.logger.info(
                f"Job scheduled successfully: {job_id}",
                extra={'extra_data': {
                    'job_id': job_id,
                    'job_type': job_type.value,
                    'trigger_type': trigger_type,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }}
            )

            return job_id

        except Exception as e:
            self.logger.error(f"Failed to schedule job: {str(e)}")
            raise SchedulingError(
                f"Failed to schedule job: {str(e)}",
                original_exception=e
            )

    def _validate_trigger_args(self, trigger_type: str, trigger_args: Dict[str, Any]):
        """Validate trigger arguments."""
        if trigger_type == "interval":
            if not any(key in trigger_args for key in ['seconds', 'minutes', 'hours', 'days']):
                raise SchedulingError("Interval trigger requires at least one time unit")
        elif trigger_type == "cron":
            # Basic cron validation - APScheduler will do detailed validation
            pass
        elif trigger_type == "date":
            if 'run_date' not in trigger_args:
                raise SchedulingError("Date trigger requires 'run_date' argument")

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        Args:
            job_id: ID of job to remove

        Returns:
            True if job was removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]

            self.logger.info(f"Job removed: {job_id}")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to remove job {job_id}: {str(e)}")
            return False

    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a scheduled job."""
        if job_id not in self.jobs:
            return None

        scheduled_job = self.jobs[job_id]
        apscheduler_job = self.scheduler.get_job(job_id)

        return {
            'job_id': job_id,
            'job_type': scheduled_job.job_type.value,
            'status': scheduled_job.status.value,
            'created_at': scheduled_job.created_at.isoformat(),
            'last_run': scheduled_job.last_run.isoformat() if scheduled_job.last_run else None,
            'next_run': apscheduler_job.next_run_time.isoformat() if apscheduler_job and apscheduler_job.next_run_time else None,
            'run_count': scheduled_job.run_count,
            'error_count': scheduled_job.error_count,
            'last_error': scheduled_job.last_error,
            'trigger_type': scheduled_job.trigger_type,
            'trigger_args': scheduled_job.trigger_args,
            'metadata': scheduled_job.metadata
        }

    def list_jobs(self, job_type: Optional[JobType] = None) -> List[Dict[str, Any]]:
        """List all scheduled jobs, optionally filtered by type."""
        jobs = []

        for job_id, scheduled_job in self.jobs.items():
            if job_type is None or scheduled_job.job_type == job_type:
                job_info = self.get_job_info(job_id)
                if job_info:
                    jobs.append(job_info)

        return jobs

    def get_job_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get job execution history."""
        return self.job_history[-limit:]

    def start(self):
        """Start the scheduler."""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.logger.info("Scheduler started successfully")
            else:
                self.logger.warning("Scheduler is already running")

        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {str(e)}")
            raise SchedulingError(
                "Failed to start scheduler",
                original_exception=e
            )

    def stop(self, wait: bool = True):
        """Stop the scheduler."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=wait)
                self.logger.info("Scheduler stopped successfully")
            else:
                self.logger.warning("Scheduler is not running")

        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {str(e)}")
            raise SchedulingError(
                "Failed to stop scheduler",
                original_exception=e
            )

    def pause_job(self, job_id: str):
        """Pause a scheduled job."""
        try:
            self.scheduler.pause_job(job_id)
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.PENDING
            self.logger.info(f"Job paused: {job_id}")

        except Exception as e:
            self.logger.error(f"Failed to pause job {job_id}: {str(e)}")
            raise SchedulingError(f"Failed to pause job: {str(e)}")

    def resume_job(self, job_id: str):
        """Resume a paused job."""
        try:
            self.scheduler.resume_job(job_id)
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.PENDING
            self.logger.info(f"Job resumed: {job_id}")

        except Exception as e:
            self.logger.error(f"Failed to resume job {job_id}: {str(e)}")
            raise SchedulingError(f"Failed to resume job: {str(e)}")

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics."""
        return {
            'running': self.scheduler.running if self.scheduler else False,
            'total_jobs': len(self.jobs),
            'active_jobs': len([j for j in self.jobs.values() if j.status == JobStatus.PENDING]),
            'failed_jobs': len([j for j in self.jobs.values() if j.status == JobStatus.FAILED]),
            'completed_jobs': len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED]),
            'total_executions': sum(j.run_count for j in self.jobs.values()),
            'total_errors': sum(j.error_count for j in self.jobs.values()),
            'history_entries': len(self.job_history)
        }


# Global scheduler instance
_scheduler = None


def get_scheduler() -> ContentScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ContentScheduler()
    return _scheduler


# Convenience functions for common scheduling patterns
def schedule_content_generation(
        prompt: str,
        interval_hours: int = 24,
        style: str = "engaging",
        theme: Optional[str] = None
) -> str:
    """Schedule regular content generation.

    Args:
        prompt: Content generation prompt
        interval_hours: Hours between generations
        style: Caption style
        theme: Content theme

    Returns:
        Job ID
    """
    from main import AISocials

    def generate_content_job():
        app = AISocials()
        return app.generate_content(prompt=prompt, style=style, theme=theme)

    scheduler = get_scheduler()
    return scheduler.add_job(
        function=generate_content_job,
        job_type=JobType.CONTENT_GENERATION,
        trigger_type="interval",
        hours=interval_hours
    )


def schedule_instagram_publishing(
        image_path: str,
        caption: str,
        publish_time: datetime
) -> str:
    """Schedule Instagram publishing at specific time.

    Args:
        image_path: Path to image file
        caption: Post caption
        publish_time: When to publish

    Returns:
        Job ID
    """
    from main import AISocials

    def publish_job():
        app = AISocials()
        return app.publish_content(image_path=image_path, caption=caption)

    scheduler = get_scheduler()
    return scheduler.add_job(
        function=publish_job,
        job_type=JobType.INSTAGRAM_PUBLISHING,
        trigger_type="date",
        run_date=publish_time
    )
