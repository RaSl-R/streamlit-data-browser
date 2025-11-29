import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

def send_password_reset_email(recipient_email: str, reset_token: str) -> bool:
    """
    Odešle e-mail s odkazem pro reset hesla.
    
    Args:
        recipient_email: E-mail příjemce
        reset_token: Reset token pro URL
    
    Returns:
        bool: True pokud se email odeslal úspěšně
    """
    try:
        # Načtení nastavení z secrets
        smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = st.secrets.get("SMTP_PORT", 587)
        smtp_user = st.secrets.get("SMTP_USER")
        smtp_password = st.secrets.get("SMTP_PASSWORD")
        app_url = st.secrets.get("APP_URL", "http://localhost:8501")
        
        if not smtp_user or not smtp_password:
            st.error("E-mailová služba není nakonfigurována. Kontaktujte administrátora.")
            return False
        
        # Vytvoření zprávy
        message = MIMEMultipart("alternative")
        message["Subject"] = "Reset hesla - Data Browser"
        message["From"] = smtp_user
        message["To"] = recipient_email
        
        # Reset URL
        reset_url = f"{app_url}?reset_token={reset_token}"
        
        # Text verze
        text_content = f"""
Dobrý den,

obdrželi jsme požadavek na reset hesla pro váš účet.

Pro reset hesla klikněte na následující odkaz:
{reset_url}

Odkaz je platný 1 hodinu.

Pokud jste o reset hesla nežádali, ignorujte tento e-mail.

S pozdravem,
Data Browser tým
"""
        
        # HTML verze
        html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #333;">Reset hesla</h2>
    <p>Dobrý den,</p>
    <p>obdrželi jsme požadavek na reset hesla pro váš účet.</p>
    <p>Pro reset hesla klikněte na tlačítko níže:</p>
    <p style="margin: 30px 0;">
      <a href="{reset_url}" 
         style="background-color: #4CAF50; color: white; padding: 12px 24px; 
                text-decoration: none; border-radius: 4px; display: inline-block;">
        Resetovat heslo
      </a>
    </p>
    <p style="color: #666; font-size: 0.9em;">
      Odkaz je platný 1 hodinu.
    </p>
    <p style="color: #666; font-size: 0.9em;">
      Pokud jste o reset hesla nežádali, ignorujte tento e-mail.
    </p>
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 0.8em;">
      S pozdravem,<br>
      Data Browser tým
    </p>
  </body>
</html>
"""
        
        # Připojení obou verzí
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Odeslání
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        
        return True
        
    except Exception as e:
        st.error(f"Chyba při odesílání e-mailu: {e}")
        return False


def send_welcome_email(recipient_email: str) -> bool:
    """
    Odešle uvítací e-mail po registraci (volitelné).
    """
    try:
        smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = st.secrets.get("SMTP_PORT", 587)
        smtp_user = st.secrets.get("SMTP_USER")
        smtp_password = st.secrets.get("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_password:
            return False
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Vítejte v Data Browser"
        message["From"] = smtp_user
        message["To"] = recipient_email
        
        html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2>Vítejte v Data Browser!</h2>
    <p>Váš účet byl úspěšně vytvořen.</p>
    <p>Nyní se můžete přihlásit a začít pracovat s daty.</p>
    <p>S pozdravem,<br>Data Browser tým</p>
  </body>
</html>
"""
        
        part = MIMEText(html_content, "html")
        message.attach(part)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        
        return True
        
    except Exception as e:
        print(f"Chyba při odesílání uvítacího e-mailu: {e}")
        return False