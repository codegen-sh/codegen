def greet_user(name: str | None = None) -> None:
    if name:
        print(f"Hello, {name}")
    else:
        print("Hello, Guest")


def process_data(data: list[int], factor: int | None = None) -> dict[str, int]:
    result = {}
    for item in data:
        if factor:
            result[str(item)] = item * factor
        else:
            result[str(item)] = item
    print(f"Processed {len(data)} items")
    return result


def complex_operation(x, y):
    result = x * y
    print(f"Result: {result}")
    return result


def main():
    greet_user("Alice")
    data = [1, 2, 3, 4, 5]
    processed = process_data(data, 2)
    print(f"Processed data: {processed}")
    complex_operation(3, 4)


if __name__ == "__main__":
    main()
