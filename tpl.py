""" The main SPL runner. """

import sys
import script
import time
import os
from bin import spl_lexer, spl_parser as psr, spl_interpreter
import bin.tpl_pre_processor as tpp

sys.setrecursionlimit(10000)

EXE_NAME = "tpl.py"

INSTRUCTION = """Welcome to Slowest Programming Language.

Try "{} help" to see usage.""".format(EXE_NAME)

HELP = """Name
    {}  -  Slowest Programming Language command line interface.

Usage
    {} [OPTIONS]... [FLAGS]... FILE [ARGV]...
    
Description
OPTIONS:    
    -a,   --ast,     abstract syntax tree    shows the structure of the abstract syntax tree     
    -d,   --debug,   debugger                enables debugger
    -et,             execution               shows the execution times of each node
    -e,   --exit,    exit value              shows the program's exit value
    -l,   --link,    link                    write the linked script to file
    -t,   --timer,   timer                   enables the timer
    -tk,  --tokens,   tokens                 shows language tokens
    -v,   --vars,    variables               prints out all global variables after execution
    
FLAGS:
    -Dfile ENCODING    --file encoding       changes the tp file decoding
    
ARGV:
    command-line argument for the spl program
    
Example
    {} -ast -tokens example.tp -something
""".format(EXE_NAME, EXE_NAME, EXE_NAME)


def parse_arg(args):
    d = {"file": None, "dir": None, "debugger": False, "timer": False, "ast": False, "tokens": False,
         "vars": False, "argv": [], "encoding": None, "exit": False, "exec_time": False, "link": False,
         "import": True, "out": sys.stdout, "in": sys.stdin, "err": sys.stderr}
    i = 1
    while i < len(args):
        arg: str = args[i]
        if d["file"] is not None:
            d["argv"].append(arg)
        else:
            if arg[0] == "-":
                flag = arg[1:]
                if flag == "d" or flag == "-debug":
                    d["debugger"] = True
                elif flag == "t" or flag == "-timer":
                    d["timer"] = True
                elif flag == "a" or flag == "-ast":
                    d["ast"] = True
                elif flag == "tk" or flag == "-tokens":
                    d["tokens"] = True
                elif flag == "v" or flag == "-vars":
                    d["vars"] = True
                elif flag == "e" or flag == "-exit":
                    d["exit"] = True
                elif flag == "l" or flag == "-link":
                    d["link"] = True
                elif flag == "ni" or flag == "-noimport":
                    d["import"] = False
                elif flag == "Dfile":
                    i += 1
                    d["encoding"] = args[i]
                elif flag == "et":
                    d["exec_time"] = True
                else:
                    print("unknown flag: -" + flag)
            elif arg.lower() == "help":
                print_help()
                return None
            else:
                d["file"] = arg
                d["dir"] = spl_lexer.get_dir(arg)
                d["argv"].append(arg)
        i += 1
    if d["file"] is None:
        print_usage()
        return None
    else:
        return d


def print_usage():
    print(INSTRUCTION)


def print_help():
    print(HELP)


def interpret(mode: str):
    lex_start = time.time()

    if mode == "tp":
        lexer = spl_lexer.Tokenizer()
        lexer.setup(script.get_spl_path(), file_name, argv["dir"])
        lexer.tokenize(f)
    # elif mode == "lsp":
    #     lexer = spl_lexer.Tokenizer()
    #     lexer.restore_tokens(f)
    else:
        raise Exception

    if argv["tokens"]:
        print(lexer.get_tokens())

    parse_start = time.time()

    parser = psr.Parser(lexer.get_tokens())
    block = parser.parse()

    # pre = tpp.PreProcessor()
    # pre.process(block)

    if argv["ast"]:
        print("===== Abstract Syntax Tree =====")
        print(block)
        print("===== End of AST =====")
    if argv["debugger"]:
        spl_interpreter.DEBUG = True

    interpret_start = time.time()

    # ioe = (argv["in"], argv["out"], argv["err"])

    itr = spl_interpreter.Interpreter()
    itr.set_ast(block, parser.literal_bytes)
    result = itr.interpret()

    end = time.time()

    sys.stdout.flush()
    sys.stderr.flush()

    if argv["exit"]:
        print("Process finished with exit value " + str(result))

    # if argv["vars"]:
    #     print(itr.env)

    if argv["timer"]:
        print("Time used: tokenize: {}s, parse: {}s, execute: {}s.".format
              (parse_start - lex_start, interpret_start - parse_start, end - interpret_start))

    if argv["exec_time"]:
        print(block)


class ArgumentsException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


if __name__ == "__main__":
    argv = parse_arg(sys.argv)
    if argv:
        file_name = argv["file"]

        if not os.path.exists(file_name):
            print("File '{}' not found!".format(file_name))
            exit(1)

        encoding = argv["encoding"]
        if file_name[-3:] == ".tp":
            if encoding is not None:
                assert isinstance(encoding, str)
                f = open(file_name, "r", encoding=encoding)
            else:
                f = open(file_name, "r")

            try:
                interpret("tp")
            except Exception as e:
                raise e
            finally:
                f.close()
        elif file_name[-4:] == ".lsp":
            f = open(file_name, "rb")

            try:
                interpret("lsp")
            except Exception as e:
                raise e
            finally:
                f.close()
        else:
            raise ArgumentsException("Input file can either be SPL script '.tp' or linked SPL script '.lsp'.")
