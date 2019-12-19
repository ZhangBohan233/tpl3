import bin.spl_types as typ

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0


class VirtualMachine:
    def __init__(self):
        self.memory_size = 4096
        self.stack_begin = 1
        self.literal_begin = 1024
        self.global_begin = 1024
        self.code_begin = 1024
        self.heap_begin = 1024

        self.pc = 1024  # program counter
        self.sp = 1
        # self.ret = 1

        self.exit_code = 0

        self.memory = bytearray(self.memory_size)

        self.call_stack = []
        self.pc_backup = []
        # self.

        self.op_table = {
            2: self.exit_func,
            3: self.assign,
            4: self.call,
            5: self.return_,
            6: self.goto,
            7: self.push_stack,
            10: self.add_i,
            16: self.eq_i,
            30: self.if_zero_goto
        }

    def load_code(self, codes: bytes):
        literal_len = typ.bytes_to_int(codes[:INT_LEN])
        global_len = typ.bytes_to_int(codes[INT_LEN: INT_LEN * 2])
        self.global_begin += literal_len
        self.code_begin = self.global_begin + global_len
        self.pc = self.code_begin
        copy_len = len(codes) - INT_LEN * 2
        self.heap_begin += copy_len
        self.memory[self.literal_begin: self.heap_begin] = codes[INT_LEN * 2:]

    def run(self):
        self.print_memory()
        while self.pc < self.heap_begin:
            instruction = self.memory[self.pc]
            self.pc += 1
            print(instruction)
            if instruction in self.op_table:
                op = self.op_table[instruction]
                op()
            else:
                print("Unknown instruction {}".format(instruction))
                return
        self.print_memory()
        print("Process finished with exit code {}".format(typ.bytes_to_int(self.memory[1:9])))

    def push_stack(self):
        push_num = typ.bytes_to_int(self.memory[self.pc: self.pc + INT_LEN])
        self.pc += INT_LEN
        self.sp += push_num
        print("push to", self.sp)

    def read_3_ints(self) -> (int, int, int):
        i1 = typ.bytes_to_int(self.memory[self.pc:self.pc + INT_LEN])
        i2 = typ.bytes_to_int(self.memory[self.pc + INT_LEN:self.pc + INT_LEN * 2])
        i3 = typ.bytes_to_int(self.memory[self.pc + INT_LEN * 2:self.pc + INT_LEN * 3])
        self.pc += INT_LEN * 3
        return i1, i2, i3

    def read_4_ints(self) -> (int, int, int, int):
        i1, i2, i3 = self.read_3_ints()
        i4 = typ.bytes_to_int(self.memory[self.pc:self.pc + INT_LEN])
        self.pc += INT_LEN
        return i1, i2, i3, i4

    def assign(self):
        tar, src, length = self.read_3_ints()
        # self.pc += INT_LEN * 3
        real_tar = self.generate_true_ptr(tar)
        real_src = self.generate_true_ptr(src)
        self.mem_copy(real_src, real_tar, length)

    def call(self):
        func_ptr, r_len, arg_count = self.read_3_ints()
        pc_b = self.pc
        self.pc += arg_count * (PTR_LEN + INT_LEN)  # arg ptr, arg length
        print("call", func_ptr, r_len, arg_count)

        # self.sp += r_len  # reserve the return location

        self.enter_func()

        # TODO: copy args
        for i in range(arg_count):
            arg_ptr = typ.bytes_to_int(self.memory[pc_b:pc_b + PTR_LEN])
            pc_b += PTR_LEN
            arg_len = typ.bytes_to_int(self.memory[pc_b:pc_b + INT_LEN])
            pc_b += INT_LEN
            self.mem_copy(arg_ptr, self.sp, arg_len)
            self.sp += arg_len

        # self.sp += arg_count * PTR_LEN

        self.pc = func_ptr

    def return_(self):
        v_ptr = typ.bytes_to_int(self.memory[self.pc:self.pc + INT_LEN])
        rtn_len = typ.bytes_to_int(self.memory[self.pc + INT_LEN: self.pc + INT_LEN * 2])
        real_v_ptr = self.generate_true_ptr(v_ptr)

        to = self.call_stack[-1] - rtn_len
        print("return", real_v_ptr, rtn_len, to)
        self.mem_copy(real_v_ptr, to, rtn_len)

        self.exit_func()

    def generate_true_ptr(self, i):
        if i < self.literal_begin:
            return i + self.call_stack[-1]
        else:
            return i

    def get(self, pos, length):
        return self.memory[pos:pos + length]

    def set(self, pos: int, byt: bytes):
        self.memory[pos:pos + len(byt)] = byt

    def add_i(self):
        res, lp, rp = self.read_3_ints()
        real_res = self.generate_true_ptr(res)
        real_lp = self.generate_true_ptr(lp)
        real_rp = self.generate_true_ptr(rp)
        lv = self.get(real_lp, INT_LEN)
        rv = self.get(real_rp, INT_LEN)
        res_v = typ.int_add_int(lv, rv)
        self.set(real_res, res_v)

    def enter_func(self):
        print("enter", self.sp)
        self.call_stack.append(self.sp)
        self.pc_backup.append(self.pc)

    def exit_func(self):
        self.sp = self.call_stack.pop()
        self.pc = self.pc_backup.pop()
        print("exit", self.sp)

    def eq_i(self):
        res, lp, rp = self.read_3_ints()
        real_res = self.generate_true_ptr(res)
        real_lp = self.generate_true_ptr(lp)
        real_rp = self.generate_true_ptr(rp)
        lv = self.get(real_lp, INT_LEN)
        rv = self.get(real_rp, INT_LEN)
        res_v = typ.int_cmp_int(lv, rv)

        if res_v == 0:  # equal
            b = 1
        else:
            b = 0
        self.set(real_res, bytes((b,)))

    def goto(self):
        skip_count = typ.bytes_to_int(self.memory[self.pc:self.pc + INT_LEN])
        self.pc += INT_LEN
        self.pc += skip_count

    def if_zero_goto(self):
        skip_len = typ.bytes_to_int(self.memory[self.pc: self.pc + INT_LEN])
        cond_ptr = typ.bytes_to_int(self.memory[self.pc + INT_LEN: self.pc + INT_LEN * 2])
        real_cond_ptr = self.generate_true_ptr(cond_ptr)
        self.pc += INT_LEN * 2
        b = self.memory[real_cond_ptr]
        if b == 0:
            self.pc += skip_len

    def mem_copy(self, from_, to, length):
        self.memory[to:to + length] = self.memory[from_:from_ + length]

    def print_memory(self):
        print("STACK: ", list(self.memory[:self.literal_begin]))
        print("LITERAL: ", list(self.memory[self.literal_begin: self.global_begin]))
        print("GLOBAL: ", list(self.memory[self.global_begin:self.code_begin]))
        print("CODES: ", list(self.memory[self.code_begin:self.heap_begin]))
        print("HEAP: ", list(self.memory[self.heap_begin:]))
