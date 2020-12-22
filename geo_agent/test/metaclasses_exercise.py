class Bar():

    def __init__(self, event_instance_history = {}):
        object.__setattr__(self, '_Bar__dic', event_instance_history)


class Foo():
    def __init__(self, event_instance_history = {}):

        object.__setattr__(self, '_Foo__dic', event_instance_history)
        self.a = 5
        self.b = 10

    def __setattr__(self, name, value):
        self[name] = value

    def __setitem__(self, name, value):
        self.__dic[name] = value

    def __delitem__(self, name):
        del self.__dic[name]

    def __getitem__(self, name):
        value = self.__dic[name]
        if isinstance(value, dict):  # recursively view sub-dicts as objects
            value = Foo(event_instance_history =  value)
        return value

    def __getattr__(self, name):
        if name == "__setstate__":
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __delattr__(self, name):
        del self[name]





a = Foo(event_instance_history = {})
a.a = 2
a.b = 3
a.c =4
print(a.a, a.b, a.c)
a.d = {}
a.d["b"] = 4



print("assignment",a.b)
print(a.__dict__)

b= Foo(event_instance_history = {})
c = Foo(event_instance_history = {})

b.b = 2
b.f = 10
print(a.b, b.b, b.f)
print(a.__dict__)
print(b.__dict__)
print(a.b, b.b, c.b)

# class Fit(Foo):
#     def __init__(self, a, b, event_instance_history = {}):

#         super().__init__()
#         object.__setattr__(self, 'a', a)
#         object.__setattr__(self, 'b', b)

#         result = self.process(a)
#         for key, value in result.items():
#             object.__setattr__(self, key, value)

#     def __setattr__(self, name, value):
#         print(self.b) # Call to a function using self.b
#         # object.__setattr__(self, name, value)
#         self[name] = value

#     def __setitem__(self, name, value):
#         self.__dic[name] = value

#     def __delitem__(self, name):
#         del self.__dic[name]

#     def __getitem__(self, name):
#         value = self.__dic[name]
#         if isinstance(value, dict):  # recursively view sub-dicts as objects
#             value = Foo(event_instance_history =  value)
#         return value

#     def __getattr__(self, name):
#         if name == "__setstate__":
#             raise AttributeError(name)
#         try:
#             return self[name]
#         except KeyError:
#             raise AttributeError(name)

#     def __delattr__(self, name):
#         del self[name]


