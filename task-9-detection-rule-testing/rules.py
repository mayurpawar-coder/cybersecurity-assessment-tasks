import csv, datetime as dt
FMT = "%Y-%m-%d %H:%M:%S"
MIN = dt.timedelta(minutes=1)

def load(path="logs.csv"):
    ev = []
    with open(path) as f:
        for r in csv.DictReader(f):
            r["t"] = dt.datetime.strptime(r["timestamp"], FMT); r["event_id"] = int(r["event_id"]); ev.append(r)
    return sorted(ev, key=lambda r: r["t"])

def fails(ev): return [e for e in ev if e["status"] == "FAIL"]

# ---------- SUPPLIED RULE (v1) ----------
# "Alert when one source IP has >= 5 failed logins within 5 minutes."
def rule_v1(ev):
    alerts, seen = [], set()
    for e in fails(ev):
        w = [x for x in fails(ev) if x["src_ip"] == e["src_ip"] and e["t"] - 5 * MIN <= x["t"] <= e["t"]]
        if len(w) >= 5 and e["src_ip"] not in seen:
            seen.add(e["src_ip"])
            alerts.append(dict(rule="V1 ip>=5 fails/5min", time=e["t"], key=e["src_ip"], severity="MEDIUM", events=w))
    return alerts

# ---------- IMPROVED RULE SET (v2) ----------
def rule_v2(ev):
    alerts, seen = [], set()
    F = fails(ev)
    def fire(rule, key, e, sev, w):
        if (rule, key) in seen: return
        seen.add((rule, key)); alerts.append(dict(rule=rule, time=e["t"], key=key, severity=sev, events=w))
    for e in F:
        t = e["t"]
        # R1 brute force per (ip, user): >=5 in 5 min OR >=10 in 30 min (catches low-and-slow)
        pair = [x for x in F if x["src_ip"] == e["src_ip"] and x["user"] == e["user"]]
        w5 = [x for x in pair if t - 5 * MIN <= x["t"] <= t]
        w30 = [x for x in pair if t - 30 * MIN <= x["t"] <= t]
        if len(w5) >= 5 or len(w30) >= 10:
            sev = "MEDIUM"
            ok_after = [s for s in ev if s["status"] == "SUCCESS" and s["src_ip"] == e["src_ip"] and s["user"] == e["user"] and s["t"] >= w30[0]["t"]]
            if ok_after: sev = "CRITICAL"   # fails followed by success = probable compromise
            fire("R1 brute-force ip+user", f'{e["src_ip"]}|{e["user"]}', e, sev, w30)
        # R2 spray: >=5 distinct users failing from one IP in 30 min AND zero successes from that IP in window
        ipw = [x for x in F if x["src_ip"] == e["src_ip"] and t - 30 * MIN <= x["t"] <= t]
        users = {x["user"] for x in ipw}
        succ = [s for s in ev if s["status"] == "SUCCESS" and s["src_ip"] == e["src_ip"] and t - 30 * MIN <= s["t"] <= t]
        if len(users) >= 5 and not succ:
            fire("R2 password-spray ip", e["src_ip"], e, "HIGH", ipw)
        # R3 distributed: >=8 fails on one user in 10 min from >=3 distinct IPs
        uw = [x for x in F if x["user"] == e["user"] and t - 10 * MIN <= x["t"] <= t]
        if len(uw) >= 8 and len({x["src_ip"] for x in uw}) >= 3:
            fire("R3 distributed-user", e["user"], e, "HIGH", uw)
    # for CRITICAL escalation, re-evaluate after full scan (success may come later than alert time)
    return alerts
