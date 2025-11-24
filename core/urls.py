from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import views as auth_views

# Import all views FIRST
from app.views import (
    dashboard,
    scheme_list,
    user_dashboard,
    user_profile,
    user_scheme,
    user_charges,
    user_rewards,
    run_monthly_now,
    admin_add_user,
    admin_members,
    admin_dashboard,
    admin_charges,
    admin_rewards,
    admin_members_summary,
    admin_member_summary_single,
    export_members_summary_csv,
    export_member_single_csv,
    mark_charge_paid,
    export_members_csv,   # <-- FIXED (added)
    login_redirect,
    admin_edit_profile,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Default landing page = LOGIN PAGE
    path('', auth_views.LoginView.as_view(template_name="login.html"), name='login'),
    path('login-redirect/', login_redirect, name='login_redirect'),

    # Public pages
    path('schemes/', scheme_list),

    # User panel
    path('user-dashboard/', user_dashboard, name='user_dashboard'),
    path('user-scheme/', user_scheme, name='user_scheme'),
    path('user-charges/', user_charges, name='user_charges'),
    path('user-rewards/', user_rewards, name='user_rewards'),
    path('user-profile/', user_profile, name='user_profile'),
    
    # Admin panel
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-charges/', admin_charges, name='admin_charges'),
    path('admin-rewards/', admin_rewards, name='admin_rewards'),
    path('admin-add-user/', admin_add_user, name='admin_add_user'),
    path('admin-run-monthly/', run_monthly_now, name='run_monthly_now'),
    path('mark-charge-paid/<int:charge_id>/', mark_charge_paid, name='mark_charge_paid'),
    path('admin-members-summary/', admin_members_summary, name='admin_members_summary'),
    path('admin-member-summary/<str:member_id>/', admin_member_summary_single, name='admin_member_summary_single'),

    path('admin-members-summary/export/', export_members_summary_csv, name='export_members_summary_csv'),
    path('admin-member-summary/<str:member_id>/export/', export_member_single_csv, name='export_member_single_csv'),
    path("admin-user-profile/<int:user_id>/", admin_edit_profile, name="admin_edit_profile"),

    # Members list + Export
    path('admin-members/', admin_members, name='admin_members'),
    path('admin-members/export/', export_members_csv, name='export_members_csv'),

    # Password change
    path(
        'password_change/',
        auth_views.PasswordChangeView.as_view(template_name="password_change.html"),
        name='password_change'
    ),
    path(
        'password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name="password_change_done.html"),
        name='password_change_done'
    ),
]
from app.views import quick_mark_paid

path("admin/mark-paid/<int:user_id>/", quick_mark_paid),
# Password Reset URLs
path("password-reset/", 
     auth_views.PasswordResetView.as_view(template_name="password_reset.html"), 
     name="password_reset"),

path("password-reset/done/", 
     auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"), 
     name="password_reset_done"),

path("reset/<uidb64>/<token>/", 
     auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), 
     name="password_reset_confirm"),

path("reset/done/", 
     auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), 
     name="password_reset_complete"),
