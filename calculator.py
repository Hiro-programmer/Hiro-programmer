def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("0で割ることはできません")
    return a / b

def calculate(expression):
    history = []

    print("=== 電卓 ===")
    print("終了するには 'q' を入力してください")
    print("操作: +, -, *, /\n")

    while True:
        user_input = input("計算式を入力 (例: 3 + 5): ").strip()

        if user_input.lower() == 'q':
            print("\n履歴:")
            for h in history:
                print(f"  {h}")
            print("終了します。")
            break

        try:
            parts = user_input.split()
            if len(parts) != 3:
                print("形式が正しくありません。例: 3 + 5\n")
                continue

            a, op, b = float(parts[0]), parts[1], float(parts[2])

            if op == '+':
                result = add(a, b)
            elif op == '-':
                result = subtract(a, b)
            elif op == '*':
                result = multiply(a, b)
            elif op == '/':
                result = divide(a, b)
            else:
                print(f"未対応の演算子: {op}\n")
                continue

            output = f"{user_input} = {result}"
            print(f"答え: {result}\n")
            history.append(output)

        except ValueError as e:
            print(f"エラー: {e}\n")
        except Exception:
            print("入力が正しくありません。\n")

if __name__ == "__main__":
    calculate(None)
