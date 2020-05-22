'''
@Author: your name
@Date: 2020-05-09 16:14:17
@LastEditTime : 2020-05-09 16:22:01
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /paddlerec/models/rank/hi_dnn/test.py
'''
import json

dest_map = {}
with open("data/train_data_whole/whole_0520", 'r') as f:
    for line in f:
        #print line 
        cur_map = json.loads(line)
        log_id = cur_map["log_id"]
        dest_map["log_hash"] = hash(log_id)
        dest_map["log_id"] = log_id
        json_str = json.dumps(dest_map)
        print(json_str)
