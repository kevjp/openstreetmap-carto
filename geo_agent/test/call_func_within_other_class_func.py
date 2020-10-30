

class Demo():

    def func1(self, a=2, b=3, **kwargs):
        c = a * b
        return c

    def func2(self):
        f = getattr(self, 'func1')
        a = f()
        b =2
        c = b+a
        return c


demo_inst = Demo()


check = demo_inst.func2()

print(demo_inst.__class__.__dict__)
k = "func1"
d = {'a':4}
checkfunc = getattr(Demo(), k)

print(checkfunc(b=10,**d))



# print(demo_inst.__class__.__dict__["func1"])
