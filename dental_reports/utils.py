# dental_reports/utils.py
from io import BytesIO
from django.http import HttpResponse
from django.core.files.base import ContentFile
from xhtml2pdf import pisa
import os
from django.conf import settings


def link_callback(uri, rel):
    """
    Convierte URIs de HTML a rutas absolutas del sistema de archivos
    """
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
    """Genera un PDF a partir de contenido HTML"""
    result = BytesIO()

    # Añadir estilos básicos para el PDF
    styled_html = f"""
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
    """

    pdf = pisa.pisaDocument(BytesIO(styled_html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        return ContentFile(result.getvalue())
    return None


def html_to_pdf_response(html_content, filename="informe.pdf"):
    """Convierte HTML a respuesta PDF para descargar"""
    result = BytesIO()

    # Añadir estilos básicos para el PDF
    styled_html = f"""
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
    """

    pdf = pisa.pisaDocument(BytesIO(styled_html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    return HttpResponse('Error al generar el PDF', content_type='text/plain')
