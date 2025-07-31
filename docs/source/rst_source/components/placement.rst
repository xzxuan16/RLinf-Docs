Placement Strategies
====================

The placement module defines how tasks are distributed across the hardware resources (nodes and GPUs) of the cluster. 
A **PlacementStrategy** encapsulates a particular policy for assigning tasks to GPUs and nodes. 
This allows flexibility in how a set of tasks (e.g., a `TaskGroup`) utilizes the available GPUs. 
For each strategy, a list of `Placement` objects is returned by the `get_placement(num_gpus_per_node, isolate_gpu)` method. Each `Placement` includes:

+---------------------------+----------------------------------------------+
| Property                  | Description                                  |
+===========================+==============================================+
| ``rank``                  | Unique global task index                     |
+---------------------------+----------------------------------------------+
| ``node_id``               | Identifier of the node where the task runs   |
+---------------------------+----------------------------------------------+
| ``node_rank``             | Index of the node within the cluster         |
+---------------------------+----------------------------------------------+
| ``local_gpu_id``          | GPU index assigned to the task on that node  |
+---------------------------+----------------------------------------------+
| ``local_rank``            | Task’s index among tasks on the same node    |
+---------------------------+----------------------------------------------+
| ``local_world_size``      | Total number of tasks on the same node       |
+---------------------------+----------------------------------------------+
| ``cuda_visible_devices``  | List of GPU IDs visible to the task          |
+---------------------------+----------------------------------------------+
| ``isolate_gpu``           | Whether the task is restricted to those GPUs |
+---------------------------+----------------------------------------------+

Below are the provided strategies:

- **PackedPlacementStrategy** (default): This strategy places one task per GPU in a simple “fill every GPU” order. It starts from a master node (default node 0) and assigns tasks to GPUs 0,1,… on that node until it runs out of GPUs, then moves to the next node. 

.. Each task gets a single GPU. If `isolate_gpu` is true, each task will only see its one GPU; if false, the task can see all GPUs on its node (though it is intended to primarily use the one it was assigned). The result is a list of placements where `rank` increases sequentially and corresponds directly to an absolute GPU index in the cluster. For example, with 2 nodes each having 4 GPUs, and 8 tasks, ranks 0-3 might be on node 0’s GPUs 0-3, and ranks 4-7 on node 1’s GPUs 0-3. This close-packed strategy is the simplest and is the default when no specific placement is given.

- **ChunkedPlacementStrategy**: In this strategy, each **task process can use multiple GPUs** as a chunk. You specify `num_gpus_per_process` (the size of the chunk). The strategy will allocate tasks such that each task has a contiguous block of GPUs on a node. 

.. For example, if `num_gpus_per_process=2` on a node with 8 GPUs, a single task could be assigned GPUs [0,1], the next task [2,3], and so on. It effectively reduces the number of processes by grouping GPUs into chunks for each process. This strategy requires `isolate_gpu=True` to function correctly (ensuring a process only “sees” its chunk of GPUs). The placement algorithm for chunked strategy calculates a global GPU index for each process (rank * num_gpus_per_process) and derives the node and local GPU indices from that. It stops when it reaches the total number of nodes or cannot fit another full chunk on the remaining GPUs. The `Placement` entries for chunked tasks will list multiple CUDA devices in the `cuda_visible_devices` field (equal to the chunk size). This is useful for scenarios like data parallel training where each worker might leverage multiple GPUs internally (e.g., model parallelism within a single task).

- **StridedPlacementStrategy**: This strategy also allows multiple GPUs per process but distributes them in a strided pattern across the GPU indices. It takes parameters `stride` and `num_gpus_per_process`. The GPUs are conceptually divided into groups, each group spanning a number of GPUs equal to `stride * num_gpus_per_process`. Within each group, GPUs are assigned to tasks such that there is a fixed stride between the GPUs of consecutive tasks. 

.. For example, consider 1 node with 8 GPUs, `num_gpus_per_process=2` and `stride=2`: GPUs can be thought of as indexed 0..7. The strategy will form groups of size `stride * num_gpus_per_process = 2*2 = 4` GPUs. Group 0 might cover GPUs 0-3 and group 1 covers GPUs 4-7. Within each group, tasks are created such that task 0 takes GPUs [0,2] and task 1 takes GPUs [1,3] (stride of 2 between GPUs in the same task). In group 1, task 2 takes [4,6], task 3 takes [5,7]. The effect is interleaving GPU assignments among tasks. Strided placement can be useful for certain parallel algorithms that prefer evenly spaced GPU indices, or when trying to avoid neighboring GPUs being on the same task due to hardware locality or bandwidth considerations. This strategy also demands `isolate_gpu=True`, and it ensures that each process’s GPUs respect the stride and count constraints. The number of tasks created will be `(num_nodes * num_gpus_per_node) / (stride * num_gpus_per_process)` (which should be an integer—if it’s not, the strategy configuration is invalid for the given cluster size).

- **FineGrainedPackedPlacementStrategy**: This strategy allows precise selection of how many GPUs to use in total and from where to start. It is useful when you want to run a job on a subset of the cluster’s GPUs rather than all available ones. The strategy will allocate tasks on GPUs starting from the specified `master_node` and `master_gpu`, then continue sequentially (as if using packed strategy) until it has assigned `num_gpus` tasks.

.. It takes `master_node` (the starting node index, default 0), `master_gpu` (the starting GPU index on that master node), and `num_gpus` (the total number of GPUs to utilize across the cluster). The strategy will allocate tasks on GPUs starting from the specified `master_node` and `master_gpu`, then continue sequentially (as if using packed strategy) until it has assigned `num_gpus` tasks. For example, if `master_node=0, master_gpu=2, num_gpus=3` on a cluster where each node has 4 GPUs, this would create tasks on GPU 2 and GPU 3 of node 0, and then GPU 0 of node 1 (assuming node 0 had only 2 GPUs left after starting at index 2). Each task is one GPU (similar to packed), but the total world size is limited to `num_gpus`. This strategy can be combined with `isolate_gpu=False` if you want each task to still see all GPUs on its node (though typically one might isolate anyway for consistency). Fine-grained placement is essentially a “partial packed” strategy for cases where you don’t want to use the entire cluster or want to offset where usage begins.

In summary, the **placement** component ensures that tasks are deployed in a way that matches the desired parallel execution pattern and resource usage policy, which is crucial for performance and correctness in distributed training.
