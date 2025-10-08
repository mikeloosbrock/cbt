from .mbench import MBench

class MBenchFioKrbd( MBench ):
  """
  Multidimensional Benchmark (MBench) that uses fio and krbd to measure the IO performance of mapped (and optionally mounted) RBD images.
  Unlike the MBenchFioLibrbd benchmark, this benchmark sends IO through the Linux filesystem and block layers.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base MBench initializer.
    """
    self.driver = 'fio-krbd'
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
            with command_variations( 'pre-map' ):
              with map_variations():
                with command_variations( 'pre-mkfs' ):
                  with filesystem_variations():
                    with command_variations( 'pre-mount' ):
                      with mount_variations():
                        with command_variations( 'pre-jobs' ):
                          run_fio_jobs()
