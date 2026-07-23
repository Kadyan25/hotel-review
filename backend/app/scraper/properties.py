from dataclasses import dataclass


@dataclass(frozen=True)
class PropertyDef:
    slug: str
    name: str
    city: str
    booking_url: str


PROPERTIES: list[PropertyDef] = [
    PropertyDef(
        slug="surry-hills",
        name="Surry Hills Budget Hotel - Near Oxford Street",
        city="Sydney",
        booking_url="https://www.booking.com/hotel/au/sydney-city-stay.html",
    ),
    PropertyDef(
        slug="potts-point",
        name="Venus Potts Point Sydney",
        city="Sydney",
        booking_url="https://www.booking.com/hotel/au/venus-potts-point-sydney.html",
    ),
    PropertyDef(
        slug="central-sydney",
        name="Venus Surry Hills",
        city="Sydney",
        booking_url="https://www.booking.com/hotel/au/venus-surry-hills.html",
    ),
    PropertyDef(
        slug="darling-harbour",
        name="Chateau De Venus",
        city="Sydney",
        booking_url="https://www.booking.com/hotel/au/chateau-de-venus.html",
    ),
]
