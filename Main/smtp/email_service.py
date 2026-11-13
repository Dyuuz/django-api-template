import logging
import os

import resend
from django.conf import settings

logger = logging.getLogger(__name__)
resend.api_key = settings.RESEND_API_KEY

# Set RESEND_FROM_EMAIL to an address on a domain you have verified in Resend.
DEFAULT_FROM = os.getenv("RESEND_FROM_EMAIL", "ProjectTemplate <noreply@example.com>")


def send_mail_with_resend(to, subject, html_message):
    """ """
    resend_msg = resend.Emails.send(
        {
            "from": DEFAULT_FROM,
            "to": to,
            "subject": subject,
            "html": html_message,
        }
    )
    logger.info(f"Resend successful {resend_msg['id']}")
    return resend_msg
