"""Download NBA box score payloads into a single JSONL file."""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, IO, Iterable

import pandas as pd
from nba_api.stats.endpoints import boxscoretraditionalv2, boxscoretraditionalv3
from requests.exceptions import ReadTimeout, RequestException

from src.etl.download_season import (
    DEFAULT_SEASON_TYPES,
    fetch_games,
    season_slices,
)


BOX_SCORE_FIELDS = (
    "gameId", "teamId", "teamCity", "teamName", "teamTricode", "teamSlug",
    "personId", "firstName", "familyName", "nameI", "playerSlug", "position",
    "comment", "jerseyNum", "minutes",
    "fieldGoalsMade", "fieldGoalsAttempted", "fieldGoalsPercentage",
    "threePointersMade", "threePointersAttempted", "threePointersPercentage",
    "freeThrowsMade", "freeThrowsAttempted", "freeThrowsPercentage",
    "reboundsOffensive", "reboundsDefensive", "reboundsTotal",
    "assists", "steals", "blocks", "turnovers", "foulsPersonal",
    "points", "plusMinusPoints",
)

_STRING_FIELDS = {
    "gameId", "teamCity", "teamName", "teamTricode", "teamSlug",
    "firstName", "familyName", "nameI", "playerSlug", "position",
    "comment", "jerseyNum", "minutes",
}


# -- Payload formatting -------------------------------------------------------

def _rows_to_column_payload(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not rows:
        return {f: {} for f in BOX_SCORE_FIELDS}
    frame = pd.DataFrame(rows)
    for f in BOX_SCORE_FIELDS:
        if f not in frame.columns:
            frame[f] = "" if f in _STRING_FIELDS else 0
    return frame.loc[:, list(BOX_SCORE_FIELDS)].to_dict(orient="dict")


# -- Retry helper -------------------------------------------------------------

def _backoff_wait(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    return min(base * (2 ** (attempt - 1)) + random.uniform(0.2, 1.0), cap)


# -- Manifest -----------------------------------------------------------------

def _manifest_path(output_file: Path) -> Path:
    return output_file.with_suffix(output_file.suffix + ".manifest.json")


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"seasons": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"seasons": {}}
    return {"seasons": data["seasons"]} if isinstance(data.get("seasons"), dict) else {"seasons": {}}


def _save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _season_key(label: str, stype: str) -> str:
    return f"{label}|{stype}"


def _is_season_complete(entry: dict[str, Any] | None) -> bool:
    if not isinstance(entry, dict):
        return False
    expected = entry.get("expected_game_ids")
    completed = entry.get("completed_game_ids")
    if not isinstance(expected, list) or not isinstance(completed, list):
        return False
    exp = {str(g) for g in expected if str(g)}
    return bool(exp) and exp <= {str(g) for g in completed if str(g)}


def _load_existing_game_ids(output_file: Path) -> set[str]:
    ids: set[str] = set()
    if not output_file.exists():
        return ids
    with output_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            gf = payload.get("gameId") if isinstance(payload, dict) else None
            if isinstance(gf, dict) and gf:
                val = next(iter(gf.values()), None)
                if val is not None:
                    ids.add(str(val))
    return ids


def _load_failed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _save_failed_ids(path: Path, ids: set[str]) -> None:
    path.write_text("\n".join(sorted(ids)) + "\n" if ids else "", encoding="utf-8")


def _load_local_expected_game_ids(output_dir: Path, label: str, stype: str) -> list[str]:
    suffix = stype.replace(" ", "_")
    base = output_dir / f"games_{label}_{suffix}.json"
    candidates = [base, base.with_suffix(".jsonl"), output_dir / f"{base.stem}_columnar.json"]

    for path in candidates:
        if not path.exists():
            continue

        if path.suffix == ".jsonl":
            ids: set[str] = set()
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    gf = row.get("GAME_ID") if isinstance(row, dict) else None
                    if isinstance(gf, dict):
                        ids.update(str(v) for v in gf.values() if v is not None)
            return sorted(ids)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        if isinstance(data, list):
            return sorted({str(r["GAME_ID"]) for r in data if isinstance(r, dict) and r.get("GAME_ID") is not None})
        if isinstance(data, dict):
            gf = data.get("GAME_ID")
            if isinstance(gf, dict):
                return sorted(str(v) for v in gf.values() if v is not None)

    return []


# -- Single game fetch --------------------------------------------------------

@dataclass
class FetchConfig:
    timeout: int = 30
    max_timeout: int = 45
    timeout_step: int = 5
    max_retries: int = 4
    invalid_retries: int = 3
    max_backoff: float = 30.0
    read_timeout_streak_limit: int = 3
    max_elapsed: float = 180.0


def fetch_game_box_score(game_id: str, cfg: FetchConfig | None = None) -> dict[str, dict[str, Any]] | None:
    c = cfg or FetchConfig()
    started_at = time.monotonic()
    rt_streak = 0

    for attempt in range(1, c.max_retries + 1):
        if time.monotonic() - started_at >= c.max_elapsed:
            print(f"  Aborting {game_id}: exceeded {c.max_elapsed:.0f}s budget.")
            return None

        eff_timeout = min(c.timeout + (attempt - 1) * c.timeout_step, c.max_timeout)

        try:
            resp = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id, timeout=eff_timeout)
            frames = resp.get_data_frames()
            if not frames or frames[0].empty:
                return None
            return _rows_to_column_payload(frames[0].to_dict(orient="records"))

        except RequestException as exc:
            rt_streak = rt_streak + 1 if isinstance(exc, ReadTimeout) or "Read timed out" in str(exc) else 0
            if rt_streak >= c.read_timeout_streak_limit:
                print(f"  {game_id}: {rt_streak} consecutive timeouts. Giving up.")
                return None
            if attempt == c.max_retries:
                print(f"  {game_id}: failed after {c.max_retries} attempts: {exc}")
                return None
            wait = _backoff_wait(attempt, cap=c.max_backoff)
            print(f"  {game_id}: attempt {attempt}/{c.max_retries} failed: {exc}. Retry in {wait:.1f}s...")
            time.sleep(wait)

        except (json.JSONDecodeError, ValueError) as exc:
            rt_streak = 0
            # V2 fallback for legacy games
            try:
                fb = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=eff_timeout)
                fb_frames = fb.get_data_frames()
                if fb_frames and not fb_frames[0].empty:
                    return _rows_to_column_payload(fb_frames[0].to_dict(orient="records"))
            except Exception:
                pass
            if attempt >= min(c.max_retries, max(1, c.invalid_retries)):
                print(f"  {game_id}: invalid response after {attempt} attempts: {exc}")
                return None
            wait = _backoff_wait(attempt, cap=c.max_backoff)
            print(f"  {game_id}: invalid response, attempt {attempt}. Retry in {wait:.1f}s...")
            time.sleep(wait)

        except Exception as exc:
            rt_streak = 0
            if attempt == c.max_retries:
                print(f"  {game_id}: unexpected error after {c.max_retries} attempts: {exc}")
                return None
            wait = _backoff_wait(attempt, cap=c.max_backoff)
            print(f"  {game_id}: unexpected error, attempt {attempt}. Retry in {wait:.1f}s...")
            time.sleep(wait)

    return None


# -- Download state -----------------------------------------------------------

@dataclass
class _DownloadState:
    manifest: dict[str, Any]
    manifest_path: Path
    failed_path: Path
    existing: set[str] = field(default_factory=set)
    failed: set[str] = field(default_factory=set)
    total_written: int = 0
    total_skipped: int = 0
    consecutive_failures: int = 0

    def record_failure(self, game_id: str, sk: str, expected: list[str],
                       threshold: int, cooldown: float) -> None:
        self.failed.add(game_id)
        _save_failed_ids(self.failed_path, self.failed)
        self._sync_manifest(sk, expected)
        self.consecutive_failures += 1
        if self.consecutive_failures >= threshold:
            print(f"    {self.consecutive_failures} consecutive failures; cooling down {cooldown:.0f}s...")
            time.sleep(cooldown)
            self.consecutive_failures = 0

    def record_success(self, game_id: str, sk: str, expected: list[str], out: IO[str],
                       payload: dict, pause: float) -> None:
        out.write(json.dumps(payload, ensure_ascii=False) + "\n")
        out.flush()
        self.existing.add(game_id)
        if game_id in self.failed:
            self.failed.discard(game_id)
            _save_failed_ids(self.failed_path, self.failed)
        completed = set(self.manifest["seasons"].get(sk, {}).get("completed_game_ids", []))
        completed.add(game_id)
        entry = self.manifest["seasons"][sk]
        entry["completed_game_ids"] = sorted(g for g in completed if g in expected)
        entry["completed_game_count"] = len(entry["completed_game_ids"])
        entry["failed_game_ids"] = sorted(g for g in self.failed if g in expected)
        _save_manifest(self.manifest_path, self.manifest)
        self.total_written += 1
        self.consecutive_failures = 0
        time.sleep(pause)

    def _sync_manifest(self, sk: str, expected: list[str]) -> None:
        entry = self.manifest["seasons"].get(sk, {})
        completed = set(entry.get("completed_game_ids", []))
        entry["completed_game_count"] = len(set(expected) & completed)
        entry["failed_game_ids"] = sorted(g for g in self.failed if g in expected)
        _save_manifest(self.manifest_path, self.manifest)


# -- Bulk download ------------------------------------------------------------

def download_box_scores_jsonl(
    start_year: int = 2000,
    end_year: int = 2025,
    output_file: str = "data/box_scores.jsonl",
    season_types: Iterable[str] = DEFAULT_SEASON_TYPES,
    pause_between_slices: float = 1.5,
    pause_between_games: float = 0.75,
    resume: bool = False,
    fetch_cfg: FetchConfig | None = None,
    consecutive_failure_threshold: int = 5,
    failure_cooldown: float = 20.0,
    failed_games_output: str = "data/failed_box_score_games.txt",
) -> None:
    """Download box scores across a season range into one JSONL file."""
    cfg = fetch_cfg or FetchConfig()
    target = Path(output_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    mp = _manifest_path(target)
    failed_path = Path(failed_games_output)
    failed_path.parent.mkdir(parents=True, exist_ok=True)

    state = _DownloadState(
        manifest=_load_manifest(mp),
        manifest_path=mp,
        failed_path=failed_path,
        failed=_load_failed_ids(failed_path) if resume else set(),
    )

    if not resume:
        _save_failed_ids(failed_path, set())

    if resume and target.exists():
        state.existing = _load_existing_game_ids(target)
        print(f"Resume: {len(state.existing)} existing games in {target}.")

    file_mode = "a" if resume and target.exists() else "w"
    with target.open(file_mode, encoding="utf-8") as out:
        for sl in season_slices(start_year, end_year, season_types=season_types):
            print(f"Processing {sl.season_label} | {sl.season_type}...")
            games = fetch_games(sl.season_label, sl.season_type)

            if games is None or games.empty:
                reason = "request failures" if games is None else "no games"
                print(f"  Skipping ({reason}).")
                time.sleep(pause_between_slices)
                continue

            game_ids = sorted({str(v) for v in games["GAME_ID"].dropna().tolist()})
            print(f"  {len(game_ids)} unique games")
            sk = _season_key(sl.season_label, sl.season_type)
            entry = state.manifest["seasons"].get(sk)

            # Skip completed seasons
            if _is_season_complete(entry):
                recorded = {str(g) for g in entry.get("expected_game_ids", [])}
                if recorded == set(game_ids):
                    print("  Already complete. Skipping.")
                    state.total_skipped += len(game_ids)
                    continue

            # Init manifest entry for this season
            completed_so_far = set(state.existing)
            if isinstance(entry, dict):
                completed_so_far.update(str(g) for g in entry.get("completed_game_ids", []) if str(g))

            state.manifest["seasons"][sk] = {
                "season_label": sl.season_label,
                "season_type": sl.season_type,
                "expected_game_count": len(game_ids),
                "expected_game_ids": game_ids,
                "completed_game_count": len(set(game_ids) & completed_so_far),
                "completed_game_ids": sorted(set(game_ids) & completed_so_far),
                "failed_game_ids": sorted(g for g in state.failed if g in game_ids),
            }
            _save_manifest(mp, state.manifest)

            written_slice = 0
            fetch_cfg_for_slice = FetchConfig(
                timeout=cfg.timeout, max_timeout=cfg.max_timeout,
                timeout_step=cfg.timeout_step,
                max_retries=1 if sl.season_type == "Pre Season" else cfg.max_retries,
                invalid_retries=cfg.invalid_retries,
                max_backoff=cfg.max_backoff,
                read_timeout_streak_limit=cfg.read_timeout_streak_limit,
                max_elapsed=cfg.max_elapsed,
            )

            for idx, gid in enumerate(game_ids, 1):
                print(f"    [{idx}/{len(game_ids)}] {gid}")
                if gid in state.existing:
                    state.total_skipped += 1
                    continue

                try:
                    payload = fetch_game_box_score(gid, fetch_cfg_for_slice)
                except Exception as exc:
                    print(f"    Unexpected error for {gid}: {exc}. Skipping.")
                    payload = None

                if payload is None:
                    state.record_failure(gid, sk, game_ids, consecutive_failure_threshold, failure_cooldown)
                    continue

                state.record_success(gid, sk, game_ids, out, payload, pause_between_games)
                written_slice += 1

            print(f"  Wrote {written_slice} box scores.")
            _save_failed_ids(failed_path, state.failed)
            _save_manifest(mp, state.manifest)
            time.sleep(pause_between_slices)

    _save_failed_ids(failed_path, state.failed)
    print(
        f"Done. Wrote {state.total_written} new, skipped {state.total_skipped}, "
        f"failed {len(state.failed)} (saved to {failed_path})."
    )


# -- Manifest rebuild / status ------------------------------------------------

def rebuild_manifest(
    *, output_file: str, output_dir: str = "data/season",
    start_year: int = 2000, end_year: int = 2025,
    season_types: Iterable[str] = DEFAULT_SEASON_TYPES,
    failed_games_output: str = "data/failed_box_score_games.txt",
) -> int:
    target = Path(output_file)
    mp = _manifest_path(target)
    existing = _load_existing_game_ids(target)
    failed = _load_failed_ids(Path(failed_games_output))
    local_dir = Path(output_dir)

    manifest: dict[str, Any] = {"seasons": {}}
    found = False

    for sl in season_slices(start_year, end_year, season_types=season_types):
        expected = _load_local_expected_game_ids(local_dir, sl.season_label, sl.season_type)
        if not expected:
            continue
        found = True
        exp_set = set(expected)
        manifest["seasons"][_season_key(sl.season_label, sl.season_type)] = {
            "season_label": sl.season_label,
            "season_type": sl.season_type,
            "expected_game_count": len(expected),
            "expected_game_ids": expected,
            "completed_game_count": len(existing & exp_set),
            "completed_game_ids": sorted(existing & exp_set),
            "failed_game_ids": sorted(failed & exp_set),
        }

    if not found:
        print(f"No local season metadata found in {local_dir}.")
        return 1

    _save_manifest(mp, manifest)
    print(f"Rebuilt manifest at {mp} with {len(manifest['seasons'])} entries.")
    return 0


def show_status(
    *, output_file: str, season_label: str | None = None,
    season_types: Iterable[str] = DEFAULT_SEASON_TYPES,
) -> int:
    mp = _manifest_path(Path(output_file))
    seasons = _load_manifest(mp).get("seasons", {})

    if not seasons:
        print(f"No manifest at {mp}.")
        return 1

    keys = ([_season_key(season_label, st) for st in season_types] if season_label
            else sorted(seasons.keys()))

    found = incomplete = 0
    for sk in keys:
        entry = seasons.get(sk)
        if not isinstance(entry, dict):
            continue
        found += 1
        done = _is_season_complete(entry)
        if not done:
            incomplete += 1
        c, e = entry.get("completed_game_count", 0), entry.get("expected_game_count", 0)
        print(f"{entry.get('season_label', '?')} | {entry.get('season_type', '?')}: "
              f"{'complete' if done else 'incomplete'} ({c}/{e})")

    if not found:
        print(f"No entries for {season_label}." if season_label else "No entries found.")
        return 1
    return 0 if incomplete == 0 else 2


# -- CLI ----------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="Download NBA box score payloads.")
    p.add_argument("--start-year", type=int, default=2000)
    p.add_argument("--end-year", type=int, default=2025)
    p.add_argument("--season-label", type=str, default=None)
    p.add_argument("--output-dir", type=str, default="data/season")
    p.add_argument("--output-file", type=str, default="data/box_scores.jsonl")
    p.add_argument("--season-types", nargs="*", default=list(DEFAULT_SEASON_TYPES))
    p.add_argument("--resume", action="store_true")
    p.add_argument("--status-only", action="store_true")
    p.add_argument("--rebuild-manifest", action="store_true")
    p.add_argument("--pause-between-slices", type=float, default=1.5)
    p.add_argument("--pause-between-games", type=float, default=0.75)
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--max-timeout", type=int, default=45)
    p.add_argument("--timeout-step", type=int, default=5)
    p.add_argument("--max-retries", type=int, default=4)
    p.add_argument("--invalid-retries", type=int, default=3)
    p.add_argument("--max-backoff", type=float, default=30.0)
    p.add_argument("--read-timeout-streak-limit", type=int, default=3)
    p.add_argument("--max-elapsed", type=float, default=180.0)
    p.add_argument("--failure-threshold", type=int, default=5)
    p.add_argument("--failure-cooldown", type=float, default=20.0)
    p.add_argument("--failed-games-output", type=str, default="data/failed_box_score_games.txt")
    args = p.parse_args()

    if args.rebuild_manifest:
        raise SystemExit(rebuild_manifest(
            output_file=args.output_file, output_dir=args.output_dir,
            start_year=args.start_year, end_year=args.end_year,
            season_types=args.season_types, failed_games_output=args.failed_games_output,
        ))

    if args.status_only:
        raise SystemExit(show_status(
            output_file=args.output_file, season_label=args.season_label,
            season_types=args.season_types,
        ))

    cfg = FetchConfig(
        timeout=args.timeout, max_timeout=args.max_timeout,
        timeout_step=args.timeout_step, max_retries=args.max_retries,
        invalid_retries=args.invalid_retries, max_backoff=args.max_backoff,
        read_timeout_streak_limit=args.read_timeout_streak_limit,
        max_elapsed=args.max_elapsed,
    )

    download_box_scores_jsonl(
        start_year=args.start_year, end_year=args.end_year,
        output_file=args.output_file, season_types=args.season_types,
        pause_between_slices=args.pause_between_slices,
        pause_between_games=args.pause_between_games,
        resume=args.resume, fetch_cfg=cfg,
        consecutive_failure_threshold=args.failure_threshold,
        failure_cooldown=args.failure_cooldown,
        failed_games_output=args.failed_games_output,
    )


if __name__ == "__main__":
    main()
