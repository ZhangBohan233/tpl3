import bin.spl_types as typ

INT_LEN = 8
PTR_LEN = 8


class VirtualMachine:
    def __init__(self):
        self.memory_size = 4096
        self.stack_size = 1024
        self.literal_size = 0
        self.code_length = 0

        self.code_ptr = 0

        self.exit_code = 0

        self.memory = bytearray(self.memory_size)

        self.op_table = {
            3: self.assign,
            10: self.add_i
        }

    def load_code(self, code: bytes):
        self.memory[self._literal_starts(): self._literal_starts() + len(code) - INT_LEN] = code[INT_LEN:]
        self.literal_size = typ.bytes_to_int(code[:INT_LEN])
        self.code_length = len(code) - self.literal_size - INT_LEN

    def interpret(self):
        while self.code_ptr < self.code_length:
            op_code = self.read_one()
            op = self.op_table[op_code]
            op()

        exit_ptr = 9
        self.exit_code = typ.bytes_to_int(self.memory[exit_ptr:exit_ptr + INT_LEN])
        print(self.exit_code)
        # self.print_memory()

    def read_int(self):
        cp = self._cp()
        i = typ.bytes_to_int(self.memory[cp: cp + INT_LEN])
        self.code_ptr += INT_LEN
        return i

    def read_one(self):
        b = self.memory[self._cp()]
        self.code_ptr += 1
        return b

    def assign(self):
        cp = self._cp()
        tar_b = self.memory[cp: cp + INT_LEN]
        src_b = self.memory[cp + INT_LEN: cp + INT_LEN * 2]
        len_b = self.memory[cp + INT_LEN * 2: cp + INT_LEN * 3]
        self.code_ptr += INT_LEN * 3
        tar = typ.bytes_to_int(tar_b)
        src = typ.bytes_to_int(src_b)
        length = typ.bytes_to_int(len_b)
        self.mem_copy(tar, src, length)

    def add_i(self):
        cp = self._cp()
        res_b = self.memory[cp: cp + INT_LEN]
        lb = self.memory[cp + INT_LEN: cp + INT_LEN * 2]
        rb = self.memory[cp + INT_LEN * 2: cp + INT_LEN * 3]
        self.code_ptr += INT_LEN * 3
        res_p = typ.bytes_to_int(res_b)
        lp = typ.bytes_to_int(lb)
        rp = typ.bytes_to_int(rb)
        left = self.mem_get(lp, INT_LEN)
        right = self.mem_get(rp, INT_LEN)
        res = typ.int_add_int(left, right)
        self.mem_set(res_p, res)

    def mem_get(self, ptr, length):
        return self.memory[ptr: ptr + length]

    def mem_set(self, ptr, value: bytes):
        self.memory[ptr: ptr + len(value)] = value

    def mem_copy(self, tar, src, length):
        self.memory[tar:tar + length] = self.memory[src: src + length]

    def print_memory(self):
        print(self.memory[:self.stack_size])
        print(self.memory[self.stack_size:self.stack_size + self.literal_size])
        print(self.memory[self._heap_starts():])

    def _cp(self):
        return self._code_starts() + self.code_ptr

    def _literal_starts(self):
        return self.stack_size

    def _code_starts(self):
        return self.stack_size + self.literal_size

    def _heap_starts(self):
        return self.stack_size + self.code_length + self.literal_size
