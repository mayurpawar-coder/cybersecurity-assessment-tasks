"""Generates SYNTHETIC authentication logs (no real data). Deterministic (seeded)."""
import csv, random, datetime as dt
random.seed(7)
base = dt.datetime(2026, 10, 27, 9, 0, 0)
rows, labels = [], []
eid = 0

def add(minutes, seconds, user, ip, status, scen):
    global eid
    eid += 1
    t = base + dt.timedelta(minutes=minutes, seconds=seconds)
    rows.append((eid, t.strftime("%Y-%m-%d %H:%M:%S"), user, ip, status))
    labels.append((eid, scen))

# S00 normal background: 40 users, own IP each, mostly success, a few lone typos
for i in range(40):
    u, ip = f"user{i:02d}", f"198.51.100.{i+1}"
    m = random.randint(0, 55)
    if i % 7 == 0:
        add(m, 0, u, ip, "FAIL", "S00"); add(m, 25, u, ip, "SUCCESS", "S00")
    else:
        add(m, random.randint(0, 59), u, ip, "SUCCESS", "S00")

# S01 classic brute force: 1 IP, 1 account, 8 fails in ~2 min
for k in range(8): add(5, k * 15, "admin", "203.0.113.10", "FAIL", "S01")

# S02 slow password spray: 1 IP, 20 different users, 1 try each every 2 min
for k in range(20): add(2 + k * 2, 0, f"user{k:02d}", "203.0.113.20", "FAIL", "S02")

# S03 distributed attack on ONE account from 10 IPs within 6 min
for k in range(10): add(20 + (k * 36) // 60, (k * 36) % 60, "finance.lead", f"192.0.2.{k+1}", "FAIL", "S03")

# S04 office NAT: 6 different users behind one IP mistype once, then log in OK
for k in range(6):
    u = f"staff{k}"
    add(30, k * 30, u, "198.51.100.200", "FAIL", "S04")
    add(30, k * 30 + 20, u, "198.51.100.200", "SUCCESS", "S04")

# S05 one user forgets password: 3 fails then success
for k in range(3): add(40, k * 20, "ravi", "198.51.100.77", "FAIL", "S05")
add(41, 10, "ravi", "198.51.100.77", "SUCCESS", "S05")

# S06 boundary: exactly 4 fails (below threshold), no success
for k in range(4): add(45, k * 15, "intern01", "203.0.113.50", "FAIL", "S06")

# S07 brute force that SUCCEEDS (compromise)
for k in range(7): add(50, k * 13, "svc.backup", "203.0.113.30", "FAIL", "S07")
add(51, 40, "svc.backup", "203.0.113.30", "SUCCESS", "S07")

# S08 low-and-slow brute force: 12 fails, one every 2 min, 1 IP, 1 account
for k in range(12): add(3 + k * 2, 30, "admin2", "203.0.113.40", "FAIL", "S08")

# S09 botnet spray: 30 IPs, 30 users, 1 fail each over 20 min
for k in range(30): add(10 + (k * 2) // 3, (k * 40) % 60, f"user{k:02d}", f"100.64.0.{k+1}", "FAIL", "S09")

rows.sort(key=lambda r: r[1])
with open("logs.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["event_id", "timestamp", "user", "src_ip", "status"]); w.writerows(rows)
with open("ground_truth_labels.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["event_id", "scenario"]); w.writerows(sorted(labels))
print(f"wrote {len(rows)} events")
