from .mbench import MBench

class MBenchFioLibrados( MBench ):
  """
  Multidimensional Benchmark (MBench) that uses fio and librados to measure direct RADOS object IO performance.
  This benchmark and the MBenchRadosbench benchmark are similar in function, and should therefore yield similar performance.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base MBench initializer.
    """
    self.driver = 'fio_librados'
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
            run_fio_jobs()
