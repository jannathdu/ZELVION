from backend.app.core.config import get_settings


class AlipayConfig:
    """
    Alipay integration configuration.

    Loads credentials from application settings.
    """

    def __init__(self) -> None:
        settings = get_settings()

        self.enabled = (
            settings.enable_alipay_payments
        )

        self.app_id = (
            settings.alipay_app_id
        )

        self.app_private_key = (
            settings.alipay_app_private_key
        )

        self.alipay_public_key = (
            settings.alipay_public_key
        )

        self.gateway_url = (
            settings.alipay_gateway_url
        )

        self.notify_url = (
            settings.alipay_notify_url
        )

        self.environment = (
           settings.environment
    )

def get_alipay_config() -> AlipayConfig:
    """
    Return Alipay configuration instance.
    """

    return AlipayConfig()