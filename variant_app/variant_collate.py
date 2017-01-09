def collate(A, B, similarity):
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
