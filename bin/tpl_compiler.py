import bin.spl_ast as ast
import bin.spl_environment as en
import bin.spl_types as typ
import bin.spl_lib as lib

INT_LEN = 8
FLOAT_LEN = 8
PTR_LEN = 8
BOOLEAN_LEN = 1
CHAR_LEN = 1
VOID_LEN = 0


ASSIGN = 3  # ASSIGN   TARGET    SOURCE   LENGTH    | copy LENGTH bytes from SOURCE to TARGET
CALL = 4    # CALL     FN PTR
ADD_I = 10  # ADD_I    RESULT_P  LEFT_P   RIGHT_P   | add the ints pointed by pointers, store the result to RESULT_P


class ByteOutput:
    def __init__(self):
        self.codes = bytearray()

    def __len__(self):
        return len(self.codes)

    def __bytes__(self):
        return bytes(self.codes)

    def assign(self, tar: int, src: int, length: int):
        # print(tar, src, length)
        self.codes.append(ASSIGN)
        self.write_int(tar)
        self.write_int(src)
        self.write_int(length)

    def add_binary_op_int(self, op: int, res: int, left: int, right: int):
        self.codes.append(op)
        self.write_int(res)
        self.write_int(left)
        self.write_int(right)

    def add_call(self, ftn_ptr):
        self.codes.append(CALL)
        self.write_int(ftn_ptr)

    def write_int(self, i):
        self.codes.extend(typ.int_to_bytes(i))

    def reserve_space(self, n) -> int:
        i = len(self.codes)
        self.codes.extend(bytes(n))
        return i

    def set_bytes(self, from_: int, b: bytes):
        self.codes[from_: from_ + len(b)] = b


class MemoryManager:
    def __init__(self, literal_bytes):
        self.stack_begin = 1
        self.sp = 1
        self.literal_begins = 1024
        self.global_begins = 1024 + len(literal_bytes)
        self.gp = self.global_begins

        self.global_bytes = bytearray()

        self.blocks = []

        self.type_sizes = {
            "int": INT_LEN,
            "float": FLOAT_LEN,
            "char": CHAR_LEN,
            "boolean": BOOLEAN_LEN,
            "void": VOID_LEN
        }
        self.pointer_length = PTR_LEN

    def get_type_size(self, name):
        if name[0] == "*":  # is a pointer
            return self.pointer_length
        return self.type_sizes[name]

    def push_stack(self):
        self.blocks.append(self.sp)

    def restore_stack(self):
        self.sp = self.blocks.pop()

    def allocate(self, length) -> int:
        if len(self.blocks) == 0:  # global
            ptr = self.gp
            self.gp += length
        else:  # in call
            ptr = self.sp - self.blocks[-1]
            self.sp += length
        return ptr

    def calculate_lit_ptr(self, lit_num):
        return lit_num + self.literal_begins

    def get_last_call(self):
        return self.blocks[-1]

    def define_func(self, fn_bytes: bytes):
        self.global_bytes.extend(fn_bytes)
        self.gp += len(fn_bytes)


class ParameterPair:
    def __init__(self, name: str, tal: en.Type):
        self.name: str = name
        self.tal = tal

    def __str__(self):
        return "{}".format(self.name)

    def __repr__(self):
        return self.__str__()


class Function:
    def __init__(self, params, outer, r_tal, ptr):
        self.params: [ParameterPair] = params
        # self.annotations = annotations
        # self.body = body
        self.outer_scope = outer
        self.r_tal: en.Type = r_tal
        self.ptr = ptr


class Compiler:
    def __init__(self, literal_bytes: bytes):
        self.memory = MemoryManager(literal_bytes)

        self.node_table = {
            ast.LITERAL: self.compile_literal,
            ast.DEF_STMT: self.compile_def_stmt,
            ast.NAME_NODE: self.compile_name_node,
            ast.BLOCK_STMT: self.compile_block_stmt,
            ast.FUNCTION_CALL: self.compile_call,
            ast.BINARY_OPERATOR: self.compile_binary_op,
            ast.RETURN_STMT: self.compile_return,
            ast.ASSIGNMENT_NODE: self.compile_assignment_node
        }

    def compile_all(self, root: ast.Node) -> bytes:
        bo = ByteOutput()

        env = en.GlobalEnvironment()
        self.compile(root, env, bo)

        if "main" in env.functions:
            main_ptr = env.functions["main"]
            self.function_call(main_ptr, [], env, bo)

        print(env.functions)
        print(self.memory.global_bytes)
        return bytes(bo)

    def compile(self, node: ast.Node, env: en.Environment, bo: ByteOutput):
        nt = node.node_type
        cmp_ftn = self.node_table[nt]
        return cmp_ftn(node, env, bo)

    def compile_block_stmt(self, node: ast.BlockStmt, env: en.Environment, bo: ByteOutput):
        for line in node.lines:
            self.compile(line, env, bo)

    def compile_literal(self, node: ast.Literal, env: en.Environment, bo: ByteOutput):
        return self.memory.calculate_lit_ptr(node.lit_pos)

    def compile_def_stmt(self, node: ast.DefStmt, env: en.Environment, bo: ByteOutput):

        r_tal = get_tal_of_defining_node(node.r_type, env, self.memory)
        ftn_ptr = self.memory.gp
        # env.define_function(node.name, r_tal, self.memory.gp)

        inner_bo = ByteOutput()
        st = inner_bo.reserve_space(INT_LEN)
        scope = en.FunctionEnvironment(env)
        self.memory.push_stack()
        for param in node.params.lines:
            tn: ast.TypeNode = param
            name_node: ast.NameNode = tn.left
            tal = get_tal_of_defining_node(tn.right, env, self.memory)
            total_len = tal.total_len(self.memory)
            ptr = self.memory.allocate(total_len)
            scope.define_var(name_node.name, tal, ptr)

        self.compile(node.body, scope, inner_bo)
        func_len = len(inner_bo) - st - INT_LEN
        len_b = typ.int_to_bytes(func_len)
        inner_bo.set_bytes(st, len_b)

        self.memory.restore_stack()
        self.memory.define_func(bytes(inner_bo))

        ftn = Function()

        # bo.add_function(bytes(inner_bo))

    def compile_name_node(self, node: ast.NameNode, env: en.Environment, bo: ByteOutput):
        pass

    def compile_assignment_node(self, node: ast.AssignmentNode, env: en.Environment, bo: ByteOutput):
        r = self.compile(node.right, env, bo)
        lf = node.line_num, node.file

        if node.left.node_type == ast.NAME_NODE:
            if node.level == ast.ASSIGN:
                ptr = env.get(node.left.name, lf)
                tal = get_tal_of_evaluated_node(node.left, env)
                total_len = tal.total_len(self.memory)

                bo.assign(ptr, r, total_len)

        elif node.left.node_type == ast.TYPE_NODE:
            type_node: ast.TypeNode = node.left
            if node.level == ast.VAR:
                tal = get_tal_of_defining_node(type_node.right, env, self.memory)
                total_len = tal.total_len(self.memory)
                ptr = self.memory.allocate(total_len)
                env.define_var(type_node.left.name, tal, ptr)

                bo.assign(ptr, r, total_len)

    def compile_call(self, node: ast.FuncCall, env: en.Environment, bo: ByteOutput):
        assert node.call_obj.node_type == ast.NAME_NODE

        lf = node.line_num, node.file

        # TODO: check is native function
        ftn_ptr = env.get_function(node.call_obj.name, lf)

        args = []
        for arg_node in node.args.lines:
            tal = get_tal_of_evaluated_node(arg_node, env)
            total_len = tal.total_len(self.memory)

            arg_ptr = self.compile(arg_node, env, bo)
            tup = arg_ptr, total_len
            args.append(tup)

        return self.function_call(ftn_ptr, args, env, bo)

    def function_call(self, func_ptr: int, args: list, call_env: en.Environment, bo: ByteOutput):
        bo.add_call(func_ptr)
        bo.write_int(len(args))
        for arg in args:
            bo.write_int(arg[1])
            bo.write_int(arg[0])

    def compile_binary_op(self, node: ast.BinaryOperator, env: en.Environment, bo: ByteOutput):
        pass

    def compile_return(self, node: ast.ReturnStmt, env: en.Environment, bo: ByteOutput):
        pass


def get_tal_of_defining_node(node: ast.Node, env: en.Environment, mem: MemoryManager) -> en.Type:
    if node.node_type == ast.NAME_NODE:
        node: ast.NameNode
        return en.Type(node.name)
    # elif node.node_type == ast.INDEXING_NODE:  # array
    #     node: ast.IndexingNode
    #     tn_al_inner: en.Type = get_tal_of_defining_node(node.call_obj, env, mem)
    #     if len(node.arg.lines) == 0:
    #         return en.Type(tn_al_inner.type_name, 0)
    #     arr_len_ptr = evaluate(node.arg, env)
    #     arr_len_b = mem.MEMORY.get(arr_len_ptr, INT_LEN)
    #     arr_len_v = typ.bytes_to_int(arr_len_b)
    #     # return type_name, arr_len_inner * typ.bytes_to_int(arr_len_b)
    #     return en.Type(tn_al_inner.type_name, *tn_al_inner.array_lengths, arr_len_v)
    elif node.node_type == ast.UNARY_OPERATOR:
        node: ast.UnaryOperator
        tal = get_tal_of_defining_node(node.value, env, mem)
        if node.operation == "unpack":
            return en.Type("*" + tal.type_name, *tal.array_lengths)
        else:
            raise lib.UnexpectedSyntaxException()


LITERAL_TYPE_TABLE = {
    0: en.Type("int"),
    1: en.Type("float"),
    2: en.Type("boolean"),
    3: en.Type("string"),
    4: en.Type("char")
}


def get_tal_of_evaluated_node(node: ast.Node, env: en.Environment) -> en.Type:
    if node.node_type == ast.LITERAL:
        node: ast.Literal
        return LITERAL_TYPE_TABLE[node.lit_type]
    elif node.node_type == ast.STRING_LITERAL:
        node: ast.StringLiteralNode
        return en.Type("char", node.byte_length)
    elif node.node_type == ast.NAME_NODE:
        node: ast.NameNode
        return env.get_type_arr_len(node.name, (node.line_num, node.file))
    elif node.node_type == ast.UNARY_OPERATOR:
        node: ast.UnaryOperator
        tal = get_tal_of_evaluated_node(node.value, env)
        if node.operation == "unpack":
            if len(tal.type_name) > 1 and tal.type_name[0] == "*":
                return en.Type(tal.type_name[1:])
            else:
                raise lib.TypeException("Cannot unpack a non-pointer type")
        elif node.operation == "pack":
            return en.Type("*" + tal.type_name)
        else:
            return tal
    elif node.node_type == ast.BINARY_OPERATOR:
        node: ast.BinaryOperator
        return get_tal_of_evaluated_node(node.left, env)
    elif node.node_type == ast.FUNCTION_CALL:
        node: ast.FuncCall
        call_obj = node.call_obj
        if call_obj.node_type == ast.NAME_NODE:
            func: Function = env.get_function(call_obj.name, (node.line_num, node.file))
            return func.r_tal
    elif node.node_type == ast.INDEXING_NODE:  # array
        node: ast.IndexingNode
        # return get_tal_of_ordinary_node(node.call_obj, env)
        tal_co = get_tal_of_evaluated_node(node.call_obj, env)
        if en.is_array(tal_co):
            return en.Type(tal_co.type_name, *tal_co.array_lengths[1:])
        elif tal_co.type_name[0] == "*":
            return en.Type(tal_co.type_name[1:])
        else:
            raise lib.TypeException()
    elif node.node_type == ast.IN_DECREMENT_OPERATOR:
        node: ast.InDecrementOperator
        return get_tal_of_evaluated_node(node.value, env)
    elif node.node_type == ast.NULL_STMT:
        return en.Type("*void")
