from .pbench import PBench

class PBenchDevice( PBench ):
  """
  This Permutation Benchmark (PBench) uses fio to measure the IO performance of individual OSD devices (drives).
  Unlike other PBench benchmarks, this benchmark sends IO directly to locally-attached devices, not to a Ceph cluster.
  As such, the 'client' hosts configured for this benchmark should actually be the OSD hosts.
  And more importantly, this benchmark should only be run before OSD hosts join the Ceph cluster.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the PBench base class initializer.
    """
    self.driver = 'device-fio'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def run_permutations( self ):
    """
    Iterates over all configured test permutations.
    This method is called by the run() method in the PBench base class.
    """
    with self.device_permutations():
      with self.command_permutations( 'pre-test' ):
        self.test_permutations()
