import ipdb
import numpy as np

from cle.cle.cost import NllBin
from cle.cle.graph.net import Net
from cle.cle.layers import (
    InputLayer,
    InitCell,
    MaskLayer,
    BinCrossEntropyLayer
)
from cle.cle.layers.feedforward import FullyConnectedLayer
from cle.cle.layers.recurrent import LSTM
from cle.cle.train import Training
from cle.cle.train.ext import (
    EpochCount,
    GradientClipping,
    Monitoring,
    Picklize
)
from cle.cle.train.opt import Adam
from cle.cle.utils import unpack
from cle.datasets.music import Music


#datapath = '/data/lisa/data/music/MuseData.pickle'
#savepath = '/u/chungjun/repos/cle/saved/'
datapath = '/home/junyoung/data/music/MuseData.pickle'
savepath = '/home/junyoung/repos/cle/saved/'

batchsize = 10
nlabel = 105
trdata = Music(name='train',
               path=datapath,
               nlabel=nlabel,
               batchsize=batchsize)
valdata = Music(name='valid',
               path=datapath,
               nlabel=nlabel,
               batchsize=batchsize)

# Choose the random initialization method
init_W, init_U, init_b = InitCell('randn'), InitCell('ortho'), InitCell('zeros')

# Define nodes: objects
inp, tar, mask = trdata.theano_vars()
x = InputLayer(name='x', root=inp, nout=nlabel)
y = InputLayer(name='y', root=tar, nout=nlabel)
mask = InputLayer(name='mask', root=mask)
# Using skip connections is easy
h1 = LSTM(name='h1',
          parent=[x],
          batchsize=batchsize,
          nout=200,
          unit='tanh',
          init_W=init_W,
          init_U=init_U,
          init_b=init_b)
h2 = LSTM(name='h2',
          parent=[x, h1],
          batchsize=batchsize,
          nout=200,
          unit='tanh',
          init_W=init_W,
          init_U=init_U,
          init_b=init_b)
h3 = LSTM(name='h3',
          parent=[x, h2],
          batchsize=batchsize,
          nout=200,
          unit='tanh',
          init_W=init_W,
          init_U=init_U,
          init_b=init_b)
h4 = FullyConnectedLayer(name='h4',
                         parent=[h1, h2, h3],
                         nout=nlabel,
                         unit='sigmoid',
                         init_W=init_W,
                         init_b=init_b)
masked_y = MaskLayer(name='masked_y', parent=[y, mask])
masked_y_hat = MaskLayer(name='masked_y_hat', parent=[h4, mask])
cost = BinCrossEntropyLayer(name='cost', parent=[masked_y, masked_y_hat], use_sum=1)
nodes = [x, y, h1, h2, h3, h4, cost, mask, masked_y, masked_y_hat]
model = Net(nodes=nodes)

# You can either use dict or list
#cost = unpack(model.build_recurrent_graph(output_args=[cost]))
cost, masked_y, masked_y_hat =\
    model.build_recurrent_graph(output_args=[cost, masked_y, masked_y_hat])
nll = NllBin(masked_y, masked_y_hat).mean()
cost = cost[-1]
cost.name = 'cost'
nll.name = 'nll'

optimizer = Adam(
    lr=0.001
)

extension = [
    GradientClipping(batchsize),
    EpochCount(100),
    Monitoring(freq=10,
               ddout=[cost, nll],
               data=[valdata]),
    Picklize(freq=10,
             path=savepath)
]

mainloop = Training(
    name='toy_music',
    data=trdata,
    model=model,
    optimizer=optimizer,
    cost=cost,
    outputs=[cost],
    extension=extension
)
mainloop.run()
