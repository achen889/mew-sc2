# mew-sc2
mew's python sc2 utilities

mew managers

Specifically Broodmother, ArmyManager and ManageLarvae contains the onscreen debug shown here:

<img width="1279" alt="image" src="https://github.com/achen889/mew-sc2/assets/3443269/58377669-0303-4aa2-8ecd-c5b669df9baa">

Singleton Manager lets me manage all my manager through instances instantiated when the bot calls configure managers.

Mika Queens is my version of integrating the queens_sc2 project into my bot, it currently just has a single helper MikaSetQueenPolicy function that starts it off with the early game queen policy and 7 minutes later switches to the mid game queen policy.

Unit State tracks previous positions when enemy units are visible and I use the information in kiting micro and corrosive bile skillshots.

For the sake of simplicity I copied the singleton manager class into EnemyUnitsManager in sharpy and anywhere else I need it.

I'll hold off on uploading mew micro, I don't want all my secrets to be taken.



