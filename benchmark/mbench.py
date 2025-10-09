import common
import settings
import monitoring
import os
import time
import logging
import copy
import yaml
from contextlib import contextmanager

from .benchmark import Benchmark

logger = logging.getLogger( "cbt" )

#==============================================================================#
#==============================================================================#

class MBenchDimensions:
  """
  TODO
  """

  #----------------------------------------------------------------------------#

  def __init__( self ):
    """
    TODO
    """
    self.reset()

  #----------------------------------------------------------------------------#

  def reset( self ):
    """
    (Re)intializes the dimension stack, removing any existing dimensions.
    """
    self.stack      = []
    self.dimensions = {}

  #----------------------------------------------------------------------------#

  def push( self, name, value, state={} ):
    """
    Adds a new dimension on the stack.
    """
    self.stack.append({
      'name'  : name,
      'value' : value,
      'state' : {}.update( state ), # purposely *not* a deep copy
    })
    self.dimensions[name] = self.stack[-1]

  #----------------------------------------------------------------------------#

  def pop( self ):
    """
    Removes the last dimension on the stack.
    """
    if self.stack.count() == 0:
      return None
    dimension = self.stack.pop()
    self.dimensions.pop( dimension['name'] )
    return dimension

  #----------------------------------------------------------------------------#

  def tail( self ):
    """
    Returns the last dimension on the stack.
    """
    return self.stack[-1]

  #----------------------------------------------------------------------------#

  def __getitem__( self, dimension ):
    """
    Returns the dimension specified by either an integer stack index or a string dimension name.
    """
    if type( dimension ) == int and dimension >= 0 and dimension < self.stack.count():
      return self.stack[dimension]

    elif dimension in self.dimensions:
      return self.dimensions[dimension]
      
    return None

  #----------------------------------------------------------------------------#

  def path( self, dimension=None, s1="/", s2="=" ):
    """
    Returns .
    """
    stack = self.stack

    if dimension != None:
      stack = []
      for d in self.stack:
        stack.append( d )
        if d['name'] == dimension:
          break

    return s1.join( [ f"{d['name']}{s2}{d['value']}" for d in stack ] )

#==============================================================================#
#==============================================================================#

class MBench( Benchmark ):
  """
  Multidimensional Benchmark.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base Benchmark initializer.
    """
    super().__init__( archive_dir, cluster, config )
    self.load_cfg( config )
    self.dimensions = MBenchDimensions()
    self.out_dir = self.archive_dir

  #----------------------------------------------------------------------------#

  def initialize(self):
    super().initialize()

    logger.info('Pausing for 60s for idle monitoring.')
    with monitoring.monitor("%s/idle_monitoring" % self.run_dir):
      # time.sleep(60)
      pass

    common.sync_files('%s/*' % self.run_dir, self.out_dir)

  #----------------------------------------------------------------------------#

  def exists( self ):
    """
    TODO
    """
    if os.path.exists( self.out_dir ):
      logger.info( f'Skipping existing test in {self.out_dir}.' )
      return True
    return False

  #----------------------------------------------------------------------------#

  def log( self, message ):
    """
    TODO
    """
    logger.info( message )

  #----------------------------------------------------------------------------#

  def default_cfg( self ):
    """
    Returns a copy of the default cfg that is overridden/extended by the user cfg in self.load_cfg().
    """
    return yaml.safe_load('''

      osd:                         # controls ...
        configurations:            # named osd configurations
          default:                 # configuration name
            sysctl-settings: {}    #
            sysfs-settings: {}     #
            tell-commands:         #
              head: []             #
              tail: []             #
            shell-commands:        #
              head: []             #
              tail: []             #

      client:                      # controls ...
        user-id: cbt               #
        user-key:                  #
        configurations:            # named client configurations
          default:                 # configuration name
            hosts: '*'             # client host list, must contain one or more dns-resolvable hostnames or '*' to use all clients defined in the cluster cfg
            sysctl-settings: {}    #
            sysfs-settings: {}     #
            tell-commands:         #
              head: []             #
              tail: []             #
            shell-commands:        #
              head: []             #
              tail: []             #

      pool:                        # controls how benchmark pools are created
        monitor: false             # enable/disable performance monitoring of pool creation/removal
        name: cbt                  # pool name, probably no reason to ever change this
        profiles:                  # ?
          - replica-2

      image:                       # controls how per-client RBD images are created - only used by MBench drivers that use RBD
        monitor: true              # enable/disable performance monitoring of RBD image creation/removal
        name-prefix: ''            # this string is always appended with "`hostname -s`-" to ensure pool-global unique RBD image names
        per-client-counts: [ 1 ]   # must contain one or more integer values, each being a number of RBD images to create per client
        options:                   # named option strings, each being passed as-is to the 'rbd create' cli command
          default: --size 1TB

      pre-map:                     # shell commands to run on clients before mapping RBD images - only used by MBench drivers that use RBD
        monitor: false             # enable/disable performance monitoring of the commands
        commands:                  # named groups of commands
          default:                 # group name
            head: []               # group commands to run before mapping RBD images
            tail: []               # group commands to undo or clean up the head commands, after unmapping RBD images

      map:                         # controls how RBD images are mapped on clients - only used by MBench drivers that use RBD
        monitor: false             # enable/disable performance monitoring of RBD image mapping/unmapping
        options:                   # named option strings, each being single-quoted and passed as the value of the --options option of the 'rbd device map' cli command
          default: ''              # => no extra options

      pre-mkfs:                    # shell commands to run on clients before creating RBD image filesystems - only used by MBench drivers that use RBD
        monitor: false             # enable/disable performance monitoring of the commands
        commands:                  # named groups of commands
          default:                 # group name
            head: []               # group commands to run before creating filesystems on RBD images
            tail: []               # group commands to undo or clean up the head commands, after unmounting RBD images

      mkfs:                        # controls how RBD image filesystems are created on clients - only used by MBench drivers that use RBD
        monitor: true              # enable/disable performance monitoring of RBD image filesystem creation
        options:                   # named option strings, each being passed as-is to the 'mkfs' cli command
          default: -t xfs          # => create a default XFS filesystem - setting to the null value instead causes no filesystem to be created

      pre-mount:                   # shell commands to run on clients before mounting RBD image filesystems - only used by MBench drivers that use RBD, and when RBD image filesystems are created
        monitor: false             # enable/disable performance monitoring of the commands
        commands:                  # named groups of commands
          default:                 # group name
            head: []               # group commands to run before mounting RBD image filesystems
            tail: []               # group commands to undo or clean up the head commands, after unmounting RBD image filesystems

      mount:                       # controls how RBD image filesystems are mounted on clients - only used by MBench drivers that use RBD, and when RBD image filesystems are created
        monitor: false             # enable/disable performance monitoring of RBD image filesystem mounting/unmounting
        options:                   # named option strings, each being passed as-is to the 'mount' cli command
          default: defaults        # => rw,suid,dev,exec,auto,nousr,async (possibly others depending on the filesystem type)

      pre-jobs:                    # shell commands to run on clients before running radosbench or fio jobs
        monitor: false             # enable/disable performance monitoring of the commands
        commands:                  # named groups of commands
          default:                 # group name
            head: []               # group commands to run before running radosbench or fio jobs
            tail: []               # group commands to undo or clean up the head commands, after running radosbench or fio jobs

      radosbench:                  # controls how radosbench jobs are run on clients
        monitor: true              # enable/disable performance monitoring of radosbench jobs
        defaults:                  # radosbench cmd line options used for every job unless a job-specific override is specified
          duration: 30             # pseudo-option that maps to the radosbench positional argument that controls the test duration
          o: 4096                  #
        jobs:                      # named radosbench jobs
          read:                    # simple read job:
            operation: read        # pseudo-option that maps to the radosbench positional argument that controls the test IO operation
          write:                   # simple write job:
            operation: write       # pseudo-option that maps to the radosbench positional argument that controls the test IO operation

      fio:                         # controls how fio jobs are run on clients
        monitor: true              # enable/disable performance monitoring of fio jobs
        defaults:                  # fio cmd line options used for every job unless a job-specific override is specified
          ioengine:  libaio        # this is forcefully overridden for certain MBench drivers
          rwmixread: 50            #
          blocksize: 4096          #
          iodepth:   32            #
          runtime:   30            #
        jobs:                      # named fio jobs
          read:                    # simple read job:
            readwrite: read        #
          write:                   # simple write job:
            readwrite: write       #
    ''')

  #----------------------------------------------------------------------------#

  def load_cfg( self, user_cfg ):
    """
    Loads the user configuration.
    """
    defaults = self.default_cfg() # used to re-populate any mandatory nested keys that are pruned after merging the user cfg
    self.cfg = self.default_cfg() # start with a (deep) copy of the default cfg ...
    self.cfg.update( user_cfg )   # ... then override/extend it by (shallow) merging the user cfg

    for section in defaults.keys():
      for key, default_value in defaults[section].items():
        self.cfg[section][key] = self.cfg[section].get( key, default_value )

#   for s in 'osd client'.split():
#     section = self.cfg[s]
#     if type( section ) != dict:
#       raise Exception( f"Error: MBench cfg.{s} must be a hash/dict." )
#     for key in 'configurations'.split():
#       section[key] = section.get( key, defaults[s][key] )
#     if type( section['configurations'] ) != dict:
#       raise Exception( f"Error: MBench cfg.{s}.configurations must be a hash/dict of named {s} configurations." )
#
#   pool = self.cfg['pool']
#   if type( pool ) != dict:
#     raise Exception( "Error: MBench cfg.pool must be a hash/dict." )
#   for key in 'monitor profiles'.split():
#     pool[key] = pool.get( key, defaults[s][key] )
#   if type( pool['profiles'] ) != list:
#     raise Exception( "Error: MBench cfg.pool.profiles must be an array/list of named pool profiles from the cluster pool_profiles cfg." )
#   for profile in pool['profiles']:
#     if type( profile ) != str:
#       raise Exception( f"Error: MBench cfg.pool.profiles.{profile} must be a string profile name from the cluster pool_profiles cfg." )
#
#   for s in 'image map mkfs mount'.split():
#     section = self.cfg[s]
#     cmd = { 'image':"'rbd create'", 'map':"'rbd device map'" }.get( s, s )
#     if type( section ) != dict:
#       raise Exception( f"Error: MBench cfg.{s} must be a hash/dict." )
#     for key in 'monitor options'.split():
#       section[key] = section.get( key, defaults[s][key] )
#     if type( section['options'] ) != dict:
#       raise Exception( f"Error: MBench cfg.{s}.options must be a hash/dict of named {cmd} command line options." )
#     for name, options in section['options'].items():
#       if type( options ) != str:
#         raise Exception( f"Error: MBench cfg.{s}.options.{name} must be a {cmd} command line option string." )
#
#   for s in 'pre-map pre-mkfs pre-mount pre-jobs'.split():
#     section = self.cfg[s]
#     if type( section ) != dict:
#       raise Exception( f"Error: MBench cfg.{s} must be a hash/dict." )
#     for key in 'monitor commands'.split():
#       section[key] = section.get( key, defaults[s][key] )
#     if type( section['commands'] ) != dict:
#       raise Exception( f"Error: MBench cfg.{s}.commands must be a hash/dict of named groups of client shell commands." )
#     for name, commands in section['commands'].items():
#       for ctype in 'head tail'.split():
#         commands[ctype] = commands.get( ctype, [] )
#         if type( commands[ctype] ) != list:
#           raise Exception( f"Error: MBench cfg.{s}.commands.{name}.{ctype} must be an array/list of client shell command strings." )
#         if [ c for c in commands[ctype] if type(c) != str ].count() > 0:
#           raise Exception( f"Error: MBench cfg.{s}.commands.{name}.{ctype} must be an array/list of client shell command strings." )
#
#   for s in 'radosbench fio'.split():
#     section = self.cfg[s]
#     if type( section ) != dict:
#       raise Exception( f"cfg.{s} must be a hash/dict." )
#     for key in 'monitor defaults jobs'.split():
#       section[key] = section.get( key, defaults[s][key] )
#     if type( section['defaults'] ) != dict:
#       raise Exception( f"cfg.{s}.defaults must be a hash/dict of {s} command line option name/value pairs." )
#     if [ v for k, v in section['defaults'].items() if type(v) != str ].count > 0:
#       raise Exception( f"cfg.{s}.defaults must be a hash/dict of {s} command line option name/value pairs." )
#     if type( section['jobs'] ) != dict:
#       raise Exception( f"cfg.{s}.jobs must be a hash/dict of named {s} jobs." )
#     for name, job in section['jobs'].items():
#       if type( job ) != dict:
#         raise Exception( f"cfg.{s}.jobs.{name} must be a hash/dict of {s} command line option name/value pairs." )
#       if [ v for k, v in job.items() if type(v) != str ].count > 0:
#         raise Exception( f"cfg.{s}.jobs.{name} must be a hash/dict of {s} command line option name/value pairs." )

  #----------------------------------------------------------------------------#

  def rbd( self ):
    """
    Returns .
    """
    rbd  = 'rbd' #self.cfg['client']['rbd-path'] or self.cluster.
    user = self.cfg['client']['id']
    conf = f'{self.run_dir}/ceph.conf'
    return f'{rbd} --id {user} --conf {conf}'

  #----------------------------------------------------------------------------#

  def image_count( self ):
    """
    Returns the number of images to use per client.
    The return value changes as different cfg.image.per-client-counts are traversed in self.image_variations().
    """
    return self.dimensions['image-count']['value']

  #----------------------------------------------------------------------------#

  def pool_image( self ):
    """
    Returns (most of) the pool and RBD image names in <pool>/<image> format.
    The caller must append the RBD image index number to the returned string. See self.image_count().
    Also note that the image name portion contains shell expansion syntax to get client FQDNs.
    Therfore the returned string should only be used in shell commands executed on clients.
    """
    return f"{self.cfg['pool']['name']}/`hostname -f`-"

  #----------------------------------------------------------------------------#

  def mount_point( self ):
    """
    Returns (most of) the absolute path to the directory that an RBD image filesystem is mounted at.
    The caller must append the RBD image index number to the returned string. See self.image_count().
    """
    return f"{self.run_dir}/{self.cfg['mount']['subdir']}-"

  #----------------------------------------------------------------------------#

  def execute_on_clients( self, command ):
    """
    Executes a shell command on the current client group.
    The client hosts used changes as different cfg.client.groups are traversed in self.client_variations().
    """
    group = self.dimensions['client']['value']
    hosts = self.cfg['client']['groups'][group]['hosts']
    hosts = settings.getnodes( 'clients' ) if hosts == '*' else ','.join( hosts )

    return common.pdsh( hosts, command, continue_if_error=False ).communicate()

  #----------------------------------------------------------------------------#

  @contextmanager
  def monitoring( self, task, enabled=True ):
    """
    Conditionally monitors a block of code.
    """
    if enabled:

      output_dir = f'{self.run_dir}/{self.dimensions.path()}/{task}'

      with monitoring.monitor( output_dir ):
        yield

    else:

      yield

  #----------------------------------------------------------------------------#

  @contextmanager
  def osd_variations( self ):
    """
    Creates OSD variations using one or more named OSD configurations.
    """
    for name, configuration in self.cfg['osd']['configurations'].items():

      self.dimensions.push( 'osd', name )
      
      yield

      self.dimensions.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def client_variations( self ):
    """
    Creates client variations using one or more named client configurations.
    """
    for name, configuration in self.cfg['client']['configurations'].items():

      self.dimensions.push( 'client', name ) # used by self.execute_on_clients()

      yield

      self.dimensions.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def command_variations( self, section ):
    """
    Runs one or more named groups of client shell commands from a particular cfg section.
    """
    for name, commands in self.cfg[section]['commands'].items():

      self.dimensions.push( section, name )

      with self.monitoring( f'{section}-head-commands', self.cfg[section]['monitor'] ):
        # for command in commands['head']:
        #   self.execute_on_clients( command )
        pass

      yield

      with self.monitoring( f'{section}-tail-commands', self.cfg[section]['monitor'] ):
        # for command in commands['tail']:
        #   self.execute_on_clients( command )
        pass

      self.dimensions.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def pool_variations( self ):
    """
    Creates pool variations using one or more named pool profiles.
    """
    pool = self.cfg['pool']['name']

    for profile in self.cfg['pool']['profiles']:

      self.dimensions.push( 'pool', profile )

      with self.monitoring( 'create-pool', self.cfg['pool']['monitor'] ):
        # self.cluster.mkpool( ? )
        pass

      yield

      with self.monitoring( 'remove-pool', self.cfg['pool']['monitor'] ):
        # self.cluster.rmpool( ? )
        pass

      self.dimensions.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def image_variations( self ):
    """
    Creates client RBD image variations using one or more named image creation option strings.
    This method is only used by MBench drivers that use RBD images.
    Note that RBD image creation/removal commands are executed from clients, not the head host.
    """
    image_counts = self.cfg['image']['per-client-counts']

    for name, options in self.cfg['image']['options'].items():

      self.dimensions.push( 'image', name )

      # Create all images (the max count) up front, instead of recreating them for each image count variation.
      with self.monitoring( 'create-images', self.cfg['image']['monitor'] ):
        # self.execute_on_clients( f'''
        #   for i in {{1..{max(image_counts)}}}; do
        #     sudo {self.rbd()} create {self.pool_image()}$i {options}
        #   done
        # ''')
        pass

      for image_count in image_counts:

        self.dimensions.push( 'image-count', image_count ) # used by self.image_count()

        yield

        self.dimensions.pop() # image-count

      # Delete all images at the end.
      with self.monitoring( 'remove-images', self.cfg['image']['monitor'] ):
        # self.execute_on_clients( f'''
        #   for i in {{1..{max(image_counts)}}}; do
        #     sudo {self.rbd()} rm {self.pool_image()}$i
        #   done
        # ''')
        pass

      self.dimensions.pop() # image

  #----------------------------------------------------------------------------#

  @contextmanager
  def map_variations( self ):
    """
    Creates client RBD image mapping variations using one or more named map option strings.
    This method is only used by MBench drivers that map RBD images.
    """
    for name, options in self.cfg['map']['options'].items():

      self.dimensions.push( 'map', name )

      with self.monitoring( 'map-images', self.cfg['map']['monitor'] ):
        # self.execute_on_clients( f'''
        #   for i in {{1..{self.image_count()}}}; do
        #     sudo {self.rbd()} device map {self.pool_image()}$i --options '{options}'
        #   done
        # ''')
        pass

      yield

      with self.monitoring( 'unmap-images', self.cfg['map']['monitor'] ):
        # self.execute_on_clients( f'''
        #   for i in {{1..{self.image_count()}}}; do
        #     sudo {self.rbd()} device unmap {self.pool_image()}$i
        #   done
        # ''')
        pass

      self.dimensions.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def filesystem_variations( self ):
    """
    Creates client RBD image filesystem variations using one or more named mkfs option strings.
    If the named mkfs option string is null/None, no RBD image filesystem is created.
    This method is only used by MBench drivers that map and mount RBD images.
    """
    for name, options in self.cfg['mkfs']['options'].items():

      self.dimensions.push( 'mkfs', name, options )

      if options:
        with self.monitoring( 'make-filesystems', self.cfg['mkfs']['monitor'] ):
          # self.execute_on_clients( f'''
          #   for i in {{1..{self.image_count()}}}; do
          #     sudo mkfs {options} /dev/rbd/{self.pool_image()}$i
          #   done
          # ''')
          pass

      yield

      self.dimensions.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def mount_variations( self ):
    """
    Creates RBD image filesystem mount variations using one or more named mount option strings.
    If the RBD image does not have a filesystem (because the mkfs options were null/None), it is not mounted/unmounted.
    This method is only used by MBench drivers that map and mount RBD images.
    """
    if self.dimensions['mkfs']['value'] == None: # image does not have a filesystem, so skip mount variations

      self.dimensions.push( 'mount', '-' )

      yield

      self.dimensions.pop()

    else: # image does have a filesystem, so run through mount variations

      for name, options in self.cfg['mount']['options'].items():

        self.dimensions.push( 'mount', name )

        with self.monitoring( 'mount-filesystems', self.cfg['mount']['monitor'] ):
          # self.execute_on_clients( f'''
          #   for i in {{1..{self.image_count()}}}; do
          #     sudo mount {options} /dev/rbd/{self.pool_image()}$i {self.mount_point()}$i;
          #   done
          # ''')
          pass

        yield

        with self.monitoring( 'unmount-filesystems', self.cfg['mount']['monitor'] ):
          # self.execute_on_clients( f'''
          #   for i in {{1..{self.image_count()}}}; do
          #     sudo umount {self.mount_point()}$i;
          #   done
          # ''')
          pass

        self.dimensions.pop()

  #----------------------------------------------------------------------------#

  def get_radosbench_job_options( self ):
    """
    Returns a string containing the radosbench command line options for the current radosbench job.
    This method is only used by MBench drivers that leverage radosbench.
    """
    def dash( o ):
      return f'-{o}' if len(o) == 1 else f'--{o}'
    
    job = self.dimensions['job']['value']
    options = copy.deepcopy( self.cfg['radosbench']['defaults'] )
    options.update( self.cfg['radosbench']['jobs'][job] )

    if 'duration' not in options:
      raise Exception( f"Error: For radosbench job '{job}', the mandatory 'duration' pseudo-option is missing." )

    if 'operation' not in options:
      raise Exception( f"Error: For radosbench job '{job}', the mandatory 'operation' pseudo-option is missing." )

    duration  = options.pop( 'duration' )
    operation = options.pop( 'operation' )

    forced_options = {
      'id'         : self.cfg['client']['id'],
      'conf'       : self.conf_path,
      'pool'       : self.cfg['pool']['name'],
      'no-cleanup' : None,
      'run-name'   : f'`hostname -s`',
    }

    for o, v in forced_options.items():
      if o in options:
        logger.info( f"Warning: For radosbench job '{job}', the {dash(o)} option is being forced to '{v}'." )
      options[o] = v

    for o in 'n name c p f'.split():
      if o in options:
        logger.info( f"Warning: For radosbench job '{job}', the {dash(o)} option is being ignored because it conflicts with a forced option." )
        option.pop( o )

    run_name = options.pop( 'run-name' ) # to guarantee this is the last option, so a job process index can be appended

    options = ' '.join([ f'{dash(o)} {v}' for o, v in options.items() ])
    options = f'{duration} {operation} {options} --run-name {run_name}' # --run-name must be the last option so a job process index can be appended

    return options

  #----------------------------------------------------------------------------#

  def run_radosbench_jobs( self ):
    """
    Runs one or more named radosbench jobs.
    This method is only used by MBench drivers that leverage radosbench.
    """
    for job in self.cfg['radosbench']['jobs']:

      self.dimensions.push( 'job', job ) # used by radosbench_job_options()

      job_dir    = f'{self.run_dir}/{self.dimensions.path()}'
      radosbench = f'{self.cmd_path_full}'
      options    = self.get_radosbench_job_options() # --run-name must be the last option so a job process index can be appended

      # self.dropcaches()

      with self.monitoring( None, self.cfg['radosbench']['monitor'] ):

        process_count = self.dimensions['procs']['value']
        processes = []

        # for p in range( process_count ):
        #   processes.append(
        #     self.execute_on_clients( f'''
        #       mkdir -p {job_dir}/process-{p}
        #       cd {job_dir}/process-{p}
        #       {radosbench} {options}-{p} 2> stderr > stdout
        #     '''))

        # for process in processes:
        #   process.wait()

      self.dimensions.pop()

  #----------------------------------------------------------------------------#

  def get_fio_job_options( self ):
    """
    Returns a string containing the fio command line options for the current fio job.
    This method is only used by MBench drivers that leverage fio.
    """
    job = self.dimensions['job']['value']
    options = copy.deepcopy( self.cfg['fio']['defaults'] )
    options.update( self.cfg['fio']['jobs'][job] )

    match self.driver:
      case 'fio-librados': forced_ioengine = 'rados'
      case 'fio-librbd':   forced_ioengine = 'rbd'
      case self.driver:    forced_ioengine = None

    forced_options = {
      'ioengine'        : forced_ioengine or options['ioengine'] or 'libaio',
      'group_reporting' : 1,
      'per_job_logs'    : 0,
      'write_bw_log'    : 'process', # => process_bw.log
      'write_iops_log'  : 'process', # => process_iops.log
      'write_lat_log'   : 'process', # => process_lat.log
      'write_hist_log'  : 'process', # => process_hist.log
      'output'          : 'process',
      'output-format'   : 'terse,json',
    }

    for o, v in forced_options.items():
      if o in options:
        logger.info( f"Warning: For fio job '{job}', the --{o} option is being forced to '{v}'." )
      options[o] = v

    options = ' '.join([ f'--{o}={v}' for o, v in options.items() ])

    # TODO: Add file target file/device names.

    return options

  #----------------------------------------------------------------------------#

  def run_fio_jobs( self ):
    """
    Runs one or more named FIO jobs.
    This method is only used by MBench drivers that leverage fio.
    """
    for job in self.cfg['fio']['jobs']:

      self.dimensions.push( 'job', job ) # used by fio_job_options()

      job_dir = f'{self.run_dir}/{self.dimensions.path()}'
      fio     = f'{self.cmd_path_full}'
      options = self.get_fio_job_options()

      # self.dropcaches()

      with self.monitoring( None, self.cfg['fio']['monitor'] ):

        process_count = self.dimensions['procs']['value']
        processes = []

        # for p in range( process_count ):
        #   processes.append(
        #     self.execute_on_clients( f'''
        #       mkdir -p {job_dir}/process-{p}
        #       cd {job_dir}/process-{p}
        #       {fio} {options} 2> stderr > stdout
        #     '''))

        # for process in processes:
        #   process.wait()

      self.dimensions.pop()

  #----------------------------------------------------------------------------#

  def setup_hosts( self ):
    """
    TODO
    """
    hosts = settings.getnodes( 'osds', 'clients' )
    # commands = f'''
    #   sudo mkdir -p -m 0755 {self.run_dir}
    #   cd {self.run_dir}
    #   sudo 
    #   echo '' | sudo tee ceph.conf
    # '''
    # common.pdsh( hosts, commands, continue_if_error=False )

  #----------------------------------------------------------------------------#

  def run_variations( self ):
    """
    TODO
    """
    pass

  #----------------------------------------------------------------------------#

  def gather_results( self ):
    """
    TODO
    """
    pass

  #----------------------------------------------------------------------------#

  def run( self ):
    """
    This method is called by main() in cbt.py.
    """
    super().run()

    self.dimensions.reset()

    self.setup_hosts()
    self.run_variations()
    self.gather_results()
