# Task 4: profile

Pouzivam Claude Code. Ten nema "profily" s dropdownom. Najblizsie je custom subagent v `.claude/agents/*.md`. Kazdy subagent ma vlastny system prompt, model a zoznam toolov.
Output styles a permission modes tiez menia spravanie, ale nebalia dokopy model a system prompt.
Jeden moj preddefionvany agent je [.claude/agents/web_browser.md](../../../.claude/agents/web_browser.md), browser subagent co pouzivam automatizaciu web taskov. Bezi na modeli `haiku` a robi vsetko prehliadanie webu, aby sa velky obsah stranok nedostal do hlavnej session.
[screenshot.webp](./screenshot.webp)