# SPARQL Query Patterns Reference

## Basic Query Structure

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX uni: <http://example.org/university#>

SELECT ?var1 ?var2
WHERE {
  # Triple patterns
  ?subject ?predicate ?object .
}
ORDER BY ?var1
```

## String Matching Patterns

### Starts With
```sparql
FILTER(STRSTARTS(?role, "Professor of"))
```

### Contains
```sparql
FILTER(CONTAINS(?title, "Engineering"))
```

### Compound String Conditions
```sparql
# Match "Professor of X" but not "Assistant Professor of X"
FILTER(STRSTARTS(?role, "Professor of") && !STRSTARTS(?role, "Assistant Professor"))
```

### Regex Matching
```sparql
FILTER(REGEX(?name, "^Dr\\.", "i"))
```

## Value Lists (IN Operator)

### Country Code Filtering
```sparql
# EU-27 member states
FILTER(?countryCode IN (
  "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
  "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
  "NL", "PL", "PT", "RO", "SE", "SI", "SK"
))
```

## Date Handling

### Currently Active (No End Date OR Future End Date)
```sparql
FILTER(!BOUND(?graduationDate) || ?graduationDate >= "2025-01-01"^^xsd:date)
```

### Date Comparison
```sparql
FILTER(?startDate <= "2024-09-01"^^xsd:date && ?endDate >= "2024-09-01"^^xsd:date)
```

## Aggregation Patterns

### Count with Grouping
```sparql
SELECT ?department (COUNT(DISTINCT ?student) AS ?studentCount)
WHERE {
  ?student uni:enrolledIn ?course .
  ?course uni:offeredBy ?department .
}
GROUP BY ?department
HAVING (COUNT(DISTINCT ?student) > 10)
```

### Subquery for Aggregation
```sparql
SELECT ?professor ?country
WHERE {
  ?professor uni:worksIn ?dept .
  ?dept uni:locatedIn ?country .

  # Subquery to count students
  {
    SELECT ?dept (COUNT(DISTINCT ?student) AS ?count)
    WHERE {
      ?student uni:enrolledIn ?course .
      ?course uni:offeredBy ?dept .
    }
    GROUP BY ?dept
    HAVING (COUNT(DISTINCT ?student) > 10)
  }
}
```

## Conditional Existence (EXISTS)

### Filter Based on Related Data
```sparql
SELECT ?professor ?name
WHERE {
  ?professor rdf:type uni:Person .
  ?professor uni:name ?name .

  # Professor must work in at least one qualifying department
  FILTER EXISTS {
    ?professor uni:worksIn ?dept .
    ?dept uni:locatedIn ?euCountry .
    FILTER(?euCountry IN ("DE", "FR", "IT", ...))

    # Department must have >10 students
    ?student uni:enrolledIn ?course .
    ?course uni:offeredBy ?dept .
  }
}
```

## Optional Patterns

### Handle Missing Data
```sparql
SELECT ?person ?name ?email
WHERE {
  ?person rdf:type uni:Person .
  ?person uni:name ?name .
  OPTIONAL { ?person uni:email ?email }
}
```

## DISTINCT Usage

### Avoid Double Counting
```sparql
# Student enrolled in multiple courses counts once per department
SELECT ?dept (COUNT(DISTINCT ?student) AS ?count)
WHERE {
  ?student uni:enrolledIn ?course .
  ?course uni:offeredBy ?dept .
}
GROUP BY ?dept
```

## Common University Ontology Predicates

| Relationship | Example Predicate |
|-------------|-------------------|
| Person → Department | `uni:worksIn`, `uni:memberOf` |
| Person → Role | `uni:hasRole`, `uni:position` |
| Student → Course | `uni:enrolledIn`, `uni:takes` |
| Course → Department | `uni:offeredBy`, `uni:belongsTo` |
| Department → Location | `uni:locatedIn`, `uni:country` |
| Student → Dates | `uni:enrollmentDate`, `uni:graduationDate` |

## Verification Queries

### Check Schema Structure
```sparql
# List all predicates used with a class
SELECT DISTINCT ?predicate
WHERE {
  ?entity rdf:type uni:Person .
  ?entity ?predicate ?object .
}
```

### Sample Data Inspection
```sparql
# Get sample instances with all properties
SELECT ?property ?value
WHERE {
  ?entity rdf:type uni:Professor .
  ?entity ?property ?value .
}
LIMIT 50
```
