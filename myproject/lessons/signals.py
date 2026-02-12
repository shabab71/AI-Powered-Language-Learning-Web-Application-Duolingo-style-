from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AppUser, EmailVerification
from .models import AppUser, UserProgress



@receiver(post_save, sender=AppUser)
def create_email_verification(sender, instance, created, **kwargs):
    if created:
        verification = EmailVerification.objects.create(user=instance)
        try:
            verification.send_verification_email()
        except Exception as e:
            print("Email send failed:", e)

@receiver(post_save, sender=AppUser)
def create_user_progress(sender, instance, created, **kwargs):
    if created:
        UserProgress.objects.get_or_create(app_user=instance)