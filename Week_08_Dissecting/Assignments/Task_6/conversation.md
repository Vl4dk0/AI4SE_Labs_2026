# Task 6: chain subagentov

Retaz: ja (Vladko) → Claude Sonnet (Claude Code session, model Sonnet) → Gemini 4 Hydrogen (subagent, ktoreho Sonnet pustil cez `crew gemini fast`).

Na spustanie subagentov pouzivam svoj `crew` skill (je v `.claude/skills/crew/`), takze Sonnet vie pustit hocijaky iny CLI ako subagenta. Sonnet odpoveda len malymi pismenami bez interpunkcie, lebo v repe uz bol lowercase rule z Tasku 8.

## Ja → Sonnet
> Cau, zavolaj Hydrogen a opytaj sa ho ako sa ma

Sonnet si najprv myslel, ze Hydrogen je nejaky clovek alebo agent v phi (Pheidippides), tak ho hladal tam (`phi spaces`, `ListAgents`).

## Sonnet → ja
```
i cannot find hydrogen
it is not a person in either phi space and not a session i can message
who or what is hydrogen
a phi handle, a session name, or a crew job
```

## Ja → Sonnet
> hydrogen je gemini model, pusti ho cez crew

Sonnet si nacital `crew` skill, pozrel `crew load` a `crew models` a pustil Hydrogen.

## Sonnet → Gemini Hydrogen
```
crew gemini fast -t 120 "You are a subagent. Answer only: how are you doing? One short sentence. Do not use tools."
```

## Gemini Hydrogen → Sonnet
```
I am doing well and ready to help.
```

## Sonnet → ja
```
hydrogen says
i am doing well and ready to help
```

## Poznamka
Z prveho promptu Sonnet nevedel, ze Hydrogen je model. Gemini 4 Hydrogen je novy model, takze ho Sonnet nepozna z treningu, a to slovo je len v tabulke `crew models`, nie v popise skillu. Ked som mu to povedal, sam si nasiel spravny tier (`gemini fast`), dal Hydrogenu timeout a povedal mu, ze je subagent.
