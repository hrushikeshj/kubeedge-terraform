from time import sleep
from kubernetes import client, config
from kubernetes.stream import stream
# https://github.com/kubernetes/kubectl/blob/b73518af09755bb9607e8755e7fc111ee1adceb5/pkg/describe/describe.go#L1485
from collections import defaultdict
import requests
import os.path
import random
import json
import yaml
import re
import cov

try:
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
except:
    pass    
prev_shed = {}


class ResourceReq:
    def __init__(self, cpu, mem):
        self.cpu = cpu
        self.mem = mem

    def __repr__(self) -> str:
        return f"<{self.cpu}, {self.mem}>"

class Node:
    def __init__(self, id, name, spec_cpu, spec_mem, bitrate, disk_total, disk_free, inuse_cpu=0, inuse_mem=0, data_bytes=0):
        self.id = id
        self.name = name
        self.spec_cpu = spec_cpu
        self.spec_mem = spec_mem
        self.bitrate = bitrate # bitrate to master
        self.disk_total = disk_total
        self.disk_free = disk_free
        self.inuse_cpu = inuse_cpu    
        self.inuse_mem = inuse_mem
        self.data_bytes = data_bytes
        self.pods = None # only fast API bytes
        self.all_pods = None
        self.resourse_req: ResourceReq = None
        self.all_pods = None

    def __repr__(self) -> str:
        return f"Node(Name: <{self.id}:{self.name}>, Spec: <cpu: {self.spec_cpu}({self.cpu_percentage():.2f}%), mem: {self.spec_mem:.2f}({self.mem_percentage():.2f}%), {self.bitrate:.2f}>, db: {self.data_bytes})"
    
    def __repr2__(self) -> str:
        return f"Node(Name: <{self.id}:{self.name}>, Spec: <cpu: {self.spec_cpu}({self.inuse_cpu:.4f}), mem: {self.spec_mem:.2f}({self.inuse_mem:.4f}), {self.bitrate:.2f}>)"
    def get_rem_cpu(self):
        return self.spec_cpu - self.inuse_cpu

    def get_rem_mem(self):
        return self.spec_mem - self.inuse_mem
    
    def mem_percentage(self):
        return 100 * self.inuse_mem/self.spec_mem
    
    def cpu_percentage(self):
        return 100 * self.inuse_cpu/self.spec_cpu
    
    def bytes_per_node(self):
        if len(self.get_pods()) == 0:
            return 0
        return (self.data_bytes / len(self.get_pods()))/1048576 # bytes to mb
    
    def set_pods(self, v1=None):
        if not v1:
            v1 = client.CoreV1Api()
        
        pods = v1.list_namespaced_pod('default',
                                      field_selector=f"spec.nodeName={self.name}",
                                      label_selector="app=fast-api")
        self.pods = pods.items

        # TODO: refactor
        self.all_pods = v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={self.name}").items

    def set_requests(self):
        total_cpu_req_nano, total_mem_req_kbi = 0, 0
        for pod in self.all_pods:
            for cont in pod.spec.containers:
                req = cont.resources.requests
                if req:
                    cpu, mem = cov.to_nano_cpu(req['cpu']), cov.to_kbi_memory(req['memory'])
                    total_cpu_req_nano += cpu
                    total_mem_req_kbi += mem

        self.resourse_req = ResourceReq(total_cpu_req_nano/1000_000_000, total_mem_req_kbi/1024)

    def get_pods(self):
        if self.pods == None:
            self.set_pods()
        
        return self.pods

    def pods_created(self) -> bool:
        return len(self.get_pods()) > 0

class Container:
    def __init__(self, id, name, app_name, req_cpu, req_mem):
        self.id = id
        self.name = name
        self.app_name = app_name
        self.req_cpu = req_cpu
        self.req_mem = req_mem
    
    def __repr__(self) -> str:
        return f"Container(ID: {self.id}, App: {self.app_name}, req: <{self.req_cpu}, {self.req_mem}>)"    

def get_all_simul_nodes(n):
    nodes = []
    possible_cpu = range(1,9)
    possible_mem = [1000, 2000, 4000, 8000, 10000, 12000]
    possible_bitrate = [2, 5, 10, 15, 20, 30, 35]
    possible_disk = [(10000,5000), (15000,5000), (8000,3000), (8000, 2000)]
    for i in range(1,n+1):
        disk = random.choice(possible_disk)
        nodes.append(Node("n"+str(i), "n"+str(i), random.choice(possible_cpu),
                          random.choice(possible_mem), random.choice(possible_bitrate), disk[0], disk[1]))
        
    return nodes

def get_all_simul_containers(n):
    containers = []
    possible_req_cpu = range(1,5)
    possible_req_mem = range(100, 4000, 200)
    possible_apps = ["app1", "app2"]
    for i in range(1,n+1):
        containers.append(Container("c"+str(i), "c"+str(i), random.choice(possible_apps),
                                    random.choice(possible_req_cpu), random.choice(possible_req_mem)))
        
    return containers

def get_nodes(get_disk=True):
    v1 = client.CoreV1Api()
    cust = client.CustomObjectsApi()

    metrics = cust.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes')

    cluster_nodes = defaultdict(dict)
    
    # n = nano cores, Ki = kilobytes
    for stats in metrics['items']:
        node_name = stats['metadata']['name']
        cluster_nodes[node_name]['used_cpu'] = float(stats['usage']['cpu'][:-1]) / 10**9
        cluster_nodes[node_name]['used_memory'] = float(stats['usage']['memory'][:-2]) / 10**3

    control_plane_name = ''  
    for node in v1.list_node().items:
        node_name = node.status.addresses[1].address
        cluster_nodes[node_name]['spec_cpu'] = float(node.status.allocatable['cpu'])
        cluster_nodes[node_name]['spec_memory'] = float(node.status.allocatable['memory'][:-2]) / 10**3
        if node.metadata.labels.get('layer') == 'fog':
            control_plane_name = node.status.addresses[1].address
              
    if os.path.exists('network_iperf_test.json'):
        with open('network_iperf_test.json', 'r') as testfile:
            net_bitrate = json.load(testfile)
    else:
        net_bitrate = get_network_bitrate()
        
    for node in net_bitrate:
        cluster_nodes[node['node']]['bitrate'] = node['bitrate']
        
    if get_disk:
        disk_vals = get_disk_volume()
        for node in disk_vals:
            cluster_nodes[node['node']]['disk_total'] = node['disk_total']
            cluster_nodes[node['node']]['disk_free'] = node['disk_free']
    
    cluster_nodes.pop(control_plane_name)    
    nodes = []
    for id, (name, info) in enumerate(cluster_nodes.items(), 1):
        node = Node('n'+str(id), name, info['spec_cpu'], info['spec_memory'],
                    info.get('bitrate', 0), info.get('disk_total', 0), info.get('disk_free', 0),
                    info['used_cpu'], info['used_memory'])
        nodes.append(node)
    
    return nodes

def get_pending_containers():
    v1 = client.CoreV1Api()
    containers = []
    
    # cpu in mili, memory in Mi
    for id, pod in enumerate(v1.list_pod_for_all_namespaces().items, 1):
        if pod.status.phase == 'Pending' and pod.spec.scheduler_name == 'hybrid-scheduler':
            pod_name = pod.metadata.name
            app_name = pod.metadata.labels['app']
            req_cpu = float(pod.spec.containers[0].resources.requests['cpu'][:-1]) / 1000
            req_memory = float(pod.spec.containers[0].resources.requests['memory'][:-2])
            containers.append(Container('c'+str(id), pod_name, app_name, req_cpu, req_memory))
        
    return containers

def get_disk_volume():
    # use only in topsis. not nsga.
    
    v1 = client.CoreV1Api()

    pat_disk_total = re.compile(r'\nnode_filesystem_size_bytes.*mountpoint="/"} (.*)')   
    pat_disk_free = re.compile(r'\nnode_filesystem_avail_bytes.*mountpoint="/"} (.*)')
    
    nodes = []
    for pod in v1.list_namespaced_pod('monitoring').items:
        nodes.append({'node':pod.spec.node_name,'ip':pod.status.pod_ip, 'disk_free':0, 'disk_total':0})
    
    try:    
        for node in nodes:
            metrics = requests.get(f"http://{node['ip']}:9100/metrics").text

            node['disk_total'] = int(float(re.search(pat_disk_total, metrics).group(1))/10**9)
            node['disk_free'] = int(float(re.search(pat_disk_free, metrics).group(1))/10**9)
    except:
        print('could not read disk values. returned zero.')
        
    return nodes


def get_my_nodes(get_disk=True, label=None):
    v1 = client.CoreV1Api()
    cust = client.CustomObjectsApi()

    metrics = cust.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes')

    cluster_nodes = defaultdict(dict)
    
    # n = nano cores, Ki = kilobytes
    for stats in metrics['items']:
        node_name = stats['metadata']['name']
        cluster_nodes[node_name]['used_cpu'] = float(stats['usage']['cpu'][:-1]) / 10**9
        cluster_nodes[node_name]['used_memory'] = float(stats['usage']['memory'][:-2]) / 10**3

    for node in v1.list_node().items:
        node_name = node.status.addresses[1].address
        cluster_nodes[node_name]['spec_cpu'] = float(node.status.allocatable['cpu'])
        cluster_nodes[node_name]['spec_memory'] = float(node.status.allocatable['memory'][:-2]) / 10**3
        #if node.metadata.labels.get('layer') == 'fog':
        cluster_nodes[node_name]['labels'] = node.metadata.labels
              
    if get_disk:
        disk_vals = get_disk_volume()
        for node in disk_vals:
            cluster_nodes[node['node']]['disk_total'] = node['disk_total']
            cluster_nodes[node['node']]['disk_free'] = node['disk_free']
    
    params = {'query': """sum(rate(container_network_receive_bytes_total{container_label_io_kubernetes_container_name=~".*", container_label_app="fast-api"}[30s])) by (node)"""}
    r = requests.get("http://terraform-monitoring-4:9090/api/v1/query", params=params)
    if r.status_code == 200:
        data =  r.json()['data']['result']
        for node_data in data:
            cluster_nodes[node_data['metric']['node']]['data_bytes'] = node_data['value'][0]
    else:
        print("failed to fetch data from promethes")

    nodes = []
    for id, (name, info) in enumerate(cluster_nodes.items(), 1):
        if label != None and label not in info['labels']:
            continue
        node = Node('n'+str(id), name, info['spec_cpu'], info['spec_memory'],
                    info.get('bitrate', 0), info.get('disk_total', 0), info.get('disk_free', 0),
                    info['used_cpu'], info['used_memory'], data_bytes=info.get('data_bytes', 0))
        nodes.append(node)

        # set pods and retquests
    for node in nodes:
        node.set_pods()
        node.set_requests()

    return nodes

v1 = client.CoreV1Api()
import datetime

def schedule(name, node, scheduler_type, namespace='default'):
    target = client.V1ObjectReference(kind = 'Node', api_version = 'v1', name = node)
    meta = client.V1ObjectMeta(name = name)
    body = client.V1Binding(api_version=None, kind=None, target=target, metadata=meta)

    event_involved_object = client.V1ObjectReference(kind='Pod', api_version='v1', name=name, namespace=namespace)
    event_timestamp = datetime.datetime.now(datetime.timezone.utc)
    event_meta = client.V1ObjectMeta(name=name, creation_timestamp=event_timestamp)
    event_source = client.V1EventSource(component='hybrid-scheduler')
    event_message = f"Successfully assigned default/{name} to {node} by {scheduler_type}"
    print(event_message)
    event = client.CoreV1Event(message=event_message,metadata=event_meta, involved_object=event_involved_object,
                               first_timestamp=event_timestamp, reason='Scheduled', source=event_source, type='Normal')
    v1.create_namespaced_event('default', event)

    prev_shed[name] = 1
    label_pod(name, node)
    return v1.create_namespaced_pod_binding(name, namespace=namespace, body=body, _preload_content=False)

print(get_my_nodes(True, 'node-role.kubernetes.io/edge'))


def label_pod(pod_name, node_name):
    v1 = client.CoreV1Api()
    body = {
        'metadata': {
            'labels': {
                'node': node_name
            }
        }
    }
    v1.patch_namespaced_pod(pod_name, 'default', body)

# return false if all nodes have a pod
# and the podd was not scheduled
def one_per_node(nodes, pod_name) -> bool:
    for node in nodes:
        if not node.pods_created():
            schedule(pod_name, node.name, "hrushi")
            print("## one_per_node: scheduled")
            return True
    return False

import electra3
def main(algo="", nodes=None):
    if not nodes:
        nodes = get_my_nodes(True, 'node-role.kubernetes.io/edge')
    pending_cont: Container = get_pending_containers()
    pending_cont = [c for c in pending_cont if c.name not in prev_shed]
    #electra3.schd(nodes)
    #print(nodes)
    if pending_cont:
        cont = pending_cont[0]
        if one_per_node(nodes, cont.name):
            print("* one-per-node done")
            print()
            return

        if algo == "vikor":
            best_node = vikor_schd(nodes)
            schedule(cont.name, best_node.name, "vikor")
            best_node.resourse_req.cpu += 0.2 # 200m
            best_node.resourse_req.mem += 300
            print()
            main(algo, nodes)
            return
        elif algo == "vikor_connection_based":
            best_node = vikor_schd_conn(nodes)
            schedule(cont.name, best_node.name, "vikor_connection_based")
            best_node.resourse_req.cpu += 0.2 # 200m
            best_node.resourse_req.mem += 300
            print()
            main(algo, nodes)
            return
        elif algo == "electra":
            best_node = electra3.schd(nodes)
            schedule(cont.name, best_node.name, "electra")
            best_node.resourse_req.cpu += 0.2 # 200m
            best_node.resourse_req.mem += 300
            print()
            main(algo, nodes)
            return
        else:
            raise Exception("invalid algo")
            
        print(f"container: {cont.name}")
        best_node: Node = max(nodes, key=lambda n: n.get_rem_cpu())
        print(f"best: {best_node.name}, {best_node.cpu_percentage()}")
        schedule(cont.name, best_node.name, "hrushi")
    else:
        print("* no pending containers")

    scheduler_name = "hybrid-scheduler"
    #print(get_pending_containers())
    print()

import numpy as np
from crispyn.mcda_methods import VIKOR
from crispyn import weighting_methods as mcda_weights
from crispyn import normalizations as norms
from crispyn.additions import rank_preferences

def print_to_file(matrix, rank, a):
    with open("./log", "a") as f:
        for r in matrix:
            f.write("\t".join([str(f) for f in r]))
            f.write("\n")
        f.write("-".join([str(f) for f in rank]))
        f.write(f"\n{a}")
        f.write("\n\n")


"""
- total-cpu
- remaining-cpu < +
- commited-cpu  < -
- remaining-mem < +
- commited-mem  < -
- connections   < +
"""
def vikor_schd(nodes):
    matrix = [[node.get_rem_cpu(), node.resourse_req.cpu, node.get_rem_mem(), node.resourse_req.mem]
                for node in nodes]
    matrix = np.array(matrix)

    types = np.array([1, -1, 1, -1])
    weights = mcda_weights.entropy_weighting(matrix)

    # Create the VIKOR method object
    vikor = VIKOR(normalization_method=norms.minmax_normalization)
    # Calculate alternatives preference function values with VIKOR method
    pref = vikor(matrix, weights, types
    # Rank alternatives according to preference values
    rank = rank_preferences(pref, reverse = False)

    idx = np.argmin(rank)
    print_to_file(matrix, rank, idx)

    print("rank: ", nodes[np.argmin(idx)])

    return nodes[idx]

def vikor_schd_conn(nodes):
    matrix = [[node.get_rem_cpu(), node.resourse_req.cpu, node.get_rem_mem(), node.resourse_req.mem, node.bytes_per_node()]
                for node in nodes]
    matrix = np.array(matrix)
    print(matrix)

    types = np.array([1, -1, 1, -1, 1])
    weights = mcda_weights.entropy_weighting(matrix)

    # Create the VIKOR method object
    vikor = VIKOR(normalization_method=norms.minmax_normalization)
    # Calculate alternatives preference function values with VIKOR method
    pref = vikor(matrix, weights, types)
    # Rank alternatives according to preference values
    rank = rank_preferences(pref, reverse = False)

    idx = np.argmin(rank)
    print_to_file(matrix, rank, idx)

    print("rank: ", nodes[np.argmin(idx)])

    return nodes[idx]

if __name__ == '__main__':
    while True:
        main("electra")
        sleep(2)
