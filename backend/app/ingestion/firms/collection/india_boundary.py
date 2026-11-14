import json

from pathlib import Path
from typing import Optional

from shapely.geometry import shape, Point
from shapely.ops import unary_union


class IndiaBoundary:
    """
    Load India's geographic boundary and filter
    fire observations using the actual polygon.
    """

    def __init__(self, geojson_path: Optional[str] = None):

        if geojson_path is None:
            project_root = Path(__file__).resolve().parents[5]

            geojson_path = (
                project_root
                / "data"
                / "boundaries"
                / "india_soi.geojson"
            )

        self.geojson_path = Path(geojson_path)

        self.geometry = self._load_geometry()

    def _load_geometry(self):

        if not self.geojson_path.exists():
            raise FileNotFoundError(
                f"India boundary file not found: "
                f"{self.geojson_path}"
            )

        with self.geojson_path.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        geojson_type = data.get("type")

        if geojson_type == "FeatureCollection":

            geometries = [
                shape(feature["geometry"])
                for feature in data["features"]
                if feature.get("geometry")
            ]

            if not geometries:
                raise ValueError(
                    "GeoJSON contains no valid geometries."
                )

            geometry = unary_union(geometries)

        elif geojson_type == "Feature":

            geometry = shape(data["geometry"])

        else:

            geometry = shape(data)

        if geometry.is_empty:
            raise ValueError(
                "India boundary geometry is empty."
            )

        if not geometry.is_valid:
            raise ValueError(
                "India boundary geometry is invalid."
            )

        if geometry.geom_type not in (
            "Polygon",
            "MultiPolygon"
        ):
            raise ValueError(
                f"Unexpected geometry type: "
                f"{geometry.geom_type}"
            )

        return geometry

    def contains(self, latitude: float, longitude: float) -> bool:
        """
        Check whether a coordinate falls inside
        or on the India boundary.
        """

        point = Point(longitude, latitude)

        return self.geometry.covers(point)

    def filter_observations(self, observations: list) -> list:
        """
        Keep only observations inside India's boundary.
        """

        return [
            observation
            for observation in observations
            if self.contains(
                observation.latitude,
                observation.longitude
            )
        ]