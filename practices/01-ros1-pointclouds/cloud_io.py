"""Provided PointCloud2 I/O. No rotation is implemented here."""
import copy
import numpy as np


def _views(msg, buffer):
    if len(buffer) != msg.row_step * msg.height:
        raise ValueError('Invalid PointCloud2 data length')
    if msg.row_step < msg.width * msg.point_step:
        raise ValueError('Invalid row_step')
    fields = {f.name: f for f in msg.fields}
    views = []
    for name in ('x', 'y', 'z'):
        f = fields[name]
        if f.count != 1 or f.datatype not in (7, 8):
            raise ValueError('xyz must be scalar FLOAT32 or FLOAT64')
        dtype = np.dtype(('>' if msg.is_bigendian else '<') + ('f4' if f.datatype == 7 else 'f8'))
        if f.offset < 0 or f.offset + dtype.itemsize > msg.point_step:
            raise ValueError('Invalid field offset')
        views.append(np.ndarray((msg.height, msg.width), dtype=dtype,
                                buffer=buffer, offset=f.offset,
                                strides=(msg.row_step, msg.point_step)))
    return views


def read_xyz(msg):
    """Return N x 3 float64 copy, including invalid points; preserve row order."""
    if msg.height * msg.width == 0:
        return np.empty((0, 3), dtype=np.float64)
    return np.column_stack([a.ravel() for a in _views(msg, msg.data)]).astype(np.float64)


def replace_xyz(msg, xyz, frame_id):
    """Copy message, modify only xyz bytes and frame_id. Keep stamp/fields/padding."""
    xyz = np.asarray(xyz)
    if xyz.shape != (msg.height * msg.width, 3):
        raise ValueError('Point count/order must not change')
    result = copy.deepcopy(msg)
    buffer = bytearray(msg.data)
    if len(xyz):
        for i, view in enumerate(_views(msg, buffer)):
            view[:] = xyz[:, i].reshape(msg.height, msg.width)
    result.data = bytes(buffer)
    result.header.frame_id = frame_id
    return result
