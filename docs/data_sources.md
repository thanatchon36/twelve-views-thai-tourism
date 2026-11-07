# Data sources: the shopping list

Every file in `data/raw/` is **synthetic** (`synthetic_*.csv`). To run the pipeline on real data, put a file named
`data/raw/<dataset>.csv` with the same columns next to its synthetic stand-in; the loader
(`twelveviews.loaders`) then uses the real file and stops warning about it. Any subset works: datasets without a
real file keep falling back to the synthetic one, with a warning on every run. Then run `make all`.

The numbers, tables and figures update automatically. The interpretive text in `paper/paper.tex` was written about
the synthetic data and must be revised by hand.

## The datasets

| Dataset | Rows (synthetic) | Columns | Content |
|---|---:|---|---|
| `arrivals_by_nationality` | 272 | `year, nationality, origin_region, region_id, kind, arrivals` | Annual international arrivals by market, 2010–2025 (`kind` = named market or residual group) |
| `arrivals_monthly` | 192 | `month, arrivals` | Monthly international arrivals, all markets (`month` as `YYYY-MM`) |
| `stay_length` | 270 | `nationality, origin_region, region_id, nights, share` | Distribution of nights per trip by market (shares sum to one per market) |
| `nationality_profiles` | 15 | `nationality, origin_region, region_id, spend_per_day, avg_nights, repeat_share, independent_share, beach_share, median_age` | Behavioural profiles of fifteen markets |
| `trip_flows` | 144 | `origin_region, region_id, destination, dest_id, style, style_id, travelers` | Origin region → main destination → trip style, latest year |
| `region_flows` | 30 | `from, from_id, to, to_id, travelers` | Onward trips between six destination clusters |
| `provinces` | 77 | `province, thai_region, thai_region_id, foreign_visitors, spend_per_visitor, revenue_mb` | Foreign visitors, spend per visitor (THB) and revenue (THB million) for all 77 provinces |
| `province_covisits` | 76 | `province_a, province_b, trips` | Pairs of provinces visited on the same trip |
| `spending_breakdown` | 21 | `category, cat_id, subcategory, item, share` | Three-level structure of visitor spending |
| `traveler_segments` | 1,200 | `x, y, segment, segment_id, origin_region, region_id, spend_per_day, nights, age, group_size` | Individual survey responses with t-SNE coordinates and (planted) persona |
| `traveler_features` | 1,200 | `log_spend, nights, age, group, beach, shopping, culture, nightlife` | Standardised features of the same respondents, the input to t-SNE and k-means |

`data/raw/synthetic_manifest.json` records the rows, columns and description of the ten main datasets.

## Where real counterparts come from

From Table 6 of the paper. These are kinds of source, not endorsements of a particular publisher; check the
licence and definitions of whatever you use.

| Synthetic dataset | Candidate source | Caveats |
|---|---|---|
| `arrivals_by_nationality`, `arrivals_monthly` | Official monthly statistics of international arrivals by nationality | Definitions of arrivals versus tourists differ |
| `stay_length`, `nationality_profiles`, `spending_breakdown` | Surveys of visitor behaviour and expenditure | Sampling weights and survey error must be reported |
| `trip_flows`, `region_flows`, `province_covisits` | Mobile positioning, card-payment or booking data | Privacy; aggregation required before use |
| `provinces` | Provincial statistics on visitors and tourism receipts | Definitions of revenue vary by source |
| `traveler_segments`, `traveler_features` | Individual-level visitor surveys | Ethical review required |

Flows and co-visitation are usually the hardest to obtain, because they need individual-level mobility data that
must be aggregated before use. With real survey data, `traveler_segments.segment` holds whatever grouping you want
to compare the k-means clusters against; the persona-recovery statistic (E8) is only meaningful where such a
reference grouping exists.
