import random

def roll_dice(num_dice=1, num_sides=6):
    """指定された数のサイコロを振る"""
    rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    return rolls

def dice_game():
    print("=== サイコロゲーム ===")
    print("プレイヤーとコンピュータがサイコロを振り、合計値の大きい方が勝ちです。\n")
    
    try:
        num_dice = int(input("振るサイコロの数を入力してください（1-5）: "))
        if num_dice < 1 or num_dice > 5:
            print("1から5の間の数を入力してください。")
            return
            
        num_sides = int(input("サイコロの面の数を入力してください（通常は6）: "))
        if num_sides < 2:
            print("2以上の数を入力してください。")
            return
    except ValueError:
        print("無効な入力です。整数を入力してください。")
        return
    
    # プレイヤーのターン
    print(f"\n--- プレイヤーのターン（サイコロ{num_dice}個） ---")
    player_rolls = roll_dice(num_dice, num_sides)
    print(f"出目: {player_rolls}")
    player_total = sum(player_rolls)
    print(f"合計値: {player_total}")
    
    # コンピュータのターン
    print(f"\n--- コンピュータのターン（サイコロ{num_dice}個） ---")
    computer_rolls = roll_dice(num_dice, num_sides)
    print(f"出目: {computer_rolls}")
    computer_total = sum(computer_rolls)
    print(f"合計値: {computer_total}")
    
    # 結果判定
    print("\n=== 結果 ===")
    if player_total > computer_total:
        print("プレイヤーの勝ちです！おめでとうございます！🎉")
    elif player_total < computer_total:
        print("コンピュータの勝ちです。また挑戦してください。")
    else:
        print("引き分けです！")

if __name__ == "__main__":
    dice_game()
