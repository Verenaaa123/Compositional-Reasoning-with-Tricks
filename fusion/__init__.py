def __init__(self):
    self.variable_library = list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') + [chr(i) for i in range(0x03B1,0x03C9 + 1)]
    self.operations_list = [1] * 15 + [2] * 15 + [3] * 15 + [4] * 5 + [5] * 15 + [6] * 15 + [7] * 15 + [8] * 5 + [9] * 5 + [10] * 15
    self.reset_counters()