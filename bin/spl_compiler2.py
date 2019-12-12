import bin.spl_ast as ast
import bin.spl_types as typ

INT_LEN = 8


class Compiler:
    def __init__(self, tree):
        self.root: ast.Node = tree
        self.res = bytearray()

    def compile(self):
        self.compile_node(self.root)

    def get_bytes(self) -> bytes:
        return bytes(self.res)

    def compile_node(self, node: ast.Node):
        if node.node_type == 0:
            print("wrong")
        self.write_int(node.node_type)
        if isinstance(node, ast.BlockStmt):  # not using node.node_type because of convenience
            i = len(self.res)
            self.reserve_space(INT_LEN)
            for line in node.lines:
                self.compile_node(line)
            children_end = len(self.res)
            self.write_int(children_end, i)
        elif isinstance(node, ast.NameNode):
            self.write_string(node.name)
        elif isinstance(node, ast.BinaryExpr):
            self.write_string(node.operation)
            if isinstance(node, ast.AssignmentNode):
                self.res.append(node.level)
            i = len(self.res)
            self.reserve_space(INT_LEN * 2)
            self.compile_node(node.left)
            left_end = len(self.res)
            self.compile_node(node.right)
            right_end = len(self.res)
            self.write_int(left_end, i)
            self.write_int(right_end, i + INT_LEN)
        elif isinstance(node, ast.UnaryExpr):
            self.write_string(node.operation)
            i = len(self.res)
            self.reserve_space(INT_LEN)
            self.compile_node(node.value)
            child_end = len(self.res)
            self.write_int(child_end, i)
        elif isinstance(node, ast.Literal):
            if node.is_int:
                self.res.append(0)
                self.write_int(node.literal)
            elif node.is_float:
                self.res.append(1)
                self.write_float(node.literal)
            elif node.is_boolean:
                self.res.append(2)
                self.res.append(node.literal)
            else:
                self.res.append(3)
                self.write_string(node.literal)
        elif isinstance(node, ast.DefStmt):
            i = len(self.res)
            self.reserve_space(INT_LEN * 3)
            self.compile_node(node.params)
            param_end = len(self.res)
            self.compile_node(node.r_type)
            rt_end = len(self.res)
            self.compile_node(node.body)
            body_end = len(self.res)
            self.write_int(param_end, i)
            self.write_int(rt_end, i + INT_LEN)
            self.write_int(body_end, i + INT_LEN * 2)
        else:
            print("Type {} not implemented".format(node.node_type))

    def write_int(self, i: int, index=None):
        b = typ.int_to_bytes(i)
        if index is None:
            self.res.extend(b)
        else:
            self.res[index: index + len(b)] = b

    def write_string(self, s: str):
        b = s.encode("ascii")
        length = len(b)
        self.write_int(length)
        self.res.extend(b)

    def write_float(self, f: float):
        b = typ.float_to_bytes(f)
        self.res.extend(b)

    def reserve_space(self, length):
        self.res.extend(bytes(length))
