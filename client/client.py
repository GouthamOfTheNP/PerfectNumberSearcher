#!/usr/bin/env python3
"""
client.py - Perfect Number Network Client (HTTP REST API)
Distributed search for perfect numbers via Mersenne primes

Usage:
    python client.py [--server URL] [--username USERNAME]

Examples:
    python client.py
    python client.py --server http://192.168.1.100:5000
    python client.py --server http://example.com:5000 --username alice

Requirements:
    pip install requests gmpy2
"""
import sys
import time
import pickle
import argparse
import requests
from datetime import datetime
from pathlib import Path

try:
	import gmpy2
	from gmpy2 import mpz
	GMPY2_AVAILABLE = True
except ImportError:
	print("⚠️  Warning: gmpy2 not installed. Install with: pip install gmpy2")
	print("⚠️  Falling back to slower Python integers\n")
	GMPY2_AVAILABLE = False
	mpz = int

sys.set_int_max_str_digits(0)


class PerfectNumberClient:
	def __init__(self, server_url='http://localhost:5000', username=None):
		self.server_url = server_url.rstrip('/')
		self.username = username
		self.api_key = None
		self.session = requests.Session()
		self.checkpoint_file = Path(f'checkpoint_{username}.dat')
		self.current_assignment = None

	def register(self):
		try:
			response = self.session.get(f'{self.server_url}/api/health', timeout=5)
			response.raise_for_status()

			response = self.session.post(
				f'{self.server_url}/api/register',
				json={'username': self.username},
				timeout=10
			)
			response.raise_for_status()

			data = response.json()
			self.api_key = data['api_key']

			self.session.headers.update({'X-API-Key': self.api_key})

			print(f"✓ Connected to server at {self.server_url}")
			print(f"✓ Registered as: {self.username}")

			if GMPY2_AVAILABLE:
				print(f"✓ Using gmpy2 v{gmpy2.version()} for fast arithmetic\n")
			else:
				print(f"⚠️  Using Python integers (slower)\n")

			self._save_api_key()

			return True

		except requests.exceptions.ConnectionError:
			print(f"✗ Error: Could not connect to server at {self.server_url}")
			print("  Make sure the server is running and URL is correct!")
			return False
		except requests.exceptions.Timeout:
			print(f"✗ Error: Connection to server timed out")
			return False
		except Exception as e:
			print(f"✗ Connection error: {e}")
			return False

	def _save_api_key(self):
		try:
			key_file = Path(f'.api_key_{self.username}')
			key_file.write_text(self.api_key)
		except:
			pass

	def _load_api_key(self):
		try:
			key_file = Path(f'.api_key_{self.username}')
			if key_file.exists():
				self.api_key = key_file.read_text().strip()
				self.session.headers.update({'X-API-Key': self.api_key})
				return True
		except:
			pass
		return False

	def get_assignment(self):
		try:
			response = self.session.get(
				f'{self.server_url}/api/assignment',
				timeout=10
			)

			if response.status_code == 404:
				print("ℹ No work available from server. Waiting...")
				return False

			response.raise_for_status()
			data = response.json()

			self.current_assignment = {
				'exponent': data['exponent'],
				'expires_at': data['expires_at'],
				'hours_allowed': data['hours_allowed'],
				'perfect_number': data['candidate_perfect_number'],
				'digit_count': data['digit_count']
			}

			print(f"╔{'═' * 68}╗")
			print(f"║  New Perfect Number Candidate Assignment{' ' * 25}║")
			print(f"╚{'═' * 68}╝")
			print(f"Candidate: P = 2^{data['exponent'] - 1} × (2^{data['exponent']} - 1)")
			print(f"Exponent p = {data['exponent']}")
			print(f"Digits: {data['digit_count']:,}")
			print(f"Time allowed: {data['hours_allowed']} hours")
			print(f"Expires: {data['expires_at']}")
			print(f"\nWill verify p is prime before running Lucas-Lehmer test...")
			print()

			return True

		except requests.exceptions.RequestException as e:
			print(f"✗ Error getting assignment: {e}")
			return False

	def report_progress(self, exponent, progress):
		try:
			response = self.session.post(
				f'{self.server_url}/api/progress',
				json={
					'exponent': exponent,
					'progress': progress
				},
				timeout=5
			)
			return response.status_code == 200
		except:
			return False

	def submit_perfect_number(self, exponent, perfect_number, digit_count, time_seconds):
		try:
			response = self.session.post(
				f'{self.server_url}/api/submit',
				json={
					'exponent': exponent,
					'perfect_number': perfect_number,
					'digit_count': digit_count,
					'time_seconds': time_seconds
				},
				timeout=30
			)
			response.raise_for_status()

			data = response.json()

			if data.get('success'):
				print(f"\n{'=' * 70}")
				print(f"🎉 PERFECT NUMBER DISCOVERED! 🎉")
				print(f"P = 2^{exponent - 1} × (2^{exponent} - 1)")
				print(f"Digits: {digit_count:,}")
				print(f"Value: {perfect_number[:60]}...")
				print(f"\n✓ This equals the sum of all its proper divisors!")
				print(f"(Verified via Mersenne prime M({exponent}) = 2^{exponent} - 1)")
				print(f"{'=' * 70}\n")
				return True
			else:
				print(f"✗ Error submitting result: {data.get('error', 'Unknown')}")
				return False

		except Exception as e:
			print(f"✗ Error submitting result: {e}")
			return False

	def save_checkpoint(self, exponent, iteration, s_value):
		s_int = int(s_value) if GMPY2_AVAILABLE else s_value

		checkpoint = {
			'exponent': exponent,
			'iteration': iteration,
			's': s_int,
			'timestamp': datetime.now().isoformat()
		}

		try:
			with open(self.checkpoint_file, 'wb') as f:
				pickle.dump(checkpoint, f)
		except Exception as e:
			print(f"⚠️  Warning: Could not save checkpoint: {e}")

	def load_checkpoint(self, exponent):
		if not self.checkpoint_file.exists():
			return None

		try:
			with open(self.checkpoint_file, 'rb') as f:
				checkpoint = pickle.load(f)

			if checkpoint['exponent'] == exponent:
				print(f"✓ Resuming from iteration {checkpoint['iteration']}")
				if GMPY2_AVAILABLE:
					checkpoint['s'] = mpz(checkpoint['s'])
				return checkpoint
			else:
				return None

		except Exception as e:
			print(f"⚠️  Warning: Could not load checkpoint: {e}")
			return None

	def is_prime(self, n):
		if n < 2:
			return False
		if n == 2:
			return True
		if n % 2 == 0:
			return False

		if GMPY2_AVAILABLE:
			return gmpy2.is_prime(n)
		else:
			if n < 9:
				return n in (2, 3, 5, 7)
			if n % 3 == 0:
				return False

			limit = int(n ** 0.5) + 1
			for i in range(5, limit, 6):
				if n % i == 0 or n % (i + 2) == 0:
					return False
			return True

	def lucas_lehmer_test_optimized(self, p, report_interval=1000):
		if p == 2:
			return True, 0.0

		start_time = time.time()

		checkpoint = self.load_checkpoint(p)

		if checkpoint:
			s = checkpoint['s']
			start_iter = checkpoint['iteration']
		else:
			s = mpz(4)
			start_iter = 0

		if GMPY2_AVAILABLE:
			M = (mpz(1) << p) - 1
		else:
			M = (1 << p) - 1

		iterations_needed = p - 2

		print(f"Lucas-Lehmer test for M({p}) = 2^{p} - 1")
		print(f"Iterations needed: {iterations_needed:,}")
		if GMPY2_AVAILABLE:
			print(f"Using gmpy2 for fast arithmetic")
		print(f"Testing if M({p}) is prime (p={p} is prime ✓)")
		print(f"If M({p}) is prime → P = 2^{p - 1} × M({p}) is a perfect number\n")

		last_report = time.time()
		last_checkpoint = start_iter

		for i in range(start_iter, iterations_needed):
			if GMPY2_AVAILABLE:
				s = (s * s - 2) % M
			else:
				s = ((s * s) - 2) % M

			if (i + 1) % report_interval == 0:
				progress = ((i + 1) / iterations_needed) * 100
				elapsed = time.time() - start_time
				remaining = (elapsed / (i + 1 - start_iter)) * (iterations_needed - i - 1)

				print(f"Iteration {i + 1:,}/{iterations_needed:,} ({progress:.2f}%) - "
				      f"ETA: {remaining:.0f}s")

				if time.time() - last_report > 10:
					self.report_progress(p, progress)
					last_report = time.time()

			if ((i + 1) % 10000 == 0 or time.time() - start_time > last_checkpoint + 120) and i > last_checkpoint:
				self.save_checkpoint(p, i + 1, s)
				last_checkpoint = i + 1

		elapsed = time.time() - start_time
		is_prime = (s == 0)

		if self.checkpoint_file.exists():
			try:
				self.checkpoint_file.unlink()
			except:
				pass

		return is_prime, elapsed

	def get_stats(self):
		try:
			response = self.session.get(
				f'{self.server_url}/api/stats/user',
				timeout=5
			)
			response.raise_for_status()

			data = response.json()

			print(f"\n{'=' * 60}")
			print(f"User Statistics: {self.username}")
			print(f"{'=' * 60}")
			print(f"GHz-days: {data['ghz_days']:.2f}")
			print(f"Exponents tested: {data['exponents_tested']}")
			print(f"Perfect numbers found: {data['perfect_numbers_found']}")
			print(f"{'=' * 60}\n")
		except:
			pass

	def run(self):
		if not self._load_api_key():
			if not self.register():
				return
		else:
			print(f"✓ Using saved API key for {self.username}")
			print(f"✓ Connected to server at {self.server_url}\n")

		try:
			print(f"╔{'═' * 68}╗")
			print(f"║  Perfect Number Network Client{' ' * 35}║")
			print(f"║  Searching for perfect numbers via Euclid-Euler theorem{' ' * 10}║")
			print(f"╚{'═' * 68}╝")
			print(f"User: {self.username}")
			print(f"Press Ctrl+C to stop\n")

			while True:
				if not self.get_assignment():
					time.sleep(30)
					continue

				exponent = self.current_assignment['exponent']

				try:
					print(f"Checking if exponent p={exponent} is prime...")
					if not self.is_prime(exponent):
						print(f"✗ Exponent p={exponent} is composite")
						print(f"   M({exponent}) = 2^{exponent} - 1 cannot be prime")
						print(f"   Skipping Lucas-Lehmer test\n")
						continue

					print(f"✓ Exponent p={exponent} is prime\n")

					is_prime, time_taken = self.lucas_lehmer_test_optimized(exponent)

					print(f"\n✓ Test completed in {time_taken:.2f} seconds")

					if is_prime:
						if GMPY2_AVAILABLE:
							perfect_number = str(mpz(2) ** (exponent - 1) * (mpz(2) ** exponent - 1))
						else:
							perfect_number = str((2 ** (exponent - 1)) * ((2 ** exponent) - 1))

						digit_count = len(perfect_number)

						self.submit_perfect_number(exponent, perfect_number, digit_count, time_taken)
					else:
						print(f"Candidate P(p={exponent}) is not perfect")
						print(f"(M({exponent}) = 2^{exponent} - 1 is composite)\n")

				except KeyboardInterrupt:
					print("\n\n⚠️  Test interrupted - saving checkpoint...")
					raise

				self.current_assignment = None

		except KeyboardInterrupt:
			print("\n\n⚠️  Stopping client...")

		except Exception as e:
			print(f"\n✗ Error: {e}")


def main():
	parser = argparse.ArgumentParser(description='Perfect Number Network Client')
	parser.add_argument('--server', default='http://localhost:5000',
	                    help='Server URL (default: http://localhost:5000)')
	parser.add_argument('--username', help='Username for authentication')

	args = parser.parse_args()

	print("╔═══════════════════════════════════════════════════════════╗")
	print("║  Perfect Number Network - Distributed Search Client      ║")
	print("║  Finding perfect numbers via the Euclid-Euler theorem    ║")
	print("╚═══════════════════════════════════════════════════════════╝\n")

	username = args.username
	if not username:
		username = input("Enter username: ").strip()

	if not username or len(username) < 3:
		print("✗ Username must be at least 3 characters. Exiting.")
		sys.exit(1)

	print(f"\nConnecting to {args.server}...\n")

	client = PerfectNumberClient(args.server, username)
	client.run()


if __name__ == '__main__':
	main()
