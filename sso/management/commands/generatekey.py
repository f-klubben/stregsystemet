import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from jwcrypto import jwk


class Command(BaseCommand):
    help = "Generate oidc.key in the project root"

    def handle(self, *args, **options):
        key_path = os.path.join(settings.BASE_DIR, "oidc.key")
        key = jwk.JWK.generate(kty="RSA", size=4096)

        try:
            descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise CommandError(f"{key_path} already exists") from error

        with os.fdopen(descriptor, "wb") as key_file:
            key_file.write(key.export_to_pem(private_key=True, password=None))

        self.stdout.write(self.style.SUCCESS(f"Generated {key_path}"))
