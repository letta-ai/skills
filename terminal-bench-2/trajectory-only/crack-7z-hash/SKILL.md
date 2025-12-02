---
name: crack-7z-hash
description: This skill provides guidance for cracking 7z archive password hashes. It should be used when tasks involve extracting hashes from password-protected 7z archives, selecting appropriate cracking tools, and recovering passwords through dictionary or brute-force attacks. Applicable to password recovery, security testing, and CTF challenges involving encrypted 7z files.
---

# Crack 7z Hash

## Overview

This skill guides agents through the process of extracting and cracking password hashes from 7z archives. It covers hash extraction, tool selection, attack methodology, and verification procedures essential for successful password recovery.

## Workflow

### Step 1: Hash Extraction

Before cracking, extract the hash from the 7z archive using appropriate tools.

**Primary tool: 7z2john**
```bash
# Locate 7z2john (usually part of john the ripper)
locate 7z2john.pl
# or
find /usr -name "7z2john*" 2>/dev/null

# Extract hash from archive
7z2john.pl archive.7z > hash.txt
# or if using Python version
7z2john.py archive.7z > hash.txt
```

**Verify hash extraction:**
- The output should contain a hash string starting with `$7z$` or similar format
- Check the hash file is not empty
- Confirm the hash format matches expected 7z encryption type

**Common issues:**
- Archive not encrypted: No hash will be extracted
- Corrupted archive: Extraction may fail
- Multiple encrypted files: May produce multiple hashes

### Step 2: Hash Format Identification

Identify the hash type to select the correct cracking mode.

**7z hash formats:**
- `$7z$0$` - 7z with AES-256 + SHA-256 (most common)
- `$7z$1$` - 7z with older encryption
- `$7z$2$` - 7z variant formats

**Verify format compatibility:**
```bash
# For hashcat, check supported modes
hashcat --help | grep -i 7z
# Mode 11600 = 7-Zip

# For john, check format support
john --list=formats | grep -i 7z
```

### Step 3: Tool Selection and Configuration

Choose the appropriate cracking tool based on available resources.

**Hashcat (GPU-accelerated, faster for large wordlists):**
```bash
# Basic dictionary attack
hashcat -m 11600 hash.txt wordlist.txt

# With rules for password variations
hashcat -m 11600 hash.txt wordlist.txt -r rules/best64.rule

# Brute-force with mask (e.g., 6-8 lowercase letters)
hashcat -m 11600 hash.txt -a 3 ?l?l?l?l?l?l?l?l --increment --increment-min 6
```

**John the Ripper (CPU-based, good for varied attacks):**
```bash
# Basic dictionary attack
john --wordlist=wordlist.txt hash.txt

# With rules
john --wordlist=wordlist.txt --rules hash.txt

# Incremental mode
john --incremental hash.txt
```

### Step 4: Wordlist Selection

Choose appropriate wordlists based on the context.

**Common wordlists:**
- `/usr/share/wordlists/rockyou.txt` - General passwords
- `/usr/share/seclists/Passwords/` - Various password lists
- Custom wordlists based on context (usernames, dates, etc.)

**Wordlist strategies:**
1. Start with common password lists (rockyou, common-passwords)
2. Try context-specific wordlists if available
3. Use rules to generate variations
4. Fall back to brute-force for short passwords

### Step 5: Execute Cracking Attack

Run the selected tool and monitor progress.

**Monitor and document:**
- Record the command used
- Note the start time
- Monitor progress/speed
- Capture any errors or warnings

**Example session with hashcat:**
```bash
# Start attack with status updates
hashcat -m 11600 hash.txt wordlist.txt --status --status-timer=60

# Check status during run
hashcat -m 11600 hash.txt --status

# Show cracked passwords
hashcat -m 11600 hash.txt --show
```

### Step 6: Verification

**CRITICAL: Always verify the cracked password works.**

```bash
# Test with 7z command
7z t -p"recovered_password" archive.7z

# Or extract to verify
7z x -p"recovered_password" archive.7z -o./extracted/
```

**Verification checklist:**
- [ ] Password successfully extracted from cracking tool output
- [ ] Password tested against original archive
- [ ] Archive contents successfully accessed
- [ ] Document the working password

## Common Pitfalls

### Incomplete Documentation
Always document each step:
- Commands executed
- Tool outputs
- Errors encountered
- Final results

### Skipping Verification
Never assume a cracked hash means success. The password must be verified against the actual archive.

### Wrong Hash Mode
Ensure the hash mode matches the 7z encryption type. Mode 11600 is standard but verify format.

### Resource Exhaustion
Long-running attacks can consume significant resources:
- Monitor CPU/GPU usage
- Use `--session` flag to save progress
- Consider time limits for bounded tasks

### Missing Dependencies
Verify tools are installed before starting:
```bash
which hashcat john 7z 7z2john.pl
```

## Verification Strategies

1. **Hash Validity Check**: Ensure extracted hash matches expected format
2. **Tool Compatibility Check**: Verify cracking tool recognizes the hash
3. **Password Verification**: Test recovered password against archive
4. **Content Verification**: Confirm archive contents are accessible

## Output Requirements

A successful completion should document:
1. The extracted hash (or confirmation of extraction)
2. The tool and method used
3. The recovered password
4. Verification that the password works
5. Any relevant errors or warnings encountered
