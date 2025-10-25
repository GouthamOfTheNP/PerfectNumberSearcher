import csv
import os
import sys
import time
import math

CSV_FILE = "perfect_numbers.csv"

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"


def is_mersenne_prime(p):
    if p == 2:
        return True
    M = (1 << p) - 1
    s = 4
    for _ in range(p - 2):
        s = (s * s - 2) % M
    return s == 0


def perfect_number(p):
    return (1 << (p - 1)) * ((1 << p) - 1)


def get_start_index():
    if not os.path.exists(CSV_FILE):
        return 2
    with open(CSV_FILE, "r") as f:
        last_line = None
        for line in f:
            last_line = line
        if not last_line:
            return 2
        last_p = int(last_line.split(',')[0])
        return last_p + 1


csv_file = open(CSV_FILE, "a", newline="", buffering=1)
writer = csv.writer(csv_file)
p = get_start_index()

title = "<== Welcome to the Perfect Number Finder! ==>"

width = len(title) + 4
top_border = f"{BOLD}{CYAN}+" + "-" * width + f"+{RESET}"
bottom_border = f"{BOLD}{CYAN}+" + "-" * width + f"+{RESET}"

print()
print(top_border)
padding = width - len(title)
left_padding = padding // 2
right_padding = padding - left_padding
print(f"{BOLD}{CYAN}|{' ' * left_padding}{title}{' ' * right_padding}|{RESET}")
print(bottom_border)
print()

print(f"{YELLOW}Output will be saved to:{RESET} {BOLD}{GREEN}'{CSV_FILE}'{RESET}")
print(f"{YELLOW}Starting from exponent:{RESET} {BOLD}{MAGENTA}p={p}{RESET}")
print(f"{YELLOW}Controls:{RESET} Press {BOLD}Enter{RESET} to start, {BOLD}Ctrl+C{RESET} to stop at any time.")
input()

print(f"{BOLD}{CYAN}{'-' * (width + 2)}{RESET}")

print(f"--> Press {BOLD}Ctrl+C{RESET} to stop the search at any time.\n")

spinner = "|/-\\"
spinner_index = 0

try:
    while True:
        if is_mersenne_prime(p):
            sys.stdout.write("\r" + " " * 50 + "\r")
            sys.stdout.flush()

            n = perfect_number(p)
            estimated_digits = int(p * math.log10(2)) + int(math.log10((1 << p) - 1)) + 1
            writer.writerow([p, n])
            csv_file.flush()
            time.sleep(0.4)
            print(f"Found perfect number for {BOLD}p={p}{RESET}, {BOLD}digits~{estimated_digits}{RESET}")
            time.sleep(.4)
        else:
            sys.stdout.write(f"\rSearching p={BOLD}{p}{RESET} {spinner[spinner_index % len(spinner)]}")
            if spinner_index % 10 == 0:
                sys.stdout.flush()
            spinner_index += 1
            time.sleep(0.1)
        p += 1
except KeyboardInterrupt:
    print("\nSearch stopped by user.")
finally:
    csv_file.close()
