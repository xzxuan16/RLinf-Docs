Start Your First Training Job
=============================

This page explains how to launch **GRPO** training with the provided `bash` script and *which* parameters you must customise.

We recommend trying **single-node × 8 GPUs** first; distributed multi-node tweaks are identical except for setting `NNODES`, `MASTER_ADDR`, and network ports.

Prepare Data & Model
--------------------

1. **Dataset** – download or preprocess:

   .. code-block:: bash

      # TODO:
      python tools/download_dataset.py \
          --name XXX_DATASET_NAME \
          --output /mnt/public/dataset

2. **Base Model** – obtain from Hugging Face / ModelScope / internal storage:

   .. code-block:: bash

      # TODO:
      python -c "import transformers, os; transformers.pipeline('text-generation', model='XXX_BASE_MODEL')"

Update `CHECKPOINT_LOAD_PATH` to point to the downloaded checkpoint directory.

Launch Training
---------------

From inside the repository root:

.. code-block:: bash

   cd /workspace/megatron-RLInf
   bash scripts/run_grpo.sh

Key Flags Explained
~~~~~~~~~~~~~~~~~~~

+ `MICRO_BATCH_SIZE` / `GLOBAL_BATCH_SIZE` – micro per GPU vs effective global tokens.  
+ `SEQ_LEN` – prompt + response length (9216 by default).  
+ Offloading (`OFFLOAD_*`) – enable ZeRO-3 style CPU offload when GPU memory is tight.  
+ Sampling params (`TEMPERATURE`, `TOP_P`, etc.) – govern how roll-out responses are generated.  
+ `SAVE_INTERVAL` – checkpoint frequency (in training steps).  

The script auto-derives:

* `WORLD_SIZE = NNODES × GPUS_PER_NODE`
* Port offsets for vLLM (`WEIGHT_PORT_BASE`, `TOKEN_PORT_BASE`)
* Log file names with time-stamps

Monitoring & Output
-------------------

* **Stdout / stderr** are tee-ed to `logs/MEGA-*.log` per rank.  
* **TensorBoard**: if `TENSORBOARD_ENABLE=True`, run  
  ::

     tensorboard --logdir logs/ --port 6006

Next Steps
----------

* Tweak micro-batch size or enable optimizer offload if you hit out-of-memory.  
* Scale-out: set `NNODES > 1`, make sure `MASTER_ADDR` and network ports are reachable.  
* Explore other algorithms (`PPO`, `DPO`) in the `examples/` directory.

You are now running your first post-training job with RLInf — happy fine-tuning!
