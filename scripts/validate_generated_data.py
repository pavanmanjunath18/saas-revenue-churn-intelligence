#!/usr/bin/env python3
"""
SaaS Revenue & Churn Intelligence Platform — Phase 1
Data Validation & Reporting Script

Runs 15 integrity checks + detailed analytical summary:
  - FK integrity, monetary consistency, impossible states
  - Row counts, date ranges, sample rows
  - Churn rate by segment
  - MRR distribution by plan
  - Upgrade/downgrade/churn/reactivation event breakdown
  - Payment failure rates
  - Correlation checks (signals vs churn)

Usage: python scripts/validate_generated_data.py
"""

import os, sys
import pandas as pd
import numpy as np
from datetime import date

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "synthetic"
)

G = "\033[92m"   # green
R = "\033[91m"   # red
Y = "\033[93m"   # yellow
B = "\033[96m"   # cyan
E = "\033[0m"    # reset

results = []

def chk(name, ok, detail=""):
    tag = f"{G}PASS{E}" if ok else f"{R}FAIL{E}"
    print(f"  [{tag}]  {name}")
    if detail:
        print(f"          {detail}")
    results.append((name, ok))

def hdr(title):
    print(f"\n{B}{'─'*58}")
    print(f"  {title}")
    print(f"{'─'*58}{E}")

def row(label, value):
    print(f"  {label:<40} {value}")


# ── Load ───────────────────────────────────────────────────────────────────
hdr("Loading CSVs")
tables = {}
for t in ["customers","products","plans","subscriptions","subscription_items",
          "discounts","invoices","invoice_line_items","payments","refunds",
          "product_usage","support_tickets"]:
    p = os.path.join(DATA_DIR, f"{t}.csv")
    if os.path.exists(p):
        tables[t] = pd.read_csv(p, low_memory=False)
        print(f"  {t:<28} {len(tables[t]):>8,} rows")
    else:
        print(f"  {t:<28}  FILE MISSING")
        tables[t] = pd.DataFrame()

cust   = tables["customers"]
subs   = tables["subscriptions"]
invs   = tables["invoices"]
pays   = tables["payments"]
refs   = tables["refunds"]
usage  = tables["product_usage"]
tix    = tables["support_tickets"]
items  = tables["subscription_items"]
lines  = tables["invoice_line_items"]
plans  = tables["plans"]

total_rows = sum(len(v) for v in tables.values())
print(f"\n  {'TOTAL':28} {total_rows:>8,} rows")


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRITY CHECKS
# ═══════════════════════════════════════════════════════════════════════════
hdr("Integrity Checks  (15 assertions)")

# 1. No duplicate PKs
for t, col in [("customers","customer_id"),("subscriptions","subscription_id"),
               ("invoices","invoice_id"),("payments","payment_id"),("plans","plan_id")]:
    df = tables[t]
    dups = df[col].duplicated().sum() if not df.empty else 0
    chk(f"No duplicate PKs — {t}", dups == 0, f"{dups} duplicates" if dups else "")

# 2–3. FK: subscriptions → customers, invoices → customers
for child, pk, parent in [
    ("subscriptions","customer_id","customers"),
    ("invoices","customer_id","customers"),
]:
    orphans = tables[child][~tables[child][pk].isin(set(tables[parent]["customer_id"]))]\
              if not tables[child].empty and not tables[parent].empty else pd.DataFrame()
    chk(f"FK {child} → {parent}", len(orphans)==0,
        f"{len(orphans)} orphans" if len(orphans) else "")

# 4. Invoices → subscriptions
if not invs.empty and not subs.empty:
    orphans = invs[~invs["subscription_id"].isin(set(subs["subscription_id"]))]
    chk("FK invoices → subscriptions", len(orphans)==0,
        f"{len(orphans)} orphans" if len(orphans) else "")

# 5. Payments → invoices
if not pays.empty and not invs.empty:
    orphans = pays[~pays["invoice_id"].isin(set(invs["invoice_id"]))]
    chk("FK payments → invoices", len(orphans)==0,
        f"{len(orphans)} orphans" if len(orphans) else "")

# 6. Refunds → payments
if not refs.empty and not pays.empty:
    orphans = refs[~refs["payment_id"].isin(set(pays["payment_id"]))]
    chk("FK refunds → payments", len(orphans)==0,
        f"{len(orphans)} orphans" if len(orphans) else "")

# 7. No negative MRR
if not subs.empty:
    neg = (subs["mrr_cents"] < 0).sum()
    chk("No negative MRR on subscriptions", neg==0, f"{neg} rows" if neg else "")

# 8. No negative invoice totals
if not invs.empty:
    neg = (invs["total_cents"] < 0).sum()
    chk("No negative invoice totals", neg==0, f"{neg} rows" if neg else "")

# 9. Valid subscription statuses
if not subs.empty:
    bad = subs[~subs["status"].isin({"active","canceled","past_due","paused","trialing"})]
    chk("Valid subscription statuses", len(bad)==0, f"{len(bad)} invalid" if len(bad) else "")

# 10. Canceled subs have canceled_at
if not subs.empty:
    canceled = subs[subs["status"]=="canceled"]
    missing  = canceled["canceled_at"].isna().sum()
    chk("Canceled subs have canceled_at", missing==0,
        f"{missing} missing dates" if missing else "")

# 11. canceled_at > started_at
if not subs.empty:
    c = subs[subs["canceled_at"].notna()].copy()
    if not c.empty:
        c["started_at"]  = pd.to_datetime(c["started_at"])
        c["canceled_at"] = pd.to_datetime(c["canceled_at"])
        bad = (c["canceled_at"] <= c["started_at"]).sum()
        chk("canceled_at > started_at", bad==0, f"{bad} bad rows" if bad else "")

# 12. Invoice total_cents > 0
if not invs.empty:
    bad = (invs["total_cents"] <= 0).sum()
    chk("Invoice total_cents > 0", bad==0, f"{bad} rows" if bad else "")

# 13. Usage → customers FK
if not usage.empty and not cust.empty:
    orphans = usage[~usage["customer_id"].isin(set(cust["customer_id"]))]
    chk("FK product_usage → customers", len(orphans)==0,
        f"{len(orphans)} orphans" if len(orphans) else "")

# 14. Support tickets → customers FK
if not tix.empty and not cust.empty:
    orphans = tix[~tix["customer_id"].isin(set(cust["customer_id"]))]
    chk("FK support_tickets → customers", len(orphans)==0,
        f"{len(orphans)} orphans" if len(orphans) else "")

# 15. Subscriptions → plans FK
if not subs.empty and not plans.empty:
    bad = subs[~subs["plan_id"].isin(set(plans["plan_id"]))]
    chk("FK subscriptions → plans", len(bad)==0,
        f"{len(bad)} bad rows" if len(bad) else "")


# ═══════════════════════════════════════════════════════════════════════════
# DATE RANGES
# ═══════════════════════════════════════════════════════════════════════════
hdr("Date Ranges")
if not cust.empty:
    cust["signup_date"] = pd.to_datetime(cust["signup_date"])
    row("Customer signup range:",
        f"{cust['signup_date'].min().date()}  →  {cust['signup_date'].max().date()}")

if not subs.empty:
    subs["started_at"] = pd.to_datetime(subs["started_at"])
    row("Subscription start range:",
        f"{subs['started_at'].min().date()}  →  {subs['started_at'].max().date()}")

if not invs.empty:
    invs["billing_period_start"] = pd.to_datetime(invs["billing_period_start"])
    row("Invoice billing period:",
        f"{invs['billing_period_start'].min().date()}  →  {invs['billing_period_start'].max().date()}")

if not usage.empty:
    usage["month"] = pd.to_datetime(usage["month"])
    row("Product usage range:",
        f"{usage['month'].min().date()}  →  {usage['month'].max().date()}")


# ═══════════════════════════════════════════════════════════════════════════
# ROW COUNTS SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
hdr("Row Counts")
for t in ["customers","subscriptions","invoices","payments","product_usage","support_tickets"]:
    row(t, f"{len(tables[t]):>8,}")


# ═══════════════════════════════════════════════════════════════════════════
# SAMPLE ROWS
# ═══════════════════════════════════════════════════════════════════════════
hdr("Sample Rows — customers (3 rows)")
if not cust.empty:
    sample_cols = ["customer_id","company_name","segment","industry","signup_date","acquired_channel"]
    print(cust[sample_cols].head(3).to_string(index=False))

hdr("Sample Rows — subscriptions (3 rows)")
if not subs.empty:
    s_cols = ["subscription_id","customer_id","status","billing_interval","mrr_cents","started_at","canceled_at"]
    print(subs[s_cols].head(3).to_string(index=False))

hdr("Sample Rows — product_usage (3 rows)")
if not usage.empty:
    u_cols = ["customer_id","month","active_users","sessions_count","features_used_count","api_calls"]
    print(usage[u_cols].head(3).to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════════
# CHURN RATE BY SEGMENT
# ═══════════════════════════════════════════════════════════════════════════
hdr("Churn Rate by Segment")
if not cust.empty and not subs.empty:
    # Identify each customer's primary subscription lifecycle
    subs_merged = subs.merge(cust[["customer_id","segment"]], on="customer_id", how="left")
    # One row per customer: did any subscription get canceled?
    cust_churn = (
        subs_merged.groupby(["customer_id","segment"])
        .agg(ever_canceled=("status", lambda x: (x=="canceled").any()),
             ever_active=("status", lambda x: (x.isin(["active","canceled"])).any()))
        .reset_index()
    )
    seg_stats = (
        cust_churn.groupby("segment")
        .agg(total=("customer_id","count"),
             churned=("ever_canceled","sum"))
        .reset_index()
    )
    seg_stats["churn_rate_%"] = (seg_stats["churned"] / seg_stats["total"] * 100).round(1)
    print(seg_stats.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════════
# MRR DISTRIBUTION BY PLAN
# ═══════════════════════════════════════════════════════════════════════════
hdr("MRR Distribution — Active Subscriptions by Plan")
if not subs.empty and not plans.empty:
    active = subs[subs["status"]=="active"].copy()
    active = active.merge(plans[["plan_id","plan_name"]], on="plan_id", how="left")
    mrr_dist = (
        active.groupby(["plan_name","billing_interval"])
        .agg(count=("subscription_id","count"),
             total_mrr=("mrr_cents","sum"),
             avg_mrr=("mrr_cents","mean"))
        .reset_index()
    )
    mrr_dist["total_mrr_$"] = (mrr_dist["total_mrr"] / 100).round(0).astype(int)
    mrr_dist["avg_mrr_$"]   = (mrr_dist["avg_mrr"]   / 100).round(0).astype(int)
    mrr_dist = mrr_dist.sort_values(["plan_name","billing_interval"])
    print(mrr_dist[["plan_name","billing_interval","count","total_mrr_$","avg_mrr_$"]]
          .to_string(index=False))

    total_mrr = active["mrr_cents"].sum() / 100
    row("\nTotal active MRR:", f"${total_mrr:,.0f}")
    row("Total active ARR:", f"${total_mrr*12:,.0f}")


# ═══════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION EVENTS BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════
hdr("Subscription Events Breakdown")
if not subs.empty and not cust.empty:
    n_active    = (subs["status"]=="active").sum()
    n_canceled  = (subs["status"]=="canceled").sum()
    total_subs  = len(subs)

    # Customers with more than 1 subscription (had a plan change)
    sub_counts  = subs.groupby("customer_id")["subscription_id"].count()
    n_changed   = (sub_counts > 1).sum()
    n_reactivated = 0

    # Reactivations: customers who have ≥2 subs, with a gap between cancel and next start
    subs_dt = subs.copy()
    subs_dt["started_at"]  = pd.to_datetime(subs_dt["started_at"])
    subs_dt["canceled_at"] = pd.to_datetime(subs_dt["canceled_at"])
    for cid, grp in subs_dt.sort_values("started_at").groupby("customer_id"):
        if len(grp) < 2:
            continue
        grp2 = grp.reset_index(drop=True)
        for i in range(1, len(grp2)):
            prev_cancel = grp2.loc[i-1, "canceled_at"]
            next_start  = grp2.loc[i,   "started_at"]
            if pd.notna(prev_cancel) and prev_cancel < next_start:
                n_reactivated += 1
                break

    n_customers = len(cust)
    row("Total customers:",            f"{n_customers:,}")
    row("Total subscription records:", f"{total_subs:,}")
    row("Active subscriptions:",       f"{n_active:,}")
    row("Canceled subscriptions:",     f"{n_canceled:,}")
    row("Customers w/ plan changes:",  f"{n_changed:,}  ({n_changed/n_customers*100:.1f}% of customers)")
    row("Customers reactivated:",      f"{n_reactivated:,}  ({n_reactivated/n_customers*100:.1f}% of customers)")


# ═══════════════════════════════════════════════════════════════════════════
# PAYMENT & INVOICE HEALTH
# ═══════════════════════════════════════════════════════════════════════════
hdr("Payment & Invoice Health")
if not pays.empty:
    fail_rate  = (pays["status"]=="failed").mean() * 100
    succ_rate  = (pays["status"]=="succeeded").mean() * 100
    row("Payment success rate:",    f"{succ_rate:.1f}%")
    row("Payment failure rate:",    f"{fail_rate:.1f}%")
    row("Total payment attempts:",  f"{len(pays):,}")

if not invs.empty:
    paid_pct = (invs["status"]=="paid").mean() * 100
    row("Invoice paid %:",          f"{paid_pct:.1f}%")

if not refs.empty:
    row("Refund records:",          f"{len(refs):,}")


# ═══════════════════════════════════════════════════════════════════════════
# SUPPORT TICKET DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════
hdr("Support Ticket Priority Distribution")
if not tix.empty:
    pri_dist = tix["priority"].value_counts().reset_index()
    pri_dist.columns = ["priority","count"]
    pri_dist["pct"] = (pri_dist["count"] / len(tix) * 100).round(1)
    print(pri_dist.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL CORRELATION SANITY CHECK
# Check that churned customers had lower usage than retained customers
# ═══════════════════════════════════════════════════════════════════════════
hdr("Signal Correlation Sanity Check")
if not usage.empty and not subs.empty:
    # Get churn status per customer
    churn_status = (
        subs.groupby("customer_id")["status"]
        .apply(lambda x: "churned" if (x=="canceled").any() else "retained")
        .reset_index()
        .rename(columns={"status":"churn_label"})
    )
    usage_merged = usage.merge(churn_status, on="customer_id", how="left")
    avg_usage = (
        usage_merged.groupby("churn_label")
        .agg(avg_features=("features_used_count","mean"),
             avg_sessions=("sessions_count","mean"),
             avg_active_users=("active_users","mean"))
        .round(1)
    )
    print(avg_usage.to_string())

    churned_feat   = avg_usage.loc["churned","avg_features"]   if "churned"   in avg_usage.index else 0
    retained_feat  = avg_usage.loc["retained","avg_features"]  if "retained"  in avg_usage.index else 1
    corr_ok = churned_feat < retained_feat
    chk("Churned customers have lower avg feature usage than retained",
        corr_ok,
        f"churned={churned_feat:.1f}  retained={retained_feat:.1f}")

if not pays.empty and not subs.empty:
    # Churned customers should have higher payment failure rates
    churn_map = dict(
        subs.groupby("customer_id")["status"]
        .apply(lambda x: "churned" if (x=="canceled").any() else "retained")
    )
    pays_labeled = pays.copy()
    pays_labeled["churn_label"] = pays_labeled["customer_id"].map(churn_map)
    pay_corr = (
        pays_labeled.groupby("churn_label")["status"]
        .apply(lambda x: (x=="failed").mean() * 100)
        .round(1)
    )
    print("\n  Payment failure rate by churn outcome:")
    print(pay_corr.to_string())
    churned_fail  = pay_corr.get("churned",  0)
    retained_fail = pay_corr.get("retained", 0)
    chk("Churned customers have higher payment failure rates",
        churned_fail > retained_fail,
        f"churned={churned_fail:.1f}%  retained={retained_fail:.1f}%")


# ═══════════════════════════════════════════════════════════════════════════
# FINAL RESULT
# ═══════════════════════════════════════════════════════════════════════════
hdr("Final Result")
failed  = [n for n, ok in results if not ok]
passed  = sum(ok for _, ok in results)

print(f"  {passed}/{len(results)} checks passed\n")
if failed:
    print(f"  {R}Failed:{E}")
    for n in failed:
        print(f"    ✗  {n}")
    sys.exit(1)
else:
    print(f"  {G}All checks passed. Phase 1 data is valid and analytically sound.{E}")
