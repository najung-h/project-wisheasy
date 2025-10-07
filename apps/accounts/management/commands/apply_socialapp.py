import os
from django.core.management import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = "Create/Update Google SocialApp from env vars"

    def handle(self, *args, **kwargs):
        cid = os.environ.get("GOOGLE_CLIENT_ID")
        secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        site_id = int(os.environ.get("SITE_ID", "1"))
        if not (cid and secret):
            self.stderr.write("Missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET")
            return 1
        site = Site.objects.get(id=site_id)
        app, _ = SocialApp.objects.update_or_create(
            provider="google",
            defaults={"name": "Google OAuth", "client_id": cid, "secret": secret, "key": ""},
        )
        app.sites.set([site]); app.save()
        self.stdout.write(f"Applied SocialApp id={app.id} site={site.domain}")