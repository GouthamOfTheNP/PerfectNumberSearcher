#!/usr/bin/env python3
"""
dashboard.py - Perfect Number Network Web Dashboard (Updated)
Real-time monitoring dashboard via HTTP

Usage:
    python dashboard.py [http_port] [db_file]

Example:
    python dashboard.py 8080 perfectnet.db
"""
import http.server
import socketserver
import sqlite3
import json
import sys
import math
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

sys.set_int_max_str_digits(0)

class DashboardHandler(http.server.BaseHTTPRequestHandler):
	db_file = 'perfectnet.db'

	def log_message(self, format, *args):
		"""Suppress default logging"""
		pass

	def do_GET(self):
		"""Handle GET requests"""
		parsed_path = urlparse(self.path)
		path = parsed_path.path

		if path == '/':
			self.serve_dashboard()
		elif path == '/api/stats':
			self.serve_stats()
		elif path == '/api/users':
			self.serve_users()
		elif path == '/api/assignments':
			self.serve_assignments()
		elif path == '/api/results':
			self.serve_results()
		elif path == '/api/perfects':
			self.serve_perfects()
		else:
			self.send_error(404)

	def serve_dashboard(self):
		"""Serve the main dashboard HTML"""
		html = '''<!DOCTYPE html>
<html>
<head>
    <title>Perfect Number Network - Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            font-size: 1.1em;
            margin-bottom: 10px;
        }
        .theorem {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 0.95em;
            border-left: 4px solid #667eea;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .stat-value {
            color: #667eea;
            font-size: 2.5em;
            font-weight: bold;
        }
        .section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .section.scrollable {
            max-height: 500px;
            overflow-y: auto;
        }
        .section.scrollable .section-content {
            max-height: 400px;
            overflow-y: auto;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #667eea;
            border-bottom: 2px solid #dee2e6;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .progress-bar {
            background: #e9ecef;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }
        .progress-fill {
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
            font-weight: bold;
        }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        .badge-primary {
            background: #cfe2ff;
            color: #084298;
        }
        .badge-warning {
            background: #fff3cd;
            color: #664d03;
        }
        .perfect-discovery {
            background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        .perfect-discovery h3 {
            font-size: 1.3em;
            margin-bottom: 10px;
        }
        .perfect-discovery .formula {
            font-family: 'Courier New', monospace;
            font-size: 1.1em;
            background: rgba(255,255,255,0.2);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .refresh-info {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .mono {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .time-ago {
            color: #888;
            font-size: 0.9em;
        }
        .digit-count {
            color: #28a745;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✨ Perfect Number Network</h1>
            <p class="subtitle">Distributed Search for Perfect Numbers</p>
            <div class="theorem">
                <strong>Euclid-Euler Theorem:</strong> Every even perfect number has the form 
                <code>P = 2<sup>p-1</sup> × (2<sup>p</sup> - 1)</code> 
                where <code>2<sup>p</sup> - 1</code> is a Mersenne prime
            </div>
        </div>
        
        <div class="stats-grid" id="stats-grid">
            <div class="loading">Loading statistics...</div>
        </div>
        
        <div class="section" id="perfects-section">
            <h2>✨ Discovered Perfect Numbers</h2>
            <div id="perfects-list" class="loading">Loading discoveries...</div>
        </div>
        
        <div class="section scrollable" id="assignments-section">
            <h2>⚙️ Active Searches</h2>
            <div class="section-content" id="assignments-list">
                <div class="loading">Loading assignments...</div>
            </div>
        </div>
        
        <div class="section" id="users-section">
            <h2>🏆 Top Contributors</h2>
            <div id="users-list" class="loading">Loading users...</div>
        </div>
        
        <div class="section" id="recent-section">
            <h2>📊 Recent Results</h2>
            <div id="results-list" class="loading">Loading results...</div>
        </div>
        
        <div class="refresh-info">
            <p>Dashboard auto-refreshes every 10 seconds</p>
            <p>Last updated: <span id="last-update">--</span></p>
        </div>
    </div>
    
    <script>
        function formatNumber(num) {
            return num.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, ",");
        }
        
        function timeAgo(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const seconds = Math.floor((now - date) / 1000);
            
            if (seconds < 60) return 'just now';
            const minutes = Math.floor(seconds / 60);
            if (minutes < 60) return `${minutes}m ago`;
            const hours = Math.floor(minutes / 60);
            if (hours < 24) return `${hours}h ago`;
            const days = Math.floor(hours / 24);
            return `${days}d ago`;
        }
        
        async function loadStats() {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            const statsHtml = `
                <div class="stat-card">
                    <div class="stat-label">Candidates in Queue</div>
                    <div class="stat-value">${formatNumber(data.work_queue_size)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Active Searches</div>
                    <div class="stat-value">${formatNumber(data.active_assignments)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Users</div>
                    <div class="stat-value">${formatNumber(data.total_users)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Perfect Numbers Found</div>
                    <div class="stat-value">${formatNumber(data.perfects_found)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Tests Completed</div>
                    <div class="stat-value">${formatNumber(data.tests_completed)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Compute Hours</div>
                    <div class="stat-value">${data.compute_hours.toFixed(1)}</div>
                </div>
            `;
            
            document.getElementById('stats-grid').innerHTML = statsHtml;
        }
        
        async function loadPerfects() {
            const response = await fetch('/api/perfects');
            const data = await response.json();
            
            if (data.perfects.length === 0) {
                document.getElementById('perfects-list').innerHTML = 
                    '<p style="color: #666; padding: 20px; text-align: center;">No perfect numbers discovered yet. Keep searching!</p>';
                return;
            }
            
            let html = '';
            data.perfects.forEach(p => {
                html += `
                    <div class="perfect-discovery">
                        <h3>Perfect Number #${p.exponent}</h3>
                        <div class="formula">P = 2<sup>${p.exponent-1}</sup> × (2<sup>${p.exponent}</sup> - 1)</div>
                        <p>Digits: <strong>${formatNumber(p.digit_count)}</strong></p>
                        <p>Discovered by: <strong>${p.username}</strong> on ${p.discovered_at.split('T')[0]}</p>
                        <p>Value: ${p.perfect_number.substring(0, 60)}...</p>
                        <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.9;">
                            ✓ This number equals the sum of all its proper divisors
                        </p>
                    </div>
                `;
            });
            
            document.getElementById('perfects-list').innerHTML = html;
        }
        
        async function loadAssignments() {
            const response = await fetch('/api/assignments');
            const data = await response.json();
            
            const now = new Date();
            const activeAssignments = data.assignments.filter(a => {
                const expiresAt = new Date(a.expires_at);
                return expiresAt > now;
            });
            
            if (activeAssignments.length === 0) {
                document.getElementById('assignments-list').innerHTML = 
                    '<p style="color: #666; padding: 20px; text-align: center;">No active searches</p>';
                return;
            }
            
            let html = '<table><tr><th>Username</th><th>Candidate</th><th>Progress</th><th>Started</th></tr>';
            
            activeAssignments.forEach(a => {
                html += `
                    <tr>
                        <td><strong>${a.username}</strong></td>
                        <td class="mono">P(p=${formatNumber(a.exponent)})</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${a.progress}%">
                                    ${a.progress.toFixed(1)}%
                                </div>
                            </div>
                        </td>
                        <td class="time-ago">${timeAgo(a.assigned_at)}</td>
                    </tr>
                `;
            });
            
            html += '</table>';
            document.getElementById('assignments-list').innerHTML = html;
        }
        
        async function loadUsers() {
            const response = await fetch('/api/users');
            const data = await response.json();
            
            if (data.users.length === 0) {
                document.getElementById('users-list').innerHTML = 
                    '<p style="color: #666; padding: 20px; text-align: center;">No users yet</p>';
                return;
            }
            
            let html = '<table><tr><th>Rank</th><th>Username</th><th>Tests</th><th>Perfect Numbers</th><th>Last Active</th></tr>';
            
            data.users.forEach((u, i) => {
                html += `
                    <tr>
                        <td><strong>${i + 1}</strong></td>
                        <td><strong>${u.username}</strong></td>
                        <td>${formatNumber(u.exponents_tested)}</td>
                        <td><span class="badge ${u.perfects_found > 0 ? 'badge-success' : 'badge-primary'}">${u.perfects_found}</span></td>
                        <td class="time-ago">${timeAgo(u.last_active)}</td>
                    </tr>
                `;
            });
            
            html += '</table>';
            document.getElementById('users-list').innerHTML = html;
        }
        
        async function loadResults() {
            const response = await fetch('/api/results');
            const data = await response.json();
            
            if (data.results.length === 0) {
                document.getElementById('results-list').innerHTML = 
                    '<p style="color: #666; padding: 20px; text-align: center;">No results yet</p>';
                return;
            }
            
            let html = '<table><tr><th>Candidate</th><th>Result</th><th>Digits</th><th>User</th><th>Time</th><th>Completed</th></tr>';
            
            data.results.forEach(r => {
                const badge = r.is_perfect ? 
                    '<span class="badge badge-success">PERFECT ✓</span>' : 
                    '<span class="badge badge-warning">Not Perfect</span>';
                
                const digits = r.digit_count > 0 ? 
                    `<span class="digit-count">${formatNumber(r.digit_count)}</span>` : 
                    '-';
                
                html += `
                    <tr>
                        <td class="mono">P(p=${formatNumber(r.exponent)})</td>
                        <td>${badge}</td>
                        <td>${digits}</td>
                        <td><strong>${r.username}</strong></td>
                        <td>${r.time_seconds.toFixed(2)}s</td>
                        <td class="time-ago">${timeAgo(r.discovered_at)}</td>
                    </tr>
                `;
            });
            
            html += '</table>';
            document.getElementById('results-list').innerHTML = html;
        }
        
        async function refresh() {
            try {
                await Promise.all([
                    loadStats(),
                    loadPerfects(),
                    loadAssignments(),
                    loadUsers(),
                    loadResults()
                ]);
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            } catch (error) {
                console.error('Refresh error:', error);
            }
        }
        
        refresh();
        
        setInterval(refresh, 10000);
    </script>
</body>
</html>'''

		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		self.wfile.write(html.encode())

	def serve_stats(self):
		"""Serve overall statistics"""
		try:
			conn = sqlite3.connect(self.db_file)
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
			compute_hours = total_seconds / 3600

			conn.close()

			data = {
				'work_queue_size': work_queue_size,
				'active_assignments': active_assignments,
				'total_users': total_users,
				'perfects_found': perfects_found,
				'tests_completed': tests_completed,
				'compute_hours': compute_hours
			}

			self.send_json(data)

		except Exception as e:
			self.send_json({'error': str(e)}, 500)

	def serve_users(self):
		"""Serve top users"""
		try:
			conn = sqlite3.connect(self.db_file)
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
			self.send_json({'users': users})

		except Exception as e:
			self.send_json({'error': str(e)}, 500)

	def serve_assignments(self):
		"""Serve active assignments"""
		try:
			conn = sqlite3.connect(self.db_file)
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
			self.send_json({'assignments': assignments})

		except Exception as e:
			self.send_json({'error': str(e)}, 500)

	def serve_results(self):
		"""Serve recent results"""
		try:
			conn = sqlite3.connect(self.db_file)
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
			self.send_json({'results': results})

		except Exception as e:
			self.send_json({'error': str(e)}, 500)

	def serve_perfects(self):
		"""Serve discovered perfect numbers"""
		try:
			conn = sqlite3.connect(self.db_file)
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
			self.send_json({'perfects': perfects})

		except Exception as e:
			self.send_json({'error': str(e)}, 500)

	def send_json(self, data, status=200):
		"""Send JSON response"""
		self.send_response(status)
		self.send_header('Content-type', 'application/json')
		self.end_headers()
		self.wfile.write(json.dumps(data).encode())

def main():
	port = 8080
	db_file = 'perfectnet.db'

	if len(sys.argv) > 1:
		port = int(sys.argv[1])
	if len(sys.argv) > 2:
		db_file = sys.argv[2]

	DashboardHandler.db_file = db_file

	print(f"╔{'═'*68}╗")
	print(f"║{'Perfect Number Network - Web Dashboard'.center(68)}║")
	print(f"╚{'═'*68}╝\n")
	print(f"Dashboard URL: http://localhost:{port}")
	print(f"Database: {db_file}")
	print(f"\nPress Ctrl+C to stop\n")

	try:
		with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
			httpd.serve_forever()
	except KeyboardInterrupt:
		print("\n\nShutting down dashboard...")

if __name__ == '__main__':
	main()