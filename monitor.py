#!/usr/bin/env python3
"""
monitor.py - Perfect Number Network Monitor
Query server status and view network statistics

Usage:
    python monitor.py [server_host] [server_port]

Example:
    python monitor.py localhost 5555
"""
import socket
import json
import sys
import sqlite3
from datetime import datetime, timedelta

def query_server_status(host, port):
	"""Query server for current status via network"""
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((host, port))

		request = {'type': 'register', 'username': 'monitor'}
		sock.send(json.dumps(request).encode('utf-8'))
		sock.recv(8192)

		request = {'type': 'server_status'}
		sock.send(json.dumps(request).encode('utf-8'))
		data = sock.recv(8192).decode('utf-8')
		response = json.loads(data)

		request = {'type': 'disconnect'}
		sock.send(json.dumps(request).encode('utf-8'))
		sock.close()

		return response

	except Exception as e:
		print(f"Error querying server: {e}")
		return None

def display_server_status(status):
	"""Display server status information"""
	if not status or status.get('type') != 'server_status':
		print("Unable to get server status")
		return

	print(f"\n╔{'═'*68}╗")
	print(f"║{'Perfect Number Network - Server Status'.center(68)}║")
	print(f"╚{'═'*68}╝\n")

	print(f"📊 Network Statistics:")
	print(f"   Candidates in Queue:    {status['work_queue_size']:,}")
	print(f"   Active Searches:        {status['active_assignments']:,}")
	print(f"   Connected Clients:      {status['clients_connected']:,}")
	print(f"   Active Users (7d):      {status['active_users_7d']:,}")
	print(f"   Perfect Numbers Found:  {status['perfect_numbers_found']:,}")

def display_database_stats(db_file='perfectnet.db'):
	"""Display detailed statistics from database"""
	try:
		conn = sqlite3.connect(db_file)
		cursor = conn.cursor()

		print(f"\n╔{'═'*68}╗")
		print(f"║{'Detailed Statistics (from database)'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		print("🏆 Top Contributors:")
		cursor.execute('''
                       SELECT username, exponents_tested, perfect_numbers_found, total_ghz_days
                       FROM users
                       ORDER BY exponents_tested DESC
                           LIMIT 10
		               ''')

		rows = cursor.fetchall()
		if rows:
			print(f"{'Rank':<6} {'Username':<20} {'Tested':<10} {'Perfects':<10} {'GHz-days':<12}")
			print(f"{'-'*68}")
			for i, (username, tested, perfects, ghz_days) in enumerate(rows, 1):
				print(f"{i:<6} {username:<20} {tested:<10} {perfects:<10} {ghz_days:<12.2f}")
		else:
			print("   No users yet")

		print(f"\n📅 Recent Activity:")
		cursor.execute('''
                       SELECT username, last_active
                       FROM users
                       ORDER BY last_active DESC
                           LIMIT 5
		               ''')

		rows = cursor.fetchall()
		if rows:
			for username, last_active in rows:
				try:
					last_time = datetime.fromisoformat(last_active)
					time_ago = datetime.now() - last_time

					if time_ago < timedelta(minutes=1):
						time_str = "just now"
					elif time_ago < timedelta(hours=1):
						time_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
					elif time_ago < timedelta(days=1):
						time_str = f"{int(time_ago.total_seconds() / 3600)} hours ago"
					else:
						time_str = f"{time_ago.days} days ago"

					print(f"   {username:<20} {time_str}")
				except:
					print(f"   {username:<20} {last_active}")

		print(f"\n⚙️  Active Searches:")
		cursor.execute('''
                       SELECT username, exponent, progress, assigned_at
                       FROM assignments
                       WHERE status = 'assigned'
                       ORDER BY exponent
		               ''')

		rows = cursor.fetchall()
		if rows:
			print(f"{'Username':<20} {'Candidate':<15} {'Progress':<12} {'Assigned':<20}")
			print(f"{'-'*68}")
			for username, exponent, progress, assigned_at in rows:
				try:
					assigned_time = datetime.fromisoformat(assigned_at)
					time_str = assigned_time.strftime("%Y-%m-%d %H:%M")
				except:
					time_str = assigned_at[:19]

				print(f"{username:<20} P(p={exponent}){' '*(11-len(str(exponent)))} {progress:>10.1f}% {time_str:<20}")
		else:
			print("   No active searches")

		print(f"\n✨ Discovered Perfect Numbers:")
		cursor.execute('''
                       SELECT exponent, username, discovered_at, perfect_number, digit_count
                       FROM results
                       WHERE is_perfect = 1
                       ORDER BY exponent
		               ''')

		rows = cursor.fetchall()
		if rows:
			print(f"{'Exponent':<12} {'Discoverer':<20} {'Date':<20} {'Digits':<12} {'Value Preview'}")
			print(f"{'-'*68}")
			for exponent, username, discovered, perfect_num, digits in rows:
				try:
					disc_time = datetime.fromisoformat(discovered)
					time_str = disc_time.strftime("%Y-%m-%d %H:%M")
				except:
					time_str = discovered[:19]

				pn_preview = perfect_num[:25] + "..." if len(perfect_num) > 25 else perfect_num
				print(f"{exponent:<12} {username:<20} {time_str:<20} {digits:<12,} {pn_preview}")

			print(f"\n   Total perfect numbers found: {len(rows)}")
		else:
			print("   No perfect numbers discovered yet")

		print(f"\n📋 Next Candidates in Queue:")
		cursor.execute('''
                       SELECT exponent, priority
                       FROM work_queue
                       ORDER BY priority DESC, exponent ASC
                           LIMIT 10
		               ''')

		rows = cursor.fetchall()
		if rows:
			exponents = [str(exp) for exp, _ in rows]
			print(f"   {', '.join(exponents)}")

			cursor.execute('SELECT COUNT(*) FROM work_queue')
			total = cursor.fetchone()[0]
			print(f"   ({total:,} total candidates in queue)")
		else:
			print("   Work queue is empty")

		print(f"\n📈 Overall Statistics:")
		cursor.execute('SELECT COUNT(*) FROM results')
		total_tests = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM results WHERE is_perfect = 1')
		total_perfects = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(DISTINCT username) FROM users')
		total_users = cursor.fetchone()[0]

		cursor.execute('SELECT SUM(time_seconds) FROM results')
		total_time = cursor.fetchone()[0] or 0

		print(f"   Total exponents tested: {total_tests:,}")
		print(f"   Perfect numbers found:  {total_perfects:,}")
		print(f"   Total users:            {total_users:,}")
		print(f"   Total compute time:     {total_time/3600:.2f} hours")

		conn.close()

	except sqlite3.OperationalError as e:
		print(f"\n⚠️  Database not accessible: {e}")
		print("   (Server may not be running or database doesn't exist yet)")
	except Exception as e:
		print(f"\n⚠️  Error reading database: {e}")

def main():
	server_host = 'localhost'
	server_port = 5555

	if len(sys.argv) > 1:
		server_host = sys.argv[1]
	if len(sys.argv) > 2:
		server_port = int(sys.argv[2])

	print(f"\n╔{'═'*68}╗")
	print(f"║{'Perfect Number Network - Monitor'.center(68)}║")
	print(f"╚{'═'*68}╝")
	print(f"\nServer: {server_host}:{server_port}")
	print(f"Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

	print(f"\n{'─'*70}")
	print("Querying server...")
	status = query_server_status(server_host, server_port)

	if status:
		display_server_status(status)

	print(f"\n{'─'*70}")
	display_database_stats()

	print(f"\n{'─'*70}\n")

if __name__ == '__main__':
	main()