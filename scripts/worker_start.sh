set -x

exec &> /output.log
KB="gs://kubeedge-config-bucket"

if [ -f /cluster-inited ]; then
    echo "---already inited"
    exit 0
fi


echo $HOME
echo "$HOME $(pwd)" > /pwdddd
#exit 0
# Waiting for kube config file to be available on GCS
until gsutil -q stat $KB/common.sh
do
    sleep 15
done
gsutil cp $KB/*.sh ./

echo "stating common"
sudo bash common.sh

until gsutil -q stat $KB/token
do
    sleep 20
done

config_path="/hrushi2002j/configs"
sudo mkdir -p $config_path
sudo gsutil cp $KB/token $config_path/
sudo gsutil cp $KB/CONTROL_IP $config_path/

sudo bash edge.sh

echo "edge done"
echo "created" > /cluster-inited