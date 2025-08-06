NodeManager: Node Metadata Service
==================================

The `NodeManager` is a simple global manager that stores information about the cluster’s nodes and provides it to tasks on request. When the cluster is initialized, the `Cluster` launches the `NodeManager` actor with all the relevant data, so that any task can later retrieve cluster configuration without needing direct access to Ray’s node APIs.

Upon initialization (`NodeManager.__init__`), it is provided with:
- `nodes`: a list of `NodeInfo` objects, one for each node in the cluster. Each `NodeInfo` holds details such as the node’s Ray ID, IP address, number of GPUs, and number of CPUs.
- `num_gpus_per_node`: an integer indicating how many GPUs each node is expected to have (as configured when launching the cluster).
- `master_ip` and `master_port`: the network address and port designated as the "master" for collective communications (the port that will be used as the basis for creating process groups in torch distributed).

The NodeManager simply stores these in its attributes. It exposes the following methods (accessible via a proxy in tasks):
- `get_nodes()`: returns the list of `NodeInfo` for all nodes. A task might use this if it needs to know about all nodes and their resources.
- `get_master_ip()`: returns the master node’s IP address (useful for any operation that might need a stable rendezvous address or to identify if the current node is master).
- `get_master_port()`: returns the master port number. This is mainly used by the collective module when initializing distributed process groups, to know which port to use for rendezvous.
- `get_num_gpus_per_node()`: returns the number of GPUs expected per node. This can be used by placement strategies or tasks to understand the cluster layout.

The NodeManager does not have complex logic; it acts as a read-only repository. By having this data in a Ray actor, all tasks (which might be on different machines) can uniformly query the cluster setup without needing special privileges or environment variables. This is especially important for processes not started by the original driver, as they wouldn’t have direct access to the cluster’s configuration otherwise.

In short, the **NodeManager** provides a consistent view of the cluster’s node configuration to all parts of the system. It is one of the first things initialized by the `Cluster` and then used whenever tasks need to know “how many nodes/GPU do we have” or “what is the master address for communications.” Its simplicity and centralization help avoid scattering such configuration in global variables or passing them explicitly to every task.
