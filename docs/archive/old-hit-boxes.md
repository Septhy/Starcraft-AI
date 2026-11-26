# Backup: the old way of planning a hit's boxes (on the minimap)

Replaced by `sweep_screen` in bot/trial.py (boxes planned on the game
screen, the repository owner's choice after trial 36). Kept as a backup:
the code is in `docs/archive/old_hit_boxes.py`, and the whole bot as it was
is on the branch `backup/minimap-hit-boxes` (commit 9f57b19).

## How it worked

For each pass of a hit (`hit` → `sweep_mass`, up to 4 passes):

1. The minimap was read twice, 0.6 s apart; our pixels standing still in
   both, within 15 minimap pixels of the mass point, were the mass.
2. They were cut into screen-sized views (`live.clusters(there, 20, 8)`),
   ordered from the back (farthest from the target) to the front.
3. For each view the camera was put on it, and every box was mapped out
   from the minimap before any was drawn (`plan_boxes`): from the back-most
   pixel, the nearest `want` pixels made one box; those pixels were taken,
   and the next back-most pixel started the next box. `want` came from how
   many men a minimap pixel had held in earlier boxes (`st.box_px`, or
   12 / `st.men_per_pixel`).
4. The boxes were drawn one after another (`sweep_planned`), each through
   `select_full`: the box round its pixels, turned into screen pixels with
   the estimated camera (`box_around`), was dragged, and the game's count
   read. Short (under 9): it could reach into the pixels not yet boxed, and
   the rest of the view was mapped out again with a bigger size. Full (12):
   its far half went on a "later" list, boxed again once after the rest of
   the view. Scouts picked up were dropped (`drop_scouts`).
5. Each box was sent with `send_at` (attack-move to a spot along the
   target's front) and, while ground keys were free, put on the next key.

## Why it was replaced

- A minimap pixel is about a tile, and the screen position worked out from
  it can be a tile or two off, so boxes sat beside the men, or across men
  just sent who had not walked off (the same men boxed twice, trial 34).
- In the test game the screen boxes sent the first hit faster (35.5 s and
  29.2 s against 38.8 s and 39.0 s) and sent more of the army by the end
  in three of four camera variants (286, 283, 228, 274 of 307 against
  243, 299, 233, 185).

## To bring it back

Copy `plan_boxes` and `sweep_planned` from `docs/archive/old_hit_boxes.py`
back into bot/trial.py (before `sweep_mass`), and in `sweep_mass` call
`sweep_planned(io, watch, mapdata, st, target, view, w, order, cam, dest,
max_boxes, boxes)` where it now calls `sweep_screen`. Or build from the
branch `backup/minimap-hit-boxes`.
