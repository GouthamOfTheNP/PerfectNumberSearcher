import csv
import os
import sys
import time
import math
from pathlib import Path

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
RED = "\033[31m"

SLEEP_FOUND = 0.4
SLEEP_SEARCHING = 0.05
FLUSH_INTERVAL = 10
SPINNER_CHARS = "|/-\\"

KNOWN_MERSENNE_PRIMES = [2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127]

default_csv_path = Path.home() / "Downloads" / "perfect_numbers.csv"
config_file_path = Path.home() / "Downloads" / ".perfect_numbers_config"


def save_csv_path(path):
    try:
        with open(config_file_path, "w") as f:
            f.write(str(path))
    except Exception:
        pass


def log_message(msg, csv_path):
    try:
        log_file = Path(csv_path).parent / "perfect_numbers_output.txt"
        with open(log_file, "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def get_csv_path():
    if config_file_path.exists():
        try:
            with open(config_file_path, "r") as f:
                path = f.read().strip()
                if path and Path(path).parent.exists():
                    return path
        except Exception:
            pass
    print(f"{CYAN}First time setup: Please choose where to save your perfect numbers.{RESET}")
    while True:
        path_input = input(f"{YELLOW}Output CSV file [default: {default_csv_path}]: {RESET}").strip()
        path = Path(path_input) if path_input else default_csv_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
            save_csv_path(path)
            return str(path)
        except (IOError, OSError, PermissionError) as e:
            print(f"{RED}Error: Cannot write to {path}. Please choose a different location.{RESET}")


def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def is_mersenne_prime(p):
    if p < 10000:
        if not is_prime(p):
            return False
    if p == 2:
        return True
    M = (1 << p) - 1
    s = 4
    for _ in range(p - 2):
        s = (s * s - 2) % M
    return s == 0

def perfect_number(p):
    return (1 << (p - 1)) * ((1 << p) - 1)


def get_start_index(csv_path):
    if not os.path.exists(csv_path):
        return 2
    try:
        with open(csv_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            if not lines:
                return 2
            last_line = lines[-1]
            last_p = int(last_line.split(',')[0])
            return last_p + 1
    except Exception:
        print(f"{YELLOW}Warning: Could not parse CSV file. Starting from p=2.{RESET}")
        return 2


def print_header(csv_file, start_p):
    title = "<== Welcome to the Perfect Number Finder! ==>"
    width = len(title) + 4
    border = f"{BOLD}{CYAN}+" + "-" * width + f"+{RESET}"
    
    print()
    print(border)
    padding = width - len(title)
    left_padding = padding // 2
    right_padding = padding - left_padding
    print(f"{BOLD}{CYAN}|{' ' * left_padding}{title}{' ' * right_padding}|{RESET}")
    print(border)
    print()
    
    print(f"{YELLOW}Output will be saved to:{RESET} {BOLD}{GREEN}'{csv_file}'{RESET}")
    print(f"{YELLOW}Starting from exponent:{RESET} {BOLD}{MAGENTA}p={start_p}{RESET}")
    print(f"{YELLOW}Known Mersenne primes loaded:{RESET} {BOLD}{len(KNOWN_MERSENNE_PRIMES)}{RESET}")
    print(f"{YELLOW}Controls:{RESET} Press {BOLD}Enter{RESET} to start, {BOLD}Ctrl+C{RESET} to stop at any time.")
    input()
    print(f"{BOLD}{CYAN}{'-' * (width + 2)}{RESET}")
    print(f"--> Press {BOLD}Ctrl+C{RESET} to stop the search at any time.\n")


csv_path = get_csv_path()
p = get_start_index(csv_path)

print_header(csv_path, p)

try:
    with open(csv_path, "a", newline="", buffering=1) as csv_file:
        writer = csv.writer(csv_file)
        
        known_to_add = [prime for prime in KNOWN_MERSENNE_PRIMES if prime >= p]
        if known_to_add:
            print(f"{CYAN}Pre-calculating {len(known_to_add)} known Mersenne primes...{RESET}")
            for prime in known_to_add:
                n = perfect_number(prime)
                estimated_digits = int((2*prime - 1) * math.log10(2)) + 1
                writer.writerow([prime, n])
                csv_file.flush()
                msg = f"Added known perfect number for p={prime}, digits~{estimated_digits}"
                print(f"{GREEN}{msg}{RESET}")
                log_message(msg, csv_path)
            print()
        
        if p <= KNOWN_MERSENNE_PRIMES[-1]:
            p = KNOWN_MERSENNE_PRIMES[-1] + 1
            print(f"{YELLOW}Skipping to p={p} (after known primes){RESET}\n")
        
        spinner_index = 0
        
        while True:
            if is_mersenne_prime(p):
                sys.stdout.write("\r" + " " * 80 + "\r")
                sys.stdout.flush()
                
                estimated_digits = int((2*p - 1) * math.log10(2)) + 1
                
                try:
                    n = perfect_number(p)
                    writer.writerow([p, n])
                    csv_file.flush()
                except IOError as e:
                    msg = f"Error writing to CSV: {e}"
                    print(f"\n{RED}{msg}{RESET}")
                    log_message(msg, csv_path)
                    break
                
                time.sleep(SLEEP_FOUND)
                msg = f"Found perfect number for p={p}, digits~{estimated_digits}"
                print(f"{GREEN}{msg}{RESET}")
                log_message(msg, csv_path)
                
            else:
                spinner = SPINNER_CHARS[spinner_index % len(SPINNER_CHARS)]
                sys.stdout.write(f"\rSearching p={BOLD}{p}{RESET} {spinner}")
                
                if spinner_index % FLUSH_INTERVAL == 0:
                    sys.stdout.flush()
                
                spinner_index += 1
                time.sleep(SLEEP_SEARCHING)
            
            p += 1         
except KeyboardInterrupt:
    print(f"\n{YELLOW}Search stopped by user.{RESET}")
except Exception as e:
    msg = f"Unexpected error: {e}"
    print(f"\n{RED}{msg}{RESET}")
    log_message(msg, csv_path)
finally:
    print(f"{GREEN}Progress saved. Last checked: p={p-1}{RESET}")
