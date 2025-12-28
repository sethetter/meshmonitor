"""Discord webhook notifier for Meshtastic messages"""
import logging
import requests
import config

logger = logging.getLogger(__name__)


def post_to_discord(mqtt_source_name: str, from_name: str, to_name: str, num_hops: int, message: str) -> bool:
    """Send a text message to Discord via webhook.

    Args:
        from_name: The node name that sent the message
        text: The message content

    Returns:
        True if message was sent successfully, False otherwise
    """
    if not config.DISCORD_WEBHOOK_URL:
        logger.debug("Discord webhook URL not configured, skipping notification")
        return False

    payload = {
        'username': f"{config.DISCORD_BOT_USERNAME}: ({mqtt_source_name})",
        'embeds': [
            {
                'type': "rich",
                'color': 65280, # green
                'fields': [
                    {
                        'name': f"{from_name} -> {to_name}",
                        'value': f"{message}\n🐇: {num_hops}",
                        'inline': False
                    }
                ]
            }
        ]
    }


    try:
        response = requests.post(
            config.DISCORD_WEBHOOK_URL,
            json=payload,
            headers={ 'content-type': 'application/json' },
            timeout=5
        )
        response.raise_for_status()
        logger.debug(f"Sent message to Discord from {from_name}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False
