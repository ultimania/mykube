#/bin/sh
# git clone -b twitter_api https://github.com/ultimania/investmentTools.git
# python /opt/${PROJECT_NAME}/manage.py shell_plus --notebook
cp -rp ~/${PROJECT_NAME} /opt
python /opt/${PROJECT_NAME}/manage.py makemigrations
python /opt/${PROJECT_NAME}/manage.py migrate
python /opt/${PROJECT_NAME}/manage.py runserver 0.0.0.0:8000