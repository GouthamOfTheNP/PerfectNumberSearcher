#!/usr/bin/env python3
"""
client.py - Perfect Number Network Client
Distributed search for perfect numbers via Mersenne primes

Perfect numbers equal the sum of their proper divisors.
Example: 6 = 1 + 2 + 3, 28 = 1 + 2 + 4 + 7 + 14

By the Euclid-Euler theorem, every even perfect number has the form:
    P = 2^(p-1) × (2^p - 1)
where 2^p - 1 is a Mersenne prime (tested via Lucas-Lehmer)

Usage:
    python client.py [server_host] [server_port]

Examples:
    python client.py                    # Connect to localhost:5555
    python client.py 192.168.1.100      # Connect to remote server
    python client.py localhost 5555     # Specify host and port
"""
import socket
import json
import sys
import time
import pickle
from datetime import datetime
from pathlib import Path

class PerfectNumberClient:
	def __init__(self, server_host='localhost', server_port=5555, username=None):
		self.server_host = server_host
		self.server_port = server_port
		self.username = username
		self.socket = None
		self.checkpoint_file = Path(f'checkpoint_{username}.dat')
		self.current_assignment = None

	def connect(self):
		"""Connect to the server"""
		try:
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.connect((self.server_host, self.server_port))

			self.send_request({'type': 'register', 'username': self.username})

			print(f"✓ Connected to server at {self.server_host}:{self.server_port}")
			print(f"✓ Registered as: {self.username}\n")
			return True

		except ConnectionRefusedError:
			print(f"✗ Error: Could not connect to server at {self.server_host}:{self.server_port}")
			print("  Make sure the server is running!")
			return False
		except Exception as e:
			print(f"✗ Connection error: {e}")
			return False

	def send_request(self, request):
		"""Send request to server and get response"""
		if not self.socket:
			raise ConnectionError("Not connected to server")

		self.socket.send(json.dumps(request).encode('utf-8'))
		data = self.socket.recv(8192).decode('utf-8')

		if not data:
			raise ConnectionError("Server closed connection")

		return json.loads(data)

	def disconnect(self):
		"""Disconnect from server"""
		if self.socket:
			try:
				self.send_request({'type': 'disconnect'})
			except:
				pass

			try:
				self.socket.close()
			except:
				pass

			self.socket = None
			print("\n✓ Disconnected from server")

	def get_assignment(self):
		"""Request work assignment from server"""
		try:
			response = self.send_request({'type': 'get_assignment'})

			if response['type'] == 'assignment':
				self.current_assignment = {
					'exponent': response['exponent'],
					'expires_at': response['expires_at'],
					'hours_allowed': response['hours_allowed'],
					'perfect_number': response['candidate_perfect_number'],
					'digit_count': response['digit_count']
				}

				print(f"╔{'═'*68}╗")
				print(f"║  New Perfect Number Candidate Assignment{' '*25}║")
				print(f"╚{'═'*68}╝")
				print(f"Candidate: P = 2^{response['exponent']-1} × (2^{response['exponent']} - 1)")
				print(f"Digits: {response['digit_count']:,}")
				print(f"Time allowed: {response['hours_allowed']} hours")
				print(f"Expires: {response['expires_at']}")
				print(f"\nVerifying via Lucas-Lehmer test of M({response['exponent']})...")
				print()

				return True

			elif response['type'] == 'no_work':
				print("ℹ No work available from server. Waiting...")
				return False

			else:
				print(f"✗ Server error: {response.get('message', 'Unknown error')}")
				return False

		except Exception as e:
			print(f"✗ Error getting assignment: {e}")
			return False

	def report_progress(self, exponent, progress):
		"""Report progress to server"""
		try:
			response = self.send_request({
				'type': 'progress',
				'exponent': exponent,
				'progress': progress
			})
			return response.get('success', False)
		except:
			return False

	def submit_result(self, exponent, is_prime, residue, time_seconds):
		"""Submit test result to server"""
		try:
			response = self.send_request({
				'type': 'submit_result',
				'exponent': exponent,
				'is_prime': is_prime,
				'residue': residue,
				'time_seconds': time_seconds
			})

			if response.get('success'):
				print(f"\n✓ Result submitted successfully")

				if response.get('is_perfect'):
					perfect_num = response.get('perfect_number', '')
					digits = response.get('digit_count', 0)
					print(f"\n{'='*70}")
					print(f"🎉 PERFECT NUMBER DISCOVERED! 🎉")
					print(f"P = 2^{exponent-1} × (2^{exponent} - 1)")
					print(f"Digits: {digits:,}")
					print(f"Value: {perfect_num[:60]}...")
					print(f"\n✓ This equals the sum of all its proper divisors!")
					print(f"(Verified via Mersenne prime M({exponent}) = 2^{exponent} - 1)")
					print(f"{'='*70}\n")
				else:
					print(f"Candidate P(p={exponent}) is not perfect")
					print(f"(M({exponent}) = 2^{exponent} - 1 is composite)")
					print(f"Residue: {residue}\n")

				return True
			else:
				print(f"✗ Error submitting result: {response.get('error', 'Unknown')}")
				return False

		except Exception as e:
			print(f"✗ Error submitting result: {e}")
			return False

	def save_checkpoint(self, exponent, iteration, s_value):
		"""Save checkpoint to resume work later"""
		checkpoint = {
			'exponent': exponent,
			'iteration': iteration,
			's': s_value,
			'timestamp': datetime.now().isoformat()
		}

		try:
			with open(self.checkpoint_file, 'wb') as f:
				pickle.dump(checkpoint, f)
		except Exception as e:
			print(f"⚠️  Warning: Could not save checkpoint: {e}")

	def load_checkpoint(self, exponent):
		"""Load checkpoint if available for this exponent"""
		if not self.checkpoint_file.exists():
			return None

		try:
			with open(self.checkpoint_file, 'rb') as f:
				checkpoint = pickle.load(f)

			if checkpoint['exponent'] == exponent:
				print(f"✓ Resuming from iteration {checkpoint['iteration']}")
				return checkpoint
			else:
				return None

		except Exception as e:
			print(f"⚠️  Warning: Could not load checkpoint: {e}")
			return None

	def lucas_lehmer_test(self, p, report_interval=1000):
		"""
		Lucas-Lehmer primality test for Mersenne numbers
		Tests if M(p) = 2^p - 1 is prime
		If prime, then P = 2^(p-1) × M(p) is a perfect number

		Returns: (is_prime, residue, time_seconds)
		"""
		if p == 2:
			return True, "0", 0.0

		start_time = time.time()

		checkpoint = self.load_checkpoint(p)

		if checkpoint:
			s = checkpoint['s']
			start_iter = checkpoint['iteration']
		else:
			s = 4
			start_iter = 0

		M = (1 << p) - 1

		iterations_needed = p - 2

		print(f"Lucas-Lehmer test for M({p}) = 2^{p} - 1")
		print(f"Iterations needed: {iterations_needed:,}")
		print(f"If prime → P = 2^{p-1} × M({p}) is a perfect number\n")

		last_report = time.time()

		for i in range(start_iter, iterations_needed):
			s = (s * s - 2) % M

			if (i + 1) % report_interval == 0:
				progress = ((i + 1) / iterations_needed) * 100
				elapsed = time.time() - start_time
				remaining = (elapsed / (i + 1 - start_iter)) * (iterations_needed - i - 1)

				print(f"Iteration {i+1:,}/{iterations_needed:,} ({progress:.2f}%) - "
				      f"ETA: {remaining:.0f}s")

				if time.time() - last_report > 300:
					self.report_progress(p, progress)
					last_report = time.time()

				if (i + 1) % 10000 == 0:
					self.save_checkpoint(p, i + 1, s)

		elapsed = time.time() - start_time

		is_prime = (s == 0)
		residue = hex(s)[:20]

		# Clean up checkpoint
		if self.checkpoint_file.exists():
			try:
				self.checkpoint_file.unlink()
			except:
				pass

		return is_prime, residue, elapsed

	def run(self):
		"""Main client loop"""
		if not self.connect():
			return

		try:
			print(f"╔{'═'*68}╗")
			print(f"║  Perfect Number Network Client{' '*35}║")
			print(f"║  Searching for perfect numbers via Euclid-Euler theorem{' '*10}║")
			print(f"╚{'═'*68}╝")
			print(f"User: {self.username}")
			print(f"Press Ctrl+C to stop\n")

			while True:
				# Get work assignment
				if not self.get_assignment():
					time.sleep(30)
					continue

				exponent = self.current_assignment['exponent']

				try:
					is_prime, residue, time_taken = self.lucas_lehmer_test(exponent)

					print(f"\n✓ Test completed in {time_taken:.2f} seconds")

					self.submit_result(exponent, is_prime, residue, time_taken)

				except KeyboardInterrupt:
					print("\n\n⚠️  Test interrupted - saving checkpoint...")
					raise

				self.current_assignment = None

		except KeyboardInterrupt:
			print("\n\n⚠️  Stopping client...")

		except Exception as e:
			print(f"\n✗ Error: {e}")

		finally:
			self.disconnect()

	def get_stats(self):
		"""Get user statistics from server"""
		try:
			response = self.send_request({'type': 'get_stats'})

			if response['type'] == 'stats':
				print(f"\n{'='*60}")
				print(f"User Statistics: {self.username}")
				print(f"{'='*60}")
				print(f"GHz-days: {response['ghz_days']:.2f}")
				print(f"Exponents tested: {response['exponents_tested']}")
				print(f"Perfect numbers found: {response['perfect_numbers_found']}")
				print(f"{'='*60}\n")
		except:
			pass

if __name__ == '__main__':
	server_host = 'localhost'
	server_port = 5555

	if len(sys.argv) > 1:
		server_host = sys.argv[1]
	if len(sys.argv) > 2:
		server_port = int(sys.argv[2])

	print("╔══════════════════════════════════════════════════════════╗")
	print("║  Perfect Number Network - Distributed Search Client     ║")
	print("║  Finding perfect numbers via the Euclid-Euler theorem   ║")
	print("╚══════════════════════════════════════════════════════════╝\n")

	username = input("Enter username: ").strip()
	if not username:
		print("✗ Username cannot be empty. Exiting.")
		sys.exit(1)

	print(f"\nConnecting to {server_host}:{server_port}...\n")

	client = PerfectNumberClient(server_host, server_port, username)
	client.run()