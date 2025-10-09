import common
import settings
import monitoring
import os
import time
import logging
import copy

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
    reset()

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
    self.stack += {
      'name'  : name,
      'value' : value,
      'state' : {}.update( state ), # purposely *not* a deep copy
    }
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
    self.load_cfg()
    self.dimensions = MBenchDimensions()

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

  def default_cfg( self ):
    """
    Returns a copy of the default cfg that is overridden/extended by the user cfg in load_cfg().
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
            hosts: *               # client host list, must contain one or more dns-resolvable hostnames or '*' to use all clients defined in the cluster cfg
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
          replica-x4:
          ec-k8-m4:

      image:                       # controls how per-client RBD images are created - only used by MBench drivers that use RBD
        monitor: true              # enable/disable performance monitoring of RBD image creation/removal
        name-prefix: ""            # this string is always appended with "`hostname -s`-" to ensure pool-global unique RBD image names
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
          default: ""              # => no extra options

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

  def load_cfg( self ):
    """
    .
    """
    defaults = self.default_cfg() # used to re-populate any mandatory nested keys that are pruned after merging the user cfg
    self.cfg = self.default_cfg() # start with a copy of the default cfg ...
    self.cfg.update( cfg )   # ... then override/extend it by (shallow) merging the user cfg

    for key in self.cfg.keys():
      if key in user_cfg:
        self.cfg

    for key in user_cfg:
      if key in default_cfg:
        self.cfg[key].update( user_cfg[key] )

    client = self.cfg['client']
    if type( client ) != dict:
      fail( "cfg.client must be a hash/dict." )
    client['groups'] = \
      client.get( 'groups', defaults['client']['groups'] ) # in case user cfg is missing 'groups' key
    if type( client['groups'] ) != dict:
      fail( "cfg.client.groups must be a hash/dict of named client groups." )

    pool = self.cfg['pool']
    if type( pool ) != dict:
      fail( "cfg.pool must be a hash/dict." )
    pool['profiles'] = \
      pool.get( 'profiles', defaults['pool']['profiles'] ) # in case user cfg is missing 'profiles' key
    if type( pool['options'] ) != dict:
      fail( "cfg.pool.profiles must be a hash/dict of named pool profiles." )
    for name, profile in pool['profiles'].items():
      if type( profile ) != dict:
        fail( "cfg.pool.profiles.%s must be a hash/dict." % ( name ))

    for s in 'image map mkfs mount'.split():
      section = self.cfg[s]
      cmd = { 'image':"'rbd create'", 'map':"'rbd device map'" }.get( s, s )
      if type( section ) != dict:
        fail( "cfg.%s must be a hash/dict." % ( s ))
      section['options'] = \
        section.get( 'options', defaults[s]['options'] ) # in case user cfg is missing 'options' key
      if type( section['options'] ) != dict:
        fail( "cfg.%s.options must be a hash/dict of named %s command options strings." % ( s, cmd ))
      for name, options in section['options'].items():
        if type( options ) != str:
          fail( "cfg.%s.options.%s must be a %s command options string." % ( s, name, cmd ))

    for s in 'pre-map post-map pre-mount post-mount'.split():
      section = self.cfg[s]
      if type( section ) != dict:
        fail( "cfg.%s must be a hash/dict." % ( s ))
      section['commands'] = \
        section.get( 'commands', defaults[s]['commands'] ) # in case user cfg is missing 'commands' key
      if type( section['commands'] ) != dict:
        fail( "cfg.%s.commands must be a hash/dict of named client shell command sets." % ( s ))
      for name, commands in section['commands'].items():
        for ctype in 'head tail'.split():
          commands[ctype] = commands.get( ctype, [] ) # in case 'head' or 'tail' key is missing
          if type( commands[ctype] ) != list:
            fail( "cfg.%s.commands.%s.%s must be an array/list of client shell command strings." % ( s, name, ctype ))
          if [ c for c in commands[ctype] if type(c) != str ].count() > 0:
            fail( "cfg.%s.commands.%s.%s must be an array/list of client shell command strings." % ( s, name, ctype ))

    fio = self.cfg['fio']
    if type( fio ) != dict:
      fail( "cfg.fio must be a hash/dict." )
    fio['defaults'] = \
      fio.get( 'defaults', defaults['fio']['defaults'] ) # in case user cfg is missing 'defaults' key
    if type( fio['defaults'] ) != dict:
      fail( "cfg.fio.defaults must be a hash/dict of fio command line option name/value string pairs." )
    if [ v for k, v in fio['defaults'].items() if type(v) != str ].count > 0:
      fail( "cfg.fio.defaults must be a hash/dict of fio command line option name/value string pairs." )
    fio['jobs'] = \
      fio.get( 'jobs', defaults['fio']['jobs'] ) # in case user cfg is missing 'jobs' key
    if type( fio['jobs'] ) != dict:
      fail( "cfg.fio.jobs must be a hash/dict of named fio jobs." )
    for name, job in fio['jobs'].items():
      if type( job ) != dict:
        fail( "cfg.fio.jobs.%s must be a hash/dict of fio command line option name/value string pairs." % ( name ))
      if [ v for k, v in job.items() if type(v) != str ].count > 0:
        fail( "cfg.fio.jobs.%s must be a hash/dict of fio command line option name/value string pairs." % ( name ))

    if self.driver == 'fio_krbd' or self.driver == 'fio_device':
      if 'ioengine' not in self.cfg['fio']['defaults']:
        self.cfg['fio']['defaults'] = 'libaio'

  #----------------------------------------------------------------------------#

  def rbd( self ):
    """
    Returns .
    """
    rbd  = self.cfg['client']['rbd-path']
    user = self.cfg['client']['id']
    conf = self.cfg['client']['conf-path']
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

    for name, profile in self.cfg['pool']['profiles'].items():

      self.dimensions.push( 'pool', name )

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

  def radosbench_job_options( self ):
    """
    Returns a string containing the radosbench command line options for the current radosbench job.
    This method is only used by MBench drivers that leverage radosbench.
    """
    def dash( o ):
      return f'-{o}' if len(o) == 1 else f'--{o}'
    
    job      = self.dimensions['job']['value']
    defaults = copy.deepcopy( self.cfg['radosbench']['defaults'] )
    options  = defaults.update( self.cfg['radosbench']['jobs'][job] )

    if 'duration' not in options:
      fail( f"Error: For radosbench job '{job}', the mandatory 'duration' pseudo-option is missing." )

    if 'operation' not in options:
      fail( f"Error: For radosbench job '{job}', the mandatory 'operation' pseudo-option is missing." )

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
      options    = radosbench_job_options() # --run-name must be the last option so a job process index can be appended

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

  def fio_job_options( self ):
    """
    Returns a string containing the fio command line options for the current fio job.
    This method is only used by MBench drivers that leverage fio.
    """
    job      = self.dimensions['job']['value']
    defaults = copy.deepcopy( self.cfg['fio']['defaults'] )
    options  = defaults.update( self.cfg['fio']['jobs'][job] )

    forced_options = {
      'ioengine'        : self.forced_fio_ioengine or options['ioengine'],
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
      options = fio_job_options()

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

  def setup_hosts( self )
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
    super().__init__()

    self.dimensions.reset()

    self.setup_hosts()
    self.run_variations()
    self.gather_results()
