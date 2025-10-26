#!/usr/bin/env python3
"""
admin.py - Perfect Number Network Administration Tool
Manage the database, add work, reset assignments, etc.

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
    
Examples:
    python admin.py add-work 521 607 1279
    python admin.py add-range 10000 20000
    python admin.py reset
    python admin.py export results.csv
"""
import sqlite3
import sys
import csv
from datetime import datetime, timedelta

class PerfectNetAdmin:
	def __init__(self, db_file='perfectnet.db'):
		self.db_file = db_file

	def add_work(self, exponents, priority=100):
		"""Add specific exponents to work queue"""
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
		"""Add a range of exponents"""
		print(f"Adding exponents from {start} to {end}...")

		exponents = [p for p in range(start, end + 1) if self._is_prime_simple(p)]

		print(f"Found {len(exponents)} prime exponents in range")

		return self.add_work(exponents, priority)

	def _is_prime_simple(self, n):
		"""Simple primality test for adding work"""
		if n < 2:
			return False
		if n == 2:
			return True
		if n % 2 == 0:
			return False

		for i in range(3, int(n**0.5) + 1, 2):
			if n % i == 0:
				return False

		return True

	def reset_expired(self):
		"""Reset expired assignments back to work queue"""
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
		"""Clear all assignments for a specific user"""
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

	def export_results(self, filename):
		"""Export all results to CSV"""
		conn = sqlite3.connect(self.db_file)
		cursor = conn.cursor()

		cursor.execute('''
                       SELECT exponent, username, is_perfect, perfect_number, digit_count,
                              discovered_at, residue, time_seconds
                       FROM results
                       ORDER BY discovered_at
		               ''')

		with open(filename, 'w', newline='') as f:
			writer = csv.writer(f)
			writer.writerow(['Exponent', 'Username', 'Is Perfect', 'Perfect Number', 'Digit Count',
			                 'Discovered At', 'Residue', 'Time (seconds)'])

			count = 0
			for row in cursor:
				writer.writerow(row)
				count += 1

		conn.close()

		print(f"✓ Exported {count} results to {filename}")
		return count

	def show_stats(self):
		"""Show detailed statistics"""
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
			print(f"\n⚙️  Active Assignments:")
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
                       SELECT username, exponents_tested, perfect_numbers_found, total_ghz_days
                       FROM users
                       ORDER BY exponents_tested DESC
                           LIMIT 10
		               ''')

		print(f"   {'Rank':<6} {'Username':<20} {'Tests':<8} {'Perfects':<10}")
		print(f"   {'-'*50}")

		for i, (username, tests, perfects, ghz_days) in enumerate(cursor.fetchall(), 1):
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
		"""Optimize database"""
		print("Optimizing database...")

		conn = sqlite3.connect(self.db_file)
		conn.execute('VACUUM')
		conn.execute('ANALYZE')
		conn.close()

		print("✓ Database optimized")

def main():
	if len(sys.argv) < 2:
		print("Perfect Number Network - Administration Tool")
		print("\nUsage: python admin.py [command] [options]\n")
		print("Commands:")
		print("  add-work <exp1> <exp2> ...  Add specific exponents to queue")
		print("  add-range <start> <end>     Add range of prime exponents")
		print("  reset                       Reset expired assignments")
		print("  clear-user <username>       Clear user's assignments")
		print("  export <filename>           Export results to CSV")
		print("  stats                       Show detailed statistics")
		print("  vacuum                      Optimize database")
		print("\nExamples:")
		print("  python admin.py add-work 521 607 1279")
		print("  python admin.py add-range 10000 20000")
		print("  python admin.py reset")
		print("  python admin.py export results.csv")
		sys.exit(1)

	command = sys.argv[1]
	admin = PerfectNetAdmin()

	try:
		if command == 'add-work':
			if len(sys.argv) < 3:
				print("Error: Specify exponents to add")
				print("Example: python admin.py add-work 521 607 1279")
				sys.exit(1)

			exponents = [int(arg) for arg in sys.argv[2:]]
			admin.add_work(exponents)

		elif command == 'add-range':
			if len(sys.argv) < 4:
				print("Error: Specify start and end of range")
				print("Example: python admin.py add-range 10000 20000")
				sys.exit(1)

			start = int(sys.argv[2])
			end = int(sys.argv[3])
			admin.add_range(start, end)

		elif command == 'reset':
			admin.reset_expired()

		elif command == 'clear-user':
			if len(sys.argv) < 3:
				print("Error: Specify username")
				print("Example: python admin.py clear-user alice")
				sys.exit(1)

			username = sys.argv[2]
			admin.clear_user_assignments(username)

		elif command == 'export':
			if len(sys.argv) < 3:
				print("Error: Specify output filename")
				print("Example: python admin.py export results.csv")
				sys.exit(1)

			filename = sys.argv[2]
			admin.export_results(filename)

		elif command == 'stats':
			admin.show_stats()

		elif command == 'vacuum':
			admin.vacuum()

		else:
			print(f"Unknown command: {command}")
			print("Run 'python admin.py' for help")
			sys.exit(1)

	except Exception as e:
		print(f"Error: {e}")
		sys.exit(1)

if __name__ == '__main__':
	main()