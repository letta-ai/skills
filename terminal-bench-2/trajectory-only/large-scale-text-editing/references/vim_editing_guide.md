# Vim Large-Scale Editing Reference

This reference provides detailed Vim commands and patterns for large-scale text transformations.

## Substitution Commands

### Basic Syntax

```vim
:[range]s/pattern/replacement/[flags]
```

- `%` - All lines in file
- `1,100` - Lines 1 through 100
- `.,$` - Current line to end of file
- `g` flag - Replace all occurrences on each line
- `c` flag - Confirm each replacement
- `i` flag - Case insensitive

### Common Patterns

#### Whitespace Removal
```vim
:%s/\s\+//g           " Remove all whitespace
:%s/^\s\+//           " Remove leading whitespace
:%s/\s\+$//           " Remove trailing whitespace
:%s/\s\+/ /g          " Collapse multiple spaces to single space
```

#### Case Transformations
```vim
:%s/.*/\U&/           " Uppercase entire line
:%s/.*/\L&/           " Lowercase entire line
:%s/\<\w/\u&/g        " Capitalize first letter of each word
:%s/\([^,]*\)/\U\1/   " Uppercase first CSV field
```

#### CSV Column Operations
```vim
" Reorder 3 columns: ABC -> CBA
:%s/\([^,]*\),\([^,]*\),\([^,]*\)/\3,\2,\1/

" Reorder 3 columns: ABC -> BCA
:%s/\([^,]*\),\([^,]*\),\([^,]*\)/\2,\3,\1/

" Delete second column (3 columns to 2)
:%s/\([^,]*\),[^,]*,\([^,]*\)/\1,\2/

" Add new column at end
:%s/$/,new_value/
```

#### Field Matching
```vim
[^,]*     " Match any characters except comma (non-greedy for CSV)
[^,]\+    " Match one or more non-comma characters
\([^,]*\) " Capture group for CSV field
```

## Macros

### Recording and Playback

```vim
qa        " Start recording into register a
<commands>
q         " Stop recording

@a        " Play macro once
@@        " Repeat last macro
10@a      " Play macro 10 times
:%normal @a  " Apply macro to all lines
```

### Macro Content Verification

```vim
:registers a    " Show content of register a
:echo @a        " Display macro content
```

### Setting Macros Programmatically

```vim
let @a = '0f,ldt,A,\<Esc>p'
```

Note: In Vimscript strings:
- `\<Esc>` represents the Escape key
- `\\` represents a literal backslash
- Special keys use `\<keyname>` format

## Keystroke Counting

### What Counts as a Keystroke

| Action | Keystroke Count |
|--------|-----------------|
| Single character (a, b, 1, etc.) | 1 |
| Escape key | 1 |
| Enter key | 1 |
| Ctrl+key combination | 1 |
| `:` command mode entry | 1 |
| Each character in `:` command | 1 each |

### Escape Sequences in Vimscript

When counting keystrokes from a Vimscript `let @a = '...'` statement:

| In Script | Actual Keys | Count |
|-----------|-------------|-------|
| `\\s` | `\s` | 2 |
| `\\+` | `\+` | 2 |
| `\<Esc>` | Escape | 1 |
| `\<CR>` | Enter | 1 |

### Example Counting

Script: `let @a = ':s/\\s\\+//g\<CR>'`

Actual keystrokes:
1. `:` - enter command mode
2. `s`
3. `/`
4. `\`
5. `s`
6. `\`
7. `+`
8. `/`
9. `/`
10. `g`
11. Enter

Total: 11 keystrokes

## Running Vim Scripts

### From Command Line

```bash
# Run script on file
vim -s script.vim input.txt

# Run Ex commands directly
vim -c '%s/foo/bar/g' -c 'wq' input.txt

# Silent/headless mode
vim -es -c '%s/foo/bar/g' -c 'wq' input.txt
```

### Script Structure

```vim
" transform.vim

" Define macros
let @a = 'macro_content'
let @b = 'another_macro'

" Perform substitutions
%s/pattern1/replacement1/g
%s/pattern2/replacement2/g

" Apply macros
%normal @a

" Save and quit
wq
```

## Performance Considerations

### For Large Files (>100K lines)

1. **Disable features during editing**:
   ```vim
   :set noswapfile
   :set nobackup
   :set nowritebackup
   :syntax off
   ```

2. **Use `:silent` for commands**:
   ```vim
   :silent %s/pattern/replacement/g
   ```

3. **Prefer single global substitutions over macros when possible**:
   - `:%s/...` is faster than `:%normal @a` for simple replacements

### Batch Operations

For multiple operations, chain them efficiently:

```vim
" Less efficient: multiple passes
:%s/\s\+//g
:%s/.*/\U&/
:%s/\([^,]*\),\([^,]*\),\([^,]*\)/\3,\2,\1/

" More efficient if possible: combine into single pass
" (only when operations don't conflict)
```

## Verification Commands

### In Vim

```vim
:!wc -l %              " Line count of current file
:!head -20 %           " View first 20 lines
:!diff % expected.csv  " Compare with expected output
```

### Exit Codes

- Vim exits with code 0 on successful `:wq`
- Check with `echo $?` after Vim command completes

## Common Regex Pitfalls

| Issue | Wrong | Correct |
|-------|-------|---------|
| Greedy match eating delimiters | `.*,` | `[^,]*,` |
| Missing escape for special chars | `\s+` | `\s\+` |
| Not anchoring patterns | `s/foo/bar/` | `s/\<foo\>/bar/` (word boundary) |
| Forgetting `g` flag | `:%s/a/b/` | `:%s/a/b/g` (all occurrences) |
