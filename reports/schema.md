# Relational Data Warehouse Schema Diagram

This diagram displays the analytical Star Schema structure built inside `data/airbnb_warehouse.db`.

```mermaid
erDiagram
    dim_listings {
        BIGINT listing_id PK
        VARCHAR city
        BIGINT host_id FK
        VARCHAR neighbourhood_id FK
        VARCHAR room_type
        VARCHAR property_type
        DOUBLE latitude
        DOUBLE longitude
        INTEGER accommodates
        INTEGER bedrooms
        INTEGER beds
        DOUBLE price
        DOUBLE review_rating
        VARCHAR license
        VARCHAR regulatory_status
    }

    dim_hosts {
        BIGINT host_id PK
        VARCHAR host_name
        DATE host_since
        BOOLEAN is_superhost
        INTEGER total_host_listings
    }

    dim_neighbourhoods {
        VARCHAR neighbourhood_id PK
        VARCHAR city
        VARCHAR neighbourhood_name
        VARCHAR neighbourhood_group
    }

    fact_reviews {
        BIGINT review_id PK
        BIGINT listing_id FK
        VARCHAR city
        DATE review_date
    }

    dim_hosts ||--o{ dim_listings : "supplies"
    dim_neighbourhoods ||--o{ dim_listings : "contains"
    dim_listings ||--o{ fact_reviews : "receives"