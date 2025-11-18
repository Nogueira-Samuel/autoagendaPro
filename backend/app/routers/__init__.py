"""
API Routers Package

REST API endpoints for AutoAgenda Pro:
- webhooks: WhatsApp message webhooks from Evolution API
- appointments: Appointment CRUD operations
- customers: Customer management
- auth: Authentication and authorization

All routers are multi-tenant aware and use async/await patterns.
"""

from app.routers import webhooks, appointments, customers, auth

__all__ = ["webhooks", "appointments", "customers", "auth"]
