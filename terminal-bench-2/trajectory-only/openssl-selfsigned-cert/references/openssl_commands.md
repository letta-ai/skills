# OpenSSL Command Reference

## Key Generation Commands

### RSA Key Generation

```bash
# Generate 2048-bit RSA private key
openssl genrsa -out private.key 2048

# Generate 4096-bit RSA private key
openssl genrsa -out private.key 4096

# Generate encrypted private key (prompts for password)
openssl genrsa -aes256 -out private.key 2048
```

### ECDSA Key Generation

```bash
# Generate ECDSA key with P-256 curve
openssl ecparam -name prime256v1 -genkey -noout -out private.key

# Generate ECDSA key with P-384 curve
openssl ecparam -name secp384r1 -genkey -noout -out private.key
```

## Certificate Generation Commands

### Self-Signed Certificate (Combined)

```bash
# Generate key and self-signed certificate in one command
openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt -subj "/CN=example.com"

# With additional subject fields
openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt \
    -subj "/C=US/ST=California/L=San Francisco/O=MyOrg/OU=IT/CN=example.com"
```

### Self-Signed Certificate (From Existing Key)

```bash
# Create self-signed certificate from existing private key
openssl req -new -x509 -key private.key -out certificate.crt -days 365 -subj "/CN=example.com"
```

### Certificate Signing Request (CSR)

```bash
# Generate CSR from existing key
openssl req -new -key private.key -out request.csr -subj "/CN=example.com"

# Generate key and CSR together
openssl req -newkey rsa:2048 -nodes -keyout private.key -out request.csr -subj "/CN=example.com"
```

## Certificate Inspection Commands

### View Certificate Details

```bash
# Full certificate details
openssl x509 -in certificate.crt -text -noout

# Subject only
openssl x509 -in certificate.crt -noout -subject

# Issuer only
openssl x509 -in certificate.crt -noout -issuer

# Serial number
openssl x509 -in certificate.crt -noout -serial

# Validity dates
openssl x509 -in certificate.crt -noout -dates
openssl x509 -in certificate.crt -noout -startdate
openssl x509 -in certificate.crt -noout -enddate

# Fingerprints
openssl x509 -in certificate.crt -noout -fingerprint -sha256
openssl x509 -in certificate.crt -noout -fingerprint -sha1

# Public key
openssl x509 -in certificate.crt -noout -pubkey
```

### Verify Certificate

```bash
# Verify self-signed certificate
openssl verify -CAfile certificate.crt certificate.crt

# Verify certificate against CA
openssl verify -CAfile ca.crt certificate.crt

# Check certificate expiration
openssl x509 -in certificate.crt -noout -checkend 86400  # expires within 24 hours?
```

## Key Inspection Commands

### RSA Key

```bash
# Check RSA key validity
openssl rsa -in private.key -check -noout

# View key details
openssl rsa -in private.key -text -noout

# Extract public key from private key
openssl rsa -in private.key -pubout -out public.key
```

### Verify Key-Certificate Match

```bash
# Compare modulus (should match for RSA)
openssl x509 -in certificate.crt -noout -modulus | openssl md5
openssl rsa -in private.key -noout -modulus | openssl md5
```

## Format Conversion Commands

### PEM to DER

```bash
# Convert certificate
openssl x509 -in certificate.pem -outform DER -out certificate.der

# Convert private key
openssl rsa -in private.pem -outform DER -out private.der
```

### DER to PEM

```bash
# Convert certificate
openssl x509 -in certificate.der -inform DER -outform PEM -out certificate.pem

# Convert private key
openssl rsa -in private.der -inform DER -outform PEM -out private.pem
```

### Create PKCS#12 Bundle

```bash
# Create PKCS#12 file (prompts for password)
openssl pkcs12 -export -out bundle.p12 -inkey private.key -in certificate.crt

# With CA certificate chain
openssl pkcs12 -export -out bundle.p12 -inkey private.key -in certificate.crt -certfile ca-chain.crt
```

### Extract from PKCS#12

```bash
# Extract certificate
openssl pkcs12 -in bundle.p12 -clcerts -nokeys -out certificate.crt

# Extract private key
openssl pkcs12 -in bundle.p12 -nocerts -nodes -out private.key
```

## Subject Field Reference

| Field | Abbreviation | Example |
|-------|--------------|---------|
| Country | C | US |
| State/Province | ST | California |
| Locality/City | L | San Francisco |
| Organization | O | MyCompany |
| Organizational Unit | OU | IT Department |
| Common Name | CN | example.com |
| Email Address | emailAddress | admin@example.com |

### Subject Format Examples

```bash
# Minimal (CN only)
-subj "/CN=example.com"

# Standard
-subj "/C=US/ST=California/L=San Francisco/O=MyCompany/CN=example.com"

# Full
-subj "/C=US/ST=California/L=San Francisco/O=MyCompany/OU=IT/CN=example.com/emailAddress=admin@example.com"
```

## Common Options Reference

| Option | Description |
|--------|-------------|
| `-nodes` | Do not encrypt the private key |
| `-days N` | Certificate validity in days |
| `-x509` | Output a self-signed certificate instead of a CSR |
| `-newkey rsa:N` | Generate new RSA key with N bits |
| `-keyout FILE` | Output private key to FILE |
| `-out FILE` | Output certificate/CSR to FILE |
| `-in FILE` | Input file |
| `-text` | Print in human-readable form |
| `-noout` | Do not output the encoded version |
| `-subj SUBJ` | Set subject name directly |
| `-check` | Check consistency of key |

## Error Handling

### Common Errors and Solutions

**"unable to write 'random state'"**
- OpenSSL cannot write to random seed file
- Solution: Set `RANDFILE` environment variable or use `-rand` option

**"problems making Certificate Request"**
- Usually caused by invalid subject format
- Solution: Check subject string escaping and field values

**"No such file or directory"**
- Input file not found
- Solution: Verify file path and permissions

**"unable to load Private Key"**
- Key file format issue or password required
- Solution: Check file format (PEM/DER) and provide password if encrypted
