from django import forms
from .models import DocumentoPDF


class ProcesarPDFForm(forms.ModelForm):
    class Meta:
        model = DocumentoPDF
        fields = ['ruta_archivo']
        widgets = {
            # El atributo accept ayuda en el frontend, pero la validación real va en el modelo/form
            'ruta_archivo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }

    def clean_ruta_archivo(self):
        archivo = self.cleaned_data.get('ruta_archivo')
        if archivo:
            if not archivo.name.endswith('.pdf'):
                raise forms.ValidationError("Solo se permiten archivos PDF.")
        return archivo
