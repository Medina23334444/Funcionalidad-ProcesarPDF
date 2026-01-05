import os
import html
from django.db import models
from django.core.files.base import ContentFile
from django.utils.timezone import now
from pypdf import PdfReader


class EstadoDocumento(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    VALIDADO = 'VALIDADO', 'Validado'
    ERROR = 'ERROR', 'Error'


class Documento(models.Model):
    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.FileField(upload_to='docs/')
    tamanio = models.FloatField(default=0.0)
    # Agregamos estado para controlar el flujo
    estado = models.CharField(
        max_length=20,
        choices=EstadoDocumento.choices,
        default=EstadoDocumento.PENDIENTE
    )

    class Meta:
        abstract = False


class DocumentoPDF(Documento):
    tiene_etiquetas = models.BooleanField(default=False)
    numero_paginas = models.IntegerField(default=0)
    metadatos = models.TextField(blank=True, null=True)  # Para almacenar titulo/autor extraído

    def validarFormato(self):
        """
        Maneja el Flujo Alternativo 5': El archivo PDF está dañado o no cumple formato.
        """
        print(f"Validando: {self.ruta_archivo.path}")
        try:
            # 1. Validar extensión
            if not self.ruta_archivo.name.lower().endswith('.pdf'):
                return False, "El archivo debe tener extensión .pdf"

            # 2. Validar integridad intentando abrirlo con pypdf
            reader = PdfReader(self.ruta_archivo.path)
            if len(reader.pages) == 0:
                return False, "El archivo PDF está vacío."

            return True, "Formato válido"
        except Exception as e:
            return False, f"Archivo dañado o ilegible: {str(e)}"

    def obtenerContenido(self):
        """
        Maneja el Flujo Básico 4: El prototipo analiza el documento y extrae
        contenido (texto, etiquetas, metadatos).
        """
        try:
            ruta_completa = self.ruta_archivo.path
            reader = PdfReader(ruta_completa)

            # Extraer metadatos básicos
            self.numero_paginas = len(reader.pages)
            self.tamanio = os.path.getsize(ruta_completa) / (1024 * 1024)

            # Intentar extraer metadatos del PDF (Autor, Título)
            info = reader.metadata
            if info:
                titulo = info.title if info.title else "Sin título"
                autor = info.author if info.author else "Desconocido"
                self.metadatos = f"Título: {titulo} | Autor: {autor}"

            # Verificar si tiene etiquetas (StructTreeRoot) - Crucial para accesibilidad
            # Si '/MarkInfo' existe y '/Marked' es True, suele indicar PDF etiquetado.
            try:
                root = reader.trailer['/Root']
                if '/MarkInfo' in root and root['/MarkInfo'].get('/Marked', False):
                    self.tiene_etiquetas = True
                else:
                    self.tiene_etiquetas = False
            except:
                self.tiene_etiquetas = False

            self.estado = EstadoDocumento.VALIDADO
            self.save()

        except Exception as e:
            print(f"Error analizando contenido: {e}")
            self.estado = EstadoDocumento.ERROR
            self.save()


class ArchivoHTML(models.Model):
    """
    Representa el resultado del RF02 según el Diagrama de Clases.
    """
    documento_fuente = models.OneToOneField('DocumentoPDF', on_delete=models.CASCADE, related_name='html_generado')
    archivo = models.FileField(upload_to='html_generados/')
    etiquetas_semanticas = models.TextField(blank=True, help_text="Lista de etiquetas usadas (ej: main, nav, p)")
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    # Atributos del diagrama de clases
    nivel_accesibilidad = models.CharField(max_length=50, default="A (Básico)")
    cantidad_etiquetas = models.IntegerField(default=0)
    lenguaje_html = models.CharField(max_length=5, default="es")

    def __str__(self):
        return f"HTML de {self.documento_fuente.nombre_archivo}"


class ConversorFormato(models.Model):
    """
    Clase controladora del proceso de conversión (Controlador en el diagrama de clases).
    """
    documento_origen = models.ForeignKey('DocumentoPDF', on_delete=models.CASCADE)
    fecha_conversion = models.DateTimeField(auto_now_add=True)
    tiempo_ejecucion = models.FloatField(null=True, blank=True)

    def convertirPDFaHTML(self):
        """
        Implementación del RF02: Convertir PDF a versión HTML accesible.
        Aplica etiquetas semánticas y estructura WCAG básica.
        """
        import time
        inicio = time.time()

        try:
            # 1. Preparar lectura
            ruta_pdf = self.documento_origen.ruta_archivo.path
            reader = PdfReader(ruta_pdf)
            meta = reader.metadata
            titulo = meta.title if meta and meta.title else "Documento Accesible"

            # 2. Iniciar estructura HTML5 semántica (Requisito RF02)
            html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(titulo)}</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        main {{ background: #fff; padding: 20px; }}
        article {{ margin-bottom: 2rem; border-bottom: 1px solid #eee; }}
    </style>
</head>
<body>
    <header>
        <h1 id="doc-title">{html.escape(titulo)}</h1>
        <div role="doc-subtitle">Convertido automáticamente por Sistema de Accesibilidad</div>
    </header>

    <nav aria-label="Navegación de páginas">
        <ul>
            <li><a href="#main-content">Saltar al contenido principal</a></li>
        </ul>
    </nav>

    <main id="main-content" role="main">
"""
            conteo_etiquetas = 4  # html, head, body, main ya contados

            # 3. Iterar páginas y estructurar contenido
            for i, page in enumerate(reader.pages):
                texto = page.extract_text()
                if texto:
                    texto_saneado = html.escape(texto)
                    # Heurística simple: Convertir saltos de línea en párrafos
                    parrafos = texto_saneado.split('\n')

                    html_content += f"""
        <article aria-labelledby="page-{i + 1}-heading">
            <h2 id="page-{i + 1}-heading" class="visually-hidden">Página {i + 1}</h2>
            <div class="page-content">
"""
                    conteo_etiquetas += 2  # article, h2

                    for p in parrafos:
                        if len(p.strip()) > 0:
                            # Detectar posibles encabezados (muy básico)
                            if len(p) < 100 and p.isupper():
                                html_content += f"                <h3>{p}</h3>\n"
                            else:
                                html_content += f"                <p>{p}</p>\n"
                            conteo_etiquetas += 1

                    html_content += """            </div>
        </article>
"""

            # 4. Cerrar estructura
            html_content += """    </main>
    <footer>
        <p>Fin del documento.</p>
    </footer>
</body>
</html>"""

            # 5. Crear el objeto ArchivoHTML
            archivo_html = ArchivoHTML(documento_fuente=self.documento_origen)

            # Guardar el archivo físico
            nombre_archivo = f"{os.path.splitext(self.documento_origen.nombre_archivo)[0]}.html"
            archivo_html.archivo.save(nombre_archivo, ContentFile(html_content.encode('utf-8')))

            # Llenar metadatos del diagrama
            archivo_html.cantidad_etiquetas = conteo_etiquetas
            archivo_html.etiquetas_semanticas = "html, body, main, article, h1, h2, h3, p, nav"
            archivo_html.save()

            # 6. Actualizar estado y métricas
            self.tiempo_ejecucion = time.time() - inicio
            self.save()

            self.documento_origen.estado = 'CONVERTIDO'
            self.documento_origen.save()

            return True, "Conversión a HTML exitosa"

        except Exception as e:
            return False, f"Error en conversión: {str(e)}"
