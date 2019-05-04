# config
SAT = 2

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


if __name__ == "__main__":
        
    with open("in.txt", "r") as f:
        seq = f.read()
        print("sequence = " + str(seq))


        seq = list(seq)
        sStatement = "S = {"
        clauses = []
        for x in chunker(seq, SAT):
            x = ["x" + n for n in x]
            clauses.append("(" + ",".join(x) + ")")
            
        s_statement = "S = {" + ",".join(clauses) + "}"
        print(s_statement)


        #display patter for each variable
        iseq = [int(n) for n in seq]
        max_var = max(iseq)
        for i in range(0, max_var+1):
            #i = max_var-i
            print("x{0} = {1}(0){1}(1)".format(i, 2**i))
        

