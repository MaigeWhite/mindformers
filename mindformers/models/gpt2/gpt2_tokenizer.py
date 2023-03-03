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
"""GPT2 Tokenzier"""
import json
from functools import lru_cache
from typing import List, Optional
import os
import regex as re

from mindformers.tools.register import MindFormerRegister, MindFormerModuleType
from mindformers.models.base_tokenizer import Tokenizer
from ...mindformer_book import MindFormerBook

__all__ = ['Gpt2Tokenizer']


@lru_cache()
def bytes_to_unicode():
    """
    bytes to unicode
    """
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(2 ** 8):
        if b not in bs:
            bs.append(b)
            cs.append(2 ** 8 + n)
            n += 1
    cs = [chr(i) for i in cs]
    return dict(zip(bs, cs))


def get_pairs(word):
    """
    Return set of symbol pairs in a word.
    Word is represented as tuple of symbols (symbols being variable-length strings).
    """
    pairs = set()
    prev_char = word[0]
    for char in word[1:]:
        pairs.add((prev_char, char))
        prev_char = char
    return pairs


@MindFormerRegister.register(MindFormerModuleType.TOKENIZER)
class Gpt2Tokenizer(Tokenizer):
    """
    Gpt2Tokenizer
    """
    VOCAB_FILES = {'merge_file': 'merges.txt', 'vocab_file': 'vocab.json'}
    FILE_LIST = ['tokenizer_config.json']
    _support_list = MindFormerBook.get_tokenizer_support_list()['gpt2']

    def __init__(
            self,
            vocab_file,
            merge_file,
            unk_token="<|endoftext|>",
            bos_token="<|endoftext|>",
            eos_token="<|endoftext|>",
            pad_token="<|endoftext|>",
            add_prefix_space=False,
            **kwargs
    ):
        super(Gpt2Tokenizer, self).__init__(
            unk_token=unk_token, bos_token=bos_token, eos_token=eos_token, pad_token=pad_token, **kwargs
        )
        with open(vocab_file, 'r', encoding="utf-8") as vocab_handle:
            self.encoder = json.load(vocab_handle)
        self.decoder = {v: k for k, v in self.encoder.items()}
        with open(merge_file, 'r', encoding="utf-8") as merge_handle:
            bpe_merges = merge_handle.read().split('\n')[1:-1]

        self.the_unk_token = unk_token

        bpe_merges = [tuple(merge.split()) for merge in bpe_merges]

        self.bpe_ranks = dict(zip(bpe_merges, range(len(bpe_merges))))
        self.byte_encoder = bytes_to_unicode()
        self.byte_decoder = {v: k for k, v in self.byte_encoder.items()}

        self.pat = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""")
        self.add_prefix_space = add_prefix_space
        self.cache = {}

    def bpe(self, token):
        """ bpe encode """
        if token in self.cache:
            return self.cache[token]

        word = tuple(token)
        pairs = get_pairs(token)
        if not pairs:
            return token

        while True:
            bigram = min(pairs, key=lambda pair: self.bpe_ranks.get(pair, float("inf")))
            if bigram not in self.bpe_ranks:
                break
            first, second = bigram
            new_word = []
            i = 0
            while i < len(word):
                try:
                    j = word.index(first, i)
                except ValueError:
                    new_word.extend(word[i:])
                    break
                else:
                    new_word.extend(word[i:j])
                    i = j

                if word[i] == first and i + 1 < len(word) and word[i + 1] == second:
                    new_word.append(first + second)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_word = tuple(new_word)
            word = new_word
            if len(word) == 1:
                break
            else:
                pairs = get_pairs(word)
        word = " ".join(word)
        self.cache[token] = word
        return word

    def tokenize(self, text):
        if not isinstance(text, str):
            raise ValueError("Text should be type str, but found type", type(text))
        return self._tokenize(text)

    def _tokenize(self, text, **kwargs):
        """ Tokenize a string using bpe encode. """
        text = self.prepare_for_tokenization(text, is_pretokenized=False)
        bpe_tokens = []
        for token in re.findall(self.pat, text):
            token = "".join(
                self.byte_encoder[b] for b in token.encode("utf-8")
            )
            bpe_tokens.extend(bpe_token for bpe_token in self.bpe(token).split(" "))
        return bpe_tokens

    def _convert_tokens_to_ids(self, tokens):
        """ the index of the tokens in the vocabulary. """
        if isinstance(tokens, str):
            return self.encoder.get(tokens, self.encoder.get(self.the_unk_token))
        output = []
        for token in tokens:
            output.append(self.encoder.get(token, self.encoder.get(self.the_unk_token)))
        return output

    def _convert_ids_to_tokens(self, ids):
        """ return the origin bpe tokens according to ids """
        if isinstance(ids, int):
            return self.decoder.get(ids)

        if isinstance(ids, list):
            output = []
            for item in ids:
                output.append(self.decoder.get(item))
            return output
        raise TypeError(f"The type of ids should be int or list, but found {type(ids)}.")

    def _convert_tokens_to_string(self, tokens):
        """ return a string according to the list of tokens"""
        text = "".join(tokens)
        text = bytearray([self.byte_decoder[c] for c in text]).decode("utf-8", errors='ignore')
        return text

    def convert_tokens_to_string(self, tokens):
        """Convert the tokens to the string"""
        return self._convert_tokens_to_string(tokens)

    def build_inputs_with_special_tokens(self, token_ids_0: List[int], token_ids_1: Optional[List[int]] = None):
        """
        Build model inputs from a sequence or a pair of sequence by concatenating and adding special tokens.

        A GPT2 sequence has the following format:
        - single sequence: ``<bos> X <eos>``
        - pair of sequences: ``<bos> A <eos> B <eos>``

        Args:
            token_ids_0 (List[int]): List of IDs to which the special tokens will be added
            token_ids_1 (List[int], `optional`, defaults to `None`): Optional second list of IDs for sequence pairs.
        """
        bos = [self.bos_token_id]
        eos = [self.eos_token_id]
        if token_ids_1 is None:
            return bos + token_ids_0 + eos
        return bos + token_ids_0 + eos + token_ids_1 + eos

    def prepare_for_tokenization(self, text, is_pretokenized=False, **kwargs):
        """ whether to add a whitespace in the front of text """
        add_prefix_space = kwargs.pop("add_prefix_space", self.add_prefix_space)
        if is_pretokenized or add_prefix_space:
            text = " " + text
        return text

    def save_vocabulary(self, save_directory, filename_prefix):
        """write the word to the files"""
        output_file_path = os.path.join(save_directory, filename_prefix)
        with open(output_file_path, 'w') as fp:
            for k in self.vocab_dict.keys():
                fp.write(k + '\n')
        return output_file_path

    @property
    def vocab_size(self):
        """Get the vocab size of the """
        return len(self.decoder)
