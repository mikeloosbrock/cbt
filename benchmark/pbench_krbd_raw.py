from .pbench import PBench

class PBenchKrbdRaw( PBench ):
  """
  This Permutation Benchmark (PBench) measures the IO performance of mapped, but unformatted/unmounted RBD images.
  It uses the supported test tools (see below) to generate IO against raw block offsets in the RBD images.
  Since both krbd and raw block IO are used, the IO passes through the Linux block layer, but not the filesystem layer.

  Compared to PBenchKrbdFile:
  - Both use krbd to benchmark mapped RBD images, so both pass IO through the Linux block layer.
  - But PBenchKrbdFile formats and mounts the RBD images, and uses file IO instead of raw block IO.
  - As such, PBenchKrbdFile IO also passes through the Linux filesystem layer.

  Compared to PBenchRbd:
  - Both use raw block IO to benchmark RBD images.
  - But PBenchRbd does not use krbd or map the RBD images, so its IO does not pass through the Linux block layer.

  Supported Test Tools:
  - fio: Uses the 'libaio' engine by default.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the PBench base class initializer.
    """
    self.driver = 'krbd-raw'
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
            with self.command_permutations( 'pre-map' ):
              with self.map_permutations():
                with self.command_permutations( 'pre-test' ):
                  self.test_permutations()
