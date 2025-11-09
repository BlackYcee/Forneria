from django.contrib import admin
from django.urls import path,include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pos/', include('pos.urls')),

    # Esquema OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Documentación ReDoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
