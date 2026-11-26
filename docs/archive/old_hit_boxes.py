"""ARCHIVED: the old way a hit's boxes were planned, on the minimap.

Not imported by the bot. Kept so it can be brought back (see
docs/archive/old-hit-boxes.md). It ran inside `sweep_mass` in
bot/trial.py, in place of `sweep_screen`, as:

    if plan_first:
        o, b = sweep_planned(io, watch, mapdata, st, target, view, w, order,
                             cam, dest, max_boxes, boxes)
        orders += o
        boxes = b
        continue

It uses these from bot/trial.py: live, select_full, send_at, attack_move,
free_ground_keys, FULL, GOOD_BOX. The last build that used it is commit
9f57b19 (also 0b596a0 and 0fd0cfc, where it could be switched on).
"""


def plan_boxes(pixels, target_xy, order, want):
    """Every box for one view, mapped out before any is drawn (the
    repository owner): from the back (or front), each the `want` pixels
    nearest its starting point, none sharing a pixel. Lists of pixels,
    in the order they are to be drawn."""
    left, plan = set(pixels), []
    while left:
        seed = order(list(left), target_xy, lambda p: live.from_drawn(*p))[0]
        chunk = sorted(left, key=lambda p: (p[0] - seed[0]) ** 2
                       + (p[1] - seed[1]) ** 2)[:max(2, want)]
        plan.append(chunk)
        left -= set(chunk)
    return plan


def sweep_planned(io, watch, mapdata, st, target, view, w, order, cam, dest,
                  max_boxes, boxes):
    """One view of a hit, the boxes mapped out first (the repository
    owner): every box is planned from where our troops stand in this view
    before any is drawn, then drawn and sent one after another, back to
    front, never on ground already boxed. A box that comes out short may
    reach into the ground not yet boxed; what is left is then mapped out
    again with a better size. A full box may have held more: its far half
    is planned again once, after the rest. Returns (orders, boxes drawn
    so far)."""
    want = st.box_px or max(3, round(FULL / max(st.men_per_pixel, 0.2)))
    plan = plan_boxes(view, (w["x"], w["y"]), order, want)
    io.log(f"  hit: {len(plan)} boxes mapped out for this view")
    orders, later, rounds = 0, set(), 0
    while plan:
        if max_boxes is not None and boxes >= max_boxes:
            break
        chunk = plan.pop(0)
        rest = {p for c in plan for p in c}
        boxes += 1
        # the planned box first; if short, it may take in the next ground
        pool = chunk + sorted(rest, key=lambda p: (p[0] - chunk[0][0]) ** 2
                              + (p[1] - chunk[0][1]) ** 2)
        boxed, n = select_full(io, st, chunk[0], pool, cam)
        if n == 0:
            watch.forget(boxed)
        else:
            if dest is not None:
                attack_move(io, *dest)
            else:
                send_at(io, mapdata, st, target)
                free = free_ground_keys(st)
                if st.rekey < len(free):
                    io.combo("ctrl", free[st.rekey])
                    io.sleep(0.04)
                    st.rekey += 1
            orders += 1
            if n >= FULL and len(boxed) > 1:
                later |= set(boxed[len(boxed) // 2:])
        used = set(boxed) | set(chunk)
        if used & rest:
            want = st.box_px or want
            plan = plan_boxes(rest - used, (w["x"], w["y"]), order, want)
        if not plan and later and rounds == 0:
            rounds = 1
            io.sleep(0.3)               # the sent men walk off first
            want = st.box_px or want
            plan = plan_boxes(later, (w["x"], w["y"]), order, want)
            later = set()
    return orders, boxes


