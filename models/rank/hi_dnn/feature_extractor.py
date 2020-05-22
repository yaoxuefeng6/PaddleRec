# -*- coding: utf-8 -*-
"""
@Author: yaoxuefeng
@Date: 2020-05-12 16:36:27
@LastEditTime : 2020-05-15 18:39:17
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /elastic-ctr-baiduhi/retrieval/servers/feature_extractor.py
"""
import os
import logging
logging.basicConfig(filename='frature_extractor.log', filemode='w', 
    format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class FeatureConfig(object):
    """
    Feature Config
    """
    def __init__(self, line):
        """
        constructor
        """
        attrs = line.strip().split(';')
        self.arg = -1

        for attr in attrs:
            
            kv = attr.strip().split('=')
            #print("fature_extractor:: __init__  kv[0]: {}".format(kv[0]))
            if kv[0] == "feature_name":
                self.name = kv[1]
            elif kv[0] == "method":
                self.method = kv[1]
            elif kv[0] == "slot":
                self.slot = kv[1]
            elif kv[0] == "depend":
                self.depend = kv[1].strip().split(',')
            elif kv[0] == "arg":
                self.arg = int(kv[1])
                #print("fature_extractor:: __init__  arg: {}".format(self.arg))
        
class Feature(object):
    """
    Feature
    """
    def __init__(self, config, feature_id_map, featrue_id):
        """
        constructor
        """
        self.name = config.name
        self.method = config.method
        self.slot = config.slot
        self.feature_id = featrue_id
        self.arg = config.arg
        self.depend = []
        for dp in config.depend:
            if not dp in feature_id_map.keys():
                raise ValueError("depend: {} is not exist".format(dp))
            self.depend.append(feature_id_map[dp])

    def get_slot(self):
        """
        get slot
        """
        return self.slot
        
class FeatureExtractor(object):
    """
    Feature Extractor
    """
    def __init__(self, slot_file):
        """
        constructor
        """
        self._feature_id = 0  # int64
        self._origin_feature_num = 0
        self._slot_feature_num = 0
        self._feature_id_map = {}
        self._method_map = {}
        self._extract_slots = set()
        self.features = []
        self.feed_names = []
        self.feed_slot_names = []

        if not os.path.isfile(slot_file):
            raise IOError("No this slot conf file: {} not exist".format(slot_file))
        
        lines = open(slot_file).readlines()
        for line in lines:
            if len(line) == 0 or line[0] == '#':
                logging.debug("frature extractor parse slot conf skip this line: {}".format(line))
                continue
            if "origin_feature" in line:
                self.add_origin_field(line)
                #self.register_extract_method()
            elif "feature_name" in line:
                self.add_feature(line)
        

    def get_all_feature_num(self):
        """
        get all feature num
        """
        return len(self._feature_id_map)

    def get_origin_feature_num(self):
        """
        get origin feature num
        """
        return self._origin_feature_num
    
    def get_feature_index(self, name):
        """
        get feature index
        """
        if not name in self._feature_id_map:
            return -1 
        return self._feature_id_map[name]

    def get_feed_slots(self):
        """
        get feed slots
        """
        return self._extract_slots
        
    def register_extract_method(self):
        """
        register extract method
        """
        # TODO: resigter real method
        # currently extract method directly called in instance
        self._method_map["hashop"] = "hashop"
        self._method_map["get_topk"] = "get_topk"
    
    def add_origin_field(self, line):
        """
        add origin field
        """
        origin_feature_list = line.split(":")[1].strip().split(", ")
        for origin_feature in origin_feature_list:
            self._feature_id_map[origin_feature] = self._feature_id
            self._feature_id += 1
        logging.debug("add origin feature{}".format(origin_feature_list))
        self._origin_feature_num = len(origin_feature_list)

    def add_feature(self, line):
        """
        add feature
        """
        feature_config = FeatureConfig(line)
        feature = Feature(feature_config, self._feature_id_map, self._feature_id)
        self._feature_id_map[feature.name] = self._feature_id
        self._feature_id += 1
        self._extract_slots.add(feature.slot)
        self.features.append(feature)
        self.feed_names.append(feature.name)
        self.feed_slot_names.append(feature.slot)
        

    def extract_one(self, instance, slots):
        """
        extract_one
        """
        pass
