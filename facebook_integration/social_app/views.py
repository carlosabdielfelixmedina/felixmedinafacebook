import requests  # Para hacer peticiones HTTP a Facebook API
import json
from django.shortcuts import render, redirect  # Funciones de Django para renderizar templates y redirigir
from django.contrib.auth.decorators import login_required  # Decorador para proteger vistas que requieren login
from django.conf import settings  # Acceso a configuración de settings.py
from django.http import JsonResponse  # Para respuestas en formato JSON
from django.contrib.auth import logout as auth_logout
from .models import FacebookAccount, FacebookPost  # Nuestros modelos
from django.contrib.auth.models import User

# ============================================
# VISTA: Cerrar Sesión
# ============================================
@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('inicio')

# ============================================
# VISTA 0: Página de Inicio (NUEVO)
# ============================================
def inicio(request):
    """
    Muestra la página principal con el botón de login con Facebook.
    Si el usuario ya está autenticado, lo redirige al dashboard.
    """
    # Verificar si el usuario ya tiene sesión activa
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Mostrar página de login
    return render(request, 'login.html')

# ============================================
# VISTA 1: Iniciar Login con Facebook
# ============================================
def facebook_login(request):
    """
    Redirige al usuario a Facebook para que autorice nuestra aplicación.
    
    Flujo OAuth 2.0 - Paso 1: Authorization Request
    El usuario es enviado a Facebook donde verá qué permisos solicita nuestra app.
    """
    
    # Construir URL de autorización de Facebook
    # Esta es la URL a la que redirigiremos al usuario
    auth_url = "https://www.facebook.com/v18.0/dialog/oauth?"
    
    # Parámetro 1: client_id (nuestro App ID de Facebook)
    auth_url += f"client_id={settings.FACEBOOK_APP_ID}"
    
    # Parámetro 2: redirect_uri (dónde Facebook enviará al usuario después de autorizar)
    # DEBE coincidir EXACTAMENTE con la URL configurada en Facebook Developers
    auth_url += f"&redirect_uri={settings.FACEBOOK_REDIRECT_URI}"
    
    # Parámetro 3: scope (permisos que solicitamos)
    # public_profile: nombre, foto de perfil, etc.
    # pages_show_list: listar páginas administradas
    # pages_read_engagement: leer métricas de páginas
    # pages_manage_posts: PUBLICAR en páginas
    # NOTA: email y pages_manage_posts requieren App Review aprobado.
    #       En modo desarrollo, solo funcionan con usuarios de prueba/admins de la app.
    auth_url += "&scope=public_profile,pages_show_list,pages_read_engagement,pages_manage_posts"
    
    # Parámetro 4: response_type (queremos un 'code' para intercambiar por token)
    auth_url += "&response_type=code"
    
    # Parámetro opcional: state (token CSRF para seguridad - recomendado en producción)
    # auth_url += f"&state={generate_random_state()}"
    
    # Redirigir al usuario a Facebook
    return redirect(auth_url)


# ============================================
# VISTA 2: Callback de Facebook (Procesar Autorización)
# ============================================
def facebook_callback(request):
    """
    Esta función se ejecuta cuando Facebook redirige al usuario de vuelta a nuestra app.
    
    Flujo OAuth 2.0 - Pasos 2 y 3:
    - Paso 2: Recibir código de autorización
    - Paso 3: Intercambiar código por access_token
    """
    
    # PASO 2.1: Obtener el código de autorización de la URL
    # Facebook envía el código como parámetro GET: ?code=ABC123...
    code = request.GET.get('code')
    
    # Si no hay código, significa que el usuario canceló la autorización
    # o hubo un error
    if not code:
        error_description = request.GET.get('error_description', 'Usuario canceló la autorización')
        return render(request, 'error.html', {
            'error': 'No se recibió código de autorización',
            'detalle': error_description
        })
    
    # PASO 2.2: Intercambiar código por access_token
    # Hacer petición POST a Facebook para obtener el token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    
    params = {
        'client_id': settings.FACEBOOK_APP_ID,           # Nuestro App ID
        'client_secret': settings.FACEBOOK_APP_SECRET,   # Nuestro App Secret (¡secreto!)
        'redirect_uri': settings.FACEBOOK_REDIRECT_URI,  # Mismo redirect_uri del paso 1
        'code': code,                                     # Código recibido de Facebook
    }
    
    # Hacer la petición HTTP GET
    response = requests.get(token_url, params=params)
    token_data = response.json()  # Convertir respuesta JSON a diccionario Python
    
    # Verificar si hubo error
    if 'error' in token_data:
        return render(request, 'error.html', {
            'error': 'Error al obtener token de Facebook',
            'detalle': token_data.get('error_description', 'Error desconocido')
        })
    
    # Extraer el access_token de la respuesta
    access_token = token_data.get('access_token')
    
    # PASO 2.3: Obtener información del usuario usando el access_token
    # Consultar el endpoint /me de Graph API
    me_url = "https://graph.facebook.com/v18.0/me"
    
    user_params = {
        # 'fields': especifica qué información queremos obtener
        'fields': 'id,name,email,picture.type(large)',
        'access_token': access_token,  # Autenticación mediante token
    }
    
    user_response = requests.get(me_url, params=user_params)
    user_data = user_response.json()
    
    # Verificar si hubo error
    if 'error' in user_data:
        return render(request, 'error.html', {
            'error': 'Error al obtener datos del usuario',
            'detalle': user_data.get('error', {}).get('message', 'Error desconocido')
        })
    
    # PASO 2.4: Crear o actualizar usuario de Django y cuenta de Facebook
    # Primero, verificar si el usuario ya tiene cuenta en Django
    
    # Buscar si ya existe una cuenta Facebook con este ID
    try:
        facebook_account = FacebookAccount.objects.get(facebook_id=user_data['id'])
        # Si existe, actualizar el token (puede haber expirado el anterior)
        facebook_account.access_token = access_token
        facebook_account.nombre = user_data['name']
        facebook_account.email = user_data.get('email', '')
        facebook_account.foto_perfil = user_data['picture']['data']['url']
        facebook_account.save()
        
    except FacebookAccount.DoesNotExist:
        # Si no existe, crear nuevo usuario Django y cuenta Facebook
        
        # Verificar si el usuario ya está autenticado en Django
        if request.user.is_authenticated:
            django_user = request.user
        else:
            # Crear nuevo usuario Django
            username = f"fb_{user_data['id']}"  # Username único basado en FB ID
            django_user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': user_data.get('email', ''),
                    'first_name': user_data['name'].split()[0] if user_data['name'] else '',
                }
            )
        
        # Crear cuenta Facebook vinculada
        facebook_account = FacebookAccount.objects.create(
            user=django_user,
            facebook_id=user_data['id'],
            access_token=access_token,
            nombre=user_data['name'],
            email=user_data.get('email', ''),
            foto_perfil=user_data['picture']['data']['url'],
        )
    
    # PASO 2.5: Iniciar sesión del usuario en Django
    from django.contrib.auth import login
    login(request, facebook_account.user, backend='django.contrib.auth.backends.ModelBackend')
    
    # Redirigir al dashboard
    return redirect('dashboard')


# ============================================
# VISTA 3: Dashboard de Usuario
# ============================================
@login_required  # Solo usuarios autenticados pueden acceder
def dashboard(request):
    """
    Muestra el panel principal con información del usuario
    y sus publicaciones recientes.
    """
    
    try:
        # Obtener cuenta de Facebook del usuario actual
        facebook_account = FacebookAccount.objects.get(user=request.user)
        
        # Obtener últimas 10 publicaciones
        posts = FacebookPost.objects.filter(account=facebook_account)[:10]
        
        # Calcular estadísticas
        total_posts = FacebookPost.objects.filter(account=facebook_account).count()
        total_likes = sum(post.likes for post in posts)
        total_comentarios = sum(post.comentarios for post in posts)
        
        context = {
            'facebook_account': facebook_account,
            'posts': posts,
            'total_posts': total_posts,
            'total_likes': total_likes,
            'total_comentarios': total_comentarios,
        }
        
        return render(request, 'dashboard.html', context)
        
    except FacebookAccount.DoesNotExist:
        # Si el usuario no tiene cuenta Facebook vinculada, redirigir a login
        return redirect('facebook_login')


# ============================================
# VISTA 4: Publicar en Facebook
# ============================================
@login_required
def publicar_facebook(request):
    """
    Publica en una PÁGINA de Facebook (no en perfil personal).
    Facebook bloqueó publicaciones en perfiles personales desde 2018.
    """
    
    if request.method == 'POST':
        # Obtener mensaje del formulario
        mensaje = request.POST.get('mensaje', '').strip()
        
        # Validar que no esté vacío
        if not mensaje:
            return render(request, 'publicar.html', {
                'error': 'El mensaje no puede estar vacío'
            })
        
        try:
            # Obtener cuenta de Facebook del usuario
            account = FacebookAccount.objects.get(user=request.user)
            
            # PASO 4.1: Obtener lista de PÁGINAS administradas por el usuario
            pages_url = "https://graph.facebook.com/v18.0/me/accounts"
            pages_params = {
                'access_token': account.access_token,
            }
            
            pages_response = requests.get(pages_url, params=pages_params)
            pages_data = pages_response.json()
            
            # Verificar si hay error al obtener páginas
            if 'error' in pages_data:
                return render(request, 'publicar.html', {
                    'error': f"Error de Facebook: {pages_data['error']['message']}",
                    'detalle': 'Necesitas autorizar el permiso "pages_manage_posts"',
                    'solucion': 'Cierra sesión, vuelve a iniciar sesión con Facebook y autoriza todos los permisos.'
                })
            
            # Verificar si el usuario tiene páginas
            if not pages_data.get('data'):
                return render(request, 'publicar.html', {
                    'error': 'No administras ninguna Página de Facebook',
                    'detalle': 'Facebook ya NO permite publicar en perfiles personales.',
                    'solucion': 'Crea una Página de pruebas en: https://facebook.com/pages/create'
                })
            
            # PASO 4.2: Usar la primera página (puedes agregar selector después)
            primera_pagina = pages_data['data'][0]
            page_id = primera_pagina['id']
            page_access_token = primera_pagina['access_token']  # Token ESPECÍFICO de la página
            page_name = primera_pagina['name']
            
            # PASO 4.3: Publicar en la PÁGINA usando su access_token
            post_url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            
            data = {
                'message': mensaje,
                'access_token': page_access_token,  # ¡IMPORTANTE! Usar token de la PÁGINA
            }
            
            # Hacer petición POST a Facebook
            response = requests.post(post_url, data=data)
            post_data = response.json()
            
            # Verificar si hubo error al publicar
            if 'error' in post_data:
                error_message = post_data['error']['message']
                error_code = post_data['error'].get('code', 'N/A')
                error_type = post_data['error'].get('type', 'N/A')
                
                return render(request, 'publicar.html', {
                    'error': f"Error {error_code} ({error_type}): {error_message}",
                    'detalle': 'Revisa los permisos de tu app en Facebook Developers',
                    'json_response': json.dumps(post_data, indent=2)
                })
            
            # PASO 4.4: Guardar publicación en base de datos
            FacebookPost.objects.create(
                account=account,
                mensaje=mensaje,
                post_id=post_data.get('id', ''),
                page_access_token=page_access_token,
                estado='publicado',
            )
            
            # Construir URL del post para abrirlo
            post_facebook_url = f"https://www.facebook.com/{post_data.get('id', '').replace('_', '/posts/')}"
            
            # PASO 4.5: Mensaje de éxito
            return render(request, 'publicar.html', {
                'success': f'✅ ¡Publicación exitosa en la página "{page_name}"!',
                'post_id': post_data.get('id', ''),
                'page_name': page_name,
                'post_url': post_facebook_url,
                'nota': f'Se publicó en tu PÁGINA "{page_name}", no en tu perfil personal (Facebook lo bloqueó).'
            })
        
        except FacebookAccount.DoesNotExist:
            return redirect('facebook_login')
        
        except requests.exceptions.RequestException as e:
            return render(request, 'publicar.html', {
                'error': 'Error de conexión con Facebook',
                'detalle': str(e),
                'solucion': 'Verifica tu conexión a Internet y que Facebook esté disponible.'
            })
        
        except Exception as e:
            return render(request, 'publicar.html', {
                'error': f'Error inesperado: {type(e).__name__}',
                'detalle': str(e),
                'traza': 'Revisa los logs del servidor para más información.'
            })
    
    # Si es GET, mostrar formulario
    return render(request, 'publicar.html')


# ============================================
# VISTA 5: Obtener Métricas de un Post (API)
# ============================================
@login_required
def actualizar_metricas_post(request, post_id):
    """
    Actualiza las métricas (likes, comentarios, shares) de una publicación
    consultando la Graph API de Facebook.
    """

    try:
        post = FacebookPost.objects.get(id=post_id, account__user=request.user)

        # Usar el token de página guardado al publicar (el más confiable).
        # Si no hay uno guardado, intentar obtenerlo de /me/accounts como fallback.
        page_token = post.page_access_token
        if not page_token:
            if '_' in post.post_id:
                page_id = post.post_id.split('_')[0]
                pages_response = requests.get(
                    "https://graph.facebook.com/v18.0/me/accounts",
                    params={'access_token': post.account.access_token}
                )
                for page in pages_response.json().get('data', []):
                    if page['id'] == page_id:
                        page_token = page['access_token']
                        post.page_access_token = page_token
                        post.save(update_fields=['page_access_token'])
                        break
            if not page_token:
                page_token = post.account.access_token

        insights_url = f"https://graph.facebook.com/v18.0/{post.post_id}"
        params = {
            'fields': 'reactions.summary(true),comments.summary(true),shares',
            'access_token': page_token,
        }

        response = requests.get(insights_url, params=params)
        metrics_data = response.json()

        if 'error' in metrics_data:
            return JsonResponse({'error': metrics_data['error']['message']}, status=400)

        post.likes = metrics_data.get('reactions', {}).get('summary', {}).get('total_count', 0)
        post.comentarios = metrics_data.get('comments', {}).get('summary', {}).get('total_count', 0)
        post.compartidos = metrics_data.get('shares', {}).get('count', 0)
        post.save()

        return JsonResponse({
            'success': True,
            'likes': post.likes,
            'comentarios': post.comentarios,
            'compartidos': post.compartidos,
        })

    except FacebookPost.DoesNotExist:
        return JsonResponse({'error': 'Post no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)