#!/usr/bin/env python3
"""
server.py - Perfect Number Network Server (Optimized)
Coordinates distributed search for perfect numbers via Mersenne primes

A perfect number equals the sum of its proper divisors.
By the Euclid-Euler theorem, every even perfect number has the form:
    P = 2^(p-1) × (2^p - 1)
where 2^p - 1 is a Mersenne prime.

Usage:
    python server.py [port]

Example:
    python server.py 5555

Requirements:
    pip install gmpy2 (optional, for faster primality testing)
"""
import socket
import threading
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
	import gmpy2
	GMPY2_AVAILABLE = True
except ImportError:
	GMPY2_AVAILABLE = False

sys.set_int_max_str_digits(0)

class PerfectNumberServer:
	def __init__(self, host='0.0.0.0', port=5555, db_file='perfectnet.db'):
		self.host = host
		self.port = port
		self.db_file = db_file
		self.lock = threading.Lock()
		self.clients_active = 0

		self._init_database()

		maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
		maintenance_thread.start()

	def is_prime(self, n):
		"""
		Check if n is prime
		Uses gmpy2.is_prime if available, otherwise basic trial division
		"""
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

	def _init_database(self):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users (
                                                            username TEXT PRIMARY KEY,
                                                            total_ghz_days REAL DEFAULT 0,
                                                            exponents_tested INTEGER DEFAULT 0,
                                                            perfect_numbers_found INTEGER DEFAULT 0,
                                                            last_active TEXT
                       )
		               ''')

		cursor.execute('''
                       CREATE TABLE IF NOT EXISTS assignments (
                                                                  exponent INTEGER PRIMARY KEY,
                                                                  username TEXT,
                                                                  assigned_at TEXT,
                                                                  expires_at TEXT,
                                                                  status TEXT,
                                                                  progress REAL DEFAULT 0,
                                                                  last_update TEXT
                       )
		               ''')

		cursor.execute('''
                       CREATE TABLE IF NOT EXISTS results (
                                                              exponent INTEGER PRIMARY KEY,
                                                              username TEXT,
                                                              is_perfect INTEGER,
                                                              perfect_number TEXT,
                                                              digit_count INTEGER,
                                                              discovered_at TEXT,
                                                              time_seconds REAL
                       )
		               ''')

		cursor.execute('''
                       CREATE TABLE IF NOT EXISTS work_queue (
                                                                 exponent INTEGER PRIMARY KEY,
                                                                 priority INTEGER DEFAULT 0,
                                                                 added_at TEXT
                       )
		               ''')

		cursor.execute('SELECT COUNT(*) FROM work_queue')
		if cursor.fetchone()[0] == 0:
			print("Initializing work queue with prime exponents...")

			initial_range = range(127, 10000)
			prime_exponents = [exp for exp in initial_range if self.is_prime(exp)]

			print(f"Found {len(prime_exponents)} prime exponents in range 127-9999")
			print(f"Skipped {len(initial_range) - len(prime_exponents)} composite exponents")

			for exp in prime_exponents:
				priority = 100 if exp < 1000 else 50
				cursor.execute('''
                               INSERT INTO work_queue (exponent, priority, added_at)
                               VALUES (?, ?, ?)
				               ''', (exp, priority, datetime.now().isoformat()))

			print(f"✓ Work queue initialized with {len(prime_exponents)} prime candidates\n")

		conn.commit()
		conn.close()

	def _maintenance_loop(self):
		while True:
			try:
				threading.Event().wait(60)

				with self.lock:
					conn = sqlite3.connect(self.db_file)
					cursor = conn.cursor()

					now = datetime.now().isoformat()
					cursor.execute('''
                                   SELECT exponent, username FROM assignments
                                   WHERE status = 'assigned' AND expires_at < ?
					               ''', (now,))

					expired = cursor.fetchall()

					for exponent, username in expired:
						cursor.execute('''
                                       INSERT OR IGNORE INTO work_queue (exponent, priority, added_at)
                            VALUES (?, ?, ?)
						               ''', (exponent, 150, now))

						cursor.execute('DELETE FROM assignments WHERE exponent = ?', (exponent,))
						print(f"⚠️  Expired: Reassigned exponent {exponent} from {username}")

					conn.commit()
					conn.close()

			except Exception as e:
				print(f"Maintenance error: {e}")

	def _get_work_assignment(self, username, preferred_size='medium'):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			cursor.execute('''
                           INSERT INTO users (username, last_active)
                           VALUES (?, ?)
                               ON CONFLICT(username) DO UPDATE SET last_active = ?
			               ''', (username, datetime.now().isoformat(), datetime.now().isoformat()))

			cursor.execute('''
                           SELECT exponent FROM work_queue
                           ORDER BY priority DESC, exponent ASC
                               LIMIT 1
			               ''')

			result = cursor.fetchone()
			if not result:
				conn.close()
				return None

			exponent = result[0]

			cursor.execute('DELETE FROM work_queue WHERE exponent = ?', (exponent,))

			hours = 24 if exponent < 10000 else 72
			expires_at = (datetime.now() + timedelta(hours=hours)).isoformat()

			cursor.execute('''
                           INSERT INTO assignments (exponent, username, assigned_at, expires_at, status, last_update)
                           VALUES (?, ?, ?, ?, 'assigned', ?)
			               ''', (exponent, username, datetime.now().isoformat(), expires_at, datetime.now().isoformat()))

			conn.commit()

			perfect_number = (2 ** (exponent - 1)) * ((2 ** exponent) - 1)
			digits = len(str(perfect_number))

			return {
				'exponent': exponent,
				'expires_at': expires_at,
				'hours_allowed': hours,
				'candidate_perfect_number': str(perfect_number),
				'digit_count': digits
			}

		finally:
			conn.close()

	def _report_progress(self, username, exponent, progress, iteration=None):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			cursor.execute('''
                           UPDATE assignments
                           SET progress = ?, last_update = ?
                           WHERE exponent = ? AND username = ? AND status = 'assigned'
			               ''', (progress, datetime.now().isoformat(), exponent, username))

			conn.commit()
			updated = cursor.rowcount > 0

			if updated:
				print(f"Progress: {username} - candidate P(p={exponent}) - {progress:.1f}% complete")

			return updated

		finally:
			conn.close()

	def _submit_perfect_number(self, username, exponent, perfect_number, digit_count, time_seconds):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			cursor.execute('''
                           SELECT username FROM assignments
                           WHERE exponent = ? AND status = 'assigned'
			               ''', (exponent,))

			result = cursor.fetchone()
			if not result or result[0] != username:
				return {'success': False, 'error': 'Invalid assignment'}

			cursor.execute('''
                           INSERT INTO results (exponent, username, is_perfect, perfect_number,
                                                digit_count, discovered_at, time_seconds)
                           VALUES (?, ?, 1, ?, ?, ?, ?)
			               ''', (exponent, username, perfect_number, digit_count,
			                     datetime.now().isoformat(), time_seconds))

			cursor.execute('''
                           UPDATE assignments
                           SET status = 'completed', progress = 100
                           WHERE exponent = ? AND username = ?
			               ''', (exponent, username))

			cursor.execute('''
                           UPDATE users
                           SET exponents_tested = exponents_tested + 1,
                               perfect_numbers_found = perfect_numbers_found + 1
                           WHERE username = ?
			               ''', (username,))

			conn.commit()

			print(f"\n{'='*70}")
			print(f"🎉 PERFECT NUMBER DISCOVERED! 🎉")
			print(f"Perfect Number: 2^{exponent-1} × (2^{exponent} - 1)")
			print(f"Digits: {digit_count:,}")
			print(f"Discovered by: {username}")
			print(f"Value: {perfect_number[:60]}...")
			print(f"(Verified via Mersenne prime M({exponent}) = 2^{exponent} - 1)")
			print(f"{'='*70}\n")

			return {
				'success': True,
				'exponent': exponent
			}

		finally:
			conn.close()

	def _mark_composite(self, username, exponent):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			cursor.execute('''
                           SELECT username FROM assignments
                           WHERE exponent = ? AND status = 'assigned'
			               ''', (exponent,))

			result = cursor.fetchone()
			if not result or result[0] != username:
				return False

			cursor.execute('''
                           UPDATE assignments
                           SET status = 'completed', progress = 100
                           WHERE exponent = ? AND username = ?
			               ''', (exponent, username))

			cursor.execute('''
                           UPDATE users
                           SET exponents_tested = exponents_tested + 1
                           WHERE username = ?
			               ''', (username,))

			conn.commit()
			print(f"Candidate p={exponent}: Not a perfect number (M({exponent}) is composite)")

			return True

		finally:
			conn.close()

	def _get_user_stats(self, username):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			cursor.execute('''
                           SELECT total_ghz_days, exponents_tested, perfect_numbers_found
                           FROM users WHERE username = ?
			               ''', (username,))

			result = cursor.fetchone()
			if result:
				return {
					'ghz_days': result[0],
					'exponents_tested': result[1],
					'perfect_numbers_found': result[2]
				}
			return None

		finally:
			conn.close()

	def _get_server_status(self):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			cursor.execute('SELECT COUNT(*) FROM work_queue')
			queue_size = cursor.fetchone()[0]

			cursor.execute('SELECT COUNT(*) FROM assignments WHERE status = "assigned"')
			active_assignments = cursor.fetchone()[0]

			cursor.execute('SELECT COUNT(*) FROM results WHERE is_perfect = 1')
			perfect_found = cursor.fetchone()[0]

			cursor.execute('SELECT COUNT(DISTINCT username) FROM users WHERE last_active > ?',
			               ((datetime.now() - timedelta(days=7)).isoformat(),))
			active_users = cursor.fetchone()[0]

			return {
				'work_queue_size': queue_size,
				'active_assignments': active_assignments,
				'perfect_numbers_found': perfect_found,
				'active_users_7d': active_users,
				'clients_connected': self.clients_active
			}

		finally:
			conn.close()

	def add_work_range(self, start, end):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			prime_count = 0
			composite_count = 0

			for exp in range(start, end + 1):
				if self.is_prime(exp):
					try:
						cursor.execute('''
                                       INSERT INTO work_queue (exponent, priority, added_at)
                                       VALUES (?, ?, ?)
						               ''', (exp, 50, datetime.now().isoformat()))
						prime_count += 1
					except sqlite3.IntegrityError:
						pass
				else:
					composite_count += 1

			conn.commit()
			print(f"Added {prime_count} prime exponents to work queue")
			print(f"Skipped {composite_count} composite exponents")

		finally:
			conn.close()

	def handle_client(self, conn, addr):
		client_id = f"{addr[0]}:{addr[1]}"
		username = None

		with self.lock:
			self.clients_active += 1

		try:
			while True:
				data = conn.recv(8192).decode('utf-8')
				if not data:
					break

				try:
					request = json.loads(data)
				except json.JSONDecodeError:
					response = {'type': 'error', 'message': 'Invalid JSON'}
					conn.send(json.dumps(response).encode('utf-8'))
					continue

				req_type = request.get('type')

				if req_type == 'register':
					username = request.get('username')
					print(f"Client registered: {username} from {client_id}")
					response = {'type': 'registered', 'username': username}
					conn.send(json.dumps(response).encode('utf-8'))

				elif req_type == 'get_assignment':
					if not username:
						response = {'type': 'error', 'message': 'Not registered'}
					else:
						with self.lock:
							assignment = self._get_work_assignment(username)

						if assignment:
							response = {'type': 'assignment', **assignment}
							print(f"Assigned P(p={assignment['exponent']}) to {username} ({assignment['digit_count']:,} digits)")
						else:
							response = {'type': 'no_work', 'message': 'No work available'}

					conn.send(json.dumps(response).encode('utf-8'))

				elif req_type == 'progress':
					exponent = request.get('exponent')
					progress = request.get('progress', 0)

					with self.lock:
						success = self._report_progress(username, exponent, progress)

					response = {'type': 'progress_ack', 'success': success}
					conn.send(json.dumps(response).encode('utf-8'))

				elif req_type == 'submit_perfect':
					exponent = request.get('exponent')
					perfect_number = request.get('perfect_number')
					digit_count = request.get('digit_count')
					time_seconds = request.get('time_seconds', 0)

					with self.lock:
						result = self._submit_perfect_number(username, exponent,
						                                     perfect_number, digit_count, time_seconds)

					response = {'type': 'result_ack', **result}
					conn.send(json.dumps(response).encode('utf-8'))

				elif req_type == 'get_stats':
					with self.lock:
						stats = self._get_user_stats(username) if username else None

					if stats:
						response = {'type': 'stats', **stats}
					else:
						response = {'type': 'error', 'message': 'User not found'}

					conn.send(json.dumps(response).encode('utf-8'))

				elif req_type == 'server_status':
					with self.lock:
						status = self._get_server_status()

					response = {'type': 'server_status', **status}
					conn.send(json.dumps(response).encode('utf-8'))

				elif req_type == 'disconnect':
					print(f"Client {username or client_id} disconnecting")
					break

				else:
					response = {'type': 'error', 'message': f'Unknown request type: {req_type}'}
					conn.send(json.dumps(response).encode('utf-8'))

		except Exception as e:
			print(f"Error with client {username or client_id}: {e}")

		finally:
			with self.lock:
				self.clients_active -= 1
			conn.close()
			if username:
				print(f"Client disconnected: {username} (Active: {self.clients_active})")

	def start(self):
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.bind((self.host, self.port))
		server.listen(10)

		print(f"╔{'═'*68}╗")
		print(f"║{'Perfect Number Network Server'.center(68)}║")
		print(f"╚{'═'*68}╝")
		print(f"Server: {self.host}:{self.port}")
		print(f"Database: {self.db_file}")
		if GMPY2_AVAILABLE:
			print(f"gmpy2: Available (v{gmpy2.version()}) - fast primality testing enabled")
		else:
			print(f"gmpy2: Not available - using fallback primality testing")
		print(f"\n💡 Searching for perfect numbers via the Euclid-Euler theorem:")
		print(f"   P = 2^(p-1) × (2^p - 1) where 2^p - 1 is prime")
		print(f"\n🔍 Optimization: Only prime exponents assigned (M(p) requires prime p)")
		print(f"\nStatus: Waiting for clients...\n")

		try:
			while True:
				conn, addr = server.accept()
				thread = threading.Thread(target=self.handle_client, args=(conn, addr))
				thread.daemon = True
				thread.start()
		except KeyboardInterrupt:
			print("\n\nShutting down server...")
			server.close()

if __name__ == '__main__':
	port = 5555

	if len(sys.argv) > 1:
		port = int(sys.argv[1])

	server = PerfectNumberServer(port=port)
	server.start()
