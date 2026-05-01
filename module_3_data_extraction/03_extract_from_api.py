"""
Module 3 - Lesson 3: Extracting Data from APIs
================================================
REST APIs are a major data source in modern data engineering.
Whether you're pulling data from Salesforce, Stripe, Twitter,
or an internal microservice, the pattern is always similar:
  1. Make an HTTP request
  2. Handle errors and rate limits
  3. Parse the response (usually JSON)
  4. Handle pagination to get all records

This lesson uses https://jsonplaceholder.typicode.com — a free,
public REST API for testing. No API key required.

Topics covered:
  - Making GET requests with the requests library
  - Reading response status codes
  - Parsing JSON responses
  - Adding headers (for authentication)
  - Handling pagination (page-based and cursor-based)
  - Rate limiting (respecting API limits)
  - Error handling for network/API failures
  - Converting API data to a DataFrame
"""

import time
import requests
import pandas as pd
from typing import Optional, Generator

# Base URL for our demo API (JSONPlaceholder — free, public, no auth needed)
BASE_URL = "https://jsonplaceholder.typicode.com"


# =============================================================================
# 1. BASIC GET REQUEST
# =============================================================================

print("=" * 60)
print("1. BASIC GET REQUEST")
print("=" * 60)

# requests.get() — sends an HTTP GET request and returns a Response object
print(f"Making GET request to {BASE_URL}/posts/1")

try:
    response = requests.get(f"{BASE_URL}/posts/1", timeout=10)

    # Always check the status code
    print(f"Status code: {response.status_code}")
    print(f"Headers: {dict(list(response.headers.items())[:3])}...")

    # 200 = OK; raise an exception for 4xx/5xx status codes
    response.raise_for_status()

    # Parse the JSON response body
    post = response.json()
    print(f"\nResponse (post #1):")
    for k, v in post.items():
        print(f"  {k}: {v}")

except requests.exceptions.ConnectionError:
    print("  [OFFLINE] Cannot connect to API. Demo values used.")
    post = {"userId": 1, "id": 1, "title": "Demo post", "body": "Demo body"}
except requests.exceptions.Timeout:
    print("  [TIMEOUT] Request timed out after 10s")
    post = None
except requests.exceptions.HTTPError as e:
    print(f"  [HTTP ERROR] {e}")
    post = None


# =============================================================================
# 2. HTTP STATUS CODES REFERENCE
# =============================================================================

print("\n" + "=" * 60)
print("2. HTTP STATUS CODES")
print("=" * 60)

status_codes = {
    200: "OK — success",
    201: "Created — resource was created",
    204: "No Content — success with no body",
    400: "Bad Request — malformed request",
    401: "Unauthorized — missing/invalid credentials",
    403: "Forbidden — valid credentials but no access",
    404: "Not Found — resource doesn't exist",
    429: "Too Many Requests — rate limit exceeded",
    500: "Internal Server Error — API bug",
    503: "Service Unavailable — API down/overloaded",
}

for code, description in status_codes.items():
    print(f"  {code}: {description}")


# =============================================================================
# 3. ADDING HEADERS (AUTHENTICATION)
# =============================================================================

print("\n" + "=" * 60)
print("3. AUTHENTICATION HEADERS")
print("=" * 60)

# Most production APIs require authentication via:
#   - API Key in header: "X-Api-Key": "your_key"
#   - Bearer token:      "Authorization": "Bearer <token>"
#   - Basic auth:        requests.get(..., auth=("user", "pass"))

# Example headers (JSONPlaceholder doesn't require auth, but this shows the pattern)
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    # For real APIs, you'd add:
    # "Authorization": "Bearer YOUR_TOKEN_HERE",
    # "X-Api-Key": "YOUR_API_KEY_HERE",
}

try:
    response = requests.get(
        f"{BASE_URL}/users/1",
        headers=headers,
        timeout=10
    )
    response.raise_for_status()
    user = response.json()
    print(f"User #1: {user.get('name')}, {user.get('email')}")
    print(f"Company: {user.get('company', {}).get('name')}")
except (requests.exceptions.RequestException, Exception) as e:
    print(f"  [OFFLINE] {e}")
    user = {"id": 1, "name": "Leanne Graham", "email": "demo@example.com"}


# =============================================================================
# 4. FETCHING A LIST ENDPOINT
# =============================================================================

print("\n" + "=" * 60)
print("4. FETCHING A LIST AND CONVERTING TO DATAFRAME")
print("=" * 60)

def fetch_users() -> pd.DataFrame:
    """Fetch all users from the API and return as a DataFrame."""
    try:
        response = requests.get(f"{BASE_URL}/users", timeout=10)
        response.raise_for_status()
        users = response.json()  # list of user objects
        df = pd.json_normalize(users)   # flatten nested fields
        print(f"  Fetched {len(df)} users")
        return df
    except requests.exceptions.RequestException as e:
        print(f"  [OFFLINE] Could not fetch users: {e}")
        # Return sample data for offline testing
        return pd.DataFrame([
            {"id": 1, "name": "Alice", "email": "alice@example.com", "address.city": "NY"},
            {"id": 2, "name": "Bob",   "email": "bob@example.com",   "address.city": "LA"},
        ])

users_df = fetch_users()
print(f"Columns: {list(users_df.columns)}")
print(users_df[["id", "name", "email"]].head() if "id" in users_df.columns else users_df.head())


# =============================================================================
# 5. PAGINATION — PAGE-BASED
# =============================================================================

print("\n" + "=" * 60)
print("5. PAGINATION — Page-Based")
print("=" * 60)

# Most APIs return results in pages. You must loop through all pages
# to get the complete dataset.
# JSONPlaceholder supports: ?_page=1&_limit=10

def fetch_posts_paginated(base_url: str, page_size: int = 10, max_pages: int = 3) -> pd.DataFrame:
    """
    Fetch posts from the API with page-based pagination.

    Args:
        base_url: API base URL.
        page_size: Number of records per page.
        max_pages: Maximum pages to fetch (safety limit).

    Returns:
        DataFrame with all fetched posts.
    """
    all_posts = []
    page = 1

    while page <= max_pages:
        print(f"  Fetching page {page} (limit={page_size})...")

        try:
            response = requests.get(
                f"{base_url}/posts",
                params={"_page": page, "_limit": page_size},
                timeout=10
            )
            response.raise_for_status()
            posts = response.json()

        except requests.exceptions.RequestException as e:
            print(f"  [OFFLINE] Could not fetch page {page}: {e}")
            # Generate demo data for offline mode
            posts = [{"userId": i % 5 + 1, "id": (page-1)*page_size + i + 1,
                      "title": f"Post {(page-1)*page_size + i + 1}",
                      "body": "Sample body"} for i in range(page_size)]

        if not posts:
            print(f"  No more posts (empty page at page {page})")
            break

        print(f"  Got {len(posts)} posts on page {page}")
        all_posts.extend(posts)

        # If we got fewer records than page_size, we've reached the last page
        if len(posts) < page_size:
            print(f"  Last page reached (got {len(posts)} < {page_size})")
            break

        page += 1
        time.sleep(0.1)   # polite delay between requests

    df = pd.DataFrame(all_posts)
    print(f"\n  Total posts fetched: {len(df)}")
    return df

posts_df = fetch_posts_paginated(BASE_URL, page_size=10, max_pages=3)
print(f"Posts DataFrame shape: {posts_df.shape}")
if len(posts_df) > 0:
    print(posts_df[["id", "userId", "title"]].head(5))


# =============================================================================
# 6. RATE LIMITING — RESPECTING API LIMITS
# =============================================================================

print("\n" + "=" * 60)
print("6. RATE LIMITING")
print("=" * 60)

# APIs limit how many requests you can make per second/minute/day.
# Exceeding limits returns HTTP 429 (Too Many Requests).
# Well-behaved clients: check headers and back off when needed.

def safe_get(url: str, headers: dict = None, max_retries: int = 3, base_delay: float = 1.0):
    """
    Make a GET request with automatic retry on rate-limit (429) errors.

    Uses exponential backoff: waits 1s, 2s, 4s between retries.

    Args:
        url: The URL to fetch.
        headers: Optional request headers.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.

    Returns:
        Response object on success.

    Raises:
        requests.HTTPError: If all retries fail.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)

            # Handle rate limiting explicitly
            if response.status_code == 429:
                # Check if API tells us how long to wait
                retry_after = int(response.headers.get("Retry-After", base_delay * (2 ** attempt)))
                print(f"  Rate limited! Waiting {retry_after}s before retry {attempt}/{max_retries}...")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            wait = base_delay * (2 ** attempt)
            print(f"  Timeout on attempt {attempt}/{max_retries}. Retrying in {wait:.1f}s...")
            time.sleep(wait)

        except requests.exceptions.ConnectionError as e:
            print(f"  Connection error: {e}")
            return None  # Don't retry connection errors in offline demo

    raise requests.HTTPError(f"All {max_retries} retries failed for {url}")

# Demo the safe_get function
print("Testing safe_get with JSONPlaceholder:")
result = safe_get(f"{BASE_URL}/todos/1")
if result:
    data = result.json()
    print(f"  Fetched todo: id={data['id']}, completed={data['completed']}, title={data['title'][:40]}")
else:
    print("  [OFFLINE] Could not connect to API")


# =============================================================================
# 7. GENERATOR-BASED PAGINATOR (PRODUCTION PATTERN)
# =============================================================================

print("\n" + "=" * 60)
print("7. GENERATOR-BASED PAGINATOR")
print("=" * 60)

# A generator-based paginator is memory efficient — it yields one page
# at a time rather than loading everything into memory at once.

def paginate_api(
    base_url: str,
    endpoint: str,
    page_size: int = 20,
    max_pages: int = 5,
) -> Generator[list, None, None]:
    """
    Generator that yields one page of results at a time.
    Stops when an empty page is returned or max_pages is reached.
    """
    for page in range(1, max_pages + 1):
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                params={"_page": page, "_limit": page_size},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                return   # generator exhaustion

            yield data

            if len(data) < page_size:
                return   # last page

            time.sleep(0.05)   # small delay between pages

        except requests.exceptions.RequestException:
            # In offline mode, yield demo data once and stop
            yield [{"id": i, "title": f"Demo {i}", "userId": 1} for i in range(1, page_size + 1)]
            return

# Use the generator to stream all comments into a DataFrame
all_data = []
print("Streaming data via generator:")
for page_num, page_data in enumerate(paginate_api(BASE_URL, "/comments", page_size=10, max_pages=2), 1):
    print(f"  Page {page_num}: {len(page_data)} records")
    all_data.extend(page_data)

df_all = pd.DataFrame(all_data)
print(f"Total records collected: {len(df_all)}")
if len(df_all) > 0 and "name" in df_all.columns:
    print(df_all[["id", "postId", "name"]].head(5))


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Full API Extraction Pipeline")
    print("=" * 60)

    def extract_from_api(
        resource: str,
        page_size: int = 20,
        max_pages: int = 5,
    ) -> pd.DataFrame:
        """Extract all records for a resource, handling pagination."""
        print(f"\n[EXTRACT] Fetching '{resource}' from {BASE_URL}")
        records = []

        for page in range(1, max_pages + 1):
            try:
                resp = requests.get(
                    f"{BASE_URL}/{resource}",
                    params={"_page": page, "_limit": page_size},
                    timeout=10
                )
                resp.raise_for_status()
                page_data = resp.json()
            except requests.exceptions.RequestException as e:
                print(f"  [OFFLINE] {e} — using demo data")
                page_data = [{"id": i, "resource": resource} for i in range(1, page_size+1)]
                records.extend(page_data)
                break

            if not page_data:
                break

            records.extend(page_data)
            print(f"  Page {page}: {len(page_data)} records (total: {len(records)})")

            if len(page_data) < page_size:
                break

            time.sleep(0.1)

        df = pd.DataFrame(records)
        print(f"[EXTRACT] Complete — {len(df)} total records")
        return df

    # Extract multiple resources
    posts = extract_from_api("posts", page_size=10, max_pages=2)
    users = extract_from_api("users", page_size=10, max_pages=1)

    if "userId" in posts.columns and "id" in users.columns:
        enriched = posts.merge(
            users[["id", "name", "email"]],
            left_on="userId",
            right_on="id",
            how="left",
            suffixes=("", "_user")
        )
        print(f"\nEnriched posts (joined with users): {len(enriched)} rows")
        print(enriched[["id", "name", "title"]].head(5))
