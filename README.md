# Perfect Number Network (GIMPS-style)

A complete distributed computing system for discovering Mersenne primes and perfect numbers, modeled after the Great Internet Mersenne Prime Search (GIMPS) project.

## Overview

This system coordinates distributed searches for Mersenne primes using the Lucas-Lehmer primality test. When a Mersenne prime 2^p - 1 is found, it generates a perfect number: 2^(p-1) × (2^p - 1).

## System Components

### 🖥️ server.py - Coordination Server
The main server that distributes work and tracks progress.

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
The worker client that performs Lucas-Lehmer tests.

**Features:**
- Lucas-Lehmer primality testing
- Progress reporting every 5 minutes
- Checkpoint system (saves every 10,000 iterations)
- Resume capability for interrupted tests
- Real-time progress display with ETA
- Automatic work request and submission

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
- Active assignment tracking
- User leaderboard
- Discovery announcements
- Recent results feed
- Auto-refresh every 10 seconds
- Responsive design

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
- Current assignments
- Discovered primes list
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
╔════════════════════════════════════════════════════════════╗
║  Perfect Number Network Server (GIMPS-style)             ║
╚════════════════════════════════════════════════════════════╝
Server: 0.0.0.0:5555
Database: perfectnet.db
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
- Receive work assignments
- Perform Lucas-Lehmer tests
- Report progress
- Submit results

### 5. Monitor Progress
```bash
python monitor.py
```
or visit the web dashboard at `http://localhost:8080`

## System Architecture

```
┌─────────────────┐
│  Web Dashboard  │ ← HTTP :8080
│  (dashboard.py) │
└────────┬────────┘
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
┌─────▼─────┐ ┌────▼────┐ ┌───▼─────┐ ┌────▼─────┐
│  Client   │ │ Client  │ │ Client  │ │  Monitor │
│  (alice)  │ │  (bob)  │ │ (carol) │ │   Tool   │
└───────────┘ └─────────┘ └─────────┘ └──────────┘
```

## How It Works

### Mersenne Primes and Perfect Numbers

**Mersenne number**: M(p) = 2^p - 1

A Mersenne number is prime only for prime values of p. Known Mersenne primes:
- M(2) = 3
- M(3) = 7
- M(5) = 31
- M(7) = 127
- M(13) = 8191
- ... (51 known as of 2024)

**Perfect number**: When M(p) is prime, then 2^(p-1) × (2^p - 1) is perfect.

Example: M(7) = 127 is prime → Perfect number = 2^6 × 127 = 8128

### Lucas-Lehmer Test

The most efficient primality test for Mersenne numbers:

```
1. Let s = 4
2. For i = 1 to p-2:
      s = (s² - 2) mod M(p)
3. If s = 0, then M(p) is prime
```

### Work Distribution Flow

1. **Server starts** and initializes work queue with exponents to test
2. **Client connects** and registers with username
3. **Server assigns** smallest untested exponent with time limit
4. **Client performs** Lucas-Lehmer test
5. **Client reports** progress every 5 minutes
6. **Client checkpoints** every 10,000 iterations
7. **Client submits** result (prime or composite) with residue
8. **Server records** result and credits user
9. **Server assigns** next work item
10. **If work expires**, server automatically reassigns to another client

## Database Schema

### users
- `username` - User identifier
- `total_ghz_days` - Total computational contribution
- `exponents_tested` - Number of completed tests
- `primes_found` - Mersenne primes discovered
- `last_active` - Last activity timestamp

### assignments
- `exponent` - Mersenne exponent being tested
- `username` - Assigned user
- `assigned_at` - Assignment timestamp
- `expires_at` - Expiration timestamp
- `status` - 'assigned' or 'completed'
- `progress` - Percentage complete (0-100)
- `last_update` - Last progress update

### results
- `exponent` - Tested exponent
- `username` - User who completed test
- `is_prime` - Boolean result
- `perfect_number` - Generated perfect number (if prime)
- `discovered_at` - Completion timestamp
- `residue` - Final residue (for verification)
- `time_seconds` - Test duration

### work_queue
- `exponent` - Exponent to test
- `priority` - Priority value (higher = sooner)
- `added_at` - Queue entry timestamp

## Performance Estimates

Based on modern hardware (approximate):

| Exponent | Iterations | Time Estimate |
|----------|-----------|---------------|
| 127      | 125       | < 1 second    |
| 521      | 519       | < 1 second    |
| 1,279    | 1,277     | ~1 second     |
| 2,281    | 2,279     | ~5 seconds    |
| 9,941    | 9,939     | ~30 seconds   |
| 21,701   | 21,699    | ~3 minutes    |
| 44,497   | 44,495    | ~15 minutes   |
| 100,000  | 99,998    | ~2 hours      |
| 1,000,000| 999,998   | ~7 days       |

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
# Add known Mersenne prime exponents (for testing)
python admin.py add-work 127 521 607 1279 2203 2281

# Add range for real searching
python admin.py add-range 10000 20000

# Add large exponents
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
Assigned p=127 to alice
Progress: alice - p=127 - 100.0% complete

═══════════════════════════════════════════════════════
🎉 MERSENNE PRIME FOUND! 🎉
Exponent: 127
Discovered by: alice
Perfect Number: 14474011154664524427946373126085988...
═══════════════════════════════════════════════════════
```

**Client:**
```
╔═══════════════════════════════════════════════════════════╗
║  New Assignment Received                                 ║
╚═══════════════════════════════════════════════════════════╝
Exponent: 2^127 - 1
Time allowed: 24 hours

Testing M(127) = 2^127 - 1
Iterations needed: 125
Starting Lucas-Lehmer test...

Iteration 125/125 (100.00%) - ETA: 0s

✓ Test completed in 0.02 seconds
✓ Result submitted successfully

═══════════════════════════════════════════════════════
🎉 MERSENNE PRIME DISCOVERED! 🎉
2^127 - 1 is PRIME
Perfect Number: 14474011154664524427946373126085988...
═══════════════════════════════════════════════════════
```

## Comparison to GIMPS

| Feature | GIMPS/mprime | This Implementation |
|---------|-------------|---------------------|
| Communication | PrimeNet API (HTTP) | JSON over TCP |
| Database | MySQL/PostgreSQL | SQLite |
| Test algorithm | LL + FFT + optimizations | Lucas-Lehmer (basic) |
| Checkpointing | Every 10-30 min | Every 10,000 iterations |
| Progress updates | Every 30 sec | Every 5 minutes |
| Work reservation | Yes (days/weeks) | Yes (24-72 hours) |
| Double-checking | Yes | Not implemented |
| User credit | Yes | Yes |
| TF/P-1 factoring | Yes | Not implemented |
| GPU support | Yes | No |
| Web interface | Yes | Yes (included) |

## Known Mersenne Prime Exponents

First 20: 2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127, 521, 607, 1279, 2203, 2281, 3217, 4253, 4423

The 51st Mersenne prime (discovered 2018) has exponent 82,589,933 and is 24,862,048 digits long!

## Future Enhancements

- **Trial factoring**: Pre-screen candidates with small factors
- **P-1 factoring**: Pollard's p-1 method
- **FFT multiplication**: Speed up large exponent tests dramatically
- **Double-checking**: Verify results independently
- **GPU acceleration**: OpenCL/CUDA support
- **Automatic benchmarking**: Optimize work assignment per client
- **Email notifications**: Alert on prime discoveries
- **REST API**: Modern HTTP API instead of raw TCP

## System Requirements

- **Python 3.7+** (no external dependencies!)
- **RAM**: 1GB+ (more for large exponents)
- **CPU**: Any (faster = better)
- **Disk**: 100MB+ for database
- **Network**: For distributed operation

## Troubleshooting

### Client can't connect
```bash
# Check if server is running
python monitor.py

# Check firewall settings
# Make sure port 5555 is open
```

### Work assignments expire
```bash
# Reset expired work
python admin.py reset

# Check client performance
python benchmark.py
```

### Database locked
```bash
# Close all clients and dashboard
# Restart server
# Optimize database
python admin.py vacuum
```

### Dashboard not loading
```bash
# Check if dashboard is running on correct port
# Try different port
python dashboard.py 8081
```

## Contributing

This is an educational demonstration system. For actual Mersenne prime hunting, join the real GIMPS project at **https://www.mersenne.org**!

## Credits

- Inspired by GIMPS (Great Internet Mersenne Prime Search)
- Lucas-Lehmer test algorithm
- Mersenne prime research community

## License

Public domain - for educational purposes

---

**Happy Prime Hunting! 🔢✨**

*"In theory, theory and practice are the same. In practice, they are not."*