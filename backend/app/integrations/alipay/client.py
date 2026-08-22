from alipay.aop.api.DefaultAlipayClient import (
    DefaultAlipayClient,
)
from alipay.aop.api.AlipayClientConfig import (
    AlipayClientConfig,
)

from backend.app.integrations.alipay.config import (
    get_alipay_config,
)


def create_alipay_client() -> DefaultAlipayClient:
    """
    Create Alipay SDK client.
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
        or config.gateway_url is None
    ):
        raise RuntimeError(
            "Incomplete Alipay configuration."
        )

    client_config = AlipayClientConfig()

    client_config.server_url = (
        config.gateway_url
    )

    client_config.app_id = (
        config.app_id
    )

    client_config.app_private_key = (
        config.app_private_key.get_secret_value()
    )

    client_config.alipay_public_key = (
        config.alipay_public_key
    )

    client_config.protocol = "https"
    client_config.sign_type = "RSA2"

    return DefaultAlipayClient(
        client_config
    )