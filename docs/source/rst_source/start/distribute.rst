Multi-node Training
===================

This guide shows how to launch a **4-node Ray cluster** (each node
has **8 GPUs**) and run distributed RL training on
the *math* task with the
`DeepSeek-R1-Distill-Qwen-1.5B <https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B>`_
model.  The same procedure scales to any number of nodes / GPUs once
you adjust the YAML config correspondingly.


Prerequisites
-------------

* Clone RLinf to a shared filesystem (e.g., NFS) that each node can read from.
* CUDA and driver versions identical across the cluster.
* ``ray`` installed on **every** node (``pip install ray[default]``).


Step 1: Start a Ray Cluster
----------------------------

Clean up *old* cached state first:

.. code-block:: bash

   rm -f ray_utils/ray_head_ip.txt

Open a shell on *each* node and run:

==========================================  ==========================
node index                                  command
==========================================  ==========================
0 (head)                                    ``RANK=0 bash ray_utils/start_ray.sh``
1                                           ``RANK=1 bash ray_utils/start_ray.sh``
2                                           ``RANK=2 bash ray_utils/start_ray.sh``
3                                           ``RANK=3 bash ray_utils/start_ray.sh``
==========================================  ==========================


Once the scripts run successfully, the terminal on the **head node** should display output similar to the following (for simplicity, we only show the example of 2 nodes with 16 GPUs):

.. raw:: html

   <img src="https://github.com/user-attachments/assets/7d74a914-6a02-47b3-aebe-f62f505d6eb6" width="800"/>

On each **worker node**, the terminal should display:

.. raw:: html

   <img src="https://github.com/user-attachments/assets/d1b3ca82-0449-4720-a9fc-fb4265944273" width="800"/>

After all four startup scripts print *Ray started*, **remain** in the head node terminal and verify the total cluster size (in this example, ``4 × 8 = 32`` GPUs):

.. code-block:: bash

   bash ray_utils/check_ray.sh 32

.. note::

   The argument to ``check_ray.sh`` must equal the product of
   ``num_nodes × num_gpus_per_node``. 

If successful, your terminal should show:

.. raw:: html

   <img src="https://github.com/user-attachments/assets/28e8d7e3-0794-4072-911c-bbd7b509d107" width="800"/>

Note: For simplicity, the images in this example only show a 2-node setup with 16 GPUs.


Step 2: Launch Training Tasks
------------------------------------

Here we provide startup examples in two modes: collocated mode and disaggregated mode.

Collocated 
^^^^^^^^^^^^^^

Every training stage (rollout, inference, actor) shares **all GPUs**.
Edit the sample YAML:

.. code-block:: yaml

   # examples/math/config/qwen2.5-1.5b-grpo-megatron.yaml
   cluster:
     num_nodes: 4          # adapt to your cluster
     num_gpus_per_node: 8
     component_placement:
       actor,rollout: all  # “all” means the whole visible GPU set

Launch from the head node:

.. code-block:: bash

   bash examples/math/run_main_math_grpo_megatron.sh \
        qwen2.5-1.5b-grpo-megatron


Disaggregated
^^^^^^^^^^^^^^^^^^

Different stages receive disjoint GPU ranges,
allowing fine-grained pipeliningng. Edit the pipeline YAML:

.. code-block:: yaml

   # examples/math/config/qwen2.5-1.5b-grpo-megatron-pipeline.yaml
   cluster:
     num_nodes: 4
     num_gpus_per_node: 8
     component_placement:
       rollout:    0-19        # 20 GPUs
       inference:  20-23       # 4  GPUs
       actor:      24-31       # 8  GPUs

* ``rollout + inference + actor`` **must equal** the total GPU count
  (here ``32``).
* Ranges are inclusive.

Start the job:

.. code-block:: bash

   bash examples/math/run_main_math_pipeline_grpo_megatron.sh \
        qwen2.5-1.5b-grpo-megatron-pipeline