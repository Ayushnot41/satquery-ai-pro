"""Raster loading, georeferencing, and normalization layer.

Provides safe loading for GeoTIFF, JP2, and standard image formats.
Gracefully falls back to PIL/numpy if GDAL/rasterio bindings are absent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from ..schemas.imagery import BandInfo, GeoMetadata, ImageFormat, ImageryMetadata, SensorType


class RasterSizeError(ValueError):
    """Decoding a raster would exceed the workspace memory budget."""


def load_raster_data(file_path: str | Path) -> tuple[np.ndarray, GeoMetadata]:
    """Load raster file into numpy array and extract geospatial metadata."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raster file not found: {path}")

    # Attempt to load using rasterio
    try:
        import rasterio

        with rasterio.open(str(path)) as src:
            # Read bands (rasterio is (bands, height, width))
            if src.width * src.height * src.count > 100_000_000:
                raise RasterSizeError('Raster exceeds decoded size limit')
            data = src.read()
            # Transpose to (height, width, bands) for image operations
            if data.ndim == 3:
                data = np.transpose(data, (1, 2, 0))
                if data.shape[2] == 1:
                    data = data[:, :, 0]

            bounds_list = [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top]
            transform_list = list(src.transform)[:6]
            crs_str = str(src.crs) if src.crs else None

            bands_info = []
            for i in range(1, src.count + 1):
                dtype_name = str(src.dtypes[i - 1])
                nodata_val = float(src.nodatavals[i - 1]) if src.nodatavals[i - 1] is not None else None
                bands_info.append(BandInfo(index=i, dtype=dtype_name, nodata=nodata_val))

            geo = GeoMetadata(
                crs=crs_str,
                bounds=bounds_list if src.crs else None,
                transform=transform_list if src.crs else None,
                width=src.width,
                height=src.height,
                band_count=src.count,
                bands=bands_info,
                resolution=(float(src.res[0]), float(src.res[1])) if src.crs else None,
            )
            return data, geo

    except RasterSizeError:
        raise
    except Exception:
        # Fallback to PIL
        with Image.open(path) as pil_img:
            if pil_img.width * pil_img.height * max(1, len(pil_img.getbands())) > 100_000_000:
                raise RasterSizeError('Raster exceeds decoded size limit')
            # Convert palette images to RGB
            if pil_img.mode in ("P", "RGBA"):
                pil_img = pil_img.convert("RGB")
            arr = np.array(pil_img)

            width, height = pil_img.size
            bands_count = arr.shape[2] if arr.ndim == 3 else 1

            geo = GeoMetadata(
                crs=None,
                bounds=None,
                transform=None,
                width=width,
                height=height,
                band_count=bands_count,
                bands=[BandInfo(index=i + 1, dtype=str(arr.dtype)) for i in range(bands_count)],
                resolution=None,
            )
            return arr, geo


def extract_metadata(file_path: str | Path, image_id: str) -> ImageryMetadata:
    """Extract complete metadata record from raster file."""
    path = Path(file_path)
    file_size = path.stat().st_size if path.exists() else 0
    ext = path.suffix.lower()

    if ext in (".tif", ".tiff", ".geotiff"):
        fmt = ImageFormat.GEOTIFF
    elif ext == ".jp2":
        fmt = ImageFormat.JP2
    elif ext == ".png":
        fmt = ImageFormat.PNG
    elif ext in (".jpg", ".jpeg"):
        fmt = ImageFormat.JPEG
    else:
        fmt = ImageFormat.UNKNOWN

    sensor = SensorType.OPTICAL
    name_lower = path.name.lower()
    if "sar" in name_lower or "s1" in name_lower or "sentinel-1" in name_lower:
        sensor = SensorType.SAR

    _, geo = load_raster_data(path)

    return ImageryMetadata(
        id=image_id,
        filename=path.name,
        file_size_bytes=file_size,
        format=fmt,
        sensor_type=sensor,
        satellite=None,
        extra={"sensor_inferred_from_filename": True, "georeferenced": bool(geo.crs)},
        geo=geo,
    )
