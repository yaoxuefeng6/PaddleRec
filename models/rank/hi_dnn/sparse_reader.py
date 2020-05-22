'''
@Author: your name
@Date: 2020-05-20 02:13:02
@LastEditTime: 2020-05-20 02:13:03
@LastEditors: your name
@Description: In User Settings Edit
@FilePath: /paddlerec/models/rank/hi_dnn/sparse_reader.py
'''
from __future__ import print_function

from paddlerec.core.reader import Reader
from paddlerec.core.utils import envs
try:
    import cPickle as pickle
except ImportError:
    import pickle
import collections
import sys

class TrainReader(Reader):
    def init(self):
        self.sparse_feature_number = envs.get_global_env("hyper_parameters.sparse_feature_number", 100001, "train.model") 
        self.slots = envs.get_global_env("sparse_inputs_slots", [], "train.model")
        #self.slots = ['1000','2','3','4','5','6','7','8'] 
        #print(self.slots)
        self._all_slots_dict = collections.OrderedDict()
        for index, slot in enumerate(self.slots):
            self._all_slots_dict[slot.strip()] = [False, index + 1]
        
    
    def generate_sample(self, line):
        """
        Read the data line by line and process it as a dictionary
        ligid show clk feasign:slot ......
        """
        def data_iter():
            elements = line.strip().split(' ')
            #print(elements)
            if len(elements) >= 4:
                padding = 0
                output = [("click", [int(elements[2])])]
                output.extend([(slot, []) for slot in self._all_slots_dict])
                for elem in elements[3:]:
                    feasign, slot = elem.split(':')
                    feasign = int(feasign)
                    # for sparse id must be in [0,sparse_feature_number)
                    feasign = feasign % self.sparse_feature_number
                    if not self._all_slots_dict.has_key(slot):
                        continue
                    self._all_slots_dict[slot][0] = True
                    index = self._all_slots_dict[slot][1]
                    output[index][1].append(feasign)
                for slot in self._all_slots_dict:
                    visit, index = self._all_slots_dict[slot]
                    if visit:
                        self._all_slots_dict[slot][0] = False
                    else:
                        output[index][1].append(padding)
                yield output

        return data_iter

'''
if __name__ == "__main__":
    reader = TrainReader()
    reader.init()
    for line in sys.stdin:
        line_iter = reader.generate_sample(line)
        for l in line_iter():
            print(l)
'''            
