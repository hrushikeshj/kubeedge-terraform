import requests
import re

kube_end_point = "http://127.0.0.1:10550"

def to_nano_cpu(cpu):
    # https://github.com/kubernetes/apimachinery/blob/master/pkg/api/resource/suffix.go#L121
    if cpu == "0" or cpu == "":
        return 0

    # have to take of case when > G
    suffix_val = {
        'n': 1_000_000_000,
        'u': 1_000_000,
        'm': 1_000
    }

    for suffix, scale in suffix_val.items():
        if re.match(f".*{suffix}", cpu):
            cpu_in_actual = float(cpu.replace(suffix, '')) / scale
            cpu_in_nano = cpu_in_actual * 1_000_000_000

            return int(cpu_in_nano)

    return int(cpu)

def to_kbi_memory(memory):
    if re.match(".*Ki", memory):
        return int(memory.replace("Ki", ''))
    
    if re.match(".*Mi", memory):
        return int(memory.replace("Mi", '')) * 1024

    return int(memory)


def node_name(pod):
    if 'nodeName' in pod['spec']:
        return pod['spec']['nodeName']

    else:
        return "-err-"

def pod_name(pod):
    return pod['metadata']['name']

def get_metrics(metric):
    total_cpu, total_memory = 0, 0
    for container in metric['containers']:
        cpu = container['usage']['cpu']
        memory = container['usage']['memory']

        total_cpu += to_nano_cpu(cpu)
        total_memory += to_kbi_memory(memory)

    return total_cpu / 1000_000, total_memory / 1024

def node_labels(pod):
    if 'node' in pod['metadata']['labels']:
        return f"node={pod['metadata']['labels']['node']}"
    
    return '-'

def map_metrics(metrics):
    res = {}
    for metric in metrics:
        cpu, memory = get_metrics(metric)
        res[metric['metadata']['name']] = {
            'cpu': cpu,
            'memory': memory
        }
    
    return res


if __name__ == '__main__':
    pods_req = requests.get(kube_end_point + "/api/v1/namespaces/default/pods?limit=400")
    pods = pods_req.json()
    #print(pods)
    #top_pods.nodes['items'][0]['spec']['nodeName']

    metrics_req = requests.get(kube_end_point + "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods")
    mapped_metrics = map_metrics(metrics_req.json()['items'])

    print("-Name ", "\t", "Node", "\t", "CPU", "\t", "Memory")
    for pod in pods['items']:
        cpu, mem = "-", "-"
        if pod_name(pod) in mapped_metrics:
            cpu, mem = mapped_metrics[pod_name(pod)]['cpu'], mapped_metrics[pod_name(pod)]['memory']
            cpu = round(cpu, 2)
            mem = round(mem, 2)

        print(pod_name(pod), "\t", node_name(pod), "\t", f"{cpu}m", "\t", f"{mem}Mi", "\t", node_labels(pod))
