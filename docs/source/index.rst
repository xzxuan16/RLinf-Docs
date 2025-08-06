.. image:: _static/logo_white.svg
   :width: 500px
   :align: center
   :class: logo-img

Welcome to **RLinf**!
=====================

RLinf is a flexible, scalable and open-source infrastructure designed for reinforcement-learning (RL) post-training of **foundation models** — including large language models (LLMs), vision-language models (VLMs), and vision-language-action (VLA) models.  

.. RLinf is engineered as the **core engine** for RL post-training in the era of embodied intelligence.  
.. It merges an *integrated rendering-training-inference pipeline* with a *dual-backend training stack*, delivering state-of-the-art performance from academic prototyping to industrial-scale deployment.

RLinf supports:

- **Embodied Intelligence**
  
  - Native adapters for VLA models: `OpenVLA`_, `OpenVLA-OFT`_, :math:`\href{https://github.com/Physical-Intelligence/openpi}{\pi_0}`
  - Plug-and-play connectors for simulators: `IsaacLab`_, `ManiSkill3`_, `LIBERO`_
  - First RL fine-tuning of the :math:`\pi_0` model family

- **Hybrid Execution Modes**
  
  - Automatic switching between *task-collocated* and *task-separated* placements to maximize GPU utilization
  - Boosts training throughput by **TODO** over prior systems

- **Flexible Backend Integration**
  
  - **Small-scale validation**: Hugging Face + FSDP for lightweight experiments
  - **Large-scale training**: `Megatron-LM`_ + `SGLang`_ for billion- to trillion-parameter convergence

- **Adaptive Communication & Scheduling**
  
  - **TODO**

- **SOTA perfermance**


Our goal is to unleash boundless computing resources, integrate mainstream development frameworks, and streamline the entire development workflow, empowering developers to make RL post-training accessible to everyone!

* Related publication : `PAPER TITLE <TODO>`_
* Source code : `GitHub repository <TODO>`_


.. _OpenVLA: https://github.com/openvla/openvla
.. _OpenVLA-OFT: https://github.com/moojink/openvla-oft
.. _IsaacLab: https://github.com/isaac-sim/IsaacLab
.. _ManiSkill3: https://github.com/haosulab/ManiSkill
.. _LIBERO: https://github.com/Lifelong-Robot-Learning/LIBERO
.. _pi_0: https://github.com/Physical-Intelligence/openpi
.. _Megatron-LM: https://github.com/NVIDIA/Megatron-LM
.. _SGLang: https://github.com/sgl-project/sglang


.. toctree::
  :maxdepth: 2
  :hidden:
  :caption: Quickstart

  rst_source/start/index

.. toctree::
  :maxdepth: 2
  :hidden:
  :caption: Tutorials

  rst_source/tutorials/index

.. toctree::
  :maxdepth: 2
  :hidden:
  :caption: Example Gallery

  rst_source/examples/index

.. toctree::
  :maxdepth: 2
  :hidden:
  :caption: API Reference

  rst_source/apis/index

.. toctree::
  :maxdepth: 2
  :hidden:
  :caption: Miscellaneous

  rst_source/misc/index

.. toctree::
  :maxdepth: 1
  :hidden:
  :caption: FAQ

  rst_source/faq



.. Embodied Intelligence Support
.. -----------------------------

.. RLinf is the **first RL infrastructure purpose-built for embodied intelligence**, positioning itself as the cornerstone of the field.

.. * Native adapters for VLA models such as `OpenVLA`_, `OpenVLA-OFT`_, and :math:`\href{https://github.com/Physical-Intelligence/openpi}{\pi_0}`
.. * Plug-and-play connectors for leading simulators: `IsaacLab`_, `ManiSkill3`_, and `LIBERO`_  
.. * First to accomplish RL fine-tuning of the :math:`{\pi_0}` model family

.. These integrations cover **TODO:** embodied tasks including: TODO:


.. Extreme Render-Train-Serve Integration
.. --------------------------------------

.. * Efficiently bridges CPU and GPU based simulators, ensuring high throughput across hundreds of embodied tasks.  
.. * Provides **separated, shared, and hybrid** execution modes. A hybrid scheduler automatically switches between *task-collocated* and *task-separated* placement to maximize GPU utilization, 
..   boosting training throughput by **TODO:** over prior systems.


.. Flexible Backend Integration
.. ----------------------------

.. Swap backends without changing a single line of user code. RLinf supports:

.. * **Small-scale validation** - Hugging Face + FSDP for lightweight, easy-to-deploy experimentation.  
.. * **Large-scale training** - Megatron-LM + SGLang for billion to trillion parameter convergence.

.. +-----------------------------------------------+------------------------------+---------------------------------------------------------------+
.. | Purpose                                       | Backend Engine               | Key Characteristics                                           |
.. +===============================================+==============================+===============================================================+
.. | Lightweight experimentation                   | Hugging Face + FSDP          | • Works on a single machine or small cluster.                 |
.. |                                               |                              | • Zero-code-change fine-tuning up to tens of billions         |
.. |                                               |                              |   parameters.                                                 |
.. +-----------------------------------------------+------------------------------+---------------------------------------------------------------+
.. | Large-scale production training               | Megatron-LM + SGLang         | • 3-D parallelism (tensor, pipeline, sequence).  TODO:        |
.. |                                               |                              | • Converges trillion-parameter models in days.                |
.. +-----------------------------------------------+------------------------------+---------------------------------------------------------------+



.. Under-the-Hood Optimizations
.. -----------------------------
.. #TODO:

.. High-Throughput Communication
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. * Adaptive **CUDA-IPC / NCCL** channels with multi-lane concurrency and GPU queue load balancing.  
.. * Fast communicator resizing keeps thousand-GPU clusters running stably and efficiently.

.. Adaptive Scheduling
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. * **Second-scale** cluster auto-scaling enables on-the-fly GPU allocation and migration.  
.. * A built-in online configuration optimizer tunes micro-batch size, gradient accumulation, and parallelism degree, lifting overall utilization by **X %**.

.. SOTA Benchmark-Proven
.. ---------------------
.. #TODO:
.. *(coming soon)*


.. Table of Contents
.. ------------------
