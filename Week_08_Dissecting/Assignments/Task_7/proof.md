# Proof

Run from the repo root:

```
claude -p "Roll 3d6+2 with the dice tool" --mcp-config .mcp.json --allowedTools mcp__dice__roll_dice
```

Output:

```
I rolled 3d6+2 and got **14**. The dice showed 3, 5 and 4, then +2 was added.
```
