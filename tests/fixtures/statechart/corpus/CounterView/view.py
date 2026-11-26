def state(v):
    x = v["x"]
    return "odd" if x > 0 and x % 2 == 1 else str(x)
