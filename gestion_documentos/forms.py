from django import forms
from .models import DocumentoPDF

class ProcesarPDFForm(forms.ModelForm):
    class Meta:
        model = DocumentoPDF
        fields = ['ruta_archivo']
        widgets = {
            'ruta_archivo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }