def calculator():
    print("=== シンプルな電卓 ===")
    print("操作を選択してください:")
    print("1. 加算 (+)")
    print("2. 減算 (-)")
    print("3. 乗算 (*)")
    print("4. 除算 (/)")
    print("5. 終了")
    
    while True:
        try:
            choice = input("\n操作番号を入力してください: ")
            
            if choice == '5':
                print("電卓を閉じます。")
                break
            
            if choice not in ('1', '2', '3', '4'):
                print("無効な選択です。1から4のいずれかを選択してください。")
                continue
            
            num1 = float(input("最初の数値を入力してください: "))
            num2 = float(input("2番目の数値を入力してください: "))
            
            if choice == '1':
                result = num1 + num2
                operation = "+"
            elif choice == '2':
                result = num1 - num2
                operation = "-"
            elif choice == '3':
                result = num1 * num2
                operation = "*"
            else:
                if num2 == 0:
                    print("ゼロによる除算はできません。")
                    continue
                result = num1 / num2
                operation = "/"
            
            print(f"結果: {num1} {operation} {num2} = {result}")
            
        except ValueError:
            print("無効な数値が入力されました。整数または小数を入力してください。")

if __name__ == "__main__":
    calculator()
