import torch.nn as nn
import numpy as np
from utils.init_layer import nn_block
from utils.util_func import maybe_kwargs, maybe_default_kwarg

from gated_networks.gated_linear_unit import GatedLinearUnit


class GatedResidualNetwork(nn.Module):

    def __init__(
            self,
            in_features,
            out_features,
            hidden_features,
            use_projector=True,
            use_layer_norm=True,
            elu_dense_kwargs=None,
            linear_dense_kwargs=None,
            glu_gate_kwargs=None,
            glu_dense_kwargs=None,
            projector_kwargs=None,
            layer_norm_kwargs=None,
    ):
        super(GatedResidualNetwork, self).__init__()

        self.in_features = in_features
        self.hidden_features = hidden_features
        self.out_features = out_features

        elu_dense_kwargs = maybe_default_kwarg(elu_dense_kwargs, 'layer_nn', nn.Linear)
        elu_dense_kwargs = maybe_default_kwarg(elu_dense_kwargs, 'activation', nn.ELU)
        self.elu_dense = nn_block(
            in_features=in_features,
            out_features=hidden_features,
            **elu_dense_kwargs
        )

        linear_dense_kwargs = maybe_default_kwarg(linear_dense_kwargs, 'layer_nn', nn.Linear)
        linear_dense_kwargs = maybe_default_kwarg(linear_dense_kwargs, 'activation', None)
        linear_dense_kwargs = maybe_default_kwarg(linear_dense_kwargs, 'dropout_p', 0.15)
        linear_dense_kwargs = maybe_default_kwarg(linear_dense_kwargs, 'dense_dropout_type', nn.Dropout)
        self.linear_dense = nn_block(
            in_features=hidden_features,
            out_features=out_features,
            **linear_dense_kwargs
        )

        self.gated_linear_unit = GatedLinearUnit(
            in_features=in_features,
            out_features=out_features,
            gate_kwargs=glu_gate_kwargs,
            dense_kwargs=glu_dense_kwargs,
        )

        if use_projector:
            self.projector = nn_block(
                in_features=in_features,
                out_features=out_features,
                **maybe_kwargs(projector_kwargs)
            )
        else:
            if in_features != out_features:
                raise Exception(f"in_features must be the same as out_features, when not using a projector layer"
                                f"in_features: {in_features}, out_features: {out_features}")
            self.projector = None

        if use_layer_norm:
            self.layer_norm = nn.LayerNorm(out_features, **maybe_kwargs(layer_norm_kwargs))
        else:
            self.layer_norm = None

    def forward(self, inputs):

        x = self.elu_dense(inputs)
        x = self.linear_dense(x)

        if self.projector is not None:
            inputs = self.projector(inputs)

        x = inputs + self.gated_linear_unit(x)

        if self.layer_norm is not None:
            x = self.layer_norm(x)

        return x
