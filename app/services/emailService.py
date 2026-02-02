import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def get_email_config():
    """Get email configuration from environment variables."""
    return {
        "recipient": os.getenv("EMAIL_RECIPIENT"),
        "smtp_host": os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
        "smtp_user": os.getenv("EMAIL_SMTP_USER"),
        "smtp_password": os.getenv("EMAIL_SMTP_PASSWORD"),
    }


def validate_email_config(config: dict) -> bool:
    """Validate that all required email config is present."""
    required = ["recipient", "smtp_user", "smtp_password"]
    return all(config.get(key) for key in required)


def send_feedback_email(
    feedback_type: str,
    message: str,
    user_email: str = None
) -> bool:
    """
    Send feedback email to the configured recipient.
    
    Args:
        feedback_type: Type of feedback (suggestion, bug, other)
        message: The feedback message
        user_email: Optional email for reply
    
    Returns:
        True if email sent successfully
    
    Raises:
        EmailServiceError: If email sending fails
    """
    config = get_email_config()
    
    if not validate_email_config(config):
        raise EmailServiceError(
            "Configuração de email não definida no servidor",
            status_code=503
        )
    
    if not message or not message.strip():
        raise EmailServiceError("Mensagem é obrigatória", status_code=400)
    
    if len(message) > 5000:
        raise EmailServiceError("Mensagem muito longa (máx 5000 caracteres)", status_code=400)
    
    type_labels = {
        "suggestion": "Sugestão de Funcionalidade",
        "bug": "Reporte de Bug",
        "other": "Outro Feedback"
    }
    
    type_label = type_labels.get(feedback_type, "Feedback")
    
    # Build email
    msg = MIMEMultipart()
    msg["From"] = config["smtp_user"]
    msg["To"] = config["recipient"]
    msg["Subject"] = f"[TREM API] {type_label}"
    
    # Email body
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    reply_info = f"Email para resposta: {user_email}" if user_email else "Sem email informado"
    
    body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{type_label}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Data/Hora: {timestamp}
{reply_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MENSAGEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{message.strip()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enviado automaticamente via TREM API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    try:
        with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
            server.starttls()
            server.login(config["smtp_user"], config["smtp_password"])
            server.send_message(msg)
        
        return True
    
    except smtplib.SMTPAuthenticationError:
        raise EmailServiceError(
            "Falha na autenticação SMTP",
            status_code=503
        )
    except smtplib.SMTPException as e:
        raise EmailServiceError(
            f"Erro ao enviar email: {str(e)}",
            status_code=503
        )
    except Exception as e:
        raise EmailServiceError(
            f"Erro inesperado: {str(e)}",
            status_code=500
        )
