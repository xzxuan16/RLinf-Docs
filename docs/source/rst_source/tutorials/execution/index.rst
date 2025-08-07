Flexible Execution and Scaling
==============================

This chapter dives deeper into RLInf's **dynamic execution** process, explaining how the framework manages and schedules large-scale distributed training.

- :doc:`Placement Strategies <placement>` 
   Describing how GPU resources are strategically planned and allocated across tasks.

- :doc:`Cluster and Resource Management <cluster>` 
   Introducing the globally unique cluster object, which serves as a centralized descriptor of the entire distributed training job, coordinating roles and connections among all nodes.

- :doc:`Distribute Training Launch <distribute>` 
   Providing a step-by-step guide to launching distributed training jobs, with an emphasis on multi-node training process.

- :doc:`Fine-Grained Pipelining <pipeline>` 
   Explaining how to construct and execute fine-grained, multi-stage pipelines that boost training throughput and minimize idle time across workers.


.. toctree::
   :hidden:
   :maxdepth: 2

   placement
   cluster
   distribute
   pipeline
