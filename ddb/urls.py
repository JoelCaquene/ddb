from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Importar settings
from django.conf.urls.static import static # Importar static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# 💡 CORREÇÃO: As rotas estáticas e de mídia devem ser adicionadas 
# APENAS se estiver em modo de desenvolvimento (DEBUG=True).
if settings.DEBUG:
    # 1. Rotas Estáticas (para imagens do carrossel, etc.)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # 2. Rotas de Mídia (para comprovativos, etc., localmente)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    