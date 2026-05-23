def fibonacci(n):
    """
    フィボナッチ数列の第n項を返す
    
    Args:
        n: 非負整数
        
    Returns:
        フィボナッチ数列の第n項
    """
    if n < 0:
        raise ValueError("nは非負整数である必要があります")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b
