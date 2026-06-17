# Data Quality & Profiling Diagnostics Report

**Target Market Analysis:** Barcelona
Generated using High-Performance Polars Core Engine.

## Detailed Listings Data (`listings.csv.gz`)
* **Total Observations (Rows):** 18,177
* **Total Attributes (Columns):** 85

### Column Structural Diagnostics

| Column Name | Data Type | Null Count | Null % | Unique Count |
| :--- | :--- | :--- | :--- | :--- |
| id | Int64 | 0 | 0.00% | 18,177 |
| listing_url | String | 0 | 0.00% | 18,177 |
| scrape_id | Int64 | 0 | 0.00% | 1 |
| last_scraped | String | 0 | 0.00% | 2 |
| source | String | 0 | 0.00% | 2 |
| name | String | 0 | 0.00% | 17,353 |
| description | String | 627 | 3.45% | 14,475 |
| neighborhood_overview | String | 18,177 | 100.00% | 1 |
| picture_url | String | 0 | 0.00% | 17,954 |
| host_id | Int64 | 0 | 0.00% | 5,776 |
| host_url | String | 0 | 0.00% | 5,776 |
| host_profile_id | Int64 | 0 | 0.00% | 5,775 |
| host_profile_url | String | 0 | 0.00% | 5,773 |
| host_name | String | 6 | 0.03% | 2,874 |
| host_since | String | 6 | 0.03% | 3,271 |
| hosts_time_as_user_years | Int64 | 6 | 0.03% | 19 |
| hosts_time_as_user_months | Int64 | 6 | 0.03% | 13 |
| hosts_time_as_host_years | Int64 | 6 | 0.03% | 16 |
| hosts_time_as_host_months | Int64 | 6 | 0.03% | 13 |
| host_location | String | 4,263 | 23.45% | 385 |
| host_about | String | 4,193 | 23.07% | 2,846 |
| host_response_time | String | 6 | 0.03% | 6 |
| host_response_rate | String | 6 | 0.03% | 62 |
| host_acceptance_rate | String | 6 | 0.03% | 97 |
| host_is_superhost | String | 0 | 0.00% | 2 |
| host_thumbnail_url | String | 6 | 0.03% | 5,585 |
| host_picture_url | String | 6 | 0.03% | 5,606 |
| host_neighbourhood | String | 9,791 | 53.86% | 131 |
| host_listings_count | Int64 | 6 | 0.03% | 110 |
| host_total_listings_count | Int64 | 6 | 0.03% | 137 |
| host_verifications | String | 0 | 0.00% | 9 |
| host_has_profile_pic | String | 6 | 0.03% | 3 |
| host_identity_verified | String | 6 | 0.03% | 3 |
| neighbourhood | String | 18,177 | 100.00% | 1 |
| neighbourhood_cleansed | String | 0 | 0.00% | 71 |
| neighbourhood_group_cleansed | String | 0 | 0.00% | 10 |
| latitude | Float64 | 0 | 0.00% | 9,878 |
| longitude | Float64 | 0 | 0.00% | 10,713 |
| property_type | String | 0 | 0.00% | 52 |
| room_type | String | 0 | 0.00% | 4 |
| accommodates | Int64 | 0 | 0.00% | 16 |
| bathrooms | Float64 | 3,558 | 19.57% | 24 |
| bathrooms_text | String | 9 | 0.05% | 39 |
| bedrooms | Int64 | 1,649 | 9.07% | 24 |
| beds | Int64 | 3,632 | 19.98% | 35 |
| amenities | String | 0 | 0.00% | 15,204 |
| price | String | 18,177 | 100.00% | 1 |
| minimum_nights | Int64 | 0 | 0.00% | 75 |
| maximum_nights | Int64 | 0 | 0.00% | 196 |
| minimum_minimum_nights | Int64 | 8 | 0.04% | 81 |
| maximum_minimum_nights | Int64 | 8 | 0.04% | 100 |
| minimum_maximum_nights | Int64 | 8 | 0.04% | 190 |
| maximum_maximum_nights | Int64 | 8 | 0.04% | 193 |
| minimum_nights_avg_ntm | Float64 | 0 | 0.00% | 528 |
| maximum_nights_avg_ntm | Float64 | 0 | 0.00% | 1,250 |
| calendar_updated | String | 18,177 | 100.00% | 1 |
| has_availability | String | 1,024 | 5.63% | 2 |
| availability_30 | Int64 | 0 | 0.00% | 31 |
| availability_60 | Int64 | 0 | 0.00% | 61 |
| availability_90 | Int64 | 0 | 0.00% | 91 |
| availability_365 | Int64 | 0 | 0.00% | 366 |
| calendar_last_scraped | String | 0 | 0.00% | 2 |
| number_of_reviews | Int64 | 0 | 0.00% | 655 |
| number_of_reviews_ltm | Int64 | 0 | 0.00% | 188 |
| number_of_reviews_l30d | Int64 | 0 | 0.00% | 36 |
| availability_eoy | Int64 | 0 | 0.00% | 19 |
| number_of_reviews_ly | Int64 | 0 | 0.00% | 176 |
| estimated_occupancy_l365d | Int64 | 0 | 0.00% | 90 |
| estimated_revenue_l365d | String | 18,177 | 100.00% | 1 |
| first_review | String | 5,082 | 27.96% | 3,819 |
| last_review | String | 5,082 | 27.96% | 1,828 |
| review_scores_rating | Float64 | 5,082 | 27.96% | 158 |
| review_scores_accuracy | Float64 | 5,085 | 27.97% | 152 |
| review_scores_cleanliness | Float64 | 5,084 | 27.97% | 169 |
| review_scores_checkin | Float64 | 5,086 | 27.98% | 155 |
| review_scores_communication | Float64 | 5,083 | 27.96% | 146 |
| review_scores_location | Float64 | 5,085 | 27.97% | 136 |
| review_scores_value | Float64 | 5,085 | 27.97% | 187 |
| license | String | 7,163 | 39.41% | 9,254 |
| instant_bookable | String | 0 | 0.00% | 2 |
| calculated_host_listings_count | Int64 | 0 | 0.00% | 69 |
| calculated_host_listings_count_entire_homes | Int64 | 0 | 0.00% | 61 |
| calculated_host_listings_count_private_rooms | Int64 | 0 | 0.00% | 35 |
| calculated_host_listings_count_shared_rooms | Int64 | 0 | 0.00% | 9 |
| reviews_per_month | Float64 | 5,082 | 27.96% | 794 |

---

## Detailed Calendar/Availability Data (`calendar.csv.gz`)
* **Total Observations (Rows):** 6,634,623
* **Total Attributes (Columns):** 7

### Column Structural Diagnostics

| Column Name | Data Type | Null Count | Null % | Unique Count |
| :--- | :--- | :--- | :--- | :--- |
| listing_id | Int64 | 0 | 0.00% | 18,177 |
| date | String | 0 | 0.00% | 366 |
| available | String | 0 | 0.00% | 2 |
| price | String | 6,634,623 | 100.00% | 1 |
| adjusted_price | String | 6,634,623 | 100.00% | 1 |
| minimum_nights | Int64 | 0 | 0.00% | 130 |
| maximum_nights | Int64 | 0 | 0.00% | 742 |

---

## Detailed Customer Reviews Data (`reviews.csv.gz`)
* **Total Observations (Rows):** 991,795
* **Total Attributes (Columns):** 6

### Column Structural Diagnostics

| Column Name | Data Type | Null Count | Null % | Unique Count |
| :--- | :--- | :--- | :--- | :--- |
| listing_id | Int64 | 0 | 0.00% | 13,095 |
| id | Int64 | 0 | 0.00% | 991,795 |
| date | String | 0 | 0.00% | 5,025 |
| reviewer_id | Int64 | 0 | 0.00% | 938,974 |
| reviewer_name | String | 0 | 0.00% | 120,330 |
| comments | String | 0 | 0.00% | 947,957 |

---

