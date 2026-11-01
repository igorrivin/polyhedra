"""Normalize an explicitly declared approval schema without rewriting evidence."""
import re

from checkpoint_lib import get_pointer, require


def approved_source_map(record, pin):
    value = get_pointer(record, pin["source_sha256_pointer"])
    shape = pin.get("source_sha256_shape", "mapping")
    if shape == "mapping":
        require(isinstance(value, dict), "source approval must contain a hash mapping")
        result = dict(value)
    elif shape == "path-record-list":
        require(isinstance(value, list) and value, "source approval must contain a nonempty path-record list")
        result = {}
        for row in value:
            require(isinstance(row, dict) and "path" in row and "sha256" in row, "invalid approval path record")
            require(row["path"] not in result, "duplicate approval source path")
            result[row["path"]] = row["sha256"]
    else:
        raise RuntimeError("unsupported explicitly declared approval schema: " + str(shape))
    require(result and all(isinstance(p, str) and isinstance(h, str)
                           and re.fullmatch(r"[0-9a-f]{64}", h) for p, h in result.items()),
            "invalid or empty approval source map")
    return result
