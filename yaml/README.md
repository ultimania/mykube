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
各ノードがクラスタに登録されていることを確認する。

    # kubectl get node -o wide
      NAME         STATUS    AGE       EXTERNAL-IP  
      pshost02     Ready     19d       <none>  
      pshost03     Ready     19d       <none>  

## ２．Dockerレジストリ作成
k8s用のリポジトリをクローンする。

    # git clone https://github.com/ultimania/mykube.git

Dockerレジストリをデプロイする。

    # kubectl create -f ./yaml/template/myregistry.yaml

```yaml
[myregistry.yaml]
# Dockerレジストリ用サービス
apiVersion: 
  v1
kind: 
  Service
metadata:
  name: 
    myregistry-svc
spec:
  selector:       # サービスとPodを紐づけるための識別子
    name: 
      registry
  ports:
  - port:         # サービス待受けポート 
      5000
    targetPort:   # Pod側へフォワードするポート
      5000
    nodePort:     # クラスタ管理用のポート
      30000
    protocol: 
      TCP
  externalIPs:    # 外部接続用の待受けIPアドレス
  - 192.168.0.21
  - 192.168.0.22
  type:           # サービス提供タイプ
    NodePort
---
# Dockerレジストリコンテナ
apiVersion: 
  extensions/v1beta1
kind: 
  Deployment
metadata:
  name: 
    registry
spec:
  replicas: 
    1
  template:
    metadata:
      labels:       # サービスとPodを紐づけるための識別子
        name:     
          registry
    spec:
      volumes:
      - name: 
          myregistry-volume
        persistentVolumeClaim:
          claimName: 
            myregistry-claim
      containers:
        - name: 
            registry
          image: 
            registry:2.3.0
          ports:
          - containerPort: 
              5000
          volumeMounts:
          - name: 
              myregistry-volume
            mountPath: 
              /var/lib/registry
---
# コンテナ用ボリューム請求
apiVersion: 
  v1
kind: 
  PersistentVolumeClaim
metadata:
  name: 
    myregistry-claim
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 
        100Gi
```
サービス提供タイプは以下の４種類
- ClusterIp : クラスタ内のIPにServiceを公開。クラスタ内部からのみアクセス可能。
- NodePort : 各ノードの静的ポートにServiceを公開。クラスタ外部からもアクセス可能。
- LoadBalancer : クラウドプロバイダのロードバランサを使用してServiceを公開。
- ExternalName : kube-dnsを使用してCNAMEレコードでServiceを公開。

"サービスとPodを紐づけるための識別子"は、サービス/Podそれぞれのマニフェストで同一のものを指定すること。(上記だと「name : registry」)

Dockerレジストリは永続ボリュームの仕様を推奨する。デプロイ前に「４．永続ボリューム作成」を参考にPod用の永続ボリュームを作成しておく。

Docker Image Pull用のSecretを作成する

    # kubectl create secret docker-registry ${SECRET_NAME} --docker-server=${REGISTRY_FQDN} --docker-username=${REGISTRY_USERNAME} --docker-password=${REGISTRY_PASSWORD} --docker-email=${REGISTRY_EMAIL}

|変数名|設定内容|
|:-----------|:-----------|
|SECRET_NAME|任意のSecret名|
|REGISTRY_FQDN|レジストリのFQDN|
|REGISTRY_USERNAME|認証ユーザ名|
|REGISTRY_PASSWORD|認証パスワード|
|REGISTRY_EMAIL|Emailアドレス|


## ３．コンテナからイメージ作成・登録
    # export container_id=<コンテナID>
    # export image_name=<イメージ名>
    # export version=<バージョン>

対象のコンテナを停止しイメージを作成する

    # docker stop ${container_id}
    # docker commit  ${container_id}  ${image_name}:${version}

作成したイメージをDockerレジストリへ登録する

    # docker tag ${image_name}:${version}  pshost02:5000/study/${image_name}:${version}
    # docker login  pshost02:5000
    # docker push  pshost02:5000/study/${image_name}:${version}


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
```
persistentVolumeReclaimPolicyは、ボリュームに割り当てられたClaimが削除された場合のデータ削除についてのポリシー。上記の場合(Retain)だと同じClaimが割り当てられるまではデータを消さずに保持する。


## ５．Secretの作成

マニフェストファイルに直接記載できないような値（rootパスワード等）はsecretを使用jする。
設定情報はマスターのetcdの中に保存される。

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
        imagePullSecrets:       # image pullで使用するsecret
        -   name: regcred
        volumes:                # ボリュームに対する請求
            -   name: redmine-db-volume
                persistentVolumeClaim:
                    claimName: mypvc
```
