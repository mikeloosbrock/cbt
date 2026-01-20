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

class PBenchPermutationStack:
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

  def push( self, tipe, name, cfg, state={} ):
    """
    Appends a new permutation stack element.
    """
    tipe = str( tipe ) # ensure the type is always a string
    if tipe in self.types:
      raise Exception( f"Error: Attempted to add multiple PBench permutation stack elements of type '{tipe}'." )
    self.stack.append({
      'index' : len( self.stack ),
      'type'  : tipe,
      'name'  : name,
      'cfg'   : cfg,
      'state' : state, # purposely *not* a copy
    })
    self.types[tipe] = self.stack[-1]
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

  def __getitem__( self, toi ):
    """
    Returns a permutation stack element identified by its stack index (negative indexes supported) or element type.
    """
    if type( iot ) == int and iot > (-1 * len( self.stack )) and iot < len( self.stack ): # iot is a stack index
      return self.stack[iot]
    if iot in self.types: # iot is an element type
      return self.types[iot]
    return None # iot is not a valid stack index or element type

  #----------------------------------------------------------------------------#

  def path( self, s1="/", s2="=", upto=None ):
    """
    Returns .
    """
    if upto == None:
      upto = len( self.stack )
    else:
      e = self.__get__( upto )
      if e == None:
        raise Exception( f"Error: No PBench permutation stack element with index or type '{upto}' exists." )
      upto = element['index'] + 1

    return s1.join([ f"{e['type']}{s2}{e['name']}" for e in self.stack[:upto] ])

#==============================================================================#
#==============================================================================#

class PBench( Benchmark ):
  """
  Permutation Benchmark.
  """

  #----------------------------------------------------------------------------#

  def default_cfg( self ):
    """
    Returns a copy of the default cfg that is overridden/extended by the user cfg in self.load_cfg().
    """
    return '''

      pbench:                        # this section controls high-level pbench settings
        idle-monitor-wait: 60        #   ?
        use-sudo:  true              #   enable/disable the use of sudo with all shell commands (ceph, rbd, fio, radosbench, etc.)
        ceph-path: ceph              #   path to the ceph binary, may be an absolute path or rely on $PATH lookup
        rbd-path:  rbd               #   path to the rbd  binary, may be an absolute path or rely on $PATH lookup

      osd:                           # this section controls OSD host configuration
        permutations:                #   named OSD cfgs
          default:                   #     default OSD cfg
            sysctl: {}               #       osd sysctl changes, restored afterwards
            sysfs: {}                #       osd sysfs changes, restored afterwards
            cmds:                    #       osd shell cmds
              head: []               #         cmds ran before client cfg
              tail: []               #         cmds ran after client cfg, used to undo/cleanup the head cmds

      client:                        # this section controls client host configuration
        ceph-client-id: cbt-pbench   #   ceph client id used for all IO operations
        permutations:                #   named client cfgs
          default:                   #     default client cfg
            nodes: '*'               #       client host list, must contain one or more dns-resolvable hostnames or '*' to use all clients defined in the cluster cfg
            sysctl: {}               #       client sysctl changes, restored afterwards
            sysfs: {}                #       client sysfs changes, restored afterwards
            cmds:                    #       client shell cmds
              head: []               #         cmds ran before creating pools
              tail: []               #         cmds ran after removing pools, used to undo/cleanup the head cmds

      pool:                          # this section controls how pools are created
        monitor: false               #   enable/disable performance monitoring
        name: cbt-pbench             #   pool name, this pool will be auto created/removed and must not pre-exist in the cluster - likely no reason to change this value
        ec-profiles:                 #   .
          k8-m4-jbod:                #     default erasure-coded pool profile
            k: 8                     #       EC k value
            m: 4                     #       EC m value, the number of domain failures the pool can withstand
            domain: jbod             #       pool failure domain, defaults to 'osd'
        permutations:                #   named pool parameter sets
          default:                   #     default pool parameters
            profile: replica         #       ?

      image:                         # this section controls how RBD images are created - only used by PBench drivers that use RBD
        monitor: true                #   enable/disable performance monitoring
        name: '`hostname -s`'        #   base image name, ensures pool-global unique image names - uses client shell expansion - likely no reason to change this value
        permutations:                #   named image parameter sets
          default:                   #     default image parameters
            images-per-client: 1     #       how many images to create per client
            size: 1TB                #       size of each image
            options: ''              #       options passed as-is to the underlying 'rbd create' cmd - should not contain the '--size' or '--data-pool' options

      pre-map:                       # this section defines shell cmds ran on clients before mapping RBD images - only used by PBench drivers that map RBD images
        monitor: false               #   enable/disable performance monitoring
        permutations:                #   named cmd sets
          noop:                      #     default cmds - do not run any cmds
            head: []                 #       cmds ran before mapping RBD images
            tail: []                 #       cmds ran after unmapping RBD images, used to undo/cleanup the head cmds

      map:                           # this section controls how RBD images are mapped - only used by PBench drivers that map RBD images
        monitor: false               #   enable/disable performance monitoring
        permutations:                #   named map parameter sets
          default:                   #     default map parameters
            options: ''              #       options passed as-is to the underlying 'rbd map' cmd - this is the exact value of the '--options' option

      pre-mkfs:                      # this section defines shell cmds ran on clients before creating RBD image filesystems - only used by PBench drivers that format and mount RBD images
        monitor: false               #   enable/disable performance monitoring
        permutations:                #   named cmd sets
          noop:                      #     default cmds - do not run any cmds
            head: []                 #       cmds ran before creating filesystems on RBD images
            tail: []                 #       cmds ran after unmounting RBD images, used to undo/cleanup the head cmds

      mkfs:                          # this section controls how RBD image filesystems are created - only used by PBench drivers that format and mount RBD images
        monitor: true                #   enable/disable performance monitoring
        permutations:                #   named filesystem parameter sets
          default:                   #     default filesystem parameters
            options: -t xfs          #       options passed as-is to the underlying 'mkfs' cmd

      pre-mount:                     # this section defines shell cmds ran on clients before mounting RBD image filesystems - only used by PBench drivers that format and mount RBD images
        monitor: false               #   enable/disable performance monitoring
        permutations:                #   named cmd sets
          noop:                      #     default cmds - do not run any cmds
            head: []                 #       cmds ran before mounting RBD image filesystems
            tail: []                 #       cmds ran after unmounting RBD image filesystems, used to undo/cleanup the head cmds

      mount:                         # this section controls how RBD image filesystems are mounted on clients - only used by PBench drivers that format and mount RBD images
        monitor: false               #   enable/disable performance monitoring
        permutations:                #   named mount parameter sets
          default:                   #     default mount parameters
            options: defaults        #       options passed as is to the underlying 'mount' cmd, note that 'defaults' == 'rw,suid,dev,exec,auto,nousr,async' (and possibly others depending on the fs type)

      pre-test:                      # this section defines shell cmds ran on clients before running IO tests
        monitor: false               #   enable/disable performance monitoring
        permutations:                #   named cmd sets
          noop:                      #     default cmds - do not run any cmds
            head: []                 #       cmds ran before running IO tests
            tail: []                 #       cmds ran after running IO tests, used to undo/cleanup the head cmds

      fio:                           # this section controls how fio IO tests are run on clients - only used by fio-based PBench drivers
        binary: fio                  #   how to invoke fio, should include sudo and/or filesystem path if necessary - likely no reason to change this value
        defaults:                    #   fio command line options used for every test unless there is a test-specific override
          processes: 1               #     pseudo-option to control how many concurrent processes are used, works slightly differently than the numjobs option
          ioengine:  libaio          #     this is automatically overridden for certain PBench drivers
          rwmixread: 50              #     .
          blocksize: 4096            #     .
          iodepth:   32              #     .
          runtime:   30              #     .
        examples:                    #   .
          fio-seqread:               #     fio sequential read
            tool: fio                #       use the fio tool
            readwrite: read          #       sequential read operation
          fio-seqwrite:              #     fio sequential write
            tool: fio                #       use the fio tool
            readwrite: write         #       sequential write operation
          fio-randread:              #     fio random read
            tool: fio                #       use the fio tool
            readwrite: randread      #       random read operation
          fio-randwrite:             #     fio random write
            tool: fio                #       use the fio tool
            readwrite: randwrite     #       random write operation

      radosbench:                    # this section controls how radosbench IO tests are run on clients - only used by radosbench-based PBench drivers
        binary: radosbench           #   how to invoke fio, should include sudo and/or filesystem path if necessary - likely no reason to change this value
        defaults:                    #   radosbench command line options used for every test unless there is a test-specific override
          processes: 1               #     pseudo-option to control how many concurrent processes to use for the test (each 
          duration: 30               #     pseudo-option that maps to the radosbench positional argument that controls the test duration
          o: 4096                    #     .
        examples:                    #   .
          read:                      #     sequential read
            tool: radosbench         #       use the radosbench tool
            operation: read          #       pseudo-option that maps to the radosbench positional argument that controls the test IO operation
          write:                     #     sequential write
            tool: radosbench         #       use the radosbench tool
            operation: write         #       pseudo-option that maps to the radosbench positional argument that controls the test IO operation

      test:                          # this section controls how IO tests are run on clients
        monitor: false               #   enable/disable performance monitoring
        permutations: {}             #   named IO tests - see the examples in the 'fio' and 'radosbench' sections above
    '''

  #----------------------------------------------------------------------------#
  
  def deep_merge_cfg( a, b ):
    """
    Recursively merges cfg dict b into cfg dict a. Note that dict a is modified in place.
    """
    for k in b.keys():
      if isinstance( b[k], dict ) and k in a and isinstance( a[k], dict ):
        a[k] = deep_merge_cfg( a[k], b[k] )
      elif isinstance( b[k], list ):
        a[k] = b[k] # copy.deepcopy( b[k] ) # a deep copy should not be necessary
      else:
        a[k] = b[k]
    return a

  #----------------------------------------------------------------------------#

  def load_cfg( user_cfg ):
    """
    Loads the effective configuration.
    """
    self.cfg = {}
    defaults = yaml.safe_load( default_cfg() )

    # Check for invalid 1st and 2nd-level dict keys in the user cfg.
    for s in user_cfg:
      if s not in defaults:
        raise Exception( f"Error: PBench cfg has invalid section '{s}'." )
      for k in user_cfg[s]:
        if k not in defaults[s]:
          raise Exception( f"Error: PBench cfg has invalid key '{k}' in section '{s}'." )

    # Build the effective cfg by deep-merging the default and user cfgs.
    deep_merge_cfg( self.cfg, defaults )
    deep_merge_cfg( self.cfg, user_cfg )

    # Deep-merging the user cfg into/ontop of the default cfg is appropriate for most parts of the cfg.
    # However, there are some parts of the cfg should be overridden rather than merged.
    # That is, if a value exists in the user cfg, it should completely replace, instead of being merged with, the value in the default cfg.
    # The following code checks and fixes these 'no-merge' parts of the effective cfg.
    for s in self.cfg.keys():
      for k in self.cfg[s].keys():
        if s in user_cfg and k in user_cfg[s]:
          if (( k == 'permutations'                ) or # don't merge permutations in any cfg section
              ( s == 'pool' and k == 'ec-profiles' ) or # don't merge pool ec-profiles
              ( s == 'fio' and k == 'tests'        ) or # don't merge fio tests
              ( s == 'radosbench' and k == 'tests' )):  # don't merge radosbench tests
            self.cfg[s][k] = user_cfg[s][k]

  #----------------------------------------------------------------------------#

  def __init__( self, archive_dir, cluster, config ):
    """
    PBench base class initializer.
    This method extends the Benchmark base class initializer.
    This method is also extended by all PBench subclasses.
    """
    super().__init__( archive_dir, cluster, config )
    self.load_cfg( config )
    self.pstack = PBenchPermutationStack()
    self.out_dir = self.archive_dir

    ceph = self.cfg['head']['ceph-path']
    rbd  = self.cfg['client']['rbd-path']
    user = self.cfg['client']['ceph-client-id']
    conf = f"{self.run_dir}/ceph.conf"
    
    self.sudo = f"sudo"
    self.ceph = f"{self.sudo} {ceph} --id {user} --conf {conf}"
    self.rbd  = f"{self.sudo} {rbd } --id {user} --conf {conf}"

  #----------------------------------------------------------------------------#

  def initialize( self ):
    """
    TODO
    """
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

  def images_per_client( self ):
    """
    Returns the number of images to use per client.
    The return value changes as different image permutations are iterated over in self.image_permutations().
    """
    return self.pstack['image']['cfg']['images-per-client']

  #----------------------------------------------------------------------------#

  def image_name( self, i=None ):
    """
    Returns an RBD image name.
    The i parameter is the RBD image index. See self.images_per_client().
    Note that the image name usually contains shell expansion syntax to get the client's FQDN.
    Therefore the returned string must only be used in shell commands executed on the client host.
    """
    i = '' if i is None else f"-{i}"
    return f"{self.cfg['image']['name']}{i}"

  #----------------------------------------------------------------------------#

  def pool_image( self, i=None ):
    """
    Returns an RBD image name in <pool>/<image> format.
    The i parameter is the RBD image index. See self.images_per_client().
    Note that the image name usually contains shell expansion syntax to get the client's FQDN.
    Therefore the returned string must only be used in shell commands executed on the client host.
    """
    return f"{self.cfg['pool']['name']}/{self.image_name(i)}"

  #----------------------------------------------------------------------------#

  def mount_point( self, i=None ):
    """
    Returns the absolute path to the directory that an RBD image filesystem is mounted at.
    The i parameter is the RBD image index. See self.images_per_client().
    """
    i = '' if i is None else f"-{i}"
    return f"{self.run_dir}/rbd-mnt{i}"

  #----------------------------------------------------------------------------#

  def execute_on_head( self, cmds, continue_if_error=False ):
    """
    Executes shell commands on the head node, which is usually one of the cluster mon/mgr nodes.
    """
    if type( cmds ) == list:
      cmds = "\n".join( cmds )

    node = settings.getnodes( 'head' )
    return common.pdsh( node, cmds, continue_if_error ).communicate()

  #----------------------------------------------------------------------------#

  def execute_on_osds( self, cmds, continue_if_error=False ):
    """
    Executes shell commands on all OSD nodes.
    """
    if type( cmds ) == list:
      cmds = "\n".join( cmds )

    nodes = settings.getnodes( 'osds' )
    return common.pdsh( node, cmds, continue_if_error ).communicate()

  #----------------------------------------------------------------------------#

  def execute_on_clients( self, cmds, continue_if_error=False ):
    """
    Executes shell commands on all currently active client nodes.
    The active client node set changes as different client permutations are iterated over in self.client_permutations().
    """
    if type( cmds ) == list:
      cmds = "\n".join( cmds )

    if self.pstack['client']['cfg']['nodes'] == '*':
      nodes = settings.getnodes( 'clients' )
    else:
      nodes = ','.join( self.pstack['client']['cfg']['nodes'] )

    return common.pdsh( nodes, cmds, continue_if_error ).communicate()

  #----------------------------------------------------------------------------#

  @contextmanager
  def monitoring( self, task='', enabled=False ):
    """
    Conditionally monitors a block of code.
    """
    enabled = self.pstack[-1]['cfg'].get( 'monitor', false ) or enabled
    path = f"{self.run_dir}/{self.pstack.path()}/monitoring/{task}"

    if enabled:
      with monitoring.monitor( path ):
        yield

    else:
      yield

  #----------------------------------------------------------------------------#

  @contextmanager
  def osd_permutations( self ):
    """
    Iterates over OSD host configuration permutations.
    Modifies sysctl variables, writes to sysfs files and executes shell commands on OSD hosts.
    """
    for pname, p in self.cfg['osd']['permutations'].items():

      self.pstack.push( 'osd', pname, p )

      # todo: backup and modify sysctl variables
      # todo: backup and write sysfs files
      self.execute_on_osds( p['cmds']['head'] )

      yield

      # todo: restore sysctl variables
      # todo: restore sysfs files
      self.execute_on_osds( p['cmds']['tail'] )

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def client_permutations( self ):
    """
    Iterates over client host configuration permutations.
    Modifies sysctl variables, writes to sysfs files and executes shell commands on client hosts.
    """
    for pname, p in self.cfg['client']['permutations'].items():

      self.pstack.push( 'client', pname, p ) # see self.execute_on_clients()

      # todo: backup and modify sysctl variables
      # todo: backup and write to sysfs files
      self.execute_on_clients( p['cmds']['head'] )

      yield

      # todo: restore sysctl variables
      # todo: restore sysfs files
      self.execute_on_clients( p['cmds']['tail'] )

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def command_permutations( self, section ):
    """
    Iterates over command permutations configured in a particular cfg section.
    Executes shell commands on client hosts.
    """
    for pname, p in self.cfg[section]['permutations'].items():

      self.pstack.push( section, pname, p )

      with self.monitoring( f"{section}-head" ):
        self.execute_on_clients( p['head'] )

      yield

      with self.monitoring( f"{section}-tail" ):
        self.execute_on_clients( p['tail'] )

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def pool_permutations( self ):
    """
    Iterates over pool permutations, executing pool and erasure-code-profile create/remove commands on the head host.
    """
    self.execute_on_head([
      f"#{self.ceph} osd erasure-code-profile set {ec_profile} k={ec['k']} m={ec['m']} crush-failure-domain={ec['domain']}"
      for ec_profile, ec in self.cfg['pool']['ec-profiles'].items()
    ])

    for pname, p in self.cfg['pool']['permutations'].items():

      self.pstack.push( 'pool', pname, p )

      pool = self.cfg['pool']['name']
      if 'ec-profile' in p:
        ec_profile = p['ec-profile']
        if ec_profile in self.cfg['pool']['ec-profiles']:
          ec_profile = f"{pool}-{p['ec-profile']}"

      pg_num = p['pg-num'] if 'pg-num' in p else 
      pg_nums  = ''
      pg_nums += f"{p['pg-num']} " if 'pg-num' in p else ''
      pg_nums += f"{p['pgp-num']}" if 'pg-num' in p and 'pgp-num' in p else ''

      with self.monitoring( 'create-pool' ):
        if ec:
          self.execute_on_head( f'''
            #{self.ceph} osd pool create {pool}-data {pg_nums} erasure {p['ec-profile']}
            #{self.ceph} osd pool create {pool} {pg_nums} replicated {p['size']}
          ''')
          if self.rbd_driver:
            self.execute_on_head( f'''
              #{self.rbd} pool init {pool}-data"
              #{self.rbd} pool init {pool}"
            ''')
        else:
          self.execute_on_head( f'''
            #{self.ceph} osd pool create {pool} {pg_nums} replicated {p['size']}
          ''')
          if self.rbd_driver:
            self.execute_on_head( f'''
              #{self.rbd} pool init {pool}
            ''')

      yield

      with self.monitoring( 'remove-pool' ):
        self.execute_on_clients([
          f"#{self.ceph} osd pool rm {pool_name}" )
          for pool_name in pool_names
        ])

      self.pstack.pop()
    
    self.execute_on_clients([
      f"#{self.ceph} osd erasure-code-profile rm {pool}-{ec_profile}"
      for ec_profile in self.cfg['pool']['ec-profiles']
    ])

  #----------------------------------------------------------------------------#

  @contextmanager
  def image_permutations( self ):
    """
    Iterates over RBD image permutations, executing RBD image create/remove commands on client hosts (not the head host).
    This method is only used by PBench drivers that use RBD images.
    """
    for pname, p in self.cfg['image']['permutations'].items():

      self.pstack.push( 'image', pname, p ) # see self.images_per_client()
      
      pool = self.cfg['pool']['name']
      data_pool = f"--data-pool {pool}-data" if 'ec-profile' in self.pstack['pool']['cfg'] else ''
      options = p['options'] if 'options' in p else ''

      with self.monitoring( 'create-images' ):
        self.execute_on_clients([
          f"#{self.rbd} create {self.pool_image(i)} --size {p['size']} {data_pool} {options}"
          for i in self.images_per_client()
        ])

      yield

      with self.monitoring( 'remove-images' ):
        self.execute_on_clients([
          f"#{self.rbd} rm {self.pool_image(i)}"
          for i in self.images_per_client()
        ])

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def map_permutations( self ):
    """
    Iterates over RBD image map permutations, executing RBD image map/unmap commands on client hosts.
    This method is only used by PBench drivers that map RBD images.
    """
    for pname, p in self.cfg['map']['permutations'].items():

      self.pstack.push( 'map', pname, p )

      options = f"--options '{p['options']}'" if 'options' in p else ''

      with self.monitoring( 'map-images' ):
        self.execute_on_clients([
          f"#{self.rbd} device map {self.pool_image(i)} {options}"
          for i in self.images_per_client()
        ])

      yield

      with self.monitoring( 'unmap-images' ):
        self.execute_on_clients([
          f"#{self.rbd} device unmap {self.pool_image(i)}"
          for i in self.images_per_client()
        ])

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def mkfs_permutations( self ):
    """
    Iterates over RBD image filesystem permutations, executing mkfs commands to format RBD images mapped on client hosts.
    This method is only used by PBench drivers that format and mount RBD images.
    """
    for pname, p in self.cfg['fs']['permutations'].items():

      self.pstack.push( 'mkfs', pname, p )

      with self.monitoring( 'make-filesystems' ):
        self.execute_on_clients([
          f"#{self.sudo} mkfs {p['options']} /dev/rbd/{self.pool_image(i)}"
          for i in self.images_per_client()
        ])

      yield

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def mount_permutations( self ):
    """
    Iterates over RBD image mount permutations, executing mount/umount commands against RBD images mapped on client hosts.
    This method is only used by PBench drivers that format and mount RBD images.
    """
    for pname, p in self.cfg['mount']['permutations'].items():

      self.pstack.push( 'mount', pname, p )

      options = p['options'] if 'options' in p else ''

      with self.monitoring( 'mount-filesystems' ):
        self.execute_on_clients([
          f"#{self.sudo} mount {options} /dev/rbd/{self.pool_image(i)} {self.mount_point(i)}"
          for i in self.images_per_client()
        ])

      yield

      with self.monitoring( 'unmount-filesystems' ):
        self.execute_on_clients([
          f"#{self.sudo} umount {self.mount_point(i)}"
          for i in self.images_per_client()
        ])

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  def fio_options( self ):
    """
    Returns fio command line options for the current fio test.
    This method is only used by fio-based PBench drivers.
    """
    test = self.pstack['test']['name'] # the current fio test
    options = copy.deepcopy( self.cfg['fio']['defaults'] )
    options.update( self.cfg['fio']['tests'][test] )

    processes = 1
    if 'processes' in options:
      processes = options.pop( 'processes' ) # 'processes' is not an actual fio option

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

    options = ' '.join([ f"--{o}={v}" for o, v in options.items() ])
    options = [ '', f"--name=global {options}" ] + names

    return ''.join([ f'\\\n  {o}' for o in options ] + '\\\n  '

  #----------------------------------------------------------------------------#

  def fio_tests( self ):
    """
    Iterates over fio test permutations, executing fio tests on client hosts.
    This method is only used by fio-based PBench drivers.
    """
    for test in self.cfg['fio']['tests']:

      self.pstack.push( 'test', test )

      test_dir = f"{self.run_dir}/{self.pstack.path()}"
      fio      = f"{self.sudo} {self.cmd_path_full}"
      options  = self.fio_options()

      self.dropcaches()

      with self.monitoring():
        self.execute_on_clients( f'''
          {self.sudo} mkdir -p -m 0755 {test_dir}
          {self.sudo} cd {test_dir}
          #{fio} {options} 2> stderr > stdout
        ''')

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  def radosbench_options( self ):
    """
    Returns radosbench command line options for the current radosbench test.
    This method is only used by radosbench-based PBench drivers.
    """
    def dash( o ):
      return f"-{o}" if len(o) == 1 else f"--{o}"
    
    test = self.pstack['test']['name']
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
      'conf'       : f"{self.run_dir}/ceph.conf",
      'pool'       : self.cfg['pool']['name'],
      'no-cleanup' : '',
      'run-name'   : f"cbt-pbench-radosbench-`hostname -s`-",
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

    options = ' '.join([ f"{dash(o)} {v}" for o, v in options.items() ])
    options = f"{duration} {operation} {options} --run-name {run_name}" # --run-name must be the last option so a process index can be appended

    return options

  #----------------------------------------------------------------------------#

  def radosbench_tests( self ):
    """
    Iterates over radosbench test permutations, executing radosbench tests on client hosts.
    This method is only used by radosbench-based PBench drivers.
    """
    for test in self.cfg['radosbench']['tests']:

      self.pstack.push( 'test', test )

      test_dir   = f"{self.run_dir}/{self.pstack.path()}"
      radosbench = f"{self.sudo} {self.cmd_path_full}"
      options    = self.radosbench_test_options() # --run-name must be the last option so a process index can be appended

      processes = 1 # todo: extract process count from radosbench defaults and test-specific cfg
      commands  = []

      for p in processes:
        commands.extend( f'''
          {self.sudo} mkdir -p -m 0755 {test_dir}
          {self.sudo} cd {test_dir}
          #{radosbench} {options}-{p} 2> stderr > stdout
        ''')

      self.dropcaches()

      with self.monitoring():
        self.execute_on_clients( cmds )

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  @contextmanager
  def test_permutations( self ):
    """
    Iterates over test permutations, executing test commands on client hosts.
    """
    for pname, p in self.cfg['test']['permutations'].items():

      self.pstack.push( 'test', pname, p )

      test_dir = f"{self.run_dir}/{self.pstack.path()}"
      commands = [f'''
        {self.sudo} mkdir -p -m 0755 {test_dir}
        {self.sudo} cd {test_dir}
      ''']

      match p['tool']:

        case 'fio':
          fio     = f"{self.sudo} {}"
          options = self.fio_options()
          commands.extend( f'''
            #{fio} {options} 2> stderr > stdout
          ''')
      
        case 'radosbench':
          radosbench = self.cfg['test']['radosbench-']
          options    = self.radosbench_options() # --run-name must be the last option so a process index can be appended
          processes  = 1 # todo: extract process count from radosbench defaults and test-specific cfg
          for p in processes:
            commands.extend( f'''
              #{radosbench} {options}-{p} 2> stderr > stdout
            ''')

      self.dropcaches()

      with self.monitoring():
        self.execute_on_clients( commands )

      self.pstack.pop()

  #----------------------------------------------------------------------------#

  def run_setup( self ):
    """
    Performs common cleanup tasks needed before running most PBench benchmarks.
    This method may be extended or overridden by PBench subclasses.
    """
    client   = f"client.{self.cfg['clients']['ceph-client-id']}"
    mon_caps = f"mon 'profile rbd'"
    osd_caps = f"osd 'allow * pool={self.cfg['pool']['name']}, allow * pool={self.cfg['pool']['name']}-data'"
    mgr_caps = f"mgr 'profile rbd pool={self.cfg['pool']['name']}, profile rbd pool={self.cfg['pool']['name']}-data'"

    self.execute_on_head( f'''
      {self.sudo} mkdir -p -m 0755 {self.run_dir}
      {self.ceph} auth rm {client}
      {self.ceph} auth add {client} {mon_caps} {osd_caps} {mgr_caps}
      {self.ceph} auth get {client} | sudo tee {self.run_dir}/ceph.keyring
    ''')

    self.pstack.reset()

  #----------------------------------------------------------------------------#
  
  def run_cleanup( self ):
    """
    Performs common cleanup tasks needed after running most PBench benchmarks.
    This method may be extended or overridden by PBench subclasses.
    """
    client = f"client.{self.cfg['clients']['ceph-client-id']}"

    self.execute_on_head( f'''
      {self.ceph} auth rm {client}
    ''')

  #----------------------------------------------------------------------------#

  def run_permutations( self ):
    """
    Iterates over all configured test permutations.
    This method must be implemented by PBench subclasses.
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
    self.run_permutations()
    self.run_cleanup()
    self.gather_results()
