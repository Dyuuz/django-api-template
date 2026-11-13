from rest_framework.throttling import (
    AnonRateThrottle,
    UserRateThrottle,
)


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class RegistrationThrottle(AnonRateThrottle):
    scope = "registration"


class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"


class PaymentThrottle(UserRateThrottle):
    scope = "payment"
