from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY='devkey'
DEBUG=True
ALLOWED_HOSTS=[]
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'app',    # <-- ADD THIS LINE
]

MIDDLEWARE=[
 'django.middleware.security.SecurityMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware',
 'django.middleware.common.CommonMiddleware',
 'django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware',
 'django.contrib.messages.middleware.MessageMiddleware',
]
ROOT_URLCONF='core.urls'
TEMPLATES=[{
 'BACKEND':'django.template.backends.django.DjangoTemplates',
 'DIRS':[BASE_DIR/'templates'],  # Make sure this line exists
 'APP_DIRS':True,
 'OPTIONS':{'context_processors':[
  'django.template.context_processors.debug',
  'django.template.context_processors.request',
  'django.contrib.auth.context_processors.auth',
  'django.contrib.messages.context_processors.messages',
 ]},
}]
WSGI_APPLICATION='core.wsgi.application'
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS=[]
LANGUAGE_CODE='en-us'
TIME_ZONE='Asia/Kolkata'
USE_I18N=True
USE_TZ=True
STATIC_URL='static/'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'YOUR_GMAIL_ADDRESS@gmail.com'
EMAIL_HOST_PASSWORD = 'YOUR_16_CHAR_APP_PASSWORD'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
LOGIN_REDIRECT_URL = '/login-redirect/'
AUTHENTICATION_BACKENDS = [
    'app.backends.EmailOrUsernameBackend',      # custom backend
    'django.contrib.auth.backends.ModelBackend' # default backend
]
