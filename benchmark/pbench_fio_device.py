from .pbench import PBench

class PBenchFioDevice( PBench ):
  """
  Permutation Benchmark (PBench) that uses fio to measure the IO performance of OSD storage devices.
  Unlike other PBench benchmarks, this benchmark sends IO directly to devices, and not to a Ceph cluster.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base PBench initializer.
    """
    self.driver = 'fio-device'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def iterate_permutations( self ):
    """
    Called by the base PBench.run() method.
    """
    with self.device_permutations():
      with self.command_permutations( 'pre-test' ):
        self.run_fio_tests()
