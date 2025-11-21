import httpx
import logging
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.notification_log import NotificationLog
from app.models.appointment import Appointment
from app.models.customer import Customer
from app.models.business_config import BusinessConfig
from app.core.templates import MessageTemplates
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via WhatsApp"""

    def __init__(self, db: Session):
        self.db = db
        self.evolution_url = settings.EVOLUTION_API_URL
        self.evolution_key = settings.EVOLUTION_API_KEY

    async def send_whatsapp(self, instance: str, phone: str, message: str) -> bool:
        """Send WhatsApp message via Evolution API"""
        try:
            url = f"{self.evolution_url}/message/sendText/{instance}"
            headers = {
                "apikey": self.evolution_key,
                "Content-Type": "application/json"
            }
            data = {
                "number": phone,
                "text": message
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=30)

                if response.status_code == 200:
                    logger.info(f"WhatsApp sent successfully to {phone}")
                    return True
                else:
                    logger.error(f"WhatsApp send failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending WhatsApp: {str(e)}")
            return False

    def log_notification(
        self,
        tenant_id: int,
        appointment_id: Optional[int],
        recipient_type: str,
        recipient_phone: str,
        notification_type: str,
        message_text: str,
        status: str = 'pending',
        error_message: Optional[str] = None
    ) -> NotificationLog:
        """Log notification attempt"""
        log = NotificationLog(
            tenant_id=tenant_id,
            appointment_id=appointment_id,
            recipient_type=recipient_type,
            recipient_phone=recipient_phone,
            notification_type=notification_type,
            message_text=message_text,
            status=status,
            sent_at=datetime.utcnow() if status == 'sent' else None,
            error_message=error_message
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    async def send_confirmation(self, appointment: Appointment) -> bool:
        """Send appointment confirmation"""
        try:
            # Get business config for custom template
            config = self.db.query(BusinessConfig).filter(
                BusinessConfig.tenant_id == appointment.tenant_id
            ).first()

            # Prepare data
            data = {
                'customer_name': appointment.customer.name,
                'date': str(appointment.scheduled_date),
                'time': str(appointment.scheduled_time),
                'service': appointment.service.name,
                'price': str(appointment.service.price),
                'business_name': appointment.tenant.name,
                'template': config.confirmation_message_template if config and hasattr(config, 'confirmation_message_template') else None
            }

            # Generate message
            message = MessageTemplates.confirmation(data)

            # Send to customer
            instance = appointment.tenant.evolution_instance_name or f"tenant_{appointment.tenant_id}"
            success = await self.send_whatsapp(
                instance,
                appointment.customer.phone,
                message
            )

            # Log
            self.log_notification(
                tenant_id=appointment.tenant_id,
                appointment_id=appointment.id,
                recipient_type='customer',
                recipient_phone=appointment.customer.phone,
                notification_type='confirmation',
                message_text=message,
                status='sent' if success else 'failed',
                error_message=None if success else 'Failed to send'
            )

            # Send to owner if configured
            if config and hasattr(config, 'notify_owner') and config.notify_owner:
                owner_data = {
                    'type': 'new',
                    'customer_name': appointment.customer.name,
                    'customer_phone': appointment.customer.phone,
                    'date': str(appointment.scheduled_date),
                    'time': str(appointment.scheduled_time),
                    'service': appointment.service.name
                }
                owner_message = MessageTemplates.owner_notification(owner_data)

                # Get owner phone from first admin user
                from app.models.user import User
                owner = self.db.query(User).filter(
                    User.tenant_id == appointment.tenant_id,
                    User.role == 'admin'
                ).first()

                if owner and hasattr(owner, 'phone') and owner.phone:
                    await self.send_whatsapp(instance, owner.phone, owner_message)

            return success

        except Exception as e:
            logger.error(f"Error sending confirmation: {str(e)}")
            return False

    async def send_reminder_24h(self, appointment: Appointment) -> bool:
        """Send 24 hour reminder"""
        try:
            config = self.db.query(BusinessConfig).filter(
                BusinessConfig.tenant_id == appointment.tenant_id
            ).first()

            data = {
                'customer_name': appointment.customer.name,
                'date': str(appointment.scheduled_date),
                'time': str(appointment.scheduled_time),
                'service': appointment.service.name,
                'business_name': appointment.tenant.name,
                'template': config.reminder_message_template if config and hasattr(config, 'reminder_message_template') else None
            }

            message = MessageTemplates.reminder_24h(data)
            instance = appointment.tenant.evolution_instance_name or f"tenant_{appointment.tenant_id}"
            success = await self.send_whatsapp(
                instance,
                appointment.customer.phone,
                message
            )

            self.log_notification(
                tenant_id=appointment.tenant_id,
                appointment_id=appointment.id,
                recipient_type='customer',
                recipient_phone=appointment.customer.phone,
                notification_type='reminder_24h',
                message_text=message,
                status='sent' if success else 'failed'
            )

            return success

        except Exception as e:
            logger.error(f"Error sending 24h reminder: {str(e)}")
            return False

    async def send_reminder_1h(self, appointment: Appointment) -> bool:
        """Send 1 hour reminder"""
        try:
            data = {
                'customer_name': appointment.customer.name,
                'time': str(appointment.scheduled_time),
                'service': appointment.service.name,
                'business_name': appointment.tenant.name
            }

            message = MessageTemplates.reminder_1h(data)
            instance = appointment.tenant.evolution_instance_name or f"tenant_{appointment.tenant_id}"
            success = await self.send_whatsapp(
                instance,
                appointment.customer.phone,
                message
            )

            self.log_notification(
                tenant_id=appointment.tenant_id,
                appointment_id=appointment.id,
                recipient_type='customer',
                recipient_phone=appointment.customer.phone,
                notification_type='reminder_1h',
                message_text=message,
                status='sent' if success else 'failed'
            )

            return success

        except Exception as e:
            logger.error(f"Error sending 1h reminder: {str(e)}")
            return False

    async def send_cancellation(self, appointment: Appointment) -> bool:
        """Send cancellation confirmation"""
        try:
            data = {
                'customer_name': appointment.customer.name,
                'date': str(appointment.scheduled_date),
                'time': str(appointment.scheduled_time),
                'business_name': appointment.tenant.name
            }

            message = MessageTemplates.cancellation(data)
            instance = appointment.tenant.evolution_instance_name or f"tenant_{appointment.tenant_id}"
            success = await self.send_whatsapp(
                instance,
                appointment.customer.phone,
                message
            )

            self.log_notification(
                tenant_id=appointment.tenant_id,
                appointment_id=appointment.id,
                recipient_type='customer',
                recipient_phone=appointment.customer.phone,
                notification_type='cancellation',
                message_text=message,
                status='sent' if success else 'failed'
            )

            return success

        except Exception as e:
            logger.error(f"Error sending cancellation: {str(e)}")
            return False

    async def send_thanks(self, appointment: Appointment) -> bool:
        """Send thank you message after appointment"""
        try:
            data = {
                'customer_name': appointment.customer.name,
                'business_name': appointment.tenant.name
            }

            message = MessageTemplates.thanks(data)
            instance = appointment.tenant.evolution_instance_name or f"tenant_{appointment.tenant_id}"
            success = await self.send_whatsapp(
                instance,
                appointment.customer.phone,
                message
            )

            self.log_notification(
                tenant_id=appointment.tenant_id,
                appointment_id=appointment.id,
                recipient_type='customer',
                recipient_phone=appointment.customer.phone,
                notification_type='thanks',
                message_text=message,
                status='sent' if success else 'failed'
            )

            return success

        except Exception as e:
            logger.error(f"Error sending thanks message: {str(e)}")
            return False
