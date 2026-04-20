# ========================================
# PARTE 6.2: Modificar facebook_integration/urls.py
# ========================================
# Este es el archivo de URLs principal del proyecto
# Incluye las URLs de todas las apps

from django.contrib import admin
from django.urls import path, include  # Agregar 'include'

urlpatterns = [
    # Panel de administración de Django
    # Accesible en: http://localhost:8000/admin/
    path('admin/', admin.site.urls),
    
    # Incluir todas las URLs de social_app
    # El segundo argumento '' significa que no hay prefijo adicional
    # Por eso facebook/login/ queda como http://localhost:8000/facebook/login/
    path('', include('social_app.urls')),
    
    # Si quisieras un prefijo, podrías hacer:
    # path('api/', include('social_app.urls'))
    # Entonces quedaría: http://localhost:8000/api/facebook/login/
]

# Estructura de URLs final:
# /admin/                          → Panel administración Django
# /facebook/login/                 → Iniciar login Facebook
# /facebook/callback/              → Callback OAuth Facebook
# /dashboard/                      → Dashboard del usuario
# /facebook/publicar/              → Publicar en Facebook
# /facebook/post//metricas/    → Actualizar métricas