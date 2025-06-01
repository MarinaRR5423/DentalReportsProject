# dental_reports/utils.py
from io import BytesIO
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from xhtml2pdf import pisa
import os
import uuid
import logging

# Configuración de logging
logger = logging.getLogger(__name__)


def link_callback(uri, rel):
    """
    Convierte URIs de HTML a rutas absolutas del sistema de archivos
    """
    try:
        if uri.startswith(settings.MEDIA_URL):
            path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        elif uri.startswith(settings.STATIC_URL):
            path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
        else:
            return uri

        # Verificar si el archivo existe
        if not os.path.isfile(path):
            logger.warning(f'Media URI {uri} no encontrado')
            return uri  # Devolver URI original si no se encuentra, en lugar de lanzar excepción

        return path
    except Exception as e:
        logger.error(f'Error en link_callback: {e}')
        return uri  # Devolver URI original en caso de error


def generate_pdf_from_template(template_name, context=None):
    """
    Genera un PDF a partir de una plantilla Django y un contexto
    """
    if context is None:
        context = {}

    # Renderizar la plantilla con el contexto
    html_content = render_to_string(template_name, context)
    return generate_pdf_from_html(html_content)


def generate_pdf_from_html(html_content):
    """
    Genera un PDF a partir de contenido HTML

    Args:
        html_content: String con contenido HTML

    Returns:
        ContentFile con el PDF generado o None si hay error
    """
    result = BytesIO()

    # Añadir estilos básicos para el PDF
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Informe Dental</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{ 
                font-family: Arial, sans-serif; 
                font-size: 12px; 
                line-height: 1.5;
            }}
            h1 {{ 
                font-size: 18px; 
                text-align: center; 
                color: #2c3e50;
                margin-bottom: 20px;
            }}
            h2 {{ 
                font-size: 16px; 
                color: #3498db;
                margin-top: 15px;
            }}
            h3 {{ 
                font-size: 14px; 
                color: #2c3e50;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-bottom: 15px;
            }}
            table, th, td {{ 
                border: 1px solid #ddd; 
            }}
            th, td {{ 
                padding: 8px; 
                text-align: left; 
            }}
            th {{ 
                background-color: #f2f2f2; 
                font-weight: bold;
            }}
            img {{ 
                max-width: 100%; 
                height: auto; 
            }}
            .header {{ 
                display: table;
                width: 100%;
                margin-bottom: 20px;
            }}
            .header-left {{
                display: table-cell;
                width: 50%;
            }}
            .header-right {{
                display: table-cell;
                width: 50%;
                text-align: right;
            }}
            .footer {{
                position: fixed;
                bottom: 0;
                width: 100%;
                text-align: center;
                font-size: 10px;
                color: #7f8c8d;
                padding-bottom: 10px;
            }}
            .page-number:before {{
                content: "Página " counter(page) " de " counter(pages);
            }}
        </style>
    </head>
    <body>
        {html_content}
        <div class="footer">
            <span class="page-number"></span>
        </div>
    </body>
    </html>
    """

    try:
        pdf = pisa.pisaDocument(
            BytesIO(styled_html.encode("UTF-8")),
            result,
            link_callback=link_callback,
            encoding='utf-8'
        )

        if not pdf.err:
            return ContentFile(result.getvalue())
        else:
            logger.error(f"Error al generar PDF: {pdf.err}")
            return None
    except Exception as e:
        logger.error(f"Excepción al generar PDF: {str(e)}")
        return None


def html_to_pdf_response(html_content, filename="informe.pdf", as_attachment=False):
    """
    Convierte HTML a respuesta PDF para visualizar o descargar

    Args:
        html_content: String con contenido HTML
        filename: Nombre del archivo para la descarga
        as_attachment: Si es True, fuerza la descarga del PDF
                      Si es False, muestra el PDF en el navegador

    Returns:
        HttpResponse con el PDF o mensaje de error
    """
    result = BytesIO()

    # Añadir estilos básicos para el PDF
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Informe Dental</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{ 
                font-family: Arial, sans-serif; 
                font-size: 12px; 
                line-height: 1.5;
            }}
            h1 {{ 
                font-size: 18px; 
                text-align: center; 
                color: #2c3e50;
                margin-bottom: 20px;
            }}
            h2 {{ 
                font-size: 16px; 
                color: #3498db;
                margin-top: 15px;
            }}
            h3 {{ 
                font-size: 14px; 
                color: #2c3e50;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-bottom: 15px;
            }}
            table, th, td {{ 
                border: 1px solid #ddd; 
            }}
            th, td {{ 
                padding: 8px; 
                text-align: left; 
            }}
            th {{ 
                background-color: #f2f2f2; 
                font-weight: bold;
            }}
            img {{ 
                max-width: 100%; 
                height: auto; 
            }}
            .header {{ 
                display: table;
                width: 100%;
                margin-bottom: 20px;
            }}
            .header-left {{
                display: table-cell;
                width: 50%;
            }}
            .header-right {{
                display: table-cell;
                width: 50%;
                text-align: right;
            }}
            .footer {{
                position: fixed;
                bottom: 0;
                width: 100%;
                text-align: center;
                font-size: 10px;
                color: #7f8c8d;
                padding-bottom: 10px;
            }}
            .page-number:before {{
                content: "Página " counter(page) " de " counter(pages);
            }}
        </style>
    </head>
    <body>
        {html_content}
        <div class="footer">
            <span class="page-number"></span>
        </div>
    </body>
    </html>
    """

    try:
        pdf = pisa.pisaDocument(
            BytesIO(styled_html.encode("UTF-8")),
            result,
            link_callback=link_callback,
            encoding='utf-8'
        )

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            disposition = 'attachment' if as_attachment else 'inline'
            response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
            return response
        else:
            logger.error(f"Error al generar PDF para respuesta: {pdf.err}")
            return HttpResponse('Error al generar el PDF: Problema de conversión.', content_type='text/plain',
                                status=500)
    except Exception as e:
        logger.error(f"Excepción al generar PDF para respuesta: {str(e)}")
        return HttpResponse(f'Error al generar el PDF: {str(e)}', content_type='text/plain', status=500)


def save_pdf_to_model(model_instance, html_content, field_name='pdf_file', filename=None):
    """
    Genera un PDF a partir de HTML y lo guarda en un campo FileField de un modelo

    Args:
        model_instance: Instancia del modelo donde guardar el PDF
        html_content: String con contenido HTML
        field_name: Nombre del campo FileField en el modelo
        filename: Nombre personalizado para el archivo

    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    if filename is None:
        filename = f"report_{uuid.uuid4().hex}.pdf"

    pdf_content = generate_pdf_from_html(html_content)
    if pdf_content:
        # Obtener el campo FileField del modelo
        file_field = getattr(model_instance, field_name)

        # Si ya existe un archivo, eliminarlo para no acumular archivos
        if file_field:
            try:
                file_field.delete(save=False)
            except Exception as e:
                logger.warning(f"No se pudo eliminar el archivo PDF anterior: {e}")

        # Guardar el nuevo archivo
        file_field.save(filename, pdf_content, save=True)
        return True
    return False


def send_report_email(report, dentist, subject=None, message=None, template=None):
    """
    Envía un informe por email a un dentista

    Args:
        report: Objeto Report (informe a enviar)
        dentist: Objeto Dentist (destinatario)
        subject: Asunto personalizado (opcional)
        message: Mensaje personalizado (opcional)
        template: Plantilla de email a utilizar (opcional)

    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        if not subject:
            subject = f"Informe dental: {report.title}"

        context = {
            'report': report,
            'dentist': dentist,
            'message': message or ""
        }

        if template:
            # Usar plantilla HTML para el email
            html_content = render_to_string(f'dental_reports/email_templates/{template}.html', context)
            text_content = strip_tags(html_content)
        else:
            # Email simple sin plantilla HTML
            text_content = message or f"Adjuntamos el informe dental {report.title} para el paciente {report.patient_name}."
            html_content = f"<p>{text_content}</p>"

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[dentist.email]
        )

        email.attach_alternative(html_content, "text/html")

        # Adjuntar el PDF si existe
        if report.pdf_file and hasattr(report.pdf_file, 'path') and os.path.exists(report.pdf_file.path):
            with open(report.pdf_file.path, 'rb') as f:
                email.attach(f"Informe_{report.title}.pdf", f.read(), 'application/pdf')
        else:
            # Si no hay PDF guardado, generarlo al vuelo
            html_content = render_to_string('dental_reports/pdf_templates/report.html', {'report': report})
            pdf_content = generate_pdf_from_html(html_content)
            if pdf_content:
                email.attach(f"Informe_{report.title}.pdf", pdf_content.read(), 'application/pdf')

        email.send()
        return True
    except Exception as e:
        logger.error(f"Error al enviar email con informe: {e}")
        return False
