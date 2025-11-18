"""
Seed Initial Data

Populates database with initial test/development data.

Usage:
    python -m database.seeds.initial_data

This creates:
- Test tenant (Clínica Exemplo)
- Admin user (admin@clinica-exemplo.com / admin123)
- Business configuration with default hours
- Sample services (Consulta, Exame, Retorno)
"""

import asyncio
import sys
from datetime import date, time
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import DatabaseManager
from app.models import Tenant, User, BusinessConfig, Service
from app.utils.auth import get_password_hash


async def seed_data() -> None:
    """
    Seed initial data for development/testing.

    Creates:
    - 1 test tenant
    - 1 admin user
    - 1 business config
    - 3 sample services
    """

    print("🌱 Starting database seeding...")
    print("=" * 50)

    # Get database session
    session_factory = DatabaseManager.get_session_factory()

    async with session_factory() as db:
        try:
            # 1. Create test tenant
            print("\n📦 Creating test tenant...")
            tenant = Tenant(
                name="Clínica Exemplo",
                slug="clinica-exemplo",
                is_active=True,
                plan="free",
                timezone="America/Sao_Paulo",
                # Note: Add real credentials for full functionality
                google_calendar_credentials=None,
                google_calendar_id=None,
                evolution_instance_name="clinica-exemplo-test",
                evolution_api_key=None,
            )
            db.add(tenant)
            await db.flush()  # Get tenant ID

            print(f"   ✓ Tenant created: {tenant.name} (ID: {tenant.id})")

            # 2. Create admin user
            print("\n👤 Creating admin user...")
            admin = User(
                tenant_id=tenant.id,
                email="admin@clinica-exemplo.com",
                password_hash=get_password_hash("admin123"),
                full_name="Admin Clínica",
                role="admin",
                is_active=True,
            )
            db.add(admin)

            print(f"   ✓ User created: {admin.email}")

            # 3. Create business config
            print("\n⚙️  Creating business configuration...")
            config = BusinessConfig(
                tenant_id=tenant.id,
                business_hours={
                    "monday": {"open": "09:00", "close": "18:00", "is_open": True},
                    "tuesday": {"open": "09:00", "close": "18:00", "is_open": True},
                    "wednesday": {"open": "09:00", "close": "18:00", "is_open": True},
                    "thursday": {"open": "09:00", "close": "18:00", "is_open": True},
                    "friday": {"open": "09:00", "close": "18:00", "is_open": True},
                    "saturday": {"open": "09:00", "close": "13:00", "is_open": True},
                    "sunday": {"open": "00:00", "close": "00:00", "is_open": False},
                },
                default_appointment_duration=60,
                buffer_time=15,
                max_advance_booking_days=30,
                auto_confirm_appointments=False,
                send_reminders=True,
                reminder_hours_before=24,
                cancellation_hours_before=2,
                welcome_message="Olá! Bem-vindo à Clínica Exemplo. Como posso ajudar?",
                confirmation_message_template="Seu agendamento está confirmado para {date} às {time}. Serviço: {service}.",
                reminder_message_template="Lembrete: Você tem consulta amanhã às {time}. Nos vemos lá!",
                cancellation_message_template="Seu agendamento foi cancelado. Se precisar, estamos à disposição.",
            )
            db.add(config)

            print("   ✓ Business config created")
            print("     - Hours: Mon-Fri 9:00-18:00, Sat 9:00-13:00, Sun closed")
            print("     - Default duration: 60 minutes")
            print("     - Buffer time: 15 minutes")

            # 4. Create sample services
            print("\n🏥 Creating sample services...")
            services = [
                Service(
                    tenant_id=tenant.id,
                    name="Consulta",
                    description="Consulta médica geral",
                    duration_minutes=60,
                    price=150.00,
                    is_active=True,
                    color="#3B82F6",  # Blue
                ),
                Service(
                    tenant_id=tenant.id,
                    name="Exame",
                    description="Exames laboratoriais",
                    duration_minutes=30,
                    price=80.00,
                    is_active=True,
                    color="#10B981",  # Green
                ),
                Service(
                    tenant_id=tenant.id,
                    name="Retorno",
                    description="Consulta de retorno",
                    duration_minutes=30,
                    price=75.00,
                    is_active=True,
                    color="#F59E0B",  # Amber
                ),
            ]

            for service in services:
                db.add(service)
                print(f"   ✓ Service: {service.name} - {service.duration_minutes}min - R${service.price:.2f}")

            # Commit all changes
            await db.commit()

            # Print summary
            print("\n" + "=" * 50)
            print("✅ Database seeded successfully!")
            print("=" * 50)
            print("\n📊 Summary:")
            print(f"   - Tenant: {tenant.name} (ID: {tenant.id})")
            print(f"   - Admin User: {admin.email}")
            print(f"   - Services: {len(services)}")
            print("\n🔐 Login Credentials:")
            print(f"   Email:    {admin.email}")
            print(f"   Password: admin123")
            print("\n🚀 Next Steps:")
            print("   1. Start the application: uvicorn app.main:app --reload")
            print("   2. Login at: http://localhost:8000/api/v1/auth/login")
            print("   3. API docs: http://localhost:8000/docs")
            print("=" * 50)

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error seeding database: {e}")
            import traceback

            traceback.print_exc()
            raise


async def clear_data() -> None:
    """
    Clear all data from database (use with caution!).

    WARNING: This will delete ALL data from the database.
    """
    print("⚠️  WARNING: This will delete ALL data!")
    confirmation = input("Type 'DELETE ALL DATA' to confirm: ")

    if confirmation != "DELETE ALL DATA":
        print("❌ Operation cancelled")
        return

    print("\n🗑️  Clearing database...")

    session_factory = DatabaseManager.get_session_factory()

    async with session_factory() as db:
        try:
            # Delete in reverse order of dependencies
            from app.models import Conversation, Appointment, Customer, Service, BusinessConfig, User, Tenant

            # Delete conversations
            await db.execute("DELETE FROM conversations")
            print("   ✓ Conversations deleted")

            # Delete appointments
            await db.execute("DELETE FROM appointments")
            print("   ✓ Appointments deleted")

            # Delete customers
            await db.execute("DELETE FROM customers")
            print("   ✓ Customers deleted")

            # Delete services
            await db.execute("DELETE FROM services")
            print("   ✓ Services deleted")

            # Delete business configs
            await db.execute("DELETE FROM business_configs")
            print("   ✓ Business configs deleted")

            # Delete users
            await db.execute("DELETE FROM users")
            print("   ✓ Users deleted")

            # Delete tenants
            await db.execute("DELETE FROM tenants")
            print("   ✓ Tenants deleted")

            await db.commit()

            print("\n✅ Database cleared successfully!")

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error clearing database: {e}")
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database seeding utilities")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data (WARNING: destructive!)",
    )

    args = parser.parse_args()

    if args.clear:
        asyncio.run(clear_data())
    else:
        asyncio.run(seed_data())
