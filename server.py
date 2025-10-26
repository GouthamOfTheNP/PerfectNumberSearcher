#!/usr/bin/env python3
"""
server.py - Perfect Number Network Server (GIMPS-style)
Coordinates distributed search for Mersenne primes and perfect numbers

Usage:
    python server.py [port]

Example:
    python server.py 5555
"""
import socket
import threading
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

class PerfectNetworkServer:
	def __init__(self, host='0.0.0.0', port=5555, db_file='perfectnet.db'):
		self.host = host
		self.port = port
		self.db_file = db_file
		self.lock = threading.Lock()
		self.clients_active = 0

		self._init_database()

		maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
		maintenance_thread.start()

	def _init_database(self):
		"""Initialize SQLite database with required tables"""
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users (
                                                            username TEXT PRIMARY KEY,
                                                            total_ghz_days REAL DEFAULT 0,
                                                            exponents_tested INTEGER DEFAULT 0,
                                                            primes_found INTEGER DEFAULT 0,
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
                                                              is_prime INTEGER,
                                                              perfect_number TEXT,
                                                              discovered_at TEXT,
                                                              residue TEXT,
                                                              fft_length INTEGER,
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
			known_primes = [2, 3, 5, 7, 13, 17, 19, 31, 61, 89]
			initial_exponents = list(range(127, 10000))

			for exp in initial_exponents:
				cursor.execute('''
                               INSERT INTO work_queue (exponent, priority, added_at)
                               VALUES (?, ?, ?)
				               ''', (exp, 100 if exp < 1000 else 50, datetime.now().isoformat()))

		conn.commit()
		conn.close()

	def _maintenance_loop(self):
		"""Periodically check for expired assignments and reassign work"""
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
						print(f"⚠ Expired: Reassigned exponent {exponent} from {username}")

					conn.commit()
					conn.close()

			except Exception as e:
				print(f"Maintenance error: {e}")

	def _get_work_assignment(self, username, preferred_size='medium'):
		"""Assign work to a user"""
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

			return {
				'exponent': exponent,
				'expires_at': expires_at,
				'hours_allowed': hours,
				'perfect_number_if_prime': str(perfect_number)
			}

		finally:
			conn.close()

	def _report_progress(self, username, exponent, progress, iteration=None):
		"""Update progress on an assignment"""
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
				print(f"Progress: {username} - p={exponent} - {progress:.1f}% complete")

			return updated

		finally:
			conn.close()

	def _submit_result(self, username, exponent, is_prime, residue=None, time_seconds=0):
		"""Submit a completed test result"""
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

			perfect_number = None
			if is_prime:
				perfect_number = str((2 ** (exponent - 1)) * ((2 ** exponent) - 1))

			cursor.execute('''
                           INSERT INTO results (exponent, username, is_prime, perfect_number,
                                                discovered_at, residue, time_seconds)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
			               ''', (exponent, username, 1 if is_prime else 0, perfect_number,
			                     datetime.now().isoformat(), residue, time_seconds))

			cursor.execute('''
                           UPDATE assignments
                           SET status = 'completed', progress = 100
                           WHERE exponent = ? AND username = ?
			               ''', (exponent, username))

			if is_prime:
				cursor.execute('''
                               UPDATE users
                               SET exponents_tested = exponents_tested + 1,
                                   primes_found = primes_found + 1
                               WHERE username = ?
				               ''', (username,))

				print(f"\n{'='*60}")
				print(f"🎉 MERSENNE PRIME FOUND! 🎉")
				print(f"Exponent: {exponent}")
				print(f"Discovered by: {username}")
				print(f"Perfect Number: {perfect_number[:50]}...")
				print(f"{'='*60}\n")
			else:
				cursor.execute('''
                               UPDATE users
                               SET exponents_tested = exponents_tested + 1
                               WHERE username = ?
				               ''', (username,))

			conn.commit()

			return {
				'success': True,
				'is_prime': is_prime,
				'perfect_number': perfect_number,
				'exponent': exponent
			}

		finally:
			conn.close()

	def _get_user_stats(self, username):
		"""Get statistics for a user"""
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			cursor.execute('''
                           SELECT total_ghz_days, exponents_tested, primes_found
                           FROM users WHERE username = ?
			               ''', (username,))

			result = cursor.fetchone()
			if result:
				return {
					'ghz_days': result[0],
					'exponents_tested': result[1],
					'primes_found': result[2]
				}
			return None

		finally:
			conn.close()

	def _get_server_status(self):
		"""Get overall server statistics"""
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		try:
			cursor.execute('SELECT COUNT(*) FROM work_queue')
			queue_size = cursor.fetchone()[0]

			cursor.execute('SELECT COUNT(*) FROM assignments WHERE status = "assigned"')
			active_assignments = cursor.fetchone()[0]

			cursor.execute('SELECT COUNT(*) FROM results WHERE is_prime = 1')
			primes_found = cursor.fetchone()[0]

			cursor.execute('SELECT COUNT(DISTINCT username) FROM users WHERE last_active > ?',
			               ((datetime.now() - timedelta(days=7)).isoformat(),))
			active_users = cursor.fetchone()[0]

			return {
				'work_queue_size': queue_size,
				'active_assignments': active_assignments,
				'total_primes_found': primes_found,
				'active_users_7d': active_users,
				'clients_connected': self.clients_active
			}

		finally:
			conn.close()

	def handle_client(self, conn, addr):
		"""Handle client connection"""
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
							print(f"Assigned p={assignment['exponent']} to {username}")
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

				elif req_type == 'submit_result':
					exponent = request.get('exponent')
					is_prime = request.get('is_prime')
					residue = request.get('residue')
					time_seconds = request.get('time_seconds', 0)

					with self.lock:
						result = self._submit_result(username, exponent, is_prime,
						                             residue, time_seconds)

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
		"""Start the server"""
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.bind((self.host, self.port))
		server.listen(10)

		print(f"╔{'═'*60}╗")
		print(f"║  Perfect Number Network Server (GIMPS-style)             ║")
		print(f"╚{'═'*60}╝")
		print(f"Server: {self.host}:{self.port}")
		print(f"Database: {self.db_file}")
		print(f"Status: Waiting for clients...\n")

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

	server = PerfectNetworkServer(port=port)
	server.start()