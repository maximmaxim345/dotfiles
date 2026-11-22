## Spaces

On the board I group efforts into spaces, like work and personal, and turn each space on or off. Several can be on at once. `state/spaces.json` holds the spaces, the ones that are off, and each effort's space. Efforts without one, and items and threads without an effort, belong to `work`. The board hides what belongs to a space that is off.

Run `bin/space-sync`. It prints one JSON line per thread to change and keeps the parked threads in `state/parked.json`:
- `park`: an idle thread of a started item in a space that is off. Settle it as "Compacting" says, without the checks of sweep step 5, unless it started running since or a reply since my last message asks me something. Its item stays started.
- `restore`: a parked thread whose space is on again, or a thread whose PR news was held. Unsettle it, and when `news` lists anything, send it that news as "PR check" step 3 says.

Reply in one line with the threads you put away or brought back, and stay silent when it printed nothing.
