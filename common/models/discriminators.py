import numpy as np
import math
import chainer
import chainer.functions as F
import chainer.links as L
from chainer import cuda, optimizers, serializers, Variable
from chainer import function
from chainer.utils import type_check
from .ops import *

class DCGANDiscriminator(chainer.Chain):
    def __init__(self, in_ch=3, base_size=64, down_layers=4, use_bn=True, noise_all_layer=False, conv_as_last=False):
        layers = {}

        self.down_layers = down_layers
        self.conv_as_last = conv_as_last

        if use_bn:
            norm = 'bn'
        else:
            norm = None

        act = F.leaky_relu
        w = chainer.initializers.Normal(0.02)

        layers['c_first'] = NNBlock(in_ch, base_size, nn='conv', norm=None, activation=act, noise=noise_all_layer, w_init=w)
        base = base_size

        for i in range(down_layers):
            layers['c'+str(i)] = NNBlock(base, base*2, nn='down_conv', norm=norm, activation=act, noise=noise_all_layer, w_init=w)
            base*=2

        if conv_as_last:
            layers['c_last'] = NNBlock(base, 1, nn='conv', norm=None, activation=None, w_init=w)
        else:
            layers['c_last'] = NNBlock(None, 1, nn='linear', norm=None, activation=None, w_init=w)

        super(DCGANDiscriminator, self).__init__(**layers)

    def __call__(self, x, test=False):
        h = self.c_first(x, test=test)
        for i in range(self.down_layers):
            h = getattr(self, 'c'+str(i))(h, test=test)
        if not self.conv_as_last:
            _b, _ch, _w, _h = h.data.shape
            h = F.reshape(h, (_b, _ch*_w*_h))
        h = self.c_last(h, test=test)
        return h
