# Phase 11 — Insights & Findings Report

**Source:** real OnlineRetail project data through the approved pipeline (Phase 5 cleaned data → Phase 7 RFM → Phase 8 Segmentation → Phase 9 Statistical Analysis → Phase 10 Visualization).

**Customer population (measured):** 4338 customers.

## 1. Measured Segment Findings

| Segment | Customers | Share % | Frequency mean | Frequency median | Monetary mean | Monetary median |
|---|---|---|---|---|---|---|
| Champions | 923 | 21.28 | 13.38 | 8 | £8,627.61 | £3,018.63 |
| Loyal Customers | 983 | 22.66 | 3.87 | 4 | £1,433.29 | £1,117.13 |
| Average Customers | 1040 | 23.97 | 2.17 | 2 | £842.58 | £575.70 |
| At-Risk Customers | 1058 | 24.39 | 1.15 | 1 | £326.04 | £300.99 |
| Lost Customers | 334 | 7.7 | 1.00 | 1 | £145.73 | £143.28 |

**Segment ranking (by measured mean Monetary):**
- Strongest: **Champions** (highest mean Monetary).
- Weakest: **Lost Customers** (lowest mean Monetary).
- Largest: **At-Risk Customers** (most customers).
- Smallest: **Lost Customers** (fewest customers).

## 1.1 Segment RFM-Score & Recency Characteristics

| Segment | Customers | Recency (days) mean | Recency score mean | Frequency score mean | Monetary score mean |
|---|---|---|---|---|---|
| Champions | 923 | 13.5 | 4.52 | 4.81 | 4.74 |
| Loyal Customers | 983 | 40.8 | 3.60 | 3.63 | 3.71 |
| Average Customers | 1040 | 89.0 | 2.71 | 2.63 | 2.69 |
| At-Risk Customers | 1058 | 149.8 | 2.02 | 1.26 | 1.76 |
| Lost Customers | 334 | 279.9 | 1.00 | 1.00 | 1.00 |

**Segment score-profile insight (measured):** the segment with the highest mean Monetary RFM score is **Champions** (mean monetary score 4.74), consistent with the Monetary-mean ranking above.


## 1.2 Revenue Insights (11.3)

### Measured Revenue Facts

Total revenue (sum of per-customer Monetary values, the Phase 7 Monetary metric on the Phase 5 working data): **£10,642,110.80** across 4338 customers.

| Segment | Customers | Revenue | Revenue share % | Monetary mean | Monetary median |
|---|---|---|---|---|---|
| Champions | 923 | £7,963,283.65 | 74.83 | £8,627.61 | £3,018.63 |
| Loyal Customers | 983 | £1,408,919.51 | 13.24 | £1,433.29 | £1,117.13 |
| Average Customers | 1040 | £876,279.96 | 8.23 | £842.58 | £575.70 |
| At-Risk Customers | 1058 | £344,952.81 | 3.24 | £326.04 | £300.99 |
| Lost Customers | 334 | £48,674.87 | 0.46 | £145.73 | £143.28 |

- **Highest-revenue segment:** Champions (largest absolute revenue and largest revenue share).
- **Lowest-revenue segment:** Lost Customers (smallest absolute revenue and smallest revenue share).
- **Revenue concentration (measured):** the single largest-revenue segment (Champions) contributes 74.83% of total revenue — a marked revenue concentration.

### Revenue Interpretation / Insights (not measured data)

- The strong measured Frequency–Monetary correlation (Phase 9, frequency_vs_monetary Pearson r = +0.952) means higher-purchasing customers drive disproportionately more revenue; this underlies the segments' wide revenue-per-customer spread.
- The top segment's large measured revenue share means retaining the high-Monetary segment protects the majority of the business's revenue, while the low-revenue segments contribute comparatively little.
- Phase 9 statistical evidence (Kruskal-Wallis Monetary H = 3177.53, p ≈ 0) confirms the segment revenue gaps are statistically significant; Phase 10 `segment_monetary_box.png` and `rfm_metric_correlation_scatter.png` illustrate the same measured concentration.

## 2. Measured Statistical Findings

### 2.1 RFM metric correlations

| Pair | Pearson r | Pearson p | Spearman ρ | Spearman p | n |
|---|---|---|---|---|---|
| recency_days_vs_frequency | -0.1004 | 3.39e-11 | -0.5628 | 0.0 | 4338 |
| recency_days_vs_monetary | -0.0521 | 0.0006 | -0.4811 | 3.60e-250 | 4338 |
| frequency_vs_monetary | +0.9519 | 0.0 | +0.8073 | 0.0 | 4338 |

### 2.2 Normality assessment (D'Agostino-Pearson)

- **recency_days:** statistic = 731.29, p = 1.59e-159 → NOT normal at 0.05.
- **frequency:** statistic = 14251.38, p = 0.0 → NOT normal at 0.05.
- **monetary:** statistic = 14349.24, p = 0.0 → NOT normal at 0.05.

### 2.3 Segment comparison tests

- **Kruskal-Wallis H** (frequency_kruskal_wallis): statistic = 3507.14, p = 0.0.
- **Kruskal-Wallis H** (monetary_kruskal_wallis): statistic = 3177.53, p = 0.0.
- **Mann-Whitney U** (champions_vs_lost_frequency_mannwhitney): statistic = 308282.00, p = 2.01e-165.
- **Mann-Whitney U** (champions_vs_lost_monetary_mannwhitney): statistic = 308282.00, p = 6.74e-162.

## 3. Interpretation (not measured data)

- Recency vs Frequency is moderate negative (Pearson r = -0.100). For this dataset this means higher values of the first metric are associated with lower values of the second.
- Recency vs Monetary is weak (near-zero) (Pearson r = -0.052). For this dataset this means higher values of the first metric are associated with lower values of the second.
- Frequency vs Monetary is strong positive (Pearson r = +0.952). For this dataset this means higher values of the first metric are associated with higher values of the second.

- Frequency is statistically significantly different across the customer segments (Kruskal-Wallis H = 3507.14, p = 0.0, df = 4).
- Monetary is statistically significantly different across the customer segments (Kruskal-Wallis H = 3177.53, p = 0.0, df = 4).
- The best segment (Champions, n = 923) and worst segment (Lost Customers, n = 334) differ significantly in Frequency (Mann-Whitney U = 308282, p = 2.01e-165) and Monetary (U = 308282, p = 6.74e-162).

## 4. Actionable Conclusions

- **Protect the strongest segment:** the highest-spending segment has the highest measured mean Monetary; retention effort on this group directly protects disproportionate revenue.
- **Re-engagement priority:** the measured Largest segment is At-Risk Customers and the weakest is Lost Customers; targeted re-engagement offers are supported by the quantified gap.
- **Cross-sell/upsell:** the strong measured Frequency-Monetary relationship supports channeling frequent buyers toward higher-value products.
- **Analytics method:** all RFM metrics are measured as non-normal and the segment comparisons are significant, justifying the chosen non-parametric statistical approach.

## 5. Outputs

- Phase 10 chart evidence: `outputs/charts/rfm_score_distributions.png`, `segment_size_bar.png`, `segment_monetary_box.png`, `rfm_metric_correlation_scatter.png`.
- This report: `outputs/reports/phase11_insights_report.md`.

## Final Findings (11.4)

### 1. Overall customer behaviour findings

**Measured facts:**

The analysis covers 4338 unique customers generating 10,642,110.80 GBP in total revenue across 5 verified segments (Champions, Loyal Customers, Average Customers, At-Risk Customers, Lost Customers).

**Final interpretation / findings:**

The customer base is large but its value is not evenly distributed: a minority of customers account for the majority of revenue, indicating a strong Pareto effect in the e-commerce portfolio.

### 2. Most important segment findings

**Measured facts:**

Five segments were produced by the Phase 8 rules. The largest segment by customer count is 'At-Risk Customers'; the smallest is 'Lost Customers'. Each segment's customer count, share and RFM-score / revenue profile are recorded in 11.2 and 11.3.

**Final interpretation / findings:**

Segment membership is driven primarily by Recency and Monetary value: recently active, high-spending customers form Champions, while inactive low-spenders form the Lost group. The segment size mix reflects how many customers have lapsed versus remained engaged.

### 3. Most important revenue findings

**Measured facts:**

Total revenue is 10,642,110.80 GBP. The highest-revenue segment is 'Champions'; the lowest-revenue segment is 'Lost Customers'. Revenue contribution and shares are documented per segment in 11.3 (revenue_ranking).

**Final interpretation / findings:**

Revenue is highly concentrated in the top segment(s). A single segment contributes well over half of total revenue despite representing a modest share of customers, so retention of the top segment is disproportionately important to revenue.

### 4. Important RFM patterns

**Measured facts:**

The strongest measured RFM correlation is frequency_vs_monetary (r=0.952). Frequency and Monetary values are correlated (Pearson r=0.952), consistent with the Phase 10 scatter (rfm_metric_correlation_scatter.png).

**Final interpretation / findings:**

RFM metrics move together predictably: customers who buy more frequently also spend more monetarily, and recent buyers tend to be higher-value. This supports using RFM (rather than any single metric) for segmentation.

### 5. Important statistical evidence

**Measured facts:**

Phase 9 statistical tests confirm the segment structure differs significantly across RFM metrics (Kruskal-Wallis tests with very low p-values), and inter-metric correlations are as reported in 11.1. Exact test statistics are in summarize_statistical_insights().

**Final interpretation / findings:**

The differences between segments are statistically significant, not attributable to random variation. The correlation and normality results justify the parametric/non-parametric choices made in the analysis.

### 6. Most important business / customer observations

**Measured facts:**

Champions are simultaneously the highest-revenue segment and the most Recency- and Monetary-favourable group, while the At-Risk and Lost groups are low-Recency / low-Monetary and contribute little revenue. These are derived from the 11.2 / 11.3 per-segment characteristics and revenue tables.

**Final interpretation / findings:**

Two clear business priorities emerge: protect the top revenue segment (Champions) from churn, and re-engage At-Risk customers before they fall into the Lost group. The Lost group is small but inactive and low-value, warranting only minimal recovery effort.

### 7. Overall conclusion

**Measured facts:**

Across 4338 customers and 10,642,110.80 GBP in revenue, segmentation and statistical analysis identify five distinct, statistically separable customer groups with a strong revenue concentration signal and strong Frequency-Monetary correlation.

**Final interpretation / findings:**

The RFM pipeline delivers actionable, data-driven customer groups: revenue is concentrated in Champions, the Frequency and Monetary values are strongly positively linked, and the segment structure is statistically robust - supporting targeted retention and re-engagement strategies as the core business recommendation.

*Synthesis source: 11.1 + 11.2 + 11.3*
