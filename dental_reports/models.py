# dental_reports/models.py

from django.db import models
from django.contrib.auth.models import User


class TemplateCategory(models.Model):
    """Categoría de plantillas (ej: Endodoncia, Periodoncia, etc.)"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categoría de Plantilla"
        verbose_name_plural = "Categorías de Plantillas"


class Specialty(models.Model):
    """Especialidades dentales"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Especialidad"
        verbose_name_plural = "Especialidades"


class ReportTemplate(models.Model):
    """Modelo para almacenar plantillas de informes dentales"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    category = models.ForeignKey(TemplateCategory, on_delete=models.SET_NULL, null=True,
                                 related_name='templates', verbose_name="Categoría")
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='report_templates', verbose_name="Especialidad")
    description = models.TextField(blank=True, verbose_name="Descripción")

    # Contenido HTML de la plantilla
    html_content = models.TextField(verbose_name="Contenido HTML",
                                    help_text="Contenido HTML con marcadores como {{paciente.nombre}}")

    # Estructura de datos para los campos dinámicos
    fields_schema = models.JSONField(default=dict, verbose_name="Esquema de Campos",
                                     help_text="Estructura JSON con los campos del formulario")

    # Metadatos
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='created_templates', verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_public = models.BooleanField(default=False, verbose_name="Público",
                                    help_text="Si es accesible para todos los usuarios")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Plantilla de Informe"
        verbose_name_plural = "Plantillas de Informes"


class GeneratedReport(models.Model):
    """Informes generados a partir de plantillas"""
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, null=True,
                                 verbose_name="Plantilla")

    # Información del paciente y médico
    patient_name = models.CharField(max_length=255, verbose_name="Nombre del paciente")
    doctor_name = models.CharField(max_length=255, verbose_name="Nombre del doctor")

    # Contenido del informe
    title = models.CharField(max_length=200, verbose_name="Título")
    report_content = models.TextField(verbose_name="Contenido del informe")
    form_data = models.JSONField(verbose_name="Datos del formulario")

    # Archivo generado
    pdf_file = models.FileField(upload_to='reports/%Y/%m/', blank=True, null=True,
                                verbose_name="Archivo PDF")

    # Metadatos
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    version = models.PositiveIntegerField(default=1, verbose_name="Versión")

    def __str__(self):
        return f"{self.title} (v{self.version})"

    class Meta:
        verbose_name = "Informe Generado"
        verbose_name_plural = "Informes Generados"
        ordering = ['-created_at']


class DentalClinic(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


# Añade estos modelos a dental_reports/models.py
class DentalClinic(models.Model):
    """Modelo para clínicas o gabinetes dentales"""
    name = models.CharField(max_length=200, verbose_name="Nombre del gabinete")
    address = models.TextField(blank=True, verbose_name="Dirección")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Página web")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Clínica Dental"
        verbose_name_plural = "Clínicas Dentales"


class DentistContact(models.Model):
    """Modelo para contactos de dentistas"""
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellidos")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    address = models.TextField(blank=True, verbose_name="Dirección personal")

    # Relación con gabinete (opcional)
    clinic = models.ForeignKey(DentalClinic, on_delete=models.SET_NULL,
                               null=True, blank=True,
                               related_name='dentists',
                               verbose_name="Gabinete dental")

    notes = models.TextField(blank=True, verbose_name="Notas")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name}"

    def full_name(self):
        return f"Dr. {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Contacto Dentista"
        verbose_name_plural = "Contactos Dentistas"
        ordering = ['last_name', 'first_name']


# Si no tienes estos modelos ya, añádelos

class TipoBloque(models.Model):
    nombre = models.CharField(max_length=50)
    icono = models.CharField(max_length=50)
    color = models.CharField(max_length=20)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class BloquePreconfigurado(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoBloque, on_delete=models.CASCADE)
    plantilla_html = models.TextField()
    configuracion_defecto = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.nombre} ({self.tipo.nombre})"


# Si ya tienes un modelo de plantillas, puedes adaptarlo agregando el campo contenido
class Plantilla(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    creador = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    # Este campo almacenará la configuración de los bloques en formato JSON
    contenido = models.JSONField(default=dict)

    def __str__(self):
        return self.nombre


class Variable(models.Model):
    nombre = models.CharField(max_length=50)
    etiqueta = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.etiqueta
