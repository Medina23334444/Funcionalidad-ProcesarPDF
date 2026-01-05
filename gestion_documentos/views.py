import os

from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ProcesarPDFForm
from .models import DocumentoPDF, ConversorFormato


def procesar_pdf_view(request):
    # --- CORRECCIÓN 1: Obtener la lista de documentos al principio ---
    # Esto asegura que la variable 'documentos' siempre exista para la tabla
    documentos = DocumentoPDF.objects.all().order_by('-id')

    if request.method == 'POST':
        form = ProcesarPDFForm(request.POST, request.FILES)

        if form.is_valid():
            doc_pdf = form.save(commit=False)
            doc_pdf.nombre_archivo = doc_pdf.ruta_archivo.name
            doc_pdf.save()

            es_valido, mensaje_error = doc_pdf.validarFormato()

            if not es_valido:
                doc_pdf.delete()
                messages.error(request, f"Error: {mensaje_error}")
                # --- CORRECCIÓN 2: Pasar 'documentos' también si hay error ---
                return render(request, 'procesar_pdf.html', {'form': form, 'documentos': documentos})

            doc_pdf.obtenerContenido()

            messages.success(request,
                             f"Procesamiento exitoso: {doc_pdf.nombre_archivo}. Páginas: {doc_pdf.numero_paginas}. Etiquetas detectadas: {'Sí' if doc_pdf.tiene_etiquetas else 'No'}")

            # Al hacer redirect, se vuelve a ejecutar esta vista como GET (parte de abajo)
            return redirect('procesar_pdf')

        else:
            messages.error(request, "Error: Debe seleccionar un archivo válido.")

    else:
        form = ProcesarPDFForm()

    # --- CORRECCIÓN 3: Pasar 'documentos' al template ---
    # Antes solo pasabas {'form': form}, por eso la tabla salía vacía.
    return render(request, 'procesar_pdf.html', {'form': form, 'documentos': documentos})


def convertir_pdf_html_view(request, doc_id):
    # ... (El resto de tu código para RF02 está correcto y funcionará una vez veas el botón) ...
    doc_pdf = get_object_or_404(DocumentoPDF, id=doc_id)

    if doc_pdf.estado == 'PENDIENTE' and not doc_pdf.tamanio > 0:
        messages.warning(request, "El documento debe ser procesado (RF01) antes de convertir.")
        return redirect('procesar_pdf')

    conversor = ConversorFormato(documento_origen=doc_pdf)
    exito, mensaje = conversor.convertirPDFaHTML()

    if exito:
        messages.success(request, f"RF02 Exitoso: {mensaje}. El archivo HTML ha sido generado.")
    else:
        messages.error(request, f"Error en RF02: {mensaje}")

    return redirect('procesar_pdf')


def descargar_html_view(request, doc_id):
    """
    Implementación del RF05: Descargar archivos generados.
    """
    # 1. Buscamos el documento original
    doc_pdf = get_object_or_404(DocumentoPDF, id=doc_id)

    # 2. Verificamos que tenga un HTML generado asociado
    if not hasattr(doc_pdf, 'html_generado'):
        raise Http404("El archivo HTML no ha sido generado aún.")

    archivo_html_obj = doc_pdf.html_generado

    # 3. Abrimos el archivo y lo enviamos como descarga
    try:
        # Abrimos el archivo físico
        archivo_fisico = archivo_html_obj.archivo.open('rb')
        response = FileResponse(archivo_fisico, as_attachment=True)

        # --- CORRECCIÓN DEL ERROR ---
        # Usamos el nombre del PDF original y cambiamos la extensión a .html
        nombre_base = os.path.splitext(doc_pdf.nombre_archivo)[0]
        nombre_descarga = f"{nombre_base}.html"

        response['Content-Disposition'] = f'attachment; filename="{nombre_descarga}"'
        return response

    except FileNotFoundError:
        # Esto maneja el error 404 si el archivo se borró del disco
        raise Http404(
            "El archivo físico no se encuentra en el servidor. Por favor, elimine el registro y vuelva a convertir.")
    except Exception as e:
        # Captura cualquier otro error imprevisto
        raise Http404(f"Error al descargar: {str(e)}")
