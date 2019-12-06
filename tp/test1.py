class A:
    def __init__(self):
        self.v = 1

    def get_mul(self, m):
        for i in range(m):
            self.v *= i
        return self.v


class B:
    def __init__(self):
        self.v = 1


def get_mul(b, m):
    for i in range(m):
        b.v *= i
    return b.v


if __name__ == '__main__':
    import time

    n = 5000

    t1 = time.time()

    for j in range(n):
        x = A()
        x.get_mul(n)

    t2 = time.time()

    for j in range(n):
        x = B()
        get_mul(x, n)

    t3 = time.time()

    print(t2 - t1, t3 - t2)
