Task and TaskGroup
====================

Overview
---------

The **Task** module defines the primary abstractions for distributed tasks and their identification within a hierarchy of task groups. 
It provides classes to represent task information, address tasks in a group structure, and manage the execution context of tasks.
This module also includes **TaskGroup** for launching and managing groups of tasks collectively.


Task Class 
------------

The `Task` class encapsulates a remote or local unit of computation. In a Ray-based setup, each `Task` typically runs as a Ray actor on a specific node and GPU. 

.. **Initialization**  
.. - **Environment Variables and Context**: When a `Task` actor is created, Ray injects environment variables such as `RANK`, `WORLD_SIZE`, `NODE_ID`, `GPU_ID`, etc. The `Task`’s constructor uses `_env_setup_before_init()` (called in `__new__`) to read these and initialize internal fields like `_rank` (the task’s index in its group), `_world_size` (total tasks in the group), `_task_name` (string form of its address), and `_task_address` (the `TaskAddress` object). If the task is not running under Ray (e.g. spawned as a subprocess), these variables might not be set by Ray, so in such cases the code handles initialization differently (passing explicit parent address and rank to the constructor). 

.. - **Ray Actor vs. Non-Actor Mode**: The `Task` class can represent both Ray actors and regular processes. It uses an `_is_ray_actor` flag to differentiate. If running as a Ray actor, certain setup steps are performed: for example, registering signal handlers in the main thread (`_register_signal_handlers`) to log stack traces on crashes, and isolating the GPU visibility if required. The method `_setup_local_rank_world_size()` uses the provided `NODE_LOCAL_RANK` and `NODE_LOCAL_WORLD_SIZE` (or sets them) to configure local rank (which GPU index the task should consider as device 0) and how many tasks share the node. `_setup_gpu_info()` determines which CUDA devices are available to this task process (it queries `torch.cuda.device_count()` and collects each device’s UUID if accessible). This helps detect if two tasks share the same physical GPU, which is used later to optimize peer-to-peer communication.

.. - **Manager Proxy and Collective Initialization**: Each task needs to register itself and participate in collective operations. `_init_ray_and_proxies()` is responsible for connecting to the global coordination services. It ensures that Ray is initialized (in case the task process was forked outside of Ray’s direct control) in the correct **namespace** (the cluster’s namespace), and obtains a proxy to the `TaskManager` (a global manager actor). The task then calls `TaskManager.register_task` via this proxy to record its existence and `TaskInfo` in a central registry. It also creates a `Collective` instance (`self._collective = Collective(self)`) for orchestrating distributed communications involving this task. After this point, the task is ready to send and receive data to/from other tasks using collective groups.

.. - **Logging Setup**: The task configures a logger with a name corresponding to its task address (making it easier to trace messages per task). The logging format includes the task name, timestamps, and code location, which is helpful for debugging in a distributed context.

TaskInfo 
~~~~~~~~~~~

The `TaskInfo` dataclass **captures key properties of a task** at runtime. 

.. It includes attributes like the task’s `address` (a `TaskAddress`), its `rank` in the group, the `node_id` and `gpu_id` where it runs, the node’s IP (`node_ip`), and a list of `available_gpus` (identifiers of GPUs visible to that task). 
.. This structure allows convenient local access to a task’s metadata without needing remote calls. For example, when setting up communication, tasks can share their `TaskInfo` so peers know each other’s locations and GPU availability.

+---------------------+-----------------------------------------------+
| Attribute           | Description                                   |
+=====================+===============================================+
| ``address``         | TaskAddress of the task                       |
+---------------------+-----------------------------------------------+
| ``rank``            | Rank of the task within its group             |
+---------------------+-----------------------------------------------+
| ``node_id``         | Identifier of the node hosting the task       |
+---------------------+-----------------------------------------------+
| ``gpu_id``          | Identifier of the GPU assigned to the task    |
+---------------------+-----------------------------------------------+
| ``node_ip``         | IP address of the node hosting the task       |
+---------------------+-----------------------------------------------+
| ``available_gpus``  | List of CUDA device UUIDs available to task   |
+---------------------+-----------------------------------------------+


TaskAddress
~~~~~~~~~~~~~

The `TaskAddress` class **provides a hierarchical naming scheme** for tasks. 
It combines a root group name with an ordered path of ranks to uniquely identify a task in a task group structure. 
For instance, a root task group might be named `"task_group_MyTask"`, and tasks within it have addresses like `"task_group_MyTask:0"`, `"task_group_MyTask:1"`, etc. 
If those tasks spawn their own sub-tasks, additional ranks are appended (e.g. `"task_group_MyTask:0:0"` for a child of rank 0). 
The `TaskAddress` supports operations to navigate this hierarchy: one can get a string name via `get_name()`, retrieve the parent’s rank or address (`get_parent_rank()`, `get_parent_address()`), or derive a child’s address (`get_child_address(rank)`). 
This address system is crucial for identifying tasks across the cluster in a nested scenario—any task can refer to another by its address, even across different groups, enabling flexible communication patterns.

**Communication Methods (send/recv and Channels)**  
Once initialized, a `Task` exposes high-level methods to communicate with other tasks:

- `send(object, dst_group_name, dst_rank, async_op=False)` and the counterpart `recv(src_group_name, src_rank, async_op=False)` allow transferring arbitrary Python objects or tensors between tasks. 
  Under the hood, these calls construct a `TaskAddress` for the peer and use an appropriate **collective group** to perform point-to-point communication. 
  The `Task` does not communicate directly; instead, it delegates to a `CollectiveGroup`. (see the `collective` module ). TODO:

.. - Optimized tensor operations: `send_tensor(tensor, dst_group_name, dst_rank, async_op=False)` and `recv_tensor(tensor, src_group_name, src_rank, async_op=False)` are specialized for sending a single tensor efficiently. They avoid sending extra metadata about tensor shapes and types by assuming the receiver is already prepared with a correctly sized tensor buffer. This is useful in high-performance scenarios where the shape/dtype is known in advance. These should not be mixed with the generic send/recv in the same pairing, as the protocols differ (the generic send transmits type information first, whereas `send_tensor` does not).

In addition to pairwise communications, `Task` provides an interface for **Channels**, which are FIFO queues for exchanging data between tasks:

- `create_channel(name, group_affinity=None, group_rank_affinity=None, maxsize=0)` sets up a new channel. 
  Internally, this spawns a special `_ChannelTask` (a background task that holds the queue) using the provided name and placement, and returns a `Channel` object to interact with it.

- `connect_channel(name)` allows other tasks to connect to an existing channel by name. 
  This locates the channel’s actor (the `_ChannelTask` with rank 0 in its group) and returns a `Channel` handle for sending/receiving through it.

These channel methods illustrate how tasks coordinate higher-level workflows: the actual data transfer in channels still uses the task’s send/recv primitives, 
but the channel abstraction manages queuing and backpressure (see the `channel` module for details). TODO:

TaskGroup
----------

`TaskGroup` is a utility for creating and managing a collection of tasks of the same type. 
It simplifies the process of launching multiple tasks across the cluster and executing methods on them in parallel. Key aspects of `TaskGroup` include:

- **Group Creation**: When you call `TaskGroup(task_cls)(*args, **kwargs).create_group(cluster, ...)`, it will instantiate the given number of tasks on the cluster’s resources. 
  The placement strategy determines how many tasks will be created and on which node/GPU each will run (see the `placement` module). TODO:
  For each task to be launched, `TaskGroup` prepares a set of environment variables. 
  It then calls `Cluster.allocate(...)` to start the Ray actor on the specified node and GPU with those environment variables. 

- **Collective Execution of Methods**: One powerful feature of `TaskGroup` is the ability to call a method on all tasks as if it were a single call. 
  After creating the group, the `TaskGroup` instance dynamically attaches all the methods of the underlying `Task` class onto itself. 
  When you call one of these methods on the `TaskGroup`, it will internally invoke that method on each task in parallel (via Ray remote calls). 

.. - **Selective Execution**: By default, the proxy methods execute on all tasks in the group. However, you can restrict execution to a subset of task ranks by using `TaskGroup.execute_on(ranks)`. Calling this will make the next method invocation apply only to the specified ranks, after which the TaskGroup resets to broadcasting to all ranks. This is useful for scenarios where only one task (e.g., rank 0) should perform a certain operation or when splitting work among different subsets of tasks.

Summary
--------

In summary, the **Task** module provides the foundation for distributed execution. 
`TaskAddress` gives each task a unique identity in a potentially nested group structure, 
`TaskInfo` holds runtime metadata, 
and the `Task` class manages the lifecycle of each distributed task. On top of this, 
`TaskGroup` groups multiple tasks, handling their placement, initialization, and collective method execution. 
These abstractions hide much of the Ray-specific details and low-level environment setup, allowing users to focus on the higher-level logic of their distributed reinforcement learning algorithm.
