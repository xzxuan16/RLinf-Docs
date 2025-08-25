Worker Interface
===================================

This section provides a detailed introduction to the unified interface design of Worker and WorkerGroup in RLinf.  
The **Worker** is the fundamental unit of execution in RLinf. Different stages of RL training will inherit from it in order to achieve unified communication and scheduling.  
The **WorkerGroup** is a collection of multiple Workers, allowing users to avoid dealing with the complexities of distributed training directly.  
With WorkerGroup, users can more easily manage and schedule multiple Workers, enabling more efficient distributed training.

Worker
-------

.. autoclass:: rlinf.scheduler.worker.worker.Worker
   :members: worker_address, create_group, send, recv, send_tensor, recv_tensor, create_channel, connect_channel, broadcast
   :class-doc-from: init
   :exclude-members: __init__, __new__

WorkerGroup
-----------

.. autoclass:: rlinf.scheduler.worker.worker_group.WorkerGroup
   :members:
