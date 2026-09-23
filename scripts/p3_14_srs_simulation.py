"""Run the deterministic P3.14 long-horizon SRS quality gate."""

from __future__ import annotations

import json

from custom_components.locklearn.core.srs_simulation import LongHorizonSRSSimulator


def main() -> int:
    simulator = LongHorizonSRSSimulator()
    reports = simulator.run_suite()
    payload = [report.as_dict() for report in reports]
    print(json.dumps(payload, indent=2, sort_keys=True))

    failed = [
        report
        for report in reports
        if report.required_sustainable and not report.sustainable
    ]
    detector_missed = [
        report
        for report in reports
        if not report.required_sustainable and report.sustainable
    ]
    if failed or detector_missed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
