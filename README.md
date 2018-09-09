# kubernetesCluster構築
`git clone https://github.com/ultimania/mykube.git`
---

## リポジトリ構成
- mykube
 - yaml
  - jenkins
  - nginx
  - redmine
  - system
- README.md

## jenkins
~~~bash
cd mykube
kubectl create -f yaml/jenkins.yaml
kubectl create -f yaml/jenkins_svc.yaml
~~~

|Serviceポート|jenkinsポート|
|8080|8080|


