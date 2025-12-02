---
name: openssl-selfsigned-cert
description: This skill provides guidance for generating self-signed SSL/TLS certificates using OpenSSL. Use this skill when tasks involve creating private keys, self-signed certificates, certificate signing requests (CSRs), or combined PEM files. It covers verification strategies and common pitfalls in certificate generation workflows.
---

# OpenSSL Self-Signed Certificate Generation

## Overview

This skill provides procedural knowledge for generating self-signed SSL/TLS certificates using OpenSSL command-line tools. It covers key generation, certificate creation, file format conventions, and verification strategies to ensure certificates are correctly generated.

## Workflow

### Step 1: Environment Verification

Before generating certificates, verify the environment:

1. Confirm OpenSSL is installed: `openssl version`
2. Check the target directory exists and is writable
3. Verify no existing files will be silently overwritten (or handle explicitly)

### Step 2: Key and Certificate Generation

Two approaches exist for generating self-signed certificates:

**Approach A: Combined Command (Recommended)**

Generate the private key and certificate in a single command:

```bash
openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt -subj "/CN=localhost"
```

This approach reduces the chance of intermediate failures and is more efficient.

**Approach B: Separate Commands**

Generate the private key first, then create the certificate:

```bash
# Generate private key
openssl genrsa -out server.key 2048

# Generate self-signed certificate
openssl req -new -x509 -key server.key -out server.crt -days 365 -subj "/CN=localhost"
```

### Step 3: Combined PEM File Creation

When a combined PEM file is required, concatenate the certificate and key:

```bash
cat server.crt server.key > server.pem
```

**Note on ordering**: Industry convention typically places the certificate first, then the private key. Some applications may require specific ordering—verify requirements before concatenating.

### Step 4: Verification

Always verify generated artifacts before marking the task complete.

**Verify private key:**
```bash
openssl rsa -in server.key -check -noout
openssl rsa -in server.key -text -noout | grep "Private-Key"
```

**Verify certificate:**
```bash
openssl x509 -in server.crt -text -noout
openssl x509 -in server.crt -noout -dates
openssl x509 -in server.crt -noout -subject -issuer
```

**Verify certificate validity period:**
```bash
openssl x509 -in server.crt -noout -startdate -enddate
```

**Verify self-signed certificate is properly formed:**
```bash
openssl verify -CAfile server.crt server.crt
```

**Verify combined PEM file:**
```bash
openssl x509 -in server.pem -text -noout
openssl rsa -in server.pem -check -noout
```

## Verification Strategies

### File Content Verification

After writing any file (especially scripts), always verify the contents were written correctly:

```bash
cat <filename>
```

This is critical for catching truncated writes or encoding issues.

### Certificate Property Verification

To verify specific certificate properties match requirements:

| Property | Verification Command |
|----------|---------------------|
| Key size | `openssl rsa -in key.pem -text -noout \| grep "Private-Key"` |
| Validity days | `openssl x509 -in cert.pem -noout -dates` (calculate difference) |
| Subject/CN | `openssl x509 -in cert.pem -noout -subject` |
| Issuer | `openssl x509 -in cert.pem -noout -issuer` |
| Serial number | `openssl x509 -in cert.pem -noout -serial` |

### Date Format Extraction

For extracting dates in specific formats:

**OpenSSL default format:**
```bash
openssl x509 -in cert.pem -noout -startdate -enddate
```

**ISO format (YYYY-MM-DD) using date parsing:**
```bash
openssl x509 -in cert.pem -noout -startdate | cut -d= -f2 | xargs -I{} date -d "{}" "+%Y-%m-%d"
```

## Common Pitfalls

### 1. Silent Command Failures

OpenSSL commands may fail silently. Always check exit codes:

```bash
openssl genrsa -out server.key 2048 || echo "Key generation failed"
```

Or use `set -e` in scripts to exit on any failure.

### 2. File Overwrite Without Warning

OpenSSL will overwrite existing files without prompting. To prevent accidental overwrites:

```bash
if [ -f server.key ]; then
    echo "Warning: server.key already exists"
    exit 1
fi
```

### 3. Incomplete File Writes

When writing files (especially via scripts or tools), verify the file was completely written before proceeding. Truncated files can appear successful but contain invalid data.

### 4. Missing Python Dependencies

When using Python for certificate verification with the `cryptography` library:
- Verify the library is installed: `pip show cryptography`
- Use a virtual environment to isolate dependencies
- Check for version-specific API differences (e.g., `not_valid_after_utc` vs `not_valid_after`)

### 5. PEM File Ordering

Different applications expect different orderings in combined PEM files:
- Some expect: certificate, then key
- Others expect: key, then certificate
- Verify application requirements before creating combined files

### 6. Unverified Certificate Properties

Do not assume command flags produce expected results. Always verify:
- `-days 365` actually produces a 365-day validity period
- `-rsa:2048` actually produces a 2048-bit key
- Subject fields are correctly populated

## References

For detailed OpenSSL command options and certificate format specifications, see `references/openssl_commands.md`.
