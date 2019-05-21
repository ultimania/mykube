# Kubernetes 操作リファレンス
### 前提条件
* dockerが導入済みであること

## イメージのビルド
リポジトリをクローンする。

    # git clone https://github.com/ultimania/mykube.git

DockerFileをビルドする

    # cd ./dockerfile/api-server
    # docker build . -t api-server

イメージが作成されていることを確認する

    # docker images
