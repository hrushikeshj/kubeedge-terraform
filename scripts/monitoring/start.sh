#!/bin/bash
#
#

set -euxo pipefail
exec &> /output.log

KB="gs://kubeedge-config-bucket"

until gsutil -q stat $KB/monitoring/prometheus.sh
do
    sleep 15
done
mkdir monitoring  && cd monitoring
gsutil cp $KB/monitoring/* ./

echo "running prometheus.sh"
sudo bash prometheus.sh
