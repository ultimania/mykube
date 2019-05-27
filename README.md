# Kubernetes環境構築
## 前提条件
* 物理マシン（VM）でMaster1台、Node2台を用意（いずれもインターネット接続可能）
* ソフトウェアバージョンは以下のとおり。

|SW|Version|note|
|:--|:--|:--|
|CentOS|7.5.1804||
|Kubernetes|v1.14|Latest Version|
|Docker|1.13.1||


* ネットワーク構成は以下のとおり

|No|Machine|Hostname|IP Address|
|:--|:--|:--|:--|
|1|Master|pshost01|192.168.0.20|
|2|Node1|pshost02|192.168.0.21|
|3|Node2|pshost03|192.168.0.22|

## 手順概要

|No|作業内容|作業時間|作業ホスト|
|:-----------|:-----------|:-----------|:-----------|
|1|共通設定|5分|pshost01,pshost02,pshost03|
|2|Master設定|5分|pshost01|
|3|Node設定|5分|pshost02,pshost03|
|4|Kubernetes Dashboardの設定|5分|pshost02,pshost03|


## １．共通設定
### ホスト間の名前解決（/etc/hosts）
    # vi /etc/hosts
    # cp -p /etc/hosts /etc/hosts.`date +%Y%m%d`
    # echo "192.168.0.20    pshost01"  >>  /etc/hosts
    # echo "192.168.0.21    pshost02"  >>  /etc/hosts
    # echo "192.168.0.22    pshost03"  >>  /etc/hosts


### 前提パッケージのインストール
    # yum -y update
    # yum -y install docker
    # systemctl enable docker && sudo systemctl start docker


### Dockerインストール用レポジトリの設定
    # cat <<EOF > /etc/yum.repos.d/kubernetes.repo
    [kubernetes]
    name=Kubernetes
    baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
    enabled=1
    gpgcheck=1
    repo_gpgcheck=1
    gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
    exclude=kube*
    EOF


### Kubernetes関連ソフトウェアのインストール
    # yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes
    # systemctl enable kubelet && sudo systemctl start kubelet


### セキュリティ関連機能(SELinux,Firewalld)の無効化
    # setenforce 0
    # cp -p /etc/selinux/config /etc/selinux/config.`date +%Y%m%d`
    # sed -i -e 's#SELINUX=enforcing#SELINUX=disabled#g'  /etc/selinux/config
    # systemctl disable firewalld
    # systemctl stop firewalld

### ネットワーク用パラメータの設定
    # cat <<EOF >  /etc/sysctl.d/k8s.conf
    net.bridge.bridge-nf-call-ip6tables = 1
    net.bridge.bridge-nf-call-iptables = 1
    EOF
    # sysctl --system
    # lsmod | grep br_netfilter


### swapの無効化
    # swapoff -a
    # sed -i -e 's%/dev/mapper/rhel-swap%#/dev/mapper/rhel-swap%g' /etc/fstab


## ２．Master設定
### イメージプル
    # kubeadm config images pull


### クラスタの作成
    # kubeadm init --pod-network-cidr=10.244.0.0/16


### 各種設定ファイルの変更
    # mkdir -p $HOME/.kube
    # cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    # chown $(id -u):$(id -g) $HOME/.kube/config


### ネットワーク設定の反映
    # kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/a70459be0084506e4ec919aa1c114638878db11b/Documentation/kube-flannel.yml


## ３．Node設定
### クラスタへの追加
    # kubeadm join 192.168.0.20:6443 --token a48nff.801d2m441e9tw1pg --discovery-token-ca-cert-hash sha256:14ae615f1ec87efa10124952950ba663a35101f1f1d35094175a3ffa1f9e9083 
    # kubectl get nodes


## 4．Kubernetes Dashboardの設定
### Kubernetes Dashboardのインストール
    # wget https://raw.githubusercontent.com/kubernetes/dashboard/master/aio/deploy/alternative/kubernetes-dashboard.yaml
    # #ServiceのTypeをnodePortにし、ClusterIPを追加する
    # kubectl apply -f  kubernetes-dashboard.yaml


### Service Accountの権限設定
    # cat <<EOF | kubectl apply -f -
    apiVersion: rbac.authorization.k8s.io/v1beta1
    kind: ClusterRoleBinding
    metadata:
      name: kubernetes-dashboard
      labels:
        k8s-app: kubernetes-dashboard
    roleRef:
      apiGroup: rbac.authorization.k8s.io
      kind: ClusterRole
      name: cluster-admin
    subjects:
    - kind: ServiceAccount
      name: kubernetes-dashboard
      namespace: kube-system
    EOF

