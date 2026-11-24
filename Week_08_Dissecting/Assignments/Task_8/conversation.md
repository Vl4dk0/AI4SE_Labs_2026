# Task 8: test rule

Rule subor: [.claude/rules/lowercase-only.md](../../../.claude/rules/lowercase-only.md). Claude Code pri starte nacita kazdy `.md` subor z `.claude/rules/` a ma rovnaku prioritu ako projektovy CLAUDE.md.

Test: cista Claude Code session s Claude Haiku, pustena z rootu repa (`crew claude fast -C . "..."`). Model nedostal ziadnu inu instrukciu.

## Turn 1
**Me:** why are keyboards so expensive ?

**Claude Haiku:**
```
the main reason is the switches
a switch is the small part under each key that registers a press
a mechanical switch has many tiny parts and each part costs money to make
keyboards also sell in small batches so each unit costs more to build
enthusiast boards add metal cases and thick keycaps and those cost more
hot swap sockets let you change switches easily but add more parts
you also pay for the brand and the design
cheap keyboards use a rubber sheet with plastic keys and they are made in huge runs so they cost very little
```

## Turn 2 (ta ista session)
**Me:** /beer

**Claude Haiku:**
```
good idea
```

## Vysledok
Rule drzala v oboch turnoch, iba male pismena, medzery a novy riadok.
V turne 2 rule dokonca premohla `/beer`, ktory chce presny text `Good idea!`. Model vyhodil velke pismeno aj `!`, aby rule dodrzal.
