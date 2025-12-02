# Data Preprocessing Patterns for Embedding Tasks

## Common Input Format Issues

### Line Number Prefixes

Many data files include line numbers as navigation aids. These must be stripped before embedding computation.

**Pattern variations:**
```
  1→Document text here
 11→Another document
123→Yet another document
1	Document with tab separator
```

**Removal patterns:**
```python
import re

# Arrow prefix with optional whitespace and digits
line = re.sub(r'^\s*\d+→', '', line)

# Tab separator after numbers
line = re.sub(r'^\s*\d+\t', '', line)

# Any common delimiter after numbers
line = re.sub(r'^\s*\d+[→\t:|]\s*', '', line)
```

### Whitespace Issues

```python
# Strip leading/trailing whitespace
line = line.strip()

# Normalize internal whitespace (multiple spaces to single)
line = ' '.join(line.split())

# Remove non-breaking spaces and other Unicode whitespace
import unicodedata
line = ''.join(c if not unicodedata.category(c).startswith('Z') or c == ' ' else ' ' for c in line)
```

### Empty Line Handling

```python
# Filter after cleaning
documents = [clean(line) for line in raw_lines]
documents = [doc for doc in documents if doc]  # Remove empty strings
```

## Model Selection Reference

### Common Embedding Models by Language

**English:**
- `sentence-transformers/all-MiniLM-L6-v2` - Fast, good quality
- `BAAI/bge-small-en-v1.5` - Small, high quality
- `BAAI/bge-large-en-v1.5` - Large, best quality
- `sentence-transformers/all-mpnet-base-v2` - Balanced

**Chinese:**
- `BAAI/bge-small-zh-v1.5` - Small Chinese model
- `BAAI/bge-large-zh-v1.5` - Large Chinese model

**Multilingual:**
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- `BAAI/bge-m3` - State-of-the-art multilingual

### Model Name Conventions

| Suffix | Meaning |
|--------|---------|
| `-en-` | English-optimized |
| `-zh-` | Chinese-optimized |
| `-m3`, `-multilingual` | Multilingual |
| `-small-` | Smaller, faster |
| `-large-` | Larger, more accurate |
| `-v1.5`, `-v2` | Version indicator |

## Similarity Computation Reference

### Cosine Similarity via Dot Product

When embeddings are L2-normalized, cosine similarity equals dot product:

```python
# Method 1: With normalized embeddings
embeddings = model.encode(texts, normalize_embeddings=True)
similarities = np.dot(doc_embeddings, query_embedding)

# Method 2: Explicit cosine similarity
from sklearn.metrics.pairwise import cosine_similarity
similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
```

### Ranking and Selection

```python
# Sort indices by similarity (descending)
sorted_indices = np.argsort(similarities)[::-1]

# k-th highest (1-indexed to 0-indexed conversion)
k = 5  # Want 5th highest
result_idx = sorted_indices[k - 1]  # Index 4

# Handle ties by checking for equal scores
fifth_score = similarities[sorted_indices[4]]
ties = [i for i in sorted_indices if similarities[i] == fifth_score]
if len(ties) > 1:
    print(f"Warning: {len(ties)} documents tied at rank 5")
```

## Verification Checklist

1. [ ] Document count matches expected input size
2. [ ] Sample documents show clean text (no line numbers, prefixes)
3. [ ] Embedding dimensions match model specification
4. [ ] Top-k results printed with scores for manual verification
5. [ ] Output file contains only semantic content
6. [ ] Ties at target rank noted if present
7. [ ] Model language matches content language
