# Copyright 2022 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""
Data operations, will be used in run_pretrain.py
"""
import os
import numpy as np
import mindspore.common.dtype as mstype
import mindspore.dataset as ds
import mindspore.dataset.transforms.c_transforms as C
from mindspore import log as logger


class BucketDatasetGenerator:
    """
    Provide data distribution of different gears for the bert network.

    Args:
        dataset (Dataset): The training dataset.
        batch_size (Int): The training batchsize.
        bucket_list (List): List of different sentence lengths，such as [128, 256, 512]. Default: None.
    """

    def __init__(self, dataset, batch_size, bucket_list=None):
        self.dataset = dataset
        self.batch_size = batch_size
        self.bucket_list = bucket_list
        self.data_bucket = {bucket: [] for bucket in bucket_list}
        bucket_size = len(bucket_list)
        self.random_list = np.random.binomial(n=(bucket_size - 1), p=0.55, size=self.__len__())
        self.random_list = (self.random_list + 2) % bucket_size
        self.random_list = [bucket_list[i] for i in self.random_list]
        self.iter = 0

    def __next__(self):
        for item in self.iterator:
            for seq_length in self.bucket_list:
                if np.sum(item[1]) <= seq_length:
                    self.data_bucket[seq_length].append(item)
                    break
            for key in self.data_bucket.keys():
                data = self.data_bucket[key]
                if len(data) >= self.batch_size and self.random_list[self.iter] == key:
                    self.data_bucket[key] = self.data_bucket[key][self.batch_size:]
                    arr = data[0]
                    for i in range(1, self.batch_size):
                        current_data = data[i]
                        for j in range(len(current_data)):
                            arr[j] = np.concatenate((arr[j], current_data[j]))
                    res = ()
                    for label in arr:
                        newlabel = np.reshape(label, (self.batch_size, -1))
                        res += (newlabel,)
                    res += (np.array(key, np.int32),)
                    self.iter += 1
                    return res
        raise StopIteration

    def __iter__(self):
        self.iterator = self.dataset.create_tuple_iterator(output_numpy=True)
        return self

    def __len__(self):
        return (self.dataset.get_dataset_size() // self.batch_size) - 1


def create_bert_dataset(config):
    """Create bert dataset"""
    device_num = config.dataset_device_num
    rank = config.dataset_rank
    batch_size = config.dataset_batch_size
    data_dir = config.dataset_path
    do_shuffle = config.dataset_do_shuffle
    schema_dir = config.dataset_schema_dir
    bucket_list = config.dataset_bucket_list
    # apply repeat operations
    print("device num", device_num, rank, do_shuffle, data_dir, schema_dir, batch_size, bucket_list)
    files = os.listdir(data_dir)
    data_files = []
    for file_name in files:
        if "tfrecord" in file_name:
            data_files.append(os.path.join(data_dir, file_name))
    data_set = ds.TFRecordDataset(data_files, schema_dir if schema_dir != "" else None,
                                  columns_list=["input_ids", "input_mask", "segment_ids", "next_sentence_labels",
                                                "masked_lm_positions", "masked_lm_ids", "masked_lm_weights"],
                                  shuffle=ds.Shuffle.FILES if do_shuffle == "true" else False,
                                  num_shards=device_num, shard_id=rank, shard_equal_rows=True)
    if bucket_list:
        bucket_dataset = BucketDatasetGenerator(data_set, batch_size, bucket_list=bucket_list)
        data_set = ds.GeneratorDataset(bucket_dataset,
                                       column_names=["input_ids", "input_mask", "segment_ids", "next_sentence_labels",
                                                     "masked_lm_positions", "masked_lm_ids", "masked_lm_weights",
                                                     "sentence_flag"],
                                       shuffle=False)
    else:
        data_set = data_set.batch(batch_size, drop_remainder=True)
    ori_dataset_size = data_set.get_dataset_size()
    print('origin dataset size: ', ori_dataset_size)
    type_cast_op = C.TypeCast(mstype.int32)
    data_set = data_set.map(operations=type_cast_op, input_columns="masked_lm_ids")
    data_set = data_set.map(operations=type_cast_op, input_columns="masked_lm_positions")
    data_set = data_set.map(operations=type_cast_op, input_columns="next_sentence_labels")
    data_set = data_set.map(operations=type_cast_op, input_columns="segment_ids")
    data_set = data_set.map(operations=type_cast_op, input_columns="input_mask")
    data_set = data_set.map(operations=type_cast_op, input_columns="input_ids")
    # apply batch operations
    logger.info("data size: {}".format(data_set.get_dataset_size()))
    logger.info("repeat count: {}".format(data_set.get_repeat_count()))
    return data_set


def create_ner_dataset(batch_size=1, assessment_method="accuracy", data_file_path=None,
                       dataset_format="mindrecord", schema_file_path=None, do_shuffle=True, drop_remainder=True):
    """create finetune or evaluation dataset"""
    type_cast_op = C.TypeCast(mstype.int32)
    if dataset_format == "mindrecord":
        dataset = ds.MindDataset([data_file_path],
                                 columns_list=["input_ids", "input_mask", "segment_ids", "label_ids"],
                                 shuffle=do_shuffle)
    else:
        dataset = ds.TFRecordDataset([data_file_path], schema_file_path if schema_file_path != "" else None,
                                     columns_list=["input_ids", "input_mask", "segment_ids", "label_ids"],
                                     shuffle=do_shuffle)
    if assessment_method == "Spearman_correlation":
        type_cast_op_float = C.TypeCast(mstype.float32)
        dataset = dataset.map(operations=type_cast_op_float, input_columns="label_ids")
    else:
        dataset = dataset.map(operations=type_cast_op, input_columns="label_ids")
    dataset = dataset.map(operations=type_cast_op, input_columns="segment_ids")
    dataset = dataset.map(operations=type_cast_op, input_columns="input_mask")
    dataset = dataset.map(operations=type_cast_op, input_columns="input_ids")
    # apply batch operations
    dataset = dataset.batch(batch_size, drop_remainder=drop_remainder)
    return dataset
