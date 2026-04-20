from django.db import models
from django.contrib.auth.models import User  # Modelo de usuario integrado de Django

# ============================================
# MODELO 1: FacebookAccount (Cuentas de Facebook)
# ============================================
# Esta tabla almacenará la información de las cuentas Facebook vinculadas

class FacebookAccount(models.Model):
    """
    Representa una cuenta de Facebook conectada a un usuario de Django.
    Almacena el token de acceso y datos básicos del perfil.
    """
    
    # Relación uno-a-uno con el usuario de Django
    # Si se elimina el usuario, se elimina también su cuenta Facebook (CASCADE)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        help_text="Usuario Django vinculado a esta cuenta Facebook"
    )
    
    # ID único de Facebook (ej: "1234567890123456")
    # unique=True asegura que no se dupliquen IDs
    facebook_id = models.CharField(
        max_length=100, 
        unique=True,
        help_text="ID numérico único asignado por Facebook"
    )
    
    # Token de acceso OAuth (permite hacer peticiones a Facebook API)
    # TextField porque puede ser muy largo (500+ caracteres)
    # ⚠️ En producción, este campo debería estar CIFRADO
    access_token = models.TextField(
        help_text="Token OAuth para autenticar peticiones a Facebook API"
    )
    
    # Información del perfil de Facebook
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre completo del usuario en Facebook"
    )
    
    email = models.EmailField(
        blank=True,  # Puede estar vacío si Facebook no proporciona email
        help_text="Correo electrónico del usuario (si autorizó compartirlo)"
    )
    
    foto_perfil = models.URLField(
        blank=True,  # Puede estar vacío
        help_text="URL de la foto de perfil de Facebook"
    )
    
    # Metadatos
    fecha_vinculacion = models.DateTimeField(
        auto_now_add=True,  # Se establece automáticamente al crear el registro
        help_text="Fecha y hora en que se vinculó la cuenta"
    )
    
    # Configuración de metadatos del modelo
    class Meta:
        verbose_name = 'Cuenta de Facebook'
        verbose_name_plural = 'Cuentas de Facebook'
        ordering = ['-fecha_vinculacion']  # Ordenar por más recientes primero
    
    # Representación legible del objeto (se muestra en el admin de Django)
    def __str__(self):
        return f"{self.nombre} ({self.facebook_id})"
    
    # Método personalizado para verificar si el token ha expirado
    def token_valido(self):
        """Verifica si el access_token sigue siendo válido"""
        # En implementación real, aquí harías una petición a Facebook API
        # para verificar el token con /debug_token
        pass


# ============================================
# MODELO 2: FacebookPost (Publicaciones)
# ============================================
# Esta tabla almacenará las publicaciones realizadas desde nuestra app

class FacebookPost(models.Model):
    """
    Representa una publicación hecha en Facebook desde nuestra aplicación.
    Almacena contenido, métricas de interacción y metadatos.
    """
    
    # Relación muchos-a-uno: una cuenta puede tener múltiples posts
    # Si se elimina la cuenta, se eliminan también todos sus posts (CASCADE)
    account = models.ForeignKey(
        FacebookAccount, 
        on_delete=models.CASCADE,
        related_name='publicaciones',  # Permite acceder a posts desde account: account.publicaciones.all()
        help_text="Cuenta de Facebook que realizó la publicación"
    )
    
    # Contenido de la publicación
    mensaje = models.TextField(
        help_text="Texto del post publicado en Facebook"
    )
    
    # ID del post en Facebook (ej: "123456_789012")
    # Lo proporciona Facebook después de publicar exitosamente
    post_id = models.CharField(
        max_length=200, 
        blank=True,
        help_text="ID único del post asignado por Facebook (formato: user_id_post_id)"
    )

    # Token de la página con el que se publicó (necesario para consultar métricas)
    page_access_token = models.TextField(
        blank=True,
        help_text="Token de acceso de la página usado al publicar"
    )
    
    # Metadatos temporales
    fecha_publicacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora en que se publicó el post"
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,  # Se actualiza automáticamente cada vez que se guarda
        help_text="Última vez que se actualizaron las métricas"
    )
    
    # Métricas de interacción (se actualizan periódicamente)
    likes = models.IntegerField(
        default=0,
        help_text="Cantidad de 'Me gusta' del post"
    )
    
    comentarios = models.IntegerField(
        default=0,
        help_text="Cantidad de comentarios del post"
    )
    
    compartidos = models.IntegerField(
        default=0,
        help_text="Cantidad de veces que se compartió el post"
    )
    
    alcance = models.IntegerField(
        default=0,
        help_text="Número de personas únicas que vieron el post"
    )
    
    # Estado de la publicación
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('eliminado', 'Eliminado'),
        ('error', 'Error al publicar'),
    ]
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='publicado',
        help_text="Estado actual de la publicación"
    )
    
    # Configuración de metadatos del modelo
    class Meta:
        verbose_name = 'Publicación de Facebook'
        verbose_name_plural = 'Publicaciones de Facebook'
        ordering = ['-fecha_publicacion']  # Más recientes primero
        indexes = [
            models.Index(fields=['-fecha_publicacion']),  # Índice para búsquedas rápidas
            models.Index(fields=['post_id']),
        ]
    
    def __str__(self):
        return f"Post: {self.mensaje[:50]}..." if len(self.mensaje) > 50 else f"Post: {self.mensaje}"
    
    # Método para calcular engagement (interacción total)
    @property
    def engagement_total(self):
        """Calcula la suma de todas las interacciones"""
        return self.likes + self.comentarios + self.compartidos
    
    # Método para calcular tasa de engagement
    @property
    def tasa_engagement(self):
        """Calcula el porcentaje de engagement respecto al alcance"""
        if self.alcance > 0:
            return round((self.engagement_total / self.alcance) * 100, 2)
        return 0.0