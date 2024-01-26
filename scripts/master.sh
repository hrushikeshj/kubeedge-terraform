#!/bin/bash
#
# Setup for Control Plane (Master) servers
#ip --json a s | jq '.[] | if .ifname != "lo" then .addr_info[] | if .family == "inet" then .local else empty end else empty end'
set -euxo pipefail
exec &> /master.log

DNS_SERVERS="8.8.8.8 1.1.1.1"
ENVIRONMENT=""
KUBERNETES_VERSION="1.27.1-00"
OS="xUbuntu_22.04"
CONTROL_IP=$(ip --json a s | jq -r '.[] | if .ifname != "lo" then .addr_info[] | if .family == "inet" then .local else empty end else empty end' | head -n 1)
POD_CIDR="172.16.1.0/16"
SERVICE_CIDR="172.17.1.0/18"
KB="gs://kubeedge-config-bucket"

echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update -y
sudo apt-get install -y kubelet="$KUBERNETES_VERSION" kubectl="$KUBERNETES_VERSION" kubeadm="$KUBERNETES_VERSION"
sudo apt-get update -y
sudo apt-get install -y jq

local_ip="$(ip --json a s | jq -r '.[] | if .ifname != "lo" then .addr_info[] | if .family == "inet" then .local else empty end else empty end' | head -n 1)"
cat > /etc/default/kubelet << EOF
KUBELET_EXTRA_ARGS=--node-ip=$local_ip
${ENVIRONMENT}
EOF


# Install CNI
wget https://github.com/containernetworking/plugins/releases/download/v1.3.0/cni-plugins-linux-amd64-v1.3.0.tgz
sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.3.0.tgz


NODENAME=$(hostname -s)

sudo kubeadm config images pull

echo "Preflight Check Passed: Downloaded All Required Images"

# Note: kube-proxy may be required for cloudcore
# neet to investigate
# --skip-phases=addon/kube-proxy
sudo kubeadm init --apiserver-advertise-address=$CONTROL_IP --apiserver-cert-extra-sans=$CONTROL_IP --pod-network-cidr=$POD_CIDR --service-cidr=$SERVICE_CIDR --node-name "$NODENAME" --ignore-preflight-errors Swap

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown "$(id -u)":"$(id -g)" $HOME/.kube/config

# Save Configs to shared /Vagrant location

# For Vagrant re-runs, check if there is existing configs in the location and delete it for saving new configuration.

config_path="/home/hrushi2002j/configs"

if [ -d $config_path ]; then
  rm -f $config_path/*
else
  mkdir -p $config_path
fi

cp -i /etc/kubernetes/admin.conf $config_path/config
touch $config_path/join.sh
chmod +x $config_path/join.sh

kubeadm token create --print-join-command > $config_path/join_k8s.sh

sudo -i -u hrushi2002j bash << EOF
whoami
mkdir -p /home/hrushi2002j/.kube
sudo cp -i $config_path/config /home/hrushi2002j/.kube/
sudo chown 1000:1000 /home/hrushi2002j/.kube/config
sudo chown hrushi2002j /home/hrushi2002j/.kube/config
EOF
#chmod 775

# # Install Metrics Server

# kubectl apply -f https://raw.githubusercontent.com/techiescamp/kubeadm-scripts/main/manifests/metrics-server.yaml

# Install keadm
KUBEEDGE_VERSION=v1.15.1
wget https://github.com/kubeedge/kubeedge/releases/download/$KUBEEDGE_VERSION/keadm-$KUBEEDGE_VERSION-linux-amd64.tar.gz
tar -zxvf keadm-$KUBEEDGE_VERSION-linux-amd64.tar.gz
sudo cp keadm-$KUBEEDGE_VERSION-linux-amd64/keadm/keadm /usr/local/bin/keadm

sleep 20s
# allow pods scheduling on master, (required for coredns)
kubectl taint node --all node-role.kubernetes.io/control-plane:NoSchedule-

keadm init --advertise-address=$CONTROL_IP version=v1.15.1 --kube-config=$HOME/.kube/config --set cloudCore.modules.dynamicController.enable=true
sleep 30s
keadm gettoken --kube-config=$HOME/.kube/config > $config_path/token
echo $CONTROL_IP > $config_path/CONTROL_IP

echo "copy token to config bucket"
gsutil cp $config_path/CONTROL_IP $config_path/token $KB

# flannel stuff
# sudo iptables -t nat -A OUTPUT -p tcp --dport 10350 -j DNAT --to $CONTROL_IP:10003 # check if this is required <- yes
# nohup kubectl proxy --port=10550 &
# kubectl apply -f /vagrant/kube-flannel.yml
# sudo ip link delete cni0

echo "install helm"
wget https://get.helm.sh/helm-v3.14.0-linux-amd64.tar.gz
tar -zxvf helm-v3.14.0-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
rm -f helm-v3.14.0-linux-amd64.tar.gz
