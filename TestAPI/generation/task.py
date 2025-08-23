import torch
import torch.nn as nn
from typing import List, Dict, Any, Union


class SimpleLinearModel(nn.Module):
    """
    A simple linear model built with PyTorch, inheriting from `torch.nn.Module`.

    This model contains only a single linear (fully connected) layer,
    making it useful as a minimal example for learning or small-scale experiments.

    Parameters
    ----------
    input_dim : int
        The size of the input feature dimension.
    output_dim : int
        The size of the output feature dimension.

    Attributes
    ----------
    linear : torch.nn.Linear
        A linear layer that performs the affine transformation y = xW^T + b.

    Methods
    -------
    forward(x: torch.Tensor) -> torch.Tensor
        Performs the forward pass by applying the linear transformation
        to the input tensor.

    recv(async_op: bool = False) -> AsyncWork | torch.Tensor | List[torch.Tensor] | Dict[str, torch.Tensor] | Any
        A dummy method that mimics a flexible receive operation which could
        return different types depending on the context (similar to distributed APIs).
    """

    def __init__(self, input_dim: int, output_dim: int):
        super(SimpleLinearModel, self).__init__()
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Perform the forward pass of the model.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor of shape (batch_size, input_dim).

        Returns
        -------
        torch.Tensor
            Output tensor of shape (batch_size, output_dim).
        """
        return self.linear(x)

    def recv(
        self, async_op: bool = False
    ) -> torch.Tensor | List[torch.Tensor] | Dict[str, torch.Tensor] | Any:
        """
        Dummy receive-like method that mimics flexible return types.

        This function does not actually perform communication, but shows
        how a function signature can indicate multiple possible return types.

        Parameters
        ----------
        async_op : bool, optional (default=False)
            If True, simulates returning an asynchronous work handle.
            If False, returns one of several possible tensor-based objects.

        Returns
        -------
        AsyncWork | torch.Tensor | List[torch.Tensor] | Dict[str, torch.Tensor] | Any
            - If `async_op=True`: a string `"AsyncWork"` simulating async handle.
            - If `async_op=False`: one of:
                * a single tensor,
                * a list of tensors,
                * a dict mapping string keys to tensors,
                * or other Python object for demonstration.
        """
        if async_op:
            return None  # placeholder for actual async handle
        else:
            return {
                "output": torch.ones(2, 2),
                "hidden": torch.zeros(2, 2),
            }
