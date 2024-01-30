#!/bin/bash
#
set -euxo pipefail
exec &> /prometheus.log
KB="gs://kubeedge-config-bucket"

sudo apt-get install -y apt-transport-https software-properties-common wget
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
# Updates the list of available packages
sudo apt-get -y update
# Installs the latest OSS release:
sudo apt-get -y install grafana

sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl status grafana-server

# auto start
sudo systemctl enable grafana-server.service

# prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.49.1/prometheus-2.49.1.linux-amd64.tar.gz
tar xvfz prometheus-2.49.1.linux-amd64.tar.gz
rm prometheus-2.49.1.linux-amd64.tar.gz

mv prometheus-2.49.1.linux-amd64 prometheus
cd prometheus
rm *.yml

gsutil cp $KB/monitoring/prometheus.yaml ./
gsutil cp $KB/monitoring/prometheus.service ./
sudo ln prometheus.service /etc/systemd/system/prometheus.service

# enable systemd
sudo systemctl start prometheus.service
systemctl enable prometheus.service
#./prometheus
