from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, Scheme, MonthlyCharge, MonthlyReward
from django.forms.widgets import DateInput
from .models import MonthlyCharge, MonthlyReward


# --------------------------
# USER PROFILE CUSTOM FORM
# --------------------------
class UserProfileAdminForm(forms.ModelForm):
    member_input = forms.CharField(
        label="Member ID",
        required=True,
        help_text="Enter the Member ID of the user"
    )

    class Meta:
        model = UserProfile
        fields = ['member_input', 'scheme']   # Do NOT show 'user'

    def clean(self):
        cleaned_data = super().clean()
        member_id = cleaned_data.get("member_input")

        try:
            profile = UserProfile.objects.get(member_id=member_id)
            user = profile.user
        except UserProfile.DoesNotExist:
            raise forms.ValidationError("Invalid Member ID — no such user exists.")

        cleaned_data["user"] = user
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.user = self.cleaned_data["user"]
        if commit:
            obj.save()
        return obj


class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm
    list_display = ("user", "scheme", "member_id")
    readonly_fields = ("member_id",)

    def has_add_permission(self, request):
        return True


# --------------------------
# MONTHLY REWARD CUSTOM FORM
# --------------------------
class MonthlyRewardAdminForm(forms.ModelForm):
    member_input = forms.CharField(
        label="Member ID",
        required=True,
        help_text="Enter Member ID to assign reward"
    )

    class Meta:
        model = MonthlyReward
        fields = ['member_input']      # reward text removed

    def clean(self):
        cleaned_data = super().clean()
        member_id = cleaned_data.get("member_input")

        # Find UserProfile by member ID
        try:
            profile = UserProfile.objects.get(member_id=member_id)
        except UserProfile.DoesNotExist:
            raise forms.ValidationError("Invalid Member ID — no such user exists.")

        cleaned_data["user"] = profile.user
        cleaned_data["reward_text"] = profile.scheme.monthly_reward  # AUTO FETCH

        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.user = self.cleaned_data["user"]
        obj.reward_text = self.cleaned_data["reward_text"]   # AUTO SAVE

        if commit:
            obj.save()
        return obj



class MonthlyRewardAdmin(admin.ModelAdmin):
    form = MonthlyRewardAdminForm
    list_display = ("user", "reward_text", "created_at")

    def has_add_permission(self, request):
        return True

class MonthPickerInput(DateInput):
    input_type = 'month'
    format = '%Y-%m'
class MonthlyChargeAdminForm(forms.ModelForm):
    member_input = forms.CharField(
        label="Member ID",
        required=True
    )

    class Meta:
        model = MonthlyCharge
        fields = ['member_input', 'charge_month', 'paid']
        widgets = {
            'charge_month': MonthPickerInput()
        }

    def clean(self):
        cleaned_data = super().clean()
        member_id = cleaned_data.get("member_input")

        try:
            profile = UserProfile.objects.get(member_id=member_id)
            cleaned_data["user"] = profile.user
            cleaned_data["scheme"] = profile.scheme
        except UserProfile.DoesNotExist:
            raise forms.ValidationError("Invalid Member ID")

        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)

        obj.user = self.cleaned_data["user"]

        if commit:
            obj.save()

            # AUTO CREATE REWARD IF PAID
            if obj.paid:
                MonthlyReward.objects.update_or_create(
                    user=obj.user,
                    reward_month=obj.charge_month,
                    defaults={
                        "reward_text": self.cleaned_data["scheme"].monthly_reward
                    }
                )

        return obj
class MonthlyChargeAdmin(admin.ModelAdmin):
    form = MonthlyChargeAdminForm
    list_display = ("user", "charge_month", "paid", "created_at")

# --------------------------
# REGISTER MODELS (after classes!)
# --------------------------
admin.site.register(Scheme)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(MonthlyCharge, MonthlyChargeAdmin)
admin.site.register(MonthlyReward, MonthlyRewardAdmin)

