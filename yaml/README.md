# Kubernetes 操作リファレンス
### 前提条件
* Kubernetesが構築済みであること

## 手順概要
|No|作業内容|
|:-----------|:-----------|
|1|事前確認|
|2|Dockerレジストリ構築|
|3|イメージ作成|
|4|永続ボリューム作成|
|5|secretの作成|
|6|Podの作成|

## １．事前確認
    # kubectl get node -o wide
      NAME         STATUS    AGE       EXTERNAL-IP  
      pshost02     Ready     19d       <none>  
      pshost03     Ready     19d       <none>  

## ２．Dockerレジストリ作成
    # git clone https://github.com/ultimania/mykube.git
    # kubectl create secret docker-registry ${SECRET_NAME} --docker-server=${REGISTRY_FQDN} --docker-username=${REGISTRY_USERNAME} --docker-password=${REGISTRY_PASSWORD} --docker-email=${REGISTRY_EMAIL}
    # kubectl create -f ./yaml/system/pv-pv002.yaml
    # kubectl create -f ./yaml/system/registry-private.yaml

|変数名|設定内容|
|:-----------|:-----------|
|SECRET_NAME|任意のSecret名|
|REGISTRY_FQDN|レジストリのFQDN|
|REGISTRY_USERNAME|ログインユーザ名|
|REGISTRY_PASSWORD|ログインパスワード|
|REGISTRY_EMAIL|Emailアドレス|


## ３．コンテナからイメージ作成/確認
    # export container_id=<コンテナID>
    # export image_name=<イメージ名>
    # export version=<バージョン>

    # docker stop ${container_id}
    # docker commit  ${container_id}  ${image_name}:${version}
    # docker tag ${image_name}:${version}  pshost02:5000/study/${image_name}:${version}

    # docker login  pshost02:5000
    # docker push  pshost02:5000/study/${image_name}:${version}
    # docker images


## ４．永続ボリューム作成  
    # kubectl create -f ./yaml/template/myvolume.yaml
```yaml
[myvolume.yaml]
apiVersion:                             # v1固定
    v1
kind:                                   # PersistentVolume固定
    PersistentVolume
metadata:
    name:
        mypv                            # ボリューム名
spec:
    capacity:
        storage:
            100Gi                       # ボリュームサイズ
    accessModes:
        -   ReadWriteOnce               # アクセス方式
    persistentVolumeReclaimPolicy:      # データ削除ポリシー
        Retain
    hostPath:                           # ボリューム作成先
        path: 
            /opt/kube/volumes/mypv
---
apiVersion:                             # v1固定
    v1
kind:                                   # PersistentVolumeClaim固定
    PersistentVolumeClaim
metadata:
    name:                               # 請求名
        mypvc
spec:
    accessModes:
    -   ReadWriteOnce                   # アクセス方式
    resources:
        requests:
            storage: 
                100Gi                   # 請求サイズ
```


## ５．Secretの作成
    # kubectl create -f ./yaml/template/mysecret.yaml
```yaml
[mysecret.yaml]
apiVersion:                 # "v1"固定
    v1
kind:                       # "Secret"固定
    Secret
metadata:
    name:                   # 任意の名前を記載
        mysecret
type:                       # "Opaque"固定
    Opaque
data:                       # 値はBase64エンコード
    root_password: YWRtaW4=
    user: YWRtaW4=
    password: YWRtaW4=
```

## ６．Pod(Deployment)の作成
    # kubectl create -f ./yaml/template/mariadb.yaml
```yaml
[mariadb.yaml]
apiVersion:                 # Deploymentを使用するのでextensions/v1beta1
    extensions/v1beta1
kind:                       # Deployment固定
    Deployment
metadata:
    name:                   # ポッド名
        mymariadb
spec:
  replicas:                 # 任意のスケール値
    1
  template:
    spec:
        containers:             # ポッド内で起動するコンテナ（複数指定可）
        -   image:              # コンテナイメージ
                pshost02:5000/study/mariadb:1.0
            name:               # コンテナ名
                redmine-db
            env:                # コンテナに渡す環境変数（複数指定可）
            -   name:           # 変数1
                    MYSQL_DATABASE
                value:          # 値
                    redmine
            -   name:           # 変数2
                    MYSQL_DATABASE
                valueFrom:      # 値（Secretから取得）
                    secretKeyRef:
                        name:   # Secret名
                            mysecret
                        key:    # Secretキー
                            root_password
            ports:              # コンテナ外部へ開放するポート番号（複数指定可）
            -   containerPort:  # ポート番号
                    3306
                name:           # 名前も付けられる
                    redmine-db
            volumeMounts:       # コンテナで使用するボリュームとマウントポイント（複数指定可）
            -   name: redmine-db-volume
                mountPath: /var/lib/mysql
        volumes:                # ボリュームに対する請求
            -   name: redmine-db-volume
                persistentVolumeClaim:
                    claimName: mypvc
```
