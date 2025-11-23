from calendar import month_name
from django.forms.widgets import DateInput
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import path, reverse
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, Scheme, MonthlyCharge, MonthlyReward
from django.shortcuts import render, redirect
from django.shortcuts import redirect
from django.contrib import admin
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


def mark_monthly_charges_paid(modeladmin, request, queryset):
    """
    Admin action to mark monthly charges as paid for selected users
    """
    current_month = timezone.now().replace(day=1)
    month_name_str = month_name[current_month.month]
    
    with transaction.atomic():
        created_charges = 0
        created_rewards = 0
        
        for user in queryset:
            # Get or create monthly charge
            charge, charge_created = MonthlyCharge.objects.get_or_create(
                user=user,
                charge_month=current_month,
                defaults={'paid': True}
            )
            
            if charge_created:
                created_charges += 1
                
                # Auto-create reward if user has a scheme
                try:
                    user_profile = user.userprofile
                    if user_profile.scheme:
                        MonthlyReward.objects.get_or_create(
                            user=user,
                            reward_month=current_month,
                            defaults={
                                'reward_text': user_profile.scheme.monthly_reward_text
                            }
                        )
                        created_rewards += 1
                except UserProfile.DoesNotExist:
                    pass
        
        if created_charges > 0:
            messages.success(
                request, 
                f'Successfully created {created_charges} monthly charges and {created_rewards} rewards for {month_name_str} {current_month.year}'
            )
        else:
            messages.info(request, 'No new monthly charges were created (they may already exist)')

mark_monthly_charges_paid.short_description = "Mark monthly charges as paid for current month"
def mark_monthly_charges_paid(modeladmin, request, queryset):
    """
    Admin action to mark monthly charges as paid for selected users
    """
    current_month = timezone.now().replace(day=1)
    month_name_str = month_name[current_month.month]
    
    with transaction.atomic():
        created_charges = 0
        created_rewards = 0
        
        for user in queryset:
            # Get or create monthly charge
            charge, charge_created = MonthlyCharge.objects.get_or_create(
                user=user,
                charge_month=current_month,
                defaults={'paid': True}
            )
            
            if charge_created:
                created_charges += 1
                
                # Auto-create reward if user has a scheme
                try:
                    user_profile = user.userprofile
                    if user_profile.scheme:
                        MonthlyReward.objects.get_or_create(
                            user=user,
                            reward_month=current_month,
                            defaults={
                                'reward_text': user_profile.scheme.monthly_reward_text
                            }
                        )
                        created_rewards += 1
                except UserProfile.DoesNotExist:
                    pass
        
        if created_charges > 0:
            messages.success(
                request, 
                f'Successfully created {created_charges} monthly charges and {created_rewards} rewards for {month_name_str} {current_month.year}'
            )
        else:
            messages.info(request, 'No new monthly charges were created (they may already exist)')

mark_monthly_charges_paid.short_description = "Mark monthly charges as paid for current month"# --------------------------
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
# CUSTOM USER ADMIN WITH MEMBER ID
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_member_id', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'userprofile__member_id')
    
    def get_member_id(self, obj):
        try:
            return obj.userprofile.member_id
        except UserProfile.DoesNotExist:
            return 'N/A'
    get_member_id.short_description = 'Member ID'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('userprofile')


# USER PROFILE INLINE FOR USER ADMIN
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    readonly_fields = ('member_id',)
    fields = ('member_id', 'scheme')


# EXTENDED USER ADMIN WITH PROFILE
class UserAdminWithProfile(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_member_id', 'monthly_charge_checkbox', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'userprofile__member_id')
    actions = [mark_monthly_charges_paid]
    
    def get_member_id(self, obj):
        try:
            return obj.userprofile.member_id
        except UserProfile.DoesNotExist:
            return 'N/A'
    get_member_id.short_description = 'Member ID'
    
    def monthly_charge_checkbox(self, obj):
        """
        Display a checkbox for monthly charge selection
        """
        current_month = timezone.now().replace(day=1)
        
        try:
            charge = MonthlyCharge.objects.get(user=obj, charge_month=current_month)
            if charge.paid:
                return format_html(
                    '<input type="checkbox" name="user_ids" value="{}" checked disabled> ✓ Paid',
                    obj.id
                )
            else:
                return format_html(
                    '<input type="checkbox" name="user_ids" value="{}"> Pending',
                    obj.id
                )
        except MonthlyCharge.DoesNotExist:
            return format_html(
                '<input type="checkbox" name="user_ids" value="{}"> Not Charged',
                obj.id
            )
    monthly_charge_checkbox.short_description = 'Monthly Charges'
    monthly_charge_checkbox.allow_tags = True
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('userprofile')
    
    def changelist_view(self, request, extra_context=None):
        """
        Override changelist_view to add custom button
        """
        extra_context = extra_context or {}
        extra_context['monthly_charge_button'] = True
        return super().changelist_view(request, extra_context)
    
    def get_urls(self):
        """
        Add custom URL for monthly charges processing
        """
        urls = super().get_urls()
        custom_urls = [
            path('mark-monthly-charges-paid/', self.admin_site.admin_view(self.mark_monthly_charges_paid_view), name='mark_monthly_charges_paid'),
        ]
        return custom_urls + urls
    
    def mark_monthly_charges_paid_view(self, request):
        """
        Custom view to handle monthly charges payment
        """
        if request.method == 'POST':
            user_ids = request.POST.getlist('user_ids')
            current_month = timezone.now().replace(day=1)
            month_name_str = month_name[current_month.month]
            
            with transaction.atomic():
                created_charges = 0
                created_rewards = 0
                
                for user_id in user_ids:
                    try:
                        user = User.objects.get(id=user_id)
                        
                        # Get or create monthly charge
                        charge, charge_created = MonthlyCharge.objects.get_or_create(
                            user=user,
                            charge_month=current_month,
                            defaults={'paid': True}
                        )
                        
                        if charge_created:
                            created_charges += 1
                            
                            # Auto-create reward if user has a scheme
                            try:
                                user_profile = user.userprofile
                                if user_profile.scheme:
                                    MonthlyReward.objects.get_or_create(
                                        user=user,
                                        reward_month=current_month,
                                        defaults={
                                            'reward_text': user_profile.scheme.monthly_reward_text
                                        }
                                    )
                                    created_rewards += 1
                            except UserProfile.DoesNotExist:
                                pass
                    
                    except User.DoesNotExist:
                        continue
                
                if created_charges > 0:
                    messages.success(
                        request, 
                        f'Successfully created {created_charges} monthly charges and {created_rewards} rewards for {month_name_str} {current_month.year}'
                    )
                else:
                    messages.info(request, 'No new monthly charges were created')
        
        return redirect('admin:auth_user_changelist')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('userprofile')
    get_member_id.short_description = 'Member ID'
# --------------------------
# REGISTER MODELS (after classes!)
# --------------------------
# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdminWithProfile)

admin.site.register(Scheme)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(MonthlyCharge, MonthlyChargeAdmin)
admin.site.register(MonthlyReward, MonthlyRewardAdmin)