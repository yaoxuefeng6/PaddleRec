'''
@Author: yao xuefeng
@Date: 2020-05-19 11:11:24
@LastEditTime : 2020-05-20 15:32:58
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /Hi_ranker/elastic-ctr-baiduhi/retrieval/servers/slot_reader.py
'''
from __future__ import print_function

from paddlerec.core.reader import Reader
from paddlerec.core.utils import envs

import json
import proto.user_info_pb2 as user_info_pb2
import proto.item_info_pb2 as item_info_pb2
import pbjson
import feature_extractor
import instance
import feature_provider
import sys

class EvaluateReader(Reader):
    def init(self):
       self._feature_extractor = feature_extractor.FeatureExtractor("conf/slot_list.conf")

    
    def generate_sample(self, line):
        """
        Read the data line by line and process it as a dictionary
        """

        def reader():
            """
            This function needs to be implemented by the user, based on data format
            """
            def check_feasign(feasign):
                if len(feasign) == 0:
                    return [0]
                return feasign
            
            #print line 
            pb_ins_user = None
            pb_ins_item = None
            cur_map = json.loads(line)
            label =  [1] if cur_map["behaviour"]["action"]=="click" else [0]
            log_hash = [hash(cur_map["log_id"])]
            #print(cur_map["feature"])
            if "feature" in cur_map.keys():
                #feature_map = cur_map["feature"]
                if 'user_info' in cur_map["feature"].keys():
                    # because change long_interests to long_topic 
                    if ("long_topics" not in cur_map["feature"]["user_info"].keys()) and ("longterm_interests" in cur_map["feature"]["user_info"].keys()):
                        cur_map["feature"]["user_info"]["long_topics"] = cur_map["feature"]["user_info"]["longterm_interests"]
                    pb_ins_user = pbjson.dict2pb(user_info_pb2.UserInfo, cur_map["feature"]["user_info"])
                if 'item_info' in cur_map['feature'].keys():
                    pb_ins_item = pbjson.dict2pb(item_info_pb2.ItemInfo, cur_map["feature"]["item_info"])
            if pb_ins_user == None or pb_ins_item == None:
                return 
            user_info = pb_ins_user
            item_info = pb_ins_item
            self._feature_provider = feature_provider.FeatureProvider("conf/slot_list.conf", user_info, [item_info])
            ins = instance.Instance(self._feature_extractor, self._feature_provider)
            ins.provide_from_proto(user_info, item_info, 0)
            slots = self._feature_extractor.get_feed_slots()
            ins.extract(slots)
            feature_name = ins.feed_names
            feed_feature_name = ins.feed_slot_names
            sparse_feature = [None] * len(feature_name)
            for i, name in enumerate(feature_name):
                #print("whole hash value: {}".format(ins.hash_feature))
                #print("---------- {} --------".format(ins._feature_extractor.get_feature_index(name)))
                #print("print this feed name: {} >>>> {}".format(name, ins.hash_feature[ins._feature_extractor.get_feature_index(name)]))
                sparse_feature[i] = check_feasign( ins.hash_feature[ins._feature_extractor.get_feature_index(name)] )
                
            
            
            yield zip(["label"] + ["log_hash"] + feed_feature_name, [label] + [log_hash] + sparse_feature)
            

        return reader

'''
if __name__ == "__main__":
    #reader = TrainReader("config.yaml")
    reader = TrainReader()
    reader.init()
    for line in sys.stdin:
        line_iter = reader.generate_sample(line)
        for l in line_iter():
            print(l)
'''            
