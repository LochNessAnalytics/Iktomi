import json
from datetime import datetime

import numpy as np
import pandas as pd
import networkx as nx

from pyvis.network import Network


def add_newlines(long_string, max_line_length):
    string_len = len(long_string)
    newline_indexes = list(range(max_line_length, string_len, max_line_length))

    for newline_index in reversed(newline_indexes):
        prefix = long_string[:newline_index]
        postfix = long_string[newline_index + 1:]

        long_string = ''.join([prefix, '\n', postfix])

    return long_string


class TraceGraphNetworkBuilder:
    """
    """

    def __init__(self):
        self.log_parser = LogParser()
        self.trace_df = self.log_parser.trace_log_combined
        self.num_rows = self.trace_df.shape[0]

        self.graph = nx.DiGraph()
        self.node_0_distances = None
        self.max_path = None

        self.network = Network(notebook=True, directed=True)
        self.default_node_size = None

        self.do()

    def do(self):
        self.populate_graph()
        self.set_rgb_range()
        self.populate_network()
        self.save_network()

    def get_rgb(self, pid):
        if pid not in self.node_0_distances:
            rgb_input = f"rgb(210, 210, 210)"
        else:
            path_list = self.node_0_distances[pid]
            path_length = len(path_list)
            green_val = int((path_length / self.max_path) * 255)
            rgb_input = f"rgb({255-green_val}, {green_val}, 150)"
        return rgb_input

    def set_rgb_range(self):
        origin_node = '0'
        self.node_0_distances = nx.single_source_shortest_path(self.graph, origin_node)
        max_length = 0
        for key_i in self.node_0_distances:
            max_length = max(max_length, len(self.node_0_distances[key_i]))
        self.max_path = max_length

    def populate_graph(self):
        for index, row in self.trace_df.iterrows():
            self.graph.add_node(row['PID'], label=row['COMMAND'])
            if not self.graph.has_node(row['PPID']):
                self.graph.add_node(row['PPID'])
            self.graph.add_edge(row['PPID'], row['PID'])

    def populate_network(self):

        # options = {
        #     "hierarchical": {
        #        "enabled": True,
        #        "levelSeparation": 300,
        #        "nodeSpacing": 600,
        #        "treeSpacing": 600,
        #        "directed": "UD",
        #        "sortMethod": "directed",
        #     }
        # }
        options = {
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -17000,
                    "centralGravity": 0.2,
                    "springLength": 50,
                    "springConstant": 0.05,
                    "damping": 0.7,
                    "avoidOverlap": 0.7
                }
            }
        }

        self.network.set_options(json.dumps(options))

        max_string_len = 34
        for node in self.graph.nodes(data=True):
            label_i = f'PID: {node[0]}'
            if len(node) > 1:
                keys = node[1].keys()
                if 'label' in keys:
                    label_i = f'{label_i}:\n {node[1]['label']}'
            label_i = add_newlines(label_i, max_string_len)
            node_color = self.get_rgb(node[0])
            self.network.add_node(node[0], label=label_i, color=node_color)

        for edge in self.graph.edges():
            self.network.add_edge(edge[0], edge[1])

    def save_network(self):

        self.network.show('/home/vu24/Desktop/kernel_graph.html')
        time_stamp = datetime.now().strftime('%Y:%m:%d:%H:%M:%S')
        self.network.show(f'kernel_graph_records/kernel_graph_{time_stamp}.html')


class LogParser:

    def __init__(self):
        self.trace_log_open_name = '/var/log/process_trace.log'
        self.trace_log_init_open_name = '/var/log/process_trace_init.log'
        
        self.trace_log_df = None
        self.trace_log_init_df = None
        self.trace_log_combined = None

        self.do()

    def do(self):
        self.trace_log_df = self.log_parse(self.trace_log_open_name)
        self.trace_log_init_df = self.log_parse(self.trace_log_init_open_name)
        self.log_align()

    @staticmethod
    def log_parse(open_name):
        results_dict = {}
        with open(open_name) as f:
            lines = f.readlines()
            for line in lines:
                line_split = line.split()
                if len(results_dict) == 0:
                    keys = line_split
                    for key in keys:
                        key.capitalize()
                        results_dict[key] = []
                else:
                    for key_index, key in enumerate(keys):
                        if len(line_split) < len(keys):
                            continue
                        if key_index == len(keys) - 1 and len(line_split) > len(keys):
                            arg_string = ''
                            for line_split_elem in line_split[key_index:]:
                                arg_string = ''.join([arg_string, ' ', line_split_elem])
                            results_dict[key].append(arg_string)
                        else:
                            results_dict[key].append(line_split[key_index])
            f.close()

        df_parsed = pd.DataFrame(results_dict)
        return df_parsed

    def log_align(self):

        # trace_log_df_keys = ['PCOMM', 'PID', 'PPID', 'RET', 'ARGS']
        self.trace_log_df.rename(columns={'PCOMM': 'COMMAND'}, inplace=True)
        merge_keys = ['PID', 'PPID', 'COMMAND']

        for index, elem in self.trace_log_df.iterrows():
            elem_args = elem['ARGS'][2:-2]
            elem_command = elem['COMMAND']
            elem['COMMAND'] = f'{elem_command} {elem_args}'

        self.trace_log_combined = pd.concat(
            [
                self.trace_log_init_df[merge_keys],
                self.trace_log_df[merge_keys]
            ], ignore_index=True)


if __name__ == '__main__':
    trace_parser = TraceGraphNetworkBuilder()
    # this_is_a_string = "this is totally 100% a string \\sfasdfa\\ \\ asdfawdfasdf\\ \\ asdfasdf"
    # max_string_len = 3
    # print(this_is_a_string)
    # new_string = add_newlines(this_is_a_string, max_string_len)
    # print(this_is_a_string)

