from .pbench import PBench

class PBenchKrbdFile( PBench ):
  """
  This Permutation Benchmark (PBench) measures the IO performance of mapped, formatted and mounted RBD images.
  It uses the supported test tools (see below) to generate IO against files on filesystems on the RBD images.
  Since both krbd and file IO are used, the IO passes through both the Linux block and filesystem layers.

  Compared to PBenchKrbdRaw:
  - Both use krbd to benchmark mapped RBD images, so both pass IO through the Linux block layer.
  - But PBenchKrbdRaw does not format or mount the RBD images, and uses raw block IO instead of file IO.
  - As such, PBenchKrbdRaw IO does not pass through the Linux filesystem layer.

  Compared to PBenchRbd:
  - Both benchmark RBD images.
  - But PBenchRbd does not use krbd, does not map/format/mount the RBD images, and uses raw block IO instead of file IO.
  - As such, PBenchRbd IO does not pass through the Linux block or filesystem layers.

  Supported Test Tools:
  - fio: Uses the 'libaio' engine by default.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the PBench base class initializer.
    """
    self.driver = 'krbd-file'
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
                with self.command_permutations( 'pre-mkfs' ):
                  with self.mkfs_permutations():
                    with self.command_permutations( 'pre-mount' ):
                      with self.mount_permutations():
                        with self.command_permutations( 'pre-test' ):
                          self.test_permutations()
