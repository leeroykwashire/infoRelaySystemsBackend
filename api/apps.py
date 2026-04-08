from django.apps import AppConfig
import os


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        """Create a default superuser if one doesn't exist.

        This is a simple, non-interactive fallback for environments
        where shell access is not available (e.g., Render free tier).

        It reads `ADMIN_USERNAME`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD`
        from environment variables and will create the superuser if the
        username is not present. Any errors (database not ready, etc.)
        are silently ignored to avoid blocking startup.
        """
        # Default credentials (override via env vars in Render)
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('ADMIN_PASSWORD', 'InfoRelay2026')

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
        except Exception:
            # If DB isn't ready or migrations haven't run, silently ignore
            return
