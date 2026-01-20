from .pbench import PBench

class PBenchRados( PBench ):
  """
  This Permutation Benchmark (PBench) measures the performance of native RADOS object IO.
  It uses the supported test tools (see below) to generate IO against a Ceph pool.

  Supported Test Tools:
  - fio: The 'rados' engine is forced and cannot be configured.
  - radosbench
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the PBench base class initializer.
    """
    self.driver = 'rados'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def run_permutations( self ):
    """
    Iterates over all configured test permutations.
    This method is called by the run() method in the PBench base class.
    """
    with self.osd_permutations():
      with self.client_permutations():
        with self.pool_permutations():
          with self.command_permutations( 'pre-test' ):
            self.test_permutations()
