"""Offline fallback stories.

The engine refreshes from live RSS feeds. If a machine is offline (or every
feed is rate limited) the API still returns this curated set so the demo
never opens on an empty screen.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Article


def _iso(hours_ago: float) -> str:
    moment = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


_RAW: list[dict] = [
    {
        "id": "seed-quiet-machines",
        "title": "Quiet machines: inside the labs teaching silicon to listen",
        "summary": (
            "A generation of tiny, low-power models is moving speech recognition out of "
            "the data centre and onto the device — rewriting what a pocket computer can hear."
        ),
        "body": [
            "The room is deliberately dull: grey carpet, grey desks, one window. The only "
            "thing that moves is a row of matchbox-sized boards, each listening to a loop of "
            "recorded street noise and labelling what it hears. Nobody is watching them. That "
            "is the point.",
            "For a decade, the assumption was that understanding speech required scale — "
            "thousands of chips in a cooled building, trained on an ocean of audio. The "
            "engineers here are testing the opposite claim: that a model small enough to fit "
            "in a hearing aid can be good enough, if you spend your effort on the right "
            "problems.",
            "The trade-off is not free. Small models fail gracefully in ways large ones do "
            "not, and every demo eventually meets a corridor, a crowd, a car window. But the "
            "direction is clear. When comprehension costs almost nothing, it stops being a "
            "feature and becomes a material — something you build with rather than budget for.",
        ],
        "source": "Nexora Wire",
        "category": "tech",
        "read_minutes": 4,
        "hours_ago": 1.5,
    },
    {
        "id": "seed-harbour",
        "title": "The long route home: how a fishing village rebuilt its harbour",
        "summary": (
            "After the storm took the pier, the village spent four winters arguing about "
            "whether to rebuild it — and discovered the argument was really about who stays."
        ),
        "body": [
            "The storm arrived at four in the morning and left before breakfast, which is "
            "why people still talk about it as a rumour. What it took was the pier: ninety "
            "metres of timber that had, for a century, been the difference between a village "
            "and a coastline.",
            "The first plan was concrete and quick. The second was concrete and cheaper. "
            "What was finally built, four winters later, is neither: a low wooden deck on "
            "stone footings, wide enough for two carts, with a slip that can be dragged clear "
            "before weather comes in.",
            "The harbour works because the village stopped designing it for the fleet it had "
            "and started designing it for the one it wanted. That is a subtle thing to put "
            "in a planning document. It is a very obvious thing to see at six in the morning, "
            "when the boats come back in.",
        ],
        "source": "Nexora Wire",
        "category": "world",
        "read_minutes": 5,
        "hours_ago": 3.0,
    },
    {
        "id": "seed-star-charts",
        "title": "A sky full of paper: the unlikely revival of analog star charts",
        "summary": (
            "Planetarium attendance is up, screens are down, and the most requested item at "
            "observatory gift shops is a folded sheet of cardstock."
        ),
        "body": [
            "A star chart is a stubborn object. It cannot be searched, it cannot be updated, "
            "and it is wrong by a small, measurable amount every year. It is also selling "
            "better than it has in three decades.",
            "Curators point to a simple explanation: the chart is a map you can hold while "
            "looking up. Phones are bright, and the sky is dark, and the two do not coexist "
            "comfortably. The chart asks nothing of you except that you turn it.",
            "There is a lesson in the printing, too. The best-selling charts are not the most "
            "accurate ones. They are the ones with generous margins and a spot to write the "
            "date, because the point was never the map. It was the evening.",
        ],
        "source": "Nexora Wire",
        "category": "science",
        "read_minutes": 3,
        "hours_ago": 6.0,
    },
    {
        "id": "seed-corner-store",
        "title": "Small shops, big ledgers: the new economics of the corner store",
        "summary": (
            "Independent grocers are discovering that the cheapest efficiency programme is "
            "knowing what their neighbours actually eat."
        ),
        "body": [
            "The freezer aisle in this shop is three metres long, and eleven of its products "
            "are stocked because one family buys them every week. The owner can name the "
            "family. That is not sentiment; it is inventory management.",
            "Chains optimise for the average customer, which is a person who does not exist "
            "in any single postcode. Independents optimise for the actual ones, and the gap "
            "between those two things is where the margin lives.",
            "The hard part is time. It takes an hour of attention per week to notice what "
            "changed, and attention is the one input a small shop cannot buy more of. The "
            "shops that survive tend to be the ones where somebody enjoys that hour.",
        ],
        "source": "Nexora Wire",
        "category": "business",
        "read_minutes": 4,
        "hours_ago": 9.0,
    },
    {
        "id": "seed-borrowed-guitar",
        "title": "Notes on a borrowed guitar",
        "summary": (
            "A short essay on the strange intimacy of playing an instrument that belongs to "
            "someone else — and what it teaches about taste."
        ),
        "body": [
            "It had a high action and a dead third string, and for a month it was the best "
            "guitar I had ever played, because it was the only one in the house.",
            "Instruments are opinionated. A borrowed one argues with you about how you hold "
            "your wrist, which notes you avoid, how loudly you are willing to be wrong. You "
            "can learn a great deal about someone by the wear on their fretboard.",
            "I gave it back with new strings and a small dent I have never confessed to. I "
            "have owned better guitars since. I have not played anything as carefully.",
        ],
        "source": "Nexora Wire",
        "category": "culture",
        "read_minutes": 2,
        "hours_ago": 14.0,
    },
    {
        "id": "seed-slow-cities",
        "title": "What cities learn when they slow down",
        "summary": (
            "Lower speed limits were sold as a safety measure. Three years of data suggests "
            "they quietly rewrote the economics of a street."
        ),
        "body": [
            "The change was twenty kilometres an hour, applied to eleven streets, and it was "
            "expected to be invisible. Instead, shopfront occupancy on those streets rose "
            "while comparable streets held flat.",
            "Planners offer a cautious reading: slower traffic makes a pavement usable, a "
            "usable pavement makes a walk, and a walk is the cheapest thing a high street has.",
            "None of this is an argument for doing it everywhere. Streets are not "
            "interchangeable, and the same intervention can empty a road that exists to move "
            "people through. The interesting part is that anyone measured at all.",
        ],
        "source": "Nexora Wire",
        "category": "world",
        "read_minutes": 4,
        "hours_ago": 22.0,
    },
]

SEED_ARTICLES: list[Article] = [
    Article(
        id=item["id"],
        title=item["title"],
        summary=item["summary"],
        body=item["body"],
        source=item["source"],
        category=item["category"],
        category_label={
            "world": "World",
            "tech": "Technology",
            "science": "Science",
            "business": "Business",
            "culture": "Culture",
        }.get(item["category"], "World"),
        url="",
        image=None,
        published_at=_iso(item["hours_ago"]),
        read_minutes=item["read_minutes"],
    )
    for item in _RAW
]
