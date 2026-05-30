"""Email service — console mock for development."""

from app.core.config import settings


class EmailService:
    """Sends transactional emails. In dev, logs to console instead of SMTP."""

    async def send_password_reset(self, *, to_email: str, reset_link: str) -> None:
        if settings.ENVIRONMENT == "development":
            print(f"\n[EmailService] PASSWORD RESET → {to_email}")
            print(f"  Link: {reset_link}\n")
        else:
            self._send_smtp(to_email, "Restablecer contraseña", reset_link)

    async def send_activation_token(self, *, to_email: str, activation_link: str) -> None:
        if settings.ENVIRONMENT == "development":
            print(f"\n[EmailService] ACTIVATION → {to_email}")
            print(f"  Link: {activation_link}\n")

    def _send_smtp(self, to_email: str, subject: str, body: str) -> None:
        # TODO: integrate with actual SMTP provider
        pass
