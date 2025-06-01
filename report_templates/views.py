from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template import Template, Context
from django.http import HttpResponse
from django.core.files.base import ContentFile

from .models import ReportTemplate, TemplateCategory, Specialty, GeneratedReport
from .forms import TemplateForm, DynamicReportForm

from io import BytesIO
import json
from xhtml2pdf import pisa
import os

@login_required
def template_list(request):
    """Vista para listar plantillas de informes"""
    templates = ReportTemplate.objects.all()
    category_id = request.GET.get('category')
    if category_id:
        templates = templates.filter(category_id=category_id)
    categories = TemplateCategory.objects.all()
    return render(request, 'report_templates/template_list.html', {
        'templates': templates,
        'categories': categories,
        'selected_category': category_id
    })

@login_required
def template_create(request):
    """Vista para crear una nueva plantilla"""
    if request.method == 'POST':
        form = TemplateForm(request.POST, user=request.user)
        if form.is_valid():
            template = form.save()
            messages.success(request, f"Plantilla '{template.name}' creada con éxito.")
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateForm(user=request.user)
    return render(request, 'report_templates/template_form.html', {
        'form': form,
        'is_new': True
    })

@login_required
def template_edit(request, pk):
    """Vista para editar una plantilla existente"""
    template = get_object_or_404(ReportTemplate, pk=pk)
    if template.created_by != request.user and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para editar esta plantilla.")
        return redirect('template_list')

    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template, user=request.user)
        if form.is_valid():
            template = form.save()
            messages.success(request, f"Plantilla '{template.name}' actualizada con éxito.")
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateForm(instance=template, user=request.user)

    return render(request, 'report_templates/template_form.html', {
        'form': form,
        'template': template,
        'is_new': False
    })

@login_required
def template_detail(request, pk):
    """Vista para ver detalles de una plantilla"""
    template = get_object_or_404(ReportTemplate, pk=pk)
    return render(request, 'report_templates/template_detail.html', {
        'template': template
    })

@login_required
def generate_report(request, template_id):
    """Vista para generar un informe a partir de una plantilla"""
    template = get_object_or_404(ReportTemplate, id=template_id)

    if request.method == 'POST':
        form = DynamicReportForm(request.POST, template=template)

        if form.is_valid():
            patient_name = request.POST.get('patient_name')
            doctor_name = request.POST.get('doctor_name')

            if not patient_name or not doctor_name:
                messages.error(request, "Debes ingresar el nombre del paciente y el médico.")
                return render(request, 'report_templates/generate_report.html', {
                    'form': form,
                    'template': template,
                })

            # Preparar contexto para la plantilla HTML
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

            # Renderizar contenido HTML
            try:
                html_template = Template(template.html_content)
                html_context = Context(context_data)
                rendered_html = html_template.render(html_context)
            except Exception as e:
                messages.error(request, f"Error al renderizar el informe: {str(e)}")
                return redirect('template_detail', pk=template.pk)

            # Convertir a PDF usando xhtml2pdf
            result = BytesIO()
            pdf_status = pisa.CreatePDF(rendered_html, dest=result)

            if pdf_status.err:
                messages.error(request, "Hubo un error al generar el PDF.")
                return redirect('template_detail', pk=template.pk)

            # Guardar el informe generado en la base de datos
            report = GeneratedReport.objects.create(
                template=template,
                patient_name=patient_name,
                doctor_name=doctor_name,
                data=form.cleaned_data,
                created_by=request.user
            )
            report.pdf_file.save(f'informe_{report.id}.pdf', ContentFile(result.getvalue()))
            result.close()

            messages.success(request, "Informe generado exitosamente.")
            return redirect('report_detail', pk=report.pk)
    else:
        form = DynamicReportForm(template=template)

    return render(request, 'report_templates/generate_report.html', {
        'form': form,
        'template': template
    })
