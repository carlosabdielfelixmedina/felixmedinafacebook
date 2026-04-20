from django.contrib import admin
from .models import FacebookAccount, FacebookPost

# Configuración personalizada para FacebookAccount en el admin
@admin.register(FacebookAccount)
class FacebookAccountAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para cuentas Facebook"""
    
    # Columnas que se muestran en la lista
    list_display = ('nombre', 'facebook_id', 'email', 'fecha_vinculacion')
    
    # Campos por los que se puede buscar
    search_fields = ('nombre', 'email', 'facebook_id')
    
    # Filtros laterales
    list_filter = ('fecha_vinculacion',)
    
    # Campos de solo lectura (no editables)
    readonly_fields = ('facebook_id', 'fecha_vinculacion', 'foto_perfil')
    
    # Orden por defecto
    ordering = ('-fecha_vinculacion',)

# Configuración personalizada para FacebookPost en el admin
@admin.register(FacebookPost)
class FacebookPostAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para publicaciones"""
    
    list_display = ('mensaje_corto', 'account', 'likes', 'comentarios', 
                    'compartidos', 'estado', 'fecha_publicacion')
    
    search_fields = ('mensaje', 'post_id')
    
    list_filter = ('estado', 'fecha_publicacion', 'account')
    
    readonly_fields = ('post_id', 'fecha_publicacion', 'fecha_actualizacion', 
                       'engagement_total', 'tasa_engagement')
    
    ordering = ('-fecha_publicacion',)
    
    # Mostrar engagement total como campo calculado
    def mensaje_corto(self, obj):
        return obj.mensaje[:50] + '...' if len(obj.mensaje) > 50 else obj.mensaje
    mensaje_corto.short_description = 'Mensaje'