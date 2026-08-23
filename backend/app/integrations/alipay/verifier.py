from backend.app.integrations.alipay.config import (
    get_alipay_config,
)


class AlipayVerificationError(Exception):
    """Raised when Alipay signature verification fails."""


def verify_alipay_notification(
    data: dict[str, str],
) -> bool:
    """
    Verify Alipay notification signature.

    Test environment accepts mock verification.
    Production verification will use RSA signature.
    """

    config = get_alipay_config()

    if config.environment != "production":
     return True

    if (
        not config.alipay_public_key
        or not config.app_id
    ):
        raise AlipayVerificationError(
            "Alipay verification configuration missing."
        )

    sign = data.get("sign")

    if not sign:
        raise AlipayVerificationError(
            "Missing Alipay signature."
        )

    # Real RSA verification will be added here.

    return True