import csv
from rules import load, rule_v1, rule_v2
from scenarios import SCENARIOS

ev = load()
lab = {int(r["event_id"]): r["scenario"] for r in csv.DictReader(open("ground_truth_labels.csv"))}

def flagged(alerts):
    s = {}
    for a in alerts:
        for e in a["events"]:
            s.setdefault(lab[e["event_id"]], set()).add(a["rule"].split()[0] + ("/" + a["severity"]))
    return s

def verdict(should, got):
    return {(True, True): "TP", (True, False): "FN (missed)", (False, True): "FP (false alarm)", (False, False): "TN"}[(should, got)]

a1, a2 = rule_v1(ev), rule_v2(ev)
f1, f2 = flagged(a1), flagged(a2)
out = []
out.append(f"Events: {len(ev)}   |   v1 alerts: {len(a1)}   |   v2 alerts: {len(a2)}\n")
out.append(f"{'ID':<4}{'Should alert':<14}{'v1':<32}{'v2':<28}Description")
out.append("-" * 110)
tally = {"v1": dict(TP=0, FP=0, FN=0, TN=0), "v2": dict(TP=0, FP=0, FN=0, TN=0)}
for sid, (desc, should) in SCENARIOS.items():
    r = []
    for name, f in (("v1", f1), ("v2", f2)):
        got = sid in f; v = verdict(should, got); tally[name][v.split()[0]] += 1
        r.append(v + (" " + ",".join(sorted(f[sid])) if got else ""))
    out.append(f"{sid:<4}{str(should):<14}{r[0]:<32}{r[1]:<28}{desc}")
out.append("")
for n, t in tally.items():
    p = t["TP"] / max(t["TP"] + t["FP"], 1); rc = t["TP"] / max(t["TP"] + t["FN"], 1)
    out.append(f"{n}: TP={t['TP']} FP={t['FP']} FN={t['FN']} TN={t['TN']}  precision={p:.2f} recall={rc:.2f}")
out.append("\nv2 alert detail:")
for a in a2: out.append(f"  {a['time']}  {a['severity']:<9} {a['rule']:<32} key={a['key']}  ({len(a['events'])} events)")
txt = "\n".join(out); print(txt); open("results.txt", "w").write(txt + "\n")
