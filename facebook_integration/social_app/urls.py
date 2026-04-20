from django.urls import path
from . import views  # Importar nuestras vistas

# Lista de patrones URL
urlpatterns = [
    # URL 0: Página de inicio (NUEVO)
    # Ruta raíz del sitio
    path('', views.inicio, name='inicio'),
    
    # URL 1: Iniciar login con Facebook
    # Cuando el usuario visita /facebook/login/
    # Django ejecuta views.facebook_login
    path('facebook/login/', views.facebook_login, name='facebook_login'),
    
    # URL 2: Callback de Facebook (donde redirige después de autorizar)
    # Facebook enviará al usuario a /facebook/callback/?code=ABC123
    # Django ejecuta views.facebook_callback
    path('facebook/callback/', views.facebook_callback, name='facebook_callback'),
    
    # URL 3: Dashboard principal del usuario
    # Muestra información del perfil y publicaciones
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # URL 4: Formulario para publicar en Facebook
    # GET: muestra formulario | POST: procesa publicación
    path('facebook/publicar/', views.publicar_facebook, name='publicar_facebook'),
    
    # URL 5: API para actualizar métricas de un post específico
    # <int:post_id> captura el ID del post de la URL (ej: /facebook/post/123/metricas/)
    path('facebook/post/<int:post_id>/metricas/', 
         views.actualizar_metricas_post, 
         name='actualizar_metricas'),

    # URL 6: Cerrar sesión
    path('logout/', views.logout_view, name='logout'),
]

# El parámetro 'name' permite referenciar estas URLs en templates:
# Iniciar sesión