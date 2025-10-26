#!/usr/bin/env python3
"""
benchmark.py - Perfect Number Network Benchmark Tool
Test system performance and estimate completion times

Usage:
    python benchmark.py [test_size]

Examples:
    python benchmark.py          # Quick test (small exponents)
    python benchmark.py medium   # Medium test
    python benchmark.py large    # Large test (slow)
"""
import sys
import time
import math
from datetime import timedelta

class PerfectNumberBenchmark:
	def lucas_lehmer_test(self, p, verbose=False):
		"""
		Lucas-Lehmer primality test for Mersenne numbers
		If M(p) is prime, then P = 2^(p-1) × M(p) is a perfect number

		Returns: (is_prime, time_seconds, iterations_per_second)
		"""
		if p == 2:
			return True, 0.0, 0.0

		start_time = time.time()

		s = 4
		M = (1 << p) - 1
		iterations_needed = p - 2

		if verbose:
			print(f"Testing P(p={p}) via M({p}) = 2^{p} - 1")
			print(f"Iterations: {iterations_needed:,}")

		for i in range(iterations_needed):
			s = (s * s - 2) % M

			if verbose and (i + 1) % 1000 == 0:
				progress = ((i + 1) / iterations_needed) * 100
				print(f"  Progress: {progress:.1f}%", end='\r')

		elapsed = time.time() - start_time

		if verbose:
			print()

		is_prime = (s == 0)
		iter_per_sec = iterations_needed / elapsed if elapsed > 0 else 0

		return is_prime, elapsed, iter_per_sec

	def run_benchmark(self, test_level='quick'):
		"""Run benchmark suite"""
		print(f"\n╔{'═'*68}╗")
		print(f"║{'Perfect Number Network - Benchmark Tool'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		if test_level == 'quick':
			test_exponents = [127, 521, 607, 1279]
			print("Running QUICK benchmark (small exponents)...")
		elif test_level == 'medium':
			test_exponents = [127, 521, 607, 1279, 2203, 2281]
			print("Running MEDIUM benchmark (this may take a minute)...")
		elif test_level == 'large':
			test_exponents = [127, 521, 607, 1279, 2203, 2281, 3217]
			print("Running LARGE benchmark (this may take several minutes)...")
		else:
			test_exponents = [127, 521, 607]
			print("Running benchmark...")

		print("Testing your system's performance for perfect number verification.\n")

		results = []
		total_time = 0

		for i, p in enumerate(test_exponents, 1):
			print(f"Test {i}/{len(test_exponents)}: P(p={p}) via M({p}) = 2^{p} - 1")

			is_prime, elapsed, iter_per_sec = self.lucas_lehmer_test(p, verbose=True)

			total_time += elapsed

			if is_prime:
				perfect = (1 << (p - 1)) * ((1 << p) - 1)
				digits = len(str(perfect))
				result_str = f"PERFECT NUMBER ✓ ({digits:,} digits)"
			else:
				result_str = "Not perfect (composite Mersenne)"

			print(f"  Result: {result_str}")
			print(f"  Time: {elapsed:.4f} seconds")
			print(f"  Speed: {iter_per_sec:,.0f} iterations/second\n")

			results.append({
				'exponent': p,
				'is_perfect': is_prime,
				'time': elapsed,
				'iter_per_sec': iter_per_sec
			})

		print(f"{'─'*70}\n")
		print(f"📊 Benchmark Results Summary:\n")

		avg_iter_per_sec = sum(r['iter_per_sec'] for r in results) / len(results)

		print(f"Total time: {total_time:.2f} seconds")
		print(f"Average speed: {avg_iter_per_sec:,.0f} iterations/second\n")

		print(f"{'Exponent':<12} {'Time':<12} {'Speed (iter/s)':<20}")
		print(f"{'-'*50}")
		for r in results:
			print(f"{r['exponent']:<12} {r['time']:<12.4f} {r['iter_per_sec']:>18,.0f}")

		print(f"\n{'─'*70}\n")

		self.show_estimates(avg_iter_per_sec)

		return results

	def show_estimates(self, avg_iter_per_sec):
		"""Show estimated completion times for various exponents"""
		print(f"⏱️  Estimated Completion Times (based on your performance):\n")

		estimates = [
			(10000, "Small candidate"),
			(20000, "Medium candidate"),
			(44497, "Large (Known perfect #37)"),
			(86243, "Very Large (Known perfect #45)"),
			(100000, "Massive candidate"),
			(1000000, "Extreme candidate"),
		]

		print(f"{'Exponent':<12} {'Description':<25} {'Iterations':<15} {'Est. Time':<20}")
		print(f"{'-'*70}")

		for exp, size in estimates:
			iterations = exp - 2
			est_seconds = iterations / avg_iter_per_sec

			if est_seconds < 60:
				time_str = f"{est_seconds:.1f} seconds"
			elif est_seconds < 3600:
				time_str = f"{est_seconds/60:.1f} minutes"
			elif est_seconds < 86400:
				time_str = f"{est_seconds/3600:.1f} hours"
			else:
				time_str = f"{est_seconds/86400:.1f} days"

			print(f"{exp:<12} {size:<25} {iterations:<15,} {time_str:<20}")

		print(f"\n{'─'*70}\n")

		print("💡 Recommendations:\n")

		if avg_iter_per_sec > 100000:
			print("   Excellent performance! You can handle exponents up to 100,000+")
			print("   Suggested range: 10,000 - 100,000")
		elif avg_iter_per_sec > 50000:
			print("   Good performance! Focus on exponents up to 50,000")
			print("   Suggested range: 5,000 - 50,000")
		elif avg_iter_per_sec > 10000:
			print("   Moderate performance. Stick to exponents under 20,000")
			print("   Suggested range: 2,000 - 20,000")
		else:
			print("   Lower performance. Focus on smaller exponents")
			print("   Suggested range: 1,000 - 10,000")

		print()

	def test_specific_exponent(self, p):
		"""Test a specific exponent"""
		print(f"\n╔{'═'*68}╗")
		print(f"║{'Testing Specific Perfect Number Candidate'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		print(f"Testing P(p={p}) via Lucas-Lehmer test of M({p}) = 2^{p} - 1\n")

		is_prime, elapsed, iter_per_sec = self.lucas_lehmer_test(p, verbose=True)

		print(f"\n{'─'*70}\n")
		print(f"📊 Results:\n")
		print(f"Exponent: {p}")
		print(f"Mersenne number: 2^{p} - 1")

		if is_prime:
			print(f"Result: PERFECT NUMBER ✓")
			digits = int(p * math.log10(2)) + 1
			print(f"Time: {elapsed:.4f} seconds")
			print(f"Speed: {iter_per_sec:,.0f} iterations/second")

			print(f"\n✨ PERFECT NUMBER DISCOVERED!")
			print(f"P = 2^{p-1} × (2^{p} - 1)")
			print(f"Digits: ~{digits:,}")
			print(f"This number equals the sum of all its proper divisors!")

			if p <= 127:
				perfect = (1 << (p - 1)) * ((1 << p) - 1)
				perfect_str = str(perfect)
				if len(perfect_str) <= 80:
					print(f"Value: {perfect_str}")
				else:
					print(f"Value: {perfect_str[:40]}...{perfect_str[-40:]}")
		else:
			print(f"Result: Not a perfect number (M({p}) is composite)")
			print(f"Time: {elapsed:.4f} seconds")
			print(f"Speed: {iter_per_sec:,.0f} iterations/second")

		print()

def main():
	benchmark = PerfectNumberBenchmark()

	if len(sys.argv) > 1:
		arg = sys.argv[1].lower()

		if arg.isdigit():
			exponent = int(arg)
			if exponent < 2:
				print("Error: Exponent must be >= 2")
				sys.exit(1)
			benchmark.test_specific_exponent(exponent)

		elif arg in ['quick', 'medium', 'large']:
			benchmark.run_benchmark(arg)

		else:
			print("Error: Invalid argument")
			print("Usage: python benchmark.py [quick|medium|large|exponent]")
			print("Examples:")
			print("  python benchmark.py quick      # Quick benchmark")
			print("  python benchmark.py medium     # Medium benchmark")
			print("  python benchmark.py 2281       # Test specific exponent")
			sys.exit(1)
	else:
		benchmark.run_benchmark('quick')

if __name__ == '__main__':
	main()