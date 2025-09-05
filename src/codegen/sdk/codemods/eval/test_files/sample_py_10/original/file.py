def greet_user(name: str | None = None) -> None:
    if name:
        print("Hello, " + name)
    else:
        print("Hello, Guest")


def process_data(data: list[int], factor: int | None = None) -> dict[str, int]:
    result = {}
    for item in data:
        if factor:
            result[str(item)] = item * factor
        else:
            result[str(item)] = item
    print("Processed " + str(len(data)) + " items")
    return result


def complex_operation(x, y):
    result = x * y
    print("Result: " + str(result))
    return result


def main():
    greet_user("Alice")
    data = [1, 2, 3, 4, 5]
    processed = process_data(data, 2)
    print("Processed data: " + str(processed))
    complex_operation(3, 4)


if __name__ == "__main__":
    main()
