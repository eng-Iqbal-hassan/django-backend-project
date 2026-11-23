"""Password-reset OTP: generate, email and verify one-time codes."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db.models import F
from django.utils import timezone

from app.accounts.models import PasswordResetOTP

INVALID_OTP_MESSAGE = "Invalid or expired OTP."


class InvalidOTP(Exception):
    pass


def _active_otps(user):
    return PasswordResetOTP.objects.filter(user=user, used_at__isnull=True, expires_at__gt=timezone.now())


def issue_otp(user):
    """Create a new OTP for `user` and email it. Skips sending if one was sent within the cooldown."""
    now = timezone.now()
    cooldown = timedelta(seconds=settings.PASSWORD_RESET_OTP_RESEND_COOLDOWN_SECONDS)
    if _active_otps(user).filter(created_at__gt=now - cooldown).exists():
        return

    # Only the newest code is valid; retire any earlier ones.
    _active_otps(user).update(used_at=now)

    code = f"{secrets.randbelow(10 ** 6):06d}"
    ttl = settings.PASSWORD_RESET_OTP_TTL_MINUTES
    PasswordResetOTP.objects.create(
        user=user, code_hash=make_password(code), expires_at=now + timedelta(minutes=ttl)
    )
    send_mail(
        subject="Your password reset code",
        message=(
            f"Hi {user.name},\n\n"
            f"Your password reset code is: {code}\n\n"
            f"It expires in {ttl} minutes. If you didn't request this, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def check_otp(user, code):
    """Return the matching active OTP, or raise InvalidOTP. Wrong guesses count toward the attempt limit."""
    otp = _active_otps(user).first() if user is not None else None
    if otp is None or otp.attempts >= settings.PASSWORD_RESET_OTP_MAX_ATTEMPTS:
        raise InvalidOTP(INVALID_OTP_MESSAGE)
    if not check_password(code, otp.code_hash):
        PasswordResetOTP.objects.filter(pk=otp.pk).update(attempts=F("attempts") + 1)
        raise InvalidOTP(INVALID_OTP_MESSAGE)
    return otp
