# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 15:55:34 CST 2019

@author: chenzhen
"""

import json

import numpy as np

from core import *
from core import Node, Variable
from core.graph import default_graph
from core.graph import get_node_from_graph
from ops import *
from ops.loss import *
from ops.metrics import *
from util import ClassMining


class Saver(object):

    @staticmethod
    def create_node(graph, from_model_json, node_json):
        node_type = node_json['NodeType']
        node_name = node_json['NodeName']
        parents_name = node_json['ParentsName']
        parents = []
        for parent_name in parents_name:
            parent_node = get_node_from_graph(parent_name, graph)
            if parent_node is None:
                parent_node_json = None
                for node in from_model_json:
                    if node['NodeName'] == parent_name:
                        parent_node_json = node

                assert parent_node_json is not None
                parent_node = create_node(
                    graph, from_model_json, parent_node_json)

            parents.append(parent_node)
        return ClassMining.get_instance_by_subclass_name(Node, node_type)(*parents, name=node_name)

    def save(self, graph=None):
        if graph:
            pass
        else:
            graph = default_graph

        self._save_model_and_weights(graph, 'file_path')

    def _save_model_and_weights(self, graph, root_dir):

        model_json = []
        weights_dict = dict()
        for node in graph.nodes:
            node_json = {
                'NodeType': node.__class__.__name__,
                'NodeName': node.name,
                'ParentsName': [parent.name for parent in node.parents],
                'ChildrenName': [child.name for child in node.children]
            }
            if node.value is not None:
                if isinstance(node.value, np.matrix):
                    node_json['Shape'] = node.value.shape
            model_json.append(node_json)

            # 如果节点是Variable类型，保存其值
            if isinstance(node, Variable):
                weights_dict[node.name] = node.value

        with open('./model.json', 'w') as model_file:
            json.dump(model_json, model_file, indent=4)
            print('Save model into file: {}'.format(model_file.name))

        with open('./weights.npz', 'wb') as weights_file:
            np.savez(weights_file, **weights_dict)
            print('Save weights to file: {}'.format(weights_file.name))

    def _restore_nodes(self, graph, from_model_json, from_weights_dict):
        for index in range(len(from_model_json)):
            node_json = from_model_json[index]
            node_name = node_json['NodeName']

            weights = None
            if node_name in from_weights_dict:
                weights = from_weights_dict[node_name]

            target_node = get_node_from_graph(node_name, graph)
            if target_node is None:
                print('Target node {} of type {} not exists, try to create the instance'.format(
                    node_json['NodeName'], node_json['NodeType']))
                target_node = Saver.create_node(
                    graph, from_model_json, node_json)
            target_node.value = weights

    def load(self, model_file_path=None, weights_file_path=None, to_graph=None):
        if to_graph is None:
            to_graph = default_graph

        model_json = []
        weights_dict = dict()
        with open('./model.json', 'r') as model_file:
            model_json = json.load(model_file)

        with open('./weights.npz', 'rb') as weights_file:
            weights_npz_files = np.load(weights_file)
            for file_name in weights_npz_files.files:
                weights_dict[file_name] = weights_npz_files[file_name]
            weights_npz_files.close()
        self._restore_nodes(to_graph, model_json, weights_dict)
