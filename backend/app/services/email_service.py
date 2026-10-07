"""
AttendX — Email Service Abstraction
Handles institutional transactional emails including account activation,
password reset, and security notifications.
Integrates with Module 8 observability and provides granular error classification.
"""
import os
import smtplib
import socket
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from app.core.config import get_settings
from app.core.observability import log_structured_event

logger = logging.getLogger("attendx.email")


class EmailDeliveryResult:
    """
    Structured outcome of an email dispatch operation.
    Implements __bool__ for backwards compatibility with boolean checks.
    """
    def __init__(
        self,
        success: bool,
        status: str,
        error_code: Optional[str] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.status = status  # "ACCEPTED", "FAILED", "LOCAL_RECORDED"
        self.error_code = error_code  # e.g. "EMAIL_CONFIGURATION_ERROR", "EMAIL_PROVIDER_AUTH_ERROR"
        self.message = message
        self.details = details or {}

    def __bool__(self) -> bool:
        return self.success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "error_code": self.error_code,
            "message": self.message,
        }

    def __repr__(self) -> str:
        return f"<EmailDeliveryResult success={self.success} status='{self.status}' error_code={self.error_code}>"


class EmailService:
    # In-memory store for integration testing & verification
    _sent_emails: List[Dict[str, Any]] = []

    def __init__(self):
        self.settings = get_settings()

    def _send_smtp(self, to_email: str, subject: str, text_content: str, html_content: str) -> EmailDeliveryResult:
        """Deliver email via configured SMTP server with classified error handling and zero credential leakage."""
        if not self.settings.EMAIL_HOST:
            logger.warning("SMTP delivery skipped: EMAIL_HOST is not configured.")
            return EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="EMAIL_CONFIGURATION_ERROR",
                message="SMTP host (EMAIL_HOST or SMTP_HOST) is not configured.",
            )

        start_time = time.perf_counter()
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.settings.EMAIL_FROM_NAME} <{self.settings.EMAIL_FROM}>"
            msg["To"] = to_email

            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            port = self.settings.EMAIL_PORT or 587
            if port == 465:
                server = smtplib.SMTP_SSL(self.settings.EMAIL_HOST, port, timeout=10)
            else:
                server = smtplib.SMTP(self.settings.EMAIL_HOST, port, timeout=10)
                if self.settings.EMAIL_USE_TLS:
                    server.starttls()

            if self.settings.EMAIL_USERNAME and self.settings.EMAIL_PASSWORD:
                server.login(self.settings.EMAIL_USERNAME, self.settings.EMAIL_PASSWORD)

            server.sendmail(self.settings.EMAIL_FROM, [to_email], msg.as_string())
            server.quit()

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info("Successfully delivered email via SMTP to recipient.")
            return EmailDeliveryResult(
                success=True,
                status="ACCEPTED",
                message="Invitation email accepted by the email provider.",
                details={"duration_ms": duration_ms},
            )

        except smtplib.SMTPAuthenticationError:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("SMTP authentication failed. Verify username and password/API key.")
            return EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="EMAIL_PROVIDER_AUTH_ERROR",
                message="Email provider authentication failed. Check SMTP credentials.",
                details={"duration_ms": duration_ms},
            )

        except smtplib.SMTPRecipientsRefused:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("SMTP recipient address refused by provider.")
            return EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="INVALID_RECIPIENT",
                message="Recipient email address was refused by the email provider.",
                details={"duration_ms": duration_ms},
            )

        except (smtplib.SMTPSenderRefused, smtplib.SMTPDataError):
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("SMTP message or sender rejected by provider.")
            return EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="EMAIL_PROVIDER_REJECTED",
                message="Invitation email was rejected by the email provider.",
                details={"duration_ms": duration_ms},
            )

        except (socket.timeout, TimeoutError):
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("SMTP connection timed out after 10s.")
            return EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="EMAIL_PROVIDER_TIMEOUT",
                message="Email provider timed out. Please retry.",
                details={"duration_ms": duration_ms},
            )

        except (smtplib.SMTPConnectError, ConnectionRefusedError, OSError) as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("SMTP network connection failure: %s", type(e).__name__)
            return EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="NETWORK_ERROR",
                message="Unable to connect to email provider. Network or host unreachable.",
                details={"duration_ms": duration_ms},
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("SMTP delivery encountered unexpected error: %s", type(e).__name__)
            return EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="UNKNOWN_EMAIL_ERROR",
                message="Email delivery failed due to an unexpected provider error.",
                details={"duration_ms": duration_ms},
            )

    def send_account_activation_email(
        self,
        to_email: str,
        full_name: str,
        activation_token: str,
        role: str = "Student",
    ) -> EmailDeliveryResult:
        """
        Send a secure account activation link to a newly provisioned student or lecturer.
        Sanitizes frontend activation URLs, records telemetry, and emits Module 8 structured events.
        """
        frontend_base = (self.settings.FRONTEND_URL or "http://localhost:5173").strip().rstrip("/")
        activation_url = f"{frontend_base}/activate-account?token={activation_token}"
        expires_hours = self.settings.ACCOUNT_ACTIVATION_TOKEN_EXPIRE_HOURS
        subject = "Activate your AttendX account"

        # Module 8 Observability: log invitation attempt
        log_structured_event(
            event="invitation_email_attempt",
            level="INFO",
            role=role.lower(),
            category="EMAIL_ATTEMPT",
            details={"to": to_email},
        )

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

        is_production = os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT") == "production"

        if self.settings.EMAIL_PROVIDER == "smtp":
            delivery_result = self._send_smtp(to_email, subject, text_content, html_content)
        elif is_production:
            logger.error(
                "Production email delivery failed: EMAIL_PROVIDER is '%s' and SMTP is not configured.",
                self.settings.EMAIL_PROVIDER,
            )
            delivery_result = EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="EMAIL_CONFIGURATION_ERROR",
                message="Production email service is not configured. Set EMAIL_PROVIDER=smtp and EMAIL_HOST in environment.",
            )
        else:
            logger.info("Account activation email recorded for: %s (Provider: %s)", to_email, self.settings.EMAIL_PROVIDER)
            delivery_result = EmailDeliveryResult(
                success=True,
                status="ACCEPTED",
                message="Invitation email accepted by local console provider.",
            )

        # Module 8 Observability: log delivery result
        if delivery_result.success:
            log_structured_event(
                event="invitation_email_accepted",
                level="INFO",
                role=role.lower(),
                category="EMAIL_ACCEPTED",
                duration_ms=delivery_result.details.get("duration_ms"),
                details={"to": to_email, "status": delivery_result.status},
            )
        else:
            log_structured_event(
                event="invitation_email_failed",
                level="ERROR",
                role=role.lower(),
                category=delivery_result.error_code or "EMAIL_ERROR",
                error_code=delivery_result.error_code,
                duration_ms=delivery_result.details.get("duration_ms"),
                details={"to": to_email, "reason": delivery_result.message},
            )

        return delivery_result

    def send_password_reset_email(
        self,
        to_email: str,
        full_name: str,
        reset_token: str,
    ) -> EmailDeliveryResult:
        """Send a secure password reset link to an existing active account."""
        frontend_base = (self.settings.FRONTEND_URL or "http://localhost:5173").strip().rstrip("/")
        reset_url = f"{frontend_base}/reset-password?token={reset_token}"
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

        is_production = os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT") == "production"

        if self.settings.EMAIL_PROVIDER == "smtp":
            return self._send_smtp(to_email, subject, text_content, html_content)
        elif is_production:
            return EmailDeliveryResult(
                success=False,
                status="FAILED",
                error_code="EMAIL_CONFIGURATION_ERROR",
                message="Production email service is not configured. Set EMAIL_PROVIDER=smtp and EMAIL_HOST in environment.",
            )
        else:
            logger.info("Password reset email recorded for: %s (Provider: %s)", to_email, self.settings.EMAIL_PROVIDER)
            return EmailDeliveryResult(
                success=True,
                status="ACCEPTED",
                message="Password reset email accepted by local console provider.",
            )

    def send_security_notification(
        self,
        to_email: str,
        full_name: str,
        action: str = "",
        details: str = "",
        message: str = "",
    ) -> EmailDeliveryResult:
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
        if self.settings.EMAIL_PROVIDER == "smtp":
            return self._send_smtp(to_email, subject, text_content, html_content)
        return EmailDeliveryResult(
            success=True,
            status="ACCEPTED",
            message="Security notification dispatched.",
        )

    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Return shallow copy of recorded emails sent during process lifecycle."""
        return list(self._sent_emails)

    def clear_sent_emails(self) -> None:
        """Clear the in-memory recorded email store."""
        self._sent_emails.clear()


# Global instance
email_service = EmailService()
