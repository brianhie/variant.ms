"""
This implements a version of the algorithm described by:
Myers, Eugene M. "An O(ND) Difference Algorithm and Its Variations".
Algorithmica (1986). http://www.xmailserver.org/diff2.pdf

This algorithm compares two sequences A and B, where A is length N and B
is length M, and runs in O((N+M)D) time (with O((N+M)+D^2) expected time)
and O(N+M) space. A variant of the algorithm is used the implement *nix
diff.

The algorithm is implemented as a Python generator named collate(). A
similarity function must be passed in which defines equality between the
type contained in A and B.

"""

from math import ceil
import sys

def collate(A, B, similarity, debug=False):
    result = []
    _LCS(A, B, similarity, result, 0, debug=debug)
    for r in result:
        yield r


def _LCS(A, B, similarity, result, depth, debug=False):
    if debug:
        # Tree of splitted arrays which is useful for debugging.
        sys.stdout.write('\t'*depth)
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>0')
        sys.stdout.write('\t'*depth)
        print(A)
        sys.stdout.write('\t'*depth)
        print(B)

    N = len(A)
    M = len(B)

    if N == 0 and M > 0:
        for b in B:
            result.append((None, b, 'insert'))
    elif M == 0 and N > 0:
        for a in A:
            result.append((a, None, 'delete'))
    elif N > 0 and M > 0:
        D, (x, y), (u, v) = _middle_snake(A, B, similarity)
        if D > 1:
            _LCS(A[:x], B[:y], similarity, result, depth + 1, debug=debug)

            local_results = []
            for a, b, status in _collate_ND(A[x:u], B[y:v], similarity):
                local_results.append((a, b, status))
            local_results.reverse()
            result += local_results

            _LCS(A[u:], B[v:], similarity, result, depth + 1, debug=debug)

        elif M > N:
            local_results = []
            for a, b, status in _collate_ND(A, B, similarity):
                local_results.append((a, b, status))
            local_results.reverse()
            result += local_results
        else:
            local_results = []
            for a, b, status in _collate_ND(A, B, similarity):
                local_results.append((a, b, status))
            local_results.reverse()
            result += local_results


def _middle_snake(A, B, similarity):
    N = len(A)
    M = len(B)
    delta = N - M
    delta_even = delta % 2 == 0
    V_rev = {}
    V_for = {}
    V_for[1] = 0
    V_rev[delta-1] = N
    x = 0
    y = 0
    for D in range(int(ceil(float(M+N)/2.))+1):
        for k in range(-D, D+1, 2):
            if k == -D or (k != D and V_for[k-1] < V_for[k+1]):
                x = V_for[k+1]
                i = x
                j = x - k - 1
            else:
                x = V_for[k-1] + 1
                i = V_for[k-1]
                j = x - k
            y = x - k
            (i, j) = (x, y)
            while x < N and y < M and similarity(A[x], B[y]):
                x, y = x+1, y+1
            V_for[k] = x
            if not delta_even and k >= delta-(D-1) and k <= delta+(D-1):
                for_x = V_for[k]
                for_y = for_x - k
                rev_x = V_rev[k]
                rev_y = rev_x - (k)
                if for_x - for_y == rev_x - rev_y and for_x >= rev_x:
                    return D, (i, j), (x, y)
        for k in range(-D, D+1, 2):
            if (k) == D or ((k) != -D and V_rev[(k+delta)-1] < V_rev[(k+delta)+1]):
                x = V_rev[(k+delta)-1]
                i = x
                j = x - (k+delta) + 1
            else:
                x = V_rev[(k+delta)+1] - 1
                i = V_rev[(k+delta)+1]
                j = x - (k+delta)
            y = x - (k+delta)
            (i, j) = (x, y)
            while x > 0 and y > 0 and similarity(A[x-1], B[y-1]):
                x, y = x-1, y-1
            V_rev[(k+delta)] = x
            if delta_even and (k+delta) >= -D and (k+delta) <= D:
                for_x = V_for[(k+delta)]
                for_y = for_x - (k+delta)
                rev_x = V_rev[(k+delta)]
                rev_y = rev_x - (k+delta)
                if for_x - for_y == rev_x - rev_y and for_x >= rev_x:
                    return D, (i, j), (x, y)
    # Should never reach here.
    assert(False)


def _collate_ND(A, B, similarity):
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
            while x < M and y < N and similarity(A[x], B[y]):
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
    while j > 0:
        yield None, B[j-1], 'insert'
        j -= 1
    while i > 0:
        yield A[i-1], None, 'delete'
        i -= 1


def _test(text1, text2, name, similarity):
    print(name)
    print(text1)
    print(text2)
    for word1, word2, status in collate(text1, text2, similarity, debug=True):
        print((word1, word2, status))


if __name__ == '__main__':
    similarity = lambda x, y: x == y

    text1 = 'X A B D'.split()
    text2 = 'A C B'.split()
    _test(text1, text2, 'Test 1', similarity)

    text1 = 'X A B C'.split()
    text2 = 'A B C'.split()
    _test(text1, text2, 'Test 2', similarity)

    text1 = 'A B C'.split()
    text2 = 'A B C X'.split()
    _test(text1, text2, 'Test 2', similarity)

    text1 = 'X X A B E C X X A B E C X X A B E C X X'.split()
    text2 = 'X X G Q R B E C X X G Q R B E C X X G Q R B E C X X'.split()
    _test(text1, text2, 'Test 4', similarity)
