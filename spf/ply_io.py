"""
Self-contained PLY reader/writer, numpy only.

Binary little-endian PLY is all this project needs. Keeping the dependency list to
numpy + scipy + matplotlib is deliberate: it makes the repository runnable years
from now without chasing a binary point-cloud library.
"""
from __future__ import annotations

import numpy as np

_TYPES = {
    "char": "i1", "int8": "i1", "uchar": "u1", "uint8": "u1",
    "short": "i2", "int16": "i2", "ushort": "u2", "uint16": "u2",
    "int": "i4", "int32": "i4", "uint": "u4", "uint32": "u4",
    "float": "f4", "float32": "f4", "double": "f8", "float64": "f8",
}


def read_ply(path):
    """Read a binary PLY and return its points as an (n, 3) float64 array (XYZ only)."""
    with open(path, "rb") as f:
        raw = f.read()
    end = raw.find(b"end_header")
    if end < 0:
        raise ValueError(f"{path}: not a PLY (no end_header)")
    nl = raw.find(b"\n", end)
    header = raw[:nl].decode("ascii", "replace")
    body = raw[nl + 1:]

    fmt = None
    n = None
    props = []
    in_vertex = False
    for line in header.splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] == "format":
            fmt = t[1]
        elif t[0] == "element":
            in_vertex = (t[1] == "vertex")
            if in_vertex:
                n = int(t[2])
        elif t[0] == "property" and in_vertex:
            props.append((t[2], _TYPES[t[1]]))
    endian = {"binary_little_endian": "<", "binary_big_endian": ">"}.get(fmt)
    if endian is None:
        raise ValueError(f"{path}: only binary PLY is supported (got '{fmt}')")

    dtype = np.dtype([(name, endian + kind) for name, kind in props])
    rec = np.frombuffer(body, dtype=dtype, count=n)
    return np.column_stack([rec["x"], rec["y"], rec["z"]]).astype(np.float64)


def write_ply_scalar(path, xyz, values, name="shared_presence"):
    """Write XYZ + one float32 scalar per point as binary little-endian PLY.

    The scalar is named so the file opens in CloudCompare with the field already
    present, ready to colour with a ramp.
    """
    xyz = np.asarray(xyz, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64).ravel()
    n = len(xyz)
    if len(values) != n:
        raise ValueError("values and xyz must have the same length")

    arr = np.empty(n, dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), (name, "<f4")])
    arr["x"] = xyz[:, 0]
    arr["y"] = xyz[:, 1]
    arr["z"] = xyz[:, 2]
    arr[name] = values

    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {n}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        f"property float {name}\n"
        "end_header\n"
    ).encode("ascii")
    with open(path, "wb") as f:
        f.write(header)
        f.write(arr.tobytes())
