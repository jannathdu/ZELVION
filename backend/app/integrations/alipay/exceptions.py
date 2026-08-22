class AlipayError(Exception):
    """
    Base exception for Alipay integration errors.
    """


class AlipayConfigurationError(AlipayError):
    """
    Raised when Alipay configuration is invalid.
    """


class AlipayPaymentError(AlipayError):
    """
    Raised when Alipay payment operation fails.
    """