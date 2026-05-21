#!/usr/bin/env python3
"""
SaaS Revenue & Churn Intelligence Platform — Phase 1
Synthetic Data Generator  (v2 — correlated signals)

Generates 24 months of realistic B2B SaaS billing data for 1,500 customers.

Design principles:
  1. Churn is correlated with: declining usage, failed payments, low feature
     adoption, high support severity, monthly billing, smaller segment.
  2. Expansion (upgrades) is correlated with: high usage, high active users,
     high feature adoption, long tenure, low support severity.
  3. Noise (~15%) is added to every probability so correlations are real
     but not artificially perfect.
  4. Churn and at-risk rates are intentionally amplified slightly above
     real-world SaaS benchmarks so that dashboard patterns are visible in a
     portfolio-scale dataset (1,500 customers / 24 months).
     Real-world SMB monthly churn is typically 3–5%; here it is 4.5–11%
     depending on health score.  Enterprise churn is ~0.5–1.8%.
     See docs/data_generation.md for full parameter rationale.

Usage:
    pip install -r requirements.txt
    python scripts/generate_mock_data.py

Output: data/synthetic/*.csv  (12 files, ~43 000 total rows)
"""

import os, sys, uuid, random
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ── Reproducibility ────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker("en_US")
Faker.seed(SEED)

# ── Time range ─────────────────────────────────────────────────────────────
START_DATE = date(2024, 1, 1)
END_DATE   = date(2025, 12, 31)

def add_months(d, n):
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, 1)

def last_day(d):
    return add_months(d, 1) - timedelta(days=1)

def month_range(start, end):
    months, cur = [], date(start.year, start.month, 1)
    ceil = date(end.year, end.month, 1)
    while cur <= ceil:
        months.append(cur)
        cur = add_months(cur, 1)
    return months

SIM_MONTHS = month_range(START_DATE, END_DATE)   # 24 months

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "synthetic"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# PLAN CATALOG
# Plans are per-account (fixed monthly price, seats are just usage metadata).
# Annual billing gives ~17% discount; MRR is monthly-normalised (annual/12).
# ═══════════════════════════════════════════════════════════════════════════
PLAN_CATALOG = {
    # (name, interval): mrr_cents
    ("starter",    "monthly"): 9_900,
    ("growth",     "monthly"): 29_900,
    ("business",   "monthly"): 79_900,
    ("enterprise", "monthly"): 199_900,
    ("starter",    "annual"):  8_200,
    ("growth",     "annual"):  24_900,
    ("business",   "annual"):  66_500,
    ("enterprise", "annual"):  166_600,
    ("analytics_basic", "monthly"):  4_900,
    ("analytics_pro",   "monthly"):  14_900,
}
PLAN_HIERARCHY = ["starter", "growth", "business", "enterprise"]

# Usage capacity by plan — drives realistic active_users & feature ranges
USAGE_CAP = {
    "starter":    dict(users=(1, 5),    sessions=(15, 80),   features=(2, 8),   api=(50,  500)),
    "growth":     dict(users=(3, 20),   sessions=(60, 300),  features=(5, 14),  api=(400, 2_000)),
    "business":   dict(users=(10, 60),  sessions=(200, 800), features=(9, 20),  api=(2_000, 8_000)),
    "enterprise": dict(users=(30, 200), sessions=(400,2_000),features=(14, 25), api=(5_000, 25_000)),
}

# ═══════════════════════════════════════════════════════════════════════════
# SEGMENT CONFIG
# ═══════════════════════════════════════════════════════════════════════════
SEG_CFG = {
    "smb": dict(
        weight=0.60, emp=(5, 50),
        # Base churn used only as a floor; health-score multiplier drives actual rate
        base_churn=0.045,
        profiles={"healthy": 0.50, "at_risk": 0.30, "pre_churned": 0.20},
        plan_w={"starter": 0.55, "growth": 0.38, "business": 0.07, "enterprise": 0.00},
        annual_p=0.15, addon_p=0.12,
        base_upgrade_p=0.035, base_downgrade_p=0.018,
        discount_p=0.20,
        fail_p=0.04,   # base payment failure; multiplied by health factor
    ),
    "mid_market": dict(
        weight=0.30, emp=(51, 500),
        base_churn=0.020,
        profiles={"healthy": 0.65, "at_risk": 0.25, "pre_churned": 0.10},
        plan_w={"starter": 0.05, "growth": 0.50, "business": 0.40, "enterprise": 0.05},
        annual_p=0.30, addon_p=0.30,
        base_upgrade_p=0.025, base_downgrade_p=0.012,
        discount_p=0.30,
        fail_p=0.02,
    ),
    "enterprise": dict(
        weight=0.10, emp=(501, 5000),
        base_churn=0.005,
        profiles={"healthy": 0.80, "at_risk": 0.15, "pre_churned": 0.05},
        plan_w={"starter": 0.00, "growth": 0.05, "business": 0.40, "enterprise": 0.55},
        annual_p=0.70, addon_p=0.60,
        base_upgrade_p=0.012, base_downgrade_p=0.004,
        discount_p=0.50,
        fail_p=0.006,
    ),
}

INDUSTRIES = ["SaaS","FinTech","Healthcare","E-commerce","Logistics","EdTech",
              "Marketing","Real Estate","Manufacturing","Professional Services"]
CHANNELS   = ["organic","paid_search","referral","sales","partner","product_led"]
COUNTRIES  = ["US"]*70 + ["Canada"]*10 + ["UK"]*8 + ["Germany"]*5 + \
             ["Australia"]*4 + ["France"]*3
TICKET_CATS   = ["billing","technical","feature_request","onboarding","account"]
TICKET_PRIS   = ["low","medium","high","critical"]
FAILURE_REASONS = ["insufficient_funds","card_declined","expired_card",
                   "do_not_honor","processing_error"]
REFUND_REASONS  = ["requested_by_customer","duplicate","billing_error","service_issue"]
PAYMENT_METHODS = ["card"]*70 + ["ach"]*20 + ["wire"]*10
PRI_SEVERITY    = {"low": 0.1, "medium": 0.3, "high": 0.7, "critical": 1.0}

uid = lambda: str(uuid.uuid4())
ts  = lambda d: f"{d}T00:00:00Z" if d else None


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH SCORE  (0 = critical, 1 = perfect)
# Weights reflect interview-defensible SaaS signal importance.
# ═══════════════════════════════════════════════════════════════════════════
def compute_health_score(usage_history, payment_failed_last, worst_pri_last,
                         months_active, interval):
    """
    Composite health score for one customer-month.

    Signals:
      usage_trend    (0.30) — 3-month rolling vs prior 3 months
      payment_ok     (0.25) — did last invoice pay successfully?
      support_calm   (0.20) — absence of high-severity tickets
      tenure         (0.15) — longer = stickier
      feature_depth  (0.10) — breadth of feature adoption

    Annual billing adds +0.08 bonus (switching-cost signal).
    Noise ±12% applied at the end.
    """
    # Usage trend ─────────────────────────────────────────────────────────
    if len(usage_history) >= 2:
        window = min(len(usage_history), 3)
        prior_slice = usage_history[:-window] if window < len(usage_history) else usage_history[:1]
        recent  = np.mean([u["features_used_count"] for u in usage_history[-window:]])
        prior   = np.mean([u["features_used_count"] for u in prior_slice])
        # sigmoid-like mapping: declining (-50%) → 0.1, flat → 0.5, growing (+50%) → 0.9
        trend_ratio = recent / max(prior, 1)
        usage_score = max(0.0, min(1.0, 0.5 + (trend_ratio - 1.0) * 0.8))
    else:
        usage_score = 0.55  # new customer, neutral

    # Feature depth ────────────────────────────────────────────────────────
    if usage_history:
        features = usage_history[-1]["features_used_count"]
        feature_score = min(features / 18.0, 1.0)
    else:
        feature_score = 0.5

    # Payment health ────────────────────────────────────────────────────────
    payment_score = 0.0 if payment_failed_last else 1.0

    # Support severity ──────────────────────────────────────────────────────
    sev = PRI_SEVERITY.get(worst_pri_last, 0.0)
    support_score = 1.0 - sev

    # Tenure ────────────────────────────────────────────────────────────────
    tenure_score = min(months_active / 18.0, 1.0)

    score = (
        0.30 * usage_score  +
        0.25 * payment_score +
        0.20 * support_score +
        0.15 * tenure_score  +
        0.10 * feature_score
    )

    # Annual billing bonus (switching cost)
    if interval == "annual":
        score += 0.08

    # Noise  ±12%
    score *= random.uniform(0.88, 1.12)
    return max(0.0, min(1.0, score))


# ═══════════════════════════════════════════════════════════════════════════
# USAGE GENERATOR  (correlated with profile + health trajectory)
# ═══════════════════════════════════════════════════════════════════════════
def gen_usage(plan, profile, months_active, months_to_churn):
    """
    Generate one month of product usage.
    healthy  → stable or slight growth
    at_risk  → slow decline
    pre_churned → accelerating decline, starts ~4 months before churn
    """
    cap = USAGE_CAP.get(plan, USAGE_CAP["growth"])

    if profile == "healthy":
        factor = min(1.0 + months_active * 0.008, 1.25)
    elif profile == "at_risk":
        factor = max(1.0 - months_active * 0.012, 0.45)
    else:  # pre_churned
        if months_to_churn is not None and months_to_churn <= 4:
            # Sharp decline in final 4 months
            factor = max(0.65 - (4 - months_to_churn) * 0.16, 0.04)
        else:
            factor = max(1.0 - months_active * 0.018, 0.55)

    def scaled(lo, hi):
        return max(1, int(random.randint(lo, hi) * factor * random.uniform(0.88, 1.12)))

    return dict(
        active_users        = scaled(*cap["users"]),
        sessions_count      = scaled(*cap["sessions"]),
        features_used_count = scaled(*cap["features"]),
        api_calls           = scaled(*cap["api"]),
        data_exported_mb    = round(random.uniform(0.5, 40.0) * factor, 2),
        report_views        = scaled(2, 50),
    )


# ═══════════════════════════════════════════════════════════════════════════
# SUPPORT TICKET GENERATOR  (correlated with profile + proximity to churn)
# ═══════════════════════════════════════════════════════════════════════════
def gen_tickets(cid, profile, months_to_churn, month):
    base_p = {"healthy": 0.10, "at_risk": 0.22, "pre_churned": 0.32}[profile]
    if months_to_churn is not None and months_to_churn <= 2:
        base_p = min(base_p * 2.2, 0.85)

    tickets, worst_pri = [], None
    if random.random() >= base_p:
        return tickets, worst_pri

    n = random.choices([1, 2, 3], weights=[0.70, 0.22, 0.08])[0]
    for _ in range(n):
        if months_to_churn is not None and months_to_churn <= 2:
            pri = random.choices(TICKET_PRIS, weights=[5,  20, 45, 30])[0]
            cat = random.choices(TICKET_CATS,  weights=[40, 25, 10,  5, 20])[0]
        elif profile == "at_risk":
            pri = random.choices(TICKET_PRIS, weights=[15, 40, 35, 10])[0]
            cat = random.choices(TICKET_CATS,  weights=[30, 35, 15,  5, 15])[0]
        else:
            pri = random.choices(TICKET_PRIS, weights=[40, 40, 15,  5])[0]
            cat = random.choices(TICKET_CATS,  weights=[10, 25, 35, 20, 10])[0]

        if worst_pri is None or PRI_SEVERITY[pri] > PRI_SEVERITY[worst_pri]:
            worst_pri = pri

        opened = month + timedelta(days=random.randint(0, 27))
        resolved = res_hours = csat = None
        status = "open"
        if random.random() < 0.88:
            res_hours  = max(0.5, round(random.gauss(16, 10) if pri in ["low","medium"]
                                        else random.gauss(5, 3), 1))
            resolved   = opened + timedelta(hours=res_hours)
            status     = "resolved"
            csat_w     = ([5,8,17,35,35] if profile == "healthy"
                          else [20,28,25,18,9] if months_to_churn is not None and months_to_churn <= 2
                          else [10,18,25,28,19])
            csat       = random.choices([1,2,3,4,5], weights=csat_w)[0]

        tickets.append(dict(
            ticket_id=uid(), customer_id=cid, category=cat, priority=pri,
            status=status, subject=f"{cat.replace('_',' ').title()} inquiry",
            opened_at=ts(opened), resolved_at=ts(resolved),
            resolution_time_hours=res_hours, csat_score=csat, created_at=ts(opened),
        ))
    return tickets, worst_pri


# ═══════════════════════════════════════════════════════════════════════════
# COLLECTORS
# ═══════════════════════════════════════════════════════════════════════════
rows = {t: [] for t in [
    "products","plans","customers","subscriptions","subscription_items",
    "discounts","invoices","invoice_line_items","payments","refunds",
    "product_usage","support_tickets",
]}

PRODUCT_CORE_ID  = "00000000-0000-0000-0000-000000000001"
PRODUCT_ADDON_ID = "00000000-0000-0000-0000-000000000002"

rows["products"] = [
    dict(product_id=PRODUCT_CORE_ID,  product_name="Core Platform",
         product_type="core",    description="Workflow automation platform",
         is_active=True,  created_at=ts(START_DATE)),
    dict(product_id=PRODUCT_ADDON_ID, product_name="Analytics Add-on",
         product_type="add_on",  description="Advanced analytics and reporting",
         is_active=True, created_at=ts(START_DATE)),
]

PLAN_ID_MAP = {}
for (name, interval), mrr in PLAN_CATALOG.items():
    pid = uid()
    prod = PRODUCT_ADDON_ID if name.startswith("analytics") else PRODUCT_CORE_ID
    PLAN_ID_MAP[(name, interval)] = pid
    rows["plans"].append(dict(
        plan_id=pid, product_id=prod, plan_name=name,
        billing_interval=interval, price_cents=mrr,
        max_seats=(5 if name=="starter" else 25 if name=="growth"
                   else 100 if name=="business" else None),
        is_active=True, created_at=ts(START_DATE),
    ))


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOMER GENERATION
# ═══════════════════════════════════════════════════════════════════════════
def pick(seg):
    cfg = SEG_CFG[seg]
    return (
        random.choices(list(cfg["profiles"]), weights=list(cfg["profiles"].values()))[0],
        random.choices(list(cfg["plan_w"]),   weights=list(cfg["plan_w"].values()))[0],
    )

# Slight growth in customer acquisition over 24 months
arrival_weights = [1.0 * (1.05 ** i) for i in range(len(SIM_MONTHS))]
arrival_months  = random.choices(SIM_MONTHS, weights=arrival_weights, k=1500)

customer_defs = []
discount_map  = {}

for arr_month in arrival_months:
    signup = arr_month + timedelta(days=random.randint(0, 27))
    if signup > END_DATE:
        signup = END_DATE

    seg = random.choices(list(SEG_CFG), weights=[c["weight"] for c in SEG_CFG.values()])[0]
    cfg = SEG_CFG[seg]
    profile, plan_name = pick(seg)
    interval = "annual" if random.random() < cfg["annual_p"] else "monthly"
    cid = uid()

    rows["customers"].append(dict(
        customer_id=cid, company_name=fake.company(),
        industry=random.choice(INDUSTRIES), segment=seg,
        employee_count=random.randint(*cfg["emp"]),
        country=random.choice(COUNTRIES), city=fake.city(),
        signup_date=signup, acquired_channel=random.choice(CHANNELS),
        account_owner=fake.name(), is_deleted=False,
        created_at=ts(signup), updated_at=ts(signup),
    ))

    customer_defs.append(dict(
        customer_id=cid, segment=seg, profile=profile,
        signup=signup, plan_name=plan_name, interval=interval,
    ))

    if random.random() < cfg["discount_p"]:
        dtype = random.choice(["percentage","percentage","fixed_amount"])
        dval  = (random.choice([10,15,20,25,30]) if dtype == "percentage"
                 else random.choice([500,1000,2000]))
        dur   = random.choice(["once","repeating","repeating","forever"])
        dur_m = random.randint(3, 12) if dur == "repeating" else None
        did   = uid()
        rows["discounts"].append(dict(
            discount_id=did, customer_id=cid,
            coupon_code=f"DISC-{random.randint(1000,9999)}",
            discount_type=dtype, discount_value=dval,
            duration=dur, duration_months=dur_m,
            valid_from=signup,
            valid_until=add_months(signup, dur_m) if dur_m else None,
            created_at=ts(signup),
        ))
        discount_map[cid] = did


# ═══════════════════════════════════════════════════════════════════════════
# PER-CUSTOMER MONTH-BY-MONTH SIMULATION
# ═══════════════════════════════════════════════════════════════════════════
print(f"Simulating 1,500 customers across {len(SIM_MONTHS)} months...")

_inv_counter = 0
def inv_number():
    global _inv_counter
    _inv_counter += 1
    return f"INV-{_inv_counter:07d}"

def apply_discount(mrr_cents, disc_row, months_active):
    if disc_row is None:
        return 0
    if disc_row["duration"] == "once" and months_active > 1:
        return 0
    if disc_row["valid_until"] is not None:
        try:
            vu = date.fromisoformat(str(disc_row["valid_until"]).split("T")[0])
            if date.today() > vu:  # rough check; good enough for synthetic data
                return 0
        except Exception:
            pass
    if disc_row["discount_type"] == "percentage":
        return int(mrr_cents * disc_row["discount_value"] / 100)
    return min(mrr_cents, int(disc_row["discount_value"]))


for cdef in customer_defs:
    cid      = cdef["customer_id"]
    seg      = cdef["segment"]
    profile  = cdef["profile"]
    signup   = cdef["signup"]
    cfg      = SEG_CFG[seg]

    disc_row = None
    if cid in discount_map:
        disc_row = next(d for d in rows["discounts"]
                        if d["discount_id"] == discount_map[cid])

    # Subscription state
    cur_plan     = cdef["plan_name"]
    cur_interval = cdef["interval"]
    cur_sub_id   = None
    sub_start    = None
    mrr_cents    = 0
    churned      = False
    churn_date   = None
    ever_active  = False
    reactivated  = False

    # Add-on
    addon_plan   = ("analytics_pro" if seg == "enterprise" else "analytics_basic")
    has_addon    = random.random() < cfg["addon_p"]
    addon_sub_id = None
    addon_active = False

    # Pre-churn horizon for pre_churned profiles
    churn_target = None
    if profile == "pre_churned":
        tenure = random.randint(3, 18)
        ct = add_months(date(signup.year, signup.month, 1), tenure)
        churn_target = ct if ct <= END_DATE else None

    # Per-customer signal state (drives health score)
    usage_history       = []   # list of dicts
    payment_failed_last = False
    worst_pri_last      = None
    months_active       = 0

    for month in SIM_MONTHS:
        m_start = month
        m_end   = last_day(month)

        if signup > m_end:
            continue

        # ── New subscription ───────────────────────────────────────────────
        if cur_sub_id is None and not churned:
            sub_start   = max(signup, m_start)
            cur_sub_id  = uid()
            mrr_cents   = PLAN_CATALOG[(cur_plan, cur_interval)]
            ever_active = True
            rows["subscriptions"].append(dict(
                subscription_id=cur_sub_id, customer_id=cid,
                product_id=PRODUCT_CORE_ID,
                plan_id=PLAN_ID_MAP[(cur_plan, cur_interval)],
                status="active", billing_interval=cur_interval,
                started_at=sub_start, canceled_at=None,
                trial_ends_at=None, seats=1, mrr_cents=mrr_cents,
                discount_id=discount_map.get(cid),
                created_at=ts(sub_start), updated_at=ts(sub_start),
            ))

        # ── Reactivation ───────────────────────────────────────────────────
        if churned and ever_active and not reactivated:
            since = sum(1 for m in SIM_MONTHS if churn_date and m > churn_date and m <= month)
            if since >= 3 and random.random() < 0.035:
                cur_plan     = random.choices(PLAN_HIERARCHY[:3], weights=[0.5,0.35,0.15])[0]
                cur_interval = "monthly"
                cur_sub_id   = uid()
                mrr_cents    = PLAN_CATALOG[(cur_plan, cur_interval)]
                sub_start    = m_start
                churned      = False
                reactivated  = True
                months_active = 0
                usage_history = []
                payment_failed_last = False
                worst_pri_last = None
                rows["subscriptions"].append(dict(
                    subscription_id=cur_sub_id, customer_id=cid,
                    product_id=PRODUCT_CORE_ID,
                    plan_id=PLAN_ID_MAP[(cur_plan, cur_interval)],
                    status="active", billing_interval=cur_interval,
                    started_at=sub_start, canceled_at=None,
                    trial_ends_at=None, seats=1, mrr_cents=mrr_cents,
                    discount_id=None, created_at=ts(sub_start), updated_at=ts(sub_start),
                ))

        if churned and not reactivated:
            continue

        months_active += 1

        # months_to_churn for signal decay
        if churn_target:
            diff = (churn_target.year - month.year)*12 + (churn_target.month - month.month)
            months_to_churn = max(0, diff)
        else:
            months_to_churn = None

        # ── Generate usage THIS month ──────────────────────────────────────
        usage_vals = gen_usage(cur_plan, profile, months_active, months_to_churn)
        rows["product_usage"].append(dict(
            usage_id=uid(), customer_id=cid, product_id=PRODUCT_CORE_ID,
            month=m_start, **usage_vals, created_at=ts(m_start),
        ))
        usage_history.append(usage_vals)

        # ── Support tickets THIS month ─────────────────────────────────────
        new_tickets, worst_this_month = gen_tickets(cid, profile, months_to_churn, m_start)
        rows["support_tickets"].extend(new_tickets)

        # ── Compute health score (uses LAST month's payment + support state) ─
        health = compute_health_score(
            usage_history, payment_failed_last, worst_pri_last,
            months_active, cur_interval,
        )

        # Update state for NEXT month
        worst_pri_last = worst_this_month

        # ── Derive probabilities from health score ─────────────────────────
        #
        # Churn:  low health → high churn.  Annual billing cuts churn ~60%.
        #         Health 0.0 → ~4x base churn;  Health 1.0 → ~0.3x base churn
        interval_churn_mult = 0.40 if cur_interval == "annual" else 1.0
        health_churn_mult   = max(0.3, 2.5 - 2.2 * health)
        churn_p = (cfg["base_churn"] * interval_churn_mult * health_churn_mult
                   * random.uniform(0.85, 1.15))

        # Force high churn if pre_churned customer has hit churn target
        if churn_target and month >= churn_target:
            churn_p = max(churn_p, 0.80)

        # Upgrade: high health + long tenure → more likely to expand
        # Health 1.0 → 2x base;  Health 0.0 → 0.3x base
        health_upgrade_mult = max(0.3, health * 2.0)
        tenure_bonus        = 1.0 + min(months_active / 14.0, 0.6)
        upgrade_p = (cfg["base_upgrade_p"] * health_upgrade_mult * tenure_bonus
                     * random.uniform(0.85, 1.15))

        # Downgrade: low health → more likely to contract
        health_down_mult = max(0.3, 1.8 - 1.5 * health)
        downgrade_p = (cfg["base_downgrade_p"] * health_down_mult
                       * random.uniform(0.85, 1.15))

        # Payment failure: low health → higher fail rate
        health_fail_mult = max(0.2, 2.0 - 1.6 * health)
        fail_p = cfg["fail_p"] * health_fail_mult * random.uniform(0.85, 1.15)

        # ── Upgrade / Downgrade ────────────────────────────────────────────
        can_up   = months_active >= 2 and PLAN_HIERARCHY.index(cur_plan) < 3
        can_down = months_active >= 3 and PLAN_HIERARCHY.index(cur_plan) > 0

        plan_changed = False
        if can_up and not churned and random.random() < upgrade_p:
            _old = next(s for s in rows["subscriptions"]
                        if s["subscription_id"] == cur_sub_id)
            _old["status"] = "canceled"; _old["canceled_at"] = m_start
            _old["updated_at"] = ts(m_start)
            cur_plan    = PLAN_HIERARCHY[PLAN_HIERARCHY.index(cur_plan) + 1]
            cur_sub_id  = uid()
            mrr_cents   = PLAN_CATALOG[(cur_plan, cur_interval)]
            rows["subscriptions"].append(dict(
                subscription_id=cur_sub_id, customer_id=cid,
                product_id=PRODUCT_CORE_ID,
                plan_id=PLAN_ID_MAP[(cur_plan, cur_interval)],
                status="active", billing_interval=cur_interval,
                started_at=m_start, canceled_at=None,
                trial_ends_at=None, seats=1, mrr_cents=mrr_cents,
                discount_id=None, created_at=ts(m_start), updated_at=ts(m_start),
            ))
            plan_changed = True

        elif can_down and not churned and random.random() < downgrade_p:
            _old = next(s for s in rows["subscriptions"]
                        if s["subscription_id"] == cur_sub_id)
            _old["status"] = "canceled"; _old["canceled_at"] = m_start
            _old["updated_at"] = ts(m_start)
            cur_plan    = PLAN_HIERARCHY[PLAN_HIERARCHY.index(cur_plan) - 1]
            cur_sub_id  = uid()
            mrr_cents   = PLAN_CATALOG[(cur_plan, cur_interval)]
            rows["subscriptions"].append(dict(
                subscription_id=cur_sub_id, customer_id=cid,
                product_id=PRODUCT_CORE_ID,
                plan_id=PLAN_ID_MAP[(cur_plan, cur_interval)],
                status="active", billing_interval=cur_interval,
                started_at=m_start, canceled_at=None,
                trial_ends_at=None, seats=1, mrr_cents=mrr_cents,
                discount_id=None, created_at=ts(m_start), updated_at=ts(m_start),
            ))
            plan_changed = True

        # ── Add-on subscription ────────────────────────────────────────────
        if has_addon and not addon_active and months_active >= 2 and not churned:
            if random.random() < churn_p:
                pass  # don't start an add-on if about to churn
            else:
                addon_sub_id = uid()
                addon_mrr    = PLAN_CATALOG[(addon_plan, "monthly")]
                addon_active = True
                rows["subscriptions"].append(dict(
                    subscription_id=addon_sub_id, customer_id=cid,
                    product_id=PRODUCT_ADDON_ID,
                    plan_id=PLAN_ID_MAP[(addon_plan, "monthly")],
                    status="active", billing_interval="monthly",
                    started_at=m_start, canceled_at=None,
                    trial_ends_at=None, seats=1, mrr_cents=addon_mrr,
                    discount_id=None, created_at=ts(m_start), updated_at=ts(m_start),
                ))
                rows["subscription_items"].append(dict(
                    item_id=uid(), subscription_id=addon_sub_id,
                    plan_id=PLAN_ID_MAP[(addon_plan, "monthly")],
                    quantity=1, unit_price_cents=addon_mrr,
                    total_price_cents=addon_mrr,
                    started_at=m_start, ended_at=None, created_at=ts(m_start),
                ))

        # ── Invoicing ──────────────────────────────────────────────────────
        should_invoice = (
            cur_interval == "monthly"
            or (cur_interval == "annual"
                and sub_start
                and month.month == sub_start.month
                and not plan_changed)
        )

        if should_invoice:
            disc_amt = apply_discount(mrr_cents, disc_row, months_active)
            subtotal = mrr_cents * (12 if cur_interval == "annual" else 1)
            disc_amt = disc_amt * (12 if cur_interval == "annual" else 1)
            tax      = int(subtotal * 0.08)
            total    = subtotal - disc_amt + tax

            pay_failed = random.random() < fail_p
            inv_status = "paid" if not pay_failed else random.choice(["open","uncollectible"])
            paid_at    = m_start + timedelta(days=random.randint(0,3)) if not pay_failed else None

            inv_id = uid()
            rows["invoices"].append(dict(
                invoice_id=inv_id, customer_id=cid, subscription_id=cur_sub_id,
                invoice_number=inv_number(), status=inv_status,
                billing_period_start=m_start, billing_period_end=m_end,
                subtotal_cents=subtotal, discount_amount_cents=disc_amt,
                tax_cents=tax, total_cents=total,
                amount_paid_cents=total if not pay_failed else 0,
                amount_due_cents=0 if not pay_failed else total,
                issued_at=ts(m_start),
                due_at=ts(m_start + timedelta(days=30)),
                paid_at=ts(paid_at),
                created_at=ts(m_start),
            ))
            rows["invoice_line_items"].append(dict(
                line_item_id=uid(), invoice_id=inv_id,
                subscription_item_id=None,
                description=(f"{cur_plan.title()} Plan "
                             f"({'Annual' if cur_interval=='annual' else 'Monthly'})"),
                quantity=1, unit_price_cents=subtotal, amount_cents=subtotal,
                created_at=ts(m_start),
            ))

            # Payment attempt
            pay_id = uid()
            rows["payments"].append(dict(
                payment_id=pay_id, invoice_id=inv_id, customer_id=cid,
                amount_cents=total, currency="USD",
                status="succeeded" if not pay_failed else "failed",
                payment_method=random.choice(PAYMENT_METHODS),
                failure_reason=(random.choice(FAILURE_REASONS) if pay_failed else None),
                attempted_at=ts(m_start), created_at=ts(m_start),
            ))

            # Retry on failure
            if pay_failed and random.random() < 0.55:
                retry_date = m_start + timedelta(days=random.randint(3, 7))
                retry_ok   = random.random() < 0.68
                rows["payments"].append(dict(
                    payment_id=uid(), invoice_id=inv_id, customer_id=cid,
                    amount_cents=total, currency="USD",
                    status="succeeded" if retry_ok else "failed",
                    payment_method=random.choice(PAYMENT_METHODS),
                    failure_reason=(None if retry_ok else random.choice(FAILURE_REASONS)),
                    attempted_at=ts(retry_date), created_at=ts(retry_date),
                ))
                if retry_ok:
                    _inv = next(i for i in rows["invoices"] if i["invoice_id"] == inv_id)
                    _inv["status"] = "paid"
                    _inv["amount_paid_cents"] = total
                    _inv["amount_due_cents"]  = 0
                    _inv["paid_at"]           = ts(retry_date)
                    pay_failed = False   # resolved

            # Refund ~1.8% of successful payments
            if not pay_failed and random.random() < 0.018:
                rows["refunds"].append(dict(
                    refund_id=uid(), payment_id=pay_id, customer_id=cid,
                    amount_cents=random.choice([total, total//2]),
                    reason=random.choice(REFUND_REASONS), status="succeeded",
                    issued_at=ts(m_start + timedelta(days=random.randint(1,14))),
                    created_at=ts(m_start),
                ))

            payment_failed_last = pay_failed

            # Add-on invoice
            if addon_active:
                addon_mrr_v = PLAN_CATALOG[(addon_plan, "monthly")]
                addon_tax   = int(addon_mrr_v * 0.08)
                addon_total = addon_mrr_v + addon_tax
                a_inv_id    = uid()
                rows["invoices"].append(dict(
                    invoice_id=a_inv_id, customer_id=cid, subscription_id=addon_sub_id,
                    invoice_number=inv_number(), status="paid",
                    billing_period_start=m_start, billing_period_end=m_end,
                    subtotal_cents=addon_mrr_v, discount_amount_cents=0,
                    tax_cents=addon_tax, total_cents=addon_total,
                    amount_paid_cents=addon_total, amount_due_cents=0,
                    issued_at=ts(m_start),
                    due_at=ts(m_start + timedelta(days=30)),
                    paid_at=ts(m_start + timedelta(days=1)),
                    created_at=ts(m_start),
                ))
                rows["invoice_line_items"].append(dict(
                    line_item_id=uid(), invoice_id=a_inv_id, subscription_item_id=None,
                    description=f"{addon_plan.replace('_',' ').title()} (Monthly)",
                    quantity=1, unit_price_cents=addon_mrr_v, amount_cents=addon_mrr_v,
                    created_at=ts(m_start),
                ))

        # ── Churn ──────────────────────────────────────────────────────────
        if random.random() < churn_p:
            cancel_date = max(m_end, sub_start + timedelta(days=1))
            _sub = next(s for s in rows["subscriptions"]
                        if s["subscription_id"] == cur_sub_id)
            _sub["status"] = "canceled"; _sub["canceled_at"] = cancel_date
            _sub["updated_at"] = ts(cancel_date)

            if addon_active and addon_sub_id:
                _add = next((s for s in rows["subscriptions"]
                             if s["subscription_id"] == addon_sub_id), None)
                if _add:
                    _add["status"] = "canceled"; _add["canceled_at"] = cancel_date
                    _add["updated_at"] = ts(cancel_date)
                _item = next((i for i in rows["subscription_items"]
                              if i["subscription_id"] == addon_sub_id), None)
                if _item:
                    _item["ended_at"] = cancel_date
                addon_active = False

            churned    = True
            churn_date = cancel_date
            break


# ═══════════════════════════════════════════════════════════════════════════
# WRITE CSVs
# ═══════════════════════════════════════════════════════════════════════════
print("\nWriting CSV files...\n")
for table, data in rows.items():
    df   = pd.DataFrame(data) if data else pd.DataFrame()
    path = os.path.join(OUTPUT_DIR, f"{table}.csv")
    df.to_csv(path, index=False)
    print(f"  {table:<25} {len(df):>7,} rows")

print(f"\nDone. Total rows: {sum(len(d) for d in rows.values()):,}")
print("Run scripts/validate_generated_data.py for full validation report.")
