# finance_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView # Import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Keep the tracker URLs under the /tracker/ prefix
    path('tracker/', include('tracker.urls')),

    # Redirect the root URL ('') to the tracker dashboard URL ('/tracker/')
    # 'tracker:dashboard' is the namespaced URL name for your dashboard view
    # permanent=False means it's a temporary redirect (HTTP 302)
    path('', RedirectView.as_view(pattern_name='tracker:dashboard', permanent=False)),

    # REMOVED THIS LINE: path('', include('tracker.urls')),
]