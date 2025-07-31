Channel: Inter-Task Queuing
===========================

The channel module provides a high-level **producer-consumer queue** abstraction for tasks to exchange data asynchronously. 
A `Channel` allows one or more tasks to `put` items into a queue and others to `get` them, possibly accumulating batches of items. 

Channel Creation 
--------------------------------

A new channel is created by calling `Task.create_channel(channel_name, group_affinity=None, group_rank_affinity=None, maxsize=0)`. This method:

- Determines where the channel's queue should live. By default, if no affinity is provided, it uses the current task's own group and rank 
  (meaning the channel will be hosted on the same node and GPU as the task creating it). 

- Obtains the `TaskInfo` of the target task that will host the channel (using `TaskManager.get_task_info` on the affinity address).  TODO:
  It waits until that task is up and registered.

- Uses the host task's `node_id` and `gpu_id` to employ a fine-grained placement strategy to launch a dedicated channel task on that same resource. 
  The channel internally uses a special `_ChannelTask` class (a subclass of `Task`) that actually holds the queue. 

..   This class is decorated with `@TaskGroup`, so calling `_ChannelTask(...).create_group(cluster, name=channel_name, placement_strategy=placement)` will start an actor (Ray task) for the channel, 
..   named with the given channel_name.

- The result is a `TaskGroup` of size 1 (just one channel actor) and the `Channel` object then wraps around this. The channel actor's address will be `channel_name:0`.

Channel Connection
--------------------------------

To use an existing channel from another task, one calls `Task.connect(channel_name)`. This will look up the channel's actor by name (`channel_name:0` in the cluster's namespace) using `ray.get_actor`. 
It may wait and retry until the channel actor is found (meaning the channel has been created by someone). 
Once found, it retrieves the `maxsize` of the queue (by calling a remote method on the channel actor) and returns a `Channel` object linked to that actor. 

In both creation and connection, the `Channel` object is initialized with:

- A reference to the channel actor (the `_ChannelTask` running remotely).

- The current task that will use the channel (this is needed for send/recv operations).

- The channel's name and maximum size (0 means unbounded).

.. Queue Implementation
.. ---------------------

.. The channel's core is a queue that lives inside the channel actor. The `_ChannelTask` maintains a `asyncio.Queue` (encapsulated in a custom `PeekQueue` class) of `WeightedItem` objects. 
 
.. - `WeightedItem` is a small dataclass that holds an `item` and an associated `weight`. The weight is an application-defined integer priority or size for the item.
 
.. - `PeekQueue` extends `asyncio.Queue` to add a `peek()` method, which allows looking at the next item without removing it. 
..   This is important for implementing the batch retrieval logic (so we can decide if we have enough items for a batch before popping them).
 
.. .. - The queue is used in FIFO order by default (the code doesn’t explicitly perform any priority sorting on weight for insertion—if needed, the weight could be used to implement a priority queue, but here it’s mainly used to measure batch sizes).

.. Inside `_ChannelTask`, there are a few important fields:

.. - `_queue`: an instance of `PeekQueue[WeightedItem]`.

.. - `_batch_weight`: an integer threshold used by the batch retrieval logic (set via `set_batch_weight`).

.. - `_getters`: a deque of asyncio Futures representing tasks waiting on the queue (this is part of how the queue wakes up consumers when items become available).

.. The `PeekQueue.peek()` is implemented to wait until an item is available (similar to `get()` but without removal). If the queue is empty, it creates a Future and adds it to the `_getters` wait list, which will be resolved when an item is put.

Putting Items into the Channel
--------------------------------

To put an item, a task calls `channel.put(item)`. This operation involves two steps:

1. **Enqueue request**: The channel's actor needs to be notified that a new item is incoming. This is done by calling a remote method `_ChannelTask.put` asynchronously. 

.. When this method executes on the channel actor, it will perform a `recv` to get the actual data from the producer task. The `recv` uses the collective mechanism: 
.. the producer (in step 2 below) will send the item to the channel actor. Once received, the item is wrapped in a `WeightedItem` with the given weight and placed into the queue (with `await self._queue.put(...)` 
.. which may block if the queue is full and maxsize is reached). After successfully putting the item, `_wakeup_next` is called to notify one waiting getter (if any) that an item is available.


2. **Data transfer**: In parallel, after initiating the remote put, the producer task calls its own `send(item)` to actually transmit the item to the channel actor. 
   Under the hood, this will create a collective group between the producer and the channel actor and send the data (as described in the collective module TODO:). 
   The channel actor's recv call will match this send and retrieve the item, placing it into the queue


.. If async_op=False was specified (the default), Channel.put will wait for confirmation that the item was enqueued. It does so by wrapping the Ray future from put.remote in an AsyncChannelWork and calling .wait(). If async_op=True, it would return immediately with the AsyncChannelWork, allowing the producer to continue without blocking; the producer could then check later if the put completed. 

Getting Items from the Channel
-------------------------------

Symmetrically, a consumer task calls `channel.get()` to retrieve one item. This also has two steps:

1. **Dequeue request**: The task signals the channel actor that it wants an item. On the channel side, This will await an item from the queue. 
   Once an item is obtained, it immediately calls `send(item, dest_group, dest_rank)` to forward the actual data to the requesting task. 
   This send uses the collective communication—creating or using a group between the channel actor and the consumer task. The destination is given by dst_addr (which was the consumer's task address passed in). 
   This causes the data to be transmitted out of the channel actor's process to the consumer.

2. **Data reception**: Meanwhile, on the consumer side, it calls `recv(channel_name, 0)`. 
   This means the consumer starts waiting to receive data from the channel actor (group = channel's name, rank 0). 
   This recv will pair with the channel actor's send in the get method above.

The result of `get()` is the original item that some producer put into the channel, maintaining the order of the queue in the channel actor. 

Batch Retrieval
----------------

The channel also supports getting a batch of items at once using weights to determine how large the batch should be. 
This is done via the following function.

- `set_batch_weight(batch_weight)` tells the channel actor the target cumulative weight for a batch. 

- `get_batch()` triggers the channel actor to collect multiple items that have the total weight with `batch_weight`

This feature is useful for dynamically forming batches of experiences or tasks to process, where each item has a cost or size (the weight) and you want to process roughly uniform batch sizes. 

Summary
-------

The `Channel` component offers a distributed producer-consumer queue for task communication. 
It wraps the collective send/recv mechanism with an intuitive interface supporting priority and batching, 
enabling decoupled, asynchronous data flow—ideal for reinforcement learning scenarios with parallel data collection and batched consumption.