class Clause:

    raw = []
    value = None
    def __init__(self, inp):
        if type(inp) is list or type(inp) is frozenset:
            self.raw = list(inp)
            self.sort()

        elif type(inp) is bool:
            self.value = inp
        
    def __lt__(self, other):
        selflen = len(self.raw)
        otherlen = len(other.raw)

        # in case one of them is shorter, return the shorter
        if selflen != otherlen:
            return selflen < otherlen
               
        # case where both are of equal length
        for i in range(0, selflen):

            if self.raw[i] == other.raw[i]:
                continue

            # only if two number with different signs, ex. -5 and 5, are compared, consider -5 is less
            if self.raw[i] != other.raw[i] and abs(self.raw[i]) == abs(other.raw[i]):
                return self.raw[i] < other.raw[i]
            
            # do absolute value comparison, so that -5 is greater than 3, for example.
            return abs(self.raw[i]) <= abs(other.raw[i])

        # in case both are identical lengths and values
        return 0 < 1
    

    def sort(self):
        x = sorted(self.raw, key = abs)
        self.raw = x
