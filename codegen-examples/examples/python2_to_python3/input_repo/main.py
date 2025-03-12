# Python 2 code showcasing changes in Python 3

# Print statement vs. Print function
print "This is Python 2's print statement."
# In Python 3, it becomes a function: print("This is Python 3's print function.")

# Integer division
print "Integer division in Python 2: 5/2 =", 5/2
# In Python 3, you need // for integer division: print("Integer division in Python 3: 5//2 =", 5//2)

# Unicode strings
unicode_string = u"This is a Unicode string in Python 2."
print "Unicode string in Python 2: ", unicode_string
# In Python 3, all strings are Unicode by default.

# xrange vs range
for i in xrange(3):  # xrange exists in Python 2
    print "Using xrange in Python 2: ", i
# In Python 3, xrange is removed, and range behaves like xrange: for i in range(3):

# Error handling
try:
    raise ValueError("This is an error.")
except ValueError, e:  # Comma syntax in Python 2
    print "Caught an exception in Python 2: ", e
# In Python 3, use 'as': except ValueError as e:

# Iteration over dictionaries
my_dict = {"a": 1, "b": 2}
print "Dictionary keys in Python 2: ", my_dict.keys()  # Returns a list in Python 2
# In Python 3, it returns a view: print("Dictionary keys in Python 3: ", list(my_dict.keys()))

# Input function
user_input = raw_input("Enter something (Python 2 raw_input): ")
print "You entered: ", user_input
# In Python 3, use input(): user_input = input("Enter something (Python 3 input): ")

# Itertools changes
import itertools
print "itertools.izip in Python 2: ", list(itertools.izip([1, 2], [3, 4]))
# In Python 3, use zip directly: print("zip in Python 3: ", list(zip([1, 2], [3, 4])))

# Advanced Examples

# Metaclasses
class Meta(type):
    def __new__(cls, name, bases, dct):
        print("Creating class", name)
        return super(Meta, cls).__new__(cls, name, bases, dct)

class MyClass(object):
    __metaclass__ = Meta  # Python 2 syntax for metaclasses

# In Python 3: class MyClass(metaclass=Meta):

# Iterators and Generators
class MyIterator(object):
    def __init__(self, limit):
        self.limit = limit
        self.counter = 0

    def __iter__(self):
        return self

    def next(self):  # Python 2 iterator method
        if self.counter < self.limit:
            self.counter += 1
            return self.counter
        else:
            raise StopIteration

my_iter = MyIterator(3)
for value in my_iter:
    print "Iterating in Python 2: ", value
# In Python 3, next() is replaced by __next__().

# Sorting with custom keys
data = [(1, "one"), (3, "three"), (2, "two")]
print "Sorted data in Python 2: ", sorted(data, cmp=lambda x, y: cmp(x[0], y[0]))
# In Python 3, cmp is removed. Use key: sorted(data, key=lambda x: x[0])

# File Handling
with open("example.txt", "w") as f:
    f.write("Python 2 file handling.")
# In Python 3, open() defaults to text mode with UTF-8 encoding: with open("example.txt", "w", encoding="utf-8") as f:

# Bytes and Strings
byte_string = "This is a byte string in Python 2."
print "Byte string in Python 2: ", byte_string
# In Python 3, bytes and strings are distinct types: byte_string = b"This is a byte string in Python 3."

# Final note
print "This script demonstrates key differences between Python 2 and Python 3."
