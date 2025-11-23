import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from app.models import UserProfile, MonthlyCharge, MonthlyReward


def generate_monthly_entries():
    today = timezone.now()
    month_str = today.strftime("%Y-%m")   # Format: 2025-02

    for user in User.objects.all():
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            continue

        scheme = profile.scheme
        if not scheme:
            continue

        # Check if already created for this user & month
        exists_charge = MonthlyCharge.objects.filter(
            user=user,
            month=month_str
        ).exists()

        if exists_charge:
            continue  # Avoid duplicates

        # Create monthly charge
        MonthlyCharge.objects.create(
            user=user,
            scheme=scheme,
            month=month_str,
            charge_amount=scheme.monthly_charge,
            status="Pending"
        )

        # Create locked reward
        MonthlyReward.objects.create(
            user=user,
            scheme=scheme,
            month=month_str,
            reward_text=scheme.monthly_reward_text,
            is_unlocked=False
        )
