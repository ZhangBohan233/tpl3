import sys
import bin.spl_ast as ast
import bin.tpl_compiler as cmp
import bin.spl_parser as psr
import bin.spl_lexer as lex
import script


if __name__ == '__main__':
    argv = sys.argv
    src_file = argv[1]
    target_file = argv[2]

    with open(src_file, "r") as rf:
        lexer = lex.Tokenizer()
        lexer.setup(script.get_spl_path(), src_file, lex.get_dir(argv[0]))
        lexer.tokenize(rf)

        tokens = lexer.get_tokens()

        parser = psr.Parser(tokens)
        root = parser.parse()

        print(root)
        print("========== End of AST ==========")

        compiler = cmp.Compiler(parser.literal_bytes)
        byt = compiler.compile_all(root)

        with open(target_file, "wb") as wf:
            wf.write(byt)