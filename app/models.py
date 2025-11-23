from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

# --------------------------
# Utility: Generate Member ID
# --------------------------
def generate_member_id():
    return "USR" + uuid.uuid4().hex[:6].upper()


# --------------------------
# Scheme Model
# --------------------------
class Scheme(models.Model):
    name = models.CharField(max_length=100)
    amount = models.PositiveIntegerField()
    monthly_reward_text = models.CharField(max_length=255)
    monthly_charge = models.PositiveIntegerField()

    def __str__(self):
        return self.name


# --------------------------
# User Profile
# --------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    scheme = models.ForeignKey(Scheme, on_delete=models.SET_NULL, null=True)
    member_id = models.CharField(max_length=20, unique=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.member_id})"
    

# --------------------------
# Monthly Charge
# --------------------------
class MonthlyCharge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    charge_month = models.DateField()   # month only
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.email} - {self.month} Charge"


# --------------------------
# Monthly Reward
# --------------------------
class MonthlyReward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward_month = models.DateField()   # month only
    reward_text = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.email} - {self.month} Reward"


# --------------------------
# Email Token
# --------------------------
class EmailToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    expiry = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return (not self.used) and (self.expiry > timezone.now())
