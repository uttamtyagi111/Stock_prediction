from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Authentication URLs
    path('auth/', include('authentication.urls')),

    # Email sender URLs
    path('api/', include('email_sender.urls')),

    # Admin URL
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
