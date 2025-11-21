import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.appointment import Appointment
from app.models.notification_log import NotificationLog
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, close in job functions

async def send_24h_reminders_job():
    """Job: Send 24 hour reminders"""
    db = get_db()
    try:
        logger.info("Running 24h reminder job...")

        # Get tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        # Find appointments for tomorrow that are confirmed
        appointments = db.query(Appointment).filter(
            Appointment.scheduled_date == tomorrow,
            Appointment.status == 'confirmed'
        ).all()

        logger.info(f"Found {len(appointments)} appointments for tomorrow")

        notification_service = NotificationService(db)

        for appointment in appointments:
            # Check if 24h reminder already sent
            existing = db.query(NotificationLog).filter(
                NotificationLog.appointment_id == appointment.id,
                NotificationLog.notification_type == 'reminder_24h',
                NotificationLog.status == 'sent'
            ).first()

            if existing:
                logger.info(f"24h reminder already sent for appointment {appointment.id}")
                continue

            # Send reminder
            success = await notification_service.send_reminder_24h(appointment)
            logger.info(f"24h reminder sent for appointment {appointment.id}: {success}")

        db.close()

    except Exception as e:
        logger.error(f"Error in 24h reminder job: {str(e)}")
        db.close()

async def send_1h_reminders_job():
    """Job: Send 1 hour reminders"""
    db = get_db()
    try:
        logger.info("Running 1h reminder job...")

        # Get current time + 1 hour
        now = datetime.now()
        one_hour_later = now + timedelta(hours=1)

        # Find appointments in the next hour
        today = now.date()
        appointments = db.query(Appointment).filter(
            Appointment.scheduled_date == today,
            Appointment.status == 'confirmed'
        ).all()

        # Filter by time (within next hour)
        target_appointments = []
        for apt in appointments:
            try:
                # Handle both time and string formats
                if isinstance(apt.scheduled_time, str):
                    apt_time = datetime.strptime(apt.scheduled_time, "%H:%M:%S").time()
                else:
                    apt_time = apt.scheduled_time

                apt_datetime = datetime.combine(today, apt_time)

                # Check if appointment is within the next hour
                if now <= apt_datetime <= one_hour_later:
                    target_appointments.append(apt)
            except Exception as e:
                logger.error(f"Error parsing time for appointment {apt.id}: {str(e)}")
                continue

        logger.info(f"Found {len(target_appointments)} appointments in next hour")

        notification_service = NotificationService(db)

        for appointment in target_appointments:
            # Check if 1h reminder already sent
            existing = db.query(NotificationLog).filter(
                NotificationLog.appointment_id == appointment.id,
                NotificationLog.notification_type == 'reminder_1h',
                NotificationLog.status == 'sent'
            ).first()

            if existing:
                continue

            # Send reminder
            success = await notification_service.send_reminder_1h(appointment)
            logger.info(f"1h reminder sent for appointment {appointment.id}: {success}")

        db.close()

    except Exception as e:
        logger.error(f"Error in 1h reminder job: {str(e)}")
        db.close()

async def send_thanks_job():
    """Job: Send thank you messages after completed appointments"""
    db = get_db()
    try:
        logger.info("Running thanks message job...")

        # Get yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).date()

        # Find completed appointments from yesterday
        appointments = db.query(Appointment).filter(
            Appointment.scheduled_date == yesterday,
            Appointment.status == 'completed'
        ).all()

        logger.info(f"Found {len(appointments)} completed appointments from yesterday")

        notification_service = NotificationService(db)

        for appointment in appointments:
            # Check if thanks already sent
            existing = db.query(NotificationLog).filter(
                NotificationLog.appointment_id == appointment.id,
                NotificationLog.notification_type == 'thanks',
                NotificationLog.status == 'sent'
            ).first()

            if existing:
                continue

            # Send thanks
            try:
                success = await notification_service.send_thanks(appointment)
                logger.info(f"Thanks sent for appointment {appointment.id}: {success}")
            except Exception as e:
                logger.error(f"Error sending thanks for appointment {appointment.id}: {str(e)}")

        db.close()

    except Exception as e:
        logger.error(f"Error in thanks job: {str(e)}")
        db.close()

def run_async_job(coro):
    """Helper to run async functions in scheduler"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()

def start_scheduler():
    """Start the background scheduler"""
    logger.info("Starting notification scheduler...")

    # Job 1: 24h reminders - runs every 30 minutes
    scheduler.add_job(
        func=lambda: run_async_job(send_24h_reminders_job()),
        trigger=IntervalTrigger(minutes=30),
        id='send_24h_reminders',
        name='Send 24 hour reminders',
        replace_existing=True
    )

    # Job 2: 1h reminders - runs every 10 minutes
    scheduler.add_job(
        func=lambda: run_async_job(send_1h_reminders_job()),
        trigger=IntervalTrigger(minutes=10),
        id='send_1h_reminders',
        name='Send 1 hour reminders',
        replace_existing=True
    )

    # Job 3: Thanks messages - runs once a day at 9 AM
    scheduler.add_job(
        func=lambda: run_async_job(send_thanks_job()),
        trigger='cron',
        hour=9,
        minute=0,
        id='send_thanks',
        name='Send thank you messages',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started successfully!")
    logger.info("Jobs configured:")
    logger.info("  - 24h reminders: Every 30 minutes")
    logger.info("  - 1h reminders: Every 10 minutes")
    logger.info("  - Thanks messages: Daily at 9:00 AM")

def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
