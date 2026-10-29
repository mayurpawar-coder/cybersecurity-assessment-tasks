# scenario_id: (description, should_alert)
SCENARIOS = {
 "S00": ("Normal background logins + lone typos", False),
 "S01": ("Classic brute force: 8 fails/2 min, 1 IP -> 1 account", True),
 "S02": ("Slow password spray: 1 IP, 20 users, 1 try/2 min, no success", True),
 "S03": ("Distributed attack on 1 account from 10 IPs in 6 min", True),
 "S04": ("Office NAT: 6 users mistype once then succeed (same IP)", False),
 "S05": ("Single user forgets password: 3 fails then success", False),
 "S06": ("Boundary: exactly 4 fails, below threshold", False),
 "S07": ("Brute force that ends in SUCCESS (likely compromise)", True),
 "S08": ("Low-and-slow brute force: 12 fails over 24 min", True),
 "S09": ("Botnet spray: 30 IPs x 30 users, 1 fail each", True),
}
