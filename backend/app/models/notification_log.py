from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    recipient_type = Column(String(20), nullable=False)  # 'customer' or 'owner'
    recipient_phone = Column(String(20), nullable=False)
    notification_type = Column(String(50), nullable=False)  # 'confirmation', 'reminder_24h', etc
    message_text = Column(Text, nullable=False)
    status = Column(String(20), default='pending')  # 'sent', 'failed', 'pending'
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="notification_logs")
    appointment = relationship("Appointment", back_populates="notification_logs")
