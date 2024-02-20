#! /bin/bash

set -euxo pipefail
exec &> /cadvisor.log

KB="gs://kubeedge-config-bucket"
sudo gsutil cp $KB/monitoring/cadvisor.yaml /home/hrushi2002j/

sudo -i -u hrushi2002j bash << EOF
cd /home/hrushi2002j/
sudo chown "$(id -u)":"$(id -g)" ./cadvisor.yaml
kubectl apply -f cadvisor.yaml
sudo echo "cadvisor done" /cadvisor-status
EOF

echo "cadvisor done"

sudo -i -u hrushi2002j bash << EOF
cd /home/hrushi2002j/
git clone -b kubeedge https://github.com/hrushikeshj/kube-state-metrics.git
cd kube-state-metrics
kubectl apply -f examples/standard
EOF
