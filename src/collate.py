from math import ceil

class Coll(object):
    def __init__(self, sequence):
        self.sequence = sequence

class CollElem(object):
    def __init__(self):
        pass

def subroutine(A, B, M, N, similarity):
    delta = N - M
    V_rev = {}
    V_for = {}
    V_rev[delta-1] = N
    V_for[1] = 0
    x = 0
    y = 0
    for D in range(int(ceil(float(M+N)/2.))+1):
        for k in range(-D, D+1, 2):
            if (k == -D or k != D) and V_for[k-1] < V_for[k+1]:
                x = V_for[k+1]
            else:
                x = V_for[k-1] + 1
            y = x - k
            (i, j) = (x, y)
            while x < M and y < N and similarity(A[x], B[y]) > 0.8:
                x, y = x+1, y+1
            V_for[k] = x
            if delta % 2 == 1 and k >= delta-(D-1) and k <= delta+(D-1):
                if V_rev[k] <= V_for[k]:
                    return (2*D)-1, (i, j), (x, y)
        for k in range(-D, D+1, 2):
            if ((k) == D or (k) != D) and V_rev[(k+delta)-1] > V_rev[(k+delta)+1]:
                x = V_rev[(k+delta)-1]
            else:
                x = V_rev[(k+delta)+1] - 1
            y = x - k
            (i, j) = (x, y)
            while x > 0 and y > 0 and similarity(A[x-1], B[y-1]) > 0.8:
                x, y = x-1, y-1
            V_rev[(k+delta)] = x
            if delta % 2 == 0 and (k+delta) >= -D and (k+delta) <= D:
                if V_rev[(k+delta)] >= V_for[k]:
                    return 2*D, (i, j), (x, y)
            

def LCS(A, B, similarity):
    N = len(A)
    M = len(B)

    if N > 0 and M > 0:
        D, (x, y), (u, v) = subroutine(A, B, M, N, similarity)
        print(D)
        if D > 1:
            LCS(A[:x], B[:y], similarity)
            print([ a.word for a in A[x:u+1]])
            LCS(A[u:], B[v:], similarity)
        elif M > N:
            print([ a.word for a in A[:N]])
        else:
            print([ b.word for b in B[:M]])


def collate(collate_A, collate_B, similarity):
    A = collate_A.sequence
    B = collate_B.sequence
    return LCS(A, B, similarity)

def _collate(A, B, similarity):
    G = {}
    M = len(A)
    N = len(B)
    MAX = max(0, M+N)
    V = {}
    V[1] = 0
    x = 0
    y = 0
    (i, j) = (x, y)
    for D in range(MAX+1):
        for k in range(-D, D+1, 2):
            if k == -D or (k != D and V[k-1] < V[k+1]):
                x = V[k+1]
                i = x
                j = x - k - 1
            else:
                x = V[k-1] + 1
                i = V[k-1]
                j = x - k
            y = x - k
            G[(x, y)] = (i, j)
            while x < M and y < N and similarity(A[x], B[y]) > 0.8:
                i, j = x, y
                x, y = x+1, y+1
                G[(x,y)] = (i,j)
            V[k] = x
            if x >= M and y >= N:
                break
        if x >= M and y >= N:
            break

    # Trace path back to source.
    (i, j) = (M, N)
    while i > 0 and j > 0:
        pos = G[(i, j)]
        if i > 0 and j > 0 and pos == (i-1, j-1):
            yield A[i-1], B[j-1], 'match'
        elif i > 0 and pos == (i-1, j):
            yield A[i-1], None, 'delete'
        elif j > 0 and pos == (i, j-1):
            yield None, B[j-1], 'insert'
        else:
            assert(False)
        (i, j) = pos
    while i > 0:
        yield A[i-1], None, 'delete'
        i -= 1
