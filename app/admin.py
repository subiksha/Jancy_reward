from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.forms.widgets import DateInput
from django.utils.html import format_html
from datetime import date

from .models import UserProfile, Scheme, MonthlyCharge, MonthlyReward


# -------------------------------------------------------------------
# HELPER: SAFE MONTH RANGE WITHOUT dateutil
# -------------------------------------------------------------------
def generate_months(start, end):
    months = []
    y, m = start.year, start.month
    while (y < end.year) or (y == end.year and m <= end.month):
        months.append(date(y, m, 1))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


# -------------------------------------------------------------------
# INLINE PROFILE
# -------------------------------------------------------------------
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    readonly_fields = ("member_id",)


# -------------------------------------------------------------------
# MONTH PICKER WIDGET
# -------------------------------------------------------------------
class MonthPickerInput(DateInput):
    input_type = "month"


# -------------------------------------------------------------------
# MONTHLY CHARGE FORM
# -------------------------------------------------------------------
class MonthlyChargeAdminForm(forms.ModelForm):
    member_input = forms.CharField(label="Member ID", required=True)

    class Meta:
        model = MonthlyCharge
        fields = ["member_input", "charge_month", "paid"]
        widgets = {"charge_month": MonthPickerInput()}

    def clean(self):
        cleaned = super().clean()
        member_id = cleaned.get("member_input")

        try:
            profile = UserProfile.objects.get(member_id=member_id)
            cleaned["user"] = profile.user
            cleaned["scheme"] = profile.scheme
        except UserProfile.DoesNotExist:
            raise forms.ValidationError("Invalid Member ID")

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.user = self.cleaned_data["user"]

        if commit:
            obj.save()

            # Auto reward
            if obj.paid:
                MonthlyReward.objects.update_or_create(
                    user=obj.user,
                    reward_month=obj.charge_month,
                    defaults={"reward_text": self.cleaned_data["scheme"].monthly_reward_text}
                )
        return obj


class MonthlyChargeAdmin(admin.ModelAdmin):
    form = MonthlyChargeAdminForm
    list_display = ("user", "charge_month", "paid", "created_at")


admin.site.register(MonthlyCharge, MonthlyChargeAdmin)


# -------------------------------------------------------------------
# MONTHLY REWARD ADMIN
# -------------------------------------------------------------------
class MonthlyRewardAdmin(admin.ModelAdmin):
    list_display = ("user", "reward_text", "reward_month", "created_at")
    readonly_fields = ("user", "reward_text", "reward_month", "created_at")

    def has_add_permission(self, request):
        return False


admin.site.register(MonthlyReward, MonthlyRewardAdmin)


# -------------------------------------------------------------------
# SAFE USER ADMIN
# -------------------------------------------------------------------
class UserAdminWithProfile(UserAdmin):
    inlines = [UserProfileInline]

    list_display = (
        "username", "email", "first_name", "last_name",
        "get_member_id", "monthly_charge_status",
        "pending_months", "mark_paid_button", "is_staff"
    )

    def get_member_id(self, obj):
        try:
            return obj.userprofile.member_id
        except:
            return "-"
    get_member_id.short_description = "Member ID"

    def monthly_charge_status(self, obj):
        try:
            today = date.today().replace(day=1)
            paid = MonthlyCharge.objects.filter(
                user=obj, charge_month=today, paid=True
            ).exists()
            return "✔ Paid" if paid else "⚠ Pending"
        except:
            return "?"
    monthly_charge_status.short_description = "This Month"

    def pending_months(self, obj):
        try:
            start = obj.date_joined.date().replace(day=1)
        except:
            return "?"

        today = date.today().replace(day=1)

        all_months = generate_months(start, today)
        paid_months = MonthlyCharge.objects.filter(
            user=obj, paid=True
        ).values_list("charge_month", flat=True)

        paid_set = set([d.replace(day=1) for d in paid_months])
        pending = [m for m in all_months if m not in paid_set]

        return f"{len(pending)}"
    pending_months.short_description = "Pending"

    def mark_paid_button(self, obj):
        return format_html(
            '<a href="/admin/mark-paid/{}/" '
            'style="padding:4px 8px;background:#4caf50;color:white;'
            'border-radius:4px;text-decoration:none;">Mark Paid</a>',
            obj.id
        )
    mark_paid_button.short_description = "Quick Pay"


admin.site.unregister(User)
admin.site.register(User, UserAdminWithProfile)

admin.site.register(Scheme)
admin.site.register(UserProfile)
