Manager Proxy and Base Manager
==============================

The manager module provides a base class (`Manager`) for globally accessible managers and a `ManagerProxy` helper to interact with those managers from any task process. 
These managers are implemented as Ray actors (running in the background on the cluster) that hold shared state. 
The proxy allows tasks to call the manager's methods as if they were local, abstracting away the Ray remote call details.

Manager Base Class
--------------------

`Manager` is designed to be subclassed for specific purposes (e.g., `TaskManager`, `NodeManager`, `CollectiveManager`). Key features of `Manager`:

- It defines a class attribute `MANAGER_NAME` which should be set in subclasses to a unique name for that manager type (used to register/retrieve the actor by name in Ray).

- It holds a class variable `proxy` and `PID` which are used to cache a proxy object per process.

The class method `Manager.get_proxy()` is the primary way tasks obtain a handle to the manager's functionality. 
When called, it checks if a proxy already exists and if it was created in the current OS process (comparing stored PID with `os.getpid()`). 
If not, it creates a new `ManagerProxy` for that class and updates the cached `proxy`. 
This ensures that each worker process (which may correspond to a Ray actor running a Task) has its own proxy instance, but they all talk to the single remote manager actor.

ManagerProxy
-------------

A `ManagerProxy` is initialized with a reference to the manager class (subclass of `Manager`). 
Its constructor tries to get an existing Ray actor by the name `manager_cls.MANAGER_NAME` in the current Ray namespace. 
If the actor isn't found, it raises an error (which usually means something is wrong in cluster initialization; normally the `Cluster` would have started the manager actor already). 
On success, it stores the actor handle (`self._manager`).

The clever part of `ManagerProxy` is that it dynamically exposes the manager's methods:

- It collects all callable attributes of the manager class (excluding private methods starting with `_`).

- For each such method name, it creates a `ProxyMethod` object that, when called, will in turn call the remote actor's corresponding method and `ray.get` the result. 

- This dynamic attachment is done in the `ManagerProxy.__init__` by iterating over `sched_fun_list`. Each `ProxyMethod` is a simple callable class capturing the function name and the actor handle.

With this design, using a manager from a task is straightforward. For example:

.. code-block:: python  

    task_manager = TaskManager.get_proxy()
    info = task_manager.get_task_info(some_address)

Here `get_task_info` is not a local function but a proxy to the remote `TaskManager` actor's method of the same name. 
The `ManagerProxy` takes care of sending the request to the actor and waiting for the reply. 
This pattern avoids requiring the user code to manually get actor handles and call `.remote()` and `ray.get()` for each manager interaction. 

Summary
--------

In summary, the manager base and proxy provide a clean way to use global stateful services in a distributed setting. 
Instead of passing around actor handles or using static globals, tasks simply request a proxy when needed. 