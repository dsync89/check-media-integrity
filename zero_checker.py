class ZeroChecker:
    @staticmethod
    def check(filename, length_seq_threshold=None):
        f = open(filename, "rb")
        thefilearray = f.read()
        f.close()
        num = 1
        maxnum = num
        prev = None
        maxprev = None
        for i in thefilearray:
            if prev == i:
                num += 1
            else:
                if num > maxnum:
                    maxnum = num
                    maxprev = prev
                num = 1
                prev = i
        if num > maxnum:
            maxnum = num
        if length_seq_threshold is None:
            return maxnum
        else:
            if maxnum >= length_seq_threshold:
                raise Exception("Equal value sequence, value:", maxprev, "len:", maxnum)
