from .pbench import PBench

class PBenchFioLibrados( PBench ):
  """
  Permutation Benchmark (PBench) that uses fio and librados to measure direct RADOS object IO performance.
  This benchmark and the PBenchRadosbench benchmark should, in theory, always yield similar performance. 
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base PBench initializer.
    """
    self.driver = 'fio-librados'
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
            self.run_fio_tests()
