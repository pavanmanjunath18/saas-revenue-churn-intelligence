-- ============================================================
-- analytics.invoice_details
-- One row per invoice. Enriched with customer, subscription,
-- plan, and payment context. Useful for AR and billing analysis.
-- ============================================================

CREATE OR REPLACE VIEW analytics.invoice_details AS
SELECT
    i.invoice_id,
    i.invoice_number,
    i.customer_id,
    c.company_name,
    c.segment,
    i.subscription_id,
    pl.plan_name,
    s.billing_interval,

    -- Invoice status & dates
    i.status                                        AS invoice_status,
    i.billing_period_start,
    i.billing_period_end,
    i.issued_at,
    i.due_at,
    i.paid_at,

    -- Amounts
    ROUND(i.subtotal_cents           / 100.0, 2)   AS subtotal_usd,
    ROUND(i.discount_amount_cents    / 100.0, 2)   AS discount_usd,
    ROUND(i.tax_cents                / 100.0, 2)   AS tax_usd,
    ROUND(i.total_cents              / 100.0, 2)   AS total_usd,
    ROUND(i.amount_paid_cents        / 100.0, 2)   AS amount_paid_usd,
    ROUND(i.amount_due_cents         / 100.0, 2)   AS amount_due_usd,

    -- Derived
    CASE WHEN i.status = 'paid' THEN TRUE ELSE FALSE END    AS is_paid,
    CASE WHEN i.amount_due_cents > 0 THEN TRUE ELSE FALSE END AS has_outstanding_balance,
    DATE_PART('day', i.paid_at - i.issued_at)::int          AS days_to_pay,

    -- Payment attempt count
    COALESCE(p.attempt_count, 0)                            AS payment_attempts,
    COALESCE(p.failed_attempts, 0)                          AS failed_payment_attempts

FROM raw.invoices i
JOIN raw.customers      c  ON i.customer_id     = c.customer_id
JOIN raw.subscriptions  s  ON i.subscription_id = s.subscription_id
JOIN raw.plans          pl ON s.plan_id         = pl.plan_id
LEFT JOIN (
    SELECT
        invoice_id,
        COUNT(*)                                        AS attempt_count,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)  AS failed_attempts
    FROM raw.payments
    GROUP BY invoice_id
) p ON i.invoice_id = p.invoice_id
WHERE c.is_deleted = FALSE;
