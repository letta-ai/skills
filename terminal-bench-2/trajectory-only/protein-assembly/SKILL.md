---
name: protein-assembly
description: Guidance for designing and assembling multi-component fusion protein sequences, particularly for FRET biosensors and tagged constructs. This skill applies when tasks involve identifying proteins by spectral properties (excitation/emission wavelengths), assembling fusion proteins from multiple domains, codon optimization with GC content constraints, working with PDB sequences and fluorescent protein databases, or generating gBlock sequences for gene synthesis.
---

# Protein Assembly Skill

This skill provides systematic approaches for designing multi-component fusion protein sequences, with emphasis on FRET biosensor construction, spectral matching, and codon optimization.

## Task Decomposition Strategy

Complex protein assembly tasks require systematic decomposition into discrete, verifiable sub-tasks. Establish clear success criteria for each phase before proceeding.

### Phase 1: Component Identification

Break the assembly into individual components that must be identified:

1. **Fluorescent proteins** - Identify by spectral properties (excitation/emission wavelengths)
2. **Binding domains** - Identify by ligand/substrate specificity (e.g., SNAP-tag for O6-benzylguanine)
3. **Target proteins** - Identify by function (e.g., antibody targets, enzymes)
4. **Linker sequences** - Determine type and length requirements

For each component, document:
- The identification criteria (wavelength, ligand, function)
- The source (PDB ID, database entry, plasmid file)
- The extracted sequence (verify before proceeding)

### Phase 2: Sequence Extraction

Extract and verify each protein sequence before assembly:

1. **PDB sequences**: Use RCSB PDB FASTA endpoint (`https://www.rcsb.org/fasta/entry/{PDB_ID}`)
2. **Fluorescent proteins**: Query FPbase API with wavelength filters
3. **Plasmid sequences**: Parse GenBank format files completely (handle truncation)
4. **Validate extraction**: Confirm sequence length and expected features

### Phase 3: Assembly and Optimization

Assemble components in specified order with linkers, then optimize:

1. Apply N-terminal methionine rules (remove internal Met starts)
2. Insert linker sequences between domains
3. Perform codon optimization for target organism
4. Validate constraints (length, GC content windows)

## Critical Verification Checkpoints

Establish verification checkpoints to prevent cascading errors:

### Checkpoint 1: Spectral Matching
- For FRET pairs, verify donor emission overlaps with acceptor excitation
- Match filter cube specifications exactly (not approximately)
- Document the specific wavelength values being matched

### Checkpoint 2: Sequence Completeness
- Verify API responses are not truncated
- If data exceeds buffer limits, implement pagination or filtering
- Cross-reference sequence lengths with expected values

### Checkpoint 3: Assembly Validation
- Verify component order matches requirements
- Confirm linker lengths within specified constraints
- Check total nucleotide count against limits

### Checkpoint 4: Optimization Validation
- Calculate GC content in sliding windows (typically 50nt)
- Verify all windows fall within acceptable range (e.g., 30-70%)
- Confirm codon usage matches target organism

## Common Pitfalls and Mitigations

### Data Truncation
**Problem**: API responses or file reads may be truncated at character limits.
**Mitigation**:
- Check response completeness before parsing
- Use targeted queries with filters rather than downloading entire databases
- Request specific ranges when reading large files
- Implement pagination for large result sets

### Imprecise Wavelength Matching
**Problem**: Selecting proteins with "close enough" wavelengths instead of exact matches.
**Mitigation**:
- Use FPbase API filtering parameters for excitation/emission ranges
- Query for specific wavelength values, not ranges
- Verify FRET compatibility (donor emission must overlap acceptor excitation)

### Premature Assembly
**Problem**: Attempting to assemble sequences before all components are verified.
**Mitigation**:
- Create explicit checkpoints after each component is identified
- Document each sequence extraction with source and verification
- Do not proceed to assembly until all sequences are confirmed

### Missing Constraint Validation
**Problem**: Generating sequences without validating requirements.
**Mitigation**:
- Build validation logic early in the process
- Check constraints incrementally during codon optimization
- Final validation pass before output generation

### Incomplete File Parsing
**Problem**: Assuming sequence identity without extracting from source files.
**Mitigation**:
- Parse GenBank files to extract CDS features explicitly
- Do not assume sequence identity based on file names
- Verify extracted sequences against annotations

## Systematic Workflow

### Step 1: Parse Requirements
Extract all constraints from the task specification:
- Required spectral properties (exact wavelengths)
- Component ordering requirements
- Linker specifications (type, length range)
- Optimization constraints (GC content, length limits)
- Output format requirements

### Step 2: Identify Components Individually
For each required protein component:
1. Determine identification criteria from requirements
2. Query appropriate database/source
3. Handle complete response (paginate if needed)
4. Extract candidate sequences
5. Verify match against criteria
6. Document source and sequence

### Step 3: Validate FRET Compatibility (if applicable)
For fluorescent protein pairs:
1. Confirm donor excitation matches source
2. Confirm acceptor emission matches detector
3. Verify spectral overlap for energy transfer
4. Document the FRET pair selection rationale

### Step 4: Assemble Construct
1. Order components per specification
2. Remove internal methionines as required
3. Insert appropriate linkers
4. Generate nucleotide sequence

### Step 5: Optimize Codons
1. Select codon table for target organism
2. Optimize with GC content constraints
3. Apply sliding window validation
4. Iterate until all windows pass

### Step 6: Final Validation
1. Verify total length within limits
2. Confirm GC content in all windows
3. Translate back to verify protein sequence
4. Save to specified output location

## Database Query Strategies

### FPbase Queries
- Use wavelength range parameters for initial filtering
- Query individual proteins for detailed spectral data
- Cross-reference excitation AND emission requirements

### PDB Queries
- Fetch FASTA sequences via REST API
- Verify chain identifiers when multiple chains present
- Handle homo-multimeric structures appropriately

### SMILES/Chemical Structure Identification
- Use PubChem or ChEBI for structure identification
- Cross-reference with protein binding databases
- Verify binding protein identity through literature

## Output Generation

### gBlock Sequences
- Verify sequence is within synthesis limits (typically under 3000nt)
- Check for problematic sequences (extreme GC, repeats)
- Include 5' and 3' sequences if required for cloning
- Save to specified output file path

### Documentation
- Record all component sources
- Document selection rationale for each protein
- Note any assumptions or approximations made
