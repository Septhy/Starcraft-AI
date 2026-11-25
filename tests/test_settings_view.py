"""The recommended settings page."""
from bot import settings_view


def texts():
    return [op[3] for op in settings_view.layout() if op[0] == "text"]


def test_the_page_lists_the_resolution_and_the_video_settings():
    t = texts()
    assert any("1920 x 1080" in x for x in t)
    assert "Windowed (Fullscreen)" in t
    for name, on in settings_view.VIDEO["boxes"]:
        assert name in t
    # ticked boxes carry the yellow mark, unticked ones none
    yellow = [op for op in settings_view.layout()
              if op[0] == "rect" and op[6] == settings_view.YELLOW]
    assert len(yellow) == sum(on for _, on in settings_view.VIDEO["boxes"]) \
        + settings_view.VIDEO["fps_cap"]


def test_the_page_draws_without_a_screen(tmp_path):
    im = settings_view.picture(str(tmp_path / "page.png"))
    assert im.size == (settings_view.W, settings_view.H)
