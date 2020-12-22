class Parent(object):

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class Child(object):
    def __init__(self, parent_instance):
        self.obj = parent_instance

    def __getattr__(self, attr):
        return getattr(self.obj, attr)

    def check_func(self):
        print(self.x,self.z, self.y)


b = Parent("hello", "goodbye", "ok")
a = Child(b)

print(a.x)
a.check_func()