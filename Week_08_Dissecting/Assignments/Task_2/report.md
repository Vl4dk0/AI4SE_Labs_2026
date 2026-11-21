# Task 2: custom slash command

Claude Code vie custom slash commands. Markdown subor v `.claude/commands/` sa stane commandom podla nazvu suboru, takze [.claude/commands/beer.md](../../../.claude/commands/beer.md) da `/beer`. Obsah suboru nie je kod, je to proste prompt. Claude Code posle text modelu a model odpovie. V novsich verziach Claude Code sa commands zlucili so skills, ale `.claude/commands/` stale funguje.

`/beer` povie modelu nech odpovie `Good idea!`: [Task_8/conversation.md](../Task_8/conversation.md). 
Tam lowercase rule z Tasku 8 zmenil odpoved na `good idea`, co celkom pekne ukazuje ze ten command je len prompt.
