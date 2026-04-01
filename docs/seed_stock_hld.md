# Seed Stock High-Level Design (HLD) & Schema Plan

## Overview
The TN AgriNet Seed Stock domain consists of four subsections. Three of these (Agriculture, Horticulture, Season-Wise) share a CodeIgniter/AngularJS architecture where data is fetched via stateful form POSTs and rendered into the `ng-init` attribute as JSON. The fourth (Horticulture Farm/Park) is a completely separate HTML DataTables interface hosted on `tnhorticulture.com`.

This HLD defines the parser strategy and the generalized data schema to handle these variations cleanly.

---

## 1. Parser Logic & Scraping Criteria

We will implement a unified `SeedController` that delegates to specific parsers based on the subsection. 

### A. Shared AngularJS Subsections (Agri, Horti, Season-Wise)
**Characteristics**:
- **Interface**: Dependent dropdowns (District → Block → [Crop/Stock Type/Season]).
- **Network**: Requires a valid `ci_session` cookie. 
- **Retrieval**: Search results are embedded inside the HTML payload within the `ng-init` attribute (e.g., `seed_list=[...]` or `cocn_list=[...]`).

**Parsing Strategy (`BaseAngularSeedParser`)**:
1. **Initialize Session**: Perform an initial `GET` to the entry URL (e.g., `/Seed/seed_gov/en`) to capture the CSRF session cookie.
2. **Fetch Dependencies**: 
   - Parse the HTML to extract available districts.
   - For each district, `POST /Seed/getBlocks/{id}` to get blocks.
3. **Execute Search**:
   - For each block/crop/season combination, `POST` to the result endpoint (`/Seed/result/en` or `/Season/result/en`).
4. **Extract JSON via Regex**:
   - Instead of parsing the HTML UI, use regex to extract the raw JSON: `re.search(r"seed_list\s*=\s*(\[.*?\])\s*[;'\"]", html, re.DOTALL)`.
   - Parse with `json.loads()` directly into python dictionaries.
5. **Checkpointing**: Checkpoint at the **Block** level (`district:{id}:block:{id}`) to ensure the scraper is resumable without dropping session context mid-loop.

### B. Horticulture Farm / Park Stocks
**Characteristics**:
- **Interface**: Static HTML table with DataTables.js pagination.
- **Network**: Stateless. No session or CSRF required.
- **URL Pattern**: `tnhorticulture.com/farm_inputs/Report/report/{category_id}/en`

**Parsing Strategy (`HortiFarmParser`)**:
1. **Fetch Pages**: Loop linearly through known category IDs (1 to N) using standard `requests.get()` via our `retry_request` wrapper.
2. **DOM Parsing**: Extract the `<tbody>` using BeautifulSoup.
3. **Table Row Extraction**: Iterate `<tr>` and extract standard columns (District, Park Name, Category, Sub-Category, Total Stock, Price).
4. **Checkpointing**: Checkpoint at the **Category** level (`category:{id}`).

---

## 2. Data Schema & Storage Architecture

Because the data shapes differ between general Seed variables and Farm/Park specific details, we will introduce two generic database tables rather than forcefully merging them.

### Table 1: `seed_stocks`
Designed to handle data from the Agriculture, Horticulture (general), and Season-wise endpoints.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-incrementing primary key |
| `scrape_run_id` | Integer (FK) | Link to `scrape_runs` for audit/rollback |
| `district_code` | String | District identifier |
| `block_code` | String | Block identifier |
| `source_type` | Enum | `agri`, `horti`, or `season` |
| `crop_name` | String | Extracted crop name / stock type |
| `crop_variety` | String | Specific variety of the seed |
| `agency_name` | String | e.g., 'Govt', 'Private', or specific dealer |
| `quantity_available` | Float | Number representing available stock |
| `unit` | String | e.g. 'MT', 'Kgs', 'Nos' |
| `scrape_date` | Date | The date the scrape occurred |

**Constraint**: `UNIQUE(block_code, crop_name, crop_variety, agency_name, scrape_date)`

---

### Table 2: `horti_farm_stocks`
Designed strictly for the `tnhorticulture.com` Farm/Park dataset.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-incrementing primary key |
| `scrape_run_id` | Integer (FK) | Link to `scrape_runs` for audit/rollback |
| `district_name` | String | Raw district name from table |
| `farm_name` | String | Name of the Park / Farm |
| `category` | String | e.g. 'Fruit seedlings' |
| `sub_category` | String | e.g. 'Mango - Alphonso' |
| `total_stock` | Integer | Total count available |
| `stock_for_sales`| Integer | Stock specifically for direct sales |
| `rate_per_stock` | Float | Price per item |
| `contact_name` | String | Name of the contact person |
| `scrape_date` | Date | The date the scrape occurred |

**Constraint**: `UNIQUE(farm_name, category, sub_category, scrape_date)`

---

## 3. Implementation Steps

1. **Alembic Migration**: Generate a migration for the two new models (`SeedStock` and `HortiFarmStock`).
2. **Model Definitions**: Add to `tfais/database/models.py`.
3. **Operations**: Add `insert_seed_batch` and `insert_horti_farm_batch` to `tfais/database/operations.py`.
4. **Parser Implementation**:
   - Build `SeedController`
   - Implement `AgriSeedParser` (template for shared logic)
   - Implement `HortiFarmParser`
5. **CLI Integration**: Update `main.py` so `--section seed --subsection agri` correctly routes to the new controller.
