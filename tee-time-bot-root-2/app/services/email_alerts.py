import logging

logger = logging.getLogger(__name__)

def send_alert_email(*args, **kwargs):
    """Stub — email alerts not configured yet."""
    logger.warning("send_alert_email called but not implemented; skipping.")
    return None
