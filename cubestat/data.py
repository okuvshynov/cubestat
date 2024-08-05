import collections
import itertools


class DataManager:
    def __init__(self, buffer_size):

        def init_series():
            return collections.deque(maxlen=buffer_size)

        def init_group():
            return collections.defaultdict(init_series)

        self.data = collections.defaultdict(init_group)

    # TODO: UI-related things should be moved out of here
    def get_slice(self, series, h_shift, chart_width):
        data_length = len(series) - h_shift if h_shift > 0 else len(series)
        index = max(0, data_length - chart_width)
        return list(itertools.islice(series, index, min(index + chart_width, data_length)))

    def update(self, updates):
        for (group, title, value) in updates:
            self.data[group][title].append(value)

    def data_gen(self):
        for group_name, group in self.data.items():
            for title, series in group.items():
                yield (group_name, title, series)
