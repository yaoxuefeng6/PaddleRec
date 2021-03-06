# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import random

import numpy as np

from paddlerec.core.reader import Reader
from paddlerec.core.utils import envs


class EvaluateReader(Reader):
    def init(self):
        self.batch_size = envs.get_global_env("batch_size", None, "evaluate.reader")

        self.input = []
        self.length = None

    def base_read(self, files):
        res = []
        for f in files:
            with open(f, "r") as fin:
                for line in fin:
                    line = line.strip().split('\t')
                    res.append(tuple([map(int, line[0].split(',')), int(line[1])]))
        return res

    def make_data(self, cur_batch, batch_size):
        cur_batch = [list(e) for e in cur_batch]
        max_seq_len = 0
        for e in cur_batch:
            max_seq_len = max(max_seq_len, len(e[0]))
        last_id = []
        for e in cur_batch:
            last_id.append(len(e[0]) - 1)
            e[0] += [0] * (max_seq_len - len(e[0]))

        max_uniq_len = 0
        for e in cur_batch:
            max_uniq_len = max(max_uniq_len, len(np.unique(e[0])))

        items, adj_in, adj_out, seq_index, last_index = [], [], [], [], []
        mask, label = [], []

        id = 0
        for e in cur_batch:
            node = np.unique(e[0])
            items.append(node.tolist() + (max_uniq_len - len(node)) * [0])
            adj = np.zeros((max_uniq_len, max_uniq_len))

            for i in np.arange(len(e[0]) - 1):
                if e[0][i + 1] == 0:
                    break
                u = np.where(node == e[0][i])[0][0]
                v = np.where(node == e[0][i + 1])[0][0]
                adj[u][v] = 1

            u_deg_in = np.sum(adj, 0)
            u_deg_in[np.where(u_deg_in == 0)] = 1
            adj_in.append(np.divide(adj, u_deg_in).transpose())

            u_deg_out = np.sum(adj, 1)
            u_deg_out[np.where(u_deg_out == 0)] = 1
            adj_out.append(np.divide(adj.transpose(), u_deg_out).transpose())

            seq_index.append(
                [[id, np.where(node == i)[0][0]] for i in e[0]])
            last_index.append(
                [id, np.where(node == e[0][last_id[id]])[0][0]])
            label.append(e[1] - 1)
            mask.append([[1] * (last_id[id] + 1) + [0] *
                         (max_seq_len - last_id[id] - 1)])
            id += 1

        items = np.array(items).astype("int64").reshape((batch_size, -1))
        seq_index = np.array(seq_index).astype("int32").reshape(
            (batch_size, -1, 2))
        last_index = np.array(last_index).astype("int32").reshape(
            (batch_size, 2))
        adj_in = np.array(adj_in).astype("float32").reshape(
            (batch_size, max_uniq_len, max_uniq_len))
        adj_out = np.array(adj_out).astype("float32").reshape(
            (batch_size, max_uniq_len, max_uniq_len))
        mask = np.array(mask).astype("float32").reshape((batch_size, -1, 1))
        label = np.array(label).astype("int64").reshape((batch_size, 1))
        return zip(items, seq_index, last_index, adj_in, adj_out, mask, label)

    def batch_reader(self, batch_size, batch_group_size, train=True):
        def _reader():
            random.shuffle(self.input)
            group_remain = self.length % batch_group_size
            for bg_id in range(0, self.length - group_remain, batch_group_size):
                cur_bg = copy.deepcopy(self.input[bg_id:bg_id + batch_group_size])
                if train:
                    cur_bg = sorted(cur_bg, key=lambda x: len(x[0]), reverse=True)
                for i in range(0, batch_group_size, batch_size):
                    cur_batch = cur_bg[i:i + batch_size]
                    yield self.make_data(cur_batch, batch_size)

            if group_remain == 0:
                return
            remain_data = copy.deepcopy(self.input[-group_remain:])
            if train:
                remain_data = sorted(
                    remain_data, key=lambda x: len(x[0]), reverse=True)
            for i in range(0, group_remain, batch_size):
                if i + batch_size <= group_remain:
                    cur_batch = remain_data[i:i + batch_size]
                    yield self.make_data(cur_batch, batch_size)
                else:
                    # Due to fixed batch_size, discard the remaining ins
                    return
                    # cur_batch = remain_data[i:]
                    # yield self.make_data(cur_batch, group_remain % batch_size)

        return _reader

    def generate_batch_from_trainfiles(self, files):
        self.input = self.base_read(files)
        self.length = len(self.input)
        return self.batch_reader(self.batch_size, self.batch_size * 20, False)

    def generate_sample(self, line):
        def data_iter():
            yield []

        return data_iter
