# -*- coding: utf-8 -*-
"""
@Author: your name
@Date: 2020-05-14 14:33:49
@LastEditTime : 2020-05-15 18:39:10
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /elastic-ctr-baiduhi/retrieval/servers/feature_provider.py
"""

class FeatureValue(object):
    def __init__(self):
        self.hash_value = []


class FeatureProvider(object):
    """
    Feature Provider
    """
    def __init__(self, slot_file, user_info, item_info_list):
        """
        constructor
        """
        self._user_info = user_info
        self._item_infos = item_info_list
        self._method_map = {}
        self.origin_features = []
        self.register_provide_method()
        lines = open(slot_file).readlines()
        for line in lines:
            if len(line) == 0 or line[0] == '#':
                continue
            if "origin_feature" in line:
                self.add_origin_field(line)
                break
    
    def register_provide_method(self):
        """
        register provide method
        """
        self._method_map["user_id"] = "user_id_provider"
        self._method_map["item_id"] = "item_id_provider"
        self._method_map["long_topics"] = "long_topics_provider"
        self._method_map["resource"] = "resource_provider"
        self._method_map["tags"] = "tags_provider"
        self._method_map["author_name"] = "author_name_provider"
        self._method_map["image_info"] = "image_info_provider"
        self._method_map["topics"] = "topics_provider"
        self._method_map["create_time"] = "create_time_provider"
        self._method_map["update_time"] = "update_time_provider"
        self._method_map["publish_time"] = "publish_time_provider"
        self._method_map["short_topics"] = "short_topics_provider"
        self._method_map["short_tags"] = "short_tags_provider"
        self._method_map["long_tags"] = "long_tags_provider"
        self._method_map["department"] = "department_provider"
        
    def provide_by_name(self, name, index):
        """
        provide by name
        """
        if name not in self._method_map:
            raise ValueError("name not registed in providers function")
        
        eval_provider = "self.{}({})".format(self._method_map[name], index)
        #print("provide method by name: {}".format(eval_provider))
        #self.user_id_provider(0)
        return eval(eval_provider)

    def get_origin_feature_name(self):
        """
        get origin feature name
        """
        return self.origin_features
    
    def add_origin_field(self, line):
        """
        add origin field
        """
        origin_feature_list = line.split(":")[1].strip().split(", ")
        for origin_feature in origin_feature_list:
            if not origin_feature in self._method_map:
                #print("origin frature: %s not registed in providers" % origin_feature)
                raise ValueError("origin frature: %s not registed in providers" % origin_feature)
            self.origin_features.append(origin_feature)
            
        #print("origin features: {}".format(self.origin_features))
        self._origin_feature_num = len(origin_feature_list)

    def user_id_provider(self, index=0):
        """
        user id provider
        """
        #print("user id provide here: {}".format(self._user_info.user_id))
        #print(self._user_info.user_id)
        return self._user_info.user_id, 0, 0

    def item_id_provider(self, index=0):
        """
        item id provider
        """
        return self._item_infos[index].item_id, 0, 0

    def long_topics_provider(self, index=0):
        """
        long topics provider
        """
        term_list = []
        weight_list = []
        hash_value_list = []
        for topic in self._user_info.long_topics:
            term_list.append(topic.term)
            weight_list.append(topic.weight)
            hash_value_list.append(0)
        return term_list, weight_list, hash_value_list

    def resource_provider(self, index=0):
        """
        resource provider
        """
        #print("in resource provoder with index: {} result: {}".format(index, self._item_infos[index].resource))
        return self._item_infos[index].resource, 0, 0

    def tags_provider(self, index=0):
        """
        tags provider
        """
        term_list = []
        weight_list = []
        hash_value_list = []
        for tag in self._item_infos[index].tags:
            term_list.append(tag.term)
            weight_list.append(tag.weight)
            hash_value_list.append(0)
        return term_list, weight_list, hash_value_list
    
    def author_name_provider(self, index=0):
        return self._item_infos[index].author_name, 0, 0

    def image_info_provider(self, index=0):
        return self._item_infos[index].image_info.image_quality, 0, 0
    
    def topics_provider(self, index=0):
        term_list = []
        weight_list = []
        #hash_value_list = []
        for tag in self._item_infos[index].topics:
            term_list.append(tag.term)
            weight_list.append(tag.weight)
            #hash_value_list.append(0)
        return term_list, weight_list, []
    
    def create_time_provider(self, index=0):
        return self._item_infos[index].create_time, 0, 0

    def update_time_provider(self, index=0):
        return self._item_infos[index].update_time, 0, 0
    
    def publish_time_provider(self, index=0):
        return self._item_infos[index].publish_time, 0, 0

    def short_topics_provider(self, index=0):
        """
        long topics provider
        """
        term_list = []
        weight_list = []
        #hash_value_list = []
        for topic in self._user_info.short_topics:
            term_list.append(topic.term)
            weight_list.append(topic.weight)
            #hash_value_list.append(0)
        return term_list, weight_list, []

    def short_tags_provider(self, index=0):
        """
        long topics provider
        """
        term_list = []
        weight_list = []
        #hash_value_list = []
        for topic in self._user_info.short_tags:
            term_list.append(topic.term)
            weight_list.append(topic.weight)
            #hash_value_list.append(0)
        return term_list, weight_list, []
    
    def long_tags_provider(self, index=0):
        """
        long topics provider
        """
        term_list = []
        weight_list = []
        #hash_value_list = []
        for topic in self._user_info.long_tags:
            term_list.append(topic.term)
            weight_list.append(topic.weight)
            #hash_value_list.append(0)
        return term_list, weight_list, []

    def department_provider(self, index=0):
        return self._user_info.department, 0, 0
