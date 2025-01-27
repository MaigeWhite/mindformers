# Copyright 2023 Huawei Technologies Co., Ltd
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

"""Bloom Config API"""
from mindformers.modules.transformer.moe import MoEConfig
from mindformers.modules.transformer.transformer import default_transformer_config, default_moe_config, \
    TransformerOpParallelConfig
from mindformers.tools.register import MindFormerRegister, MindFormerModuleType
from mindformers.models.utils import convert_mstype
from mindformers.models.base_config import BaseConfig
from mindformers.mindformer_book import MindFormerBook

__all__ = ['BloomConfig']

@MindFormerRegister.register(MindFormerModuleType.CONFIG)
class BloomConfig(BaseConfig):
    """
    Bloom config class which defines the model size
    """

    _support_list = MindFormerBook.get_config_support_list()['bloom']

    def __init__(self,
                 embedding_dropout_prob: float = 0.0,
                 batch_size: int = None,
                 seq_length: int = 1024,
                 vocab_size: int = 250880,
                 hidden_size: int = 64,
                 num_layers: int = 2,
                 num_heads: int = 8,
                 expand_ratio: int = 4,
                 hidden_dropout_rate: float = 0.1,
                 attention_dropout_rate: float = 0.1,
                 unk_token_id: int = 0,
                 bos_token_id: int = 1,
                 eos_token_id: int = 2,
                 pad_token_id: int = 3,
                 param_init_type: str = "float32",
                 embedding_init_type: str = "float32",
                 layernorm_compute_type: str = "float32",
                 softmax_compute_type: str = "float32",
                 compute_dtype: str = "float16",
                 hidden_act: str = 'gelu',
                 parallel_config: TransformerOpParallelConfig = default_transformer_config,
                 checkpoint_name_or_path: str = "",
                 moe_config: MoEConfig = default_moe_config,
                 use_past: bool = False,
                 use_seq_parallel: bool = False,
                 use_select_recompute: bool = False,
                 repetition_penalty: int = 1,
                 max_decode_length: int = 1024,
                 top_k: int = 5,
                 top_p: int = 1,
                 do_sample: bool = True,
                 is_npu_acceleration: bool = False,
                 **kwargs):
        super().__init__(**kwargs)
        self.embedding_dropout_prob = embedding_dropout_prob
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.expand_ratio = expand_ratio
        self.hidden_dropout_rate = hidden_dropout_rate
        self.attention_dropout_rate = attention_dropout_rate
        self.param_init_type = convert_mstype(param_init_type)
        self.embedding_init_type = convert_mstype(embedding_init_type)
        self.layernorm_compute_type = convert_mstype(layernorm_compute_type)
        self.softmax_compute_type = convert_mstype(softmax_compute_type)
        self.compute_dtype = convert_mstype(compute_dtype)
        self.parallel_config = parallel_config
        self.checkpoint_name_or_path = checkpoint_name_or_path
        self.moe_config = moe_config
        self.use_past = use_past
        self.unk_token_id = unk_token_id
        self.bos_token_id = bos_token_id
        self.eos_token_id = eos_token_id
        self.pad_token_id = pad_token_id
        self.hidden_act = hidden_act
        self.use_seq_parallel = use_seq_parallel
        self.use_select_recompute = use_select_recompute
        self.repetition_penalty = repetition_penalty
        self.max_decode_length = max_decode_length
        self.top_k = top_k
        self.top_p = top_p
        self.do_sample = do_sample
        self.is_npu_acceleration = is_npu_acceleration
        if self.batch_size is None:
            self.use_past = False # currently require batch_size = 1
            self.is_npu_acceleration = False # currently require batch_size = 1
