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
Data operations
"""
from .gpt_dataset import create_gpt_dataset
from .bert_dataset import create_bert_dataset
from .t5_dataset import create_t5_dataset
from .wiki_dataset import create_wiki_dataset
from .downstream_dataset import create_classification_dataset, create_squad_dataset, create_language_model_dataset
from .imagenet_dataset import create_imagenet_dataset