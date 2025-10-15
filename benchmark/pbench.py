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

class PBenchPermutation:
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
    (Re)intializes the permutation stack, removing any existing elements.
    """
    self.stack = []
    self.types = {}

  #----------------------------------------------------------------------------#

  def push( self, etype, name, state={} ):
    """
    Appends a new permutation stack element.
    """
    etype = str( etype ) # ensure the type is always a string
    if etype in self.types:
      raise Exception( f"Error: Attempted to add multiple PBenchPermutation elements of type '{etype}'." )
    self.stack.append({
      'index' : len( self.stack ),
      'type'  : etype,
      'name'  : name,
      'state' : state, # purposely *not* a copy
    })
    self.types[etype] = self.stack[-1]
    return self.stack[-1]

  #----------------------------------------------------------------------------#

  def pop( self ):
    """
    Removes the last permutation stack element.
    """
    if len( self.stack ) == 0:
      return None
    element = self.stack.pop()
    self.types.pop( element['type'] )
    return element

  #----------------------------------------------------------------------------#

  def __getitem__( self, e ):
    """
    Returns a permutation stack element identified by its type string or stack index (negative indexes supported).
    """
    if type( e ) == int and e > (-1 * len( self.stack )) and e < len( self.stack ):
      return self.stack[e]
    if e in self.types:
      return self.types[e]
    return None # the specified stack index or element type does not exist

  #----------------------------------------------------------------------------#

  def path( self, s1="/", s2="=", upto=None ):
    """
    Returns .
    """
    if upto == None:
      upto = len( self.stack )
    else:
      element = self.__get__( upto )
      if element == None:
        raise Exception( f"Error: No PBenchPermutation element with type or index '{upto}' exists." )
      upto = element['index'] + 1

    return s1.join([ f"{e['type']}{s2}{e['name']}" for e in self.stack[:upto] ])

#==============================================================================#
#==============================================================================#

class PBench( Benchmark ):
  """
  Permutation Benchmark.
  """

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    Extends the base Benchmark initializer.
    """
    super().__init__( archive_dir, cluster, config )
    self.load_cfg( config )
    self.permutation = PBenchPermutation()
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

      osd:                              # controls ...
        configurations:                 # named osd configurations
          default:                      # configuration name
            sysctl-settings: {}         #
            sysfs-settings: {}          #
            tell-commands:              #
              head: []                  #
              tail: []                  #
            shell-commands:             #
              head: []                  #
              tail: []                  #

      client:                           # controls ...
        ceph-auth-id: cbt-pbench        #
        configurations:                 # named client configurations
          default:                      # configuration name
            nodes: '*'                  # client host list, must contain one or more dns-resolvable hostnames or '*' to use all clients defined in the cluster cfg
            sysctl-settings: {}         #
            sysfs-settings: {}          #
            tell-commands:              #
              head: []                  #
              tail: []                  #
            shell-commands:             #
              head: []                  #
              tail: []                  #

      pool:                             # controls how benchmark pools are created
        monitor: false                  # enable/disable performance monitoring of pool creation/removal
        name: cbt-pbench                # pool name - there's probably no reason to ever change this
        permutations:                   # named pool permutations
          default:                      # permutation name
            profile: replica-2          # 

      image:                            # controls how RBD images are created - only used by PBench drivers that use RBD
        monitor: true                   # enable/disable performance monitoring of RBD image creation/removal
        name-prefix: '`hostname -s`-'   # ensures pool-global unique RBD image names
        permutations:                   # named image permutations
          default:                      # permutation name
            rbd-options: --size 1TB     # options passed as-is to the 'rbd create' command
            images-per-client: 1        # how many images to use per client

      pre-map:                          # shell commands to run on clients before mapping RBD images - only used by PBench drivers that use RBD
        monitor: false                  # enable/disable performance monitoring of the commands
        permutations:                   # named command permutations
          default:                      # permutation name
            head: []                    # commands to run before mapping RBD images
            tail: []                    # commands to undo or clean up the head commands, after unmapping RBD images

      map:                              # controls how RBD images are mapped - only used by PBench drivers that use RBD
        monitor: false                  # enable/disable performance monitoring of RBD image mapping/unmapping
        permutations:                   # named mapping permutations
          default:                      # permutation name
            rbd-options: ''             # options passed as-is to the 'rbd map' command

      pre-fs:                           # shell commands to run on clients before creating RBD image filesystems - only used by PBench drivers that use RBD
        monitor: false                  # enable/disable performance monitoring of the commands
        permutations:                   # named command permutations
          default:                      # permutation name
            head: []                    # commands to run before creating filesystems on RBD images
            tail: []                    # commands to undo or clean up the head commands, after unmounting RBD images

      fs:                               # controls how RBD image filesystems are created - only used by PBench drivers that use RBD
        monitor: true                   # enable/disable performance monitoring of RBD image filesystem creation
        permutations:                   # named filesystem permutations
          default:                      # permutation name
            mkfs-options: -t xfs        # options passed as-is to the mkfs command - if set to null, no filesystem will be created

      pre-mount:                        # shell commands to run on clients before mounting RBD image filesystems - only used by PBench drivers that use RBD, and when RBD image filesystems are created
        monitor: false                  # enable/disable performance monitoring of the commands
        permutations:                   # named command permutations
          default:                      # permutation name
            head: []                    # commands to run before mounting RBD image filesystems
            tail: []                    # commands to undo or clean up the head commands, after unmounting RBD image filesystems

      mount:                            # controls how RBD image filesystems are mounted on clients - only used by PBench drivers that use RBD, and when RBD image filesystems are created
        monitor: false                  # enable/disable performance monitoring of RBD image filesystem mounting/unmounting
        permutations:                   # named mounting permutations
          default:                      # permutation name
            mount-options: defaults     # options passed as is to the mount command - 'defaults' => rw,suid,dev,exec,auto,nousr,async (possibly others depending on the filesystem type)

      pre-test:                         # shell commands to run on clients before running radosbench or fio tests
        monitor: false                  # enable/disable performance monitoring of the commands
        permutations:                   # named command permutations
          default:                      # permutation name
            head: []                    # commands to run before running radosbench or fio tests
            tail: []                    # commands to undo or clean up the head commands, after running radosbench or fio tests

      radosbench:                       # controls how radosbench tests are run on clients
        monitor: true                   # enable/disable performance monitoring of radosbench tests
        defaults:                       # radosbench cmd line options used for every test unless there is a test-specific override
          processes: 1                  # pseudo-option to control how many concurrent processes to use for the test (each 
          duration: 30                  # pseudo-option that maps to the radosbench positional argument that controls the test duration
          o: 4096                       #
        tests:                          # named radosbench tests
          read:                         # read test
            operation: read             # pseudo-option that maps to the radosbench positional argument that controls the test IO operation
          write:                        # write test
            operation: write            # pseudo-option that maps to the radosbench positional argument that controls the test IO operation

      fio:                              # controls how fio tests are run on clients
        monitor: true                   # enable/disable performance monitoring of fio tests
        defaults:                       # fio cmd line options used for every test unless there is a test-specific override
          processes: 1                  # pseudo-option to control how many concurrent processes are used, works slightly differently than the numjobs option
          ioengine:  libaio             # this is forcefully overridden for certain PBench drivers
          rwmixread: 50                 #
          blocksize: 4096               #
          iodepth:   32                 #
          runtime:   30                 #
        tests:                          # named fio tests
          read:                         # read test
            readwrite: read             #
          write:                        # write test
            readwrite: write            # 
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

    for s in 'osd client'.split():
      section = self.cfg[s]
      if type( section ) != dict:
        raise Exception( f"Error: PBench cfg.{s} must be a hash/dict." )
      for key in 'permutations'.split():
        section[key] = section.get( key, defaults[s][key] )
      if type( section['permutations'] ) != dict:
        raise Exception( f"Error: PBench cfg.{s}.permutations must be a hash/dict." )
 
    pool = self.cfg['pool']
    if type( pool ) != dict:
      raise Exception( "Error: PBench cfg.pool must be a hash/dict." )
    for key in 'monitor profiles'.split():
      pool[key] = pool.get( key, defaults[s][key] )
    if type( pool['profiles'] ) != list:
      raise Exception( "Error: PBench cfg.pool.profiles must be an array/list of named pool profiles from the cluster pool_profiles cfg." )
    for profile in pool['profiles']:
      if type( profile ) != str:
        raise Exception( f"Error: PBench cfg.pool.profiles.{profile} must be a string profile name from the cluster pool_profiles cfg." )
 
#   for s in 'image map mkfs mount'.split():
#     section = self.cfg[s]
#     cmd = { 'image':"'rbd create'", 'map':"'rbd device map'" }.get( s, s )
#     if type( section ) != dict:
#       raise Exception( f"Error: PBench cfg.{s} must be a hash/dict." )
#     for key in 'monitor options'.split():
#       section[key] = section.get( key, defaults[s][key] )
#     if type( section['options'] ) != dict:
#       raise Exception( f"Error: PBench cfg.{s}.options must be a hash/dict of named {cmd} command line options." )
#     for name, options in section['options'].items():
#       if type( options ) != str:
#         raise Exception( f"Error: PBench cfg.{s}.options.{name} must be a {cmd} command line option string." )
#
#   for s in 'pre-map pre-mkfs pre-mount pre-test'.split():
#     section = self.cfg[s]
#     if type( section ) != dict:
#       raise Exception( f"Error: PBench cfg.{s} must be a hash/dict." )
#     for key in 'monitor commands'.split():
#       section[key] = section.get( key, defaults[s][key] )
#     if type( section['commands'] ) != dict:
#       raise Exception( f"Error: PBench cfg.{s}.commands must be a hash/dict of named groups of client shell commands." )
#     for name, commands in section['commands'].items():
#       for ctype in 'head tail'.split():
#         commands[ctype] = commands.get( ctype, [] )
#         if type( commands[ctype] ) != list:
#           raise Exception( f"Error: PBench cfg.{s}.commands.{name}.{ctype} must be an array/list of client shell command strings." )
#         if [ c for c in commands[ctype] if type(c) != str ].count() > 0:
#           raise Exception( f"Error: PBench cfg.{s}.commands.{name}.{ctype} must be an array/list of client shell command strings." )
#
#   for s in 'radosbench fio'.split():
#     section = self.cfg[s]
#     if type( section ) != dict:
#       raise Exception( f"cfg.{s} must be a hash/dict." )
#     for key in 'monitor defaults tests'.split():
#       section[key] = section.get( key, defaults[s][key] )
#     if type( section['defaults'] ) != dict:
#       raise Exception( f"cfg.{s}.defaults must be a hash/dict of {s} command line option name/value pairs." )
#     if [ v for k, v in section['defaults'].items() if type(v) != str ].count > 0:
#       raise Exception( f"cfg.{s}.defaults must be a hash/dict of {s} command line option name/value pairs." )
#     if type( section['tests'] ) != dict:
#       raise Exception( f"cfg.{s}.tests must be a hash/dict of named {s} tests." )
#     for name, test in section['tests'].items():
#       if type( test ) != dict:
#         raise Exception( f"cfg.{s}.tests.{name} must be a hash/dict of {s} command line option name/value pairs." )
#       if [ v for k, v in test.items() if type(v) != str ].count > 0:
#         raise Exception( f"cfg.{s}.tests.{name} must be a hash/dict of {s} command line option name/value pairs." )

  #----------------------------------------------------------------------------#

  def rbd( self ):
    """
    Returns .
    """
    rbd  = 'rbd' #self.cfg['client']['rbd-path'] or self.cluster.
    user = self.cfg['clients']['ceph-auth-id']
    conf = f'{self.run_dir}/ceph.conf'
    return f'{rbd} --id {user} --conf {conf}'

  #----------------------------------------------------------------------------#

  def images_per_client( self ):
    """
    Returns the number of images to use per client.
    The return value changes as different image permutations are iterated over in self.image_permutations().
    """
    return self.permutation['image']['state']['images-per-client']

  #----------------------------------------------------------------------------#

  def image_name( self, i=None ):
    """
    Returns an RBD image name.
    The i parameter is the RBD image index. See self.images_per_client().
    Note that the image name contains shell expansion syntax to get client FQDNs.
    Therfore the returned string must only be used in shell commands executed on clients.
    """
    i = '' if i is None else f'-{i}'
    return f"`hostname -s`{i}"

  #----------------------------------------------------------------------------#

  def pool_image( self, i=None ):
    """
    Returns an RBD image name in <pool>/<image> format.
    The i parameter is the RBD image index. See self.images_per_client().
    Note that the image name contains shell expansion syntax to get client FQDNs.
    Therfore the returned string must only be used in shell commands executed on clients.
    """
    return f"{self.cfg['pool']['name']}/{self.image_name(i)}"

  #----------------------------------------------------------------------------#

  def mount_point( self, i=None ):
    """
    Returns the absolute path to the directory that an RBD image filesystem is mounted at.
    The i parameter is the RBD image index. See self.images_per_client().
    """
    i = '' if i is None else f'-{i}'
    return f"{self.run_dir}/{self.cfg['mount']['subdir']}{i}"

  #----------------------------------------------------------------------------#

  def execute_on_head( self, commands, continue_if_error=False ):
    """
    Executes shell commands on the head node, which is usually one of the cluster mon/mgr nodes.
    """
    if type( commands ) == list:
      commands = "\n".join( commands )

    node = settings.getnodes( 'head' )
    return common.pdsh( node, commands, continue_if_error ).communicate()

  #----------------------------------------------------------------------------#

  def execute_on_osds( self, commands, continue_if_error=False ):
    """
    Executes shell commands on all OSD nodes.
    """
    if type( commands ) == list:
      commands = "\n".join( commands )

    nodes = settings.getnodes( 'osds' )
    return common.pdsh( node, commands, continue_if_error ).communicate()

  #----------------------------------------------------------------------------#

  def execute_on_clients( self, commands, continue_if_error=False ):
    """
    Executes shell commands on all currently active client nodes.
    The active client node set changes as different client permutations are iterated over in self.client_permutations().
    """
    if type( commands ) == list:
      commands = "\n".join( commands )

    nodes = ','.join( self.permutation['client']['state']['nodes']
    return common.pdsh( nodes, commands, continue_if_error ).communicate()

  #----------------------------------------------------------------------------#

  @contextmanager
  def monitoring( self, task='', enabled=False ):
    """
    Conditionally monitors a block of code.
    """
    enabled = self.permutation[-1]['state'].get( 'monitor', false ) or enabled
    path = f'{self.run_dir}/{self.permutation.path()}/monitoring/{task}'

    if enabled:
      with monitoring.monitor( path ):
        yield

    else:
      yield

  #----------------------------------------------------------------------------#

  @contextmanager
  def osd_permutations( self ):
    """
    Iterates over OSD permutations.
    """
    for pname, p in self.cfg['osd']['permutations'].items():

      self.permutation.push( 'osd', pname, p )
      
      yield

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def client_permutations( self ):
    """
    Iterates over client permutations.
    """
    for pname, p in self.cfg['client']['permutations'].items():

      self.permutation.push( 'client', pname, p ) # see self.execute_on_clients()

      yield

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def command_permutations( self, section ):
    """
    Iterates over client shell command permutations configured in a particular cfg section.
    """
    for pname, p in self.cfg[section]['permutations'].items():

      self.permutation.push( section, pname, p )

      with self.monitoring( f'{section}-head' ):
        self.execute_on_clients( p['head'] )

      yield

      with self.monitoring( f'{section}-tail' ):
        self.execute_on_clients( p['tail'] )

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def pool_permutations( self ):
    """
    Iterates over pool permutations.
    """
    pool = self.cfg['pool']['name']

    for pname, p in self.cfg['pool']['permutations'].items():

      self.permutation.push( 'pool', pname, p )

      with self.monitoring( 'create-pool' ):
        # self.cluster.mkpool( ? )
        pass

      yield

      with self.monitoring( 'remove-pool' ):
        # self.cluster.rmpool( ? )
        pass

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def image_permutations( self ):
    """
    Iterates over RBD image permutations.
    This method is only used by PBench drivers that use RBD images.
    Note RBD image creation/removal commands are executed on clients, not the head host.
    """
    for pname, p in self.cfg['image']['permutations'].items():

      self.permutation.push( 'image', pname, p ) # see self.images_per_client()

      with self.monitoring( 'create-images' ):
        self.execute_on_clients([
          f"# sudo {self.rbd()} create {self.pool_image(i)} {p['rbd-options']}"
          for i in self.images_per_client()
        ])

      yield

      with self.monitoring( 'remove-images' ):
        self.execute_on_clients([
          f"# sudo {self.rbd()} rm {self.pool_image(i)}"
          for i in self.images_per_client()
        ])

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def map_permutations( self ):
    """
    Iterates over RBD image mapping permutations.
    This method is only used by PBench drivers that map RBD images.
    """
    for pname, p in self.cfg['map']['permutations'].items():

      self.permutation.push( 'map', pname, p )

      with self.monitoring( 'map-images' ):
        self.execute_on_clients([
          f"# sudo {self.rbd()} device map {self.pool_image(i)} --options '{p['rbd-options']}'"
          for i in self.images_per_client()
        ])

      yield

      with self.monitoring( 'unmap-images' ):
        self.execute_on_clients([
          f"# sudo {self.rbd()} device unmap {self.pool_image(i)}"
          for i in self.images_per_client()
        ])

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def filesystem_permutations( self ):
    """
    Iterates over RBD image filesystem permutations.
    If a permutation has a null mkfs-options string, no filesystem is created.
    This method is only used by PBench drivers that map and mount RBD images.
    """
    for pname, p in self.cfg['fs']['permutations'].items():

      self.permutation.push( 'fs', pname, p )

      if p['mkfs-options'] != None:
        with self.monitoring( 'make-filesystems' ):
          self.execute_on_clients([
            f"# sudo mkfs {p['mkfs-options']} /dev/rbd/{self.pool_image(i)}"
            for i in self.images_per_client()
          ])

      yield

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def mount_permutations( self ):
    """
    Iterates over RBD image filesystem mount permutations.
    RBD images are only mounted if they have a filesystem (ie, the filesystem permutation had non-null mkfs-options).
    This method is only used by PBench drivers that map and mount RBD images.
    """
    if self.permutation['fs']['state']['mkfs-options'] != None: # images have filesystems on them

      for pname, p in self.cfg['mount']['permutations'].items():

        self.permutation.push( 'mount', pname, p )

        with self.monitoring( 'mount-filesystems' ):
          self.execute_on_clients([
            f"# sudo mount {p['mount-options']} /dev/rbd/{self.pool_image(i)} {self.mount_point(i)}"
            for i in self.images_per_client()
          ])

        yield

        with self.monitoring( 'unmount-filesystems' ):
          self.execute_on_clients([
            f"# sudo umount {self.mount_point(i)}"
            for i in self.images_per_client()
          ])

        self.permutation.pop()

    else: # images do not have filesystems on them

      self.permutation.push( 'mount', '' )

      yield

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  def radosbench_test_options( self ):
    """
    Returns radosbench command line options for the current radosbench test.
    This method is only used by PBench drivers that use radosbench.
    """
    def dash( o ):
      return f'-{o}' if len(o) == 1 else f'--{o}'
    
    test = self.permutation['test']['name']
    options = copy.deepcopy( self.cfg['radosbench']['defaults'] )
    options.update( self.cfg['radosbench']['tests'][test] )

    if 'duration' not in options:
      raise Exception( f"Error: For radosbench test '{test}', the mandatory 'duration' pseudo-option is missing." )

    if 'operation' not in options:
      raise Exception( f"Error: For radosbench test '{test}', the mandatory 'operation' pseudo-option is missing." )

    duration  = options.pop( 'duration' )
    operation = options.pop( 'operation' )

    if 'processes' in options:
      processes = options.pop( 'processes' )

    forced_options = {
      'id'         : self.cfg['clients']['ceph-auth-id'],
      'conf'       : f'{self.run_dir}/ceph.conf',
      'pool'       : self.cfg['pool']['name'],
      'no-cleanup' : '',
      'run-name'   : f'cbt-pbench-radosbench-`hostname -s`-',
    }

    for o, v in forced_options.items():
      if o in options:
        logger.info( f"Warning: For radosbench test '{test}', the {dash(o)} option is being forced to '{v}'." )
      options[o] = v

    for o in 'n name c p f'.split():
      if o in options:
        logger.info( f"Warning: For radosbench test '{test}', the {dash(o)} option is being ignored because it conflicts with a forced option." )
        option.pop( o )

    run_name = options.pop( 'run-name' ) # ensure this is the last option, so a process index can be appended

    options = ' '.join([ f'{dash(o)} {v}' for o, v in options.items() ])
    options = f'{duration} {operation} {options} --run-name {run_name}' # --run-name must be the last option so a process index can be appended

    return options

  #----------------------------------------------------------------------------#

  def run_radosbench_tests( self ):
    """
    Runs radosbench tests.
    This method is only used by PBench drivers that use radosbench.
    """
    for test in self.cfg['radosbench']['tests']:

      self.permutation.push( 'test', test )

      test_dir   = f'{self.run_dir}/{self.permutation.path()}'
      radosbench = f'{self.cmd_path_full}'
      options    = self.radosbench_test_options() # --run-name must be the last option so a process index can be appended

      processes = 1 # todo: extract process count from radosbench defaults and test-specific cfg
      commands  = []

      for p in processes:
        commands.extend([
          f"sudo mkdir -p -m 0755 {test_dir}",
          f"cd {test_dir}",
          f"# sudo {radosbench} {options}-{p} 2> stderr > stdout",
        ])

      self.dropcaches()

      with self.monitoring():
        self.execute_on_clients( commands )

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  def fio_test_options( self ):
    """
    Returns fio command line options for the current fio test.
    This method is only used by PBench drivers that use fio.
    """
    test = self.permutation['test']['name'] # the current fio test
    options = copy.deepcopy( self.cfg['fio']['defaults'] )
    options.update( self.cfg['fio']['tests'][test] )

    processes = 1
    if 'processes' in options:
      processes = options.pop( 'processes' )

    forced_options = {
      'group_reporting' : 1,
      'per_job_logs'    : 1,
      'output'          : 'results',
      'output-format'   : 'terse,json',
    }
    names = []

    match self.driver:

      case 'fio-librados':
        forced_options.update({
          'ioengine'    : 'rados',
          'clustername' : f"{}",
          'clientname'  : f"{self.cfg['client']['ceph-auth-id']}",
          'conf'        : f"{self.run_dir}/ceph.conf",
          'pool'        : f"{self.cfg['pool']['name']}",
        })
        for p in processes:
          names += [ f"--name=proc-{p}" ]

      case 'fio-librbd':
        forced_options.update({
          'ioengine'    : 'rbd',
          'clustername' : f"{}",
          'clientname'  : f"{self.cfg['client']['ceph-auth-id']}",
          'conf'        : f"{self.run_dir}/ceph.conf",
          'pool'        : f"{self.cfg['pool']['name']}",
          'rbdname'     : f"{self.}"
        })
        for p in processes:
          for i in self.images_per_client():
            names += [ f"--name=proc-{p}.image-{i} --rbdname={}" ]

      case 'fio-krbd':
        for p in processes:
          for i in self.images_per_client():
            names += [ f"--name=proc-{p}.image-{i} --directory={self.mount_point(i)}" ]

      case 'fio-device':
        for p in processes:
          names += [ f"--name=proc-{p}.image-{i} --directory={self.mount_point(i)}" ]

    for o, v in forced_options.items():
      if o in options:
        logger.info( f"Warning: For fio test '{test}', the --{o} option is being forced to '{v}'." )
      options[o] = v

    options = ' '.join([ f'--{o}={v}' for o, v in options.items() ])
    options = [ '', f'--name=global {options}' ] + names

    return ''.join([ f'\\\n  {o}' for o in options ] + '\\\n  '

  #----------------------------------------------------------------------------#

  def run_fio_tests( self ):
    """
    Runs fio tests.
    This method is only used by PBench drivers that use fio.
    """
    for test in self.cfg['fio']['tests']:

      self.permutation.push( 'test', test )

      test_dir = f'{self.run_dir}/{self.permutation.path()}'
      fio      = f'{self.cmd_path_full}'
      options  = self.fio_test_options()

      self.dropcaches()

      with self.monitoring():
        self.execute_on_clients([
          f"sudo mkdir -p -m 0755 {test_dir}",
          f"cd {test_dir}",
          f"# sudo {fio} {options} 2> stderr > stdout",
        ])

      self.permutation.pop()

  #----------------------------------------------------------------------------#

  def run_setup( self ):
    """
    TODO
    """
    client   = f"client.{self.cfg['clients']['ceph-auth-id']}"
    mon_caps = f"mon 'profile rbd'"
    osd_caps = f"osd 'allow * pool={self.cfg['pool']['name']}, allow * pool={self.cfg['pool']['name']}-data'"
    mgr_caps = f"mgr 'profile rbd pool={self.cfg['pool']['name']}, profile rbd pool={self.cfg['pool']['name']}-data'"

    self.execute_on_head( f'''
      mkdir -p -m 0755 {self.run_dir}
      sudo ceph auth rm {client}
      sudo ceph auth add {client} {mon_caps} {osd_caps} {mgr_caps}
      sudo ceph auth get {client} | sudo tee {self.run_dir}/ceph.keyring
    ''')

  #----------------------------------------------------------------------------#
  
  def run_cleanup( self ):
    """
    TODO
    """
    client = f"client.{self.cfg['clients']['ceph-auth-id']}"

    self.execute_on_head( f'''
      sudo ceph auth rm {client}
    ''')

  #----------------------------------------------------------------------------#

  def run_permutations( self ):
    """
    This method is to be implemented by PBench driver-specific subclasses.
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
    self.run_setup()
    self.permutation.reset()
    self.iterate_permutations()
    self.gather_results()
    self.run_cleanup()
