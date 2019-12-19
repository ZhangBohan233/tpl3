import bin.spl_ast as ast
import bin.spl_types as typ

INT_LEN = 8


class CompileException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class Compiler:
    def __init__(self, tree, lit_bytes):
        self.root: ast.Node = tree
        self.res = bytearray()
        self.write_int(len(lit_bytes))
        self.res.extend(lit_bytes)

        # self.name_dict: dict[str: int] = {}

    def compile(self):
        self.compile_node(self.root)

    def get_bytes(self) -> bytes:
        return bytes(self.res)

    def compile_node(self, node: ast.Node):
        if node.node_type == 0:
            print("wrong")
        self.write_one(node.node_type)
        if isinstance(node, ast.BlockStmt):  # not using node.node_type because of convenience
            i = len(self.res)
            self.reserve_space(INT_LEN)
            for line in node.lines:
                self.compile_node(line)
            children_end = len(self.res)
            self.write_int(children_end, i)
        elif isinstance(node, ast.NameNode):
            self.write_string(node.name)
            # name = node.name
            # if name in self.name_dict:
            #     rep = self.name_dict[name]
            # else:
            #     rep = len(self.name_dict)
            #     self.name_dict[name] = rep
            # self.write_int(rep)
        elif isinstance(node, ast.BinaryExpr):
            if isinstance(node, ast.AssignmentNode):
                self.res.append(node.level)
                if node.level == ast.ASSIGN:
                    if isinstance(node.left, ast.NameNode):
                        self.res.append(0)  # assign name
                        self.write_string(node.left.name)
                    else:
                        raise CompileException()
                elif node.level == ast.VAR:
                    if isinstance(node.left, ast.TypeNode) and isinstance(node.left.left, ast.NameNode):
                        # self.res.append(1)  # var declaration
                        name = node.left.left.name
                        type_ = node.left.right
                        self.write_string(name)
                        self.reserve_space(INT_LEN)
                        i = len(self.res)
                        self.compile_node(type_)
                        end = len(self.res)
                        self.write_int(end, i)
                    else:
                        raise CompileException()
                else:
                    raise CompileException()
                self.reserve_space(INT_LEN)
                i = len(self.res)
                self.compile_node(node.right)
                end = len(self.res)
                self.write_int(end, i)
            else:
                self.write_string(node.operation)
                i = len(self.res)
                self.reserve_space(INT_LEN * 2)
                self.compile_node(node.left)
                left_end = len(self.res)
                self.compile_node(node.right)
                right_end = len(self.res)
                self.write_int(left_end, i)
                self.write_int(right_end, i + INT_LEN)
        elif isinstance(node, ast.FuncCall):
            self.compile_node(node.args)
            self.compile_node(node.call_obj)
        elif isinstance(node, ast.ReturnStmt):
            i = len(self.res)
            self.reserve_space(INT_LEN)
            self.compile_node(node.value)
            child_end = len(self.res)
            self.write_int(child_end, i)
        elif isinstance(node, ast.UnaryExpr):
            self.write_string(node.operation)
            i = len(self.res)
            self.reserve_space(INT_LEN)
            self.compile_node(node.value)
            child_end = len(self.res)
            self.write_int(child_end, i)
        elif isinstance(node, ast.Literal):
            self.write_one(node.lit_type)
            self.write_int(node.lit_pos)
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

    def write_one(self, i: int):
        self.res.append(i)

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
