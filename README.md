# Kubernetes環境構築
## 前提条件
* 物理マシン（VM）でMaster1台、Node2台を用意（いずれもインターネット接続可能）
* ソフトウェアバージョンは以下のとおり。

|SW|Version|note|
|:--|:--|:--|
|CentOS|7.5.1804||
|Kubernetes|v1.5.2||
|etcd|3.2.22|node only|
|Flanneld|0.7.1||
|Docker|1.13.1|node only|


* MasterとNodeそれぞれで動くソフトウェアの配置は以下のとおり。

|No|Machine|install|
|:--|:--|:--|
|1|Master|Kubernetes, etcd, flannel, docker-registry|
|2|Node|Kubernetes (Kubelet), flannel, docker|

* ネットワーク構成は以下のとおり

|No|Machine|Hostname|IP Address|
|:--|:--|:--|:--|
|1|Master|pshost01|192.168.0.20|
|2|Node1|pshost02|192.168.0.21|
|3|Node2|pshost03|192.168.0.22|

## 手順概要
|No|作業内容|作業時間|作業ホスト|
|:-----------|:-----------|:-----------|:-----------|:-----------|
|1|共通設定|5分|pshost01,pshost02,pshost03|
|2|Master設定|10分|pshost01|
|3|Node設定|5分|pshost02,pshost03|


## １．共通設定
### ホスト間の名前解決（/etc/hosts）
    # vi /etc/hosts
    # cp -p /etc/hosts /etc/hosts.`date +%Y%m%d`
    # echo "192.168.0.20    pshost01"  >>  /etc/hosts
    # echo "192.168.0.21    pshost02"  >>  /etc/hosts
    # echo "192.168.0.22    pshost03"  >>  /etc/hosts


### 前提パッケージのインストール
    # yum -y install bash-completion tcpdump chrony wget git docker


### Dockerインストール用レポジトリの設定
    # echo "[virt7-docker-common-release]"   >> /etc/yum.repos.d/virt7-docker-common-release.repo
    # echo "name=virt7-docker-common-release"  >> /etc/yum.repos.d/virt7-docker-common-release.repo
    # echo "baseurl=http://cbs.centos.org/repos/virt7-docker-common-release/x86_64/os/"  >> /etc/yum.repos.d/virt7-docker-common-release.repo
    # echo "gpgcheck=0"  >> /etc/yum.repos.d/virt7-docker-common-release.repo

### Kubernetes関連ソフトウェアのインストール
    # yum -y install --enablerepo=virt7-docker-common-release kubernetes etcd flannel

### セキュリティ関連機能(SELinux,Firewalld)の無効化
    # setenforce 0
    # cp -p /etc/selinux/config /etc/selinux/config.`date +%Y%m%d`
    # sed -i -e 's#SELINUX=enforcing#SELINUX=disabled#g'  /etc/selinux/config
    # systemctl disable firewalld
    # systemctl stop firewalld

### 証明書の作成
    # yum -y install python-rhsm
    # wget http://mirror.centos.org/centos/7/os/x86_64/Packages/python-rhsm-certificates-1.19.10-1.el7_4.x86_64.rpm
    # rpm2cpio python-rhsm-certificates-1.19.10-1.el7_4.x86_64.rpm | cpio -iv --to-stdout ./etc/rhsm/ca/redhat-uep.pem | tee /etc/rhsm/ca/redhat-uep.pem

## ２．Master設定
### RSA鍵の作成
    openssl genrsa -out /etc/kubernetes/serviceaccount.key 2048

### 各種設定ファイルの変更
|No|ファイルパス|変更パラメータ|デフォルト値|変更値|
|:-----------|:-----------|:-----------|:-----------|:-----------|
|①|/etc/kubernetes/config|KUBE_MASTER|--master=http://127.0.0.1:8080|--master=http://pshost01:8080|
|②|/etc/kubernetes/kubelet|KUBELET_HOSTNAME|--hostname-override=127.0.0.1|--hostname-override=|
|③|/etc/kubernetes/apiserver|KUBE_API_ADDRESS|--insecure-bind-address=127.0.0.1|--insecure-bind-address=0.0.0.0|
|||KUBE_API_PORT|--port=8080|--insecure-port=8080|
|||KUBE_ETCD_SERVERS|--etcd-servers=http://127.0.0.1:2379|--etcd-servers=http://pshost01:2379|
|||KUBE_API_ARGS||--service_account_key_file=/etc/kubernetes/serviceaccount.key|
|④|/etc/kubernetes/controller-manager|KUBE_CONTROLLER_MANAGER_ARGS||--service_account_private_key_file=/etc/kubernetes/serviceaccount.key|
|⑤|/etc/etcd/etcd.conf|ETCD_LISTEN_CLIENT_URLS|http://localhost:2379|http://0.0.0.0:2379|
||||http://localhost:2379|http://0.0.0.0:2379|

#### ① /etc/kubernetes/config
    # cp -p /etc/kubernetes/config /etc/kubernetes/config.`date +%Y%m%d`
    # sed -i -e 's#--master=http://127.0.0.1:8080#--master=http://pshost01:8080#g'              /etc/kubernetes/config
#### ② /etc/kubernetes/kubelet
    # cp -p /etc/kubernetes/kubelet /etc/kubernetes/kubelet.`date +%Y%m%d`
    # sed -i -e 's#hostname-override=127.0.0.1#hostname-override=#g'                /etc/kubernetes/kubelet
#### ③ /etc/kubernetes/apiserver
    # cp -p /etc/kubernetes/apiserver /etc/kubernetes/apiserver.`date +%Y%m%d`
    # sed -i -e 's#insecure-bind-address=127.0.0.1#insecure-bind-address=0.0.0.0#g'         /etc/kubernetes/apiserver
    # sed -i -e 's%# KUBE_API_PORT="--port=8080%KUBE_API_PORT="--insecure-port=8080%g'      /etc/kubernetes/apiserver
    # sed -i -e 's#--etcd-servers=http://127.0.0.1:2379#--etcd-servers=http://pshost01:2379#g'  /etc/kubernetes/apiserver
    # echo 'KUBE_API_ARGS="--service_account_key_file=/etc/kubernetes/serviceaccount.key"' >>   /etc/kubernetes/apiserver
#### ④ /etc/kubernetes/controller-manager
    # cp -p /etc/kubernetes/controller-manager  /etc/kubernetes/controller-manager.`date +%Y%m%d`
    # sed -i -e 's#KUBE_CONTROLLER_MANAGER_ARGS=""#KUBE_CONTROLLER_MANAGER_ARGS="--service_account_private_key_file=/etc/kubernetes/serviceaccount.key"#g'  /etc/kubernetes/controller-manager
#### ⑤ /etc/etcd/etcd.conf
    # cp -p /etc/etcd/etcd.conf /etc/etcd/etcd.conf.`date +%Y%m%d`
    # sed -i -e 's%ETCD_LISTEN_CLIENT_URLS="http://localhost:2379"%ETCD_LISTEN_CLIENT_URLS="http://0.0.0.0:2379"%g'                                 /etc/etcd/etcd.conf
    # sed -i -e 's%ETCD_ADVERTISE_CLIENT_URLS="http://localhost:2379"%ETCD_ADVERTISE_CLIENT_URLS="http://0.0.0.0:2379"%g'                                 /etc/etcd/etcd.conf

### etcdctlでflannelが利用するネットワーク周りの設定
    # etcdctl mkdir /registry/network
    # etcdctl mk /registry/network/config "{ \"Network\": \"172.30.0.0/16\", \"SubnetLen\": 24, \"Backend\": { \"Type\": \"vxlan\" } }"
    # etcdctl ls

### 関連サービスの起動とサービス登録 
    # for SERVICES in etcd kube-apiserver kube-controller-manager kube-scheduler flanneld; do
        systemctl restart $SERVICES
        systemctl enable $SERVICES
        systemctl status $SERVICES
    done


## ３．Node設定
### 不要サービスの停止・無効化
    # for SERVICES in etcd kube-apiserver kube-controller-manager kube-scheduler flanneld; do
        systemctl stop $SERVICES
        systemctl disable $SERVICES
        systemctl status $SERVICES
    done

### 各種ファイル設定
|No|ファイルパス|変更パラメータ|デフォルト値|変更値|
|:-----------|:-----------|:-----------|:-----------|:-----------|
|①|/etc/kubernetes/kubelet|KUBELET_HOSTNAME|--hostname-override=127.0.0.1|--hostname-override=|
|||KUBELET_ADDRESS|--address=127.0.0.1|--address=0.0.0.0|
|||KUBELET_API_SERVER|--api-servers=http://127.0.0.1:8080|--api-servers=http://kube-master:8080|
|④|/etc/sysconfig/flanneld|FLANNEL_ETCD||http://pshost01:2379|



#### ① /etc/kubernetes/kubelet
    # cp -p /etc/kubernetes/kubelet /etc/kubernetes/kubelet.`date +%Y%m%d`
    # sed -i -e 's#hostname-override=127.0.0.1#hostname-override=#g'                /etc/kubernetes/kubelet
    # sed -i -e 's%KUBELET_ADDRESS="--address=127.0.0.1"%KUBELET_ADDRESS="--address=0.0.0.0"%g'                     /etc/kubernetes/kubelet
    # sed -i -e 's%KUBELET_API_SERVER="--api-servers=http://127.0.0.1:8080"%KUBELET_API_SERVER="--api-servers=http://pshost01:8080"%g'      /etc/kubernetes/kubelet

#### ② /etc/sysconfig/flanneld
    # echo 'FLANNEL_ETCD="http://pshost01:2379"' >> /etc/sysconfig/flanneld

### Docker Registry登録
    # echo '{ "insecure-registries":["pshost03:5000","pshost02:5000"] }' > /etc/docker/daemon.json

### 関連サービスの起動とサービス登録 (Node)
    for SERVICES in kube-proxy kubelet flanneld docker; do
        systemctl restart $SERVICES
        systemctl enable $SERVICES
        systemctl status $SERVICES
    done

### IPフォワード設定
    # iptables -P FORWARD ACCEPT
    # cp -p /etc/rc.local /etc/rc.local.`date +%Y%m%d`
    # echo "/sbin/iptables-restore < /etc/network/iptables" >> /etc/rc.local
    # diff /etc/rc.local.`date +%Y%m%d` /etc/rc.local

### kubernetesノード登録/確認
    # kubectl config set-cluster default-cluster --server=http://kube-master:8080
    # kubectl config set-context default-context --cluster=default-cluster --user=default-admin
    # kubectl config use-context default-context
    # kubectl cluster-info
      Kubernetes master is running at http://pshost01:8080

