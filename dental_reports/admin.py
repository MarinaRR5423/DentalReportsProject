from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    TemplateCategory, Specialty, ReportTemplate,
    GeneratedReport, DentalClinic, DentistContact
)


# Registrar una sola vez cada modelo
@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'template_count')
    search_fields = ('name',)

    def template_count(self, obj):
        return obj.templates.count()

    template_count.short_description = "Núm. Plantillas"


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'template_count')
    search_fields = ('name',)

    def template_count(self, obj):
        return obj.report_templates.count()

    template_count.short_description = "Núm. Plantillas"


class TemplatePreviewInline(admin.TabularInline):
    model = GeneratedReport
    extra = 0
    fields = ('title', 'patient_name', 'doctor_name', 'created_at')
    readonly_fields = ('title', 'patient_name', 'doctor_name', 'created_at')
    can_delete = False
    max_num = 5
    verbose_name_plural = "Informes generados con esta plantilla"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = (
    'name', 'category', 'specialty', 'is_active', 'is_public', 'created_by', 'created_at', 'preview_button')
    list_filter = ('is_active', 'is_public', 'category', 'specialty', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'html_preview')
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'category', 'specialty', 'description', ('is_active', 'is_public'))
        }),
        ('Contenido', {
            'fields': ('html_content', 'html_preview'),
            'classes': ('collapse',),
        }),
        ('Campos Dinámicos', {
            'fields': ('fields_schema',),
            'classes': ('collapse',),
        }),
        ('Información Adicional', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    inlines = [TemplatePreviewInline]

    def html_preview(self, obj):
        if obj.html_content:
            return format_html(
                '<div style="border: 1px solid #ddd; padding: 10px; max-height: 300px; overflow-y: auto;">{}</div>',
                obj.html_content)
        return "Sin contenido HTML"

    html_preview.short_description = "Vista previa HTML"

    def preview_button(self, obj):
        if obj.pk:
            url = reverse('template_detail', args=[obj.pk])
            return format_html('<a class="button" href="{}">Ver Plantilla</a>', url)
        return ""

    preview_button.short_description = "Acciones"

    def save_model(self, request, obj, form, change):
        if not change:  # si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'template_link', 'patient_name', 'doctor_name', 'created_at', 'pdf_download')
    list_filter = ('created_at', 'template')
    search_fields = ('title', 'patient_name', 'doctor_name')
    readonly_fields = ('created_at', 'report_preview', 'report_data_preview')
    fieldsets = (
        ('Información del Informe', {
            'fields': ('title', 'template', 'patient_name', 'doctor_name', 'created_by', 'created_at', 'version')
        }),
        ('Contenido', {
            'fields': ('report_content', 'report_preview'),
            'classes': ('collapse',),
        }),
        ('Datos del Formulario', {
            'fields': ('form_data', 'report_data_preview'),
            'classes': ('collapse',),
        }),
        ('Archivo PDF', {
            'fields': ('pdf_file',),
        }),
    )

    def template_link(self, obj):
        if obj.template:
            url = reverse('admin:dental_reports_reporttemplate_change', args=[obj.template.id])
            return format_html('<a href="{}">{}</a>', url, obj.template.name)
        return "N/A"

    template_link.short_description = "Plantilla"

    def pdf_download(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Descargar PDF</a>', obj.pdf_file.url)
        return "No disponible"

    pdf_download.short_description = "PDF"

    def report_preview(self, obj):
        if obj.report_content:
            return format_html(
                '<div style="border: 1px solid #ddd; padding: 10px; max-height: 300px; overflow-y: auto;">{}</div>',
                obj.report_content)
        return "Sin contenido"

    report_preview.short_description = "Vista previa del informe"

    def report_data_preview(self, obj):
        if obj.form_data:
            html = '<dl>'
            for key, value in obj.form_data.items():
                html += f'<dt>{key}</dt><dd>{value}</dd>'
            html += '</dl>'
            return format_html(html)
        return "Sin datos"

    report_data_preview.short_description = "Datos del formulario"


@admin.register(DentalClinic)
class DentalClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'email', 'website', 'dentist_count')
    search_fields = ('name', 'email', 'phone')
    fieldsets = (
        ('Información de la Clínica', {
            'fields': ('name', 'address', 'phone', 'email', 'website')
        }),
    )

    def dentist_count(self, obj):
        return obj.dentists.count()

    dentist_count.short_description = "Núm. Dentistas"


class ClinicFilter(admin.SimpleListFilter):
    title = 'Clínica'
    parameter_name = 'clinic'

    def lookups(self, request, model_admin):
        clinics = DentalClinic.objects.all()
        return [(clinic.id, clinic.name) for clinic in clinics]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(clinic_id=self.value())
        return queryset


@admin.register(DentistContact)
class DentistContactAdmin(admin.ModelAdmin):
    list_display = ('full_name_display', 'email', 'phone', 'clinic_link', 'is_active')
    list_filter = ('is_active', ClinicFilter)
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    fieldsets = (
        ('Información Personal', {
            'fields': (('first_name', 'last_name'), 'email', 'phone', 'address')
        }),
        ('Información Profesional', {
            'fields': ('clinic', 'notes', 'is_active')
        }),
    )

    def full_name_display(self, obj):
        return f"Dr. {obj.first_name} {obj.last_name}"

    full_name_display.short_description = "Nombre"

    def clinic_link(self, obj):
        if obj.clinic:
            url = reverse('admin:dental_reports_dentalclinic_change', args=[obj.clinic.id])
            return format_html('<a href="{}">{}</a>', url, obj.clinic.name)
        return "Sin clínica"

    clinic_link.short_description = "Clínica"


# Personalizar el sitio de administración
admin.site.site_header = "Administración de Informes Dentales"
admin.site.site_title = "Panel de Administración | Sistema de Informes Dentales"
admin.site.index_title = "Panel de Control"
