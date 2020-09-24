from abc import abstractmethod
from tqdm import tqdm
from os.path import exists, join, isfile, dirname, abspath, split
from pathlib import Path
import random

import tensorflow as tf
import numpy as np
from ...utils import Cache, get_hash

from ...datasets.utils import DataProcessing
from sklearn.neighbors import KDTree


class TFDataloader():

    def __init__(self,
                 *args,
                 dataset=None,
                 model=None,
                 use_cache=True,
                 steps_per_epoch=None,
                 **kwargs):
        self.dataset = dataset
        self.model = model
        self.preprocess = model.preprocess
        self.transform = model.transform
        self.get_batch_gen = model.get_batch_gen
        self.model_cfg = model.cfg
        self.steps_per_epoch = steps_per_epoch

        if self.preprocess is not None and use_cache:
            cache_dir = getattr(dataset.cfg, 'cache_dir')

            assert cache_dir is not None, 'cache directory is not given'

            self.cache_convert = Cache(self.preprocess,
                                       cache_dir=cache_dir,
                                       cache_key=get_hash(
                                           repr(self.preprocess)[:-15]))

            uncached = [
                idx for idx in range(len(dataset)) if dataset.get_attr(idx)
                ['name'] not in self.cache_convert.cached_ids
            ]
            if len(uncached) > 0:
                print("cache key : {}".format(repr(self.preprocess)[:-15]))
                for idx in tqdm(range(len(dataset)), desc='preprocess'):
                    attr = dataset.get_attr(idx)
                    data = dataset.get_data(idx)
                    name = attr['name']

                    self.cache_convert(name, data, attr)

        else:
            self.cache_convert = None
        self.split = dataset.split
        self.pc_list = dataset.path_list
        self.num_pc = len(self.pc_list)

    def read_data(self, index):
        attr = self.dataset.get_attr(index)
        if self.cache_convert:
            data = self.cache_convert(attr['name'])
        elif self.preprocess:
            data = self.preprocess(self.dataset.get_data(index), attr)
        else:
            data = self.dataset.get_data(index)

        return data, attr

    def get_loader(self, batch_size=1, num_threads=3):
        steps_per_epoch = self.steps_per_epoch * batch_size if self.steps_per_epoch is not None else None
        gen_func, gen_types, gen_shapes = self.get_batch_gen(
            self, steps_per_epoch)

        loader = tf.data.Dataset.from_generator(gen_func, gen_types, gen_shapes)

        loader = loader.map(map_func=self.transform,
                            num_parallel_calls=num_threads)

        if ('batcher' not in self.model_cfg.keys() or
                self.model_cfg.batcher == 'DefaultBatcher'):
            loader = loader.batch(batch_size)
            length = len(self.dataset) / batch_size + 1 if len(
                self.dataset) % batch_size else len(self.dataset) / batch_size
            length = length if self.steps_per_epoch is None else self.steps_per_epoch

        else:
            if self.dataset.split not in ['train', 'training']:
                length = self.model_cfg.get('val_batch_num', 20)
            else:
                length = self.model_cfg.get('batch_num', 20)

        return loader, int(length)
