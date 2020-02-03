# extra configuraion for my project
ALLOWED_HOSTS = ['*']

import os
import pymysql
import subprocess

pymysql.install_as_MySQLdb()
DATABASES = {
   'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER_NAME', 'apiadmin'),
        'PASSWORD': os.environ.get('DB_USER_PASS', 'apiadmin_pwd'),
        'HOST': os.environ.get('DB_HOST', os.uname()[1]),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'sql_mode': 'traditional',
        },
        'TEST_NAME': 'auto_tests',
   }
}

INSTALLED_APPS += ['django_extensions']

NOTEBOOK_ARGUMENTS = [
    # exposes IP and port
    '--ip=0.0.0.0',
    '--port=8888',
    # disables the browser
    '--no-browser',
]
