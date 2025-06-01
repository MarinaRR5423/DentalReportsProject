# dental_reports/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template import Template, Context
from django.http import HttpResponse, JsonResponse
from django.db.models import Count
from django.views.decorators.http import require_POST
import json

from .models import (
    ReportTemplate, TemplateCategory, Specialty, GeneratedReport,
    DentalClinic, DentistContact, TipoBloque, BloquePreconfigurado, Plantilla, Variable
)
from .forms import TemplateForm, DynamicReportForm, DentalClinicForm, DentistContactForm, TemplateCategoryForm
from .utils import generate_pdf_from_html, html_to_pdf_response


def home(request):
    """Vista de inicio mejorada con estadísticas y elementos recientes"""
    templates_count = ReportTemplate.objects.count()
    reports_count = GeneratedReport.objects.count()
    clinics_count = DentalClinic.objects.count()
    dentists_count = DentistContact.objects.count()

    recent_templates = ReportTemplate.objects.filter(is_active=True).order_by('-created_at')[:5]
    recent_reports = GeneratedReport.objects.order_by('-created_at')[:5]

    context = {
        'templates_count': templates_count,
        'reports_count': reports_count,
        'clinics_count': clinics_count,
        'dentists_count': dentists_count,
        'recent_templates': recent_templates,
        'recent_reports': recent_reports
    }
    return render(request, 'dental_reports/home.html', context)


@login_required
def template_list(request):
    """Vista para listar plantillas de informes con filtrado mejorado"""
    category_id = request.GET.get('category')

    if category_id:
        templates = ReportTemplate.objects.filter(category_id=category_id, is_active=True)
        category = get_object_or_404(TemplateCategory, id=category_id)
    else:
        templates = ReportTemplate.objects.filter(is_active=True)
        category = None

    categories = TemplateCategory.objects.annotate(num_templates=Count('templates')).order_by('name')

    # También mostrar plantillas visuales si existen
    visual_templates = Plantilla.objects.all().order_by('-fecha_creacion')

    return render(request, 'dental_reports/template_list.html', {
        'templates': templates,
        'visual_templates': visual_templates,
        'categories': categories,
        'selected_category': category
    })


@login_required
def template_create(request):
    """Vista mejorada para crear plantillas con soporte para campos dinámicos"""
    if request.method == 'POST':
        form = TemplateForm(request.POST, user=request.user)
        if form.is_valid():
            template = form.save()
            messages.success(request, f"Plantilla '{template.name}' creada con éxito.")
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateForm(user=request.user)

    # Variables disponibles para el editor visual
    variables = {
        'paciente': ['nombre', 'fecha_nacimiento'],
        'medico': ['nombre', 'especialidad'],
        'datos': ['diagnostico', 'tratamiento', 'diente', 'observaciones', 'revision']
    }

    return render(request, 'dental_reports/template_form.html', {
        'form': form,
        'is_new': True,
        'variables': variables
    })


@login_required
def template_detail(request, pk):
    """Vista para ver detalles de una plantilla con ejemplos de informes"""
    template = get_object_or_404(ReportTemplate, pk=pk)

    # Obtener algunos ejemplos de informes generados con esta plantilla
    example_reports = GeneratedReport.objects.filter(template=template).order_by('-created_at')[:5]

    return render(request, 'dental_reports/template_detail.html', {
        'template': template,
        'example_reports': example_reports
    })


@login_required
def template_edit(request, pk):
    """Vista para editar una plantilla con validación de permisos"""
    template = get_object_or_404(ReportTemplate, pk=pk)

    # Validar permisos - solo el creador o un superusuario pueden editar
    if template.created_by != request.user and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para editar esta plantilla.")
        return redirect('template_detail', pk=template.pk)

    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template, user=request.user)
        if form.is_valid():
            template = form.save()
            messages.success(request, f"Plantilla '{template.name}' actualizada con éxito.")
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateForm(instance=template, user=request.user)

    # Variables disponibles para el editor visual
    variables = {
        'paciente': ['nombre', 'fecha_nacimiento'],
        'medico': ['nombre', 'especialidad'],
        'datos': ['diagnostico', 'tratamiento', 'diente', 'observaciones', 'revision']
    }

    return render(request, 'dental_reports/template_form.html', {
        'form': form,
        'template': template,
        'is_new': False,
        'variables': variables
    })


@login_required
def generate_report(request, template_id):
    """Vista para generar un informe a partir de una plantilla"""
    template = get_object_or_404(ReportTemplate, id=template_id)

    if request.method == 'POST':
        # Crear formulario dinámico con los datos enviados
        form = DynamicReportForm(request.POST, template=template)

        if form.is_valid():
            # Obtener datos del paciente y médico
            patient_name = form.cleaned_data.get('patient_name')
            doctor_name = form.cleaned_data.get('doctor_name')

            # Crear contexto con todos los datos
            context_data = {
                'paciente': {
                    'nombre': patient_name,
                },
                'medico': {
                    'nombre': doctor_name,
                    'especialidad': template.specialty.name if template.specialty else '',
                },
                'datos': form.cleaned_data
            }

            # Renderizar la plantilla con los datos
            try:
                html_template = Template(template.html_content)
                html_context = Context(context_data)
                rendered_content = html_template.render(html_context)

                # Crear el informe en la base de datos
                report = GeneratedReport(
                    template=template,
                    patient_name=patient_name,
                    doctor_name=doctor_name,
                    title=f"Informe para {patient_name} - {template.name}",
                    report_content=rendered_content,
                    form_data=form.cleaned_data,
                    created_by=request.user
                )

                # Generar PDF
                pdf_file = generate_pdf_from_html(rendered_content)
                if pdf_file:
                    filename = f"informe_{patient_name.replace(' ', '_')}_{template.name.replace(' ', '_')}.pdf"
                    report.pdf_file.save(filename, pdf_file)

                report.save()

                messages.success(request, "Informe generado con éxito.")
                return redirect('report_detail', pk=report.id)

            except Exception as e:
                messages.error(request, f"Error al generar el informe: {str(e)}")
    else:
        # Crear formulario dinámico inicial
        form = DynamicReportForm(template=template)

    # Buscar dentistas para autocompletar
    dentists = DentistContact.objects.filter(is_active=True).order_by('last_name', 'first_name')

    return render(request, 'dental_reports/generate_report.html', {
        'form': form,
        'template': template,
        'dentists': dentists
    })


@login_required
def report_list(request):
    """Lista de informes generados con opciones de filtrado"""
    # Filtrar por template si se especifica
    template_id = request.GET.get('template')
    patient_name = request.GET.get('patient')

    reports = GeneratedReport.objects.all().order_by('-created_at')

    if template_id:
        reports = reports.filter(template_id=template_id)

    if patient_name:
        reports = reports.filter(patient_name__icontains=patient_name)

    # Si no es superusuario, mostrar solo sus informes
    if not request.user.is_superuser:
        reports = reports.filter(created_by=request.user)

    # Datos para filtros
    templates = ReportTemplate.objects.filter(is_active=True).order_by('name')

    return render(request, 'dental_reports/report_list.html', {
        'reports': reports,
        'templates': templates,
        'selected_template': template_id,
        'patient_search': patient_name
    })


@login_required
def report_detail(request, pk):
    """Vista para ver un informe generado con opciones para descargar PDF y enviar"""
    report = get_object_or_404(GeneratedReport, pk=pk)

    # Verificar permisos
    if report.created_by != request.user and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para ver este informe.")
        return redirect('report_list')

    # Lista de dentistas para posible envío
    dentists = DentistContact.objects.filter(is_active=True).order_by('last_name', 'first_name')

    return render(request, 'dental_reports/report_detail.html', {
        'report': report,
        'dentists': dentists
    })


@login_required
def report_pdf(request, pk):
    """Vista para generar y descargar un PDF del informe"""
    report = get_object_or_404(GeneratedReport, pk=pk)

    # Verificar permisos
    if report.created_by != request.user and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para descargar este informe.")
        return redirect('report_list')

    # Si ya existe un archivo PDF generado, servir ese
    if report.pdf_file:
        return redirect(report.pdf_file.url)

    # Si no, generar PDF dinámicamente
    filename = f"informe_{report.patient_name.replace(' ', '_')}_{report.id}.pdf"
    return html_to_pdf_response(report.report_content, filename)


# Vistas para gestión de clínicas dentales
@login_required
def clinic_list(request):
    """Lista de clínicas dentales"""
    clinics = DentalClinic.objects.all().order_by('name')
    return render(request, 'dental_reports/clinic_list.html', {'clinics': clinics})


@login_required
def clinic_create(request):
    """Crear nueva clínica dental"""
    if request.method == 'POST':
        form = DentalClinicForm(request.POST)
        if form.is_valid():
            clinic = form.save()
            messages.success(request, f"Clínica '{clinic.name}' creada con éxito.")
            return redirect('clinic_list')
    else:
        form = DentalClinicForm()

    return render(request, 'dental_reports/clinic_form.html', {'form': form, 'is_new': True})


@login_required
def clinic_detail(request, pk):
    """Ver detalles de una clínica dental"""
    clinic = get_object_or_404(DentalClinic, pk=pk)
    dentists = clinic.dentists.all().order_by('last_name', 'first_name')

    return render(request, 'dental_reports/clinic_detail.html', {
        'clinic': clinic,
        'dentists': dentists
    })


@login_required
def clinic_edit(request, pk):
    """Editar clínica dental"""
    clinic = get_object_or_404(DentalClinic, pk=pk)

    if request.method == 'POST':
        form = DentalClinicForm(request.POST, instance=clinic)
        if form.is_valid():
            clinic = form.save()
            messages.success(request, f"Clínica '{clinic.name}' actualizada con éxito.")
            return redirect('clinic_detail', pk=clinic.pk)
    else:
        form = DentalClinicForm(instance=clinic)

    return render(request, 'dental_reports/clinic_form.html', {
        'form': form,
        'clinic': clinic,
        'is_new': False
    })


# Vistas para gestión de contactos de dentistas
@login_required
def dentist_list(request):
    """Lista de contactos de dentistas"""
    # Filtrar por clínica si se especifica
    clinic_id = request.GET.get('clinic')

    if clinic_id:
        dentists = DentistContact.objects.filter(clinic_id=clinic_id).order_by('last_name', 'first_name')
        clinic = get_object_or_404(DentalClinic, id=clinic_id)
    else:
        dentists = DentistContact.objects.all().order_by('last_name', 'first_name')
        clinic = None

    # Datos para filtros
    clinics = DentalClinic.objects.all().order_by('name')

    return render(request, 'dental_reports/dentist_list.html', {
        'dentists': dentists,
        'clinics': clinics,
        'selected_clinic': clinic
    })


@login_required
def dentist_create(request):
    """Crear nuevo contacto de dentista"""
    if request.method == 'POST':
        form = DentistContactForm(request.POST)
        if form.is_valid():
            dentist = form.save()
            messages.success(request, f"Contacto '{dentist.first_name} {dentist.last_name}' creado con éxito.")
            return redirect('dentist_list')
    else:
        form = DentistContactForm()

    return render(request, 'dental_reports/dentist_form.html', {'form': form, 'is_new': True})


@login_required
def dentist_detail(request, pk):
    """Ver detalles de un contacto de dentista"""
    dentist = get_object_or_404(DentistContact, pk=pk)

    # Opcionalmente, puedes buscar informes enviados a este dentista
    # reports = GeneratedReport.objects.filter(sent_to=dentist)

    return render(request, 'dental_reports/dentist_detail.html', {
        'dentist': dentist,
        # 'reports': reports
    })


@login_required
def dentist_edit(request, pk):
    """Editar contacto de dentista"""
    dentist = get_object_or_404(DentistContact, pk=pk)

    if request.method == 'POST':
        form = DentistContactForm(request.POST, instance=dentist)
        if form.is_valid():
            dentist = form.save()
            messages.success(request, f"Contacto '{dentist.first_name} {dentist.last_name}' actualizado con éxito.")
            return redirect('dentist_detail', pk=dentist.pk)
    else:
        form = DentistContactForm(instance=dentist)

    return render(request, 'dental_reports/dentist_form.html', {
        'form': form,
        'dentist': dentist,
        'is_new': False
    })


# Función de utilidad para enviar informes por correo electrónico (opcional)
@login_required
def send_report(request, pk):
    """Enviar informe por correo electrónico a un contacto"""
    report = get_object_or_404(GeneratedReport, pk=pk)

    if request.method == 'POST':
        dentist_id = request.POST.get('dentist_id')
        if dentist_id:
            dentist = get_object_or_404(DentistContact, id=dentist_id)

            try:
                # Aquí iría la lógica de envío de correo electrónico
                # send_email_with_attachment(
                #     subject=f"Informe: {report.title}",
                #     message=f"Adjunto informe médico para paciente {report.patient_name}.",
                #     from_email=settings.DEFAULT_FROM_EMAIL,
                #     recipient_list=[dentist.email],
                #     attachment=report.pdf_file.path if report.pdf_file else None,
                # )

                messages.success(request, f"Informe enviado con éxito a {dentist.first_name} {dentist.last_name}.")
                return redirect('report_detail', pk=report.pk)

            except Exception as e:
                messages.error(request, f"Error al enviar el correo: {str(e)}")
        else:
            messages.error(request, "Por favor selecciona un destinatario.")

    return redirect('report_detail', pk=report.pk)


# Función para crear automáticamente un módulo de utilidades
def create_utils_module(request):
    """Vista para crear automáticamente el módulo de utilidades si no existe"""
    if request.user.is_superuser:
        # Código para crear el archivo utils.py
        utils_content = """
from io import BytesIO
from django.http import HttpResponse
from django.core.files.base import ContentFile
from xhtml2pdf import pisa
import os
from django.conf import settings

def link_callback(uri, rel):
    \"\"\"
    Convierte URIs de HTML a rutas absolutas del sistema de archivos
    \"\"\"
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        return uri

    # Verificar si el archivo existe
    if not os.path.isfile(path):
        raise Exception(f'Media URI {uri} no encontrado')
    return path

def generate_pdf_from_html(html_content):
    \"\"\"Genera un PDF a partir de contenido HTML\"\"\"
    result = BytesIO()

    # Añadir estilos básicos para el PDF
    styled_html = f\"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Informe Dental</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; }}
            h1 {{ font-size: 18px; text-align: center; }}
            h2 {{ font-size: 16px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            table, th, td {{ border: 1px solid #ddd; }}
            th, td {{ padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    \"\"\"

    pdf = pisa.pisaDocument(BytesIO(styled_html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        return ContentFile(result.getvalue())
    return None

def html_to_pdf_response(html_content, filename="informe.pdf"):
    \"\"\"Convierte HTML a respuesta PDF para descargar\"\"\"
    result = BytesIO()

    # Añadir estilos básicos para el PDF
    styled_html = f\"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Informe Dental</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; }}
            h1 {{ font-size: 18px; text-align: center; }}
            h2 {{ font-size: 16px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            table, th, td {{ border: 1px solid #ddd; }}
            th, td {{ padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    \"\"\"

    pdf = pisa.pisaDocument(BytesIO(styled_html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    return HttpResponse('Error al generar el PDF', content_type='text/plain')
"""

        # Escribir el archivo (esto es solo ilustrativo, no se ejecutaría en una vista real)
        # with open('dental_reports/utils.py', 'w') as f:
        #     f.write(utils_content)

        messages.success(request, "Módulo de utilidades creado correctamente.")
        return redirect('admin:index')

    messages.error(request, "No tienes permiso para realizar esta acción.")
    return redirect('home')


@login_required
def category_list(request):
    """Lista todas las categorías de plantillas"""
    # Asegúrate de importar Count si aún no lo has hecho
    from django.db.models import Count

    categories = TemplateCategory.objects.annotate(
        template_count=Count('templates')
    ).order_by('name')

    return render(request, 'dental_reports/category_list.html', {
        'categories': categories
    })


@login_required
def category_create(request):
    """Crear una nueva categoría de plantillas"""
    if request.method == 'POST':
        form = TemplateCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Categoría '{category.name}' creada con éxito.")
            return redirect('category_list')
    else:
        form = TemplateCategoryForm()

    return render(request, 'dental_reports/category_form.html', {
        'form': form,
        'is_new': True
    })


@login_required
def category_edit(request, pk):
    """Editar una categoría existente"""
    category = get_object_or_404(TemplateCategory, pk=pk)

    if request.method == 'POST':
        form = TemplateCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Categoría '{category.name}' actualizada con éxito.")
            return redirect('category_list')
    else:
        form = TemplateCategoryForm(instance=category)

    return render(request, 'dental_reports/category_form.html', {
        'form': form,
        'category': category,
        'is_new': False
    })


# ----- VISTAS ACTUALIZADAS PARA EL EDITOR VISUAL -----

@login_required
def editor_visual(request, template_id=None):
    """Vista para el editor visual tipo Scratch"""
    # Obtener o inicializar la plantilla
    plantilla = None
    if template_id:
        plantilla = get_object_or_404(Plantilla, id=template_id, creador=request.user)

    # Obtener tipos de bloques y bloques preconfigurados
    tipos_bloques = TipoBloque.objects.all()
    bloques = {}

    for tipo in tipos_bloques:
        bloques[tipo.nombre] = BloquePreconfigurado.objects.filter(tipo=tipo)

    # Obtener variables disponibles
    variables = Variable.objects.all()

    context = {
        'titulo': 'Editor Visual de Informes Dentales',
        'tipos_bloques': tipos_bloques,
        'bloques': bloques,
        'variables': variables,
        'plantilla': plantilla,
    }
    return render(request, 'dental_reports/editor_visual.html', context)


@login_required
@require_POST
def guardar_plantilla(request):
    """Guarda una plantilla desde el editor visual con soporte para campos predefinidos"""
    try:
        data = json.loads(request.body)

        # Crear o actualizar plantilla
        template_id = data.get('template_id')
        if template_id:
            plantilla = get_object_or_404(Plantilla, id=template_id, creador=request.user)
        else:
            plantilla = Plantilla(creador=request.user)

        # Actualizar datos
        plantilla.nombre = data.get('name', 'Sin nombre')

        # Guardar todo el objeto JSON (incluye bloques y campos predefinidos)
        plantilla.contenido = data

        plantilla.save()

        return JsonResponse({
            'success': True,
            'id': plantilla.id,
            'message': 'Plantilla guardada correctamente'
        })

    except Plantilla.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def vista_previa_plantilla(request, template_id):
    """Muestra una vista previa de la plantilla con datos de ejemplo"""
    plantilla = get_object_or_404(Plantilla, id=template_id, creador=request.user)

    # Datos de ejemplo para la vista previa
    datos_ejemplo = {
        'nombrePaciente': 'Juan Pérez',
        'edadPaciente': '45',
        'fechaConsulta': '08/05/2025',
        'diagnostico': 'Caries en molar inferior',
        'tratamiento': 'Empaste dental',
        'dentistaNombre': 'Dra. Laura Martínez',
        'proximaCita': '22/05/2025'
    }

    context = {
        'plantilla': plantilla,
        'datos_ejemplo': datos_ejemplo
    }

    return render(request, 'dental_reports/vista_previa_plantilla.html', context)


@login_required
def plantilla_list(request):
    """Lista de plantillas visuales"""
    plantillas = Plantilla.objects.all().order_by('-fecha_creacion')

    # Si no es superusuario, mostrar solo sus plantillas
    if not request.user.is_superuser:
        plantillas = plantillas.filter(creador=request.user)

    return render(request, 'dental_reports/plantilla_list.html', {
        'plantillas': plantillas
    })


@login_required
def template_create(request):
    """Vista mejorada para crear plantillas con soporte para el editor visual y tradicional"""
    if request.method == 'POST':
        form = TemplateForm(request.POST, user=request.user)
        if form.is_valid():
            template = form.save()
            messages.success(request, f"Plantilla '{template.name}' creada con éxito.")
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateForm(user=request.user)

    # Obtener categorías y especialidades para el editor
    categories = TemplateCategory.objects.all().order_by('name')
    specialties = Specialty.objects.all().order_by('name')

    # Definir tipos de bloques para el editor visual
    tipos_bloques = [
        {'nombre': 'Encabezado', 'color': 'bg-primary text-white'},
        {'nombre': 'Información', 'color': 'bg-info text-white'},
        {'nombre': 'Diagnóstico', 'color': 'bg-warning'},
        {'nombre': 'Tratamiento', 'color': 'bg-success text-white'},
        {'nombre': 'Conclusión', 'color': 'bg-danger text-white'},
        {'nombre': 'Instrucciones', 'color': 'bg-secondary text-white'}
    ]

    # Definir bloques predefinidos para cada tipo
    bloques = {
        'Encabezado': [
            {'nombre': 'Título Principal', 'plantilla_html': '<h1 class="text-center">Título del Informe</h1>'},
            {'nombre': 'Subtítulo', 'plantilla_html': '<h2 class="text-center">Subtítulo</h2>'},
            {'nombre': 'Fecha', 'plantilla_html': '<p class="text-end"><strong>Fecha:</strong> {fechaConsulta}</p>'}
        ],
        'Información': [
            {'nombre': 'Datos del Paciente', 'plantilla_html': """
                <div class="patient-info p-3 border rounded">
                    <h4>Información del Paciente</h4>
                    <table class="table table-bordered">
                        <tr><th>Nombre:</th><td>{nombrePaciente}</td></tr>
                        <tr><th>Edad:</th><td>{edad}</td></tr>
                        <tr><th>Teléfono:</th><td>{telefono}</td></tr>
                    </table>
                </div>
            """},
            {'nombre': 'Historia Clínica', 'plantilla_html': """
                <div class="clinical-history p-3 border rounded">
                    <h4>Historia Clínica</h4>
                    <p>El paciente presenta los siguientes antecedentes médicos:</p>
                    <ul>
                        <li>Antecedente 1</li>
                        <li>Antecedente 2</li>
                    </ul>
                </div>
            """}
        ],
        'Diagnóstico': [
            {'nombre': 'Diagnóstico General', 'plantilla_html': """
                <div class="diagnosis p-3 border rounded bg-light">
                    <h4>Diagnóstico</h4>
                    <p>{diagnostico}</p>
                </div>
            """},
            {'nombre': 'Diagnóstico por Pieza', 'plantilla_html': """
                <div class="tooth-diagnosis p-3 border rounded bg-light">
                    <h4>Diagnóstico por Pieza</h4>
                    <table class="table table-bordered">
                        <tr>
                            <th>Pieza</th>
                            <th>Diagnóstico</th>
                        </tr>
                        <tr>
                            <td>{piezaDental}</td>
                            <td>{diagnostico}</td>
                        </tr>
                    </table>
                </div>
            """}
        ],
        'Tratamiento': [
            {'nombre': 'Plan de Tratamiento', 'plantilla_html': """
                <div class="treatment-plan p-3 border rounded">
                    <h4>Plan de Tratamiento</h4>
                    <ol>
                        <li>{tratamiento}</li>
                        <li>Paso de tratamiento 2</li>
                        <li>Paso de tratamiento 3</li>
                    </ol>
                </div>
            """},
            {'nombre': 'Presupuesto', 'plantilla_html': """
                <div class="budget p-3 border rounded">
                    <h4>Presupuesto</h4>
                    <table class="table table-bordered">
                        <tr>
                            <th>Tratamiento</th>
                            <th>Coste</th>
                        </tr>
                        <tr>
                            <td>{tratamiento}</td>
                            <td>€ XXX</td>
                        </tr>
                    </table>
                </div>
            """}
        ],
        'Conclusión': [
            {'nombre': 'Observaciones', 'plantilla_html': """
                <div class="conclusion p-3 border rounded">
                    <h4>Observaciones Finales</h4>
                    <p>Texto con las observaciones finales del profesional.</p>
                </div>
            """},
            {'nombre': 'Firma', 'plantilla_html': """
                <div class="signature mt-5">
                    <div class="row">
                        <div class="col-6">
                            <p>Fecha: {fechaConsulta}</p>
                        </div>
                        <div class="col-6 text-end">
                            <p>Firma del profesional</p>
                            <div class="mt-4">________________________</div>
                        </div>
                    </div>
                </div>
            """}
        ],
        'Instrucciones': [
            {'nombre': 'Post-Tratamiento', 'plantilla_html': """
                <div class="instructions p-3 border rounded bg-light">
                    <h4>Instrucciones Post-Tratamiento</h4>
                    <ul>
                        <li>Instrucción 1</li>
                        <li>Instrucción 2</li>
                        <li>Instrucción 3</li>
                    </ul>
                </div>
            """},
            {'nombre': 'Próxima Cita', 'plantilla_html': """
                <div class="next-appointment p-3 border rounded bg-light">
                    <h4>Próxima Cita</h4>
                    <p><strong>Fecha:</strong> {proximaCita}</p>
                    <p><strong>Motivo:</strong> Seguimiento</p>
                </div>
            """}
        ]
    }

    # Variables disponibles para el editor
    variables = {
        'paciente': ['nombre', 'fecha_nacimiento', 'edad', 'telefono', 'email'],
        'medico': ['nombre', 'especialidad'],
        'datos_clinicos': ['diagnostico', 'tratamiento', 'piezaDental', 'fechaConsulta', 'proximaCita', 'observaciones']
    }

    context = {
        'form': form,
        'is_new': True,
        'variables': variables,
        'tipos_bloques': tipos_bloques,
        'bloques': bloques,
        'categories': categories,
        'specialties': specialties
    }

    return render(request, 'dental_reports/template_form.html', {
        'form': form,
        'is_new': True,
        'variables': variables,
        'tipos_bloques': tipos_bloques,
        'bloques': bloques
    })


@login_required
def save_template_ajax(request):
    """
    Vista para guardar una plantilla dental mediante AJAX.
    Recibe los datos del editor visual y los guarda en la base de datos.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_id = data.get('template_id')
            name = data.get('name')
            category_id = data.get('category_id')
            specialty_id = data.get('specialty_id')
            blocks = data.get('blocks', [])
            fields = data.get('fields', {})

            # Crear o actualizar la plantilla
            if template_id and template_id.isdigit():
                # Actualizar plantilla existente
                template = get_object_or_404(ReportTemplate, id=template_id, created_by=request.user)
                template.name = name
            else:
                # Crear nueva plantilla
                template = ReportTemplate(name=name, created_by=request.user)

            # Asignar categoría y especialidad si se proporcionan
            if category_id and category_id.isdigit():
                template.category_id = category_id

            if specialty_id and specialty_id.isdigit():
                template.specialty_id = specialty_id

            # Crear contenido HTML a partir de los bloques
            html_content = ""
            for block in blocks:
                html_content += block.get('content', '')

            # Guardar contenido HTML para el editor tradicional
            template.html_content = html_content

            # Guardar también el contenido en formato JSON para el editor visual
            # Asegúrate de que tu modelo ReportTemplate tenga un campo visual_content
            # Si no lo tiene, puedes almacenarlo en otro campo o añadir este campo
            if hasattr(template, 'visual_content'):
                template_content = {
                    'blocks': blocks,
                    'fields': fields
                }
                template.visual_content = json.dumps(template_content)

            # Guardar la plantilla
            template.save()

            return JsonResponse({
                'success': True,
                'template_id': template.id,
                'redirect_url': reverse('template_detail', kwargs={'pk': template.id})
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })
