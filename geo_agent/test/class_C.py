from class_A import a, b
import time

class C():
    print(a.shape)
    def __init__(self):

        super().__init__()
        t1 = time.time()
        print(a.shape)
        # print(A.config('route_list'))
        t2 = time.time()
        total = t2 - t1
        print("class C", total)
