helm install edgemesh --namespace kubeedge \
--set agent.psk=v116P0MeHhjKSFUG+YmJfkZiWwa+QcZFVZv/cqodCZk= \
--set agent.relayNodes[0].nodeName=terraform-master,agent.relayNodes[0].advertiseAddress="{10.128.0.2}" \
https://raw.githubusercontent.com/kubeedge/edgemesh/main/build/helm/edgemesh.tgz

helm install edgemesh \
--namespace kubeedge \
--set agent.image=kubeedge/edgemesh-agent:v1.15.0 \
--set server.image=kubeedge/edgemesh-server:v1.15.0 \
--set server.nodeName=terraform-master \
--set server.advertiseAddress="{10.128.0.2}" ./build/helm/edgemesh

sudo iptables -P FORWARD ACCEPT

#################
helm install edgemesh --namespace kubeedge \
--set agent.psk=`openssl rand -base64 32` \
--set agent.relayNodes[0].nodeName=terraform-master,agent.relayNodes[0].advertiseAddress={10.128.0.2} \
https://raw.githubusercontent.com/kubeedge/edgemesh/main/build/helm/edgemesh.tgz


sudo CLOUDCOREIPS=10.128.0.3 /etc/kubernetes/pki/certgen.sh stream

wget https://get.helm.sh/helm-v3.14.0-linux-amd64.tar.gz
tar -zxvf helm-v3.14.0-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
