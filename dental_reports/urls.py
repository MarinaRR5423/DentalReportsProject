from django.urls import path
from django.views.generic.base import RedirectView
from . import views

# Recomendaría usar el espacio de nombres para evitar colisiones de nombres de URL
app_name = 'dental_reports'

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),

    # Plantillas básicas
    path('templates/', views.template_list, name='template_list'),
    path('templates/new/', views.template_create, name='template_create'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:template_id>/generate/', views.generate_report, name='generate_report'),
    path('templates/category/<int:category_id>/', views.template_list, name='template_category'),

    # Categorías de plantillas
    path('categories/', views.category_list, name='category_list'),
    path('categories/new/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),

    # Informes generados
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/pdf/', views.report_pdf, name='report_pdf'),
    path('reports/<int:pk>/send/', views.send_report, name='send_report'),

    # Clínicas dentales
    path('clinics/', views.clinic_list, name='clinic_list'),
    path('clinics/new/', views.clinic_create, name='clinic_create'),
    path('clinics/<int:pk>/', views.clinic_detail, name='clinic_detail'),
    path('clinics/<int:pk>/edit/', views.clinic_edit, name='clinic_edit'),

    # Contactos de dentistas
    path('dentists/', views.dentist_list, name='dentist_list'),
    path('dentists/new/', views.dentist_create, name='dentist_create'),
    path('dentists/<int:pk>/', views.dentist_detail, name='dentist_detail'),
    path('dentists/<int:pk>/edit/', views.dentist_edit, name='dentist_edit'),

    # Utilidad para crear el módulo utils.py
    path('utils/create/', views.create_utils_module, name='create_utils_module'),

    # Atajos URL prácticos
    path('t/<int:pk>/', views.template_detail, name='template_short'),  # Atajo para plantillas
    path('r/<int:pk>/', views.report_detail, name='report_short'),  # Atajo para informes

    # URLs para el editor visual - Versión corregida y adaptada
    path('visual-editor/', views.editor_visual, name='editor_visual'),
    path('visual-editor/<int:template_id>/', views.editor_visual, name='editor_visual_edit'),
    path('api/save-template/', views.guardar_plantilla, name='guardar_plantilla'),
    path('visual-editor/<int:template_id>/preview/', views.vista_previa_plantilla, name='vista_previa_plantilla'),

    # Nueva URL para integrar el editor visual dentro del flujo actual de creación de plantillas
    path('templates/new/visual/', views.editor_visual, name='template_create_visual'),

    # Favicon
    path('favicon.ico', RedirectView.as_view(url='/static/dental_reports/img/favicon.ico')),

    path('save_template_ajax/', views.save_template_ajax, name='save_template_ajax'),

]
