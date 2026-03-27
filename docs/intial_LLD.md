



### What to do manually:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>Step 1 → Open http://115.243.209.84/people_app/fertilizer/stock/tm/20/2020</span></span>
<span class="line"><span>Step 2 → Click through every level and document:</span></span>
<span class="line"><span></span></span>
<span class="line"><span>LEVEL 0 (State)</span></span>
<span class="line"><span>  URL pattern:  /stock/tm/...</span></span>
<span class="line"><span>  What it shows: List of districts with summary stock</span></span>
<span class="line"><span></span></span>
<span class="line"><span>LEVEL 1 (District)</span></span>
<span class="line"><span>  URL pattern:  /stock/tm/{district_code}/...</span></span>
<span class="line"><span>  What it shows: List of blocks/circles under that district</span></span>
<span class="line"><span></span></span>
<span class="line"><span>LEVEL 2 (Block/Circle)</span></span>
<span class="line"><span>  URL pattern:  /stock/tm/{district_code}/{block_code}/...</span></span>
<span class="line"><span>  What it shows: List of dealers with fertilizer-wise stock</span></span>
<span class="line"><span></span></span>
<span class="line"><span>LEVEL 3 (Dealer - if exists)</span></span>
<span class="line"><span>  URL pattern:  ...</span></span>
<span class="line"><span>  What it shows: Individual dealer details</span></span></code></pre></div></div></pre>

### Document these things:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>┌──────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│  1. URL pattern at each drill-down level             │</span></span>
<span class="line"><span>│  2. What parameters change (codes, IDs, dates)       │</span></span>
<span class="line"><span>│  3. Is it server-rendered HTML or AJAX/JS loaded?    │</span></span>
<span class="line"><span>│  4. HTML table structure (class names, IDs, nesting) │</span></span>
<span class="line"><span>│  5. Are there hidden form POSTs or query params?     │</span></span>
<span class="line"><span>│  6. Total number of districts (≈38 in TN)            │</span></span>
<span class="line"><span>│  7. Approximate blocks per district                  │</span></span>
<span class="line"><span>│  8. Rate limiting / anti-bot behavior                │</span></span>
<span class="line"><span>└──────────────────────────────────────────────────────┘</span></span></code></pre></div></div></pre>

### Deliverable:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>reconnaissance_notes.md</span></span>
<span class="line"><span></span></span>
<span class="line"><span>Contains:</span></span>
<span class="line"><span>  - Full URL pattern map</span></span>
<span class="line"><span>  - Sample HTML snippets from each level</span></span>
<span class="line"><span>  - Navigation tree diagram</span></span>
<span class="line"><span>  - Any gotchas (JS rendering, sessions, cookies)</span></span></code></pre></div></div></pre>


Folder structure

tfais/
│
├── config/
│   ├── settings.py            # DB credentials, base URLs, timeouts
│   └── .env                   # Secrets (not committed)
│
├── scraper/
│   ├── __init__.py
│   ├── base_scraper.py        # Shared HTTP logic, retry, headers
│   ├── district_scraper.py    # Level 0 → Get all districts
│   ├── block_scraper.py       # Level 1 → Get blocks per district
│   ├── dealer_scraper.py      # Level 2 → Get dealers + stock per block
│   └── url_builder.py         # Construct URLs from codes
│
├── parser/
│   ├── __init__.py
│   ├── table_parser.py        # HTML table → Python dict/list
│   └── data_cleaner.py        # Clean names, handle missing values
│
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models (tables)
│   ├── connection.py          # DB engine + session factory
│   ├── operations.py          # Insert, upsert, query functions
│   └── migrations/            # Alembic migrations (later)
│
├── pipeline/
│   ├── __init__.py
│   └── orchestrator.py        # Ties scraper → parser → DB together
│
├── logs/
│   └── scraper.log
│
├── tests/
│   ├── test_scraper.py
│   ├── test_parser.py
│   └── test_db.py
│
├── main.py                    # Entry point
├── requirements.txt
└── README.md



## Build the Scraper 

### Strategy — Layered Scraping:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>          ┌──────────────────┐</span></span>
<span class="line"><span>          │  START: State     │</span></span>
<span class="line"><span>          │  URL: /tm/...     │</span></span>
<span class="line"><span>          └────────┬─────────┘</span></span>
<span class="line"><span>                   │</span></span>
<span class="line"><span>                   ▼</span></span>
<span class="line"><span>     ┌─────────────────────────┐</span></span>
<span class="line"><span>     │  STEP 1: Get Districts  │</span></span>
<span class="line"><span>     │  Parse table → extract  │</span></span>
<span class="line"><span>     │  district names + codes │</span></span>
<span class="line"><span>     │  Store in districts DB  │</span></span>
<span class="line"><span>     └────────────┬────────────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>          ┌───────┴───────┐</span></span>
<span class="line"><span>          │  For EACH      │</span></span>
<span class="line"><span>          │  district code │</span></span>
<span class="line"><span>          └───────┬───────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>                  ▼</span></span>
<span class="line"><span>     ┌─────────────────────────┐</span></span>
<span class="line"><span>     │  STEP 2: Get Blocks     │</span></span>
<span class="line"><span>     │  URL: /tm/{dist_code}/  │</span></span>
<span class="line"><span>     │  Parse → block names    │</span></span>
<span class="line"><span>     │  + codes                │</span></span>
<span class="line"><span>     │  Store in blocks DB     │</span></span>
<span class="line"><span>     └────────────┬────────────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>          ┌───────┴───────┐</span></span>
<span class="line"><span>          │  For EACH      │</span></span>
<span class="line"><span>          │  block code    │</span></span>
<span class="line"><span>          └───────┬───────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>                  ▼</span></span>
<span class="line"><span>     ┌─────────────────────────────┐</span></span>
<span class="line"><span>     │  STEP 3: Get Dealers+Stock  │</span></span>
<span class="line"><span>     │  URL: /tm/{dist}/{block}/   │</span></span>
<span class="line"><span>     │  Parse → dealer name,       │</span></span>
<span class="line"><span>     │  contact, fertilizer-wise   │</span></span>
<span class="line"><span>     │  quantities                 │</span></span>
<span class="line"><span>     │  Store in dealers +         │</span></span>
<span class="line"><span>     │  fertilizer_stock DB        │</span></span>
<span class="line"><span>     └─────────────────────────────┘</span></span></code></pre></div></div></pre>


### Key Scraper Rules:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>┌──────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                   SCRAPING RULES                         │</span></span>
<span class="line"><span>├──────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                                                          │</span></span>
<span class="line"><span>│  1. RATE LIMIT    → 2-3 second delay between requests   │</span></span>
<span class="line"><span>│  2. RETRY         → 3 attempts with exponential backoff │</span></span>
<span class="line"><span>│  3. TIMEOUT       → 30 seconds per request              │</span></span>
<span class="line"><span>│  4. USER AGENT    → Set a realistic browser UA          │</span></span>
<span class="line"><span>│  5. SESSION       → Reuse connection (cookies/session)  │</span></span>
<span class="line"><span>│  6. LOGGING       → Log every request URL + status      │</span></span>
<span class="line"><span>│  7. CHECKPOINTING → Save progress (resume on failure)   │</span></span>
<span class="line"><span>│  8. VALIDATION    → Verify parsed data before storing   │</span></span>
<span class="line"><span>│                                                          │</span></span>
<span class="line"><span>└──────────────────────────────────────────────────────────┘</span></span></code></pre></div></div></pre>


## Build the Parser Logic : 


## Build the Scraper (Day 4-8)

### Strategy — Layered Scraping:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>          ┌──────────────────┐</span></span>
<span class="line"><span>          │  START: State     │</span></span>
<span class="line"><span>          │  URL: /tm/...     │</span></span>
<span class="line"><span>          └────────┬─────────┘</span></span>
<span class="line"><span>                   │</span></span>
<span class="line"><span>                   ▼</span></span>
<span class="line"><span>     ┌─────────────────────────┐</span></span>
<span class="line"><span>     │  STEP 1: Get Districts  │</span></span>
<span class="line"><span>     │  Parse table → extract  │</span></span>
<span class="line"><span>     │  district names + codes │</span></span>
<span class="line"><span>     │  Store in districts DB  │</span></span>
<span class="line"><span>     └────────────┬────────────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>          ┌───────┴───────┐</span></span>
<span class="line"><span>          │  For EACH      │</span></span>
<span class="line"><span>          │  district code │</span></span>
<span class="line"><span>          └───────┬───────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>                  ▼</span></span>
<span class="line"><span>     ┌─────────────────────────┐</span></span>
<span class="line"><span>     │  STEP 2: Get Blocks     │</span></span>
<span class="line"><span>     │  URL: /tm/{dist_code}/  │</span></span>
<span class="line"><span>     │  Parse → block names    │</span></span>
<span class="line"><span>     │  + codes                │</span></span>
<span class="line"><span>     │  Store in blocks DB     │</span></span>
<span class="line"><span>     └────────────┬────────────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>          ┌───────┴───────┐</span></span>
<span class="line"><span>          │  For EACH      │</span></span>
<span class="line"><span>          │  block code    │</span></span>
<span class="line"><span>          └───────┬───────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>                  ▼</span></span>
<span class="line"><span>     ┌─────────────────────────────┐</span></span>
<span class="line"><span>     │  STEP 3: Get Dealers+Stock  │</span></span>
<span class="line"><span>     │  URL: /tm/{dist}/{block}/   │</span></span>
<span class="line"><span>     │  Parse → dealer name,       │</span></span>
<span class="line"><span>     │  contact, fertilizer-wise   │</span></span>
<span class="line"><span>     │  quantities                 │</span></span>
<span class="line"><span>     │  Store in dealers +         │</span></span>
<span class="line"><span>     │  fertilizer_stock DB        │</span></span>
<span class="line"><span>     └─────────────────────────────┘</span></span></code></pre></div></div></pre>



## PHASE 5: Build the Parser (Day 5-7, parallel with scraper)

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">Python</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span># table_parser.py — PSEUDOCODE</span></span>
<span class="line"></span>
<span class="line"><span>class</span><span> TableParser</span><span>:</span></span>
<span class="line"></span>
<span class="line"><span>    @</span><span>staticmethod</span></span>
<span class="line"><span>    def</span><span> parse_dealer_stock_table</span><span>(html, district_name, block_name):</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        Input:  Raw HTML of the dealer-level page</span></span>
<span class="line"><span>        Output: List of structured dicts</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        soup </span><span>=</span><span> BeautifulSoup(html, </span><span>'lxml'</span><span>)</span></span>
<span class="line"><span>        table </span><span>=</span><span> soup.find(</span><span>'table'</span><span>, </span><span>...</span><span>)</span></span>
<span class="line"></span>
<span class="line"><span>        results </span><span>=</span><span> []</span></span>
<span class="line"><span>        for</span><span> row </span><span>in</span><span> table.find_all(</span><span>'tr'</span><span>)[</span><span>1</span><span>:]:</span></span>
<span class="line"><span>            cols </span><span>=</span><span> row.find_all(</span><span>'td'</span><span>)</span></span>
<span class="line"></span>
<span class="line"><span>            # Map column index to field</span></span>
<span class="line"><span>            # (THIS MAPPING IS DISCOVERED IN PHASE 0)</span></span>
<span class="line"><span>            record </span><span>=</span><span> {</span></span>
<span class="line"><span>                'dealer_name'</span><span>:    clean_text(cols[</span><span>0</span><span>]),</span></span>
<span class="line"><span>                'contact'</span><span>:        clean_text(cols[</span><span>1</span><span>]),</span></span>
<span class="line"><span>                'license_no'</span><span>:     clean_text(cols[</span><span>2</span><span>]),</span></span>
<span class="line"><span>                'fertilizers'</span><span>: {</span></span>
<span class="line"><span>                    'Urea'</span><span>:       parse_number(cols[</span><span>3</span><span>]),</span></span>
<span class="line"><span>                    'DAP'</span><span>:        parse_number(cols[</span><span>4</span><span>]),</span></span>
<span class="line"><span>                    'MOP'</span><span>:        parse_number(cols[</span><span>5</span><span>]),</span></span>
<span class="line"><span>                    '16-16-16'</span><span>:   parse_number(cols[</span><span>6</span><span>]),</span></span>
<span class="line"><span>                    # ... map ALL fertilizer columns</span></span>
<span class="line"><span>                }</span></span>
<span class="line"><span>            }</span></span>
<span class="line"><span>            results.append(record)</span></span>
<span class="line"></span>
<span class="line"><span>        return</span><span> results</span></span></code></pre></div></div></pre>

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">Python</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span># data_cleaner.py</span></span>
<span class="line"></span>
<span class="line"><span>class</span><span> DataCleaner</span><span>:</span></span>
<span class="line"></span>
<span class="line"><span>    @</span><span>staticmethod</span></span>
<span class="line"><span>    def</span><span> clean_text</span><span>(td_element):</span></span>
<span class="line"><span>        """Remove whitespace, newlines, special chars"""</span></span>
<span class="line"><span>        return</span><span> td_element.get_text(</span><span>strip</span><span>=</span><span>True</span><span>)</span></span>
<span class="line"></span>
<span class="line"><span>    @</span><span>staticmethod</span></span>
<span class="line"><span>    def</span><span> parse_number</span><span>(td_element):</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        Handle: '1,650' → 1650</span></span>
<span class="line"><span>                ''       → 0</span></span>
<span class="line"><span>                'N/A'    → None</span></span>
<span class="line"><span>                '1650.5' → 1650.5</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        text </span><span>=</span><span> td_element.get_text(</span><span>strip</span><span>=</span><span>True</span><span>)</span></span>
<span class="line"><span>        if</span><span> not</span><span> text </span><span>or</span><span> text </span><span>in</span><span> [</span><span>'N/A'</span><span>, </span><span>'-'</span><span>, </span><span>''</span><span>]:</span></span>
<span class="line"><span>            return</span><span> 0</span></span>
<span class="line"><span>        text </span><span>=</span><span> text.replace(</span><span>','</span><span>, </span><span>''</span><span>)</span></span>
<span class="line"><span>        return</span><span> float</span><span>(text)</span></span>
<span class="line"></span>
<span class="line"><span>    @</span><span>staticmethod</span></span>
<span class="line"><span>    def</span><span> normalize_fertilizer_name</span><span>(name):</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        '16:16:16' → '16-16-16'</span></span>
<span class="line"><span>        'UREA'     → 'Urea'</span></span>
<span class="line"><span>        Standardize names</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        # mapping dictionary</span></span>
<span class="line"><span>        ...</span></span></code></pre></div></div></pre>

---

## PHASE 6: Build the Storage Pipeline (Day 7-9)

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">Python</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span># operations.py — PSEUDOCODE</span></span>
<span class="line"></span>
<span class="line"><span>class</span><span> DBOperations</span><span>:</span></span>
<span class="line"></span>
<span class="line"><span>    def</span><span> upsert_district</span><span>(self, code, name):</span></span>
<span class="line"><span>        """Insert if not exists, return id"""</span></span>
<span class="line"><span>        existing </span><span>=</span><span> session.query(District).filter_by(</span><span>code</span><span>=</span><span>code).first()</span></span>
<span class="line"><span>        if</span><span> existing:</span></span>
<span class="line"><span>            return</span><span> existing.id</span></span>
<span class="line"><span>        new </span><span>=</span><span> District(</span><span>code</span><span>=</span><span>code, </span><span>name</span><span>=</span><span>name)</span></span>
<span class="line"><span>        session.add(new)</span></span>
<span class="line"><span>        session.commit()</span></span>
<span class="line"><span>        return</span><span> new.id</span></span>
<span class="line"></span>
<span class="line"><span>    def</span><span> upsert_block</span><span>(self, code, name, district_id):</span></span>
<span class="line"><span>        """Same pattern"""</span></span>
<span class="line"><span>        ...</span></span>
<span class="line"></span>
<span class="line"><span>    def</span><span> upsert_dealer</span><span>(self, name, contact, license_no, block_id):</span></span>
<span class="line"><span>        """Same pattern — use license_no for dedup"""</span></span>
<span class="line"><span>        ...</span></span>
<span class="line"></span>
<span class="line"><span>    def</span><span> insert_stock</span><span>(self, dealer_id, fertilizer_name, quantity, scrape_date, run_id):</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        Insert stock record</span></span>
<span class="line"><span>        ON CONFLICT (dealer_id, fertilizer_name, scrape_date) → UPDATE quantity</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        # Use PostgreSQL UPSERT:</span></span>
<span class="line"><span>        # INSERT ... ON CONFLICT ... DO UPDATE SET quantity = EXCLUDED.quantity</span></span>
<span class="line"><span>        ...</span></span></code></pre></div></div></pre>

---

## PHASE 7: Build the Orchestrator (Day 9-10)

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">Python</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span># orchestrator.py — THE MAIN PIPELINE</span></span>
<span class="line"></span>
<span class="line"><span>class</span><span> ScrapingPipeline</span><span>:</span></span>
<span class="line"></span>
<span class="line"><span>    def</span><span> __init__</span><span>(self):</span></span>
<span class="line"><span>        self</span><span>.district_scraper </span><span>=</span><span> DistrictScraper()</span></span>
<span class="line"><span>        self</span><span>.block_scraper </span><span>=</span><span> BlockScraper()</span></span>
<span class="line"><span>        self</span><span>.dealer_scraper </span><span>=</span><span> DealerScraper()</span></span>
<span class="line"><span>        self</span><span>.parser </span><span>=</span><span> TableParser()</span></span>
<span class="line"><span>        self</span><span>.db </span><span>=</span><span> DBOperations()</span></span>
<span class="line"></span>
<span class="line"><span>    def</span><span> run_full_scrape</span><span>(self):</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        MASTER FLOW</span></span>
<span class="line"><span>        """</span></span>
<span class="line"><span>        # 1. Create scrape run record</span></span>
<span class="line"><span>        run_id </span><span>=</span><span> self</span><span>.db.create_scrape_run()</span></span>
<span class="line"><span>        today </span><span>=</span><span> date.today()</span></span>
<span class="line"></span>
<span class="line"><span>        try</span><span>:</span></span>
<span class="line"><span>            # 2. Get all districts</span></span>
<span class="line"><span>            districts </span><span>=</span><span> self</span><span>.district_scraper.get_all_districts()</span></span>
<span class="line"><span>            log.info(</span><span>f</span><span>"Found </span><span>{len</span><span>(districts)</span><span>}</span><span> districts"</span><span>)</span></span>
<span class="line"></span>
<span class="line"><span>            for</span><span> district </span><span>in</span><span> districts:</span></span>
<span class="line"></span>
<span class="line"><span>                # 3. Save district</span></span>
<span class="line"><span>                dist_id </span><span>=</span><span> self</span><span>.db.upsert_district(</span></span>
<span class="line"><span>                    district[</span><span>'code'</span><span>], district[</span><span>'name'</span><span>]</span></span>
<span class="line"><span>                )</span></span>
<span class="line"></span>
<span class="line"><span>                # 4. Get blocks for this district</span></span>
<span class="line"><span>                blocks </span><span>=</span><span> self</span><span>.block_scraper.get_blocks(district[</span><span>'code'</span><span>])</span></span>
<span class="line"><span>                log.info(</span><span>f</span><span>"  </span><span>{</span><span>district[</span><span>'name'</span><span>]</span><span>}</span><span>: </span><span>{len</span><span>(blocks)</span><span>}</span><span> blocks"</span><span>)</span></span>
<span class="line"></span>
<span class="line"><span>                for</span><span> block </span><span>in</span><span> blocks:</span></span>
<span class="line"></span>
<span class="line"><span>                    # 5. Save block</span></span>
<span class="line"><span>                    block_id </span><span>=</span><span> self</span><span>.db.upsert_block(</span></span>
<span class="line"><span>                        block[</span><span>'code'</span><span>], block[</span><span>'name'</span><span>], dist_id</span></span>
<span class="line"><span>                    )</span></span>
<span class="line"></span>
<span class="line"><span>                    # 6. Get dealer stock for this block</span></span>
<span class="line"><span>                    html </span><span>=</span><span> self</span><span>.dealer_scraper.fetch_page(</span></span>
<span class="line"><span>                        build_dealer_url(district[</span><span>'code'</span><span>], block[</span><span>'code'</span><span>])</span></span>
<span class="line"><span>                    )</span></span>
<span class="line"></span>
<span class="line"><span>                    # 7. Parse the table</span></span>
<span class="line"><span>                    dealers </span><span>=</span><span> self</span><span>.parser.parse_dealer_stock_table(</span></span>
<span class="line"><span>                        html, district[</span><span>'name'</span><span>], block[</span><span>'name'</span><span>]</span></span>
<span class="line"><span>                    )</span></span>
<span class="line"></span>
<span class="line"><span>                    # 8. Save each dealer + stock</span></span>
<span class="line"><span>                    for</span><span> dealer </span><span>in</span><span> dealers:</span></span>
<span class="line"><span>                        dealer_id </span><span>=</span><span> self</span><span>.db.upsert_dealer(</span></span>
<span class="line"><span>                            dealer[</span><span>'dealer_name'</span><span>],</span></span>
<span class="line"><span>                            dealer[</span><span>'contact'</span><span>],</span></span>
<span class="line"><span>                            dealer[</span><span>'license_no'</span><span>],</span></span>
<span class="line"><span>                            block_id</span></span>
<span class="line"><span>                        )</span></span>
<span class="line"></span>
<span class="line"><span>                        for</span><span> fert_name, quantity </span><span>in</span><span> dealer[</span><span>'fertilizers'</span><span>].items():</span></span>
<span class="line"><span>                            self</span><span>.db.insert_stock(</span></span>
<span class="line"><span>                                dealer_id, fert_name, quantity, today, run_id</span></span>
<span class="line"><span>                            )</span></span>
<span class="line"></span>
<span class="line"><span>                    # RATE LIMIT</span></span>
<span class="line"><span>                    time.sleep(</span><span>2</span><span>)</span></span>
<span class="line"></span>
<span class="line"><span>            # 9. Mark run as success</span></span>
<span class="line"><span>            self</span><span>.db.complete_scrape_run(run_id, </span><span>status</span><span>=</span><span>'success'</span><span>)</span></span>
<span class="line"></span>
<span class="line"><span>        except</span><span> Exception</span><span> as</span><span> e:</span></span>
<span class="line"><span>            log.error(</span><span>f</span><span>"Pipeline failed: </span><span>{</span><span>e</span><span>}</span><span>"</span><span>)</span></span>
<span class="line"><span>            self</span><span>.db.complete_scrape_run(run_id, </span><span>status</span><span>=</span><span>'failed'</span><span>)</span></span>
<span class="line"><span>            raise</span></span></code></pre></div></div></pre>

### Flow Diagram:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>┌─────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐</span></span>
<span class="line"><span>│ SCRAPER │───▶│ PARSER  │───▶│ CLEANER  │───▶│ DATABASE │</span></span>
<span class="line"><span>│ (fetch) │    │ (parse) │    │ (validate│    │ (store)  │</span></span>
<span class="line"><span>│         │    │         │    │  + clean)│    │          │</span></span>
<span class="line"><span>└─────────┘    └─────────┘    └──────────┘    └──────────┘</span></span>
<span class="line"><span>     │                                              │</span></span>
<span class="line"><span>     │              ┌──────────┐                    │</span></span>
<span class="line"><span>     └──────────────│  LOGGER  │────────────────────┘</span></span>
<span class="line"><span>                    │ (track   │</span></span>
<span class="line"><span>                    │  every   │</span></span>
<span class="line"><span>                    │  step)   │</span></span>
<span class="line"><span>                    └──────────┘</span></span></code></pre></div></div></pre>

---

## PHASE 8: Testing & Validation (Day 10-12)

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>┌─────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                    TEST PLAN                             │</span></span>
<span class="line"><span>├────────────────────┬────────────────────────────────────┤</span></span>
<span class="line"><span>│ Test Type          │ What to Test                       │</span></span>
<span class="line"><span>├────────────────────┼────────────────────────────────────┤</span></span>
<span class="line"><span>│ Unit Tests         │ Parser extracts correct values     │</span></span>
<span class="line"><span>│                    │ Cleaner handles edge cases         │</span></span>
<span class="line"><span>│                    │ URL builder generates correct URLs │</span></span>
<span class="line"><span>├────────────────────┼────────────────────────────────────┤</span></span>
<span class="line"><span>│ Integration Tests  │ Scraper → Parser → DB flow works  │</span></span>
<span class="line"><span>│                    │ Upsert logic doesn't create dupes  │</span></span>
<span class="line"><span>├────────────────────┼────────────────────────────────────┤</span></span>
<span class="line"><span>│ Spot Check         │ Pick 5 random dealers              │</span></span>
<span class="line"><span>│                    │ Compare DB values vs website       │</span></span>
<span class="line"><span>│                    │ They MUST match exactly             │</span></span>
<span class="line"><span>├────────────────────┼────────────────────────────────────┤</span></span>
<span class="line"><span>│ Volume Test        │ Run full scrape for 1 district     │</span></span>
<span class="line"><span>│                    │ Check: record count, time taken    │</span></span>
<span class="line"><span>├────────────────────┼────────────────────────────────────┤</span></span>
<span class="line"><span>│ Failure Test       │ Kill network mid-scrape            │</span></span>
<span class="line"><span>│                    │ Does it log? Can it resume?        │</span></span>
<span class="line"><span>└────────────────────┴────────────────────────────────────┘</span></span></code></pre></div></div></pre>

### Validation Queries:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">SQL</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>-- How many records per district?</span></span>
<span class="line"><span>SELECT</span><span> d</span><span>.</span><span>name</span><span>, </span><span>COUNT</span><span>(</span><span>fs</span><span>.</span><span>id</span><span>)</span></span>
<span class="line"><span>FROM</span><span> fertilizer_stock fs</span></span>
<span class="line"><span>JOIN</span><span> dealers dl </span><span>ON</span><span> fs</span><span>.</span><span>dealer_id</span><span> =</span><span> dl</span><span>.</span><span>id</span></span>
<span class="line"><span>JOIN</span><span> blocks b </span><span>ON</span><span> dl</span><span>.</span><span>block_id</span><span> =</span><span> b</span><span>.</span><span>id</span></span>
<span class="line"><span>JOIN</span><span> districts d </span><span>ON</span><span> b</span><span>.</span><span>district_id</span><span> =</span><span> d</span><span>.</span><span>id</span></span>
<span class="line"><span>WHERE</span><span> fs</span><span>.</span><span>scrape_date</span><span> =</span><span> CURRENT_DATE</span></span>
<span class="line"><span>GROUP BY</span><span> d</span><span>.</span><span>name</span></span>
<span class="line"><span>ORDER BY</span><span> COUNT</span><span>(</span><span>fs</span><span>.</span><span>id</span><span>) </span><span>DESC</span><span>;</span></span>
<span class="line"></span>
<span class="line"><span>-- Any dealers with zero stock across all fertilizers?</span></span>
<span class="line"><span>-- Any blocks with no dealers? (data gap detection)</span></span></code></pre></div></div></pre>

---

## EXECUTION TIMELINE

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>┌────────────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                                                                │</span></span>
<span class="line"><span>│  DAY  1-2  │████│  Phase 0: Reconnaissance                    │</span></span>
<span class="line"><span>│  DAY  2    │██│    Phase 1: Tech stack + setup                 │</span></span>
<span class="line"><span>│  DAY  2-3  │███│   Phase 2: Project structure                  │</span></span>
<span class="line"><span>│  DAY  3-4  │████│  Phase 3: Database schema + create tables    │</span></span>
<span class="line"><span>│  DAY  4-8  │██████████│  Phase 4: Build scraper (BIGGEST PHASE)│</span></span>
<span class="line"><span>│  DAY  5-7  │██████│  Phase 5: Build parser (parallel)          │</span></span>
<span class="line"><span>│  DAY  7-9  │█████│   Phase 6: Storage pipeline                 │</span></span>
<span class="line"><span>│  DAY  9-10 │████│    Phase 7: Orchestrator                     │</span></span>
<span class="line"><span>│  DAY 10-12 │████│    Phase 8: Testing + validation             │</span></span>
<span class="line"><span>│                                                                │</span></span>
<span class="line"><span>│  TOTAL: ~12 working days for MVP                               │</span></span>
<span class="line"><span>│                                                                │</span></span>
<span class="line"><span>└────────────────────────────────────────────────────────────────┘</span></span></code></pre></div></div></pre>

---

## IMMEDIATE FIRST STEPS (Start Today)

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>┌─────────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                                                             │</span></span>
<span class="line"><span>│  STEP 1:  Open the website in Chrome                        │</span></span>
<span class="line"><span>│           Right-click → View Page Source                     │</span></span>
<span class="line"><span>│           Can you see table data in raw HTML?               │</span></span>
<span class="line"><span>│           → Decides: requests vs selenium                   │</span></span>
<span class="line"><span>│                                                             │</span></span>
<span class="line"><span>│  STEP 2:  Open Chrome DevTools → Network Tab                │</span></span>
<span class="line"><span>│           Click through district → block → dealer           │</span></span>
<span class="line"><span>│           Note every URL that fires                         │</span></span>
<span class="line"><span>│           → Gives you the URL pattern map                   │</span></span>
<span class="line"><span>│                                                             │</span></span>
<span class="line"><span>│  STEP 3:  Save 3 sample HTML pages locally                  │</span></span>
<span class="line"><span>│           (state level, district level, dealer level)        │</span></span>
<span class="line"><span>│           → You can build parser OFFLINE without             │</span></span>
<span class="line"><span>│             hitting the server repeatedly                    │</span></span>
<span class="line"><span>│                                                             │</span></span>
<span class="line"><span>│  STEP 4:  Set up project folder + virtual env               │</span></span>
<span class="line"><span>│           pip install requests beautifulsoup4 lxml           │</span></span>
<span class="line"><span>│                      psycopg2-binary sqlalchemy              │</span></span>
<span class="line"><span>│                                                             │</span></span>
<span class="line"><span>│  STEP 5:  Write your FIRST scraper function:                │</span></span>
<span class="line"><span>│           Fetch state page → Extract district list           │</span></span>
<span class="line"><span>│           Print it. Verify it matches the website.           │</span></span>
<span class="line"><span>│           → THIS IS YOUR PROOF OF CONCEPT                   │</span></span>
<span class="line"><span>│                                                             │</span></span>
<span class="line"><span>└─────────────────────────────────────────────────────────────┘</span></span></code></pre></div></div></pre>


## PHASE 3: Database Schema Design (Day 3-4)

### ER Diagram (Conceptual):

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>┌──────────────┐       ┌──────────────┐       ┌──────────────────┐</span></span>
<span class="line"><span>│  districts   │       │   blocks     │       │    dealers       │</span></span>
<span class="line"><span>├──────────────┤       ├──────────────┤       ├──────────────────┤</span></span>
<span class="line"><span>│ id (PK)      │──┐    │ id (PK)      │──┐    │ id (PK)          │</span></span>
<span class="line"><span>│ code         │  │    │ code         │  │    │ name             │</span></span>
<span class="line"><span>│ name         │  │    │ name         │  │    │ contact          │</span></span>
<span class="line"><span>│ created_at   │  │    │ district_id  │──┘    │ address          │</span></span>
<span class="line"><span>└──────────────┘  │    │   (FK)       │       │ block_id (FK)  ──┘</span></span>
<span class="line"><span>                  │    │ created_at   │       │ license_no       │</span></span>
<span class="line"><span>                  │    └──────────────┘       │ created_at       │</span></span>
<span class="line"><span>                  │                           └──────────────────┘</span></span>
<span class="line"><span>                  │                                    │</span></span>
<span class="line"><span>                  │                                    │</span></span>
<span class="line"><span>                  │    ┌───────────────────────────┐   │</span></span>
<span class="line"><span>                  │    │   fertilizer_stock        │   │</span></span>
<span class="line"><span>                  │    ├───────────────────────────┤   │</span></span>
<span class="line"><span>                  │    │ id (PK)                   │   │</span></span>
<span class="line"><span>                  │    │ dealer_id (FK)  ──────────┘   │</span></span>
<span class="line"><span>                  │    │ fertilizer_name            │</span></span>
<span class="line"><span>                  │    │ quantity_kg                 │</span></span>
<span class="line"><span>                  │    │ scrape_date                 │◄── CRITICAL</span></span>
<span class="line"><span>                  │    │ created_at                  │</span></span>
<span class="line"><span>                  │    └───────────────────────────┘</span></span>
<span class="line"><span>                  │</span></span>
<span class="line"><span>                  │    ┌───────────────────────────┐</span></span>
<span class="line"><span>                  │    │   scrape_runs             │</span></span>
<span class="line"><span>                  │    ├───────────────────────────┤</span></span>
<span class="line"><span>                  │    │ id (PK)                   │</span></span>
<span class="line"><span>                  │    │ started_at                 │</span></span>
<span class="line"><span>                  │    │ completed_at               │</span></span>
<span class="line"><span>                  │    │ status (success/failed)    │</span></span>
<span class="line"><span>                  │    │ total_records              │</span></span>
<span class="line"><span>                  │    │ errors_count               │</span></span>
<span class="line"><span>                  │    └───────────────────────────┘</span></span>
<span class="line"><span>                  │</span></span></code></pre></div></div></pre>

### SQL (PostgreSQL):

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">SQL</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>-- DISTRICTS</span></span>
<span class="line"><span>CREATE</span><span> TABLE</span><span> districts</span><span> (</span></span>
<span class="line"><span>    id            </span><span>SERIAL</span><span> PRIMARY KEY</span><span>,</span></span>
<span class="line"><span>    code          </span><span>VARCHAR</span><span>(</span><span>10</span><span>) </span><span>UNIQUE</span><span> NOT NULL</span><span>,   </span><span>-- from URL pattern</span></span>
<span class="line"><span>    name</span><span>          VARCHAR</span><span>(</span><span>100</span><span>) </span><span>NOT NULL</span><span>,</span></span>
<span class="line"><span>    created_at    </span><span>TIMESTAMP</span><span> DEFAULT</span><span> NOW</span><span>()</span></span>
<span class="line"><span>);</span></span>
<span class="line"></span>
<span class="line"><span>-- BLOCKS</span></span>
<span class="line"><span>CREATE</span><span> TABLE</span><span> blocks</span><span> (</span></span>
<span class="line"><span>    id            </span><span>SERIAL</span><span> PRIMARY KEY</span><span>,</span></span>
<span class="line"><span>    code          </span><span>VARCHAR</span><span>(</span><span>10</span><span>) </span><span>NOT NULL</span><span>,</span></span>
<span class="line"><span>    name</span><span>          VARCHAR</span><span>(</span><span>100</span><span>) </span><span>NOT NULL</span><span>,</span></span>
<span class="line"><span>    district_id   </span><span>INTEGER</span><span> REFERENCES</span><span> districts(id),</span></span>
<span class="line"><span>    created_at    </span><span>TIMESTAMP</span><span> DEFAULT</span><span> NOW</span><span>(),</span></span>
<span class="line"><span>    UNIQUE</span><span>(code, district_id)</span></span>
<span class="line"><span>);</span></span>
<span class="line"></span>
<span class="line"><span>-- DEALERS</span></span>
<span class="line"><span>CREATE</span><span> TABLE</span><span> dealers</span><span> (</span></span>
<span class="line"><span>    id            </span><span>SERIAL</span><span> PRIMARY KEY</span><span>,</span></span>
<span class="line"><span>    name</span><span>          VARCHAR</span><span>(</span><span>200</span><span>) </span><span>NOT NULL</span><span>,</span></span>
<span class="line"><span>    contact       </span><span>VARCHAR</span><span>(</span><span>20</span><span>),</span></span>
<span class="line"><span>    address</span><span>       TEXT</span><span>,</span></span>
<span class="line"><span>    license_no    </span><span>VARCHAR</span><span>(</span><span>50</span><span>),</span></span>
<span class="line"><span>    block_id      </span><span>INTEGER</span><span> REFERENCES</span><span> blocks(id),</span></span>
<span class="line"><span>    created_at    </span><span>TIMESTAMP</span><span> DEFAULT</span><span> NOW</span><span>(),</span></span>
<span class="line"><span>    UNIQUE</span><span>(license_no)                          </span><span>-- deduplicate dealers</span></span>
<span class="line"><span>);</span></span>
<span class="line"></span>
<span class="line"><span>-- FERTILIZER STOCK (the core fact table)</span></span>
<span class="line"><span>CREATE</span><span> TABLE</span><span> fertilizer_stock</span><span> (</span></span>
<span class="line"><span>    id            </span><span>SERIAL</span><span> PRIMARY KEY</span><span>,</span></span>
<span class="line"><span>    dealer_id     </span><span>INTEGER</span><span> REFERENCES</span><span> dealers(id),</span></span>
<span class="line"><span>    fertilizer_name </span><span>VARCHAR</span><span>(</span><span>100</span><span>) </span><span>NOT NULL</span><span>,       </span><span>-- 'Urea', 'DAP', '16-16-16'</span></span>
<span class="line"><span>    quantity       </span><span>DECIMAL</span><span>(</span><span>10</span><span>,</span><span>2</span><span>),                 </span><span>-- in KG or bags</span></span>
<span class="line"><span>    unit           </span><span>VARCHAR</span><span>(</span><span>20</span><span>) </span><span>DEFAULT</span><span> 'KG'</span><span>,</span></span>
<span class="line"><span>    scrape_date    </span><span>DATE</span><span> NOT NULL</span><span>,                 </span><span>-- the date this was valid</span></span>
<span class="line"><span>    scrape_run_id  </span><span>INTEGER</span><span> REFERENCES</span><span> scrape_runs(id),</span></span>
<span class="line"><span>    created_at     </span><span>TIMESTAMP</span><span> DEFAULT</span><span> NOW</span><span>(),</span></span>
<span class="line"><span>    UNIQUE</span><span>(dealer_id, fertilizer_name, scrape_date)  </span><span>-- one entry per day</span></span>
<span class="line"><span>);</span></span>
<span class="line"></span>
<span class="line"><span>-- SCRAPE METADATA</span></span>
<span class="line"><span>CREATE</span><span> TABLE</span><span> scrape_runs</span><span> (</span></span>
<span class="line"><span>    id            </span><span>SERIAL</span><span> PRIMARY KEY</span><span>,</span></span>
<span class="line"><span>    started_at    </span><span>TIMESTAMP</span><span> NOT NULL</span><span>,</span></span>
<span class="line"><span>    completed_at  </span><span>TIMESTAMP</span><span>,</span></span>
<span class="line"><span>    status</span><span>        VARCHAR</span><span>(</span><span>20</span><span>) </span><span>DEFAULT</span><span> 'running'</span><span>, </span><span>-- running/success/failed</span></span>
<span class="line"><span>    total_records </span><span>INTEGER</span><span> DEFAULT</span><span> 0</span><span>,</span></span>
<span class="line"><span>    errors_count  </span><span>INTEGER</span><span> DEFAULT</span><span> 0</span><span>,</span></span>
<span class="line"><span>    notes         </span><span>TEXT</span></span>
<span class="line"><span>);</span></span>
<span class="line"></span>
<span class="line"><span>-- INDEXES for fast queries</span></span>
<span class="line"><span>CREATE</span><span> INDEX</span><span> idx_stock_date</span><span> ON</span><span> fertilizer_stock(scrape_date);</span></span>
<span class="line"><span>CREATE</span><span> INDEX</span><span> idx_stock_dealer</span><span> ON</span><span> fertilizer_stock(dealer_id);</span></span>
<span class="line"><span>CREATE</span><span> INDEX</span><span> idx_stock_fertilizer</span><span> ON</span><span> fertilizer_stock(fertilizer_name);</span></span>
<span class="line"><span>CREATE</span><span> INDEX</span><span> idx_blocks_district</span><span> ON</span><span> blocks(district_id);</span></span>
<span class="line"><span>CREATE</span><span> INDEX</span><span> idx_dealers_block</span><span> ON</span><span> dealers(block_id);</span></span></code></pre></div></div></pre>

### Why this design:

<pre><div class="not-prose my-0 flex w-full flex-col overflow-clip border border-border text-text-primary rounded-lg not-prose relative" data-code-block="true"><div class="border-border flex items-center justify-between border-b px-4 py-2"><div class="flex items-center gap-2"><svg width="14" stroke-width="1.5" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-text-secondary"><path d="M9.00001 21L8.00001 21C6.89544 21 6.00001 20.1057 6.00001 19.0011C6.00001 17.4501 6.00001 15.3443 6 14C6 13 4.5 12 4.5 12C4.5 12 6.00001 11 6.00001 10C6.00001 8.827 6.00001 6.62207 6.00001 4.99914C6.00001 3.89457 6.89544 3 8.00001 3L9.00001 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 21L16 21C17.1046 21 18 20.1057 18 19.0011C18 17.4501 18 15.3443 18 14C18 13 19.5 12 19.5 12C19.5 12 18 11 18 10C18 8.827 18 6.62207 18 4.99914C18 3.89457 17.1046 3 16 3L15 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><span class="text-text-secondary text-sm font-medium">text</span></div><button class="inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ring-offset-2 focus-visible:ring-offset-surface-primary disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 text-sm text-interactive-active hover:text-interactive-normal active:text-text-tertiary font-normal relative rounded-lg p-[6px]" type="button" data-state="closed" data-slot="tooltip-trigger"><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="text-interactive-positive absolute inset-0 m-auto rotate-90 opacity-0 transition-all duration-300"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg><svg width="16" height="16" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor" class="absolute inset-0 m-auto opacity-100 transition-opacity duration-300"><path d="M19.4 20H9.6C9.26863 20 9 19.7314 9 19.4V9.6C9 9.26863 9.26863 9 9.6 9H19.4C19.7314 9 20 9.26863 20 9.6V19.4C20 19.7314 19.7314 20 19.4 20Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15 9V4.6C15 4.26863 14.7314 4 14.4 4H4.6C4.26863 4 4 4.26863 4 4.6V14.4C4 14.7314 4.26863 15 4.6 15H9" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"></path></svg></button></div><div class="code-block_container__lbMX4"><pre class="shiki github-dark shiki-code-block" tabindex="0"><code class="whitespace-pre-wrap break-words"><span class="line"><span>┌─────────────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                                                                 │</span></span>
<span class="line"><span>│  ✅ Normalized → No data duplication                           │</span></span>
<span class="line"><span>│  ✅ Time-series ready → scrape_date on stock table             │</span></span>
<span class="line"><span>│  ✅ Hierarchy preserved → district → block → dealer → stock   │</span></span>
<span class="line"><span>│  ✅ Deduplicated → UNIQUE constraints prevent duplicates       │</span></span>
<span class="line"><span>│  ✅ Audit trail → scrape_runs tracks every scraping session    │</span></span>
<span class="line"><span>│                                                                 │</span></span>
<span class="line"><span>└─────────────────────────────────────────────────────────────────┘</span></span></code></pre></div></div></pre>


>
> **Golden Rule** : Get **one district, one block, one dealer** flowing end-to-end (scrape → parse → store in DB)  **FIRST** . Then scale to all districts. Don't try to build everything at once.
>
