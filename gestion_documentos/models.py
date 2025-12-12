import os

from django.db import models
from pypdf import PdfReader


class EstadoDocumento(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    VALIDADO = 'VALIDADO', 'Validado'


class Documento(models.Model):
    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.FileField(upload_to='docs/')
    tamanio = models.FloatField()

    class Meta:
        abstract = False


class DocumentoPDF(Documento):
    tiene_etiquetas = models.BooleanField(default=False)

    def validarFormato(self):
        print("Validando formato PDF...")
        return True

    def obtenerContenido(self):

        try:
            ruta_completa = self.ruta_archivo.path

            reader = PdfReader(ruta_completa)

            self.numero_paginas = len(reader.pages)

            self.tamanio = os.path.getsize(ruta_completa) / (1024 * 1024)

            self.save()
        except Exception as e:
            print(f"Error analizando contenido: {e}")


class ConversorFormato(models.Model):
    documento_origen = models.ForeignKey(DocumentoPDF, on_delete=models.CASCADE)
    fecha_conversion = models.DateField(auto_now_add=True)

    def convertirPDFaHTML(self):
        pass
