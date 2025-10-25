# Perfect Number Finder

A Python program that discovers perfect numbers by testing for Mersenne primes using the Lucas-Lehmer primality test.

## What are Perfect Numbers?

A perfect number is a positive integer that equals the sum of its proper divisors (excluding itself). For example, 6 is perfect because 6 = 1 + 2 + 3.

Perfect numbers are connected to Mersenne primes through Euclid-Euler theorem: if 2^p - 1 is prime (a Mersenne prime), then 2^(p-1) × (2^p - 1) is a perfect number.

## Features

- **Automated Search**: Continuously searches for perfect numbers by testing Mersenne prime candidates
- **Resume Capability**: Automatically resumes from the last tested exponent if interrupted
- **Progress Tracking**: Real-time display of the current exponent being tested with a spinner animation
- **CSV Export**: Saves all discovered perfect numbers to `perfect_numbers.csv`
- **Colored Output**: Terminal formatting for better readability

## Requirements

- Python 3.x
- Standard library only (no external dependencies)

## Usage

Run the program:

```bash
python perfect_numbers.py
```

Press **Enter** to start the search, and **Ctrl+C** to stop at any time.

## How It Works

1. **Lucas-Lehmer Test**: Uses the Lucas-Lehmer primality test to efficiently check if 2^p - 1 is prime
2. **Perfect Number Calculation**: For each Mersenne prime found, calculates the corresponding perfect number using the formula 2^(p-1) × (2^p - 1)
3. **Persistent Storage**: Records results in CSV format with columns: `exponent (p), perfect_number`
4. **Auto-Resume**: On restart, reads the CSV file to determine where to continue searching

## Output Format

The program creates/appends to `perfect_numbers.csv` with the following structure:

```
p,perfect_number
2,6
3,28
5,496
7,8128
...
```

## Performance Notes

- The program gets progressively slower as it tests larger exponents
- Known perfect numbers become extremely large (thousands of digits)
- The search can run indefinitely until manually stopped
- Uses efficient bit operations for calculations

## Controls

- **Enter**: Start the search
- **Ctrl+C**: Stop the search gracefully (current progress is saved)

## Example Output

```
<== Welcome to the Perfect Number Finder! ==>

Output will be saved to: 'perfect_numbers.csv'
Starting from exponent: p=2
Controls: Press Enter to start, Ctrl+C to stop at any time.

Found perfect number for p=2, digits~1
Found perfect number for p=3, digits~2
Searching p=4 /
```

## License

This is a personal project for exploring mathematical concepts.
