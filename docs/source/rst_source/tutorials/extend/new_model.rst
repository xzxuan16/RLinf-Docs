Adding New Models 
===================

This document describes how to add support for a new model in the RLinf training framework, which supports two types of backends:

1. HuggingFace + FSDP
2. Megatron + SGLang

Each backend has its own way of loading and running models. This guide explains how to:

- Check which models are supported by each backend

- Add new models to the RLinf

- Modify the configuration files to use your custom model

- (If necessary) Modify the backend source code for unsupported models


HuggingFace + FSDP Backend
================================

This backend uses the HuggingFace Transformers library with PyTorch FSDP (Fully Sharded Data Parallel) 
to train and generate from models. It supports any model that is implemented in HuggingFace and compatible with PyTorch.

Supported Models:
------------------

All models listed here are supported:
`HuggingFace supported models <https://huggingface.co/models>`_


How to Add a New Model:
-------------------------

1. **Select a model** from HuggingFace (e.g., `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`).

2. **Check compatibility**: make sure it is a causal language model (AutoModelForCausalLM) and available in PyTorch.

3. **Download the model** locally or point to a local/remote path.

4. **Edit the configuration file**:

- Set the following in `config.yaml` : # TODO:

  .. code-block:: yaml
      
    actor:
      tokenizer:
        tokenizer_model: <your path to the model>

- Set the `generation.model_dir` to the same path:

  .. code-block:: yaml

    generation:
      model_dir: <your path to the model>
      model_arch: qwen2.5


5. **Run the training** as usual


If your model is a custom HuggingFace model that is not in the hub, ensure that:

* Its `config.json` and tokenizer files are complete.
* You implement a compatible `AutoModelForCausalLM` subclass.


Megatron + SGLang Backend
=============================

This backend uses NVIDIA's Megatron-LM for distributed training and SGLang for efficient generation. 
It requires that the models be defined using Megatron's architecture and that inference be compatible with SGLang's runtime.

Supported Models:
------------------

- **Megatron-LM Supported Models**:
  `Megatron-LM supported models <https://github.com/NVIDIA/Megatron-LM>`_

- **SGLang Supported Models**:
  `SGLang supported models <https://github.com/sgl-project/sglang>`_

How to Add a New Model:
-------------------------

1. **Check whether your model is supported** by Megatron or SGLang (see links above).

2. If supported:

Do as same as the HuggingFace + FSDP backend:

- Download the model weights

- Set the model path in your config file

- Set the `generation.model_dir` and `model_arch` accordingly

3. If **not supported**, you will need to **modify the backend source code**: # TODO:

- **For Megatron**:

  - Add a new model definition in `megatron/model/`

  - Register the model in `get_model()` in `megatron/__init__.py`

  - Ensure the model supports TP/PP (tensor/pipeline parallel)

- **For SGLang**:

  - Add a `ModelRunner` class in `sglang/model_runner/`

  - Implement `generate()`, `load_model()`, `get_tokenizer()`

  - Register it in the `ModelRegistry`

These changes allow the system to load and generate with new architectures.


Conclusion
===========

- The **HuggingFace + FSDP** backend is flexible and supports most PyTorch-compatible transformer models.

- The **Megatron + SGLang** backend is more efficient but requires strict architectural compatibility.

- Use this guide to determine whether your model is supported and how to register it.

- For custom architectures, modifying the source code is necessary.

If you encounter issues integrating a new model, consider starting with the HuggingFace backend first for debugging and development.
