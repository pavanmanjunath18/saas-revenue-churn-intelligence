# Database Schema — SaaS Revenue & Churn Intelligence Platform

## Overview

All raw tables live in the `raw` schema. Analytics models live in the `analytics` schema.

Monetary values stored in **cents** (integer) to avoid floating-point errors.
All timestamps in **UTC**.
MRR values are **monthly-normalized** (annual subscriptions divided by 12).

---

## Entity Relationship Summary

```
customers
  └── subscriptions (1:many)
        └── subscription_items (1:many)
  └── invoices (1:many)
        └── invoice_line_items (1:many)
        └── payments (1:many)
        └── refunds (1:many)
  └── discounts (1:many)
  └── product_usage (1:many, monthly snapshots)
  └── support_tickets (1:many)

products
  └── plans (1:many)
        └── subscription_items (1:many)
```

---

## Table Definitions

### customers

The core entity. Represents a B2B company (account-level billing).

| Column | Type | Notes |
|---|---|---|
| customer_id | UUID PK | |
| company_name | VARCHAR(255) | |
| industry | VARCHAR(100) | SaaS, FinTech, Healthcare, Retail, etc. |
| segment | VARCHAR(50) | smb / mid_market / enterprise |
| employee_count | INTEGER | Drives segment classification |
| country | VARCHAR(100) | |
| city | VARCHAR(100) | |
| signup_date | DATE | When they created an account |
| acquired_channel | VARCHAR(100) | organic / paid_search / referral / sales |
| account_owner | VARCHAR(100) | Internal sales rep (synthetic) |
| is_deleted | BOOLEAN | Soft delete |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Segment logic:**
- smb: employee_count < 51
- mid_market: 51–500
- enterprise: > 500

---

### products

| Column | Type | Notes |
|---|---|---|
| product_id | UUID PK | |
| product_name | VARCHAR(100) | e.g. "Core Platform", "Analytics Add-on" |
| product_type | VARCHAR(50) | core / add_on / professional_services |
| description | TEXT | |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

---

### plans

Pricing tiers per product.

| Column | Type | Notes |
|---|---|---|
| plan_id | UUID PK | |
| product_id | UUID FK → products | |
| plan_name | VARCHAR(100) | starter / growth / professional / enterprise |
| billing_interval | VARCHAR(20) | monthly / annual |
| price_cents | INTEGER | Monthly price (annual already /12 normalized) |
| max_seats | INTEGER | NULL = unlimited |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

---

### subscriptions

One subscription per customer per product. Tracks lifecycle.

| Column | Type | Notes |
|---|---|---|
| subscription_id | UUID PK | |
| customer_id | UUID FK → customers | |
| product_id | UUID FK → products | |
| plan_id | UUID FK → plans | |
| status | VARCHAR(50) | active / canceled / past_due / paused / trialing |
| billing_interval | VARCHAR(20) | monthly / annual |
| started_at | DATE | Subscription start |
| canceled_at | DATE | NULL if active |
| trial_ends_at | DATE | NULL if not trialing |
| seats | INTEGER | Number of licensed seats |
| mrr_cents | INTEGER | Monthly-normalized MRR for this subscription |
| discount_id | UUID FK → discounts | NULL if no discount |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Key note:** `mrr_cents` = monthly-normalized value. For annual plans, this is total_annual_value / 12.

---

### subscription_items

Add-ons and per-seat charges within a subscription.

| Column | Type | Notes |
|---|---|---|
| item_id | UUID PK | |
| subscription_id | UUID FK → subscriptions | |
| plan_id | UUID FK → plans | |
| quantity | INTEGER | Seats or units |
| unit_price_cents | INTEGER | |
| total_price_cents | INTEGER | quantity × unit_price_cents |
| started_at | DATE | |
| ended_at | DATE | NULL if active |
| created_at | TIMESTAMPTZ | |

---

### invoices

One invoice per billing cycle per subscription.

| Column | Type | Notes |
|---|---|---|
| invoice_id | UUID PK | |
| customer_id | UUID FK → customers | |
| subscription_id | UUID FK → subscriptions | |
| invoice_number | VARCHAR(50) | Human-readable (INV-XXXXXX) |
| status | VARCHAR(50) | draft / open / paid / void / uncollectible |
| billing_period_start | DATE | |
| billing_period_end | DATE | |
| subtotal_cents | INTEGER | Before discounts |
| discount_amount_cents | INTEGER | |
| tax_cents | INTEGER | |
| total_cents | INTEGER | Final amount due |
| amount_paid_cents | INTEGER | |
| amount_due_cents | INTEGER | Remaining balance |
| issued_at | TIMESTAMPTZ | |
| due_at | TIMESTAMPTZ | |
| paid_at | TIMESTAMPTZ | NULL if unpaid |
| created_at | TIMESTAMPTZ | |

---

### invoice_line_items

| Column | Type | Notes |
|---|---|---|
| line_item_id | UUID PK | |
| invoice_id | UUID FK → invoices | |
| subscription_item_id | UUID FK → subscription_items | |
| description | TEXT | |
| quantity | INTEGER | |
| unit_price_cents | INTEGER | |
| amount_cents | INTEGER | |
| created_at | TIMESTAMPTZ | |

---

### payments

Payment attempts against invoices. Multiple attempts allowed per invoice.

| Column | Type | Notes |
|---|---|---|
| payment_id | UUID PK | |
| invoice_id | UUID FK → invoices | |
| customer_id | UUID FK → customers | |
| amount_cents | INTEGER | |
| currency | VARCHAR(10) | Default: USD |
| status | VARCHAR(50) | succeeded / failed / pending / refunded |
| payment_method | VARCHAR(50) | card / ach / wire |
| failure_reason | VARCHAR(255) | NULL if succeeded |
| attempted_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

---

### refunds

| Column | Type | Notes |
|---|---|---|
| refund_id | UUID PK | |
| payment_id | UUID FK → payments | |
| customer_id | UUID FK → customers | |
| amount_cents | INTEGER | |
| reason | VARCHAR(255) | duplicate / fraudulent / requested_by_customer |
| status | VARCHAR(50) | pending / succeeded / failed |
| issued_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

---

### discounts

| Column | Type | Notes |
|---|---|---|
| discount_id | UUID PK | |
| customer_id | UUID FK → customers | |
| coupon_code | VARCHAR(100) | |
| discount_type | VARCHAR(50) | percentage / fixed_amount |
| discount_value | NUMERIC(5,2) | % or cents |
| duration | VARCHAR(50) | once / repeating / forever |
| duration_months | INTEGER | NULL if once/forever |
| valid_from | DATE | |
| valid_until | DATE | NULL if forever |
| created_at | TIMESTAMPTZ | |

---

### product_usage

Monthly snapshots of feature usage per customer. Core churn signal.

| Column | Type | Notes |
|---|---|---|
| usage_id | UUID PK | |
| customer_id | UUID FK → customers | |
| product_id | UUID FK → products | |
| month | DATE | First day of the month |
| active_users | INTEGER | DAU/MAU proxy |
| sessions_count | INTEGER | Total sessions in month |
| features_used_count | INTEGER | Distinct features used |
| api_calls | INTEGER | API usage volume |
| data_exported_mb | NUMERIC | Export activity |
| report_views | INTEGER | |
| created_at | TIMESTAMPTZ | |

**Behavioral pattern:** Usage declines 2–4 months before churn in realistic scenarios.

---

### support_tickets

| Column | Type | Notes |
|---|---|---|
| ticket_id | UUID PK | |
| customer_id | UUID FK → customers | |
| category | VARCHAR(100) | billing / technical / feature_request / onboarding |
| priority | VARCHAR(50) | low / medium / high / critical |
| status | VARCHAR(50) | open / in_progress / resolved / closed |
| subject | TEXT | |
| opened_at | TIMESTAMPTZ | |
| resolved_at | TIMESTAMPTZ | NULL if open |
| resolution_time_hours | NUMERIC | |
| csat_score | INTEGER | 1–5, NULL if not rated |
| created_at | TIMESTAMPTZ | |

**Behavioral pattern:** High-priority billing tickets spike before churn.

---

## Analytics Schema (Phase 3)

Built as SQL views/materialized views on top of raw tables.

| Model | Description |
|---|---|
| customer_overview | One row per customer — segment, MRR, tenure, status |
| subscription_details | Enriched subscription view with plan and product info |
| invoice_details | Invoice + payment status joined |
| monthly_revenue_overview | MRR/ARR by month, segment, product |
| mrr_movement_report | New / expansion / contraction / churn / reactivation per customer per month |
| cohort_retention | % of each monthly cohort retained at months 1–24 |
| customer_churn_risk | Risk scores based on usage trends, payment failures, support tickets |
| customer_health_scores | Composite health score per customer |
