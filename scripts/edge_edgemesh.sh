set -euxo pipefail
exec &> /edge_edgemesh.log

config_path="/home/hrushi2002j/configs"
control_ip=$(cat $config_path/CONTROL_IP)

cat <<EOF > update_cluster_dns.txt
      clusterDNS:
      - 169.254.96.16
EOF

sudo sed -i -n '/edgeStream/{p;n;s/false/true/};p' /etc/kubeedge/config/edgecore.yaml
sudo sed -i '/clusterDomain: cluster.local/r update_cluster_dns.txt' /etc/kubeedge/config/edgecore.yaml
sudo systemctl restart edgecore.service

# update worker pods subnet
sudo sed -i "s/10\.85\.0/10\.86\.0/" /etc/cni/net.d/100-crio-bridge.conflist
sudo systemctl restart crio

echo "edge_edgemesh done"
