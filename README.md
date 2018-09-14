# 作業手順書
## 更新履歴
|更新日|更新者|更新内容|
|:-----------|:-----------|:-----------|
|2018.09.14|ultimania|新規作成|
## 前提条件
* Kubernetesが構築済みであること
## 環境
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
#### Pod
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

## 手順概要
|No|作業内容|確認事項|作業時間|備考|
|:-----------|:-----------|:-----------|:-----------|:-----------|
|1|事前確認|環境が正しい状態であることを確認|5分||
|2|DBサーバ用ボリュームの作成|PersistentVolumeが正常に作成されていること。|3分||
|3|DBサーバ用認証secretの作成|secretが正常に作成されていること。||
|4|各種Deploymentの作成|各種Podが正常に動作すること。|7分||
|5|SSL-Accelerrator用サービスの作成|サービスが正常に作成されていること。<br>外部のブラウザから正常にアクセスできること。|7分||

* * *

## 手順詳細
1. 事前確認  
各ノードが起動していることを確認する。  
```# kubectl get node -o wide```
```  
NAME         STATUS    AGE       EXTERNAL-IP  
kube-node1   Ready     19d       <none>  
kube-node2   Ready     19d       <none>  
```

2. DBサーバ用ボリュームの作成  
   リポジトリをクローンする  
```# git clone https://github.com/ultimania/mykube.git```  
<br>

   PersistentVolumeをデプロイする  
```# cd mykube```  
```# kubectl create -f yaml/redmine/mariadb_pv.yaml```  

``` 
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

   PersistentVolumeを確認する  
```# kubectl describe pv pv001```  
