from django.apps import AppConfig
import os


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        """Attempt to create a default superuser shortly after startup.

        To avoid accessing the database during app initialization (which
        raises warnings and can be problematic before migrations run),
        perform the creation in a background thread after a short delay.
        This keeps startup clean while still creating the admin for
        quick demo environments.
        """
        import threading
        import time

        def _create_admin_delayed():
            # short delay to allow migrations/build to complete
            time.sleep(5)
            username = os.environ.get('ADMIN_USERNAME', 'admin')
            email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            password = os.environ.get('ADMIN_PASSWORD', 'InfoRelay2026')
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if not User.objects.filter(username=username).exists():
                    User.objects.create_superuser(username=username, email=email, password=password)
            except Exception:
                # Log to stdout but don't raise; avoid crashing the app
                try:
                    import sys
                    print('Auto-create superuser failed', file=sys.stderr)
                except Exception:
                    pass

        t = threading.Thread(target=_create_admin_delayed, daemon=True)
        t.start()
