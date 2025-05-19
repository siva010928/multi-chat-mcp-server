# Google Chat MCP Search Recipes

This document provides practical recipes for common search scenarios using the Google Chat MCP search tools.

## Basic Search Recipes

### 1. Finding Recent Messages About a Topic

To find messages about a specific topic from the last month:

```python
search_messages(
    query="project timeline",
    search_mode="semantic",
    start_date="2024-04-01"
)
```

### 2. Finding Messages with Technical Terms

To find messages containing technical terms with various spellings:

```python
search_messages(
    query="(?i)api|rest|json|http|graphql",
    search_mode="regex"
)
```

### 3. Finding Exact Message Content

To find messages containing a specific phrase (exact match):

```python
search_messages(
    query="please review by EOD",
    search_mode="exact"
)
```

### 4. Finding Messages in a Specific Space

To limit your search to a specific space:

```python
search_messages(
    query="meeting notes",
    spaces=["spaces/AAQAXL5fJxI"]  # Your space ID
)
```

## Advanced Search Recipes

### 5. Finding Messages With Semantic Understanding

To find messages related to a concept even if they don't contain specific keywords:

```python
search_messages(
    query="platform performance issues and bottlenecks",
    search_mode="semantic",
    include_sender_info=True
)
```

This will find messages discussing slowness, latency, timeouts, or system degradation, even if they don't use the exact words in your query.

### 6. Finding Messages with Multiple Conditions

To find messages that contain certain terms in any order:

```python
search_messages(
    query="(?i)budget.*approval|approval.*budget", 
    search_mode="regex"
)
```

### 7. Finding Messages About Code Issues

To find messages discussing code-related problems:

```python
search_messages(
    query="(?i)bug|error|exception|crash|fail|issue|broken",
    search_mode="regex",
    start_date="2024-01-01"
)
```

## Date-Based Recipes

### 8. Finding Messages from Exactly One Day

To find all messages from May 15th, 2024:

```python
search_messages(
    query=".*",  # Match anything
    search_mode="regex",
    start_date="2024-05-15",
    end_date="2024-05-16"  # Not inclusive, so this means up to end of May 15
)
```

### 9. Finding All Messages Since a Certain Date

To find all messages since the beginning of the year:

```python
search_messages(
    query=".*",
    search_mode="regex",
    start_date="2024-01-01"
)
```

### 10. Finding Messages from Last Week

To find messages from the previous week (adjust dates as needed):

```python
search_messages(
    query=".*",
    search_mode="regex",
    start_date="2024-05-06",
    end_date="2024-05-13"
)
```

## Specialized Search Recipes

### 11. Finding Action Items

To find messages containing action items or tasks:

```python
search_messages(
    query="(?i)action item|todo|to-do|task|follow[-\\s]?up|next steps",
    search_mode="regex"
)
```

### 12. Finding Decision Records

To find messages where decisions were made:

```python
search_messages(
    query="(?i)decided|decision|agreed|agreement|conclusion|finalized",
    search_mode="regex"
)
```

### 13. Finding Approval Requests

To find messages requesting approvals:

```python
search_messages(
    query="(?i)approve|approval|sign[ -]?off|green[ -]?light|permission|authorize",
    search_mode="regex"
)
```

## Handling Date Filters with Different Search Modes

### 14. Exact Date Range with Strict Filtering

When you need messages strictly within a date range (will return nothing if no matches):

```python
search_messages(
    query="quarterly report",
    search_mode="regex",  # or "exact"
    start_date="2024-05-01",
    end_date="2024-05-31"
)
```

### 15. Preferred Date Range with Fallback

When you want messages in a date range but will accept older messages if needed:

```python
search_messages(
    query="quarterly financial performance",
    search_mode="semantic",  # Semantic provides fallback behavior
    start_date="2024-05-01",
    end_date="2024-05-31"
)
```

## Troubleshooting Recipes

### 16. No Results Found with Regex

If you're not finding expected results with regex search:

```python
# Try more liberal pattern matching
search_messages(
    query="(?i).*report.*",  # More permissive pattern
    search_mode="regex"
)
```

### 17. Too Many Irrelevant Results with Semantic Search

If semantic search is returning too many irrelevant results:

```python
# Use a more specific query with key terms
search_messages(
    query="detailed quarterly financial performance metrics review for Q1 2024",
    search_mode="semantic"
)
```

### 18. Verifying Date Filter Behavior

To check if there are any messages within a specific date range:

```python
search_messages(
    query=".*",  # Match anything
    search_mode="regex",
    start_date="2024-05-01",
    end_date="2024-05-31"
)
```

## Best Practice Recipes

### 19. Combining Regex and Semantic Search

For important searches, try both regex and semantic approaches:

```python
# First try regex for exact matches
regex_results = search_messages(
    query="budget approval",
    search_mode="regex",
    start_date="2024-05-01"
)

# If no results, try semantic search
if not regex_results.get("messages"):
    semantic_results = search_messages(
        query="budget approval process",
        search_mode="semantic",
        start_date="2024-05-01"
    )
```

### 20. Getting Detailed Sender Information

When you need to know who sent the matching messages:

```python
search_messages(
    query="project status",
    search_mode="semantic",
    include_sender_info=True
)
```

## Tips for Better Search Results

1. **For regex searches:** Use `(?i)` for case insensitivity, `\b` for word boundaries, and `|` for alternatives
2. **For semantic searches:** Use natural language descriptions with key concepts
3. **For date filtering:** Remember that semantic searches treat dates as preferences, not requirements
4. **For high precision:** Use regex with specific patterns
5. **For high recall:** Use semantic search with broader concepts
6. **For single-day searches:** Set start_date to that day and end_date to the next day 