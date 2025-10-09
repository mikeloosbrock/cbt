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
    self.driver = 'fio_krbd'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def run_variations( self ):
    """
    Called by the base MBench.run() method.
    """
    with self.osd_variations():
      with self.client_variations():
        with self.pool_variations():
          with self.image_variations():
            with self.command_variations( 'pre-map' ):
              with self.map_variations():
                with self.command_variations( 'pre-mkfs' ):
                  with self.filesystem_variations():
                    with self.command_variations( 'pre-mount' ):
                      with self.mount_variations():
                        with self.command_variations( 'pre-jobs' ):
                          self.run_fio_jobs()
