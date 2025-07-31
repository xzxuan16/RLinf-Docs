Collective Communication 
========================

The collective module implements low-level communication primitives between tasks, building on PyTorch's distributed backend (torch.distributed). 
It provides asynchronous work handles and manages **collective groups** for both point-to-point and (potentially) collective operations among tasks. 
The primary classes here are `Collective`, which handles group creation, and `CollectiveGroup`, which represents a communication group of tasks and provides methods like send/recv.

.. Asynchronous Work Abstractions
.. --------------------------------

.. Several helper classes (`AsyncWork`, `AsyncFuncWork`, `AsyncCollWork`) define a common interface for operations that may complete asynchronously:

.. - `AsyncWork` is an abstract base with methods `wait()` (block until completion) and `async_wait()` (awaitable coroutine for completion), and a method `then(func, *args, **kwargs)` to attach a callback to run after completion.

.. - `AsyncFuncWork` is used to chain a Python callback after an async operation. It stores a callable and its arguments, and when invoked (via the PyTorch `Future.then` mechanism), it executes the function and stores the result. This allows constructing pipelines of operations where one starts after the previous finishes.

.. - `AsyncCollWork` wraps one or multiple PyTorch `dist.Work` objects (the result of non-blocking collective ops) to conform to the `AsyncWork` interface. It provides `async_wait()` by periodically checking if each work is completed (since not all `dist.Work` implementations support awaiting), and a `then()` that attaches a callback to the underlying PyTorch future (only allowed if there is a single work in the group). It also defines `__add__` to combine two asynchronous works (e.g., if an operation internally consists of multiple sub-operations, they can be aggregated into one handle).

.. These classes make it easier to manage asynchronous sends/receives and to build non-blocking communication patterns. For instance, a call to `send(async_op=True)` will return an `AsyncWork` (specifically an `AsyncCollWork` wrapping the underlying communication work), which the caller can `wait()` on later or chain with other actions.

Collective and Group Management
--------------------------------

The `Collective` class is instantiated on each task (as a singleton per task) and is responsible for creating and caching `CollectiveGroup` instances. 
When two tasks or a set of tasks need to communicate, a collective group must be established that includes all participants. 
The typical usage in this framework is to form groups for point-to-point (often just two tasks) communication by `Collective.create_collective_group(task_addresses, group_name=None)`
which either retrieves an existing `CollectiveGroup` for the given set of task addresses or creates a new one. 

.. If `group_name` isn’t provided, it generates a unique name by concatenating the task names with a prefix (e.g., `"cg-taskA:0-taskB:0"` for a two-task group). To coordinate group creation across tasks, `Collective` consults the global `CollectiveManager`. The first task (by sorted order of addresses) acts as the master: if the group is not yet known, that task gathers the `TaskInfo` for all members (by querying the `TaskManager` for each address) and registers a new `CollectiveGroupInfo` via `CollectiveManager.register_collective_group`. This record holds the group’s name, list of tasks (with their info, including IPs and available GPUs), and designates one task’s address as master for setting up rendezvous. Other tasks attempting to join the group will find the `group_info` already registered and simply retrieve it (busy-waiting until it appears). In all cases, once the `CollectiveGroupInfo` is obtained, the local `CollectiveGroup` object is constructed (and cached in `_name_group_map` for reuse) with the group metadata and the current task’s address to determine its rank.

.. This mechanism ensures that even if two tasks nearly simultaneously try to communicate, only one creates the group metadata and the others synchronize on that information. It leverages Ray’s distributed actor (the `CollectiveManager`) as a simple coordination service.

CollectiveGroup and P2P Communication
----------------------------------------------------------------

A `CollectiveGroup` represents a group of tasks (usually 2 for point-to-point). 
On creation, it identifies the rank of the current task within the group (by matching its TaskAddress against the list in `group_info`). It then prepares to establish the communication channels.

PyTorch's `torch.distributed` requires a process group to be initialized for tasks to communicate. `CollectiveGroup._init_p2p_process_group()` is called on first use of the group.
This method create two process groups for NCCL (GPU) backend, and two for Gloo (CPU) backend. `_nccl_send_group` represents the process group where it is the sender (and similarly `_nccl_recv_group` is where it is the receiver). 
This effectively sets up dedicated one-way channels: rank 0 broadcasting to rank 1 on one group and rank 1 broadcasting to rank 0 on the other. In a two-task scenario, a broadcast is equivalent to a point-to-point send/receive.
 

.. - It uses a **master port** approach for rendezvous. The designated master task (rank 0 by convention in this group) finds a free network port (`Cluster.find_free_port()`) and stores it via `CollectiveManager.set_master_port_info(group_name, port)`. Other ranks loop, waiting for this port to appear via `CollectiveManager.get_master_port_info`.

.. - Once the port is known, each task calls PyTorch’s `dist.init_process_group` to create multiple process groups:

..   - Two process groups for NCCL (GPU) backend, and two for Gloo (CPU) backend. Specifically, one NCCL group is intended for sends from rank 0 to rank 1 and another for the reverse direction; similarly a Gloo group for CPU sends one way and another for the opposite. After initialization, if this task’s rank is 1, it swaps the send/recv group handles so that each task’s `_nccl_send_group` represents the process group where *it* is the sender (and similarly `_nccl_recv_group` is where it is the receiver). This effectively sets up dedicated one-way channels: rank 0 broadcasting to rank 1 on one group and rank 1 broadcasting to rank 0 on the other. In a two-task scenario, a broadcast is equivalent to a point-to-point send/receive.
 
..   - These process groups are created with a unique group name (suffixes like `"_nccl_send"`, `"_nccl_recv"`, etc., appended to the collective group name) to isolate them. The same master IP and port are used for all, ensuring both tasks join the same rendezvous.

.. - After setting up, the master resets the stored port in the manager (via `reset_master_port_info`) to avoid reuse for future groups.

With the process groups in place, `CollectiveGroup` can perform communications. The methods provided include:

- **Senc**: `send(obj, async_op=False)` send an object (tensor, list of tensors, dict of tensors, or arbitrary picklable object) to the single other peer in the group. 
  This method first sends a small **header** indicating the object type so that the receiver will know how to interpret the incoming data.

  .. - If it’s a single tensor (`TENSOR` code): the send call internally delegates to `_send_tensor_list` with a list of one tensor.

  .. - If it’s a list of tensors (`TENSOR_LIST`): it calls `_send_tensor_list` directly.

  .. - If it’s a dict of tensors (`TENSOR_DICT`): it will send the dictionary keys separately, then send all the tensor values as a list (using the same tensor list mechanism).

  .. - If it’s a generic object (`OBJECT`): the object is serialized to a byte tensor using PyTorch’s `distributed_c10d._object_to_tensor` utility, then that byte tensor is sent via Gloo.
  
  .. The `_send_tensor_list` method is worth noting: it first sends a metadata blob describing the list (each tensor’s shape and dtype, and whether the tensors are on CPU or GPU). This metadata is serialized to a CPU tensor and sent, so the receiver knows how to allocate buffers. After metadata, the actual tensor data is sent. For GPU tensors, if the two tasks do not share the same physical device, it uses NCCL’s non-blocking send (`dist.isend`) for each tensor. If the tasks are on the same node and share a CUDA device, an optimization kicks in: instead of sending through NCCL, it may use CUDA IPC handles. Specifically, `_check_same_device_with_peer()` checks if the tasks have a common device UUID in their `available_gpus` lists. If both tasks are actually on the exact same GPU (common device and each has only one device), then `send_tensor` or `_send_tensor_list` can use a special path: calling `torch.multiprocessing.reductions.reduce_tensor(tensor)` to get a shared memory handle to the tensor, and then sending that handle (as CPU tensor data) to the peer. The peer can reconstruct the tensor without copying through CPU memory. If they share a node but have multiple devices (result 0 from the check), a slightly different “uncertain peer” path is taken (in practice, it falls back to using NCCL per tensor sends after ensuring proper synchronization).
  

- **Recv**: `recv(async_op=False)` is the counterpart to `send`, this method receives an object from the peer. 
  It first receives of the type code (an integer) from the peer (using the Gloo CPU group). Once the type is known, it dispatches to the appropriate receive helper and receive the proper object.

  .. - If the type is `TENSOR`: it calls `_recv_tensor_list()` expecting a list of length 1, then returns the single tensor.

  .. - If `TENSOR_LIST`: it calls `_recv_tensor_list()` to get the full list.

  .. - If `TENSOR_DICT`: it calls `_recv_tensor_dict()`, which first receives the list of keys (sent earlier by the sender) and then uses `_recv_tensor_list` for the values, reconstructing the dictionary.

  .. - If `OBJECT`: it calls `_recv_object()`, which receives the size of the byte tensor and then the tensor itself, and uses `distributed_c10d._tensor_to_object` to deserialize the original Python object.

- **Direct Tensor Send/Recv**: `send_tensor(tensor, async_op=False)` and `recv_tensor(tensor, async_op=False)` are optimized for the case where only one tensor is being transferred and the receiver already has an allocated tensor buffer. 
  These avoid the extra round-trip of sending a type code or metadata. They leverage the same internal methods but do not send any header. 
  Thus, they must be used in pairs (a sender using `send_tensor` must be matched by the receiver using `recv_tensor`). 

  .. Internally, these check for the same node/device optimization as well. If the peers are on the same device, they exchange CUDA IPC handles instead of copying data. If they are on the same node but different devices, a slower path might be used to ensure correct device placement, or they revert to NCCL broadcast.
  
.. Under the hood, the fundamental operations `_send(tensor, device, async_op)` and `_recv(tensor, device, async_op)` use PyTorch’s `dist.broadcast` primitive on the appropriate process group. For example, `_send` will call `dist.broadcast(tensor, src=self._rank, group=appropriate_group)`. In a two-rank group, if `self._rank` is 0, this effectively sends the tensor to rank 1. If `self._rank` is 1, calling broadcast with src=1 will send to rank 0. The reason broadcast is used (instead of send/recv which PyTorch’s API lacks for NCCL) is that with two participants, a broadcast is equivalent to a point-to-point send. The code maintains two groups per device type so that each rank knows which group to use when it is the source versus the destination. This is why for rank 1 the groups are swapped after initialization – so that each side’s “send group” always has that side as the source.

Both `send` and `recv` can operate in `async_op=True` mode, in which case they return an `AsyncWork` handle instead of the actual result. 
The `AsyncCollWork` will encompass the underlying broadcast or isend/irecv operations and allow the caller to wait for completion or chain events.

.. Synchronization and Usage Notes
.. ------------------------------------

.. Because each collective group in this design typically handles exactly two tasks for point-to-point communication, the code contains assertions to not misuse them (for example, `_get_peer_rank_in_p2p_group()` asserts the group size is 2). The design could be extended to larger groups for true collectives (like all-reduce among many tasks), but as written it focuses on p2p transfers, likely to implement things like parameter server or pipeline communications.


.. The collective module emphasizes careful coordination:

.. - It avoids deadlocks by sending small metadata first, allowing the receiver to prepare for the right type of follow-up receive.

.. - It logs debug information (if the logging level is set to debug) about sending and receiving events, including types and tensor counts, which can help in tracing communication issues.

.. - It uses busy-wait loops (with small sleeps) for waiting on conditions like group info availability or asynchronous work completion. This is a simple approach relying on the assumption that such waits are short (thanks to the use of fast coordination through Ray and local operations).


.. Finally, the `CollectiveGroup` ensures that resources are properly set up and cleaned:

.. - After a group’s master has set the port and everyone has initialized, the master resets the port info in the manager (so that if a new group of the same name were somehow created, it wouldn’t reuse an old port – typically group names are unique for each communication pair).

.. - The process groups created for NCCL and Gloo will remain in the PyTorch process global state. There is no explicit teardown in this module, but typically these are kept for the lifetime of the tasks (which is fine, as tasks are long-lived and may re-use groups multiple times for multiple sends/receives).

Summary
--------------

In summary, the **collective** component provides the engine for data transfer between tasks. It abstracts away the details of using PyTorch's distributed backends, managing multiple process groups to simulate send/receive, and optimizing for GPU transfers. 
Users of the framework typically invoke these via the `Task.send/recv` or channel operations, rather than calling `CollectiveGroup` directly.

