"""
URL configuration for testdrive project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static                  # For static files
from accounts.views import LogoutViewAllowGet


urlpatterns = [
    path('admin/', admin.site.urls),                # Admin route
    path('', include('vehicles.urls')),             # Homepage is the vehicles' catalogue
    path('bookings/', include('bookings.urls')),    # Bookings route
    path('captcha/', include('captcha.urls')),      # Captcha route for booking verification
    path('accounts/logout/', LogoutViewAllowGet.as_view(next_page='/'), name='logout'),
    path('accounts/', include('accounts.urls')),    # Accounts route for login, logout, etc.


]

# IMPORTANT: This serves media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ALSO ensure static files are served during development (this should already exist)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])