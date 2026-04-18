from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('student/', include('student.urls')),
    path('teacher/', include('teacher.urls')),
    path('adminpanel/', include('adminpanel.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
