import random

def main():
    secret_number = random.randint(1, 100)
    attempts = 0
    
    print("1から100の数字を当ててみよう！")
    print("ヒント: 大きい・小さいを教えていきます。")
    
    while True:
        try:
            guess = int(input(f"\n{attempts + 1}回目のguess: "))
            attempts += 1
            
            if guess < secret_number:
                print("もっと大きいです！")
            elif guess > secret_number:
                print("もっと小さいです！")
            else:
                print(f"正解です！{attempts}回で当てました！")
                break
        except ValueError:
            print("数を入力してください！")

if __name__ == "__main__":
    main()
