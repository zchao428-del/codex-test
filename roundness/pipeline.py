"""Fixed-datum radial errors, not minimum-zone roundness or a machining solver."""
import csv
import hashlib
import json
import math
from pathlib import Path


def read_profile(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["angle_deg", "radial_error_um"]:
            raise ValueError("CSV header must be angle_deg,radial_error_um")
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Malformed CSV row")
            a, e = float(row["angle_deg"]), float(row["radial_error_um"])
            if not math.isfinite(a) or not math.isfinite(e) or a != int(a):
                raise ValueError("Angles must be integers; all values must be finite")
            rows.append((int(a), e))
    if len(rows) != 360 or sorted(a for a, _ in rows) != list(range(360)):
        raise ValueError("Exactly one point for every angle 0..359 is required")
    return [e for _, e in sorted(rows)]


def calculate(errors, config):
    required = {"nominal_radius_mm", "gain", "mode", "removal_direction", "z_mm", "max_compensation_um"}
    if set(config) != required:
        raise ValueError("Config keys must match documented contract")
    for key in ("nominal_radius_mm", "gain", "z_mm", "max_compensation_um"):
        if isinstance(config[key], bool) or not isinstance(config[key], (int, float)) or not math.isfinite(config[key]):
            raise ValueError(f"Invalid numeric value: {key}")
    radius, gain = config["nominal_radius_mm"], config["gain"]
    if radius <= 0 or not 0 <= gain <= 1 or config["max_compensation_um"] <= 0:
        raise ValueError("Positive radius/limit and gain in [0,1] required")
    if config["mode"] not in ("bidirectional", "remove_only") or config["removal_direction"] not in ("radius_decrease", "radius_increase"):
        raise ValueError("Invalid mode or removal direction")
    if len(errors) != 360 or any(not math.isfinite(e) for e in errors):
        raise ValueError("360 finite errors required")
    mean = sum(errors)/360
    # Preserve mean size: compensate shape relative to the supplied fixed datum.
    delta = [-gain*(e-mean) for e in errors]
    if config["mode"] == "remove_only":
        offset = max(delta) if config["removal_direction"] == "radius_decrease" else min(delta)
        delta = [d-offset for d in delta]
    if max(abs(d) for d in delta) > config["max_compensation_um"] + 1e-9:
        raise ValueError("Compensation exceeds configured limit; no clipping applied")
    result = []
    for a, (e, d) in enumerate(zip(errors, delta)):
        r = radius+d/1000
        if r <= 0:
            raise ValueError("Non-positive compensated radius")
        theta = math.radians(a)
        result.append((a, e, d, r, r*math.cos(theta), r*math.sin(theta), config["z_mm"]))
    return result, {"point_count":360, "mean_error_um":mean, "fixed_datum_radial_pv_um":max(errors)-min(errors), "min_compensation_um":min(delta), "max_compensation_um":max(delta), "status":"candidate_unvalidated"}


def dxf_text(rows):
    pairs = [(0,"SECTION"),(2,"HEADER"),(9,"$ACADVER"),(1,"AC1015"),(9,"$INSUNITS"),(70,4),(0,"ENDSEC"),(0,"SECTION"),(2,"ENTITIES"),(0,"LWPOLYLINE"),(100,"AcDbEntity"),(8,"COMPENSATION"),(100,"AcDbPolyline"),(90,360),(70,1),(38,rows[0][6])]
    for row in rows:
        pairs.extend([(10,format(row[4],".12g")),(20,format(row[5],".12g"))])
    pairs.extend([(0,"ENDSEC"),(0,"EOF")])
    return "".join(f"{code}\n{value}\n" for code,value in pairs)


def run(source, config, output):
    rows, report = calculate(read_profile(source), config)
    report.update({"schema_version":"1.0", "config":config, "input_sha256":hashlib.sha256(Path(source).read_bytes()).hexdigest(), "coordinate_system":"mm, +X=0deg, +Y=90deg, CCW viewed from +Z", "limitations":["No circle fitting, filtering or eccentricity removal", "No validated mold-to-part transfer model", "UG10.0 import not yet verified"]})
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be empty; existing results are preserved")
    output.mkdir(parents=True, exist_ok=True)
    with (output/"compensated_profile.csv").open("w", encoding="utf-8", newline="") as stream:
        writer=csv.writer(stream)
        writer.writerow(["angle_deg","radial_error_um","compensation_um","radius_mm","x_mm","y_mm","z_mm"])
        writer.writerows(rows)
    (output/"compensated_profile.dxf").write_text(dxf_text(rows), encoding="ascii")
    (output/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report
