# MIPS32 Instruction Reference

## Instruction Formats

### R-Type (Register)
```
31-26  25-21  20-16  15-11  10-6   5-0
opcode   rs     rt     rd    shamt  funct
  6      5      5      5      5      6
```
- opcode: Always 0x00 for R-type
- rs, rt: Source registers
- rd: Destination register
- shamt: Shift amount (for shift instructions)
- funct: Function code (determines actual operation)

### I-Type (Immediate)
```
31-26  25-21  20-16  15-0
opcode   rs     rt    immediate
  6      5      5       16
```
- opcode: Operation code
- rs: Source register
- rt: Destination register (or second source for branches)
- immediate: 16-bit signed/unsigned value

### J-Type (Jump)
```
31-26  25-0
opcode  address
  6       26
```
- opcode: 0x02 (J) or 0x03 (JAL)
- address: 26-bit target (combined with PC upper bits)

## Opcode Table (bits 31-26)

| Opcode | Hex  | Instruction Type |
|--------|------|------------------|
| 000000 | 0x00 | R-type (see funct) |
| 000001 | 0x01 | REGIMM (BLTZ, BGEZ, etc.) |
| 000010 | 0x02 | J |
| 000011 | 0x03 | JAL |
| 000100 | 0x04 | BEQ |
| 000101 | 0x05 | BNE |
| 000110 | 0x06 | BLEZ |
| 000111 | 0x07 | BGTZ |
| 001000 | 0x08 | ADDI |
| 001001 | 0x09 | ADDIU |
| 001010 | 0x0A | SLTI |
| 001011 | 0x0B | SLTIU |
| 001100 | 0x0C | ANDI |
| 001101 | 0x0D | ORI |
| 001110 | 0x0E | XORI |
| 001111 | 0x0F | LUI |
| 100000 | 0x20 | LB |
| 100001 | 0x21 | LH |
| 100011 | 0x23 | LW |
| 100100 | 0x24 | LBU |
| 100101 | 0x25 | LHU |
| 101000 | 0x28 | SB |
| 101001 | 0x29 | SH |
| 101011 | 0x2B | SW |

## R-Type Function Codes (bits 5-0, when opcode=0x00)

| Funct  | Hex  | Instruction |
|--------|------|-------------|
| 000000 | 0x00 | SLL |
| 000010 | 0x02 | SRL |
| 000011 | 0x03 | SRA |
| 000100 | 0x04 | SLLV |
| 000110 | 0x06 | SRLV |
| 000111 | 0x07 | SRAV |
| 001000 | 0x08 | JR |
| 001001 | 0x09 | JALR |
| 001100 | 0x0C | SYSCALL |
| 010000 | 0x10 | MFHI |
| 010010 | 0x12 | MFLO |
| 011000 | 0x18 | MULT |
| 011001 | 0x19 | MULTU |
| 011010 | 0x1A | DIV |
| 011011 | 0x1B | DIVU |
| 100000 | 0x20 | ADD |
| 100001 | 0x21 | ADDU |
| 100010 | 0x22 | SUB |
| 100011 | 0x23 | SUBU |
| 100100 | 0x24 | AND |
| 100101 | 0x25 | OR |
| 100110 | 0x26 | XOR |
| 100111 | 0x27 | NOR |
| 101010 | 0x2A | SLT |
| 101011 | 0x2B | SLTU |

## REGIMM rt Field (opcode=0x01)

| rt     | Hex  | Instruction |
|--------|------|-------------|
| 00000  | 0x00 | BLTZ |
| 00001  | 0x01 | BGEZ |
| 10000  | 0x10 | BLTZAL |
| 10001  | 0x11 | BGEZAL |

## Register Names

| Number | Name | Usage |
|--------|------|-------|
| $0 | $zero | Always zero |
| $1 | $at | Assembler temporary |
| $2-$3 | $v0-$v1 | Return values |
| $4-$7 | $a0-$a3 | Arguments |
| $8-$15 | $t0-$t7 | Temporaries |
| $16-$23 | $s0-$s7 | Saved |
| $24-$25 | $t8-$t9 | More temporaries |
| $26-$27 | $k0-$k1 | Kernel reserved |
| $28 | $gp | Global pointer |
| $29 | $sp | Stack pointer |
| $30 | $fp | Frame pointer |
| $31 | $ra | Return address |

## Instruction Semantics

### ALU Operations
```
ADD  rd, rs, rt   : rd = rs + rt (trap on overflow)
ADDU rd, rs, rt   : rd = rs + rt (no trap)
SUB  rd, rs, rt   : rd = rs - rt (trap on overflow)
SUBU rd, rs, rt   : rd = rs - rt (no trap)
AND  rd, rs, rt   : rd = rs & rt
OR   rd, rs, rt   : rd = rs | rt
XOR  rd, rs, rt   : rd = rs ^ rt
NOR  rd, rs, rt   : rd = ~(rs | rt)
SLT  rd, rs, rt   : rd = (rs < rt) ? 1 : 0 (signed)
SLTU rd, rs, rt   : rd = (rs < rt) ? 1 : 0 (unsigned)
```

### Immediate Operations
```
ADDI  rt, rs, imm : rt = rs + sign_extend(imm)
ADDIU rt, rs, imm : rt = rs + sign_extend(imm)
SLTI  rt, rs, imm : rt = (rs < sign_extend(imm)) ? 1 : 0
SLTIU rt, rs, imm : rt = (rs < sign_extend(imm)) ? 1 : 0 (unsigned compare)
ANDI  rt, rs, imm : rt = rs & zero_extend(imm)
ORI   rt, rs, imm : rt = rs | zero_extend(imm)
XORI  rt, rs, imm : rt = rs ^ zero_extend(imm)
LUI   rt, imm     : rt = imm << 16
```

### Shift Operations
```
SLL  rd, rt, sa   : rd = rt << sa
SRL  rd, rt, sa   : rd = rt >>> sa (logical)
SRA  rd, rt, sa   : rd = rt >> sa (arithmetic)
SLLV rd, rt, rs   : rd = rt << (rs & 0x1F)
SRLV rd, rt, rs   : rd = rt >>> (rs & 0x1F)
SRAV rd, rt, rs   : rd = rt >> (rs & 0x1F)
```

### Memory Operations
```
LW  rt, offset(rs) : rt = memory[rs + sign_extend(offset)]  (4 bytes)
LH  rt, offset(rs) : rt = sign_extend(memory[rs + offset])  (2 bytes)
LHU rt, offset(rs) : rt = zero_extend(memory[rs + offset])  (2 bytes)
LB  rt, offset(rs) : rt = sign_extend(memory[rs + offset])  (1 byte)
LBU rt, offset(rs) : rt = zero_extend(memory[rs + offset])  (1 byte)
SW  rt, offset(rs) : memory[rs + sign_extend(offset)] = rt  (4 bytes)
SH  rt, offset(rs) : memory[rs + offset] = rt[15:0]         (2 bytes)
SB  rt, offset(rs) : memory[rs + offset] = rt[7:0]          (1 byte)
```

### Branch Operations
```
BEQ  rs, rt, offset : if (rs == rt) PC = PC + 4 + sign_extend(offset) << 2
BNE  rs, rt, offset : if (rs != rt) PC = PC + 4 + sign_extend(offset) << 2
BLEZ rs, offset     : if (rs <= 0) PC = PC + 4 + sign_extend(offset) << 2
BGTZ rs, offset     : if (rs > 0) PC = PC + 4 + sign_extend(offset) << 2
BLTZ rs, offset     : if (rs < 0) PC = PC + 4 + sign_extend(offset) << 2
BGEZ rs, offset     : if (rs >= 0) PC = PC + 4 + sign_extend(offset) << 2
```

### Jump Operations
```
J    target        : PC = (PC & 0xF0000000) | (target << 2)
JAL  target        : $ra = PC + 8; PC = (PC & 0xF0000000) | (target << 2)
JR   rs            : PC = rs
JALR rd, rs        : rd = PC + 8; PC = rs
```

### Multiply/Divide
```
MULT  rs, rt       : (HI, LO) = rs * rt (signed 64-bit result)
MULTU rs, rt       : (HI, LO) = rs * rt (unsigned 64-bit result)
DIV   rs, rt       : LO = rs / rt; HI = rs % rt (signed)
DIVU  rs, rt       : LO = rs / rt; HI = rs % rt (unsigned)
MFHI  rd           : rd = HI
MFLO  rd           : rd = LO
```

## Linux MIPS Syscall Convention

- Syscall number in $v0 (register 2)
- Arguments in $a0-$a3 (registers 4-7)
- Additional arguments on stack
- Return value in $v0
- Error flag in $a3 (non-zero on error)

### Common Syscall Numbers (Linux MIPS o32 ABI)
```
exit        = 4001
read        = 4003
write       = 4004
open        = 4005
close       = 4006
brk         = 4045
mmap        = 4090
munmap      = 4091
gettimeofday = 4078
```

## ELF Header Quick Reference

```
Offset  Size  Field
0x00    4     Magic: 0x7F 'E' 'L' 'F'
0x04    1     Class: 1=32-bit, 2=64-bit
0x05    1     Endian: 1=little, 2=big
0x10    2     Type: 2=executable
0x12    2     Machine: 8=MIPS
0x18    4     Entry point
0x1C    4     Program header offset
0x2C    2     Program header entry size
0x2E    2     Program header count
```

### Program Header (PT_LOAD)
```
Offset  Size  Field
0x00    4     Type: 1=PT_LOAD
0x04    4     File offset
0x08    4     Virtual address
0x10    4     File size
0x14    4     Memory size (includes BSS when > file size)
```
