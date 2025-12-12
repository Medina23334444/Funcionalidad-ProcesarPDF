from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ProcesarPDFForm
from .models import DocumentoPDF


def procesar_pdf_view(request):
    if request.method == 'POST':
        form = ProcesarPDFForm(request.POST, request.FILES)

        if form.is_valid():
            doc_pdf = form.save(commit=False)

            doc_pdf.nombre_archivo = doc_pdf.ruta_archivo.name

            doc_pdf.tamanio = 0.0

            try:
                es_valido, mensaje_error = doc_pdf.validarFormato()
            except TypeError:
                es_valido = True
                mensaje_error = ""

            if not es_valido:
                messages.error(request, f"Error: {mensaje_error}")
                return render(request, 'procesar_pdf.html', {'form': form})

            doc_pdf.save()

            doc_pdf.obtenerContenido()

            messages.success(request, f"Procesamiento exitoso: {doc_pdf.nombre_archivo}")
            return redirect('procesar_pdf')

        else:
            messages.error(request, "El formulario no es válido.")

    else:
        form = ProcesarPDFForm()
    return render(request, 'procesar_pdf.html', {'form': form})
