class MemoryException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class Memory:
    def __init__(self):
        self.stack_size = 1024
        self.literal_size = 1024
        self.heap_size = 1024
        self.memory = bytearray(self.stack_size + self.literal_size + self.heap_size)
        self.available = [i + self.stack_size + self.literal_size for i in range(self.heap_size - 1, -1, -1)]

        self.sp = 1
        self.lp = self.stack_size
        self.call_stack_begins = []
        # self.string_lengths = {}

        self.type_sizes = {
            "int": 8,
            "float": 8,
            "boolean": 1,
            "char": 1,
            "void": 0
        }
        self.pointer_length = self.type_sizes["int"]

    def get_type_size(self, name: str):
        if name[0] == "*":  # is a pointer
            return self.pointer_length
        return self.type_sizes[name]

    def add_type(self, name: str, length: int):
        self.type_sizes[name] = length

    def allocate(self, byt: bytearray) -> int:
        length = len(byt)
        ptr = self.allocate_empty(length)
        self.set(ptr, byt)
        return ptr

    def allocate_empty(self, length: int) -> int:
        ptr = self.sp
        self.sp += length
        if self.sp >= self.stack_size:
            raise MemoryException("Stack overflow")
        return ptr

    def push_stack(self):
        self.call_stack_begins.append(self.sp)

    def restore_stack(self):
        self.sp = self.call_stack_begins.pop()

    def set(self, ptr: int, b: bytes):
        self._check_range(ptr)
        self.memory[ptr: ptr + len(b)] = b

    def get(self, ptr, length) -> bytes:
        self._check_range(ptr)
        return self.memory[ptr: ptr + length]

    def mem_copy(self, from_ptr, to_ptr, length):
        b = self.get(from_ptr, length)
        self.set(to_ptr, b)

    def load_literal(self, literal_bytes: bytes):
        # self.string_lengths = {}
        # ls = self._literal_starts()
        # for k in string_lengths:
        #     self.string_lengths[k + ls] = string_lengths[k]
        length = len(literal_bytes)
        if length > self.literal_size:
            raise MemoryException("Too many literals")
        ls = self._literal_starts()
        self.memory[ls: ls + length] = literal_bytes

    def get_literal_ptr(self, lit_loc) -> int:
        return self._literal_starts() + lit_loc

    def get_char_array(self, ptr) -> bytes:
        end = ptr
        while self.memory[end] != 0:
            end += 1
        return self.get(ptr, end - ptr)

    # def get_literal(self, lit_loc, lit_type) -> bytes:
    #     lit_ptr = lit_loc + self.stack_size
    #     if lit_type == 0:
    #         return self.get(lit_ptr, self.get_type_size("int"))
    #     elif lit_type == 1:
    #         return self.get(lit_ptr, self.get_type_size("float"))
    #     elif lit_type == 2:
    #         return self.get(lit_ptr, self.get_type_size("boolean"))
    #     elif lit_type == 3:
    #         # length = self.string_lengths[lit_ptr]
    #         return self.get(lit_ptr, length)
    #     else:
    #         raise MemoryException("Unexpected literal type")

    # def get_string(self, ptr):
    #     length = self.string_lengths[ptr]
    #     return self.get(ptr, length)

    def malloc(self, length) -> int:
        """
        Allocate memory of length <length> in the heap space and returns the pointer this memory to the user.

        This method will store extra information in the heap.

        :param length:
        :return:
        """
        reserved_len = self.get_type_size("int")
        total_len = length + reserved_len
        ind = self._find_available(total_len)
        loc = self.available[ind]
        self.available[ind - total_len + 1: ind + 1] = []
        b_len = int_to_bytes(length)
        self.set(loc, b_len)  # stores the allocated length before the returned position
        return loc + reserved_len

    def free(self, ptr):
        reserved_len = self.get_type_size("int")
        b_len = self.get(ptr - reserved_len, reserved_len)
        allocated_len = bytes_to_int(b_len)
        length = allocated_len + reserved_len
        for i in range(length):
            ava = ptr + length - i - 5
            self._check_in_heap(ava)
            self.available.append(ava)

    # def is_literal_ptr(self, ptr: int) -> bool:
    #     return self._literal_starts() <= ptr < self._heap_starts()

    # def is_string_literal(self, ptr: int) -> bool:
    #     return ptr in self.string_lengths

    def print_memory(self):
        print("stack pointer: {}, heap available: {}".format(self.sp, len(self.available)))
        print(self.memory[:self.stack_size])
        print(self.memory[self.stack_size:self.stack_size + self.literal_size])
        print(self.memory[self.stack_size + self.literal_size:])

    def _check_range(self, ptr: int):
        if ptr == 0:
            raise MemoryException("Trying to access null pointer")
        if self.sp <= ptr < self.stack_size:
            raise MemoryException("Unreachable stack location {}. Current tp: {}".format(ptr, self.sp))
        if ptr < 0 or ptr >= self._total_length():
            raise MemoryException("Unreachable memory location {}.".format(ptr, self.sp))

    def _total_length(self):
        return self.stack_size + self.literal_size + self.heap_size

    def _check_in_heap(self, ptr: int):
        if ptr < self._heap_starts() or ptr >= self._heap_ends():
            raise MemoryException("Pointer to {} is not in heap".format(ptr))

    def _find_available(self, length) -> int:
        """
        Finds a consecutive heap address of length <length> and returns the first address.

        :param length:
        :return:
        """
        i = len(self.available) - 1
        while i >= 0:
            j = 0
            while j < length - 1 and i - j > 0:
                if self.available[i - j - 1] != self.available[i - j] + 1:
                    break
                j += 1
            if j == length - 1:
                return i
            else:
                i -= j + 1
        raise MemoryException("No space to malloc an object of length {}".format(length))

    def _heap_starts(self):
        return self.stack_size + self.literal_size

    def _heap_ends(self):
        return self.stack_size + self.literal_size + self.heap_size

    def _literal_starts(self):
        return self.stack_size


MEMORY = Memory()


def int_to_bytes(i: int) -> bytes:
    int_len = MEMORY.get_type_size("int")
    return i.to_bytes(int_len, "big", signed=True)


def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, "big", signed=True)


if __name__ == "__main__":
    m = Memory()
