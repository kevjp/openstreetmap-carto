class A():

    def __init__(self):

        self.a = 1


    def check_func(self, E_instance):

        return self.a + E_instance.b

    def add_instance(self, E_instance):
        E_instance.A_instance = self
        self.e_instance = E_instance

class E():

    def __init__(self, A_instance = None):
        self.e = 2
        s

    def change_a (self):
        a



test = A()
e_instance = E()
test.add_instance(e_instance)
print(e_instance.A_instance.a)





