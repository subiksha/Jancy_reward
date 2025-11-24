from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone

from datetime import timedelta
import csv
from django.http import HttpResponse

from app.models import (
    Scheme,
    UserProfile,
    MonthlyCharge,
    MonthlyReward,
    EmailToken,
    generate_member_id
)

from app.utils import generate_monthly_entries

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from datetime import date

from .models import UserProfile, MonthlyCharge, MonthlyReward

@login_required
def quick_mark_paid(request, user_id):
    if not request.user.is_superuser:
        return redirect("/")

    today_month = date.today().replace(day=1)

    user = User.objects.get(id=user_id)
    profile = user.userprofile

    charge, created = MonthlyCharge.objects.get_or_create(
        user=user,
        charge_month=today_month,
        defaults={"paid": True}
    )

    charge.paid = True
    charge.save()

    MonthlyReward.objects.update_or_create(
        user=user,
        reward_month=today_month,
        defaults={"reward_text": profile.scheme.monthly_reward_text}
    )

    return redirect("/admin/auth/user/")

# ---------------------------------------------------
# PUBLIC PAGES
# ---------------------------------------------------
def dashboard(request):
    return render(request, "dashboard.html")


def scheme_list(request):
    return render(request, "schemes.html", {"schemes": Scheme.objects.all()})


# ---------------------------------------------------
# PASSWORD SETUP EMAIL
# ---------------------------------------------------
def send_password_setup(request, user_id):
    user = get_object_or_404(User, id=user_id)

    token = EmailToken.objects.create(
        user=user,
        expiry=timezone.now() + timedelta(hours=24)
    )

    link = request.build_absolute_uri(f"/set-password/{token.token}/")

    message = f"""
Hello {user.email},

Welcome! Please click the link below to set your password:

{link}

This link is valid for 24 hours.

Thank you.
"""

    send_mail(
        subject="Set your password",
        message=message,
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False
    )

    messages.success(request, "Password setup email sent successfully!")
    return redirect('/admin/auth/user/')


def set_password_page(request, token):
    token_obj = get_object_or_404(EmailToken, token=token)

    if not token_obj.is_valid():
        return render(request, "token_invalid.html")

    return render(request, "set_password.html", {"token": token})


def set_password_submit(request, token):
    token_obj = get_object_or_404(EmailToken, token=token)

    if not token_obj.is_valid():
        return render(request, "token_invalid.html")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect(f"/set-password/{token}/")

        user = token_obj.user
        user.set_password(password)
        user.save()

        token_obj.used = True
        token_obj.save()

        messages.success(request, "Password created successfully! Please log in.")
        return redirect("/")

    return redirect(f"/set-password/{token}/")


# ---------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------
from django.contrib.auth.models import User
from .models import UserProfile

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect("/")

    profiles = UserProfile.objects.select_related("user", "scheme").all()

    return render(request, "admin_dashboard.html", {
        "profiles": profiles
    })


# ---------------------------------------------------
# ADMIN MEMBERS LIST
# ---------------------------------------------------
@login_required
def admin_members(request):
    if not request.user.is_superuser:
        return redirect("/")

    profiles = UserProfile.objects.select_related("user", "scheme")

    members = []
    for profile in profiles:
        last_reward = MonthlyReward.objects.filter(
            user=profile.user,
            is_unlocked=True
        ).order_by('-month').first()

        last_reward_month = last_reward.month if last_reward else "None"

        members.append({
            "name": f"{profile.user.first_name} {profile.user.last_name}",
            "member_id": profile.member_id,
            "scheme": profile.scheme.name if profile.scheme else "",
            "email": profile.user.email,
            "last_reward": last_reward_month,
        })

    return render(request, "admin_members.html", {
        "title": "Members List",
        "members": members
    })
@login_required
def admin_members_summary(request):
    if not request.user.is_superuser:
        return redirect("/")

    profiles = UserProfile.objects.select_related("user", "scheme")

    members = []
    for profile in profiles:
        user = profile.user

        charges_paid = MonthlyCharge.objects.filter(
            user=user,
            status="Paid"
        ).count()

        rewards_received = MonthlyReward.objects.filter(
            user=user,
            is_unlocked=True
        ).count()

        join_date = user.date_joined.strftime("%Y-%m-%d")

        members.append({
            "name": f"{user.first_name} {user.last_name}",
            "member_id": profile.member_id,
            "scheme": profile.scheme.name,
            "join_date": join_date,
            "charges_paid": charges_paid,
            "rewards_received": rewards_received,
        })

    return render(request, "admin_members_summary.html", {
        "members": members,
        "title": "Member Accumulation Summary"
    })
@login_required
def admin_member_summary_single(request, member_id):
    if not request.user.is_superuser:
        return redirect("/")

    profile = get_object_or_404(UserProfile, member_id=member_id)
    user = profile.user

    charges_paid = MonthlyCharge.objects.filter(
        user=user,
        status="Paid"
    ).count()

    rewards_received = MonthlyReward.objects.filter(
        user=user,
        is_unlocked=True
    ).count()

    join_date = user.date_joined.strftime("%Y-%m-%d")

    context = {
        "title": "Member Summary",
        "name": f"{user.first_name} {user.last_name}",
        "member_id": member_id,
        "scheme": profile.scheme.name,
        "join_date": join_date,
        "charges_paid": charges_paid,
        "rewards_received": rewards_received
    }

    return render(request, "admin_member_summary_single.html", context)
@login_required
def export_members_summary_csv(request):
    if not request.user.is_superuser:
        return redirect("/")

    profiles = UserProfile.objects.select_related("user", "scheme")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="members_summary.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Member ID", "Scheme", "Join Date", "Charges Paid", "Rewards Received"])

    for profile in profiles:
        user = profile.user

        charges_paid = MonthlyCharge.objects.filter(user=user, status="Paid").count()
        rewards_received = MonthlyReward.objects.filter(user=user, is_unlocked=True).count()

        writer.writerow([
            f"{user.first_name} {user.last_name}",
            profile.member_id,
            profile.scheme.name,
            user.date_joined.strftime("%Y-%m-%d"),
            charges_paid,
            rewards_received,
        ])

    return response
@login_required
def export_member_single_csv(request, member_id):
    if not request.user.is_superuser:
        return redirect("/")

    profile = get_object_or_404(UserProfile, member_id=member_id)
    user = profile.user

    charges_paid = MonthlyCharge.objects.filter(user=user, status="Paid").count()
    rewards_received = MonthlyReward.objects.filter(user=user, is_unlocked=True).count()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{member_id}_summary.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Member ID", "Scheme", "Join Date", "Charges Paid", "Rewards Received"])

    writer.writerow([
        f"{user.first_name} {user.last_name}",
        member_id,
        profile.scheme.name,
        user.date_joined.strftime("%Y-%m-%d"),
        charges_paid,
        rewards_received,
    ])

    return response


# ---------------------------------------------------
# EXPORT MEMBERS CSV
# ---------------------------------------------------
@login_required
def export_members_csv(request):
    if not request.user.is_superuser:
        return redirect("/")

    profiles = UserProfile.objects.select_related("user", "scheme")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="members.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Member ID", "Scheme", "Email", "Last Reward"])

    for profile in profiles:
        last_reward = MonthlyReward.objects.filter(
            user=profile.user,
            is_unlocked=True
        ).order_by('-month').first()

        last_reward_month = last_reward.month if last_reward else "None"

        writer.writerow([
            f"{profile.user.first_name} {profile.user.last_name}",
            profile.member_id,
            profile.scheme.name if profile.scheme else "",
            profile.user.email,
            last_reward_month
        ])

    return response


# ---------------------------------------------------
# USER DASHBOARD
# ---------------------------------------------------
@login_required
def user_dashboard(request):
    profile = UserProfile.objects.get(user=request.user)

    unlocked = MonthlyReward.objects.filter(
        user=request.user,
        is_unlocked=True
    ).count()

    context = {
        "title": "User Dashboard",
        "member_id": profile.member_id,
        "scheme_name": profile.scheme.name if profile.scheme else "No Scheme Assigned",
        "amount": (profile.scheme.amount if profile.scheme else 0),
        "unlocked_rewards": unlocked,
    }

    return render(request, "user_dashboard.html", context)


# ---------------------------------------------------
# USER PAGES
# ---------------------------------------------------
@login_required
def user_scheme(request):
    profile = UserProfile.objects.get(user=request.user)

    return render(request, "user_scheme.html", {
        "title": "My Scheme",
        "scheme": profile.scheme,
        "member_id": profile.member_id
    })


@login_required
def user_charges(request):
    charges = MonthlyCharge.objects.filter(user=request.user).order_by('-month')

    return render(request, "user_charges.html", {
        "title": "Monthly Charges",
        "charges": charges
    })


@login_required
def user_rewards(request):
    rewards = MonthlyReward.objects.filter(user=request.user).order_by('-month')

    return render(request, "user_rewards.html", {
        "title": "Monthly Rewards",
        "rewards": rewards
    })


@login_required
def user_profile(request):
    profile = UserProfile.objects.get(user=request.user)

    return render(request, "user_profile.html", {
        "title": "My Profile",
        "profile": profile,
        "user": request.user,
        "scheme": profile.scheme,
    })


# ---------------------------------------------------
# ADMIN MONTHLY PROCESSING
# ---------------------------------------------------
@login_required
def run_monthly_now(request):
    if not request.user.is_superuser:
        return redirect("/")

    generate_monthly_entries()
    messages.success(request, "Monthly processing completed!")
    return redirect("/admin-dashboard/")


# ---------------------------------------------------
# ADMIN CHARGES & REWARDS
# ---------------------------------------------------
@login_required
def admin_charges(request):
    charges = MonthlyCharge.objects.all().order_by('-month')
    return render(request, "admin_charges.html", {"charges": charges})


@login_required
def admin_rewards(request):
    rewards = MonthlyReward.objects.all().order_by('-month')
    return render(request, "admin_rewards.html", {"rewards": rewards})


# ---------------------------------------------------
# MARK CHARGE AS PAID
# ---------------------------------------------------
@login_required
def mark_charge_paid(request, charge_id):
    charge = get_object_or_404(MonthlyCharge, id=charge_id)

    charge.status = "Paid"
    charge.paid_at = timezone.now()
    charge.save()

    reward = MonthlyReward.objects.get(
        user=charge.user,
        scheme=charge.scheme,
        month=charge.month
    )
    reward.is_unlocked = True
    reward.unlocked_at = timezone.now()
    reward.save()

    return redirect('/admin-charges/')


# ---------------------------------------------------
# ADMIN: ADD USER
# ---------------------------------------------------
@login_required
def admin_add_user(request):
    if not request.user.is_superuser:
        return redirect("/")

    if request.method == "POST":
        first = request.POST.get("first_name")
        last = request.POST.get("last_name")
        email = request.POST.get("email")

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first,
            last_name=last,
            password=User.objects.make_random_password()
        )

        UserProfile.objects.create(user=user)

        messages.success(request, "User created successfully.")
        return redirect("/admin-dashboard/")

    return render(request, "admin_add_user.html")

# ---------------------------------------------------
# LOGIN REDIRECT AFTER SUCCESSFUL LOGIN
# ---------------------------------------------------
from django.contrib.auth.decorators import login_required

@login_required
def login_redirect(request):
    if request.user.is_superuser:
        return redirect('/admin-dashboard/')
    else:
        return redirect('/user-dashboard/')
from .models import Scheme

def admin_edit_profile(request, user_id):
    if not request.user.is_superuser:
        return redirect("/")

    profile = UserProfile.objects.get(user_id=user_id)
    schemes = Scheme.objects.all()

    if request.method == "POST":
        scheme_id = request.POST.get("scheme")
        profile.scheme = Scheme.objects.get(id=scheme_id)
        profile.save()
        messages.success(request, "Profile updated")
        return redirect("/admin-dashboard/")

    return render(request, "admin_edit_profile.html", {
        "profile": profile,
        "schemes": schemes
    })
