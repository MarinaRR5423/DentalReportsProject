from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dental_reports.models import TemplateCategory, Specialty, ReportTemplate


class Command(BaseCommand):
    help = 'Crea plantillas predefinidas de informes dentales'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creando plantillas predefinidas...')

        # Crear categorías
        endodoncia, created = TemplateCategory.objects.get_or_create(
            name="Endodoncia",
            defaults={"description": "Plantillas para informes de endodoncia"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Categoría Endodoncia creada'))

        periodoncia, created = TemplateCategory.objects.get_or_create(
            name="Periodoncia",
            defaults={"description": "Plantillas para informes de periodoncia"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Categoría Periodoncia creada'))

        general, created = TemplateCategory.objects.get_or_create(
            name="Informe General",
            defaults={"description": "Plantillas para informes dentales generales"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Categoría Informe General creada'))

        # Crear especialidades
        esp_endodoncia, created = Specialty.objects.get_or_create(
            name="Endodoncia",
            defaults={"description": "Especialidad en el tratamiento del interior del diente"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Especialidad Endodoncia creada'))

        esp_periodoncia, created = Specialty.objects.get_or_create(
            name="Periodoncia",
            defaults={"description": "Especialidad en el tratamiento de las encías y tejidos de soporte del diente"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Especialidad Periodoncia creada'))

        # Obtener un usuario administrador
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                self.stdout.write(self.style.SUCCESS(f'Usuario administrador encontrado: {admin_user.username}'))
            else:
                self.stdout.write(self.style.WARNING('No se encontró un usuario administrador'))

        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('No se encontró un usuario administrador'))
            admin_user = None

        # Plantilla 1: Informe de Endodoncia Básico
        template1_html = """
        <div class="container report-container">
            <div class="report-header">
                <h2 class="text-center">INFORME DE ENDODONCIA</h2>
                <hr>
                <div class="row mt-4">
                    <div class="col-md-6">
                        <p><strong>Paciente:</strong> {{paciente.nombre}}</p>
                    </div>
                    <div class="col-md-6 text-end">
                        <p><strong>Fecha:</strong> {% now "d/m/Y" %}</p>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Médico:</strong> {{medico.nombre}}</p>
                    </div>
                </div>
            </div>

            <div class="report-content mt-4">
                <h4>Diente Tratado</h4>
                <p>{{datos.diente}}</p>

                <h4>Diagnóstico</h4>
                <p>{{datos.diagnostico}}</p>

                <h4>Procedimiento Realizado</h4>
                <p>{{datos.procedimiento}}</p>

                <h4>Observaciones</h4>
                <p>{{datos.observaciones}}</p>
            </div>

            <div class="report-footer mt-5">
                <div class="row">
                    <div class="col-md-6">
                        <p>Revisión recomendada en: {{datos.revision}} semanas</p>
                    </div>
                    <div class="col-md-6 text-end">
                        <p>____________________</p>
                        <p>Firma del especialista</p>
                    </div>
                </div>
            </div>
        </div>
        """

        template1_fields = {
            "fields": [
                {
                    "name": "diente",
                    "label": "Diente tratado (número)",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "diagnostico",
                    "label": "Diagnóstico",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "procedimiento",
                    "label": "Procedimiento realizado",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "observaciones",
                    "label": "Observaciones",
                    "type": "textarea",
                    "required": False
                },
                {
                    "name": "revision",
                    "label": "Revisión recomendada (semanas)",
                    "type": "number",
                    "required": True
                }
            ]
        }

        template1, created = ReportTemplate.objects.get_or_create(
            name="Informe de Endodoncia Básico",
            defaults={
                "category": endodoncia,
                "specialty": esp_endodoncia,
                "description": "Plantilla básica para informes de tratamiento de endodoncia",
                "html_content": template1_html,
                "fields_schema": template1_fields,
                "created_by": admin_user,
                "is_active": True,
                "is_public": True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Plantilla "Informe de Endodoncia Básico" creada'))

        # Plantilla 2: Informe de Periodoncia
        template2_html = """
        <div class="container report-container">
            <div class="report-header">
                <h2 class="text-center">INFORME DE PERIODONCIA</h2>
                <hr>
                <div class="row mt-4">
                    <div class="col-md-6">
                        <p><strong>Paciente:</strong> {{paciente.nombre}}</p>
                    </div>
                    <div class="col-md-6 text-end">
                        <p><strong>Fecha:</strong> {% now "d/m/Y" %}</p>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Médico:</strong> {{medico.nombre}}</p>
                    </div>
                </div>
            </div>

            <div class="report-content mt-4">
                <h4>Evaluación Periodontal</h4>
                <p>{{datos.evaluacion}}</p>

                <h4>Zonas Afectadas</h4>
                <p>{{datos.zonas_afectadas}}</p>

                <h4>Tratamiento Recomendado</h4>
                <p>{{datos.tratamiento}}</p>

                <h4>Instrucciones para el Paciente</h4>
                <p>{{datos.instrucciones}}</p>

                {% if datos.requiere_cirugia == "Sí" %}
                <div class="alert alert-warning">
                    <h5>Requiere Intervención Quirúrgica</h5>
                    <p>{{datos.detalles_cirugia}}</p>
                </div>
                {% endif %}
            </div>

            <div class="report-footer mt-5">
                <div class="row">
                    <div class="col-md-6">
                        <p>Próxima cita: {{datos.proxima_cita}}</p>
                    </div>
                    <div class="col-md-6 text-end">
                        <p>____________________</p>
                        <p>Firma del periodoncista</p>
                    </div>
                </div>
            </div>
        </div>
        """

        template2_fields = {
            "fields": [
                {
                    "name": "evaluacion",
                    "label": "Evaluación periodontal",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "zonas_afectadas",
                    "label": "Zonas afectadas",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "tratamiento",
                    "label": "Tratamiento recomendado",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "instrucciones",
                    "label": "Instrucciones para el paciente",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "requiere_cirugia",
                    "label": "¿Requiere intervención quirúrgica?",
                    "type": "select",
                    "options": ["No", "Sí"],
                    "required": True
                },
                {
                    "name": "detalles_cirugia",
                    "label": "Detalles de la cirugía (si aplica)",
                    "type": "textarea",
                    "required": False
                },
                {
                    "name": "proxima_cita",
                    "label": "Fecha próxima cita",
                    "type": "date",
                    "required": True
                }
            ]
        }

        template2, created = ReportTemplate.objects.get_or_create(
            name="Informe de Periodoncia",
            defaults={
                "category": periodoncia,
                "specialty": esp_periodoncia,
                "description": "Plantilla para informes de evaluación y tratamiento periodontal",
                "html_content": template2_html,
                "fields_schema": template2_fields,
                "created_by": admin_user,
                "is_active": True,
                "is_public": True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Plantilla "Informe de Periodoncia" creada'))

        # Plantilla 3: Informe Dental General
        template3_html = """
        <div class="container report-container">
            <div class="report-header">
                <h2 class="text-center">INFORME DENTAL</h2>
                <hr>
                <div class="row mt-4">
                    <div class="col-md-6">
                        <p><strong>Paciente:</strong> {{paciente.nombre}}</p>
                    </div>
                    <div class="col-md-6 text-end">
                        <p><strong>Fecha:</strong> {% now "d/m/Y" %}</p>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Médico:</strong> {{medico.nombre}}</p>
                    </div>
                </div>
            </div>

            <div class="report-content mt-4">
                <h4>Motivo de la Consulta</h4>
                <p>{{datos.motivo}}</p>

                <h4>Examen Clínico</h4>
                <p>{{datos.examen_clinico}}</p>

                <h4>Diagnóstico</h4>
                <p>{{datos.diagnostico}}</p>

                <h4>Plan de Tratamiento</h4>
                <p>{{datos.plan_tratamiento}}</p>

                <h4>Presupuesto Estimado</h4>
                <p>{{datos.presupuesto}} €</p>
            </div>

            <div class="report-footer mt-5">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Teléfono para citas:</strong> {{datos.telefono_citas}}</p>
                    </div>
                    <div class="col-md-6 text-end">
                        <p>____________________</p>
                        <p>Firma del dentista</p>
                    </div>
                </div>
            </div>
        </div>
        """

        template3_fields = {
            "fields": [
                {
                    "name": "motivo",
                    "label": "Motivo de la consulta",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "examen_clinico",
                    "label": "Examen clínico",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "diagnostico",
                    "label": "Diagnóstico",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "plan_tratamiento",
                    "label": "Plan de tratamiento",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "presupuesto",
                    "label": "Presupuesto estimado (€)",
                    "type": "number",
                    "required": True
                },
                {
                    "name": "telefono_citas",
                    "label": "Teléfono para citas",
                    "type": "text",
                    "required": True
                }
            ]
        }

        template3, created = ReportTemplate.objects.get_or_create(
            name="Informe Dental General",
            defaults={
                "category": general,
                "specialty": None,  # Sin especialidad específica
                "description": "Plantilla general para informes dentales",
                "html_content": template3_html,
                "fields_schema": template3_fields,
                "created_by": admin_user,
                "is_active": True,
                "is_public": True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Plantilla "Informe Dental General" creada'))

        self.stdout.write(self.style.SUCCESS('¡Plantillas predefinidas creadas con éxito!'))
