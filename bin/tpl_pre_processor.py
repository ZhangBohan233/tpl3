import bin.spl_ast as ast


class TestEnvironment:
    def __init__(self, outer):
        self.outer = outer

        self.variables = {}


class PreProcessor:
    def __init__(self):
        pass

    def process(self, root):
        env = TestEnvironment(None)
        self.process_node(root, env)

    def process_node(self, node, env: TestEnvironment):
        if isinstance(node, ast.NameNode):
            return node
        elif isinstance(node, ast.AssignmentNode):
            return node
        elif isinstance(node, ast.Node):
            for attr in dir(node):
                if len(attr) < 5 or attr[:2] != "__" or attr[-2:] != "__":
                    value = getattr(node, attr)
                    new_value = self.process_node(value, env)
                    setattr(node, attr, new_value)
        else:
            return node
