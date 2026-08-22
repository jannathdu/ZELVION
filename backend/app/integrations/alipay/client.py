from alipay import AliPay

from backend.app.integrations.alipay.config import (
    get_alipay_config,
)


def create_alipay_client() -> AliPay:
    """
    Create and return an Alipay SDK client.
    """

    config = get_alipay_config()

    if not config.enabled:
        raise RuntimeError(
            "Alipay payments are disabled."
        )

    if (
        config.app_id is None
        or config.app_private_key is None
        or config.alipay_public_key is None
    ):
        raise RuntimeError(
            "Incomplete Alipay configuration."
        )

    return AliPay(
        appid=config.app_id,
        app_notify_url=config.notify_url,
        app_private_key_string=(
            config.app_private_key.get_secret_value()
        ),
        alipay_public_key_string=(
            config.alipay_public_key
        ),
        sign_type="RSA2",
        debug=True,
    )