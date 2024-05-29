import json
import numpy as np
import pandas as pd
import networkx as nx

from pyvis.network import Network
from datetime import datetime


class TraceGraphNetworkBuilder:
    """
    """

    def __init__(self):
        self.time_stamp = datetime.now().strftime('%Y:%m:%d:%H:%M:%S')
        self.save_path_list = [
            '/home/vu24/Desktop/kernel_graph.html',
            f'kernel_graph_records/kernel_graph_{self.time_stamp}.html'
        ]

        self.log_parser = LogParser()
        self.trace_df = self.log_parser.trace_log_combined
        self.num_rows = self.trace_df.shape[0]

        self.graph = nx.DiGraph()
        self.node_0_distances = None
        self.max_path = None
        self.max_node_size = 27

        self.network = Network(
            notebook=True,
            directed=True,
            height="2400",
            bgcolor="#000000",
            font_color="white",
        )
        # self.network = Network(notebook=False, directed=True)
        self.default_node_size = None

        self.do()

    def do(self):
        self.populate_graph()
        self.set_pid_range()
        self.populate_network()
        self.save_network()

    def get_pid_proportion(self, pid):
        path_list = self.node_0_distances[pid]
        path_length = len(path_list)
        proportion = path_length / self.max_path
        return proportion

    def get_rgb(self, pid):
        if pid not in self.node_0_distances:
            rgb_input = f"rgb(210, 210, 210)"
        else:
            pid_proportion = self.get_pid_proportion(pid)
            # path_list = self.node_0_distances[pid]
            # path_length = len(path_list)
            #
            # green_val = int((path_length / self.max_path) * 255)
            green_val = int(pid_proportion * 255)
            rgb_input = f"rgb({255-green_val}, {green_val}, {255-green_val})"
            # rgb_input = f"rgb({255-green_val}, {green_val}, 150)"
        return rgb_input

    def get_node_size(self, pid):
        if pid not in self.node_0_distances:
            pid_proportion = 1.0
        else:
            pid_proportion = self.get_pid_proportion(pid)

        node_size = self.max_node_size * (1 - 0.75*pid_proportion)

        return node_size

    def set_pid_range(self):
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

        options = {
            "hierarchical": {
               "enabled": True,
               "levelSeparation": 4000,
               "nodeSpacing": 32000,
               "treeSpacing": 8000,
               "directed": "UD",
               "sortMethod": "directed",
            }
        }
        # options = {
        #     "physics": {
        #         "barnesHut": {
        #             "gravitationalConstant": -10000,
        #             "centralGravity": 0.05,
        #             "springLength": 10,
        #             "springConstant": 0.05,
        #             "damping": 0.7,
        #             "avoidOverlap": 1.0
        #         }
        #     }
        # }
        #            # "avoidOverlap": 1.0

        self.network.set_options(json.dumps(options))

        max_string_len = 21
        max_lines = 3
        for node in self.graph.nodes(data=True):
            pid = node[0]
            label_i = f'PID: {pid}'
            if len(node) > 1:
                keys = node[1].keys()
                if 'label' in keys:
                    command_string = node[1]['label']
                    command_string = self.add_newlines(command_string, max_string_len, max_lines)
                    label_i = f'{label_i}:\n {command_string}'
            # label_i = self.add_newlines(label_i, max_string_len)
            node_color = self.get_rgb(pid)
            node_size = self.get_node_size(pid)
            self.network.add_node(
                pid,
                label=label_i,
                color=node_color,
                size=node_size,
                style='filled',
            )

        for edge in self.graph.edges():
            self.network.add_edge(edge[0], edge[1])

    def save_network(self):
        # self.network.show_buttons(filter_=['physics'])
        for save_path in self.save_path_list:
            self.network.show(save_path)
            # self.network.write_html(save_path)

    @staticmethod
    def add_newlines(long_string, max_line_length, max_num_lines):
        string_len = len(long_string)
        newline_indexes = list(range(max_line_length, string_len, max_line_length))

        for newline_index in reversed(newline_indexes):
            prefix = long_string[:newline_index]
            postfix = long_string[newline_index + 1:]

            long_string = ''.join([prefix, '\n', postfix])

        if string_len > max_num_lines*max_line_length:
            long_string = long_string[:max_num_lines*max_line_length-3]
            long_string = long_string + '...'

        return long_string


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
        self.trace_log_combined.to_csv('/home/vu24/Desktop/trace_log_combined.csv')
        time_stamp = datetime.now().strftime('%Y:%m:%d:%H:%M:%S')
        self.trace_log_combined.to_csv(f'trace_log_records/trace_log_combined{time_stamp}.csv', index=False)


if __name__ == '__main__':
    trace_parser = TraceGraphNetworkBuilder()

