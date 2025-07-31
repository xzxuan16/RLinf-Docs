Cluster and Resource Management
===============================

The **Cluster** class manages the connection to the Ray cluster and the launching of management actors and task actors. 
It serves as a singleton representing the entire cluster’s resources and provides methods to allocate tasks on specific nodes and GPUs. 
By encapsulating Ray initialization and node information, it simplifies distributed setup for the rest of the framework.

Initialization and Ray Setup
----------------------------

When a `Cluster` object is created, it performs the following steps in its initialization:

- **Ray Initialization** : If Ray is not already started, it calls `ray.init()` with the namespace `Cluster.NAMESPACE`. 

- **Waiting for Nodes** : After Ray initialization, `Cluster` waits until the expected number of nodes (`num_nodes`) have registered with Ray. 

- **Gathering Node Information** : Once the nodes are ready, `Cluster` constructs a list of `NodeInfo` objects (Ray ID, IP, CPU and GPU counts).
  The 'master' node is placed first; remaining nodes are sorted by IP.

- **Master Address and Port** : The master node's IP is stored and a free TCP port is chosen for collective communications. 

- **Global Manager Actors** - A key part of initialization is launching three singleton manager actors:

  * `TaskManager` : tracks every task's metadata.  
  * `CollectiveManager` : stores collective-group information, including
    rendezvous ports.  
  * `NodeManager` : provides node layout (IP, GPU count, master port) to tasks.


Using Cluster to Allocate Tasks
-------------------------------

The most important methods is `allocate()`. It hides the details of starting a Ray actor on a specific node with given resources:

.. code-block:: python

   Cluster.allocate(
       cls,                     # The class of the actor to launch
       task_name,               # A unique name for the actor
       node_id,                 # The index of the node where this actor should run.
       gpu_id,                  # The index of the GPU on that node to assign to this actor.
       env_vars,                # A dictionary of environment variables to set in the actor’s runtime environment
       cls_args=[],             # positional args for the actor class
       cls_kwargs={}            # keyword args for the actor class
   )

Inside `allocate`, the cluster finds the `NodeInfo` for the specified `node_id`.  
It then creates a remote actor handle for `cls` using `ray.remote(cls)`.  
It further prepares an options dictionary for the actor that includes the `runtime_env` with the given `env_vars`.  
Finally, it calls `.remote(*cls_args, **cls_kwargs)` on the actor with those options, which launches the actor asynchronously.

Attaching to an Existing Cluster
--------------------------------

If code running in a different process needs to interact with the same cluster, it can create a `Cluster()` object without arguments.  
In this case, it calls:

.. code-block:: python

    ray.init(address="auto", namespace=Cluster.NAMESPACE, ...)

to connect to the already-running Ray cluster in the known namespace.  
It then retrieves the existing manager actors via their known names:

.. code-block:: python

    self._node_manager = NodeManager.get_proxy()
    self._nodes        = self._node_manager.get_nodes()
    self._master_ip    = self._node_manager.get_master_ip()

This allows consistency: all processes that create a Cluster (with the correct namespace) will share the same view of cluster configuration and managers.

Summary
-------

By using the Cluster class, the rest of the framework does not need to call `ray.init` or handle low-level resource scheduling; those details are handled once in the Cluster setup.  
This centralizes control of cluster resources and avoids conflicting Ray initializations, making the distributed environment predictable and easier to manage.
