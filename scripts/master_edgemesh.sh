#!/bin/bash
set -euxo pipefail
exec &> /master_edgemesh.log

config_path="/home/hrushi2002j/configs"
control_ip=$(sudo cat $config_path/CONTROL_IP)
master_node_name=$(hostname -s) # wil work bc, run by master

sudo wget https://raw.githubusercontent.com/kubeedge/kubeedge/master/build/tools/certgen.sh -O /etc/kubernetes/pki/certgen.sh
#2
sudo chmod +x /etc/kubernetes/pki/certgen.sh
#3
sudo CLOUDCOREIPS=$control_ip /etc/kubernetes/pki/certgen.sh stream

sudo -i -u hrushi2002j bash << EOF
mkdir -p /home/hrushi2002j/.kube
if [ ! -f  /home/hrushi2002j/.kube/config ]; then
  sudo cp -i $config_path/config /home/hrushi2002j/.kube/
fi
sudo chown 1000:1000 /home/hrushi2002j/.kube/config
sudo chown hrushi2002j /home/hrushi2002j/.kube/config


helm install edgemesh --namespace kubeedge \
--set agent.psk=`openssl rand -base64 32` \
--set agent.relayNodes[0].nodeName=$master_node_name,agent.relayNodes[0].advertiseAddress={$control_ip} \
https://raw.githubusercontent.com/kubeedge/edgemesh/main/build/helm/edgemesh.tgz
EOF

echo "master_edgemesh done"
