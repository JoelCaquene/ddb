"""
Django settings for ddb project.
Configuração otimizada para Produção no Render.
"""

from pathlib import Path
import os
import dj_database_url
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configurações Essenciais ---

# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts Permitidos
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
if not DEBUG:
    # Adiciona o hostname do Render dinamicamente
    RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_EXTERNAL_HOSTNAME:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition
INSTALLED_APPS = [
    # Built-in Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    
    # Static Files e Armazenamento (Whitenoise deve vir antes de staticfiles)
    'whitenoise.runserver_nostatic', # Para desenvolvimento local com whitenoise
    'django.contrib.staticfiles',
    
    # 3rd Party Apps para Produção
    'cloudinary',
    'cloudinary_storage',
    
    # Suas Aplicações
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise deve vir logo abaixo do SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ddb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ddb.wsgi.application'

# --- Database ---
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
    )
}

# --- Password validation ---
# (Manter o padrão para brevidade)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# --- Internationalization ---
LANGUAGE_CODE = 'pt-br'

# ➡️ FUSO HORÁRIO DE LUANDA (África Ocidental - WAT)
TIME_ZONE = 'Africa/Luanda' 

USE_I18N = True
USE_TZ = True

# --- Static files (CSS, JavaScript) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Use WhiteNoise para servir arquivos estáticos de forma comprimida e manifestada em Produção
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --- Media files (Arquivos do Usuário - Imagens, Documentos) ---
if not DEBUG:
    # ----------------------------------------------------------------------
    # 1. Configuração do Cloudinary (para Produção)
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': config('CLOUDINARY_API_KEY'),
        'API_SECRET': config('CLOUDINARY_API_SECRET'),
        # Opcional: Define um prefixo/pasta para os arquivos no Cloudinary
        'MEDIA_FOLDER': 'ddb_media_files', 
    }
    
    # 2. Em Produção, use o Cloudinary como o método padrão para salvar arquivos
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = '/media/'
    
else:
    # 3. Em Desenvolvimento (DEBUG=True), use o armazenamento local
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'


# --- Modelos e Redirecionamentos ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.CustomUser'
LOGIN_URL = 'login'

# --- Configuração de Segurança Adicional (Apenas para Produção) ---
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000 # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    