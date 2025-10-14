from .pbench import PBench

class PBenchRadosbench( PBench ):
  """
  Permutation Benchmark (PBench) that uses radosbench and librados to measure direct RADOS object IO performance.
  This benchmark and the PBenchFioLibrados benchmark should, in theory, always yield similar performance.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base PBench initializer.
    """
    self.driver = 'radosbench'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def iterate_permutations( self ):
    """
    Called by the base PBench.run() method.
    """
    with self.osd_permutations():
      with self.client_permutations():
        with self.pool_permutations():
          with self.command_permutations( 'pre-test' ):
            self.run_radosbench_tests()
