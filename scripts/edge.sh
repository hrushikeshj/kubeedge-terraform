#!/bin/bash
#
# Setup for Node servers

set -euxo pipefail
exec &> /edge.log

# rm below line
# head telnet  2701

config_path="/home/hrushi2002j/configs"

# /bin/bash $config_path/join.sh -v

# Install keadm
KUBEEDGE_VERSION=v1.15.1
wget https://github.com/kubeedge/kubeedge/releases/download/$KUBEEDGE_VERSION/keadm-$KUBEEDGE_VERSION-linux-amd64.tar.gz
tar -zxvf keadm-$KUBEEDGE_VERSION-linux-amd64.tar.gz
sudo cp keadm-$KUBEEDGE_VERSION-linux-amd64/keadm/keadm /usr/local/bin/keadm

# Install CNI
wget https://github.com/containernetworking/plugins/releases/download/v1.3.0/cni-plugins-linux-amd64-v1.3.0.tgz
sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.3.0.tgz

# change cgroupdriver to systemd
sudo bash -c 'echo "cgroup_manager = \"systemd\"" > /etc/crio/crio.conf.d/00-default.conf'
sudo systemctl daemon-reload
sudo systemctl restart crio


token=$(cat $config_path/token)
control_ip=$(cat $config_path/CONTROL_IP)
sudo keadm join --cloudcore-ipport=$control_ip:10000 --token=$token \
    --cgroupdriver=systemd --remote-runtime-endpoint=unix:///var/run/crio/crio.sock \
    --kubeedge-version=1.15.1


# Install crictl
VERSION="v1.26.0" # check latest version in /releases page
wget https://github.com/kubernetes-sigs/cri-tools/releases/download/$VERSION/crictl-$VERSION-linux-amd64.tar.gz
sudo tar zxvf crictl-$VERSION-linux-amd64.tar.gz -C /usr/local/bin
rm -f crictl-$VERSION-linux-amd64.tar.gz


# update edgecore.yaml, for flannel
cat <<EOF > update_edgecore.sed
/metaServer:/ {
        p;
        n;
        p;
        n;
        /enable/ {
                s/false/true/;
                p;
                d;
        }
}
p;
EOF
sudo sudo sed -i -n -f update_edgecore.sed /etc/kubeedge/config/edgecore.yaml
sudo systemctl restart edgecore # <-- may fail if kube-proxy was already started
sudo ip link delete cni0
