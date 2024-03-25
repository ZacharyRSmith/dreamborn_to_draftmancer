I think I just created the fastest, easiest way to draft Lorcana online. If there is an easier or faster way to draft Lorcana, please let me know!

All you have to do is:
1. Export the draft list from dreamborn to clipboard,
2. paste from clipboard into the bottom of a Draftmancer Custom Card List template,
3. upload to Draftmancer as a Custom Card List, then
4. copy/paste drafted decks back into dreamborn.

Here is the template: https://github.com/ZacharyRSmith/dreamborn_to_draftmancer/blob/main/draftmancer_custom_card_list_template.txt

To import drafted deck into dreamborn.ink:
1. In Draftmancer, copy drafted deck to clipboard using 'Export > CARD NAMES'.
2. In dreamborn.ink , go to 'Deck Builder', then select 'Menu > Import', then paste clipboard into import text field, then select 'Import'.

Using lorcana-api.com data, each card is assigned an ink cost.


# Potential Enhancements

Rarity and other data might be assignable with a one-line change to the python script that creates the template? If someone knows how Draftmancer expects rarity data, I or someone else can make that change then run the script to enhance the template.

## How to support sealed?

To simplify for now, I'll assume the 12th, foil card is just another rare or higher card, and that packs have random color and ink costs (idk whether or not they do).

Change the template to have:

```
[RareOrHigherSlot(3)]
[UncommonSlot(3)]
[CommonSlot(6)]
```

Change the script to read in all 612 cards using https://dreamborn.ink/decks/Xk1wFdToEUoyeb1tvU6V . Using rarity data from lorcana-api.com , put card into appropriate slot section. Number of each card can be determined by script, but more likely you want to set Draftmancer's `withReplacement` to true such that Draftmancer has an unlimited supply of each card?

Specific sets can be selected by changing the script to filter cards by set using data from lorcana-api.com .


# Testing

I tested this on all 612 cards using: https://dreamborn.ink/decks/Xk1wFdToEUoyeb1tvU6V

I successfully exported that into the template, uploaded to Draftmancer, drafted 24 cards, then imported to dreamborn.
