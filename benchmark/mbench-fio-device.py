from .mbench import MBench

class MBenchFioDevice( MBench ):
  """
  Multidimensional Benchmark (MBench) that uses fio to measure the IO performance of OSD storage devices.
  Unlike other MBench benchmarks, this benchmark sends IO directly to devices, and not to a Ceph cluster.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base MBench initializer.
    """
    self.driver = 'fio-device'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def run_variations( self ):
    """
    Called by the base MBench.run() method.
    """
    with device_variations():
      with command_variations( 'pre-jobs' ):
        run_fio_jobs()
