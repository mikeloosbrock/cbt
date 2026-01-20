import copy
import itertools

import settings
from benchmark.radosbench import Radosbench
from benchmark.fio import Fio
from benchmark.hsbench import Hsbench
from benchmark.rbdfio import RbdFio
from benchmark.rawfio import RawFio
from benchmark.kvmrbdfio import KvmRbdFio
from benchmark.librbdfio import LibrbdFio
from benchmark.nullbench import Nullbench
from benchmark.cosbench import Cosbench
from benchmark.cephtestrados import CephTestRados
from benchmark.getput import Getput
from benchmark.pbench_device    import PBenchDevice
from benchmark.pbench_rados     import PBenchRados
from benchmark.pbench_rbd       import PBenchRbd
from benchmark.pbench_krbd_raw  import PBenchKrbdRaw
from benchmark.pbench_krbd_file import PBenchKrbdFile

def get_all(archive, cluster, iteration):
    for benchmark, config in sorted(settings.benchmarks.items()):
        default = {"benchmark": benchmark,
                   "iteration": iteration}
        for current in all_configs(config):
            current.update(default)
            yield get_object(archive, cluster, benchmark, current)


def all_configs(config):
    """
    return all parameter combinations for config
    config: dict - list of params
    iterate over all top-level lists in config
    """
    cycle_over_lists = []
    cycle_over_names = []
    default = {}

    for param, value in list(config.items()):
        # acceptable applies to benchmark as a whole, no need to it to
        # the set for permutation
        if param == 'acceptable':
            default[param] = value
        elif isinstance(value, list):
            cycle_over_lists.append(value)
            cycle_over_names.append(param)
        else:
            default[param] = value

    for permutation in itertools.product(*cycle_over_lists):
        current = copy.deepcopy(default)
        current.update(list(zip(cycle_over_names, permutation)))
        yield current

def get_object(archive, cluster, benchmark, bconfig):
    benchmarks = {
        'nullbench': Nullbench,
        'radosbench': Radosbench,
        'fio': Fio,
        'hsbench': Hsbench,
        'rbdfio': RbdFio,
        'kvmrbdfio': KvmRbdFio,
        'rawfio': RawFio,
        'librbdfio': LibrbdFio,
        'cosbench': Cosbench,
        'cephtestrados': CephTestRados,
        'getput': Getput,
        'pbench_device':    PBenchDevice,
        'pbench_rados':     PBenchRados,
        'pbench_rbd':       PBenchRbd,
        'pbench_krbd_raw':  PBenchKrbdRaw,
        'pbench_krbd_file': PBenchKrbdFile,
        }
    try:
        return benchmarks[benchmark](archive, cluster, bconfig)
    except KeyError:
        return None
