import asyncio
import functools
import itertools
import logging
import math
import re
from datetime import datetime, timedelta

import aiometer
import httpx
from starlette.status import HTTP_200_OK

from ....conf import settings
from ....helpers.amadeus import Amadeus

logger = logging.getLogger(__name__)


SLEEP_AFTER_OBTAINING_TOKEN_SECONDS = 0.5
SOURCE_DATE_FORMAT = "%Y-%m-%d"

FILTER_SEGMENTS_ADDITIONAL_ACCEPTABLE = 1
FILTER_PRICE_LEFTOVER_PERCENTAGE = 0.3
FILTER_TIME_LEFTOVER_PERCENTAGE = 0.3
FILTER_ENTRY_RESULTS_LIMIT = 250


def duration_display(iso_duration):
    val = iso_duration.replace("PT", "")

    for day in range(1, 10):
        val = val.replace(f"P{day}DT", f"{day}D ")
        val = val.replace(f"P{day}D", f"{day}D ")

    return val.lower()


def duration_total_in_hours(duration_str):
    duration_str = duration_display(duration_str)

    if not duration_str:
        return 0

    match = re.match(r"(?P<days>\w+)d (?P<hours>\w+)h(?P<minutes>\w+)m", duration_str)

    if match is not None:
        days, hours, minutes = match.group(1, 2, 3)
        hours = int(days) * 24 + int(hours) + int(minutes) / 60
        return float("%.2f" % hours)

    match = re.match(r"(?P<days>\w+)d (?P<hours>\w+)h", duration_str)
    if match is not None:
        days, hours = match.group(1, 2)
        hours = int(days) * 24 + int(hours)
        return float("%.2f" % hours)

    match = re.match(r"(?P<days>\w+)d (?P<minutes>\w+)m", duration_str)
    if match is not None:
        days, minutes = match.group(1, 2)
        hours = int(days) * 24 + int(minutes) / 60
        return float("%.2f" % hours)

    match = re.match(r"(?P<hours>\w+)h(?P<minutes>\w+)m", duration_str)
    if match is not None:
        hours, minutes = match.group(1, 2)
        hours = int(hours) + int(minutes) / 60
        return float("%.2f" % hours)

    match = re.match(r"(?P<days>\w+)d", duration_str)
    if match is not None:
        days = match.group(1)
        hours = int(days) * 24
        return float("%.2f" % hours)

    match = re.match(r"(?P<hours>\w+)h", duration_str)
    if match is not None:
        hours = match.group(1)
        return float("%.2f" % int(hours))

    match = re.match(r"(?P<minutes>\w+)m", duration_str)
    if match is not None:
        minutes = match.group(1)
        hours = int(minutes) / 60
        return float("%.2f" % hours)

    raise ValueError(duration_str)


def get_date_range(start_date, end_date):
    for i in range(0, (end_date - start_date).days + 1):
        yield start_date + timedelta(days=i)


def result_get_price(result):
    return float(result["price"]["grandTotal"])


def result_get_segments(result):
    return sum([len(i["segments"]) for i in result["itineraries"]])


def result_get_total_time(result):
    return sum([duration_total_in_hours(i["duration"]) for i in result["itineraries"]])


def filter_results(items):
    if not items:
        return []

    min_price = result_get_price(items[0])
    min_segments = result_get_segments(items[0])
    min_duration = result_get_total_time(items[0])
    total = len(items)

    for i in items[1:]:
        price = result_get_price(i)
        segments = result_get_segments(i)
        duration = result_get_total_time(items[0])

        if price < min_price:
            min_price = price

        if segments < min_segments:
            min_segments = segments

        if duration < min_duration:
            min_duration = duration

    logger.info(
        f"[AMADEUS-PRESELECTION] {min_price=}, {min_segments=}, {min_duration=}"
    )

    results = [
        i
        for i in items
        if result_get_segments(i)
        <= (min_segments + FILTER_SEGMENTS_ADDITIONAL_ACCEPTABLE)
    ]
    logger.info(
        f"[AMADEUS-PRESELECTION][FILTER] post segment check was: {total} is: {len(results)}"
    )

    total = len(results)
    if total > FILTER_ENTRY_RESULTS_LIMIT:
        results = sorted(results, key=lambda x: result_get_price(x))
        results = results[
            0 : math.floor(  # noqa: E203
                len(results) * FILTER_PRICE_LEFTOVER_PERCENTAGE
            )  # noqa: E203
        ]
        logger.info(
            f"[AMADEUS-PRESELECTION][FILTER] post price check was: {total} is: {len(results)}"
        )

    total = len(results)
    if total > FILTER_ENTRY_RESULTS_LIMIT:
        results = sorted(results, key=lambda x: result_get_total_time(x))
        results = results[
            0 : math.floor(len(results) * FILTER_TIME_LEFTOVER_PERCENTAGE)  # noqa: E203
        ]
        logger.info(
            f"[AMADEUS-PRESELECTION][FILTER] post time check was: {total} is: {len(results)}"
        )

    return results[:FILTER_ENTRY_RESULTS_LIMIT]


def get_search_requests(task_params):
    source_date_from = datetime.strptime(
        task_params.pop("date_from"), SOURCE_DATE_FORMAT
    ).date()
    source_date_to = datetime.strptime(
        task_params.pop("date_to"), SOURCE_DATE_FORMAT
    ).date()
    source_return_from = datetime.strptime(
        task_params.pop("return_from"), SOURCE_DATE_FORMAT
    ).date()
    source_return_to = datetime.strptime(
        task_params.pop("return_to"), SOURCE_DATE_FORMAT
    ).date()
    nights_in_dst_from = task_params.pop("nights_in_dst_from")
    nights_in_dst_to = task_params.pop("nights_in_dst_to")
    fly_from_airports = task_params.pop("fly_from_airports")
    fly_to_airports = task_params.pop("fly_to_airports")
    return_from_airports = task_params.pop("return_from_airports")
    return_to_airports = task_params.pop("return_to_airports")
    multicity = task_params.pop("multicity")
    allow_opposite_route = task_params.pop("allow_opposite_route")

    date_tuples = []

    for departure_date in get_date_range(source_date_from, source_date_to):
        for nights in range(nights_in_dst_from, nights_in_dst_to + 1):
            return_date = departure_date + timedelta(days=nights)
            if return_date < source_return_from or return_date > source_return_to:
                continue

            date_tuples.append(
                (
                    departure_date.strftime(SOURCE_DATE_FORMAT),
                    return_date.strftime(SOURCE_DATE_FORMAT),
                )
            )

    airports = set(
        itertools.product(
            fly_from_airports,
            fly_to_airports,
            return_from_airports,
            return_to_airports,
        )
    )

    # make sure its proper two-way trip to same airports
    if not multicity:
        airports = [i for i in airports if (i[0] == i[3] and i[1] == i[2])]

    records = list(itertools.product(date_tuples, airports))

    base_params = {
        "passengers_map": task_params.pop("passengers_map"),
        "currency_code": task_params.pop("currency_code"),
    }

    logger.info(
        (
            f"[AMADEUS-PRESELECTION] date_combinations={len(date_tuples)}, "
            f"airport_combinations={len(airports)} "
            f"total_combinations={len(records)} multicity={multicity} allow_opposite_route={allow_opposite_route}"
        )
    )

    return [
        {
            **base_params,
            "flights": [
                {
                    "departure": {"iata": fly_from},
                    "arrival": {"iata": fly_to},
                    "departure_date": departure_date,
                },
                {
                    "departure": {"iata": return_from},
                    "arrival": {"iata": return_to},
                    "departure_date": return_date,
                },
            ],
        }
        for (
            (departure_date, return_date),
            (fly_from, fly_to, return_from, return_to),
        ) in records
    ]


async def handler(task_id, task_params):
    logger.info(f"[AMADEUS-PRESELECTION] {task_id=} {task_params=}")
    search_requests = get_search_requests(task_params=task_params)

    async with httpx.AsyncClient() as client:
        service = Amadeus(client=client)
        logger.info(
            f"[AMADEUS-PRESELECTION] obtaining auth token, prepared: {len(search_requests)} requests to Amadeus"
        )

        await service.async_install_access_token()
        await asyncio.sleep(SLEEP_AFTER_OBTAINING_TOKEN_SECONDS)

        logger.info(
            f"[AMADEUS-PRESELECTION] got auth token, sending: {len(search_requests)} requests to Amadeus"
        )

        jobs = [
            functools.partial(service.async_search, **search_params)
            for search_params in search_requests
        ]
        responses = await aiometer.run_all(
            jobs,
            max_at_once=settings.AMADEUS_MAX_REQUESTS_AT_ONCE,
            max_per_second=settings.AMADEUS_MAX_REQUESTS_PER_SECOND,
        )

    ok_responses = 0
    error_responses = 0
    error_statuses = set()
    results = []

    for r in responses:
        if r["status"] != HTTP_200_OK:
            error_responses += 1
            error_statuses.add(r["status"])
            continue

        ok_responses += 1
        results.extend(r["data"])

    found = len(results)
    results = filter_results(results)

    stats = {
        "total_tasks": len(search_requests),
        "200_responses": ok_responses,
        "XXX_responses": error_responses,
        "XXX_codes": list(error_statuses),
        "found": found,
        "filtered": len(results),
    }
    logger.info(f"[AMADEUS-PRESELECTION] post concurrent run {stats=}")
    return results
