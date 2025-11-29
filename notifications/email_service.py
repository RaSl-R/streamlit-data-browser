"""
Email služba pro odesílání notifikací
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config.settings import settings
from notifications.template_engine import TemplateEngine
from core.logger import logger
from core.exceptions import EmailError

class EmailService:
    """Služba pro odesílání emailů"""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.smtp_config = settings.smtp
        self.app_config = settings.app
    
    def _create_message(
        self,
        recipient: str,
        subject: str,
        text_body: str,
        html_body: str
    ) -> MIMEMultipart:
        """
        Vytvoří email zprávu.
        
        Args:
            recipient: Email příjemce
            subject: Předmět emailu
            text_body: Textová verze
            html_body: HTML verze
            
        Returns:
            MIMEMultipart objekt
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.smtp_config.sender_name} <{self.smtp_config.user}>"
        message["To"] = recipient
        
        # Připojíme obě verze
        part_text = MIMEText(text_body, "plain", "utf-8")
        part_html = MIMEText(html_body, "html", "utf-8")
        
        message.attach(part_text)
        message.attach(part_html)
        
        return message
    
    def _send_message(self, message: MIMEMultipart) -> bool:
        """
        Odešle email zprávu přes SMTP.
        
        Args:
            message: Email zpráva k odeslání
            
        Returns:
            True pokud se odeslání podařilo
        """
        try:
            with smtplib.SMTP(self.smtp_config.server, self.smtp_config.port) as server:
                server.starttls()
                server.login(self.smtp_config.user, self.smtp_config.password)
                server.send_message(message)
            
            logger.info(f"Email successfully sent to {message['To']}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise EmailError("Chyba autentizace při odesílání emailu")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise EmailError(f"Chyba při odesílání emailu: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise EmailError(f"Neočekávaná chyba při odesílání emailu: {e}")
    
    @staticmethod
    def send_password_reset_email(recipient_email: str, reset_token: str) -> bool:
        """
        Odešle email s odkazem pro reset hesla.
        
        Args:
            recipient_email: Email příjemce
            reset_token: Reset token pro URL
            
        Returns:
            True pokud se email odeslal úspěšně
        """
        try:
            service = EmailService()
            
            if not settings.is_smtp_configured:
                logger.warning("SMTP is not configured, skipping email send")
                return False
            
            # Vygenerujeme reset URL
            reset_url = f"{service.app_config.app_url}?reset_token={reset_token}"
            
            # Kontext pro šablonu
            context = {
                "reset_url": reset_url,
                "app_name": service.app_config.app_name,
                "expiry_hours": 1
            }
            
            # Načteme šablony
            text_body = service.template_engine.render_text(
                "password_reset",
                context,
                locale=service.app_config.locale
            )
            
            html_body = service.template_engine.render_html(
                "password_reset",
                context
            )
            
            # Vytvoříme a odešleme zprávu
            message = service._create_message(
                recipient=recipient_email,
                subject=f"Reset hesla - {service.app_config.app_name}",
                text_body=text_body,
                html_body=html_body
            )
            
            return service._send_message(message)
            
        except EmailError:
            raise
        except Exception as e:
            logger.error(f"Error in send_password_reset_email: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(recipient_email: str) -> bool:
        """
        Odešle uvítací email po registraci.
        
        Args:
            recipient_email: Email příjemce
            
        Returns:
            True pokud se email odeslal úspěšně
        """
        try:
            service = EmailService()
            
            if not settings.is_smtp_configured:
                logger.warning("SMTP is not configured, skipping email send")
                return False
            
            # Kontext pro šablonu
            context = {
                "app_name": service.app_config.app_name,
                "app_url": service.app_config.app_url
            }
            
            # Načteme šablony
            text_body = service.template_engine.render_text(
                "welcome",
                context,
                locale=service.app_config.locale
            )
            
            html_body = service.template_engine.render_html(
                "welcome",
                context
            )
            
            # Vytvoříme a odešleme zprávu
            message = service._create_message(
                recipient=recipient_email,
                subject=f"Vítejte v {service.app_config.app_name}",
                text_body=text_body,
                html_body=html_body
            )
            
            return service._send_message(message)
            
        except EmailError:
            raise
        except Exception as e:
            logger.error(f"Error in send_welcome_email: {e}")
            return False
    
    @staticmethod
    def send_group_approval_notification(
        recipient_email: str,
        group_name: str
    ) -> bool:
        """
        Odešle notifikaci o schválení přístupu ke skupině.
        
        Args:
            recipient_email: Email příjemce
            group_name: Název schválené skupiny
            
        Returns:
            True pokud se email odeslal úspěšně
        """
        try:
            service = EmailService()
            
            if not settings.is_smtp_configured:
                return False
            
            context = {
                "app_name": service.app_config.app_name,
                "group_name": group_name,
                "app_url": service.app_config.app_url
            }
            
            # Pro tento typ emailu použijeme jednoduchý inline template
            text_body = f"""
Dobrý den,

Vaše žádost o přístup ke skupině "{group_name}" byla schválena.

Nyní se můžete přihlásit a používat aplikaci s novými oprávněními.

Přihlásit se: {context['app_url']}

S pozdravem,
{context['app_name']} tým
"""
            
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #4CAF50;">Žádost schválena</h2>
    <p>Dobrý den,</p>
    <p>Vaše žádost o přístup ke skupině <strong>{group_name}</strong> byla schválena.</p>
    <p>Nyní se můžete přihlásit a používat aplikaci s novými oprávněními.</p>
    <p style="margin: 30px 0;">
        <a href="{context['app_url']}" 
           style="background-color: #4CAF50; color: white; padding: 12px 24px;
                  text-decoration: none; border-radius: 4px; display: inline-block;">
            Přihlásit se
        </a>
    </p>
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 0.8em;">
        S pozdravem,<br>
        {context['app_name']} tým
    </p>
</body>
</html>
"""
            
            message = service._create_message(
                recipient=recipient_email,
                subject=f"Žádost o skupinu schválena - {service.app_config.app_name}",
                text_body=text_body,
                html_body=html_body
            )
            
            return service._send_message(message)
            
        except Exception as e:
            logger.error(f"Error in send_group_approval_notification: {e}")
            return False