

import torch
from megatron.core import tensor_parallel
from omegaconf import DictConfig


class MegatronCoreExample:
    """
    A minimal example using `megatron.core` and `omegaconf.DictConfig`.

    This class demonstrates how to:
      1. Accept a configuration object defined with OmegaConf.
      2. Use a small function from `megatron.core` (e.g., tensor parallel utilities).
         Here we simply use `tensor_parallel.copy_to_tensor_model_parallel_region`
         as a demonstration.

    """

    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        # A dummy tensor for demonstration purposes
        self.tensor = torch.ones((2, 2))

    def run_parallel_copy(self) -> torch.Tensor:
        """
        Run a simple Megatron tensor-parallel operation.

        Returns
        -------
        torch.Tensor
            A tensor after applying a tensor-parallel copy operation.
        """
        return tensor_parallel.copy_to_tensor_model_parallel_region(self.tensor)

    def show_config(self):
        """
        Print the configuration values stored in the DictConfig.
        """
        print(self.cfg)
