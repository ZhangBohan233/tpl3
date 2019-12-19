import sys
import bin.tpl_vm2 as vm


if __name__ == '__main__':
    c_path = sys.argv[1]

    with open(c_path, "rb") as rf:
        b = rf.read()

        machine = vm.VirtualMachine()
        machine.load_code(b)
        machine.run()
