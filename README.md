## 更新履歴
|更新日|更新者|更新内容|
|:-----------|:-----------|:-----------|
|2018.09.14|ultimania|新規作成|
|2018.11.25|ultimania|構築手順追加|
# Kubernetes環境構築
## 前提条件
* 物理マシン（VM）でMaster1台、Node2台を用意する。
* ソフトウェアバージョンは以下のとおり。

|SW|Version|note|
|:--|:--|:--|
|CentOS|7.5.1804||
|Kubernetes|v1.5.2||
|etcd|3.2.22|node only|
|Flanneld|0.7.1||
|Docker|1.13.1|node only|


* MasterとNodeそれぞれで動くソフトウェアの配置は以下の通り。
|No|Machine|install|
|:--|:--|:--|
|1|Master|Kubernetes, etcd, flannel, docker-registry|
|2|Node|Kubernetes (Kubelet), flannel, docker|

## 手順概要
|No|作業内容|確認事項|作業時間|備考|
|:-----------|:-----------|:-----------|:-----------|:-----------|
|1|Master/Node共通設定|適切にインストールされていること|10分||
|2|Master設定|適切にインストールされていること|5分||
|3|Node設定|適切にインストールされていること|5分||


## Master/Node共通設定
### hostsの設定
```# vi /etc/hosts```
```
192.168.0.20  kube-master
192.168.0.21  kube-node1
192.168.0.22  kube-node2


### 前提パッケージのインストール
'''# yum -y install bash-completion tcpdump chrony wget git'''


### Dockerインストール用レポジトリの設定
'''# vi /etc/yum.repos.d/virt7-docker-common-release.repo'''
'''
[virt7-docker-common-release]
name=virt7-docker-common-release
baseurl=http://cbs.centos.org/repos/virt7-docker-common-release/x86_64/os/
gpgcheck=0
'''

### Kubernetes関連ソフトウェアのインストール
'''# yum -y install --enablerepo=virt7-docker-common-release kubernetes etcd flannel'''

### セキュリティ関連機能の無効化
SELinuxおよびFirewalldを停止します。
'''# getenforce'''
'''Disabled'''

この通りDisabledになっていない場合は、
'''# setenforce 0'''
Firewalldの停止
'''# systemctl disable firewalld'''
'''# systemctl stop firewalld'''



## Master設定
### Kubernetes関連ソフトウェアのインストール
'''yum -y install kubernetes'''

### RSA鍵の作成
'''# openssl genrsa -out /etc/kubernetes/serviceaccount.key 2048'''

### 各種ファイル設定
#### vi /etc/kubernetes/config
'''
KUBE_MASTER="--master=http://kube-master:8080"
'''

#### etc/kubernetes/kubelet
'''
KUBELET_HOSTNAME="--hostname-override=kube-master"
'''

#### /etc/kubernetes/apiserver
'''
KUBE_API_ADDRESS="--insecure-bind-address=0.0.0.0"
KUBE_API_PORT="--insecure-port=8080"
KUBE_ETCD_SERVERS="--etcd-servers=http://kube-master:2379"
KUBE_API_ARGS="--service_account_key_file=/etc/kubernetes/serviceaccount.key"
'''

#### /etc/kubernetes/controller-manager
'''
KUBE_CONTROLLER_MANAGER_ARGS="--service_account_private_key_file=/etc/kubernetes/serviceaccount.key"
'''

#### /etc/etcd/etcd.conf
ETCD_LISTEN_CLIENT_URLS="http://0.0.0.0:2379"


### etcdctlでflannelが利用するネットワーク周りの設定
'''# etcdctl mk /atomic.io/network/config '{"Network":"172.30.0.0/16", "SubnetLen":24, "Backend":{"Type":"vxlan"} }''''

'''# etcdctl ls'''
'''# systemctl restart flanneld'''


### 関連サービスの起動とサービス登録 
'''
for SERVICES in etcd kube-apiserver kube-controller-manager kube-scheduler flanneld; do
    systemctl restart $SERVICES
    systemctl enable $SERVICES
    systemctl status $SERVICES
done
'''

'''yum -y install python-rhsm'''
'''wget http://mirror.centos.org/centos/7/os/x86_64/Packages/python-rhsm-certificates-1.19.10-1.el7_4.x86_64.rpm'''
'''rpm2cpio python-rhsm-certificates-1.19.10-1.el7_4.x86_64.rpm | cpio -iv --to-stdout ./etc/rhsm/ca/redhat-uep.pem | tee /etc/rhsm/ca/redhat-uep.pem '''



## Node設定
### Kubernetes関連ソフトウェアのインストール
'''# yum -y install docker'''

### etcd無効化
'''# systemctl status etcd'''

### 各種ファイル設定
#### /etc/kubernetes/kubelet
KUBELET_ADDRESS="--address=0.0.0.0"
KUBELET_HOSTNAME="--hostname-override="
KUBELET_API_SERVER="--api-servers=http://kube-master:8080"

#### /etc/sysconfig/flanneld
FLANNEL_ETCD="http://kube-master:2379"


### 関連サービスの起動とサービス登録 (Node)
'''
for SERVICES in kube-proxy kubelet flanneld docker; do
    systemctl restart $SERVICES
    systemctl enable $SERVICES
    systemctl status $SERVICES
done
'''

### kubectl
'''
$ kubectl config set-cluster default-cluster --server=http://kube-master:8080
$ kubectl config set-context default-context --cluster=default-cluster --user=default-admin
$ kubectl config use-context default-context
$ kubectl cluster-info
'''


# 作業手順書
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
[mariadb_pvc.yaml]  

kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: local-claim
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
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
```# kubectl create -f yaml/redmine/mariadb_secret.yaml```  
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
```# kubectl describe secret dbsecret```
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
```# kubectl create -f yaml/redmine/mariadb_deployment.yaml```  
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
```# kubectl get pod -o wide```
```
NAME                           READY     STATUS    RESTARTS   AGE       IP            NODE
redmine-db-585564705-px4rr     1/1       Running   0          10s        172.30.20.4   kube-node2
```
