#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Councilbox Quorum Explorer HTTP API
# Copyright (C) 2018 Rodrigo Martínez Castaño, Councilbox Technology, S.L.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from web3 import Web3
import subprocess


def clean_block(block, extra_data_format=None):
    block.pop('_id')
    block['transactions'] = len(block['transactions'])
    extraData = decode_extra_data(block['extraData'])

    # Istanbul BFT
    if extra_data_format == 'ibft':
        block.pop('extraData')
        block['vanity'] = extraData['vanity']
        block['validators'] = extraData['validators']
        block['seal'] = extraData['seal']
        # Special case for the genesis block
        if 'committed_seals' in extraData:
            block['committedSeals'] = extraData['committed_seals']

def clean_transaction(transaction):
    transaction.pop('_id')
    transaction['from'] = Web3.toChecksumAddress(transaction['from'])
    if 'to' in transaction and transaction['to']:
        transaction['to'] = Web3.toChecksumAddress(transaction['to'])

def get_clean_transaction_row(transaction):
    transaction['from'] = Web3.toChecksumAddress(transaction['from'])
    if 'to' in transaction and transaction['to']:
        transaction['to'] = Web3.toChecksumAddress(transaction['to'])
    return { 'number': str(transaction['_id']),
             'timestamp': transaction['timestamp'],
             'hash': transaction['hash'],
             'from': transaction['from'],
             'to': transaction['to'],
             'value': transaction['value'],
             'v': transaction['v'] }

def clean_account(account):
    account.pop('_id')
    account['address'] = Web3.toChecksumAddress(account['address'])

def get_output(items=None, title=None):
    output = {'type': title,
              'result': None}
    if type(items) == list:
        output['result'] = {'data': items}
    else:
        output['result'] = items
    return output

def decode_extra_data(extraData):
    extraData = extraData.strip()
    args = ['/root/go/bin/istanbul', 'extra',
            'decode', '--extradata', extraData]
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read().decode('utf-8')
    output_array = output.split('\n')

    if not output_array[0]:
        return

    result_dict = {}
    for line in output_array:
        kv = line.split(':')
        if kv[0]:
            if kv[0] == 'validator':
                if not 'validators' in result_dict:
                    result_dict['validators'] = []
                result_dict['validators'].append(kv[1].strip())
            elif kv[0] == 'committed seal':
                if not 'committed_seals' in result_dict:
                    result_dict['committed_seals'] = []
                result_dict['committed_seals'].append(kv[1].strip())
            else:
                result_dict[kv[0].strip()] = kv[1].strip()
    return result_dict
