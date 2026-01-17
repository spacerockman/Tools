def snowflake(n):
    """Prints a snowflake pattern of size n."""

    if n % 2 == 0:
        n += 1  # Make sure n is odd

    for i in range(n):
        # Calculate the number of stars and spaces for each row
        stars = 2 * (n // 2 - abs(i - n // 2)) + 1
        spaces = (n - stars) // 2

        # Print spaces, stars, and spaces
        print(" " * spaces + "*" * stars + " " * spaces)

def print_cow():
    
    print("       (__)")
    print("       (oo)")
    print("  /------\/")
    print(" * |    ||")
    print("   ||----||")
    print("   ^^    ^^")
if __name__ == "__main__":
    size = 7  # Adjust the size for different snowflake patterns
    snowflake(size)
    print_cow()
