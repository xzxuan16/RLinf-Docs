Installation
============

Hardware Requirements
---------------------

The following configuration has been thoroughly tested.

+-----------------------------------------------+---------------------------------------------------------------+
| Resource                                      | Specification                                                 |
+===============================================+===============================================================+
| GPU                                           | XXX × XXX GB HBM per node                                     |
+-----------------------------------------------+---------------------------------------------------------------+
| CPU                                           | XXX cores per node                                            |
+-----------------------------------------------+---------------------------------------------------------------+
| System memory                                 | XXX TB per node                                               |
+-----------------------------------------------+---------------------------------------------------------------+
| High-speed interconnect                       | XXX Gbps (e.g. NVSwitch / InfiniBand / RoCE)                  |
+-----------------------------------------------+---------------------------------------------------------------+
| Local storage (single-node)                   | XXX TB                                                        |
+-----------------------------------------------+---------------------------------------------------------------+
| Shared storage (distributed experiments)      | XXX TB (NAS / SAN / Ceph)                                     |
+-----------------------------------------------+---------------------------------------------------------------+

Software Requirements
---------------------

+-----------------------------------------------+---------------------------------------------------------------+
| Component                                     | Version / Notes                                               |
+===============================================+===============================================================+
| Operating System                              | Linux XXX (tested)                                            |
+-----------------------------------------------+---------------------------------------------------------------+
| NVIDIA Driver                                 | XXX                                                           |
+-----------------------------------------------+---------------------------------------------------------------+
| CUDA Toolkit                                  | XXX                                                           |
+-----------------------------------------------+---------------------------------------------------------------+
| Docker Engine                                 | XXX or later *(Docker workflow)*                              |
+-----------------------------------------------+---------------------------------------------------------------+
| Conda                                         | XXX *(Conda workflow)*                                        |
+-----------------------------------------------+---------------------------------------------------------------+
| Python                                        | ≥ 3.9                                                         |
+-----------------------------------------------+---------------------------------------------------------------+





Create an Environment
---------------------

We recommend **one** of the two methods below.

Method 1 — Docker (reproducible & portable)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. **Pull or build the Docker image**

   .. code-block:: bash

      # pull a pre-built image
      docker pull RLInf:latest

#. **Run the container**

   .. code-block:: bash

      docker run -it --rm --gpus all \
        --shm-size 2g \
        -v $(pwd):/workspace/megatron-RLInf \
        -v XXX_DATASET_DIR:/workspace/dataset \
        -v XXX_TOKENIZER_DIR:/workspace/tokenizer \
        --name RLInf \
        RLInf:latest /bin/bash

   Inside the container you should see the project under `/workspace/megatron-RLInf`.

Method 2 — Conda + Pip (bare-metal or custom VMs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. **Create a new Conda environment**

   .. code-block:: bash

      conda create -y -n RLInf python=3.9
      conda activate RLInf


#. **Install RLInf and its dependencies**

   .. code-block:: bash

      pip install -r requirements.txt  # if you generated one
      export PYTHONPATH=$(pwd)         # set PYTHONPATH so that infini-rl can be correctly imported

#. **Verify the installation**

   .. code-block:: bash

      python -c "import infinigence_rl, torch; print('RLInf', infinigence_rl.__version__); print('CUDA available', torch.cuda.is_available())"

If the version prints successfully and `torch.cuda.is_available()` returns `True`, you are ready to start training.
