#!/usr/bin/env python3
"""
admin.py - Perfect Number Network Administration Tool (Flask API)
Manage the database directly - bypasses API for admin tasks

Usage:
    python admin.py [command] [options]

Commands:
    add-work      Add exponents to work queue
    reset         Reset expired assignments
    clear-user    Clear a user's assignments
    add-range     Add a range of exponents
    export        Export results to CSV
    stats         Show detailed statistics
    vacuum        Optimize database
    create-key    Create API key for existing user

Examples:
    python admin.py add-work 521 607 1279
    python admin.py add-range 10000 20000
    python admin.py reset
    python admin.py export results.csv
    python admin.py create-key username
"""
import sqlite3
import sys
import csv
import secrets
import argparse
from datetime import datetime, timedelta

try:
	import gmpy2
	GMPY2_AVAILABLE = True
except ImportError:
	GMPY2_AVAILABLE = False


class PerfectNetAdmin:
	def __init__(self, db_file='perfectnet.db'):
		self.db_file = db_file

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

	def add_work(self, exponents, priority=100):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		added = 0
		skipped = 0

		for exp in exponents:
			try:
				cursor.execute('SELECT exponent FROM work_queue WHERE exponent = ?', (exp,))
				if cursor.fetchone():
					print(f"  Skip: p={exp} (already in queue)")
					skipped += 1
					continue

				cursor.execute('SELECT exponent FROM results WHERE exponent = ?', (exp,))
				if cursor.fetchone():
					print(f"  Skip: p={exp} (already tested)")
					skipped += 1
					continue

				cursor.execute('SELECT exponent FROM assignments WHERE exponent = ?', (exp,))
				if cursor.fetchone():
					print(f"  Skip: p={exp} (currently assigned)")
					skipped += 1
					continue

				cursor.execute('''
                               INSERT INTO work_queue (exponent, priority, added_at)
                               VALUES (?, ?, ?)
				               ''', (exp, priority, datetime.now().isoformat()))

				print(f"  Added: p={exp}")
				added += 1

			except Exception as e:
				print(f"  Error adding {exp}: {e}")

		conn.commit()
		conn.close()

		print(f"\n✓ Added {added} candidates, skipped {skipped}")
		return added

	def add_range(self, start, end, priority=100):
		print(f"Adding prime exponents from {start} to {end}...")

		exponents = [p for p in range(start, end + 1) if self.is_prime(p)]

		print(f"Found {len(exponents)} prime exponents in range")

		return self.add_work(exponents, priority)

	def reset_expired(self):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		now = datetime.now().isoformat()

		cursor.execute('''
                       SELECT exponent, username, assigned_at
                       FROM assignments
                       WHERE status = 'assigned' AND expires_at < ?
		               ''', (now,))

		expired = cursor.fetchall()

		if not expired:
			print("No expired assignments found")
			conn.close()
			return 0

		print(f"Found {len(expired)} expired assignments:\n")

		for exponent, username, assigned_at in expired:
			cursor.execute('''
                           INSERT OR IGNORE INTO work_queue (exponent, priority, added_at)
                VALUES (?, ?, ?)
			               ''', (exponent, 150, now))

			cursor.execute('DELETE FROM assignments WHERE exponent = ?', (exponent,))

			print(f"  Reset: P(p={exponent}) from {username} (assigned {assigned_at})")

		conn.commit()
		conn.close()

		print(f"\n✓ Reset {len(expired)} assignments")
		return len(expired)

	def clear_user_assignments(self, username):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT exponent FROM assignments
                       WHERE username = ? AND status = 'assigned'
		               ''', (username,))

		assignments = cursor.fetchall()

		if not assignments:
			print(f"No active assignments for user: {username}")
			conn.close()
			return 0

		print(f"Clearing {len(assignments)} assignments for {username}:\n")

		for (exponent,) in assignments:
			cursor.execute('''
                           INSERT OR IGNORE INTO work_queue (exponent, priority, added_at)
                VALUES (?, ?, ?)
			               ''', (exponent, 150, datetime.now().isoformat()))

			print(f"  Cleared: P(p={exponent})")

		cursor.execute('DELETE FROM assignments WHERE username = ? AND status = "assigned"', (username,))

		conn.commit()
		conn.close()

		print(f"\n✓ Cleared {len(assignments)} assignments from {username}")
		return len(assignments)

	def create_api_key(self, username):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		cursor.execute('SELECT username, api_key FROM users WHERE username = ?', (username,))
		result = cursor.fetchone()

		if not result:
			print(f"Error: User '{username}' not found")
			print("User must register via the API first")
			conn.close()
			return None

		api_key = secrets.token_urlsafe(32)

		cursor.execute('UPDATE users SET api_key = ? WHERE username = ?', (api_key, username))
		conn.commit()
		conn.close()

		print(f"\n✓ API Key for user '{username}':")
		print(f"  {api_key}")
		print(f"\nSave this key - it won't be shown again!")

		return api_key

	def list_users(self):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT username, api_key, exponents_tested, perfect_numbers_found, created_at
                       FROM users
                       ORDER BY created_at DESC
		               ''')

		users = cursor.fetchall()
		conn.close()

		if not users:
			print("No users registered")
			return

		print(f"\n{'Username':<20} {'Tests':<8} {'Perfects':<10} {'Created':<20} {'API Key (first 16 chars)'}")
		print(f"{'-'*90}")

		for username, api_key, tests, perfects, created in users:
			created_date = created.split('T')[0] if created else 'Unknown'
			key_preview = api_key[:16] + '...' if api_key else 'None'
			print(f"{username:<20} {tests:<8} {perfects:<10} {created_date:<20} {key_preview}")

	def export_results(self, filename):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT exponent, username, is_perfect, perfect_number, digit_count,
                              discovered_at, time_seconds
                       FROM results
                       ORDER BY discovered_at
		               ''')

		with open(filename, 'w', newline='') as f:
			writer = csv.writer(f)
			writer.writerow(['Exponent', 'Username', 'Is Perfect', 'Perfect Number', 'Digit Count',
			                 'Discovered At', 'Time (seconds)'])

			count = 0
			for row in cursor:
				writer.writerow(row)
				count += 1

		conn.close()

		print(f"✓ Exported {count} results to {filename}")
		return count

	def show_stats(self):
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		print(f"\n╔{'═'*68}╗")
		print(f"║{'Perfect Number Network - Statistics'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		cursor.execute('SELECT COUNT(*) FROM users')
		total_users = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM work_queue')
		queue_size = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM assignments WHERE status = "assigned"')
		active_assignments = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM results')
		total_tests = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM results WHERE is_perfect = 1')
		total_perfects = cursor.fetchone()[0]

		cursor.execute('SELECT SUM(time_seconds) FROM results')
		total_seconds = cursor.fetchone()[0] or 0

		print(f"📊 Overall Statistics:")
		print(f"   Total users:          {total_users:,}")
		print(f"   Work queue size:      {queue_size:,}")
		print(f"   Active assignments:   {active_assignments:,}")
		print(f"   Tests completed:      {total_tests:,}")
		print(f"   Perfect numbers:      {total_perfects:,}")
		print(f"   Total compute time:   {total_seconds/3600:.2f} hours")

		if queue_size > 0:
			cursor.execute('''
                           SELECT MIN(exponent), MAX(exponent)
                           FROM work_queue
			               ''')
			min_exp, max_exp = cursor.fetchone()

			print(f"\n📋 Work Queue:")
			print(f"   Exponent range:       {min_exp:,} to {max_exp:,}")
			print(f"   Next 10 candidates:   ", end='')

			cursor.execute('''
                           SELECT exponent FROM work_queue
                           ORDER BY priority DESC, exponent ASC
                               LIMIT 10
			               ''')
			exponents = [str(row[0]) for row in cursor.fetchall()]
			print(', '.join(exponents))

		if active_assignments > 0:
			print(f"\n⚙️ Active Assignments:")
			cursor.execute('''
                           SELECT username, exponent, progress, assigned_at
                           FROM assignments
                           WHERE status = 'assigned'
                           ORDER BY assigned_at DESC
                               LIMIT 10
			               ''')

			for username, exponent, progress, assigned_at in cursor.fetchall():
				try:
					assigned_time = datetime.fromisoformat(assigned_at)
					elapsed = datetime.now() - assigned_time
					hours = elapsed.total_seconds() / 3600
					print(f"   {username:20} P(p={exponent:8,}) {progress:5.1f}% ({hours:.1f}h)")
				except:
					print(f"   {username:20} P(p={exponent:8,}) {progress:5.1f}%")

		print(f"\n🏆 Top 10 Contributors:")
		cursor.execute('''
                       SELECT username, exponents_tested, perfect_numbers_found
                       FROM users
                       ORDER BY exponents_tested DESC
                           LIMIT 10
		               ''')

		print(f"   {'Rank':<6} {'Username':<20} {'Tests':<8} {'Perfects':<10}")
		print(f"   {'-'*50}")

		for i, (username, tests, perfects) in enumerate(cursor.fetchall(), 1):
			print(f"   {i:<6} {username:<20} {tests:<8} {perfects:<10}")

		cursor.execute('''
                       SELECT exponent, username, discovered_at, digit_count
                       FROM results
                       WHERE is_perfect = 1
                       ORDER BY discovered_at DESC
                           LIMIT 5
		               ''')

		perfects = cursor.fetchall()
		if perfects:
			print(f"\n✨ Recent Perfect Number Discoveries:")
			for exponent, username, discovered_at, digits in perfects:
				date_str = discovered_at.split('T')[0]
				print(f"   P(p={exponent:,}) by {username} on {date_str} ({digits:,} digits)")

		now = datetime.now().isoformat()
		cursor.execute('''
                       SELECT COUNT(*) FROM assignments
                       WHERE status = 'assigned' AND expires_at < ?
		               ''', (now,))

		expired_count = cursor.fetchone()[0]
		if expired_count > 0:
			print(f"\n⚠️  Warning: {expired_count} expired assignments need reset")
			print(f"   Run: python admin.py reset")

		conn.close()
		print()

	def vacuum(self):
		print("Optimizing database...")

		conn = sqlite3.connect(self.db_file)
		conn.execute('VACUUM')
		conn.execute('ANALYZE')
		conn.close()

		print("✓ Database optimized")


def main():
	parser = argparse.ArgumentParser(
		description='Perfect Number Network Administration Tool',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog='''
Commands:
  add-work      Add specific exponents to work queue
  add-range     Add range of prime exponents to queue
  reset         Reset expired assignments to queue
  clear-user    Clear assignments for a specific user
  create-key    Create/regenerate API key for user
  list-users    List all registered users
  export        Export results to CSV file
  stats         Show detailed network statistics
  vacuum        Optimize database

Examples:
  python admin.py add-work 521 607 1279
  python admin.py add-range 10000 20000
  python admin.py reset
  python admin.py clear-user alice
  python admin.py create-key alice
  python admin.py export results.csv
  python admin.py stats
        '''
	)

	parser.add_argument('command', help='Command to execute')
	parser.add_argument('args', nargs='*', help='Command arguments')
	parser.add_argument('--db', default='perfectnet.db', help='Database file')

	args = parser.parse_args()

	admin = PerfectNetAdmin(args.db)
	command = args.command.lower()

	try:
		if command == 'add-work':
			if not args.args:
				print("Error: Specify exponents to add")
				print("Example: python admin.py add-work 521 607 1279")
				sys.exit(1)

			exponents = [int(arg) for arg in args.args]
			admin.add_work(exponents)

		elif command == 'add-range':
			if len(args.args) < 2:
				print("Error: Specify start and end of range")
				print("Example: python admin.py add-range 10000 20000")
				sys.exit(1)

			start = int(args.args[0])
			end = int(args.args[1])
			admin.add_range(start, end)

		elif command == 'reset':
			admin.reset_expired()

		elif command == 'clear-user':
			if not args.args:
				print("Error: Specify username")
				print("Example: python admin.py clear-user alice")
				sys.exit(1)

			username = args.args[0]
			admin.clear_user_assignments(username)

		elif command == 'create-key':
			if not args.args:
				print("Error: Specify username")
				print("Example: python admin.py create-key alice")
				sys.exit(1)

			username = args.args[0]
			admin.create_api_key(username)

		elif command == 'list-users':
			admin.list_users()

		elif command == 'export':
			if not args.args:
				print("Error: Specify output filename")
				print("Example: python admin.py export results.csv")
				sys.exit(1)

			filename = args.args[0]
			admin.export_results(filename)

		elif command == 'stats':
			admin.show_stats()

		elif command == 'vacuum':
			admin.vacuum()

		else:
			print(f"Unknown command: {command}")
			print("Run 'python admin.py --help' for usage")
			sys.exit(1)

	except Exception as e:
		print(f"Error: {e}")
		sys.exit(1)


if __name__ == '__main__':
	main()
