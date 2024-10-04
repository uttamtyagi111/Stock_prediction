from datetime import timedelta
from pathlib import Path
import os
from dotenv import load_dotenv
import ssl
from django.core.mail import  EmailMessage
import boto3 

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

# Directory settings for email templates
ORIGINAL_TEMPLATES_DIR = BASE_DIR / 'original_email_templates'
EDITED_TEMPLATES_DIR = BASE_DIR / 'edited_email_templates'

EMAIL_TEMPLATES_DIR = BASE_DIR / 'templates'

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'fallback-secret-key')

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    'https://django-api-aqlo.onrender.com',
]
import os

# settings.py
PORT = os.environ.get('PORT', '8000')

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'authentication',
    'email_sender',
    'storages', 
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=2),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': 'your-secret-key',  # Change this to a secure key
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'email_automation.middleware.DisableCsrfMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# import os
# from celery.schedules import crontab 


# # Optionally, you can set the result backend if you need to store results
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# # Optional: Set timezone and enable UTC
# CELERY_TIMEZONE = 'UTC'  # Change to your preferred timezone
# CELERY_ENABLE_UTC = True

# # Set the task track settings
# CELERY_TASK_TRACK_STARTED = True  # Track when tasks are started
# CELERY_TASK_TIME_LIMIT = 300  # Set a time limit for tasks in seconds


# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_BEAT_SCHEDULE = {
#     'delete-expired-blacklisted-tokens-every-day': {
#         'task': 'email_automation.authentication.tasks.delete_expired_blacklisted_tokens_task',
#         'schedule': crontab(hour=0, minute=0),  # Runs daily at midnight
#     },
# }


SESSION_COOKIE_AGE = 1209600  # Two weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


ROOT_URLCONF = 'email_automation.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'email_automation.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
}

DATABASE_ROUTERS = ['authentication.database_router.DatabaseRouter']


AUTHENTICATION_BACKENDS = ['authentication.backends.EmailBackend','django.contrib.auth.backends.ModelBackend' ]


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Added S3 configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')  


DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_DEFAULT_ACL = None

AWS_QUERYSTRING_AUTH = False 


AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_FILE_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/'


MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 

# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.wishgeeks.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False  # Commented out as not used
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

class SSLDisableContext:
    def __enter__(self):
        self.ssl_context = ssl._create_unverified_context()
        self.original_get_connection = get_connection

        def get_connection(backend=None, fail_silently=False, **kwargs):
            return self.original_get_connection(backend, fail_silently, ssl_context=self.ssl_context, **kwargs)

        EmailMessage.get_connection = staticmethod(get_connection)

    def __exit__(self, exc_type, exc_value, traceback):
        EmailMessage.get_connection = staticmethod(self.original_get_connection)

SSLDisableContext()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
