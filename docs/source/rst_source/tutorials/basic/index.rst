Basic Framework Usage
=====================

This chapter introduces the **static components** that underlie RLInf's dynamic scheduler.

- :doc:`YAML Configuration <yaml>`  
   Provides a comprehensive reference for all configuration parameters used across RLInf scripts. 

- :doc:`Worker and WorkerGroup <worker>`  
   Introduces the core unit in RLInf—the *worker*—which represents a specific modular role in the RL pipeline.  
   Multiple workers of the same type are grouped into a *WorkerGroup*, hiding distributed complexity and enabling seamless parallel execution.

- :doc:`Collective Communication <collective>`  
   Describes how workers efficiently exchange tensors through optimized point-to-point communication backends, leveraging low-level primitives like CUDA IPC and NCCL. TODO: CHECK

- :doc:`Channel <channel>`  
   Presents a higher-level abstraction for asynchronous data transfer, modeled as a producer-consumer queue.  


.. toctree::
   :hidden:
   :maxdepth: 2

   yaml
   worker
   collective
   channel
