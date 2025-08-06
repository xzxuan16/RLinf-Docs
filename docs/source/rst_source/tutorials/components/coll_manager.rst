CollectiveManager: Collective Group Registry
============================================

The `CollectiveManager` is a global manager that keeps track of collective communication groups and their metadata. Its role is to coordinate the setup of communication (especially point-to-point or collective groups) across multiple tasks by providing a shared lookup for group information, such as group membership and rendezvous ports.

**CollectiveGroupInfo**  
At the core of the CollectiveManager is the `CollectiveGroupInfo` class. This is a simple container for:
- `group_name`: a unique identifier for the collective group.
- `tasks`: a list of `TaskInfo` objects for each task in the group. This list defines the members of the group and their properties (addresses, node locations, etc.).
- `master_addr`: the IP address of the master node for this group (usually the IP of the first task in the list, which acts as the host for initialization).
- `master_port`: an optional integer that will be filled in with a port number when the group initializes its process groups. Initially, when a group is registered, this is `None`. Later, one task (rank 0) will choose a free port and update this field via the manager so others can retrieve it.

It also computes `world_size` as the number of tasks. For equality checking, all fields except `master_port` are considered (two CollectiveGroupInfo are equal if they describe the same group name with the same members and master address; the master_port can differ or be unset and is not part of equality to allow it being filled in later).

**Registering and Retrieving Groups**  
The `CollectiveManager` maintains a dictionary `_name_info_map` mapping group names to `CollectiveGroupInfo` objects.
- When a task wants to create or join a collective group, it will call `CollectiveManager.get_collective_group(name)`. If the name is not present, `None` is returned.
- The first task to create the group will gather the necessary info and call `CollectiveManager.register_collective_group(group_info)`. This inserts the info into the map. There is a safety check: if a group with the same name already exists but with different composition (different tasks list or world size), a `ValueError` is raised to prevent inconsistent groups from being registered under the same name.
- Subsequent tasks that call `get_collective_group(name)` will now receive the `CollectiveGroupInfo` that was stored.

This simple interface allows a handshake: one task registers, others retrieve. The design assumes that group names are unique for each communication context (the framework typically auto-generates names that include task addresses, which makes collisions unlikely except in misuse).

**Master Port Coordination**  
One of the challenges in setting up a new torch distributed process group (especially with Gloo or NCCL backends) is agreeing on a network port for rendezvous. The CollectiveManager assists with this:
- When a group is being initialized for actual communication (in `CollectiveGroup._init_p2p_process_group`), the rank 0 task will call `CollectiveManager.set_master_port_info(group_name, port)` with a chosen free port number. This writes the port into the stored CollectiveGroupInfo for that group.
- Other ranks will call `CollectiveManager.get_master_port_info(group_name)` in a loop until it returns a non-None value, indicating that the master has published the port. This is a form of barrier synchronization using the manager as the medium.
- After the process group is set up, rank 0 may call `CollectiveManager.reset_master_port_info(group_name)` to clear the port. This isn’t strictly necessary for correctness, but it prevents reusing the same port for another group with the same name in the future. In practice, group names are unique per communication pair, so reusing a name is uncommon unless perhaps tasks are reusing addresses over time.

**Usage Example**: Suppose tasks A and B want to establish a direct communication channel (point-to-point). Task A (with the lexicographically smaller address, hence chosen as master) will:
1. See no existing entry for group “cg-A-B” in `get_collective_group`, so it creates a `CollectiveGroupInfo(group_name="cg-A-B", tasks=[infoA, infoB], master_addr=ip_of_A)` and calls `register_collective_group` with it.
2. Task B will call `get_collective_group("cg-A-B")`, find the info (populated by A), and now knows it’s member of a group of size 2 with master address = ip_of_A.
3. When they proceed to init the backend, Task A finds a free port P and calls `set_master_port_info("cg-A-B", P)`. Task B loops on `get_master_port_info("cg-A-B")` until it sees P.
4. Both then use that master_addr and master_port P to call `dist.init_process_group` (for NCCL/Gloo as needed). Once done, Task A optionally calls `reset_master_port_info` to clear the stored port.

This coordination ensures that even if tasks start the group setup at slightly different times, they will synchronize on the critical information (membership and port).

**Scope**: The CollectiveManager does not manage the communications themselves; it doesn’t open sockets or launch processes for collectives. It purely holds metadata. This keeps it lightweight. The actual heavy lifting is done in the `CollectiveGroup` within each task process.

Because each `CollectiveGroupInfo` includes the list of `TaskInfo`, tasks can also use the manager to get information about peers (for instance, which GPUs they have). However, in the current design, tasks typically already gathered that info before registering the group (as seen in `Collective.create_collective_group`).

In summary, the **CollectiveManager** is the directory and synchronization service for distributed communication groups. By centralizing group metadata and providing a way to share a rendezvous port, it enables tasks to set up direct communication channels in a distributed environment without race conditions or hard-coding addresses. It is an integral part of making the dynamic send/recv collective operations work reliably.
