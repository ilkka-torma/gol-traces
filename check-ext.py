def golker(v00, v01, v02, v10, v11, v12, v20, v21, v22):
    if 6 in [v00, v01, v02, v10, v11, v12, v20, v21, v22]:
        return True
    sm = v00 + v01 + v02 + v10 + v12 + v20 + v21 + v22
    if v11 == 1:
        return sm != 2 and sm != 3
    if v11 == 0:
        return sm != 3

def all_patterns(n):
    if n == 0:
        yield ()
        return
    else:
        for i in all_patterns(n-1):
            yield (0,) + i
            yield (1,) + i

def legal(a, b, c):
    for i in range(1, len(a)-1):
        if not golker(a[i-1], b[i-1], c[i-1],
                      a[i], b[i], c[i],
                      a[i+1], b[i+1], c[i+1]):
            return False
    return True

def check(n):
    for a in all_patterns(n):
        for b in all_patterns(n):
            for c in [(1,1,1,1,1,1),
                      (0,0,0,0,0,0),
                      (1,1,1,1,1,0), (0,1,1,1,1,1),
                      (1,1,1,1,0,0), (0,0,1,1,1,1),
                      (0,0,1,0,0,0), (0,0,0,1,0,0),
                      (1,1,1,0,0,0), (0,0,0,1,1,1),
                      (1,1,0,0,0,0), (0,0,0,0,1,1),
                      (1,1,0,1,0,0), (0,0,1,0,1,1)
                      ]:
                if legal(a, b, c):
                    break
            else:
                return "%s, %s has no extension from list" % (a, b)
    return "success"

print(check(6))
