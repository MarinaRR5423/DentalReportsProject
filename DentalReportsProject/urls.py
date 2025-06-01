"""
URL configuration for DentalReportsProject project.

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
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

# Definición de manejadores de errores personalizados - opcional
# handler404 = 'dental_reports.views.custom_page_not_found'
# handler500 = 'dental_reports.views.custom_server_error'
# handler403 = 'dental_reports.views.custom_permission_denied'

urlpatterns = [
    # Administración de Django
    path('admin/', admin.site.urls),

    # Rutas de autenticación para login, logout, cambio de contraseña, etc.
    path('accounts/', include('django.contrib.auth.urls')),

    # Ruta principal a la aplicación dental_reports con namespace
    path('', include('dental_reports.urls', namespace='dental_reports')),

    # Página de mantenimiento (opcional)
    # path('maintenance/', TemplateView.as_view(template_name='maintenance.html'), name='maintenance'),

    # Sitemap (opcional)
    # path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# Configuración para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Opcional: Servir archivos estáticos en desarrollo (generalmente no es necesario)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Opcional: Incluir django-debug-toolbar para desarrollo
    # try:
    #     import debug_toolbar
    #     urlpatterns = [
    #         path('__debug__/', include(debug_toolbar.urls)),
    #     ] + urlpatterns
    # except ImportError:
    #     pass
