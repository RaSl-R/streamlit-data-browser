"""
Notifications module

Poskytuje služby pro odesílání emailových notifikací.
"""
from notifications.email_service import EmailService
from notifications.template_engine import TemplateEngine

__all__ = [
    'EmailService',
    'TemplateEngine',
]