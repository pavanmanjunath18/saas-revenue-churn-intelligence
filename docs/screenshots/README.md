# Dashboard Screenshots Guide — SaaS Revenue & Churn Intelligence

To make your GitHub repository look outstanding and give recruiters/reviewers immediate visual proof of your frontend development capabilities, we recommend capturing high-quality screenshots of the interactive Streamlit dashboard.

Follow these simple instructions to capture and save the perfect images for your root `README.md` showcase.

---

## Setup & Launching the Dashboard

1. **Ensure your database is active and compiled:**
   ```bash
   docker compose up -d
   python scripts/build_analytics.py
   ```

2. **Launch the Streamlit app:**
   ```bash
   streamlit run dashboards/streamlit_app.py
   ```
   *The app should automatically open in your browser at `http://localhost:8501`.*

---

## Recommended Screenshots to Capture

### 1. Revenue Overview Dashboard (`revenue_overview.png`)
* **Page in App:** `Revenue Overview` (First/landing page)
* **What to focus on:**
  * Keep the sidebar expanded so viewers can see the filters (Customer Segment, Plan Type, Billing Interval, Date Range).
  * Capture the top row of **KPI cards**: Ending MRR, ARR, Active Customers, ARPA.
  * Capture the beautiful **Monthly MRR Growth & Components chart** (showing New, Expansion, Churn, Contraction, and Net MRR trends).
  * Capture the **NRR & GRR Retention Trends chart** displaying the healthy customer retention profile.
* **Saving destination:** Save as `docs/screenshots/revenue_overview.png`

### 2. Cohort Retention Matrix (`cohort_analysis.png`)
* **Page in App:** `Cohort Analysis` (Select in sidebar)
* **What to focus on:**
  * Scroll so the interactive **Cohort Retention Triangle Heatmap** is fully visible.
  * The heatmap displays cohort signup months down the y-axis, and active months (M0 to M12) across the x-axis, color-coded from vibrant green to cool grey/blue.
  * Capture the average cohort retention line chart directly below the heatmap.
* **Saving destination:** Save as `docs/screenshots/cohort_analysis.png`

### 3. Customer Churn Analysis (`churn_analysis.png`)
* **Page in App:** `Churn Analysis` (Select in sidebar)
* **What to focus on:**
  * Capture the high-level metrics: Logo Churn Rate vs. Revenue Churn Rate.
  * Highlight the **Churn Risk Breakdown** and the **Failed Payment Impact chart** which shows the high correlation between payment failures and customer attrition.
* **Saving destination:** Save as `docs/screenshots/churn_analysis.png`

### 4. Customer Health & Segmentation (`customer_health.png`)
* **Page in App:** `Customer Health` (Select in sidebar)
* **What to focus on:**
  * Capture the **Composite Health Score distribution** (low risk, medium risk, critical risk tiers).
  * Show the interactive **At-Risk Customer Playbook Table**, which highlights active accounts with declining usage, open high-severity support tickets, or billing dunning flags, complete with recommended CSM playbooks.
* **Saving destination:** Save as `docs/screenshots/customer_health.png`

---

## Tips for Professional Screenshots

* **Clean Browser Environment:** Hide your bookmark bar, address bar, and browser tabs. For best results, use **full-screen screenshotting** (e.g., `Cmd + Shift + 4` then spacebar on Mac to capture the exact browser window with clean borders).
* **Consistent Resolution:** Scale your browser window to a standard desktop layout (e.g., `1920x1080` equivalent) to keep text sharp and charts balanced.
* **Aspect Ratio:** Keep the aspect ratio close to 16:9 for clean responsive embedding in standard markdown files.
* **Dark Mode vs. Light Mode:** Streamlit will match your system default. The styling is optimized for a premium dark mode, which renders high-contrast gradients that wow portfolio reviewers.

---

## Staging & Committing

Once you've captured your PNG files and saved them in this `docs/screenshots/` folder, they are already tracked by `.gitignore` to be committed. Simply add them to your commit and they will render perfectly inside the main `README.md` and `docs/dashboard_guide.md`!

```bash
git add docs/screenshots/*.png
git commit -m "docs: add dashboard screenshots for portfolio showcase"
```
