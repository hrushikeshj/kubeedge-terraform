set -x

exec &> /output.log
KB="gs://kubeedge-config-bucket"

echo $HOME

if [ -f /cluster-inited ]; then
    echo "---already inited"
    exit 0
fi

#exit 0
# Waiting for kube config file to be available on GCS
until gsutil -q stat $KB/common.sh
do
    sleep 15
done
gsutil cp $KB/*.sh ./

echo "stating common"
sudo bash common.sh
sudo bash master.sh
echo "master done"

gsutil cp 'gs://kubeedge-config-bucket/*.yaml' ./

echo "created" > /cluster-inited

sleep 30
echo "stating master_edgemesh.sh"
sudo bash master_edgemesh.sh
