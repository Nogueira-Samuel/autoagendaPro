from typing import Dict
from datetime import datetime

class MessageTemplates:
    """Templates for WhatsApp notifications"""

    @staticmethod
    def format_date(date: str) -> str:
        """Format date to DD/MM/YYYY"""
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except:
            return date

    @staticmethod
    def confirmation(data: Dict) -> str:
        """Appointment confirmation message"""
        template = data.get('template') or """
Olá {name}! 👋

Seu agendamento foi confirmado:
📅 Data: {date}
⏰ Horário: {time}
💼 Serviço: {service}
💰 Valor: R$ {price}

Para cancelar, entre em contato.

Até lá!
{business_name}
"""
        return template.format(
            name=data.get('customer_name', ''),
            date=MessageTemplates.format_date(data.get('date', '')),
            time=data.get('time', ''),
            service=data.get('service', ''),
            price=data.get('price', '0.00'),
            business_name=data.get('business_name', '')
        )

    @staticmethod
    def reminder_24h(data: Dict) -> str:
        """24 hour reminder message"""
        template = data.get('template') or """
Olá {name}! ⏰

Lembrete: Você tem um agendamento amanhã!

📅 Data: {date}
⏰ Horário: {time}
💼 Serviço: {service}

Nos vemos em breve!
{business_name}
"""
        return template.format(
            name=data.get('customer_name', ''),
            date=MessageTemplates.format_date(data.get('date', '')),
            time=data.get('time', ''),
            service=data.get('service', ''),
            business_name=data.get('business_name', '')
        )

    @staticmethod
    def reminder_1h(data: Dict) -> str:
        """1 hour reminder message"""
        template = data.get('template') or """
Olá {name}! 🔔

Seu agendamento é em 1 HORA!

⏰ Horário: {time}
💼 Serviço: {service}

Estamos te esperando!
{business_name}
"""
        return template.format(
            name=data.get('customer_name', ''),
            time=data.get('time', ''),
            service=data.get('service', ''),
            business_name=data.get('business_name', '')
        )

    @staticmethod
    def thanks(data: Dict) -> str:
        """Thank you message after appointment"""
        template = data.get('template') or """
Olá {name}! 💚

Obrigado por sua visita!

Esperamos ter atendido suas expectativas.

Até a próxima!
{business_name}
"""
        return template.format(
            name=data.get('customer_name', ''),
            business_name=data.get('business_name', '')
        )

    @staticmethod
    def cancellation(data: Dict) -> str:
        """Cancellation confirmation message"""
        template = data.get('template') or """
Olá {name},

Seu agendamento foi cancelado:
📅 Data: {date}
⏰ Horário: {time}

Para reagendar, entre em contato.

{business_name}
"""
        return template.format(
            name=data.get('customer_name', ''),
            date=MessageTemplates.format_date(data.get('date', '')),
            time=data.get('time', ''),
            business_name=data.get('business_name', '')
        )

    @staticmethod
    def owner_notification(data: Dict) -> str:
        """Notification for business owner"""
        message_type = data.get('type', 'new')

        if message_type == 'new':
            return f"""
🔔 NOVO AGENDAMENTO

Cliente: {data.get('customer_name', '')}
📱 Telefone: {data.get('customer_phone', '')}
📅 Data: {MessageTemplates.format_date(data.get('date', ''))}
⏰ Horário: {data.get('time', '')}
💼 Serviço: {data.get('service', '')}
"""
        elif message_type == 'cancelled':
            return f"""
❌ AGENDAMENTO CANCELADO

Cliente: {data.get('customer_name', '')}
📅 Data: {MessageTemplates.format_date(data.get('date', ''))}
⏰ Horário: {data.get('time', '')}
💼 Serviço: {data.get('service', '')}
"""
        return ""
