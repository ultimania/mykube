# 作業手順書
### 更新履歴
|更新日|更新者|更新内容|
|:-----------|:-----------|:-----------|
|2018.09.14|ultimania|新規作成|
### 前提条件
* Kubernetesが構築済みであること
# 環境
### 物理ホスト
|ノード名|IP|ログイン|パスワード|役割|
|:--|:--|:--|--:|:--|
|kube-master|192.168.0.20|root|********|マスターノード|
|kube-node1|192.168.0.21|root|********|クラスタ構成ノード#1|
|kube-node2|192.168.0.22|root|********|クラスタ構成ノード#2|

### バージョン（物理ホスト共通）
|SW|Version|note|
|:--|:--|:--|
|CentOS|release 7.5.1804||
|Kubernetes|1.5.2-0.7||
|etcd|3.2.22-1| node のみで実行|
|Flanneld|0.7.1-4||
|Docker|1.13.1-74|node のみで実行|
### Kubernetesクラスタ
#### Pod（IPは動的に振られるので参考値）
|名前|IP|ノード|役割|
|:-----------|:-----------|:-----------|:------------|
|ssl-accelerator|172.30.48.2|kube-node1|SSLアクセラレータ<br>ロードバランサ|
|web1|172.30.48.3|kube-node1|WEBサーバ#1<br>ロードバランサ|
|web2|172.30.20.2|kube-node2|WEBサーバ#2<br>ロードバランサ|
|ap1|172.30.48.4|kube-node1|APサーバ#1|
|ap2|172.30.20.3|kube-node2|APサーバ#2|
|db|172.30.20.4|kube-node2|DBサーバ|
#### service
|名前|外部IP|待受けポート|経由ポート|宛先ポート|役割|
|:--|:--|:--|:--|:--|:--|
|client-service|192.168.0.21|80|30001|80|外部アクセスの待受け|

### 手順概要
|No|作業内容|確認事項|作業時間|備考|
|:-----------|:-----------|:-----------|:-----------|:-----------|
|1|事前確認|環境が正しい状態であることを確認|5分||
|2|DBサーバ用ボリュームの作成|PersistentVolumeが正常に作成されていること。|3分||
|3|DBサーバ用認証secretの作成|secretが正常に作成されていること。||
|4|各種Deploymentの作成|各種Podが正常に動作すること。|7分||
|5|SSL-Accelerrator用サービスの作成|サービスが正常に作成されていること。<br>外部のブラウザから正常にアクセスできること。|7分||

* * *

# 手順詳細
## 事前確認  
各ノードが起動していることを確認する。  
```# kubectl get node -o wide```
```  
NAME         STATUS    AGE       EXTERNAL-IP  
kube-node1   Ready     19d       <none>  
kube-node2   Ready     19d       <none>  
```

## DBサーバ用ボリュームの作成  

- リポジトリをクローンする  
```# git clone https://github.com/ultimania/mykube.git```  


- PersistentVolumeをデプロイする  
```# cd mykube```  
```# kubectl create -f yaml/redmine/mariadb_pv.yaml```  

```yaml
[mariadb_pv.yaml]  

apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv001
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /opt/kube/volumes/vol1
```

- PersistentVolumeClaimをデプロイする  
```# kubectl create -f yaml/redmine/mariadb_pvc.yaml```  

```yaml
[mariadb_pv.yaml]  

apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv001
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /opt/kube/volumes/vol1
```

- PersistentVolumeを確認する  
```# kubectl describe pv pv001```  

```
Name:           pv001
Labels:         <none>
StorageClass: 
Status:         Bound
Claim:          default/local-claim
Reclaim Policy: Retain
Access Modes:   RWO
Capacity:       10Gi
Message: 
Source:
    Type:       HostPath (bare host directory volume)
    Path:       /opt/kube/volumes/vol1
No events.
```
- PersistentVolumeClaimを確認する  
```# kubectl describe pvc local-claim```  

```
Name:           local-claim
Namespace:      default
StorageClass: 
Status:         Bound
Volume:         pv001
Labels:         <none>
Capacity:       10Gi
Access Modes:   RWO
No events.
```

## DBサーバ用認証secretの作成  

- secretをデプロイする  
```kubectl create -f yaml/redmine/mariadb_secret.yaml```  
```yaml
[mariadb_secret.yaml]

apiVersion: v1
kind: Secret
metadata:
  name: dbsecret
type: Opaque
data:
  root_password: YWRtaW4=
  user: YWRtaW4=
  password: YWRtaW4=
```

- secretを確認する  
```kubectl describe secret dbsecret```
```
Name:           dbsecret
Namespace:      default
Labels:         <none>
Annotations:    <none>

Type:   Opaque

Data
====
password:       5 bytes
root_password:  5 bytes
user:           5 bytes
```


## DBサーバの作成  

- Deploymentをデプロイする  
```kubectl create -f yaml/redmine/mariadb_deployment.yaml```  
```yaml
[mariadb_deployment.yaml]

apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: redmine-db
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: redmine
    spec:
      containers:
      - image: mariadb
        name: redmine-db
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: dbsecret
              key: root_password
        ports:
        - containerPort: 3306
          name: redmine-db
        volumeMounts:
        - name: redmine-db-pvc
          mountPath: /var/lib/mysql
      volumes:
        - name: redmine-db-pvc
          persistentVolumeClaim:
            claimName: local-claim
```

- DBサーバ(Pod)が稼働しているかどうか確認する  
```kubectl get pod -o wide```
```
NAME                           READY     STATUS    RESTARTS   AGE       IP            NODE
redmine-db-585564705-px4rr     1/1       Running   0          10s        172.30.20.4   kube-node2
```
