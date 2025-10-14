from .pbench import PBench

class PBenchFioLibrbd( PBench ):
  """
  Permutation Benchmark (PBench) that uses fio and librbd to measure the IO performance of unmapped RBD images.
  Unlike the PBenchFioKrbd benchmark, this benchmark does not send IO through the Linux filesystem and block layers.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base PBench initializer.
    """
    self.driver = 'fio_librbd'
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
            with self.command_permutations( 'pre-test' ):
              self.run_fio_tests()
