

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

    Parameters
    ----------
    cfg : omegaconf.DictConfig
        A configuration object containing model parameters or runtime options.

    Attributes
    ----------
    cfg : omegaconf.DictConfig
        The provided configuration.
    tensor : torch.Tensor
        A dummy tensor to demonstrate Megatron tensor-parallel operations.

    Methods
    -------
    run_parallel_copy()
        Applies a tensor-parallel operation to the dummy tensor.
    show_config()
        Prints the configuration contents in a readable format.

    Examples
    --------
    >>> from omegaconf import DictConfig
    >>> config = DictConfig({"hidden_size": 16, "num_layers": 2})
    >>> example = MegatronCoreExample(config)
    >>> example.show_config()
    hidden_size: 16
    num_layers: 2
    >>> output = example.run_parallel_copy()
    >>> print(output.shape)
    torch.Size([2, 2])
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
