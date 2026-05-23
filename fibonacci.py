def fibonacci(n: int) -> list[int]:
    """
    フィボナッチ数列を返す関数
    
    Args:
        n: 生成する数列の項数
        
    Returns:
        フィボナッチ数列のリスト
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    
    return sequence


# テスト実行
if __name__ == "__main__":
    print("最初の10項のフィボナッチ数列:")
    print(fibonacci(10))
