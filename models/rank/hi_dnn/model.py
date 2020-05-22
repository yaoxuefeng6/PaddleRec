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

import math
import paddle.fluid as fluid

from paddlerec.core.utils import envs
from paddlerec.core.model import Model as ModelBase


class Model(ModelBase):
    def __init__(self, config):
        ModelBase.__init__(self, config)

    def input(self, is_infer=False):
        slots = envs.get_global_env("sparse_inputs_slots", [], self._namespace)
        self.sparse_inputs = [
            fluid.data(name=i,
                       shape=[-1, 1],
                       lod_level=1,
                       dtype="int64") for i in slots
        ]
        self.label_input = fluid.data(name="label", shape=[-1, 1], dtype="int64")
        #self.sparse_inputs = self._sparse_data_var[1:]
        #self.label_input = self._sparse_data_var[0]
        self.log_hash = fluid.data(name="log_hash", shape=[-1, 1], dtype="int64")

        self._data_var.append(self.label_input)
        self._data_var.append(self.log_hash)
        for input in self.sparse_inputs:
            self._data_var.append(input)
        if is_infer:
            self._infer_data_var.append(self.label_input)
            self._infer_data_var.append(self.log_hash)
            for input in self.sparse_inputs:
                self._infer_data_var.append(input)
            self._infer_data_loader = fluid.io.DataLoader.from_generator(
                feed_list=self._infer_data_var, capacity=64, use_double_buffer=False, iterable=False)
        if self._platform != "LINUX":
            self._data_loader = fluid.io.DataLoader.from_generator(
                feed_list=self._data_var, capacity=64, use_double_buffer=False, iterable=False)



    def net(self, is_infer=False):
        is_distributed = True if envs.get_trainer() == "CtrTrainer" else False
        sparse_feature_number = envs.get_global_env("hyper_parameters.sparse_feature_number", None, self._namespace)
        sparse_feature_dim = envs.get_global_env("hyper_parameters.sparse_feature_dim", None, self._namespace)

        def embedding_layer(input):
            emb = fluid.layers.embedding(
                input=input,
                is_sparse=True,
                is_distributed=is_distributed,
                size=[sparse_feature_number, sparse_feature_dim],
                param_attr=fluid.ParamAttr(
                    name="SparseFeatFactors",
                    initializer=fluid.initializer.Uniform()),
            )
            emb_sum = fluid.layers.sequence_pool(
                input=emb, pool_type='sum')
            return emb_sum

        def fc(input, output_size):
            output = fluid.layers.fc(
                input=input, size=output_size,
                act='relu', param_attr=fluid.ParamAttr(
                    initializer=fluid.initializer.Normal(
                        scale=1.0 / math.sqrt(input.shape[1]))))
            return output

        sparse_embed_seq = list(map(embedding_layer, self.sparse_inputs))
        concated = fluid.layers.concat(sparse_embed_seq, axis=1)

        fcs = [concated]
        hidden_layers = envs.get_global_env("hyper_parameters.fc_sizes", None, self._namespace)

        for size in hidden_layers:
            fcs.append(fc(fcs[-1], size))

        predict = fluid.layers.fc(
            input=fcs[-1],
            size=2,
            act="softmax",
            param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                scale=1 / math.sqrt(fcs[-1].shape[1]))))

        #fluid.layers.Print(predict)
        self.predict = predict
        if is_infer:
            auc, batch_auc, _ = fluid.layers.auc(input=self.predict,
                                             label=self.label_input,
                                             num_thresholds=2 ** 12,
                                             slide_steps=20)
            self._infer_results['test_auc'] = auc
            self._infer_results['predict_q'] = predict
            self._infer_results["log_hash"] = self.log_hash
            self._infer_results["real_label"] = self.label_input
            

    def avg_loss(self):
        cost = fluid.layers.cross_entropy(input=self.predict, label=self.label_input)
        avg_cost = fluid.layers.reduce_mean(cost)
        self._cost = avg_cost

    def metrics(self):
        auc, batch_auc, _ = fluid.layers.auc(input=self.predict,
                                             label=self.label_input,
                                             num_thresholds=2 ** 12,
                                             slide_steps=20)
        self._metrics["AUC"] = auc
        #self._metrics["BATCH_AUC"] = batch_auc
        self._metrics["predict_q"] = self.predict
        self._metrics["label"] = self.label_input
        self._metrics["log_hash"] = self.log_hash 
    def train_net(self):
        #self._init_slots()
        self.input()
        self.net()
        self.avg_loss()
        self.metrics()

    def optimizer(self):
        learning_rate = envs.get_global_env("hyper_parameters.learning_rate", None, self._namespace)
        optimizer = fluid.optimizer.Adam(learning_rate, lazy_mode=True)
        return optimizer

    def infer_net(self):
        #self._init_slots()
        self.input(is_infer=True)
        self.net(is_infer=True)
