YAML Tutorial
================
A complete reference for the configuration file used in the `GRPO + SGLang` reinforcement learning pipeline. 
Every important key in the YAML is documented below so that you can confidently adapt the file to your own cluster, model, or research ideas.  
Parameters are grouped exactly by their top-level key.


--------------------------------------------------------------------
Quick-start checklist
--------------------------------------------------------------------

1. **Change paths**  

- ``checkpoint_load_path``, ``checkpoint_save_path``  

- ``data.data_prefix`` (train / validation)  

- ``model_dir`` (inference)  

- ``tokenizer.tokenizer_model``

2. **Match parallelism to hardware**  

- Ensure *tensor_parallel_size * pipeline_parallel_size *
  num_nodes * num_gpus_per_node* ≥ GPUs you actually own.  

- When lowering ``tensor_parallel_size`` for generation, update
  ``generation.placement.stride`` accordingly.

3. **Scale batch sizes**  

- Keep ``global_batch_size`` divisible by DP world size.  

- Grow ``micro_batch_size`` until you hit GPU memory limit.

4. **Tune RL knobs**  

- ``num_responses_per_prompt`` (sample-efficiency vs compute).  

- ``kl_beta`` & ``entropy_bonus`` (stability vs exploration).  

- ``sampling_params.temperature / top_p`` (diversity).

5. **Monitoring & logging**  
  
- Flip ``tensorboard.enable`` or ``wandb.enable`` to **True**.


--------------------------------------------------------------------
cluster
--------------------------------------------------------------------
``num_nodes (default: 1)``  
  Physical nodes to reserve.

``num_gpus_per_node (default: 8)``  
  GPUs per node that Ray/Hydra should assume are free. 
  **All subsequent parallel-size calculations must divide this number cleanly.**

--------------------------------------------------------------------
training
--------------------------------------------------------------------

``placement.strategy (default: default)``
  the *placement strategy* for trainer processes.

.. ``group_name (default: "TrainerGroup")``  
..   Ray *ActorGroup* name for the trainer processes; must match the name that the generation side expects when it sends/receives tensors.

.. ``mcore_gpt``  
..   **True** = use Megatron-Core implementation instead of “legacy” Megatron-LM modules.

.. ``spec_name``  
..   Transformer layer spec to instantiate (``decoder_gpt`` by default).

``micro_batch_size``  
  Samples **per GPU per forward call** inside Megatron.

``global_batch_size``  
  Effective batch size **after** gradient accumulation & data parallel reduction.  
  ``global_batch_size = micro_batch_size * num_micro_batches * data_parallel_size``

``max_epochs``  
  Maximum number of *epochs* to run; 
  Epoch here = walking once through the *prompt dataset*.

``max_steps (default: -1)``
  Maximum number of training steps before stopping early.
  If set to -1, this defaults to: ``num_steps_per_epoch * training.max_epochs``

``val_check_interval``  
  How often to launch a validation rollout.

``save_interval``  
  Checkpoint frequency in trainer steps.

``seq_length``  
  **Total** sequence length (prompt + generated response) fed into Megatron during RL updates.

``loss_agg_func (default: "token-mean")``  
  Specifies how token-level losses are reduced into a scalar. 

- ``token-mean``: global average

- ``seq-mean-token-sum``: first sum over tokens per sequence then average over sequences  

- ``seq-mean-token-mean``: mean inside each sequence then mean across sequences

.. ``offload_optimizer / offload_weight / offload_grad``  
..   Enable CPU off-loading during *generation* to fit both training and SGLang weights on the same GPUs. Usually keep them **True**.

``checkpoint_load_path``  
  Path to a *Megatron* checkpoint folder that will be **loaded** before RL post-training starts (maybe a warm-starting from SFT).

``checkpoint_save_path``  
  Parent directory where new checkpoints are written.

``use_dynamic_batch_size (default: True)``  
  Allow Megatron to merge neighbouring micro-batches if the total token count stays below ``max_tokens_per_mbs``.

``max_tokens_per_mbs (default: 18k)``  
  Upper limit of tokens in a Megatron microbatch when dynamic batching is enabled.


algorithm
^^^^^^^^^

``num_responses_per_prompt (default: 16)``  
  the number of generations per prompt during a rollout.  
  Must be **>1** because GRPO normalises reward within a prompt group.

``rollout_micro_batch_size (default: 256)``  
  Prompt count sent to SGLang **per engine call**.

``num_rollout_samples (default: 64)``  
  Prompt count processed **per trainer step** per data-parallel rank.
  ``rollout_batch_size = num_rollout_samples * num_responses_per_prompt``

``logprob_forward_micro_batch_size (default: 16)``  
  Micro-batch size used when computing log-probabilities.

GRPO loss parameters
  containing ``kl_beta``, ``ratio_clip_eps``, ``ref_policy_kl_penalty``,
  ``entropy_bonus``, ``clip_ratio_c``, ``normalize_advantages``.

sampling_params
  For backend generation during training.
  Set ``use_greedy`` to **True** for purely deterministic rollouts; otherwise adjust ``temperature``, ``top_p`` etc.

.. batch_iterator
.. ^^^^^^^^^^^^^^
.. ``use_flask``  
..   Enable a lightweight Flask server on rank 0 to *load‑balance* prompts
..   across DP ranks whose generation lengths differ widely.

.. ``port``  
..   Listening port for that server.

.. megatron
.. ^^^^^^^^
.. ``ddp_bucket_size``  
..   Override default NCCL bucket (in bytes).  Leave *null* unless you know
..   what you are doing.

.. ``distributed_backend`` ``nccl`` or ``gloo``  
.. ``distributed_timeout_minutes``  
..   Watch‑dog for collectives.

.. ``ckpt_format`` ``torch`` or ``megatron``  
.. ``use_dist_ckpt``  
..   Whether checkpoints are the *distributed* variant.

--------------------------------------------------------------------
generation
--------------------------------------------------------------------

placement
  Ray placement rule for **SGLang** worker processes.  
  ``strategy: strided`` with ``stride`` = training-TP / generation-TP spreads
  backend ranks evenly over GPUs already occupied by training ranks.

.. ``gpu_memory_utilization``  
..   Fraction of each GPU that SGLang is allowed to lock.

``model_dir``  
  Path to the HuggingFace checkpoint **used for inference**.  
  Must be architecturally compatible with the training model.

``model_arch``  
  String token understood by SGLang to pick its tokenizer & post-processors.

.. ``enforce_eager``  
..   If False, vllm will capture cuda graph, which will take more time to initialize.

.. ``distributed_executor_backend``  
..   ``mp`` = Python multiprocessing, 
..   ``ray`` = Ray actor.  
..   The former has lower latency; the latter scales across nodes.

.. ``detokenize``  
..   Set **True** only if you need the *text* form on the Python side; RL
..   loss only requires token ids.

.. ``padding / eos``  
..   Overrides for special‑token ids sent to vLLM.  ``null`` = use tokenizer
..   default.

``tensor_parallel_size`` / ``pipeline_parallel_size``  
  Parallelism for **inference engine**.

.. Networking
..   ``master_address`` TCP IP for weight + token channels.  
..   ``weight_comm_port`` Port to ship FP16 weight shards.  
..   ``token_comm_port`` Port to stream prompt/outputs.  **Make sure ports
..   are free**.  
..   ``world_size`` Always 2 at the moment (one trainer, one SGLang).

.. ``validate_weight``  
..   When **True**, trainer sends the entire weight tensor once to let
..   vLLM verify parity against HF weights.

.. ``sglang_decode_log_interval``  
..   How often vLLM prints per‑token decode latency.

--------------------------------------------------------------------
model
--------------------------------------------------------------------

``precision (default: "bf16")``  
  governs parameter and activation dtype during training.

``tensor_model_parallel_size`` / ``pipeline_model_parallel_size``  
  *Must divide* ``cluster.num_gpus_per_node``.  
  Combined with DP they define the final device mesh.

``sequence_parallel``  
  Enable Megatron “seq-parallel” (splitting tokens over TP ranks).

``activation (default: "swiglu")``
  Activation function used in the transformer layers.

``normalization (default: "rmsnorm")``
  Normalization layer used in the transformer layers.

.. ``rotary_base``  
..   Base frequency of RoPE; larger = slower rotation = potential longer
..   context.

--------------------------------------------------------------------
tokenizer
--------------------------------------------------------------------

``tokenizer_model``  
  Directory containing tokenizer.json or HF tokenizer files.

.. ``extra_vocab_size``  
..   Reserve id space for special reward tokens etc.

.. ``use_fast``  
..   Set **True** for HF Fast-tokenizer (cython) when memory permits.

------------------------------------------------------------------------------------------------------------------------
optim
------------------------------------------------------------------------------------------------------------------------

``optimizer (default: "hybridadam")``
  Optimizer to use for training.

``lr (default: 1e-6)``  
  Learning rate for the optimizer.

``weight_decay (default: 0.05)``
  L2 penalty (applied to *all* except bias/Norm by default rules).

All other options keep recommended defaults.

.. --------------------------------------------------------------------
.. lr_sched
.. --------------------------------------------------------------------

.. - Warm‑up controlled by ``lr_warmup_fraction`` or explicit
..   ``lr_warmup_iters``.
.. - ``lr_decay_style`` = ``constant`` here (i.e. flat after warm‑up).
..   Switch to ``cosine`` or ``linear`` when needed.
.. - ``lr_decay_iters`` only relevant if style ≠ constant.

--------------------------------------------------------------------
data
--------------------------------------------------------------------

``seq_length``  
  Prompt sequence length only (response length is computed as ``training.seq_length - data.seq_length``).

``num_workers``  
  Dataloader threads **per GPU rank**.

``data_prefix``  
  Path to the training/val data file

``use_text_field_from_data``  
  If **False** loader uses the key ``problem``; set **True** to read
  ``text`` instead (supporting different json schema).



