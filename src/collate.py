import time
import numpy as np

class Coll(object):
    def __init__(self, sequence):
        self.sequence = sequence

class CollElem(object):
    def __init__(self):
        pass

def collate(collate_A, collate_B, similarity):
    A = collate_A.sequence
    B = collate_B.sequence
    F = np.empty((len(A)+1, len(B)+1)) # Scores.
    G = np.empty((len(A)+1, len(B)+1), dtype='2int32') # Directions.
    gap_penalty = -1
    start = time.time()
    for i in range(len(A)+1):
        F[i, 0] = gap_penalty * i
    for j in range(len(B)+1):
        F[0, j] = gap_penalty * j
    for i in range(1, len(A)+1):
        for j in range(1, len(B)+1):
            match = F[i-1, j-1] + similarity(A[i-1], B[j-1])
            delete = F[i-1, j] + gap_penalty
            insert = F[i, j-1] + gap_penalty
            max_score = max((match, delete, insert))
            F[i, j] = max_score
            if max_score == match:
                G[i, j] = (i-1, j-1)
            elif max_score == delete:
                G[i, j] = (i-1, j)
            elif max_score == insert:
                G[i, j] = (i, j-1)
            else:
                assert(False)
    end = time.time()
    print('Matrix construction: ' + str(end-start))

    start = time.time()
    (i, j) = (len(A), len(B))
    while i > 0 and j > 0:
        pos = G[i, j]
        pos = (pos[0], pos[1])
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
    end = time.time()
    print('Matrix traversal: ' + str(end-start))
