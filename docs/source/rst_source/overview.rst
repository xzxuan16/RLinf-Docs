.. _overview:

Overview
=========

RLInf is engineered as the **core engine** for reinforcement-learning post-training in the era of embodied intelligence.  
It merges an *integrated rendering-training-inference pipeline* with a *dual-backend training stack*, 
delivering state-of-the-art performance from academic prototyping to industrial-scale deployment.


.. Motivation
.. ----------

.. Bridging the gap from web-scale pre-training to real-world embodiment demands:

.. * High-fidelity simulators able to saturate modern GPUs.
.. * Scalable optimisation algorithms that keep thousand-GPU clusters busy.
.. * A unified interface that hides heterogeneous back-ends and schedulers.

.. RLInf tackles these challenges through a **co-design** of simulation, training runtime and cluster scheduling.

Dual-Backend Training Stack
---------------------------


+-----------------------------------------------+------------------------------+---------------------------------------------------------------+
| Purpose                                       | Backend Engine               | Key Characteristics                                           |
+===============================================+==============================+===============================================================+
| Lightweight experimentation                   | *Hugging Face* + **FSDP**    | • Works on a single machine or small cluster.                 |
|                                               |                              | • Zero-code-change fine-tuning up to tens of billions         |
|                                               |                              |   parameters.                                                 |
+-----------------------------------------------+------------------------------+---------------------------------------------------------------+
| Large-scale production training               | Megatron-LM_ + SGLang_       | • 3-D parallelism (tensor, pipeline, sequence).               |
|                                               |                              | • Converges trillion-parameter models in days.                |
+-----------------------------------------------+------------------------------+---------------------------------------------------------------+


Integrated Rendering–Training–Inference
---------------------------------------

RLInf introduces **render-train-serve unification**, bringing simulator, learner and inference engine into the same process when beneficial.

* **Separated** – Simulator and learner run on distinct GPU sets.
* **Shared** – Simulator and learner co-locate for minimal latency.
* **Hybrid** – A scheduler decides per-task colocation, achieving up to *X×* throughput over prior systems.

Embodied Intelligence Support
-----------------------------

RLInf ships with adapters for leading VLA models and embodied simulators:

* **VLA models**: `OpenVLA`_, `OpenVLA-OFT`_, :math:`\pi_0`_
* **Simulators**: `IsaacLab`_, `ManiSkill3`_, `LIBERO`_

Together they cover **100+** tasks spanning manipulation, locomotion and mobile navigation.

High-Throughput Communication Layer
-----------------------------------

An adaptive mix of **CUDA-IPC** and **NCCL** balances GPU transfer queues, while dynamic group management scales seamlessly to **1 000+ GPUs**.

Adaptive Scheduling
-------------------

A built-in **online configuration optimiser** monitors throughput and memory pressure, reacting within seconds by redistributing GPUs, retuning micro-batch sizes and resizing communication groups—improving average utilisation by **X %** and trimming wall-clock time by **Y %**.

.. _pi_0: https://github.com/lucidrains/pi-zero-pytorch
.. _OpenVLA: https://github.com/openvla/openvla
.. _OpenVLA-OFT: https://github.com/moojink/openvla-oft
.. _IsaacLab: https://github.com/isaac-sim/IsaacLab
.. _ManiSkill3: https://github.com/haosulab/ManiSkill
.. _LIBERO: https://github.com/Lifelong-Robot-Learning/LIBERO
.. _Megatron-LM: https://github.com/NVIDIA/Megatron-LM
.. _SGLang: https://github.com/sgl-project/sglang
