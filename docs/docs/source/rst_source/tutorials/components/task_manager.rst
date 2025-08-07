TaskManager: Global Task Registry
=================================

The `TaskManager` is a global service (a manager actor) that keeps track of all tasks in the system and their hierarchical relationships. Its main purpose is to allow any part of the system to query information about tasks by address, and to maintain the parent-child structure of tasks (for nested task groups).

**TaskNode Tree Structure**  
At the heart of the TaskManager is a tree representation of tasks called `TaskNode`. Each `TaskNode` holds a `TaskAddress` and an optional `TaskInfo` (if the task is running). It also contains a list of child `TaskNode` objects. The tree structure mirrors the way tasks are organized in groups:
- A **root TaskNode** represents a top-level task group (its `TaskAddress` may correspond to the group name with no ranks, or internally, `parent_address` might be stored as None for the root).
- Child nodes represent tasks that were spawned by a parent task (for example, if a root task group spawns sub-tasks, those sub-tasks will appear as children of the root’s node).

The `TaskNode.find_node(root, target_address)` class method traverses the tree to find a node with a matching address. It uses the rank path in the `TaskAddress` to navigate down from the root. If at any point it cannot find a matching child for a rank, it concludes the task is not in that subtree.

**Registering Tasks**  
When a new task starts, it calls `TaskManager.register_task(task_address, task_info)`. This method will insert the task into the TaskManager’s tree:
- It first computes the `parent_address` as `task_address.get_parent_address()`. For a root task (one whose address has no parent, i.e., it’s the first rank in its group), `parent_address` will be `None`.
- If `parent_address` is `None`, the new task is considered a root task group. The TaskManager will create a new `TaskNode` with `parent_address=None` and the provided `task_info`, and append it to its list of `_root_tasks`. (There is a slight nuance: the code actually does `self._root_tasks.append(TaskNode(parent_address, task_info))`. In this context, `parent_address` is None, so the root node’s own `_task_address` is None. This effectively means a root placeholder node is created. Immediately after, one would expect it to add the task as a child of this placeholder. However, the implementation might rely on the next part for non-None parent, or treat the root differently.)
- If `parent_address` is not None, the TaskManager tries to find the parent in one of the existing root subtrees. It loops through each root in `_root_tasks` and uses `find_node(root, parent_address)` to locate the node corresponding to the parent. If found, it calls that node’s `add_child(rank, task_info)`.
- `TaskNode.add_child(rank, task_info)` creates a new `TaskAddress` by extending the current node’s address with the child rank (via `get_child_address(rank)`), then creates a `TaskNode` for the child. It inserts this child into the parent’s `_nodes` list in sorted order by rank. Using `bisect.insort` ensures children are ordered by their rank number, which can be helpful for consistent traversal or debugging.
- In case the parent wasn’t found among existing trees (which could happen if the parent itself hasn’t been registered yet as a root), the TaskManager will create a new root node using the parent_address (even though that parent is not a root in the true sense, this situation is unusual and likely an artifact of how tasks are launched out-of-order). It asserts that this new root has no children initially, then adds the child to it and appends this structure to `_root_tasks`. Essentially, it ensures no task registration is lost even if the parent wasn’t known up front.

Through this registration process, the TaskManager maintains an up-to-date map of all running tasks and their hierarchy. Every call to `register_task` corresponds to a task calling `_manager_proxy.register_task(self._task_address, self._get_task_info())` during its initialization (in `Task._init_ray_and_proxies`). The `TaskInfo` stored contains the runtime details of the task.

**Querying Task Information**  
The main query method is `TaskManager.get_task_info(task_address)`. Given a `TaskAddress`, it searches through each root in `_root_tasks` for a node that matches the address (using `find_node`). If found, it returns the `TaskInfo` stored in that node. If not found, it returns `None`.

This lookup is used in various parts of the system when a task needs to know about another task:
- The collective module uses it to gather `TaskInfo` for all tasks in a group before forming a communication group (so it knows peers’ IPs and GPU availability).
- The channel creation waits on `TaskManager.get_task_info(affine_task_address)` to ensure the target task (where the channel should live) is up and running.
- In debugging or logging, one could traverse the task tree for introspection (the `TaskNode.__str__` provides a simple text representation of the hierarchy, listing tasks by their addresses indented by depth).

**Considerations**:
- The TaskManager is not a performance bottleneck because these operations are relatively infrequent (task registration happens at startup, and lookups happen only during setup of communications or channels). The tree is in memory on the manager actor and is not expected to grow extremely large under typical usage (it would scale with the number of tasks in the system).
- By structuring data as a tree, it naturally encodes the grouping: tasks of one group will appear under their common parent node. If tasks spawn sub-tasks (like a hierarchy), that is also captured. This is more informative than a flat list of tasks.
- The manager does not currently provide methods to remove tasks from the registry when they terminate. If tasks are short-lived or if many tasks are created and destroyed, the registry might contain stale entries. In this framework, however, tasks (especially those in TaskGroups) often live for the duration of a training run, so cleanup might be handled outside or not be critical.

In summary, the **TaskManager** serves as a directory of all tasks. By mapping each `TaskAddress` to a `TaskInfo` and maintaining parent-child relationships, it enables other components to resolve addresses to live actor references or properties (like IP or GPU id). This is essential for setting up direct communications and for overall coordination in a distributed setting.
