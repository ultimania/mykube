FROM centos
LABEL maintainer="Ultimania <yng.ultimania.gmail.com>"
WORKDIR /root

# OS Packagesインストール
COPY ./centos7.repo /etc/yum.repos.d/
ENV PATH="$PATH:/usr/local/python/bin"
ENV PYTHON_VERSION="3.6.0"
ENV DJANGO_VERSION="2.1.2"
ENV PROJECT_NAME="myproject"
ENV DB_NAME="django"
RUN set -x && \
    echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
    yum -y install git zlib-devel bzip2 bzip2-devel readline-devel openssl-devel sqlite3 sqlite-devel gcc make && \
    cd /usr/local/src && \
    curl -O https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar xvzf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --prefix=/usr/local/python && \
    make && \
    make install && \
    cd ~ && \
    ln -s /usr/local/python/bin/python3 /usr/local/bin/python && \
    ln -s /usr/local/python/bin/pip3 /usr/local/bin/pip

# pip Packagesインストール
RUN set -x && \
    pip install --upgrade pip && \
    pip install django==${DJANGO_VERSION} && \
    pip install djangorestframework && \
    pip install django-filter && \
    pip install djangorestframework-jwt && \
    pip install PyMySQL && \
    pip install uwsgi && \
    pip install django-hamlpy && \
    pip install BeautifulSoup4 && \
    pip install mpl_finance && \
    pip install pandas && \
    pip install scikit-learn && \
    pip install django-widget-tweaks && \
    pip install pycrypto && \
    pip install tweepy && \
    pip install nose && \
    django-admin startproject ${PROJECT_NAME}

# Djangoプロジェクトの作成
COPY ./my_setting.py /root/${PROJECT_NAME}/${PROJECT_NAME}/
COPY ./startup.sh /root/
ENV DB_HOST="172.17.0.2"
RUN set -x && \
    cat ~/${PROJECT_NAME}/${PROJECT_NAME}/my_setting.py >> ~/${PROJECT_NAME}/${PROJECT_NAME}/settings.py && \
    python ~/${PROJECT_NAME}/manage.py makemigrations && \
    python ~/${PROJECT_NAME}/manage.py migrate && \
    chmod 777 /root/startup.sh
ENV DB_HOST="api-server"

# DBの同期, API Server起動
CMD [ "/bin/sh" , "/root/startup.sh"]
