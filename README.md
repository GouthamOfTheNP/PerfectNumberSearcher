# 🔢 Perfect Numbers Network

A distributed computing system for discovering **perfect numbers** through the search for Mersenne primes using the Lucas-Lehmer primality test.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![No Dependencies](https://img.shields.io/badge/dependencies-none-green.svg)]()

## 🌟 What are Perfect Numbers?

A **perfect number** is a positive integer that equals the sum of its proper divisors:

```
6 = 1 + 2 + 3  ✨ Perfect!
28 = 1 + 2 + 4 + 7 + 14  ✨ Perfect!
496 = 1 + 2 + 4 + 8 + 16 + 31 + 62 + 124 + 248  ✨ Perfect!
```

### The Euclid-Euler Theorem

Every even perfect number can be expressed as:

```
Perfect Number = 2^(p-1) × (2^p - 1)
```

where `2^p - 1` is a **Mersenne prime**.

This elegant formula connects perfect numbers to Mersenne primes, allowing us to discover new perfect numbers by finding Mersenne primes!

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- No external dependencies required!

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/perfect-numbers-network.git
cd perfect-numbers-network

# Start the server
python server.py

# In another terminal, start a client
python client.py

# (Optional) Start the web dashboard
python dashboard.py
# Visit http://localhost:8080
```

## 📁 Project Structure

```
perfect-numbers-network/
├── server.py          # Coordination server
├── client.py          # Computational client
├── dashboard.py       # Web monitoring dashboard
├── monitor.py         # CLI status monitor
├── admin.py           # Database administration
├── benchmark.py       # Performance testing
├── docs/              # GitHub Pages website
│   ├── index.html
│   ├── download.html
│   ├── docs.html
│   ├── technical.html
│   └── about.html
├── README.md
└── LICENSE
```

## 🎯 Features

### Server (`server.py`)
- 🔄 Distributes work assignments to clients
- 📊 Tracks progress and results in SQLite database
- ⏰ Automatic reassignment of expired work
- 👥 User contribution tracking and credits
- 🎉 Celebrates perfect number discoveries!

### Client (`client.py`)
- 🧮 Performs Lucas-Lehmer primality tests
- 💾 Saves checkpoints every 10,000 iterations
- 📡 Reports progress every 5 minutes
- ⚡ Displays real-time progress with ETA
- 🔄 Automatic resume after interruption

### Dashboard (`dashboard.py`)
- 📈 Real-time statistics and monitoring
- ✨ Perfect number discovery announcements
- 🏆 User leaderboard
- ⚙️ Active assignment tracking
- 🔄 Auto-refresh every 10 seconds

### Admin Tools (`admin.py`)
- ➕ Add work to queue
- 🔄 Reset expired assignments
- 📤 Export results to CSV
- 📊 Detailed statistics
- 🛠️ Database optimization

### Benchmark (`benchmark.py`)
- ⚡ Test system performance
- ⏱️ Estimate completion times
- 💡 Recommendations for optimal work size
- 🎯 Test specific exponents

## 📚 Documentation

Full documentation is available at: **[Your GitHub Pages URL]**

- [User Guide](docs.html) - Getting started and usage instructions
- [Technical Documentation](technical.html) - Algorithm details and architecture
- [About](about.html) - History and background

## 🎮 Usage Examples

### Running the Server

```bash
# Default port (5555)
python server.py

# Custom port
python server.py 8000
```

### Running a Client

```bash
# Connect to localhost
python client.py

# Connect to remote server
python client.py 192.168.1.100

# Custom port
python client.py localhost 8000
```

### Administration

```bash
# Add known perfect number exponents for testing
python admin.py add-work 2 3 5 7 13 17 19 31

# Add a range of exponents to test
python admin.py add-range 10000 20000

# Show detailed statistics
python admin.py stats

# Reset expired work
python admin.py reset

# Export results
python admin.py export results.csv
```

### Benchmarking

```bash
# Quick benchmark (recommended first)
python benchmark.py quick

# Test specific exponent
python benchmark.py 2281
```

### Monitoring

```bash
# Monitor server status
python monitor.py

# Monitor remote server
python monitor.py 192.168.1.100 5555
```

## 🎓 Educational Focus

This project emphasizes **perfect numbers** as the primary discovery goal:

1. **Perfect Number Generation**: Every test result immediately calculates the corresponding perfect number
2. **Perfect Number Display**: Results prominently show the perfect number, not just the Mersenne prime
3. **Perfect Number Education**: Documentation focuses on the history and properties of perfect numbers
4. **Perfect Number Celebration**: Discoveries celebrate finding perfect numbers first and foremost

### What You'll Learn

- 🔢 **Number Theory**: Perfect numbers, Mersenne primes, divisor functions
- 🧮 **Algorithms**: Lucas-Lehmer test, modular arithmetic, primality testing
- 🌐 **Distributed Computing**: Client-server architecture, work distribution, fault tolerance
- 💾 **Database Design**: SQLite, schema design, data persistence
- 🐍 **Python Programming**: Socket programming, threading, serialization
- 📊 **Data Visualization**: Real-time dashboards, progress tracking

## 🏆 Known Perfect Numbers

| Index | Exponent (p) | Perfect Number Formula | Digits | Year |
|-------|--------------|------------------------|--------|------|
| 1 | 2 | 2¹ × (2² - 1) = 6 | 1 | Ancient |
| 2 | 3 | 2² × (2³ - 1) = 28 | 2 | Ancient |
| 3 | 5 | 2⁴ × (2⁵ - 1) = 496 | 3 | Ancient |
| 4 | 7 | 2⁶ × (2⁷ - 1) = 8,128 | 4 | Ancient |
| 5 | 13 | 2¹² × (2¹³ - 1) = 33,550,336 | 8 | 1456 |
| ... | ... | ... | ... | ... |
| 51 | 82,589,933 | 2⁸²'⁵⁸⁹'⁹³² × (2⁸²'⁵⁸⁹'⁹³³ - 1) | 49,724,095 | 2018 |

## 📊 Performance Estimates

Approximate times on modern hardware:

| Exponent | Iterations | Estimated Time |
|----------|-----------|----------------|
| 127 | 125 | < 1 second |
| 521 | 519 | < 1 second |
| 2,281 | 2,279 | ~5 seconds |
| 21,701 | 21,699 | ~3 minutes |
| 100,000 | 99,998 | ~2 hours |
| 1,000,000 | 999,998 | ~7 days |

*Run `python benchmark.py` for your system's performance.*

## 🔧 System Requirements

### Minimum
- Python 3.7+
- 1 GB RAM
- 100 MB disk space
- Network connection (for distributed operation)

### Recommended
- Python 3.9+
- 4 GB+ RAM
- Multi-core CPU
- Stable network connection

## 🌐 Setting Up GitHub Pages

To deploy the documentation website:

1. **Enable GitHub Pages** in your repository settings
2. **Set source** to `main` branch and `/docs` folder
3. **Access your site** at `https://yourusername.github.io/perfect-numbers-network/`

Or use the root directory:

```bash
# Move docs files to root for GitHub Pages
mv docs/* .
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. 🐛 **Report bugs** via GitHub Issues
2. 💡 **Suggest features** and improvements
3. 📝 **Improve documentation**
4. 🔧 **Submit pull requests** with enhancements
5. ⭐ **Star the repository** to show support

## 📄 License

This project is released under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **GIMPS** (Great Internet Mersenne Prime Search) - Inspiration for this project
- **Euclid, Euler, Lucas, Lehmer** - The mathematical giants who made this possible
- **Python Community** - For the amazing language and ecosystem
- **All Contributors** - Everyone who tests exponents and helps the search!

## ⚠️ Educational Purpose

This is an **educational project** designed to teach distributed computing and number theory. For contributing to actual mathematical research and discovering officially recognized Mersenne primes, please visit [GIMPS](https://www.mersenne.org).

## 📞 Support

- 📖 [Documentation](https://yourusername.github.io/perfect-numbers-network/)
- 🐛 [Issue Tracker](https://github.com/yourusername/perfect-numbers-network/issues)
- 💬 [Discussions](https://github.com/yourusername/perfect-numbers-network/discussions)

## 🌟 Fun Facts

- Perfect numbers are incredibly rare - only 51 are known
- The largest known perfect number has **49,724,095 digits**
- All known perfect numbers are **even** (whether odd perfect numbers exist is unknown!)
- Perfect numbers have been studied for over **2,300 years**
- The ancient Greeks believed perfect numbers had mystical significance

## 🎯 Project Goals

1. **Education First**: Teach number theory and distributed computing
2. **Perfect Number Focus**: Emphasize perfect numbers, not just primes
3. **Accessibility**: Pure Python, no dependencies, easy to understand
4. **Community**: Build a community of learners and enthusiasts
5. **Open Source**: Share knowledge freely

---

**Happy Perfect Number Hunting! 🔢✨**

*"Perfect numbers, like perfect men, are very rare." - René Descartes*
