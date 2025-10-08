class MBenchDataAnalyzer( DataAnalyzer ):
  """
  Base data analayzer for Multidimensional Benchmarks (MBench).
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, run, host, proc ):
    """
    MBenchDataAnalyzer initializer.
    """
    super().__init__( archive_dir, run, host, proc )

#==============================================================================#
#==============================================================================#

class MBenchRadosbenchDataAnalyzer( MBenchDataAnalyzer ):
  """
  Data analyzer for MBench benchmarks that use the radosbench driver.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, run, host, proc ):
    """
    Extends the base MBenchDataAnalyzer initializer.
    """
    super().__init__( archive_dir, run, host, proc )

#==============================================================================#
#==============================================================================#

class MBenchFioDataAnalyzer( MBenchDataAnalyzer ):
  """
  Data analyzer for MBench benchmarks that use fio-* drivers.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, run, host, proc ):
    """
    Extends the base MBenchDataAnalyzer initializer.
    """
    super().__init__( archive_dir, run, host, proc )
