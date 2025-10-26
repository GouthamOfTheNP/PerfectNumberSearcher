# Perfect Number Network

A complete distributed computing system for discovering **perfect numbers** via the Euclid-Euler theorem, inspired by the Great Internet Mersenne Prime Search (GIMPS).

## What Are Perfect Numbers?

A **perfect number** is a positive integer that equals the sum of its proper divisors (all divisors except the number itself).

**Examples:**
- **6** = 1 + 2 + 3 (divisors: 1, 2, 3)
- **28** = 1 + 2 + 4 + 7 + 14 (divisors: 1, 2, 4, 7, 14)
- **496** = 1 + 2 + 4 + 8 + 16 + 31 + 62 + 124 + 248
- **8128** = 1 + 2 + 4 + 8 + ... + 4064

## The Euclid-Euler Theorem

**Every even perfect number** can be expressed as:

```
P = 2^(p-1) × (2^p - 1)
```

where `2^p - 1` is a **Mersenne prime**.

This remarkable connection between perfect numbers and Mersenne primes (discovered by Euclid ~300 BC, proven by Euler in 1772) means:
- Finding a Mersenne prime → Finding a perfect number
- We test Mersenne numbers using the Lucas-Lehmer primality test
- If `M(p) = 2^p - 1` is prime, we've found a perfect number!

**Known perfect numbers:** Only 51 are known (as of 2024). The largest has 49,724,095 digits!

## Overview

This distributed system coordinates searches for perfect numbers by testing Mersenne primes. When we verify that `2^p - 1` is prime via the Lucas-Lehmer test, we've discovered a new perfect number `P = 2^(p-1) × (2^p - 1)`.

## System Components

### 🖥️ server.py - Coordination Server
The main server that distributes work and tracks discoveries.

**Features:**
- Work assignment with time-based reservations (24-72 hours)
- Progress tracking and reporting
- Automatic reassignment of expired work
- User credit and contribution tracking
- SQLite database for persistence
- Priority-based work queue
- Result verification and storage

**Usage:**
```bash
python server.py [port]
python server.py 5555
```

### 💻 client.py - Computational Worker
The worker client that performs Lucas-Lehmer tests to verify perfect numbers.

**Features:**
- Lucas-Lehmer primality testing for Mersenne numbers
- Progress reporting every 5 minutes
- Checkpoint system (saves every 10,000 iterations)
- Resume capability for interrupted tests
- Real-time progress display with ETA
- Automatic work request and submission
- Perfect number calculation and display

**Usage:**
```bash
python client.py [server_host] [server_port]
python client.py                    # localhost:5555
python client.py 192.168.1.100     # remote server
python client.py localhost 8080    # custom port
```

### 🌐 dashboard.py - Web Dashboard
Real-time web-based monitoring dashboard.

**Features:**
- Live statistics and progress
- Active search tracking
- User leaderboard
- Perfect number discovery announcements
- Recent results feed with digit counts
- Auto-refresh every 10 seconds
- Responsive design
- Euclid-Euler theorem display

**Usage:**
```bash
python dashboard.py [http_port] [db_file]
python dashboard.py 8080 perfectnet.db
```

Then open: `http://localhost:8080`

### 📊 monitor.py - Status Monitor
Command-line tool to query server and database status.

**Features:**
- Server statistics via network
- Detailed database analysis
- Top contributors
- Recent activity feed
- Current searches
- Discovered perfect numbers list
- Work queue preview

**Usage:**
```bash
python monitor.py [server_host] [server_port]
python monitor.py localhost 5555
```

### 🔧 admin.py - Administration Tool
Database management and administrative functions.

**Features:**
- Add work to queue
- Add ranges of exponents
- Reset expired assignments
- Clear user assignments
- Export results to CSV
- Database optimization
- Detailed statistics

**Usage:**
```bash
python admin.py [command] [options]

# Add specific exponents
python admin.py add-work 521 607 1279

# Add range of prime exponents
python admin.py add-range 10000 20000

# Reset expired assignments
python admin.py reset

# Clear user's work
python admin.py clear-user alice

# Export results
python admin.py export results.csv

# Show statistics
python admin.py stats

# Optimize database
python admin.py vacuum
```

### ⚡ benchmark.py - Performance Benchmark
Test system performance and estimate completion times.

**Features:**
- Quick, medium, and large benchmark suites
- Test specific exponents
- Performance estimates
- Speed calculations
- Recommendations for optimal work size
- Perfect number verification display

**Usage:**
```bash
python benchmark.py [test_level]

# Quick benchmark (recommended first run)
python benchmark.py quick

# Medium benchmark (~1 minute)
python benchmark.py medium

# Large benchmark (~several minutes)
python benchmark.py large

# Test specific exponent
python benchmark.py 2281
```

## Quick Start Guide

### 1. Start the Server
```bash
python server.py
```
Output:
```
╔════════════════════════════════════════════════════════════════════╗
║                 Perfect Number Network Server                      ║
╚════════════════════════════════════════════════════════════════════╝
Server: 0.0.0.0:5555
Database: perfectnet.db

💡 Searching for perfect numbers via the Euclid-Euler theorem:
   P = 2^(p-1) × (2^p - 1) where 2^p - 1 is prime

Status: Waiting for clients...
```

### 2. (Optional) Start Web Dashboard
In another terminal:
```bash
python dashboard.py
```
Open browser to: `http://localhost:8080`

### 3. Run Benchmark (Recommended)
In another terminal:
```bash
python benchmark.py quick
```
This shows your system's performance and estimates completion times.

### 4. Start Client(s)
In one or more terminals:
```bash
python client.py
```
Enter a username when prompted. The client will:
- Connect to the server
- Receive perfect number candidates
- Perform Lucas-Lehmer tests
- Report progress
- Submit results (including perfect number if found!)

### 5. Monitor Progress
```bash
python monitor.py
```
or visit the web dashboard at `http://localhost:8080`

## System Architecture

```
┌──────────────────┐
│  Web Dashboard  │ ← HTTP :8080
│  (dashboard.py) │
└────────┬─────────┘
         │
    ┌────▼────────────────────────────────┐
    │                                     │
    │         Server (server.py)          │
    │         ├─ Work Queue               │
    │         ├─ Assignment Manager       │
    │         ├─ Result Collector         │
    │         └─ SQLite Database          │
    │                                     │
    └────────┬────────────────────────────┘
             │ TCP :5555
      ┌──────┴──────┬───────────┬─────────────┐
      │             │           │             │
┌─────▼──────┐ ┌────▼─────┐ ┌───▼──────┐ ┌────▼──────┐
│  Client   │ │ Client  │ │ Client  │ │  Monitor │
│  (alice)  │ │  (bob)  │ │ (carol) │ │   Tool   │
└───────────┘ └─────────┘ └─────────┘ └──────────┘
```

## How It Works

### Perfect Numbers via Mersenne Primes

**Mersenne number**: M(p) = 2^p - 1

A Mersenne number is prime only for prime values of p.

**The Connection:**
- Test if M(p) = 2^p - 1 is prime (using Lucas-Lehmer)
- If M(p) is prime → P = 2^(p-1) × M(p) is a perfect number!

**Known Perfect Numbers (via Mersenne primes):**
- P₁ = 6 (p=2)
- P₂ = 28 (p=3)
- P₃ = 496 (p=5)
- P₄ = 8,128 (p=7)
- P₅ = 33,550,336 (p=13)
- ... (51 known as of 2024)

### Lucas-Lehmer Test

The most efficient primality test for Mersenne numbers:

```
1. Let s = 4
2. For i = 1 to p-2:
      s = (s² - 2) mod M(p)
3. If s = 0, then M(p) is prime
   → Therefore P = 2^(p-1) × M(p) is a perfect number!
```

### Work Distribution Flow

1. **Server starts** and initializes work queue with exponents to test
2. **Client connects** and registers with username
3. **Server assigns** smallest untested exponent with time limit
4. **Client performs** Lucas-Lehmer test on M(p) = 2^p - 1
5. **Client reports** progress every 5 minutes
6. **Client checkpoints** every 10,000 iterations
7. **Client submits** result:
    - If M(p) is prime → Perfect number P = 2^(p-1) × M(p) discovered!
    - If M(p) is composite → Candidate rejected
8. **Server records** result and credits user
9. **Server celebrates** if perfect number found!
10. **Server assigns** next work item
11. **If work expires**, server automatically reassigns to another client

## Database Schema

### users
- `username` - User identifier
- `total_ghz_days` - Total computational contribution
- `exponents_tested` - Number of completed tests
- `perfect_numbers_found` - Perfect numbers discovered
- `last_active` - Last activity timestamp

### assignments
- `exponent` - Exponent being tested (for candidate P = 2^(p-1) × M(p))
- `username` - Assigned user
- `assigned_at` - Assignment timestamp
- `expires_at` - Expiration timestamp
- `status` - 'assigned' or 'completed'
- `progress` - Percentage complete (0-100)
- `last_update` - Last progress update

### results
- `exponent` - Tested exponent
- `username` - User who completed test
- `is_perfect` - Boolean: is this a perfect number?
- `perfect_number` - The perfect number value (if verified)
- `digit_count` - Number of digits in the perfect number
- `discovered_at` - Completion timestamp
- `residue` - Final residue (for verification)
- `time_seconds` - Test duration

### work_queue
- `exponent` - Exponent to test
- `priority` - Priority value (higher = sooner)
- `added_at` - Queue entry timestamp

## Performance Estimates

Based on modern hardware (approximate):

| Exponent | Perfect Number Digits | Time Estimate |
|----------|----------------------|---------------|
| 127      | 77                   | < 1 second    |
| 521      | 314                  | < 1 second    |
| 1,279    | 770                  | ~1 second     |
| 2,281    | 1,373                | ~5 seconds    |
| 9,941    | 5,985                | ~30 seconds   |
| 21,701   | 13,066               | ~3 minutes    |
| 44,497   | 26,790               | ~15 minutes   |
| 100,000  | 60,206               | ~2 hours      |
| 1,000,000| 602,060              | ~7 days       |

**Note**: Times vary greatly by CPU. Run `benchmark.py` for your system.

## Running a Network

### Local Testing (Single Machine)
```bash
# Terminal 1: Server
python server.py

# Terminal 2: Dashboard
python dashboard.py

# Terminal 3: Client 1
python client.py
# Username: alice

# Terminal 4: Client 2
python client.py
# Username: bob
```

### Multi-Machine Network
```bash
# Server machine (192.168.1.100)
python server.py 5555

# Client machines
python client.py 192.168.1.100 5555
```

### Adding Work
```bash
# Add known perfect number exponents (for testing)
python admin.py add-work 2 3 5 7 13 17 19 31 61 89 107 127

# Add range for real searching
python admin.py add-range 10000 20000

# Add large exponents (serious searching!)
python admin.py add-range 100000 200000
```

## Management Tasks

### Monitor Status
```bash
python monitor.py
python admin.py stats
```

### Reset Stuck Work
```bash
python admin.py reset
```

### Clear User's Assignments
```bash
python admin.py clear-user username
```

### Export Results
```bash
python admin.py export results.csv
```

### Optimize Database
```bash
python admin.py vacuum
```

## Example Session Output

**Server:**
```
Client registered: alice from 127.0.0.1:54321
Assigned P(p=127) to alice (77 digits)
Progress: alice - candidate P(p=127) - 100.0% complete

══════════════════════════════════════════════════════════════════
🎉 PERFECT NUMBER DISCOVERED! 🎉
Perfect Number: 2^126 × (2^127 - 1)
Digits: 77
Discovered by: alice
Value: 14474011154664524427946373126085988...
(Verified via Mersenne prime M(127) = 2^127 - 1)
══════════════════════════════════════════════════════════════════
```

**Client:**
```
╔════════════════════════════════════════════════════════════════╗
║  New Perfect Number Candidate Assignment                       ║
╚════════════════════════════════════════════════════════════════╝
Candidate: P = 2^126 × (2^127 - 1)
Digits: 77
Time allowed: 24 hours

Verifying via Lucas-Lehmer test of M(127)...

Lucas-Lehmer test for M(127) = 2^127 - 1
Iterations needed: 125
If prime → P = 2^126 × M(127) is a perfect number

Iteration 125/125 (100.00%) - ETA: 0s

✓ Test completed in 0.02 seconds
✓ Result submitted successfully

══════════════════════════════════════════════════════════════════
🎉 PERFECT NUMBER DISCOVERED! 🎉
P = 2^126 × (2^127 - 1)
Digits: 77
Value: 14474011154664524427946373126085988...

✓ This equals the sum of all its proper divisors!
(Verified via Mersenne prime M(127) = 2^127 - 1)
══════════════════════════════════════════════════════════════════
```

## Fun Perfect Number Facts

1. **All known perfect numbers are even.** Whether odd perfect numbers exist is one of the oldest unsolved problems in mathematics!

2. **All even perfect numbers end in 6 or 28** (in base 10)

3. **The sum of reciprocals** of divisors of a perfect number equals 2:
    - For 6: 1/1 + 1/2 + 1/3 + 1/6 = 2

4. **Perfect numbers are rare**: Only 51 known in all of mathematics

5. **The largest known perfect number** (discovered 2018) has 49,724,095 digits!

6. **Ancient Greeks** knew the first 4 perfect numbers (6, 28, 496, 8128)

7. **Euclid** (300 BC) discovered the formula connecting them to Mersenne primes

8. **Euler** (1772) proved all even perfect numbers follow this formula

## Comparison to GIMPS

This project is inspired by GIMPS (Great Internet Mersenne Prime Search) but focuses on the beauty of **perfect numbers**:

| Feature | GIMPS/mprime | This Implementation |
|---------|-------------|---------------------|
| **Primary Goal** | Mersenne primes | **Perfect numbers** |
| **Display** | "M(p) is prime!" | **"P is a perfect number!"** |
| Communication | PrimeNet API (HTTP) | JSON over TCP |
| Database | MySQL/PostgreSQL | SQLite |
| Test algorithm | LL + FFT + optimizations | Lucas-Lehmer (basic) |
| Checkpointing | Every 10-30 min | Every 10,000 iterations |
| Work reservation | Yes (days/weeks) | Yes (24-72 hours) |
| User credit | Yes | Yes |
| Web interface | Yes | Yes (included) |

## Future Enhancements

- **Trial factoring**: Pre-screen candidates with small factors
- **P-1 factoring**: Pollard's p-1 method
- **FFT multiplication**: Speed up large exponent tests dramatically
- **Double-checking**: Verify results independently
- **GPU acceleration**: OpenCL/CUDA support
- **Email notifications**: Alert on perfect number discoveries
- **Perfect number properties**: Calculate and display divisor sums
- **Historical context**: Display when each perfect number was discovered

## System Requirements

- **Python 3.7+** (no external dependencies!)
- **RAM**: 1GB+ (more for large exponents)
- **CPU**: Any (faster = better)
- **Disk**: 100MB+ for database
- **Network**: For distributed operation

## Educational Value

This project demonstrates:
- **Number theory**: Perfect numbers, Mersenne primes, Euclid-Euler theorem
- **Distributed computing**: Coordinating work across multiple machines
- **Algorithms**: Lucas-Lehmer primality test
- **Network programming**: TCP sockets, JSON protocols
- **Database design**: SQLite for persistence
- **Web development**: Real-time dashboards
- **Mathematics history**: Ancient Greeks to modern discoveries

## Contributing

This is an educational demonstration system focused on the beauty of perfect numbers. For actual Mersenne prime hunting (which finds perfect numbers!), join the real GIMPS project at **https://www.mersenne.org**!

## Credits

- Inspired by GIMPS (Great Internet Mersenne Prime Search)
- Lucas-Lehmer test algorithm
- Euclid (~300 BC) - Discovery of perfect number formula
- Euler (1772) - Proof of Euclid-Euler theorem
- Perfect number research community

## License

Public domain - for educational purposes

---

**Happy Perfect Number Hunting! ✨🔢**

*"Perfect numbers, like perfect men, are very rare." - René Descartes*

*"The study of perfect numbers... has, from the earliest times, engaged the attention of mathematicians." - Leonard Eugene Dickson*