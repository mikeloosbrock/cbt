from .pbench import PBench

class PBenchRbd( PBench ):
  """
  This Permutation Benchmark (PBench) measures the IO performance of unmapped (and therefore unformatted and unmounted) RBD images.
  It uses the supported test tools (see below) to generate IO against raw block offsets in the RBD images.
  Since krbd is not used, and raw block IO is used, the IO does not pass through the Linux block or filesystem layers.

  Compared to PBenchKrbdRaw:
  - Both use raw block IO to benchmark RBD images.
  - But PBenchKrbdRaw uses krbd and maps the RBD images, so its IO passes through the Linux block layer.

  Compared to PBenchKrbdFile:
  - Both benchmark RBD images.
  - But PBenchKrbdFile uses krbd, maps/formats/mounts the RBD images, and uses file IO instead of raw block IO.
  - As such, PBenchKrbdFile IO passes through both the Linux block and filesystem layers.

  Supported Test Tools:
  - fio: The 'rbd' engine is forced and cannot be configured.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the PBench base class initializer.
    """
    self.driver = 'rbd'
    super().__init__( archive_dir, cluster, config )

  #----------------------------------------------------------------------------#

  def run_permutations( self ):
    """
    Iterates over all configured test permutations.
    This method is called by the run() method in the PBench base class.
    """
    with self.osd_permutations():
      with self.client_permutations():
        with self.pool_permutations():
          with self.image_permutations():
            with self.command_permutations( 'pre-test' ):
              self.test_permutations()
