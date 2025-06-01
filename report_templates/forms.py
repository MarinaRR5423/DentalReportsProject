from django import forms
from .models import ReportTemplate, TemplateCategory
import json


class TemplateForm(forms.ModelForm):
    """Formulario para crear y editar plantillas"""

    class Meta:
        model = ReportTemplate
        fields = ['name', 'category', 'specialty', 'description', 'html_content', 'is_active', 'is_public']
        widgets = {
            'html_content': forms.Textarea(attrs={'rows': 15, 'class': 'html-editor'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Campos adicionales para el constructor de campos dinámicos
        self.fields['fields_json'] = forms.CharField(
            widget=forms.HiddenInput(),
            required=False,
            initial=json.dumps(self.instance.fields_schema) if self.instance.pk else '{}'
        )

    def clean_fields_json(self):
        fields_json = self.cleaned_data.get('fields_json', '{}')
        try:
            fields_data = json.loads(fields_json)
            return fields_data
        except json.JSONDecodeError:
            raise forms.ValidationError("Formato JSON inválido para los campos del formulario")

    def save(self, commit=True):
        template = super().save(commit=False)

        # Asignar el usuario creador si es una nueva plantilla
        if not template.pk and self.user:
            template.created_by = self.user

        # Guardar la estructura de campos
        template.fields_schema = self.cleaned_data.get('fields_json', {})

        if commit:
            template.save()

        return template


class DynamicReportForm(forms.Form):
    """Formulario dinámico generado a partir de la estructura de campos de una plantilla"""

    def __init__(self, *args, **kwargs):
        template = kwargs.pop('template', None)
        super().__init__(*args, **kwargs)

        if template:
            # Obtener la estructura de campos
            fields_schema = template.fields_schema
            fields = fields_schema.get('fields', []) if isinstance(fields_schema, dict) else []

            # Crear campos dinámicamente
            for field_config in fields:
                field_name = field_config.get('name')
                field_label = field_config.get('label', field_name)
                field_type = field_config.get('type', 'text')
                field_required = field_config.get('required', False)
                field_options = field_config.get('options', [])
                field_help = field_config.get('help_text', '')

                # Crear el campo según su tipo
                if field_name:
                    if field_type == 'text':
                        self.fields[field_name] = forms.CharField(
                            label=field_label,
                            required=field_required,
                            help_text=field_help,
                        )
                    elif field_type == 'textarea':
                        self.fields[field_name] = forms.CharField(
                            label=field_label,
                            required=field_required,
                            help_text=field_help,
                            widget=forms.Textarea(attrs={'rows': 3})
                        )
                    elif field_type == 'number':
                        self.fields[field_name] = forms.FloatField(
                            label=field_label,
                            required=field_required,
                            help_text=field_help,
                        )
                    elif field_type == 'date':
                        self.fields[field_name] = forms.DateField(
                            label=field_label,
                            required=field_required,
                            help_text=field_help,
                            widget=forms.DateInput(attrs={'type': 'date'})
                        )
                    elif field_type == 'select' and field_options:
                        choices = [(option, option) for option in field_options]
                        self.fields[field_name] = forms.ChoiceField(
                            label=field_label,
                            required=field_required,
                            help_text=field_help,
                            choices=choices
                        )
                    elif field_type == 'checkbox':
                        self.fields[field_name] = forms.BooleanField(
                            label=field_label,
                            required=False,
                            help_text=field_help,
                        )

