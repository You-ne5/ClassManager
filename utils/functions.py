def pgcd(a, b):

    while True:
        if a%b == 0:
            return abs(b)
        else:
            rest = a%b
            a=b
            b=rest


def ppcm(a, b):
    (a, b) = (a, b) if a>b else (b, a)
    k=1
    while True:
        if (a*k)%b == 0:
            return a*k
        k+=1


def eq_2(a, b, c):
    d = pgcd(a, b)
    if c%d != 0:

        return None
    
    a//=d
    b//=d
    c//=d

    def special_solution(a, b, c):
        for m in range(1000):
            for i in [-1, 1]:

                x = i*m
                for z in range(1000):
                    for j in [-1, 1]:
                        if z == 0 and j == 1:
                            continue
                        

                        y = j*z
                        if a*x + b*y == c:
                            return (x, y)

    s_c = special_solution(a, b, c)
    if not s_c:
        return "not found brother"
    
    x0, y0 = s_c
    
    def sign(n: int):
        return "+" if n > 0 else "-"
    
    x = f"{b}k{f' {sign(x0)} {abs(x0)}' if x0 else ''}"
    y = f"{-a}k{f' {sign(y0)} {abs(y0)}' if y0 else ''}"

    return (x, y)
