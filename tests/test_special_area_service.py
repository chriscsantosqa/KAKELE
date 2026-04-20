from __future__ import annotations

from kakelebot.core.config import SpecialArea
from kakelebot.features.special_areas import SpecialAreaService


def test_special_area_service_matches_player_inside_area():
    service = SpecialAreaService()

    match = service.match(
        player_position=(100, 200, 7),
        special_areas=[
            SpecialArea(
                name="entry-room",
                x=100,
                y=200,
                z=7,
                width=2,
                height=3,
                policy="wait",
                wait_time_min_ms=500,
                wait_time_max_ms=1000,
            )
        ],
    )

    assert match is not None
    assert match.area.name == "entry-room"
    assert match.wait_time_ms == 1000


def test_special_area_service_returns_none_when_player_is_outside():
    service = SpecialAreaService()

    match = service.match(
        player_position=(99, 199, 7),
        special_areas=[
            SpecialArea(
                name="entry-room",
                x=100,
                y=200,
                z=7,
                width=2,
                height=3,
                policy="wait",
                wait_time_min_ms=500,
                wait_time_max_ms=1000,
            )
        ],
    )

    assert match is None
