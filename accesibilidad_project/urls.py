"""
URL configuration for accesibilidad_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from xml.etree.ElementInclude import include

from django.contrib import admin

from django.urls import path

from gestion_documentos import views
from gestion_documentos.views import procesar_pdf_view

from django.contrib import admin
from django.urls import path
from gestion_documentos import views

from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),

    # Ruta raíz (opcional, redirige o muestra la misma vista)
    path('', views.procesar_pdf_view, name='home'),

    # Ruta principal del proceso (RF01)
    path('procesar/', views.procesar_pdf_view, name='procesar_pdf'),

    # Ruta para la conversión (RF02)
    path('convertir/<int:doc_id>/', views.convertir_pdf_html_view, name='convertir_html'),
    path('descargar/<int:doc_id>/', views.descargar_html_view, name='descargar_html'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)