from django.db import models
from django.contrib.auth.models import User


class TemplateCategory(models.Model):
    """Categoría de plantillas (ej: Consulta, Cirugía, Endodoncia)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Template Categories"


class Specialty(models.Model):
    """Especialidades médicas"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Specialties"


class ReportTemplate(models.Model):
    """Modelo para almacenar plantillas de informes médicos"""
    name = models.CharField(max_length=100)
    category = models.ForeignKey(TemplateCategory, on_delete=models.SET_NULL, null=True, related_name='templates')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='report_templates')
    description = models.TextField(blank=True)

    # Contenido HTML de la plantilla
    html_content = models.TextField(help_text="Contenido HTML con marcadores de posición como {{paciente.nombre}}")

    # Estructura de datos para los campos dinámicos
    fields_schema = models.JSONField(default=dict, help_text="Estructura JSON con los campos del formulario")

    # Metadatos
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False, help_text="Si es público para todos los médicos")

    def __str__(self):
        return self.name


class GeneratedReport(models.Model):
    """Informes médicos generados a partir de plantillas"""
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, null=True)

    # Relaciones
    patient = models.CharField(max_length=100, help_text="Nombre del paciente")
    doctor = models.CharField(max_length=100, help_text="Nombre del doctor")

    # Contenido del informe
    title = models.CharField(max_length=200)
    report_content = models.TextField(help_text="HTML con el contenido final del informe")
    form_data = models.JSONField(help_text="Datos capturados en el formulario, en formato JSON")

    # Archivo generado
    pdf_file = models.FileField(upload_to='reports/%Y/%m/', blank=True, null=True)

    # Metadatos
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} (v{self.version})"

    class Meta:
        ordering = ['-created_at']
