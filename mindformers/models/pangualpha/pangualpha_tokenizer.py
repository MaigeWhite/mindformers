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
"""PanguAlpha Tokenzier"""

import os
from typing import List, Optional
import jieba
import sentencepiece as spm

from mindformers.tools import logger
from mindformers.tools.register import MindFormerRegister, MindFormerModuleType
from mindformers.models.base_tokenizer import Tokenizer
from ...mindformer_book import MindFormerBook


__all__ = ['PanguAlphaTokenizer']

VOCAB_FILES_NAMES = {"vocab_file": "vocab.model"}


@MindFormerRegister.register(MindFormerModuleType.TOKENIZER)
class PanguAlphaTokenizer(Tokenizer):
    r"""
    Tokenize the input string and convert them into the ids. The tokenizer use the sentence piece internally.

    Args:
        vocab_file(str): The vocabulary file path.
        eos_token(str): The token that represents the end-of-sentence. Default "<eod>".
        bos_token(str): The token that represents the begin-of-sentence. Default "<s>"".
        unk_token(str): The token that represents the unknown. Default "<unk>".
        pad_token(str): The token that represents the pad. Default "<pad>".
        add_bos_token(bool): Whether or not to add the bos_token_id to the left of the input. Default "False"
        add_eos_token(bool): Whether or not to add the eos_token_id to the right of the input. Default "False"
        **kwargs: Other kwargs that will be passed into the base class of the `Tokenizer`.

    Examples:
        >>> from mindformers import PanguAlphaTokenizer

        >>> tokenizer = PanguAlphaTokenizer.from_pretrained("pangualpha_2_6b")
        >>> res = tokenizer("你好，今天天气不错。")
        >>> print(res)
        {'input_ids': [5772, 10, 465, 235, 464, 1123, 12], \
        'token_type_ids': [0, 0, 0, 0, 0, 0, 0, 0, 0], \
        'attention_mask': [1, 1, 1, 1, 1, 1, 1]}

    Outputs:
        A dict contains the processed ids, attention_mask that specific by the member `MODEL_INPUT_NAME`
        of the subclass.
    """
    vocab_files_names = VOCAB_FILES_NAMES
    model_input_names = ["input_ids", "attention_mask"]
    FILE_LIST = ['tokenizer_config.json']
    _support_list = MindFormerBook.get_tokenizer_support_list()['pangualpha']

    def __init__(self,
                 vocab_file,
                 eos_token='<eod>',
                 bos_token='<s>',
                 unk_token='<unk>',
                 pad_token='<pad>',
                 add_bos_token=False,
                 add_eos_token=False,
                 **kwargs):
        super(PanguAlphaTokenizer, self).__init__(
            eos_token=eos_token,
            bos_token=bos_token,
            unk_token=unk_token,
            pad_token=pad_token,
            **kwargs
        )
        self.add_bos_token = add_bos_token
        self.add_eos_token = add_eos_token

        self.encoder = {}
        self.sp = spm.SentencePieceProcessor(model_file=vocab_file)

        for i in range(self.sp.get_piece_size()):
            self.encoder[self.sp.id_to_piece(i)] = i
        self.translator = str.maketrans(" \n", "\u2582\u2583")

    def tokenize(self, text, pair=None, add_special_tokens=True, **kwargs):
        if not isinstance(text, str):
            raise ValueError("Text should be type str, but found type", type(text))
        return self._tokenize(text)

    def _tokenize(self, text, **kwargs):
        """ Tokenize a string using bpe encode. """
        seg_list = [x.translate(self.translator) for x in jieba.cut(text, cut_all=False)]
        return seg_list

    def convert_tokens_to_ids(self, tokens):
        """ the index of the tokens in the vocabulary. """
        if isinstance(tokens, str):
            return self._convert_token_to_id(tokens)
        if isinstance(tokens, list):
            tokens = " ".join(tokens)
            return self.sp.encode(tokens)
        return None

    def _convert_token_to_id(self, token):
        """ the index of the tokens in the vocabulary. """
        return self.sp.piece_to_id(token)

    def _convert_id_to_token(self, index):
        """ return the origin bpe tokens according to ids """
        return self.sp.id_to_piece(index)

    def process_tokens(self, text):
        r"""replace special tokens with space and \n"""
        text = text.replace(' ', '').replace('\u2582', ' ').replace('\u2583', '\n')
        return text

    def pangu_encode(self, text):
        """pangu encode"""
        res = self.tokenize(text)
        return res

    def pangu_decode(self, tokens):
        """pangu decode"""
        text = self.sp.decode(tokens)
        return self.process_tokens(text)

    def save_vocabulary(self, save_directory, filename_prefix=None):
        """write the word to the files"""
        if not os.path.isdir(save_directory):
            logger.error("Vocabulary path (%s) should be a directory", save_directory)
            return None

        output_file_path = os.path.join(
            save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab_file"])

        with open(output_file_path, 'w', encoding="utf8") as fp:
            for k in self.encoder:
                fp.write(k + '\n')
        return output_file_path

    @property
    def vocab_size(self):
        return len(self.encoder)

    def build_inputs_with_special_tokens(self, token_ids_0, token_ids_1=None):
        r"""Insert the special tokens to the input_ids. Currently"""
        bos_token_id = [self.bos_token_id] if self.add_bos_token else []
        eos_token_id = [self.eos_token_id] if self.add_eos_token else []

        output = bos_token_id + token_ids_0 + eos_token_id

        if token_ids_1 is not None:
            output = output + bos_token_id + token_ids_1 + eos_token_id

        return output

    def create_token_type_ids_from_sequences(
            self, token_ids_0: List[int], token_ids_1: Optional[List[int]] = None
    ) -> List[int]:
        """
        Creates a mask from the two sequences passed to be used in a sequence-pair classification task. An ALBERT
        sequence pair mask has the following format:

        ```
        0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 1
        | first sequence    | second sequence |
        ```

        if token_ids_1 is None, only returns the first portion of the mask (0s).

        Args:
            token_ids_0 (`List[int]`):
                List of ids.
            token_ids_1 (`List[int]`, *optional*):
                Optional second list of IDs for sequence pairs.

        Returns:
            `List[int]`: List of [token type IDs](../glossary#token-type-ids) according to the given sequence(s).
        """
        bos_token_id = [self.bos_token_id] if self.add_bos_token else []
        eos_token_id = [self.eos_token_id] if self.add_eos_token else []

        output = [0] * len(bos_token_id + token_ids_0 + eos_token_id)

        if token_ids_1 is not None:
            output += [1] * len(bos_token_id + token_ids_1 + eos_token_id)

        return output

    def get_vocab(self):
        """Returns vocab as a dict"""
        vocab = {self.convert_ids_to_tokens(i): i for i in range(self.vocab_size)}
        vocab.update(self.added_tokens_encoder)
        return vocab
