#!/usr/bin/env python3
"""Execute the frozen Gate 4 scoping searches and write auditable logs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
LITERATURE = ROOT / "literature"
SEARCH_CUTOFF = "2026-07-10"
QUERY_DATE = "2026-07-12"
USER_AGENT = (
    "QMLforArtemisIV/0.3 systematic-scoping-review "
    "(mailto:taechasith@users.noreply.github.com)"
)
CACHE = ROOT / "tmp/gate4_literature_search"
OPENALEX_RETRIEVAL_LIMIT = 100
OPENALEX_OBSERVED_COUNTS = {
    "S1": 218,
    "S2": 824,
    "S3": 2549,
    "S4": 147,
    "S5": 1263,
    "S6": 2756,
    "S7": 1975,
}


QUERIES = {
    "S1": (
        '(spacecraft OR cislunar OR lunar OR Orion) AND ("trajectory correction" '
        'OR guidance OR "burn placement") AND (propellant OR "delta-v" OR fuel) '
        "AND (robust OR uncertainty OR dispersion)"
    ),
    "S2": (
        '("machine learning" OR "reinforcement learning" OR surrogate) AND '
        '(spacecraft OR cislunar OR "low thrust") AND (trajectory OR guidance OR control)'
    ),
    "S3": (
        '("quantum machine learning" OR "quantum kernel" OR "variational quantum" '
        'OR "quantum neural network") AND (regression OR reinforcement OR surrogate OR control)'
    ),
    "S4": (
        '("quantum annealing" OR QAOA OR QUBO) AND '
        '(spacecraft OR trajectory OR "space mission")'
    ),
    "S5": (
        '(Artemis OR Orion) AND ("trajectory correction" OR navigation OR propulsion '
        'OR "crew schedule" OR ephemeris)'
    ),
    "S6": (
        '("human spaceflight" OR astronaut OR crewed) AND '
        "(acceleration OR sleep OR workload OR radiation) AND "
        "(standard OR constraint OR spacecraft)"
    ),
    "S7": (
        '("model credibility" OR "simulation validation" OR '
        '"verification and validation") AND (NASA OR spacecraft OR trajectory)'
    ),
}

NTRS_QUERIES = {
    "S1": "trajectory correction uncertainty",
    "S5": "Artemis trajectory",
    "S6": "human spaceflight acceleration",
    "S7": "simulation validation spacecraft",
}

ARXIV_QUERIES = {
    "S2": (
        '(all:"machine learning" OR all:"reinforcement learning" OR all:surrogate) '
        'AND (all:spacecraft OR all:cislunar OR all:"low thrust") '
        "AND (all:trajectory OR all:guidance OR all:control)"
    ),
    "S3": (
        '(all:"quantum machine learning" OR all:"quantum kernel" OR '
        'all:"variational quantum" OR all:"quantum neural network") '
        "AND (all:regression OR all:reinforcement OR all:surrogate OR all:control)"
    ),
    "S4": (
        '(all:"quantum annealing" OR all:QAOA OR all:QUBO) '
        'AND (all:spacecraft OR all:trajectory OR all:"space mission")'
    ),
}

SEED_SEARCH_MAP = {
    "E001": {"S1", "S5"},
    "E002": {"S4"},
    "E003": {"S3"},
    "E004": {"S3"},
    "E005": {"S3"},
    "E006": {"S3"},
    "E007": {"S3"},
    "E008": {"S2"},
    "E009": {"S2"},
    "E010": {"S2"},
    "E011": {"S2"},
    "E012": {"S7"},
    "E013": {"S6"},
}


@dataclass
class Record:
    title: str
    year: int | None
    doi: str
    url: str
    abstract: str = ""
    language: str = ""
    record_ids: set[str] = field(default_factory=set)
    databases: set[str] = field(default_factory=set)
    search_ids: set[str] = field(default_factory=set)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows available for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def request_bytes(url: str, retries: int = 10) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt + 1 == retries:
                raise
            retry_after = error.headers.get("Retry-After")
            delay = (
                float(retry_after)
                if retry_after and retry_after.isdigit()
                else min(60.0, 2.0 ** (attempt + 1))
            )
            time.sleep(delay)
    raise RuntimeError(f"Unreachable retry state for {url}")


def request_json(url: str) -> dict[str, Any]:
    value = json.loads(request_bytes(url))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return value


def reconstruct_abstract(index: Mapping[str, Iterable[int]] | None) -> str:
    if not index:
        return ""
    positions = [
        (int(position), word)
        for word, word_positions in index.items()
        for position in word_positions
    ]
    return " ".join(word for _, word in sorted(positions))


def normalize_doi(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized.rstrip("./")


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def canonical_key(record: Record) -> str:
    return (
        f"doi:{record.doi}" if record.doi else f"title:{normalize_title(record.title)}"
    )


def merge_record(target: dict[str, Record], record: Record) -> None:
    key = canonical_key(record)
    if not key or key == "title:":
        return
    if key not in target:
        target[key] = record
        return
    existing = target[key]
    existing.record_ids.update(record.record_ids)
    existing.databases.update(record.databases)
    existing.search_ids.update(record.search_ids)
    if not existing.abstract and record.abstract:
        existing.abstract = record.abstract
    if not existing.doi and record.doi:
        existing.doi = record.doi
    if not existing.url and record.url:
        existing.url = record.url
    if existing.year is None and record.year is not None:
        existing.year = record.year


def record_to_json(record: Record) -> dict[str, Any]:
    return {
        "title": record.title,
        "year": record.year,
        "doi": record.doi,
        "url": record.url,
        "abstract": record.abstract,
        "language": record.language,
        "record_ids": sorted(record.record_ids),
        "databases": sorted(record.databases),
        "search_ids": sorted(record.search_ids),
    }


def record_from_json(value: Mapping[str, Any]) -> Record:
    return Record(
        title=str(value["title"]),
        year=value["year"],
        doi=str(value["doi"]),
        url=str(value["url"]),
        abstract=str(value["abstract"]),
        language=str(value["language"]),
        record_ids=set(value["record_ids"]),
        databases=set(value["databases"]),
        search_ids=set(value["search_ids"]),
    )


def cache_path(database: str, search_id: str) -> Path:
    safe_database = normalize_title(database).replace(" ", "_")
    return CACHE / f"{safe_database}_{search_id}.json"


def load_cache(
    database: str, search_id: str
) -> tuple[dict[str, Any], list[Record]] | None:
    path = cache_path(database, search_id)
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value["log"], [record_from_json(item) for item in value["records"]]


def save_cache(
    database: str,
    search_id: str,
    log: Mapping[str, Any],
    records: Iterable[Record],
) -> None:
    path = cache_path(database, search_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"log": dict(log), "records": [record_to_json(item) for item in records]}
    path.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
        encoding="utf-8",
        newline="\n",
    )


def _openalex_filter(search_id: str, query: str) -> str:
    values = [
        f"title_and_abstract.search:{query}",
        f"to_publication_date:{SEARCH_CUTOFF}",
        "is_retracted:false",
    ]
    if search_id in {"S2", "S3", "S4"}:
        values.insert(1, "from_publication_date:2018-01-01")
    return ",".join(values)


def search_openalex(search_id: str, query: str) -> tuple[dict[str, Any], list[Record]]:
    cached = load_cache("OpenAlex", search_id)
    if cached is not None:
        return cached
    base = "https://api.openalex.org/works"
    filter_value = _openalex_filter(search_id, query)
    cursor = "*"
    records: list[Record] = []
    result_count: int | None = None
    first_url = ""
    while cursor and len(records) < OPENALEX_RETRIEVAL_LIMIT:
        parameters = urllib.parse.urlencode(
            {
                "filter": filter_value,
                "per_page": 100,
                "cursor": cursor,
                "mailto": "taechasith@users.noreply.github.com",
                "select": (
                    "id,doi,display_name,publication_year,publication_date,type,"
                    "language,authorships,abstract_inverted_index,primary_location,is_retracted"
                ),
            }
        )
        url = f"{base}?{parameters}"
        first_url = first_url or url
        payload = request_json(url)
        if result_count is None:
            result_count = int(payload["meta"]["count"])
        for item in payload["results"]:
            location = item.get("primary_location") or {}
            landing = location.get("landing_page_url") or item.get("id") or ""
            records.append(
                Record(
                    title=item.get("display_name") or "",
                    year=item.get("publication_year"),
                    doi=normalize_doi(item.get("doi")),
                    url=landing,
                    abstract=reconstruct_abstract(item.get("abstract_inverted_index")),
                    language=item.get("language") or "",
                    record_ids={item.get("id") or ""},
                    databases={"OpenAlex"},
                    search_ids={search_id},
                )
            )
        cursor = payload["meta"].get("next_cursor")
        if not payload["results"]:
            break
        time.sleep(1.05)
    log = {
        "search_id": search_id,
        "database": "OpenAlex",
        "query_date": QUERY_DATE,
        "search_cutoff": SEARCH_CUTOFF,
        "exact_query": query,
        "field_scope": "title_and_abstract.search",
        "filters": (
            "2018-01-01 through cutoff; retracted=false"
            if search_id in {"S2", "S3", "S4"}
            else "through cutoff; retracted=false"
        ),
        "result_count": result_count or 0,
        "records_retrieved": len(records),
        "coverage_status": (
            "complete metadata retrieval"
            if len(records) >= (result_count or 0)
            else f"partial: first {OPENALEX_RETRIEVAL_LIMIT} relevance-ranked records"
        ),
        "api_url": first_url,
        "notes": (
            "Unauthenticated API export was rate-limited; exact total retained and "
            "bounded discovery records are not treated as primary evidence."
        ),
    }
    save_cache("OpenAlex", search_id, log, records)
    return log, records


def openalex_count_only_log(search_id: str, query: str) -> dict[str, Any]:
    filter_value = _openalex_filter(search_id, query)
    parameters = urllib.parse.urlencode(
        {
            "filter": filter_value,
            "per_page": 1,
            "select": "id,display_name",
            "mailto": "taechasith@users.noreply.github.com",
        }
    )
    return {
        "search_id": search_id,
        "database": "OpenAlex",
        "query_date": QUERY_DATE,
        "search_cutoff": SEARCH_CUTOFF,
        "exact_query": query,
        "field_scope": "title_and_abstract.search",
        "filters": (
            "2018-01-01 through cutoff; retracted=false"
            if search_id in {"S2", "S3", "S4"}
            else "through cutoff; retracted=false"
        ),
        "result_count": OPENALEX_OBSERVED_COUNTS[search_id],
        "records_retrieved": 0,
        "coverage_status": "count only; metadata export blocked by persistent HTTP 429",
        "api_url": f"https://api.openalex.org/works?{parameters}",
        "notes": (
            "Count observed on 2026-07-12 before export throttling. No OpenAlex "
            "record is treated as screened or as primary evidence."
        ),
    }


def search_ntrs(search_id: str, query: str) -> tuple[dict[str, Any], list[Record]]:
    cached = load_cache("NASA NTRS", search_id)
    if cached is not None:
        return cached
    base = "https://ntrs.nasa.gov/api/citations/search"
    records: list[Record] = []
    offset = 0
    result_count: int | None = None
    first_url = ""
    while result_count is None or offset < result_count:
        parameters = urllib.parse.urlencode(
            {"q": query, "page[size]": 100, "page[from]": offset}
        )
        url = f"{base}?{parameters}"
        first_url = first_url or url
        payload = request_json(url)
        result_count = int(payload["stats"]["total"])
        results = payload["results"]
        for item in results:
            year_match = re.search(
                r"(?:19|20)\d{2}", item.get("distributionDate") or ""
            )
            year = int(year_match.group()) if year_match else None
            if year is not None and date(year, 1, 1) > date.fromisoformat(
                SEARCH_CUTOFF
            ):
                continue
            records.append(
                Record(
                    title=item.get("title") or "",
                    year=year,
                    doi="",
                    url=f"https://ntrs.nasa.gov/citations/{item['id']}",
                    abstract=item.get("abstract") or "",
                    language="en",
                    record_ids={f"NTRS:{item['id']}"},
                    databases={"NASA NTRS"},
                    search_ids={search_id},
                )
            )
        if not results:
            break
        offset += len(results)
        time.sleep(0.1)
    log = {
        "search_id": search_id,
        "database": "NASA NTRS",
        "query_date": QUERY_DATE,
        "search_cutoff": SEARCH_CUTOFF,
        "exact_query": query,
        "field_scope": "NTRS q full-record search",
        "filters": "records through cutoff retained locally",
        "result_count": result_count or 0,
        "records_retrieved": len(records),
        "coverage_status": "complete API retrieval",
        "api_url": first_url,
        "notes": "Boolean concepts flattened for the NTRS q interface.",
    }
    save_cache("NASA NTRS", search_id, log, records)
    return log, records


def _arxiv_text(entry: ET.Element, tag: str) -> str:
    namespace = "{http://www.w3.org/2005/Atom}"
    return " ".join((entry.findtext(namespace + tag) or "").split())


def search_arxiv(search_id: str, query: str) -> tuple[dict[str, Any], list[Record]]:
    cached = load_cache("arXiv", search_id)
    if cached is not None:
        return cached
    base = "https://export.arxiv.org/api/query"
    atom = "{http://www.w3.org/2005/Atom}"
    opensearch = "{http://a9.com/-/spec/opensearch/1.1/}"
    records: list[Record] = []
    offset = 0
    result_count: int | None = None
    first_url = ""
    while result_count is None or offset < result_count:
        parameters = urllib.parse.urlencode(
            {
                "search_query": query,
                "start": offset,
                "max_results": 100,
                "sortBy": "relevance",
            }
        )
        url = f"{base}?{parameters}"
        first_url = first_url or url
        root = ET.fromstring(request_bytes(url))
        result_count = int(root.findtext(opensearch + "totalResults") or 0)
        entries = root.findall(atom + "entry")
        for entry in entries:
            published = _arxiv_text(entry, "published")
            if not published:
                continue
            published_date = date.fromisoformat(published[:10])
            if search_id in {"S2", "S3", "S4"} and published_date < date(2018, 1, 1):
                continue
            if published_date > date.fromisoformat(SEARCH_CUTOFF):
                continue
            entry_url = _arxiv_text(entry, "id")
            arxiv_id = entry_url.rsplit("/", 1)[-1]
            doi = ""
            for child in entry:
                if child.tag.endswith("doi") and child.text:
                    doi = normalize_doi(child.text)
            records.append(
                Record(
                    title=_arxiv_text(entry, "title"),
                    year=published_date.year,
                    doi=doi,
                    url=entry_url,
                    abstract=_arxiv_text(entry, "summary"),
                    language="en",
                    record_ids={f"arXiv:{arxiv_id}"},
                    databases={"arXiv"},
                    search_ids={search_id},
                )
            )
        if not entries:
            break
        offset += len(entries)
        time.sleep(3.0)
    log = {
        "search_id": search_id,
        "database": "arXiv",
        "query_date": QUERY_DATE,
        "search_cutoff": SEARCH_CUTOFF,
        "exact_query": query,
        "field_scope": "all fields",
        "filters": "2018-01-01 through cutoff applied locally",
        "result_count": result_count or 0,
        "records_retrieved": len(records),
        "coverage_status": "complete API retrieval with local date filter",
        "api_url": first_url,
        "notes": "Preprint discovery; companion DOI records are deduplicated when present.",
    }
    save_cache("arXiv", search_id, log, records)
    return log, records


def _contains(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def directly_relevant_title(search_id: str, title: str) -> bool:
    value = normalize_title(title)
    groups = {
        "S1": (
            ("spacecraft", "cislunar", "lunar", "orion", "artemis"),
            ("trajectory", "guidance", "burn"),
            ("robust", "uncertainty", "dispersion", "correction", "delta v", "fuel"),
        ),
        "S2": (
            ("machine learning", "reinforcement learning", "neural", "surrogate"),
            ("spacecraft", "cislunar", "low thrust", "trajectory", "guidance"),
        ),
        "S3": (
            (
                "quantum machine",
                "quantum kernel",
                "variational quantum",
                "quantum neural",
            ),
            ("regression", "reinforcement", "surrogate", "control", "learning"),
        ),
        "S4": (
            ("quantum anneal", "qaoa", "qubo"),
            ("spacecraft", "trajectory", "space mission", "orbital", "aerospace"),
        ),
        "S5": (
            ("artemis", "orion"),
            ("trajectory", "navigation", "propulsion", "crew", "ephemeris"),
        ),
        "S6": (
            ("human spaceflight", "astronaut", "crew", "human system"),
            (
                "acceleration",
                "sleep",
                "workload",
                "radiation",
                "constraint",
                "standard",
            ),
        ),
        "S7": (
            ("credibility", "verification", "validation", "validated"),
            ("model", "simulation", "spacecraft", "trajectory", "nasa"),
        ),
    }[search_id]
    return all(_contains(value, group) for group in groups)


def seed_keys() -> set[str]:
    path = LITERATURE / "evidence_matrix.csv"
    keys: set[str] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            doi = normalize_doi(row.get("doi"))
            if doi:
                keys.add(f"doi:{doi}")
            keys.add(f"title:{normalize_title(row['title'])}")
    return keys


def load_seed_records() -> list[Record]:
    path = LITERATURE / "evidence_matrix.csv"
    records = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            evidence_id = row["evidence_id"]
            records.append(
                Record(
                    title=row["title"],
                    year=int(row["year"]),
                    doi=normalize_doi(row.get("doi")),
                    url=row["url"],
                    language="en",
                    record_ids={f"seed:{evidence_id}"},
                    databases={"frozen seed evidence matrix"},
                    search_ids=set(SEED_SEARCH_MAP[evidence_id]),
                )
            )
    return records


def screen_records(records: Mapping[str, Record]) -> list[dict[str, Any]]:
    seeds = seed_keys()
    rows = []
    for index, (key, record) in enumerate(
        sorted(records.items(), key=lambda item: normalize_title(item[1].title)),
        start=1,
    ):
        matching_seed = (
            key in seeds or f"title:{normalize_title(record.title)}" in seeds
        )
        relevant_searches = sorted(
            search_id
            for search_id in record.search_ids
            if directly_relevant_title(search_id, record.title)
        )
        if record.language not in {"", "en"}:
            decision = "exclude"
            reason = "non_english_metadata_record"
            full_text = "not_requested"
        elif matching_seed:
            decision = "include"
            reason = "seed_record_matches_frozen_review_scope"
            full_text = "primary_or_authoritative_record_required"
        elif relevant_searches:
            decision = "include_for_full_text"
            reason = "title_contains_direct_task_and_method_conjunction"
            full_text = "pending_full_text_screen"
        else:
            decision = "exclude"
            reason = "title_lacks_direct_task_method_conjunction_after_concept_search"
            full_text = "not_requested"
        rows.append(
            {
                "screening_id": f"SCR{index:05d}",
                "canonical_key": key,
                "title": record.title,
                "year": record.year or "",
                "doi": record.doi,
                "source_record_ids": ";".join(
                    sorted(value for value in record.record_ids if value)
                ),
                "databases": ";".join(sorted(record.databases)),
                "search_ids": ";".join(sorted(record.search_ids)),
                "stage": "title_abstract_discovery",
                "decision": decision,
                "exclusion_reason": reason,
                "full_text_status": full_text,
                "url": record.url,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--openalex-only",
        action="store_true",
        help="skip NTRS and arXiv supplemental searches",
    )
    parser.add_argument(
        "--openalex-counts-only",
        action="store_true",
        help="use the observed OpenAlex counts and skip the throttled metadata export",
    )
    args = parser.parse_args()

    logs: list[dict[str, Any]] = []
    records: dict[str, Record] = {}
    for search_id, query in QUERIES.items():
        if args.openalex_counts_only:
            log, discovered = openalex_count_only_log(search_id, query), []
        else:
            log, discovered = search_openalex(search_id, query)
        logs.append(log)
        for record in discovered:
            merge_record(records, record)
        print(
            f"OpenAlex {search_id}: {len(discovered)}/{log['result_count']} records",
            flush=True,
        )

    if not args.openalex_only:
        for search_id, query in NTRS_QUERIES.items():
            log, discovered = search_ntrs(search_id, query)
            logs.append(log)
            for record in discovered:
                merge_record(records, record)
            print(
                f"NASA NTRS {search_id}: {len(discovered)}/{log['result_count']} records",
                flush=True,
            )
        for search_id, query in ARXIV_QUERIES.items():
            log, discovered = search_arxiv(search_id, query)
            logs.append(log)
            for record in discovered:
                merge_record(records, record)
            print(
                f"arXiv {search_id}: {len(discovered)}/{log['result_count']} records",
                flush=True,
            )

    for record in load_seed_records():
        merge_record(records, record)

    screening = screen_records(records)
    write_csv(LITERATURE / "search_log.csv", logs)
    write_csv(LITERATURE / "screening_log.csv", screening)
    decisions: dict[str, int] = {}
    for row in screening:
        decisions[row["decision"]] = decisions.get(row["decision"], 0) + 1
    print(f"Search runs: {len(logs)}")
    print(f"Deduplicated records: {len(screening)}")
    print(f"Screening decisions: {decisions}")


if __name__ == "__main__":
    main()
