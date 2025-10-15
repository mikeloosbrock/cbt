from .pbench import PBench

class PBenchFioKrbd( PBench ):
  """
  Permutation Benchmark (PBench) that uses fio and krbd to measure the IO performance of mapped (and optionally mounted) RBD images.
  Unlike the PBenchFioLibrbd benchmark, this benchmark sends IO through the Linux filesystem and block layers.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base PBench initializer.
    """
    self.driver = 'fio-krbd'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def iterate_permutations( self ):
    """
    Called by the base PBench.run() method.
    """
    with self.osd_permutations():
      with self.client_permutations():
        with self.pool_permutations():
          with self.image_permutations():
            with self.command_permutations( 'pre-map' ):
              with self.map_permutations():
                with self.command_permutations( 'pre-fs' ):
                  with self.filesystem_permutations():
                    with self.command_permutations( 'pre-mount' ):
                      with self.mount_permutations():
                        with self.command_permutations( 'pre-test' ):
                          self.run_fio_tests()
