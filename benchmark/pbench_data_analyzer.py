class PBenchDataAnalyzer( DataAnalyzer ):
  """
  Base data analayzer for Permutation Benchmarks (PBench).
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, run, host, proc ):
    """
    PBenchDataAnalyzer initializer.
    """
    super().__init__( archive_dir, run, host, proc )

#==============================================================================#
#==============================================================================#

class PBenchRadosbenchDataAnalyzer( PBenchDataAnalyzer ):
  """
  Data analyzer for PBench benchmarks that use the radosbench driver.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, run, host, proc ):
    """
    Extends the base PBenchDataAnalyzer initializer.
    """
    super().__init__( archive_dir, run, host, proc )

#==============================================================================#
#==============================================================================#

class PBenchFioDataAnalyzer( PBenchDataAnalyzer ):
  """
  Data analyzer for PBench benchmarks that use fio-* drivers.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, run, host, proc ):
    """
    Extends the base PBenchDataAnalyzer initializer.
    """
    super().__init__( archive_dir, run, host, proc )
