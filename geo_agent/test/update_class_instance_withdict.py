# class AttrDict(dict):
#     def __init__(self):
#         object.__setattr__(self, '_AttrDict__dict__', event_instance_history)
#         self.e = 21

#     def __getattr__(self, name):
#         if name in self:
#             return self[name]

#     def __setattr__(self, name, value):
#         self[name] = self.from_nested_dict(value)

#     def __delattr__(self, name):
#         if name in self:
#             del self[name]

#     @staticmethod
#     def from_nested_dict(data):
#         """ Construct nested AttrDicts from nested dictionaries. """
#         if not isinstance(data, dict):
#             return data
#         else:
#             return AttrDict({key: AttrDict.from_nested_dict(data[key])
#                                 for key in data})



# ad = AttrDict()

# print(ad.e)

# data = {'a': 'aval', 'b': {'b1':{'b2a':{'b3a':'b3aval','b3b':'b3bval'},'b2b':'b2bval'}} }

# ad.data = data

# print(ad.data.b.b1.b2a.b3b)

# import json

# class E():
#     def __init__(self, dict_ = {}):

#         self.__dict__.update(dict_)
#         self.e = 2

# def dict2obj(d, agent_instance):
#     return json.loads(json.dumps(d), object_hook=agent_instance)


# d = {'a': 1, 'b': {'c': 21}, 'd': ['hi', {'foo': 'bar'}]}

# e_instance = E()
# print(e_instance.__dict__)

# o = dict2obj(d,e_instance)




# print(o.b.c)

import copy
# class D():


#     def __init__(self, hello = {}):
#         object.__setattr__(self, '_E__dic', hello)
#         self.d = 45
# check = D()

# check2 = D()

# print(check.d, check2.d)

# check.d = 50

# print(check.d, check2.d)

#I have a Class E which i have copied from the answer posted by @user1783597 here
# https://stackoverflow.com/a/15589291/1977981 which allows you to access values
# from a nested dictionary as object attributes as demonstrated in the code below.
# The code differs from the original post in that my example the argument given
# to the class is optional. The class is passed a dictionary when instantiated.
# However if no dictionary is passed to the class then a default empty dictionary
# is passed via the init function. However passing no argument to the class has
# resulted in some unexpected behaviour (at least unexpected for me) in that all
# class instances called this way end up sharing the same class variables
# i.e. changing instance variables in one instance ends up changing the same
# variable in all other instances where the class is called without any inputted
# arguments. As shown in the code below when I look at the memory location for all
# instance they occupy different locations. However the _E__dict object found in
# all these instances relates to a single dictionary object as shown by its memory
# location (see code). Is anyone able to explain what is happening here. There is
# obviously a hole in my understanding of what is happening here under the hood.

#ANSWER: https://stackoverflow.com/questions/60543907/why-optional-arguments-act-like-class-variable
#  Default arguments is not re-created per instance and so object.__setattr__(self, '_E__dic', event_instance_history)
# is just being called the first time the class is instantiated and after this is it is the same _E__dict that is being called each time

class E(object):
    def __init__(self, event_instance_history = {}):

        print("__INIT__ CALLED")
        # super().__setattr__('_E__dic', event_instance_history)
        # super(E, self).__setattr__('_E__dic', event_instance_history)
        object.__setattr__(self, '_E__dic', event_instance_history)
        self.e = 5
        self.b = 10
        self.f = 50

    def __setattr__(self, name, value):
        print("inside __setattr__")
        self[name] = value

    def __setitem__(self, name, value):
        print("inside __setitem__")
        self.__dic[name] = value

    def __delitem__(self, name):
        print("inside __delitem__")
        del self.__dic[name]

    def __getitem__(self, name):
        print("inside __getitem__")
        value = self.__dic[name]
        if isinstance(value, dict):  # recursively view sub-dicts as objects
            value = E(event_instance_history =  value)
        return value

    def __getattr__(self, name):
        print("inside __getattr__")
        if name == "__setstate__":
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __delattr__(self, name):
        print("inside __delattr__")
        del self[name]

d = {'a': 'b', 1: 2, 'j' : {'l' : 1000}}
x = {'a': 'c', 1: 4}
e_instance = E(event_instance_history = d)
print("check",e_instance.a)
print(type(e_instance))
print(e_instance.__dict__)
print(e_instance.__class__)
e_instance.e = 42
print("_____________________")
e_instance_1 = E(event_instance_history = {})

print(type(e_instance_1))
print(e_instance_1.__dict__)
print(e_instance_1.__class__)
e_instance_1.e = 41
e_instance_1.g = 57

print(e_instance_1.__dict__)

print("________________________")

print(id(e_instance._E__dic), id(e_instance_1._E__dic))
print(e_instance.e, e_instance_1.e)

# e_instance_2 = E()
# print(e_instance.__dict__)
# print(e_instance_1.__dict__)
# print(e_instance_2.__dict__)


# print(id(e_instance.e), id(e_instance_1.e), id(e_instance_2.e))


















# d = {'a': 'b', 1: 2}
# e_instance = E(event_instance_history = d)

# e_instance.e =200
# e_instance.f = 300
# print(4)



# print("e_instance", e_instance.e)
# z = E()
# y = E(event_instance_history = {})
# y.e = 200

# print("e_instance", e_instance.e)
# print("z", z.e)
# print("y", y.e)
# print(e_instance.__dict__)
# print(z.__dict__)



# data = {'a': 'aval', 'b': {'b1':{'b2a':{'b3a':'b3aval','b3b':'b3bval'},'b2b':'b2bval'}} }

# e_instance.disease_progression = data
# print(e_instance.disease_progression.a)
# print(e_instance.disease_progression.b.b1.b2a.b3a)
# print(e_instance.check_dict)
# e_instance.check_dict["hello"] = "goodbye"
# print(e_instance.check_dict.hello)
# print(vars(e_instance.disease_progression))
# print(e_instance.disease_progression._E__dict)



# e_copy = copy.deepcopy(e_instance)
