# -*- coding: utf-8 -*-
"""
@Author: your name
@Date: 2020-05-13 01:43:02
@LastEditTime : 2020-05-15 18:38:40
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /elastic-ctr-baiduhi/retrieval/servers/instance.py
"""
import proto.rank_pb2 as rank_pb2
import proto.rank_pb2_grpc as rank_pb2_grpc
import time
import math


class Instance(object):
    """
    Instance
    """
    def __init__(self, feature_extractor, feature_provider):
        """
        constructor
        """
        #self._feature_value = []
        self._feature_provider = feature_provider
        self._feature_extractor = feature_extractor
        self._feature_value = [None] * feature_extractor.get_all_feature_num()
        self.hash_feature = [None] * feature_extractor.get_all_feature_num()
        self._fearure_base = [0] * feature_extractor.get_origin_feature_num()
        self._feature_mask = [0] * feature_extractor.get_all_feature_num()
        self.feed_names = feature_extractor.feed_names
        self.feed_slot_names = feature_extractor.feed_slot_names

    def add_origin_feature_value(self, name, feature, weights=None):
        """
        add origin feature value
        """
        index = self._feature_extractor.get_feature_index(name)
        if index < 0:
            return
        #print("instance::add_origin_feature_value  ins add fearure name: {}, feature: {} index: {}".format(name, feature, index))
        if isinstance(feature, list):

            self._feature_value[index] = feature
        else:
            #self.hash_feature[index].append(0)
            #print("ins add no list fearure name: {}, feature: {} index: {}".format(name, feature, index))
            #print("CHECK One add origin feature value BEFOREREFRESH: {}".format(self._feature_value))
            if self._feature_value[index] is None:
                self._feature_value[index] = []
            self._feature_value[index].append(feature)
            #print("END ins add no list fearure name: {}, feature: {}".format(name, feature))
            #print("CHECK One add origin feature value REFRESH: {}".format(self._feature_value))
        self._feature_mask[index] = 1
    
    def provide_from_proto(self, user_info, item_info, index_in_batch):
        """
        provide from proto
        """
        #TODO auto select base on slot conf
        for name in self._feature_provider.get_origin_feature_name():
            # call provider func by name
            #print("start provide feature name: {}".format(name))
            values, _, _ = self._feature_provider.provide_by_name(name, index_in_batch)
            #print("instance::provide_from_proto  {} value: {}".format(name, values))
            self.add_origin_feature_value(name, values)
            #print("end provide feature name: {}".format(name))

    def extract(self, slots):
        """
        extract
        """
        #print("instance::extract: {}".format(self._feature_extractor.features))
        for feature in self._feature_extractor.features:
            if len(slots) == 0 or feature.get_slot() not in slots:
                raise ValueError("no slot found to extract")
            if not self.check_valid(feature.depend):
                raise ValueError("no depend")
            #print("instance::extract  start extract {}, depend: {}, feature_id: {}".format(feature.name, feature.depend, feature.feature_id))
            self.extract_one(feature)
    
    def extract_one(self, feature):
        """
        extract one
        """
        method = feature.method
        method_eval = "self.{}_method(feature)".format(method)
        #print("instance::extract_ONE  with method {}".format(method_eval))
        eval(method_eval)

    def get_feature_value(self, index):
        """
        get feature value
        """
        return self._feature_value[index]

    def check_valid(self, depends):
        """
        check valid
        """
        for depend in depends:
            if not self._feature_mask[depend]:
                return False
        return True

    def DirectString_method(self, feature):
        """
        DirectString method
        """
        if len(feature.depend) != 1:
            raise ValueError("there must be one depend when use DirectString extract method")
        
        hash_value = hash(self._feature_value[feature.depend[0]][0] + feature.slot) % 1000001
        if self.hash_feature[feature.feature_id] is None:
            self.hash_feature[feature.feature_id] = []
        self.hash_feature[feature.feature_id].append(hash_value)
        #print("DirectString hash value: {}, depend value: {} feature_id: {} slot: {} origin value: {}".format(self.hash_feature[feature.feature_id], feature.depend[0], feature.feature_id, feature.slot, self._feature_value))
    
    def TopString_method(self, feature):
        """
        TopString method
        """
        if len(feature.depend) != 1:
            raise ValueError("there must be one depend when use TopString extract method")
        len_features = len(self._feature_value[feature.depend[0]])
        #print("instance::TopString_method  with origin len: {} featrue arg: {}, feature depend: {}, feature value: {}".format(len_features, feature.arg, feature.depend, self._feature_value[feature.depend[0]]))
        #for i in range(min(len_features, feature.arg)):
        if self.hash_feature[feature.feature_id] is None:
            self.hash_feature[feature.feature_id] = []
        for i in range(min(len_features, feature.arg)):
            #print("test")
            #print("{} th".format(i))
            #print("hash value: {}".format(self.hash_feature[feature.feature_id]))
            #print("whole hash value: {}".format(self.hash_feature))
            #print("depend value: {}".format(feature.depend))
            #print("START {} th TopString_method hash value: {}, depend value: {} feature_id: {} slot: {} origin value: {}".format(i, self.hash_feature[feature.feature_id], feature.depend[0], feature.feature_id, feature.slot, self._feature_value[feature.depend[0]][0]))
            hash_value = hash(self._feature_value[feature.depend[0]][i] + feature.slot) % 1000001
            self.hash_feature[feature.feature_id].append(hash_value)
            #print("{} th TopString_method hash value: {}, depend value: {} feature_id: {} slot: {} origin value: {}".format(i, self.hash_feature[feature.feature_id], feature.depend[0], feature.feature_id, feature.slot, self._feature_value[feature.depend[0]][0]))

    def Float2String_method(self, feature):
        if len(feature.depend) != 1:
            raise ValueError("there must be one depend when use TopString extract method")  
        float_value = self._feature_value[feature.depend[0]][0]
        str_value = ''
        if float_value < 0:
            str_value = '0'
        elif float_value > 1:
            str_value = '0'
        else:
            str_value = str(int(float_value/0.1))
        hash_value = hash(str_value + feature.slot) % 1000001
        if self.hash_feature[feature.feature_id] is None:
            self.hash_feature[feature.feature_id] = []
        self.hash_feature[feature.feature_id].append(hash_value)

    def Time2String_method(self, feature):
        #TODO : 先不加 在线和离线时间戳怎么保持一致
        if len(feature.depend) != 1:
            raise ValueError("there must be one depend when use DirectString extract method")
        
        cur_time = int(time.time())
        provide_time = self._feature_value[feature.depend[0]][0]
        time_div = (cur_time - provide_time) / 3600
        if time_div< 0:
            print("cur_time: {} provide_time: {}".format(cur_time, provide_time))
            raise ValueError("time div must be > 0")
        if time_div < 1:
            time_div = 1
        time_log = int(math.log(time_div))
        if time_log > 50:
            time_log = 50
        hash_value = hash(feature.slot + str(time_log))
        if self.hash_feature[feature.feature_id] is None:
            self.hash_feature[feature.feature_id] = []
        self.hash_feature[feature.feature_id].append(hash_value)
        
        
