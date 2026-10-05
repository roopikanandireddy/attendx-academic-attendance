"""
AttendX — Email Service Abstraction
Handles institutional transactional emails including account activation,
password reset, and security notifications.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from app.core.config import get_settings

logger = logging.getLogger("attendx.email")


class EmailService:
    # In-memory store for integration testing & verification
    _sent_emails: List[Dict[str, Any]] = []

    def __init__(self):
        self.settings = get_settings()

    def _send_smtp(self, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """Deliver email via configured SMTP server."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.settings.EMAIL_FROM_NAME} <{self.settings.EMAIL_FROM}>"
            msg["To"] = to_email

            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            if not self.settings.EMAIL_HOST:
                logger.warning("SMTP delivery skipped: EMAIL_HOST is not configured.")
                return False

            if self.settings.EMAIL_PORT == 465:
                server = smtplib.SMTP_SSL(self.settings.EMAIL_HOST, self.settings.EMAIL_PORT, timeout=10)
            else:
                server = smtplib.SMTP(self.settings.EMAIL_HOST, self.settings.EMAIL_PORT, timeout=10)
                if self.settings.EMAIL_USE_TLS:
                    server.starttls()

            if self.settings.EMAIL_USERNAME and self.settings.EMAIL_PASSWORD:
                server.login(self.settings.EMAIL_USERNAME, self.settings.EMAIL_PASSWORD)

            server.sendmail(self.settings.EMAIL_FROM, [to_email], msg.as_string())
            server.quit()
            logger.info("Successfully delivered email to recipient.")
            return True
        except Exception as e:
            logger.error("Failed to send email via SMTP: %s", str(e))
            return False

    def send_account_activation_email(
        self,
        to_email: str,
        full_name: str,
        activation_token: str,
        role: str = "Student",
    ) -> bool:
        """
        Send a secure account activation link to a newly provisioned student or faculty member.
        Does not include passwords or database keys.
        """
        activation_url = f"{self.settings.FRONTEND_URL}/activate-account?token={activation_token}"
        expires_hours = self.settings.ACCOUNT_ACTIVATION_TOKEN_EXPIRE_HOURS
        subject = "Activate your AttendX account"

        # Plaintext format
        text_content = (
            f"AttendX — Academic Attendance Management System\n\n"
            f"Hello {full_name},\n\n"
            f"Your AttendX {role} account has been created by your institution administrator.\n\n"
            f"Please click the link below to activate your account and create your password:\n"
            f"{activation_url}\n\n"
            f"This activation link expires after {expires_hours} hours.\n\n"
            f"If you did not expect this account, please contact your institution administrator.\n\n"
            f"Regards,\n"
            f"AttendX Administration\n"
        )

        # HTML format
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
            .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; }}
            .header {{ border-bottom: 1px solid #f1f5f9; padding-bottom: 16px; margin-bottom: 24px; }}
            .title {{ font-size: 20px; font-weight: 700; color: #0f172a; margin: 0; }}
            .subtitle {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
            .button {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; margin: 20px 0; }}
            .footer {{ font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 16px; margin-top: 28px; line-height: 1.5; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1 class="title">AttendX</h1>
              <p class="subtitle">Academic Attendance Management System</p>
            </div>
            <p>Hello <strong>{full_name}</strong>,</p>
            <p>Your AttendX <strong>{role}</strong> account has been created by your institution administrator.</p>
            <p>Please click the button below to activate your account and create your password:</p>
            <div style="text-align: center;">
              <a href="{activation_url}" class="button" target="_blank">Activate My Account</a>
            </div>
            <p style="font-size: 13px; color: #64748b;">Or copy and paste this link into your browser:<br>
              <a href="{activation_url}" style="color: #2563eb; word-break: break-all;">{activation_url}</a>
            </p>
            <p style="font-size: 13px; color: #64748b;">This activation link expires after <strong>{expires_hours} hours</strong>.</p>
            <div class="footer">
              <p>If you did not expect this account, please contact your institution administrator.</p>
              <p>&copy; AttendX Academic Attendance Management System. All rights reserved.</p>
            </div>
          </div>
        </body>
        </html>
        """

        # Record in test store for verification
        self._sent_emails.append({
            "to": to_email,
            "subject": subject,
            "type": "account_activation",
            "activation_url": activation_url,
            "activation_token": activation_token,
            "role": role,
        })

        if self.settings.EMAIL_PROVIDER == "smtp" and self.settings.EMAIL_HOST:
            return self._send_smtp(to_email, subject, text_content, html_content)
        else:
            logger.info("Account activation email queued for: %s (Provider: %s)", to_email, self.settings.EMAIL_PROVIDER)
            return True

    def send_password_reset_email(
        self,
        to_email: str,
        full_name: str,
        reset_token: str,
    ) -> bool:
        """Send a secure password reset link to an existing active account."""
        reset_url = f"{self.settings.FRONTEND_URL}/reset-password?token={reset_token}"
        expires_hours = self.settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
        subject = "Reset your AttendX password"

        text_content = (
            f"AttendX — Academic Attendance Management System\n\n"
            f"Hello {full_name},\n\n"
            f"We received a request to reset your AttendX account password.\n\n"
            f"Please click the link below to set a new password:\n"
            f"{reset_url}\n\n"
            f"This link expires after {expires_hours} hours.\n\n"
            f"If you did not request a password reset, you can safely ignore this email.\n\n"
            f"Regards,\n"
            f"AttendX Administration\n"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
            .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; }}
            .header {{ border-bottom: 1px solid #f1f5f9; padding-bottom: 16px; margin-bottom: 24px; }}
            .title {{ font-size: 20px; font-weight: 700; color: #0f172a; margin: 0; }}
            .subtitle {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
            .button {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; margin: 20px 0; }}
            .footer {{ font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 16px; margin-top: 28px; line-height: 1.5; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1 class="title">AttendX</h1>
              <p class="subtitle">Academic Attendance Management System</p>
            </div>
            <p>Hello <strong>{full_name}</strong>,</p>
            <p>We received a request to reset your AttendX account password.</p>
            <p>Please click the button below to set a new password:</p>
            <div style="text-align: center;">
              <a href="{reset_url}" class="button" target="_blank">Reset Password</a>
            </div>
            <p style="font-size: 13px; color: #64748b;">Or copy and paste this link into your browser:<br>
              <a href="{reset_url}" style="color: #2563eb; word-break: break-all;">{reset_url}</a>
            </p>
            <p style="font-size: 13px; color: #64748b;">This link expires after <strong>{expires_hours} hours</strong>.</p>
            <div class="footer">
              <p>If you did not request this reset, you can safely ignore this email.</p>
              <p>&copy; AttendX Academic Attendance Management System. All rights reserved.</p>
            </div>
          </div>
        </body>
        </html>
        """

        self._sent_emails.append({
            "to": to_email,
            "subject": subject,
            "type": "password_reset",
            "reset_url": reset_url,
            "reset_token": reset_token,
        })

        if self.settings.EMAIL_PROVIDER == "smtp" and self.settings.EMAIL_HOST:
            return self._send_smtp(to_email, subject, text_content, html_content)
        else:
            logger.info("Password reset email queued for: %s (Provider: %s)", to_email, self.settings.EMAIL_PROVIDER)
            return True

    def send_security_notification(
        self,
        to_email: str,
        full_name: str,
        action: str = "",
        details: str = "",
        message: str = "",
    ) -> bool:
        """Send account security notification (e.g. account activated, password changed)."""
        msg_body = message or (f"{action}: {details}" if action else "A security event occurred on your account.")
        subject = f"AttendX Security Notification{f' — {action}' if action else ''}"
        text_content = (
            f"AttendX Security Notification\n\n"
            f"Hello {full_name},\n\n"
            f"{msg_body}\n\n"
            f"If you did not initiate this change, please contact your administrator immediately.\n\n"
            f"Regards,\n"
            f"AttendX Security\n"
        )
        html_content = f"""
        <div style="font-family: sans-serif; padding: 20px;">
          <h2>AttendX Security Notification</h2>
          <p>Hello <strong>{full_name}</strong>,</p>
          <p>{msg_body}</p>
          <p style="color: #64748b; font-size: 12px;">If you did not initiate this change, contact your administrator immediately.</p>
        </div>
        """
        self._sent_emails.append({
            "to": to_email,
            "subject": subject,
            "type": "security_notification",
            "message": msg_body,
            "action": action,
            "details": details,
        })
        if self.settings.EMAIL_PROVIDER == "smtp" and self.settings.EMAIL_HOST:
            return self._send_smtp(to_email, subject, text_content, html_content)
        return True

    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Return shallow copy of recorded emails sent during process lifecycle."""
        return list(self._sent_emails)

    def clear_sent_emails(self) -> None:
        """Clear the in-memory recorded email store."""
        self._sent_emails.clear()


# Global instance
email_service = EmailService()
