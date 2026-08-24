import base64

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from backend.app.integrations.alipay.config import (
    get_alipay_config,
)


class AlipayVerificationError(Exception):
    """Raised when Alipay signature verification fails."""


def _build_sign_content(
    data: dict[str, str],
) -> str:
    """
    Build Alipay RSA2 signing content.

    Removes signature fields and sorts parameters
    alphabetically by parameter name.
    """

    excluded_keys = {
        "sign",
        "sign_type",
    }

    items = [
        (key, value)
        for key, value in data.items()
        if (
            key not in excluded_keys
            and value is not None
            and value != ""
        )
    ]

    items.sort(
        key=lambda item: item[0],
    )

    return "&".join(
        f"{key}={value}"
        for key, value in items
    )


def verify_alipay_notification(
    data: dict[str, str],
) -> bool:
    """
    Verify an Alipay asynchronous notification
    using RSA2 (SHA-256 with RSA).
    """

    config = get_alipay_config()

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

    content = _build_sign_content(
        data,
    )

    try:
        public_key = RSA.import_key(
            config.alipay_public_key,
        )

        signature = base64.b64decode(
            sign,
            validate=True,
        )

        digest = SHA256.new(
            content.encode("utf-8"),
        )

        pkcs1_15.new(
            public_key,
        ).verify(
            digest,
            signature,
        )

    except (
        ValueError,
        TypeError,
    ) as error:
        raise AlipayVerificationError(
            "Invalid Alipay signature."
        ) from error

    return True