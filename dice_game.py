"""
ダイスゲーム - 乱数を使ったサイコロゲーム
プレイヤーとコンピュータがサイコロを振り、大きい方の勝ち。
累計スコアで何戦勝ったかを競う。
"""

import random


def roll_dice(num_dice: int = 1, sides: int = 6) -> list[int]:
    """n面ダイスを指定数だけ振り、結果のリストを返す"""
    return [random.randint(1, sides) for _ in range(num_dice)]


def sum_dice(dice_values: list[int]) -> int:
    """サイコロの結果の合計を計算する"""
    return sum(dice_values)


def display_round(player_dice: list[int], comp_dice: list[int], sides: int = 6) -> None:
    """1ラウンドの結果を表示する"""
    print("\n" + "=" * 40)
    player_total = sum_dice(player_dice)
    comp_total = sum_dice(comp_dice)

    print(f"プレイヤーのサイコロ: {player_dice}  (合計: {player_total})")
    print(f"コンピュータのサイコロ: {comp_dice}  (合計: {comp_total})")

    if player_total > comp_total:
        print(">> プレイヤーの勝ち！ <<")
    elif player_total < comp_total:
        print(">> コンピュータの勝ち！ <<")
    else:
        print(">> 引き分け！ <<")
    print("=" * 40)


def ask_input(prompt: str, valid_options: list[str]) -> str:
    """ユーザー入力を受け取り、有効なオプションのみを返す"""
    while True:
        response = input(prompt).strip().lower()
        if response in valid_options:
            return response
        print(f"無効な入力です。以下のいずれかを入力してください: {', '.join(valid_options)}")


def play_single_round(player_name: str) -> int:
    """1ラウンドをプレイし、勝敗結果(1=勝ち, 0=引き分け, -1=負け)を返す"""
    print(f"\n{player_name}さん、サイコロを振ります！")

    # プレイヤーのターン
    try:
        num_dice = int(input("振るサイコロの数を入力してください (1-5): "))
        while num_dice < 1 or num_dice > 5:
            print("1から5の間で入力してください。")
            num_dice = int(input("振るサイコロの数を入力してください (1-5): "))
    except ValueError:
        print("無効な入力です。1を指定します。")
        num_dice = 1

    player_dice = roll_dice(num_dice)
    print(f"\n{player_name}のサイコロ: {player_dice}")

    # コンピュータのターン
    comp_dice = roll_dice(num_dice)
    print(f"コンピュータのサイコロ: {comp_dice}")

    # 勝敗判定
    player_total = sum_dice(player_dice)
    comp_total = sum_dice(comp_dice)

    if player_total > comp_total:
        return 1
    elif player_total < comp_total:
        return -1
    else:
        return 0


def show_scoreboard(player_name: str, player_wins: int, comp_wins: int, ties: int, total_games: int) -> None:
    """スコアボードを表示する"""
    print("\n" + "-" * 40)
    print("【スコアボード】")
    print(f"プレイヤー ({player_name}): {player_wins}勝")
    print(f"コンピュータ:             {comp_wins}勝")
    print(f"引き分け:                 {ties}回")
    print(f"総試合数:                 {total_games}")
    if total_games > 0:
        win_rate = player_wins / total_games * 100
        print(f"勝率:                     {win_rate:.1f}%")
    print("-" * 40)


def main() -> None:
    """メインゲームループ"""
    print("\n" + "*" * 50)
    print("       ★ ダイスゲームへようこそ！ ★")
    print("*" * 50)
    print("ルール: プレイヤーとコンピュータがサイコロを振り、")
    print("        合計値の大きい方が勝ちです。")
    print("        何戦かプレイして、コンピュータに勝ちましょう！")

    player_name = input("\nあなたの名前を入力してください: ")
    while not player_name.strip():
        player_name = input("名前は空白にできません。入力してください: ")

    player_wins = 0
    comp_wins = 0
    ties = 0
    total_games = 0

    while True:
        print(f"\n--- {player_name}のターン ---")

        result = play_single_round(player_name)
        display_round_from_result(result, player_name)
        total_games += 1

        if result == 1:
            player_wins += 1
        elif result == -1:
            comp_wins += 1
        else:
            ties += 1

        show_scoreboard(player_name, player_wins, comp_wins, ties, total_games)

        # 継続判定
        play_again = ask_input("\nもう一度プレイしますか？ (y/n): ", ["y", "n"])
        if play_again == "n":
            break

    # ゲーム終了
    print(f"\n{'=' * 50}")
    print(f"{player_name}さん、ありがとうございました！")
    print("最終結果:")
    show_scoreboard(player_name, player_wins, comp_wins, ties, total_games)

    if player_wins > comp_wins:
        print(f"おめでとう！{player_name}さんの勝ちです！")
    elif player_wins < comp_wins:
        print("コンピュータの勝ちでした。次回リベンジしてください！")
    else:
        print("見事な引き分けです！")
    print("=" * 50)


def display_round_from_result(result: int, player_name: str) -> None:
    """勝敗結果から簡単なメッセージを表示する補助関数"""
    if result == 1:
        print(f">> {player_name}の勝ち！ <<")
    elif result == -1:
        print(">> コンピュータの勝ち！ <<")
    else:
        print(">> 引き分け！ <<")


if __name__ == "__main__":
    main()
