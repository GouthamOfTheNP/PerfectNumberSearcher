#!/usr/bin/env python3
"""
monitor.py - Perfect Number Network Monitor (Flask API)
Query server status and view network statistics via REST API

Usage:
    python monitor.py [--server URL]

Example:
    python monitor.py
    python monitor.py --server http://192.168.1.100:5000
    python monitor.py --server http://example.com:5000
"""
import sys
import argparse
import requests
from datetime import datetime, timedelta


def format_number(num):
	return f"{num:,}"


def time_ago(date_string):
	try:
		date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
		now = datetime.now()
		delta = now - date

		seconds = delta.total_seconds()

		if seconds < 60:
			return "just now"
		elif seconds < 3600:
			minutes = int(seconds / 60)
			return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
		elif seconds < 86400:
			hours = int(seconds / 3600)
			return f"{hours} hour{'s' if hours != 1 else ''} ago"
		else:
			days = int(seconds / 86400)
			return f"{days} day{'s' if days != 1 else ''} ago"
	except:
		return date_string


def check_server_health(server_url):
	try:
		response = requests.get(f"{server_url}/api/health", timeout=5)
		if response.status_code == 200:
			data = response.json()
			return True, data
		return False, None
	except requests.exceptions.ConnectionError:
		return False, {'error': 'Connection refused'}
	except requests.exceptions.Timeout:
		return False, {'error': 'Connection timeout'}
	except Exception as e:
		return False, {'error': str(e)}


def display_server_stats(server_url):
	try:
		response = requests.get(f"{server_url}/api/stats/server", timeout=10)
		response.raise_for_status()
		data = response.json()

		print(f"\n╔{'═'*68}╗")
		print(f"║{'Server Statistics'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		print(f"📊 Network Overview:")
		print(f"   Candidates in Queue:    {format_number(data['work_queue_size'])}")
		print(f"   Active Searches:        {format_number(data['active_assignments'])}")
		print(f"   Total Users:            {format_number(data['total_users'])}")
		print(f"   Perfect Numbers Found:  {format_number(data['perfects_found'])}")
		print(f"   Tests Completed:        {format_number(data['tests_completed'])}")
		print(f"   Total Compute Hours:    {data['compute_hours']:.2f}")

		return True
	except Exception as e:
		print(f"\n✗ Error fetching server stats: {e}")
		return False


def display_users(server_url):
	try:
		response = requests.get(f"{server_url}/api/users", timeout=10)
		response.raise_for_status()
		data = response.json()

		print(f"\n╔{'═'*68}╗")
		print(f"║{'Top Contributors'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		if not data['users']:
			print("   No users registered yet")
			return True

		print(f"{'Rank':<6} {'Username':<20} {'Tests':<10} {'Perfects':<10} {'Last Active'}")
		print(f"{'-'*68}")

		for i, user in enumerate(data['users'][:20], 1):
			last_active = time_ago(user['last_active']) if user['last_active'] else 'Never'
			print(f"{i:<6} {user['username']:<20} {format_number(user['exponents_tested']):<10} "
			      f"{user['perfects_found']:<10} {last_active}")

		return True
	except Exception as e:
		print(f"\n✗ Error fetching users: {e}")
		return False


def display_assignments(server_url):
	try:
		response = requests.get(f"{server_url}/api/assignments", timeout=10)
		response.raise_for_status()
		data = response.json()

		print(f"\n╔{'═'*68}╗")
		print(f"║{'Active Searches'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		now = datetime.now()
		active = []
		for assignment in data['assignments']:
			try:
				expires_at = datetime.fromisoformat(assignment['expires_at'].replace('Z', '+00:00'))
				if expires_at > now:
					active.append(assignment)
			except:
				active.append(assignment)

		if not active:
			print("   No active searches")
			return True

		print(f"{'Username':<20} {'Candidate':<15} {'Progress':<12} {'Started'}")
		print(f"{'-'*68}")

		for assignment in active[:20]:
			started = time_ago(assignment['assigned_at']) if assignment['assigned_at'] else 'Unknown'
			candidate = f"P(p={format_number(assignment['exponent'])})"
			progress = f"{assignment['progress']:.1f}%"
			print(f"{assignment['username']:<20} {candidate:<15} {progress:<12} {started}")

		return True
	except Exception as e:
		print(f"\n✗ Error fetching assignments: {e}")
		return False


def display_perfects(server_url):
	try:
		response = requests.get(f"{server_url}/api/perfects", timeout=10)
		response.raise_for_status()
		data = response.json()

		print(f"\n╔{'═'*68}╗")
		print(f"║{'Perfect Number Discoveries'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		if not data['perfects']:
			print("   No perfect numbers discovered yet. Keep searching!")
			return True

		for perfect in data['perfects']:
			print(f"✨ Perfect Number P(p={format_number(perfect['exponent'])})")
			print(f"   Formula: 2^{perfect['exponent']-1} × (2^{perfect['exponent']} - 1)")
			print(f"   Digits: {format_number(perfect['digit_count'])}")
			print(f"   Discovered by: {perfect['username']}")

			try:
				disc_date = datetime.fromisoformat(perfect['discovered_at'].replace('Z', '+00:00'))
				date_str = disc_date.strftime("%Y-%m-%d %H:%M")
				print(f"   Date: {date_str}")
			except:
				print(f"   Date: {perfect['discovered_at'][:19]}")

			value = perfect['perfect_number']
			if len(value) <= 80:
				print(f"   Value: {value}")
			else:
				print(f"   Value: {value[:40]}...{value[-40:]}")
			print()

		return True
	except Exception as e:
		print(f"\n✗ Error fetching perfects: {e}")
		return False


def display_recent_results(server_url):
	try:
		response = requests.get(f"{server_url}/api/results", timeout=10)
		response.raise_for_status()
		data = response.json()

		print(f"\n╔{'═'*68}╗")
		print(f"║{'Recent Results'.center(68)}║")
		print(f"╚{'═'*68}╝\n")

		if not data['results']:
			print("   No results yet")
			return True

		print(f"{'Candidate':<15} {'Result':<15} {'Digits':<12} {'User':<15} {'Time'}")
		print(f"{'-'*68}")

		for result in data['results'][:20]:
			candidate = f"P(p={format_number(result['exponent'])})"
			result_str = "PERFECT ✓" if result['is_perfect'] else "Not Perfect"
			digits = format_number(result['digit_count']) if result['digit_count'] > 0 else "-"
			time_str = f"{result['time_seconds']:.2f}s"

			print(f"{candidate:<15} {result_str:<15} {digits:<12} "
			      f"{result['username']:<15} {time_str}")

		return True
	except Exception as e:
		print(f"\n✗ Error fetching results: {e}")
		return False


def main():
	parser = argparse.ArgumentParser(description='Perfect Number Network Monitor')
	parser.add_argument('--server', default='http://localhost:5000',
	                    help='Server URL (default: http://localhost:5000)')

	args = parser.parse_args()
	server_url = args.server.rstrip('/')

	print(f"\n╔{'═'*68}╗")
	print(f"║{'Perfect Number Network - Monitor'.center(68)}║")
	print(f"╚{'═'*68}╝")
	print(f"\nServer: {server_url}")
	print(f"Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

	print(f"\n{'─'*70}")
	print("Checking server health...")

	online, health_data = check_server_health(server_url)

	if online:
		print(f"✓ Server is ONLINE")
		if health_data:
			gmpy2_status = "Available" if health_data.get('gmpy2_available') else "Not Available"
			print(f"  gmpy2: {gmpy2_status}")
	else:
		print(f"✗ Server is OFFLINE")
		if health_data:
			print(f"  Error: {health_data.get('error', 'Unknown error')}")
		print("\nCannot retrieve network statistics.")
		sys.exit(1)

	print(f"\n{'─'*70}")

	success = True
	success &= display_server_stats(server_url)
	success &= display_perfects(server_url)
	success &= display_assignments(server_url)
	success &= display_users(server_url)
	success &= display_recent_results(server_url)

	print(f"\n{'─'*70}\n")

	if not success:
		print("⚠️  Some data could not be retrieved. Check server connection.")
		sys.exit(1)


if __name__ == '__main__':
	main()
