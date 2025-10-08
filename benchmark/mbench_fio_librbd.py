from .mbench import MBench

class MBenchFioLibrbd( MBench ):
  """
  Multidimensional Benchmark (MBench) that uses fio and librbd to measure the IO performance of unmapped RBD images.
  Unlike the MBenchFioKrbd benchmark, this benchmark does not send IO through the Linux filesystem and block layers.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base MBench initializer.
    """
    self.driver = 'fio_librbd'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def run_variations( self ):
    """
    Called by the base MBench.run() method.
    """
    with osd_variations():
      with client_variations():
        with pool_variations():
          with image_variations():
            with command_variations( 'pre-jobs' ):
              run_fio_jobs()
