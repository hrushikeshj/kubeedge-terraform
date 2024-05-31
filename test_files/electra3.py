from EasyMCDM.models.Electre import Electre
from crispyn import weighting_methods as mcda_weights
import numpy as np

"""
- total-cpu
- remaining-cpu < +
- commited-cpu  < -
- remaining-mem < +
- commited-mem  < -
- connections   < +
"""

def print_to_file(matrix, rank, a):
    with open("./log", "a") as f:
        for r in matrix:
            f.write("\t".join([str(f) for f in r]))
            f.write("\n")
        f.write(str(rank))
        f.write(f"\n{a}")
        f.write(" algo: electra\n\n")

def schd(nodes):
    matrix = [[node.get_rem_cpu(), node.resourse_req.cpu, node.get_rem_mem(), node.resourse_req.mem]
                for node in nodes]

    data = { str(ii): d for ii, d in enumerate(matrix)}
    matrix = np.array(matrix)

    types = np.array([1, -1, 1, -1])
    prefs = ["max", "min", "max", "min"]
    weights = mcda_weights.entropy_weighting(matrix)
    min_round = min([len(str(wx)) for wx in weights])
    weights = [round(wx, min_round) for wx in weights]
    vetoes = [1000000]*4
    indifference_threshold = 0.6
    preference_thresholds = None

    # Create the VIKOR method object
    
    e = Electre(data=data, verbose=False)

    results = e.solve(weights, prefs, vetoes, indifference_threshold, preference_thresholds)
    
    if len(results["kernels"]) == 0:
        idx = 0
        idx_w = "warn"
    else:
        idx = int(results["kernels"][0])
        idx_w = idx
    print_to_file(matrix, results, idx_w)
    print("electra rank: ", results)

    return nodes[idx]
