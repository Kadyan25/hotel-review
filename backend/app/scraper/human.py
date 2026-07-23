"""Behavioral pacing helpers so the scraper doesn't move like a bot.

Speed is not the goal here -- not looking mechanical is. Every wait below is
randomized rather than fixed, and clicks move through a curved path instead
of jumping straight to the target.
"""

import asyncio
import random

from patchright.async_api import Locator, Page

PAGE_LOAD_DELAY = (4.0, 9.0)
PAGINATION_CLICK_DELAY = (3.0, 7.0)
READING_PAUSE = (20.0, 40.0)
READING_PAUSE_EVERY_N_PAGES = 8
SCROLL_STEP_DELAY = (0.15, 0.4)


async def human_delay(low: float, high: float) -> None:
    await asyncio.sleep(random.uniform(low, high))


async def maybe_reading_pause(page_index: int) -> None:
    """Every ~8 pages, pause like someone actually reading, not a loop."""
    if page_index > 0 and page_index % READING_PAUSE_EVERY_N_PAGES == 0:
        await human_delay(*READING_PAUSE)


async def human_scroll_into_view(page: Page, locator: Locator) -> None:
    """Scroll to an element in several small steps instead of one jump."""
    box = await locator.bounding_box()
    if box is None:
        await locator.scroll_into_view_if_needed()
        return

    steps = random.randint(3, 6)
    for _ in range(steps):
        await page.mouse.wheel(0, random.uniform(80, 220))
        await asyncio.sleep(random.uniform(*SCROLL_STEP_DELAY))

    await locator.scroll_into_view_if_needed()


async def human_move_and_click(page: Page, locator: Locator) -> None:
    """Move the mouse through curved waypoints before clicking, not an instant jump."""
    await human_scroll_into_view(page, locator)

    box = await locator.bounding_box()
    if box is None:
        # Element not measurable (e.g. off-screen edge case) -- fall back
        # to a plain click rather than failing the whole run.
        await locator.click()
        return

    target_x = box["x"] + box["width"] / 2 + random.uniform(-3, 3)
    target_y = box["y"] + box["height"] / 2 + random.uniform(-3, 3)

    start_x = target_x + random.uniform(-150, 150)
    start_y = target_y + random.uniform(-100, 100)
    await page.mouse.move(start_x, start_y)

    waypoints = random.randint(3, 5)
    for step in range(1, waypoints + 1):
        fraction = step / waypoints
        # slight curve: overshoot perpendicular offset that shrinks near the target
        wobble = (1 - fraction) * random.uniform(-20, 20)
        x = start_x + (target_x - start_x) * fraction + wobble
        y = start_y + (target_y - start_y) * fraction
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.02, 0.08))

    await asyncio.sleep(random.uniform(0.1, 0.3))
    await page.mouse.click(target_x, target_y)
