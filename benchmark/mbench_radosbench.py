from .mbench import MBench

class MBenchRadosbench( MBench ):
  """
  Multidimensional Benchmark (MBench) that uses radosbench and librados to measure direct RADOS object IO performance.
  This benchmark and the MBenchFioLibrados benchmark are similar in function, and should therefore yield similar performance.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base MBench initializer.
    """
    self.driver = 'radosbench'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def run_variations( self ):
    """
    Called by the base MBench.run() method.
    """
    with osd_variations():
      with client_variations():
        with pool_variations():
          with command_variations( 'pre-jobs' ):
            run_radosbench_jobs()
