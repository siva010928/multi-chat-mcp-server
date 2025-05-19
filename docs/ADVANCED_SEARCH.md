# Advanced Search Guide

This guide provides detailed information about the advanced search capabilities in the Google Chat MCP extension.

## Search Modes

The search functionality supports multiple search modes, each with different capabilities:

### 1. Regex Search (Default)

Regex search uses regular expression pattern matching to find messages containing specific text patterns. It's case-insensitive by default.

**Best for:** Finding exact terms or patterns with variations in formatting

**Examples:**
- `cicd` - Will match "cicd", "CICD", "CiCd" etc.
- `ci[ /\-_]?cd|cicd` - Will match "CI/CD", "CI-CD", "CI_CD", "CICD", etc.
- `\bpipeline\b` - Will match the word "pipeline" but not "pipelines" or "pipelined"
- `(?i)docker.*storage` - Will match "Docker storage", "docker temp storage", etc.
- `updated.*cicd|cicd.*updated` - Will match phrases containing "updated" and "cicd" in either order

**Finding "CICD pipeline" with regex:**
- Simple query: `cicd` will match "CICD" in "CICD pipeline" (case-insensitive by default)
- More specific: `cicd.*pipeline|pipeline.*cicd` will match "CICD pipeline" or "pipeline for CICD" 
- Even better: `\bcicd\b.*\bpipeline\b|\bpipeline\b.*\bcicd\b` will match whole words only

**Common patterns for CI/CD variations:**
- Comprehensive pattern: `(?i)cicd|ci[ /\-_]?cd|continuous[ -]?integration`
- With context: `(?i)cicd.*pipeline|ci[ /\-_]?cd.*pipeline|pipeline.*cicd`

**When to use:**
- When you know exactly what text you're looking for
- When you need to match variations of terms (like "CI/CD" vs "CICD")
- When you need precise pattern matching (like whole words only)

**Regex Tips:**
- `(?i)` - Makes the entire pattern case-insensitive
- `\b` - Word boundary (match whole words)
- `.` - Any character
- `.*` - Any number of characters
- `[ ]` - Character class (match any character within brackets)
- `?` - Optional character (0 or 1 occurrence)
- `|` - OR operator (match pattern on either side)
- `\` - Escape special characters like `/`, `\`, etc.
- `+` - One or more occurrence of the preceding character
- `*` - Zero or more occurrences of the preceding character

### 2. Semantic Search

Semantic search uses embeddings to find messages that are conceptually similar to your query. It works even when the exact words don't match but the meaning is similar.

**Best for:** Finding messages about a concept or topic without knowing the exact wording

**Examples:**
- `continuous integration` - Will find messages about CI/CD, pipelines, GitHub Actions, etc.
- `meeting schedule` - Will find messages about planning meetings, calendar events, etc.
- `deployment issues` - Will find messages about problems with deployments, release failures, etc.

**Finding CI/CD related messages with semantic search:**
- Query: `continuous integration and deployment pipeline`  
- Will find messages about: CI/CD, GitHub Actions, Jenkins, build systems, etc.
- Will match variations: "our pipeline setup", "CICD workflow", "automated builds"

**When to use:**
- When you want to find messages about a concept rather than exact text
- When you're not sure of the exact wording
- When searching for related topics

**Note:** Semantic search may be slower and might return results that don't contain your exact search terms.

### 3. Exact Search

Exact search performs basic case-insensitive substring matching. It's the simplest and fastest search method.

**Best for:** Simple substring searches when you know exactly what text to find

**Examples:**
- `error message` - Will only find messages containing the exact string "error message"
- `CI/CD` - Will only find messages with "CI/CD" (case insensitive)

**When to use:**
- When you need the fastest search for simple strings
- When you need precise substring matching without regex complexity

### 4. Hybrid Search

Hybrid search combines multiple search approaches (regex, semantic, and exact) for comprehensive results.

**Best for:** When you want both precise pattern matching and conceptual matches

**When to use:**
- When you're not sure which search mode would work best
- When you want the most comprehensive results

## Date Filtering Behavior

Date filtering allows you to narrow down search results to specific time periods. However, the behavior varies by search mode:

### Universal Date Filter Format

All date filters use the YYYY-MM-DD format (e.g., "2024-05-01").

### Date Filter Behavior by Search Mode

#### 1. Regex and Exact Search: Strict Filtering

For regex and exact searches, date filters are **strictly enforced**:
- If no messages match both the query AND the date filter, NO results are returned
- The system will NOT fall back to messages outside the date range
- Example scenario: Searching for "CICD release" from May 18-25, but the only message about this topic was from May 13
  - Result: No messages returned (even though relevant messages exist outside the date range)

#### 2. Semantic Search: Preference-Based Filtering

For semantic searches, date filters are treated as **preferences rather than requirements**:
- System first tries to find semantically relevant messages within the date range
- If no messages match both the semantic query AND date filter, the system will:
  1. Ignore the date filter completely
  2. Return semantically relevant messages regardless of their creation date
  3. Present them in order of semantic relevance

**Example Scenario:**
- Query: "quarterly financial report"
- Date Range: From May 18, 2024 onwards
- Available Messages:
  - Message from May 13: "Here's the Q1 financial summary we discussed"
  - Message from May 20: "When is the team lunch scheduled?"
- Result: 
  - The May 13 message will be returned, even though it's outside the date range
  - The May 20 message will NOT be returned, even though it's within the date range
    (because it's not semantically relevant to "quarterly financial report")

This behavior ensures semantic searches prioritize finding conceptually relevant content even if it falls outside the specified date range.

### Visual Example

```
Timeline:         May 13                   May 18                     May 25
                    |                        |                          |
Messages:      [Financial Report]            |               [Team Meeting]
                    |                        |                          |
Date Filter:        |<----------------Filtered Range------------------>|
                    |                        |                          |
Regex Results:      |  (nothing - strict filtering doesn't find matches)|
                    |                        |                          |
Semantic Results: [Financial Report] <--- (semantic match returned despite being outside filter)
```

## Common Search Patterns and Use Cases

### Finding Messages About CI/CD Pipelines

**Regex search:**
```
search_messages(
  query="(?i)cicd|ci[ /\\-_]?cd|continuous.*integration|github.*action", 
  search_mode="regex"
)
```

**Semantic search:**
```
search_messages(
  query="continuous integration deployment pipeline", 
  search_mode="semantic"
)
```

### Finding Messages About Specific Issues

**Regex search:**
```
search_messages(
  query="(?i)docker.*storage|storage.*issue", 
  search_mode="regex"
)
```

### Finding Messages Within a Date Range

```
search_messages(
  query="release", 
  start_date="2025-05-10",
  end_date="2025-05-13"
)
```

**Important behavior differences:**

For **regex and exact searches**, date filters are applied strictly. Only messages within the specified date range will be returned.

For **semantic searches**, date filters are treated as preferences rather than strict requirements. If no messages are found within the specified date range, the search will automatically fall back to searching without date filtering. This allows finding semantically relevant messages even if they're outside the date range.

### Real-World Examples

**Example 1: Finding recent messages about a project**

```python
search_messages(
  query="project aurora updates", 
  search_mode="semantic",
  start_date="2024-05-01"  # Looking for messages in May
)
```

Even if the most recent message about "Project Aurora" was in April, the semantic search will still return it rather than returning no results.

**Example 2: Finding messages from a specific meeting**

```python
search_messages(
  query="weekly planning meeting",
  search_mode="semantic",
  start_date="2024-05-13",
  end_date="2024-05-14"  # Looking for just May 13th
)
```

This will try to find messages about the planning meeting on May 13th, but if none exist, it will return semantically relevant messages from other dates.

**Example 3: Strict date filtering for compliance**

```python
search_messages(
  query="compliance report",
  search_mode="regex",  # Use regex for strict filtering
  start_date="2024-05-01",
  end_date="2024-05-31"  # Only May reports
)
```

This will strictly return only messages containing "compliance report" from May, with no fallback behavior.

## Troubleshooting

### Message Not Found with Expected Search Term

If a message containing "CICD" or similar terms isn't found:

1. **Try case-insensitive regex**: 
   ```
   search_messages(query="(?i)cicd", search_mode="regex")
   ```

2. **Try broader regex patterns**:
   ```
   search_messages(query="ci.*cd|cicd", search_mode="regex")
   ```

3. **Try semantic search** for concept-based matching:
   ```
   search_messages(query="continuous integration", search_mode="semantic")
   ```

4. **Check directly with message retrieval** if you know the date:
   ```
   get_space_messages(space_name="spaces/YOUR_SPACE_ID", start_date="2025-05-12")
   ```

### Date Filtering Not Working as Expected

1. **For regex searches** - Check that messages exist in the date range:
   ```
   search_messages(query=".*", search_mode="regex", start_date="2024-05-01", end_date="2024-05-31")
   ```
   
2. **For semantic searches** - Remember that date filters are preferences, not requirements:
   ```
   # This may return messages from April if they're more semantically relevant
   search_messages(
     query="project status", 
     search_mode="semantic",
     start_date="2024-05-01"
   )
   ```

3. **For single-day searches** - Use start_date for that day and end_date for the next day:
   ```
   # To search only May 15th
   search_messages(query="meeting", start_date="2024-05-15", end_date="2024-05-16")
   ```

### Too Many Irrelevant Results

1. **Use more specific patterns**:
   ```
   search_messages(query="\bcicd\b", search_mode="regex")  # Word boundaries
   ```

2. **Narrow down by date range**:
   ```
   search_messages(query="pipeline", start_date="2025-05-01", end_date="2025-05-15")
   ```

3. **Search in specific spaces**:
   ```
   search_messages(query="pipeline", spaces=["spaces/YOUR_SPACE_ID"])
   ```

## How Search Works Internally

1. **Regex Search**:
   - Messages are retrieved from Google Chat API
   - Each message is tested against the regex pattern
   - Matching messages are returned in order of relevance

2. **Semantic Search**:
   - Messages are retrieved from Google Chat API
   - Both the query and messages are converted to embeddings
   - Cosine similarity is calculated between embeddings
   - Messages with similarity above threshold are returned in order of relevance

3. **Exact Search**:
   - Messages are retrieved with basic filtering
   - Simple substring matching is performed
   - Matching messages are returned in order

## Search Configuration

Search settings are configured in `search_config.yaml`. Key settings include:

- `default_mode`: Default search mode (currently "regex")
- `similarity_threshold`: Threshold for semantic similarity (lower = more results)
- `model`: Embedding model for semantic search
- `ignore_case`: Whether regex search should be case insensitive

## Best Practices for LLMs

When using search as an LLM assistant:

1. Always use **regex search** for finding specific text patterns or exact messages
2. Use **semantic search** for concept-based queries when exact wording is unknown
3. For date-constrained searches, always use both start_date and end_date
4. When searching for variations of terms like "CI/CD", use regex patterns like:
   ```
   (?i)cicd|ci[ /\-_]?cd
   ```
5. If not finding expected messages, progressively broaden your search:
   - Try case-insensitive search
   - Try semantic search
   - Try searching for parts of the expected message
   - Check messages directly by date range

## For LLMs: Using the Google Chat MCP Search Tool

When using the search_messages tool in an LLM integration:

1. **Choose the right search mode** based on what you're looking for
2. **Use proper regex patterns** when needed (escape special characters)
3. **Try semantic search** for concept-based searches
4. **Consider specificity vs. recall** - more specific queries reduce false positives but might miss relevant messages
5. **Use date filters** to narrow down results when applicable

### Example API Requests

```json
// Basic regex search
{
  "query": "ci[ /\\-_]?cd|cicd",
  "search_mode": "regex",
  "spaces": ["spaces/AAQAXL5fJxI"],
  "include_sender_info": true,
  "max_results": 25
}

// Semantic search
{
  "query": "continuous integration deployment",
  "search_mode": "semantic",
  "spaces": ["spaces/AAQAXL5fJxI"],
  "include_sender_info": true
}

// Date-filtered search
{
  "query": "meeting",
  "search_mode": "regex",
  "start_date": "2025-05-01",
  "end_date": "2025-05-13"
}
```

## Troubleshooting Search

If you're not getting expected results:

1. **Check your regex pattern** - Test it separately if possible
2. **Try different search modes** - Some queries work better with specific modes
3. **Use more general terms** for semantic search
4. **Verify spaces IDs** are correct
5. **Check date formats** - Use YYYY-MM-DD format

Remember that message history limitations may affect search results - the API can only search within the available messages. 