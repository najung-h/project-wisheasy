# accounts/signals.py
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount
from .models import Profile

@receiver(user_signed_up)
def create_profile_on_signup(request, user, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=user)
    try:
        sa = SocialAccount.objects.get(user=user, provider='google')
        data = sa.extra_data
    except SocialAccount.DoesNotExist:
        return

    profile.name = data.get('name', '') or ''
    profile.nickname = data.get('given_name', '') or ''
    profile.profile_image = data.get('picture', '') or ''
    profile.google_mail = data.get('email', '') or ''
    profile.save()