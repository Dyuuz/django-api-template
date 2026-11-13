class ThreatDetector:
    BLOCKED_PREFIXES = (
        "/.env",
        "/.aws",
        "/.docker",
        "/.cursor",
        "/.claude",
        "/.git",
    )

    BLOCKED_EXTENSIONS = (
        ".env",
        ".sql",
        ".zip",
        ".tar",
        ".gz",
        ".tar.gz",
        ".bak",
        ".rar",
        ".7z",
        ".dump",
        ".sqlite",
        ".sqlite3",
        ".db",
    )

    # Common automated discovery endpoints
    BLOCKED_PATHS = (
        "/wp-login.php",
        "/xmlrpc.php",
        "/wp-admin",
        "/phpmyadmin",
        "/server-status",
        "/vendor/phpunit",
    )

    def detect(self, path):
        path = path.lower().rstrip("/") or "/"

        # Sensitive configuration directories and files
        if path.startswith(self.BLOCKED_PREFIXES):
            return {
                "score": 10,
                "reason": "sensitive_configuration_probe",
            }

        # Hidden files and directories, excluding .well-known
        hidden_segments = [
            segment
            for segment in path.split("/")
            if segment.startswith(".") and segment != ".well-known"
        ]

        if hidden_segments:
            return {
                "score": 10,
                "reason": "hidden_file_probe",
            }

        # Database and archive discovery
        if path.endswith(self.BLOCKED_EXTENSIONS):
            return {
                "score": 8,
                "reason": "backup_file_probe",
            }

        # Common CMS and framework discovery
        if any(
            path == blocked or path.startswith(blocked + "/")
            for blocked in self.BLOCKED_PATHS
        ):
            return {
                "score": 5,
                "reason": "common_endpoint_probe",
            }

        return None
