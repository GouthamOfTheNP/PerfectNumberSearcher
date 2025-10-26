#!/usr/bin/env python3
"""
server.py - Perfect Number Network Server (Flask REST API)
Coordinates distributed search for perfect numbers via Mersenne primes

Usage:
    python server.py [--host HOST] [--port PORT] [--db DB_FILE]

Example:
    python server.py --host 0.0.0.0 --port 5000
    python server.py --host 0.0.0.0 --port 5000 --db perfectnet.db

For public access, use --host 0.0.0.0 and configure your firewall
"""
import sqlite3
import sys
import secrets
import argparse
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

try:
	import gmpy2
	GMPY2_AVAILABLE = True
except ImportError:
	GMPY2_AVAILABLE = False

sys.set_int_max_str_digits(0)

app = Flask(__name__)
CORS(app)

DB_FILE = 'perfectnet.db'
API_KEYS = {}
db_lock = threading.Lock()


def require_auth(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		api_key = request.headers.get('X-API-Key')
		if not api_key:
			return jsonify({'error': 'API key required'}), 401

		username = None
		for user, key in API_KEYS.items():
			if key == api_key:
				username = user
				break

		if not username:
			return jsonify({'error': 'Invalid API key'}), 401

		request.username = username
		return f(*args, **kwargs)

	return decorated_function


def is_prime(n):
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


def init_database():
	conn = sqlite3.connect(DB_FILE)
	cursor = conn.cursor()

	cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users (
                                                        username TEXT PRIMARY KEY,
                                                        api_key TEXT UNIQUE,
                                                        total_ghz_days REAL DEFAULT 0,
                                                        exponents_tested INTEGER DEFAULT 0,
                                                        perfect_numbers_found INTEGER DEFAULT 0,
                                                        last_active TEXT,
                                                        created_at TEXT
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
		prime_exponents = [exp for exp in initial_range if is_prime(exp)]

		print(f"Found {len(prime_exponents)} prime exponents in range 127-9999")

		for exp in prime_exponents:
			priority = 100 if exp < 1000 else 50
			cursor.execute('''
                           INSERT INTO work_queue (exponent, priority, added_at)
                           VALUES (?, ?, ?)
			               ''', (exp, priority, datetime.now().isoformat()))

		print(f"✓ Work queue initialized with {len(prime_exponents)} prime candidates\n")

	conn.commit()
	conn.close()


def maintenance_loop():
	while True:
		threading.Event().wait(60)

		try:
			with db_lock:
				conn = sqlite3.connect(DB_FILE)
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


@app.route('/api/health', methods=['GET'])
def health_check():
	return jsonify({
		'status': 'healthy',
		'timestamp': datetime.now().isoformat(),
		'gmpy2_available': GMPY2_AVAILABLE
	})


@app.route('/api/register', methods=['POST'])
def register():
	data = request.get_json()
	username = data.get('username', '').strip()

	if not username or len(username) < 3:
		return jsonify({'error': 'Username must be at least 3 characters'}), 400

	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('SELECT api_key FROM users WHERE username = ?', (username,))
		result = cursor.fetchone()

		if result:
			api_key = result[0]
			conn.close()
			return jsonify({
				'message': 'User already exists',
				'username': username,
				'api_key': api_key
			})

		api_key = secrets.token_urlsafe(32)
		cursor.execute('''
                       INSERT INTO users (username, api_key, created_at, last_active)
                       VALUES (?, ?, ?, ?)
		               ''', (username, api_key, datetime.now().isoformat(), datetime.now().isoformat()))

		conn.commit()
		conn.close()

	API_KEYS[username] = api_key

	print(f"✓ New user registered: {username}")

	return jsonify({
		'message': 'Registration successful',
		'username': username,
		'api_key': api_key
	}), 201


@app.route('/api/assignment', methods=['GET'])
@require_auth
def get_assignment():
	username = request.username

	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('''
                       UPDATE users SET last_active = ?
                       WHERE username = ?
		               ''', (datetime.now().isoformat(), username))

		cursor.execute('''
                       SELECT exponent FROM work_queue
                       ORDER BY priority DESC, exponent ASC
                           LIMIT 1
		               ''')

		result = cursor.fetchone()
		if not result:
			conn.close()
			return jsonify({'message': 'No work available'}), 404

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

		conn.close()

	print(f"✓ Assigned P(p={exponent}) to {username} ({digits:,} digits)")

	return jsonify({
		'exponent': exponent,
		'expires_at': expires_at,
		'hours_allowed': hours,
		'candidate_perfect_number': str(perfect_number),
		'digit_count': digits
	})


@app.route('/api/progress', methods=['POST'])
@require_auth
def report_progress():
	username = request.username
	data = request.get_json()

	exponent = data.get('exponent')
	progress = data.get('progress', 0)

	if not exponent:
		return jsonify({'error': 'Exponent required'}), 400

	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('''
                       UPDATE assignments
                       SET progress = ?, last_update = ?
                       WHERE exponent = ? AND username = ? AND status = 'assigned'
		               ''', (progress, datetime.now().isoformat(), exponent, username))

		success = cursor.rowcount > 0
		conn.commit()
		conn.close()

	if success:
		print(f"Progress: {username} - P(p={exponent}) - {progress:.1f}%")

	return jsonify({'success': success})


@app.route('/api/submit', methods=['POST'])
@require_auth
def submit_result():
	username = request.username
	data = request.get_json()

	exponent = data.get('exponent')
	perfect_number = data.get('perfect_number')
	digit_count = data.get('digit_count')
	time_seconds = data.get('time_seconds', 0)

	if not all([exponent, perfect_number, digit_count]):
		return jsonify({'error': 'Missing required fields'}), 400

	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT username FROM assignments
                       WHERE exponent = ? AND status = 'assigned'
		               ''', (exponent,))

		result = cursor.fetchone()
		if not result or result[0] != username:
			conn.close()
			return jsonify({'error': 'Invalid assignment'}), 403

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
		conn.close()

	print(f"\n{'='*70}")
	print(f"🎉 PERFECT NUMBER DISCOVERED! 🎉")
	print(f"Perfect Number: 2^{exponent-1} × (2^{exponent} - 1)")
	print(f"Digits: {digit_count:,}")
	print(f"Discovered by: {username}")
	print(f"Value: {perfect_number[:60]}...")
	print(f"{'='*70}\n")

	return jsonify({
		'success': True,
		'message': 'Perfect number recorded!',
		'exponent': exponent
	})


@app.route('/api/stats/server', methods=['GET'])
def server_stats():
	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('SELECT COUNT(*) FROM work_queue')
		work_queue_size = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM assignments WHERE status = "assigned"')
		active_assignments = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(DISTINCT username) FROM users')
		total_users = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM results WHERE is_perfect = 1')
		perfects_found = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM results')
		tests_completed = cursor.fetchone()[0]

		cursor.execute('SELECT SUM(time_seconds) FROM results')
		total_seconds = cursor.fetchone()[0] or 0

		conn.close()

	return jsonify({
		'work_queue_size': work_queue_size,
		'active_assignments': active_assignments,
		'total_users': total_users,
		'perfects_found': perfects_found,
		'tests_completed': tests_completed,
		'compute_hours': total_seconds / 3600
	})


@app.route('/api/stats/user', methods=['GET'])
@require_auth
def user_stats():
	username = request.username

	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT total_ghz_days, exponents_tested, perfect_numbers_found
                       FROM users WHERE username = ?
		               ''', (username,))

		result = cursor.fetchone()
		conn.close()

		if not result:
			return jsonify({'error': 'User not found'}), 404

	return jsonify({
		'username': username,
		'ghz_days': result[0],
		'exponents_tested': result[1],
		'perfect_numbers_found': result[2]
	})


@app.route('/api/users', methods=['GET'])
def list_users():
	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT username, exponents_tested, perfect_numbers_found, last_active
                       FROM users
                       ORDER BY exponents_tested DESC
                           LIMIT 20
		               ''')

		users = []
		for row in cursor.fetchall():
			users.append({
				'username': row[0],
				'exponents_tested': row[1],
				'perfects_found': row[2],
				'last_active': row[3]
			})

		conn.close()

	return jsonify({'users': users})


@app.route('/api/assignments', methods=['GET'])
def list_assignments():
	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT username, exponent, progress, assigned_at, expires_at
                       FROM assignments
                       WHERE status = 'assigned'
                       ORDER BY assigned_at DESC
		               ''')

		assignments = []
		for row in cursor.fetchall():
			assignments.append({
				'username': row[0],
				'exponent': row[1],
				'progress': row[2],
				'assigned_at': row[3],
				'expires_at': row[4]
			})

		conn.close()

	return jsonify({'assignments': assignments})


@app.route('/api/results', methods=['GET'])
def list_results():
	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT exponent, username, is_perfect, digit_count, discovered_at, time_seconds
                       FROM results
                       ORDER BY discovered_at DESC
                           LIMIT 50
		               ''')

		results = []
		for row in cursor.fetchall():
			results.append({
				'exponent': row[0],
				'username': row[1],
				'is_perfect': bool(row[2]),
				'digit_count': row[3] or 0,
				'discovered_at': row[4],
				'time_seconds': row[5]
			})

		conn.close()

	return jsonify({'results': results})


@app.route('/api/perfects', methods=['GET'])
def list_perfects():
	with db_lock:
		conn = sqlite3.connect(DB_FILE)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT exponent, username, discovered_at, perfect_number, digit_count
                       FROM results
                       WHERE is_perfect = 1
                       ORDER BY exponent
		               ''')

		perfects = []
		for row in cursor.fetchall():
			perfects.append({
				'exponent': row[0],
				'username': row[1],
				'discovered_at': row[2],
				'perfect_number': row[3],
				'digit_count': row[4]
			})

		conn.close()

	return jsonify({'perfects': perfects})


def load_api_keys():
	global API_KEYS
	conn = sqlite3.connect(DB_FILE)
	cursor = conn.cursor()

	cursor.execute('SELECT username, api_key FROM users')
	for username, api_key in cursor.fetchall():
		API_KEYS[username] = api_key

	conn.close()
	print(f"Loaded {len(API_KEYS)} API keys")


def main():
	parser = argparse.ArgumentParser(description='Perfect Number Network Server')
	parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
	parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
	parser.add_argument('--db', default='perfectnet.db', help='Database file (default: perfectnet.db)')
	parser.add_argument('--debug', action='store_true', help='Enable debug mode')

	args = parser.parse_args()

	global DB_FILE
	DB_FILE = args.db

	print(f"╔{'═'*68}╗")
	print(f"║{'Perfect Number Network Server (Flask)'.center(68)}║")
	print(f"╚{'═'*68}╝")
	print(f"Server: http://{args.host}:{args.port}")
	print(f"Database: {DB_FILE}")

	if GMPY2_AVAILABLE:
		print(f"gmpy2: Available (v{gmpy2.version()}) - fast primality testing enabled")
	else:
		print(f"gmpy2: Not available - using fallback primality testing")

	print(f"\n💡 Searching for perfect numbers via the Euclid-Euler theorem:")
	print(f"   P = 2^(p-1) × (2^p - 1) where 2^p - 1 is prime")
	print(f"\n🔒 API Authentication: API keys required for client operations")
	print(f"🌐 Public Access: Server accessible from any device on network")

	init_database()
	load_api_keys()

	maintenance_thread = threading.Thread(target=maintenance_loop, daemon=True)
	maintenance_thread.start()

	print(f"\n✓ Server ready and waiting for clients...")
	print(f"📊 Dashboard available at: http://{args.host}:{args.port + 1}\n")

	app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == '__main__':
	main()
