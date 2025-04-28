# finance_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('tracker/', include('tracker.urls')),


    # pswrd reset urls
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='tracker/password_reset_form.html',
             email_template_name='tracker/password_reset_email.html',
             subject_template_name='tracker/password_reset_subject.txt',
             success_url='/password_reset/done/'
         ),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='tracker/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='tracker/password_reset_confirm.html',
             success_url='/reset/done/'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='tracker/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    path('', RedirectView.as_view(pattern_name='tracker:dashboard', permanent=False)), # root redirect

    # REMOVED THIS LINE: path('', include('tracker.urls')),
]