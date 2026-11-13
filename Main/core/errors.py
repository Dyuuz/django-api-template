class AppError(Exception):
    """Base exception for all app-level errors."""

    code = "SERVER_ERROR"
    message = "An unexpected error occurred."
    status = 500
