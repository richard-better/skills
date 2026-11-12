# Owner page

One page per checkpoint, built by [scripts/owner_page.py](../scripts/owner_page.py) from a JSON
spec (format in the script's docstring). Write the spec beside the round's shots, for example
`rounds/<n>/page/owner-page.json`, and run `owner_page.py <spec>` to get the `.html` next to it.

The owner reads each fix next to the spot it touches. Every fix is a card with close-ups of its
spots at a readable zoom, one per spot (nearby spots share one). On a wide screen the full shot
sits beside the list with a numbered gutter, the selected fix opens its close-ups, and clicking a
number or highlight selects its fix. On a phone the cards stack. A sticky toolbar switches
between the Fixes and Scores pages and sets how every image compares before and after: Before
and After as words, then icons for a slider to drag across, an onion skin with a fader, and a
difference blend where only changed pixels light up. Highlights can be switched off to judge
the pixels under them. Answer buttons build the reply line. The page is
plain HTML first: without scripts it shows the slider at 50%, and answers in chat always work.

## Content

1. **Lead**: which kind of page it is and what to answer. "Proposals for round 6: answer
   Do it, Not now or Tweak per number." or "Check of round 6's build: answer Keep, Drop or Tweak."
2. **Scores**: one row per rubric group, one column per reviewer plus the median, for the product
   and each reference, this round against the last. Put the owner's cases and the veto row on
   separate rows from the general ones. They sit on their own Scores page under a one-line `summary`
   saying what moved and whether it beat the noise floor. Each rubric group is a card that
   plots every reviewer and the median per build; `targets` (`{"General": 8.5}`) draws the target.
3. **Shots**: one per screen, state and appearance ("Homepage (dark)", "Wise hover card"), the
   clean capture with nothing drawn on it, with a `short` name for the shot switcher. On a check
   page, give the same crop before and after.
4. **Items**, numbered, one per fix: a short title, the change with values where they exist
   ("Card corners 22px to 16px"), your recommendation as `rec`, a `note` when your call differs
   from or narrows what the models asked, and which models asked (`Sol 2/3 · Opus 3/3`). Show what
   each model said, not a filtered conclusion.
5. **Contests**: a contest between built variants is one item with `choices` (["dark", "Dark
   cards"]) and a shot whose before and after are the two variants, labelled with `names`. Never
   present a variant that is not built as "after".
6. **Missing**: states not captured, captures that need retaking.

Give scores one value per cell: a row per build or subject, never "7.5 / 8 / 7".

## Highlight boxes

Each item gives the box of every element it touches, in shot pixels. On web, resolve them from
selectors in the capture script, never by eye:

```js
const r = await page.locator(sel).first().boundingBox(); // CSS px, page coordinates
const box = [(r.x - clip.x) * dpr, (r.y - clip.y) * dpr,
             (r.x + r.width - clip.x) * dpr, (r.y + r.height - clip.y) * dpr];
```

`clip` is the screenshot's clip and `dpr` its device scale factor. For a full-page shot, add
`scrollY` to `r.y` first. On a check page, give `before_boxes` when the element moved, and `[]`
when it is new. On native, find the box from the accessibility tree or measure it on the shot.

Give each spot its own box, as tight as the change: "Staff Engineer", not its whole paragraph.
The close-ups are built from the boxes, so a full-width box gives a full-width strip that is too
small to judge. Pass `crops` only when the automatic close-ups miss.

Mark the spot on the actual shot, never from the plan. A change with no visible spot did not
land: say so. Before sending, look at the rendered page and fix any highlight that misses its
element.

## Showing it

In T3 Code, `html_render` the page by its path; local shots load from their absolute paths. For
viewers that cannot read local files, build with `--embed` to inline the shots.

## Answers

The reply line reads like "1-6 yes, 7 no, 12 tweak", or "go with recs" when every answer matches
the recommendation. The owner pastes it, or types the same in chat, and adds how to tweak.
