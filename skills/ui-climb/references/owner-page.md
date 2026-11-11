# Owner page

One static page per checkpoint, readable on a phone.

## Layout

1. **Opening line**: which kind of page it is and what to answer. "Proposals for round 6: answer
   Do it, Not now or Tweak per number." or "Check of round 6's build: answer Keep, Drop or Tweak."
2. **Scores**: one row per reviewer and the median, for the product and each reference, this
   round against the last. The owner's cases and the veto row sit apart from the general rows.
3. **One section per screen and appearance**, for example "Thread view (dark)":
   - **Before above, after below**, full width, the same crop.
   - **Numbered callouts** on both images: a solid badge with a white numeral, ringed in white,
     joined by a straight arrow to the exact spot. The same number marks the element on both
     images, following it if it moved.
   - **A legend under the pair**: one short line per number, with values where they exist.
     "Card corners 22px to 16px", "Branch name readable (was 40% opacity)".
4. **Questions** numbered to match the callouts, each with a recommendation and which models
   asked for it. Show what each model said, not a filtered conclusion.
5. **What the shots failed to show**: states not captured, captures that need retaking.

Draw each callout by finding the change on the actual shot, never from the plan. A change with no
visible spot did not land: say so. On web, resolve callout targets from selectors to bounding
boxes so arrows land exactly. Look at the finished page image before sending it, and fix any
arrow that misses its spot.

## Answers

Answers come back in chat as "1 yes, 3 drop, 4 tweak: smaller", so the page stays static: copy
buttons and other scripted controls break in many viewers, phones especially.
