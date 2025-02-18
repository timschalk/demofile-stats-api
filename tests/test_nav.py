import sys
import os
import math
from collections import defaultdict
from unittest.mock import patch
import pytest
import numpy as np


from awpy.data import NAV, create_nav_graphs
from awpy.analytics.nav import (
    area_distance,
    find_closest_area,
    generate_position_token,
    tree,
    point_distance,
    point_in_area,
    generate_centroids,
    stepped_hull,
    position_state_distance,
    token_state_distance,
    get_array_for_frame,
    frame_distance,
    token_distance,
    generate_area_distance_matrix,
    generate_place_distance_matrix,
)


class TestNav:
    """Class to test the nav-related functions."""

    def setup_class(self):
        """Setup class by defining custom NAV and NAV_GRAPHS"""
        # Create mock NAV mesh like this:
        # Each area is described in the format areadId(x,y)
        # Arrows indicate (directed) edges
        # 1(2,0) -> 2(3,0)
        #  ^
        #  |
        #  v
        # 3(2,-2)
        self.fake_nav = {
            "de_mock": {
                1: {
                    "areaName": "Place1",
                    "northWestX": 2,
                    "northWestY": 0,
                    "northWestZ": 0,
                    "southEastX": 2,
                    "southEastY": 0,
                    "southEastZ": 0,
                },
                2: {
                    "areaName": "Place2",
                    "northWestX": 3,
                    "northWestY": 0,
                    "northWestZ": 0,
                    "southEastX": 3,
                    "southEastY": 0,
                    "southEastZ": 0,
                },
                3: {
                    "areaName": "Place3",
                    "northWestX": 2,
                    "northWestY": -2,
                    "northWestZ": 0,
                    "southEastX": 2,
                    "southEastY": -2,
                    "southEastZ": 0,
                },
            }
        }

        self.dir = os.path.join(os.getcwd(), "nav")
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        else:
            raise AssertionError(
                "This test needs to be executed in a directory where it can savely create and delte a 'nav' subdir!"
            )
        self.map_name = "de_mock"
        self.file_name = f"{self.map_name}.txt"
        with open(os.path.join(self.dir, self.file_name), "w", encoding="utf8") as f:
            f.write("1,2\n")
            f.write("1,3\n")
            f.write("3,1\n")

        self.fake_graph = create_nav_graphs(
            self.fake_nav, os.path.join(os.getcwd(), "")
        )

        self.expected_area_matrix = {
            "1": {
                "1": {"euclidean": 0, "graph": 0, "geodesic": 0},
                "2": {"euclidean": 1.0, "graph": 1.0, "geodesic": 1.0},
                "3": {"euclidean": 2.0, "graph": 1.0, "geodesic": 2.0},
            },
            "2": {
                "1": {
                    "euclidean": 1.0,
                    "graph": float("inf"),
                    "geodesic": float("inf"),
                },
                "2": {"euclidean": 0, "graph": 0, "geodesic": 0},
                "3": {
                    "euclidean": math.sqrt(5),
                    "graph": float("inf"),
                    "geodesic": float("inf"),
                },
            },
            "3": {
                "1": {"euclidean": 2.0, "graph": 1.0, "geodesic": 2.0},
                "2": {"euclidean": math.sqrt(5), "graph": 2.0, "geodesic": 3.0},
                "3": {"euclidean": 0, "graph": 0, "geodesic": 0},
            },
        }
        self.expected_place_matrix = {
            "Place1": {
                "Place1": {
                    "euclidean": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                    "graph": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                    "geodesic": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                },
                "Place2": {
                    "euclidean": {
                        "centroid": 1.0,
                        "representative_point": 1.0,
                        "median_dist": 1.0,
                    },
                    "graph": {
                        "centroid": 1.0,
                        "representative_point": 1.0,
                        "median_dist": 1.0,
                    },
                    "geodesic": {
                        "centroid": 1.0,
                        "representative_point": 1.0,
                        "median_dist": 1.0,
                    },
                },
                "Place3": {
                    "euclidean": {
                        "centroid": 2.0,
                        "representative_point": 2.0,
                        "median_dist": 2.0,
                    },
                    "graph": {
                        "centroid": 1.0,
                        "representative_point": 1.0,
                        "median_dist": 1.0,
                    },
                    "geodesic": {
                        "centroid": 2.0,
                        "representative_point": 2.0,
                        "median_dist": 2.0,
                    },
                },
            },
            "Place2": {
                "Place1": {
                    "euclidean": {
                        "centroid": 1.0,
                        "representative_point": 1.0,
                        "median_dist": 1.0,
                    },
                    "graph": {
                        "centroid": float("inf"),
                        "representative_point": float("inf"),
                        "median_dist": float("inf"),
                    },
                    "geodesic": {
                        "centroid": float("inf"),
                        "representative_point": float("inf"),
                        "median_dist": float("inf"),
                    },
                },
                "Place2": {
                    "euclidean": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                    "graph": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                    "geodesic": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                },
                "Place3": {
                    "euclidean": {
                        "centroid": math.sqrt(5),
                        "representative_point": math.sqrt(5),
                        "median_dist": math.sqrt(5),
                    },
                    "graph": {
                        "centroid": float("inf"),
                        "representative_point": float("inf"),
                        "median_dist": float("inf"),
                    },
                    "geodesic": {
                        "centroid": float("inf"),
                        "representative_point": float("inf"),
                        "median_dist": float("inf"),
                    },
                },
            },
            "Place3": {
                "Place1": {
                    "euclidean": {
                        "centroid": 2.0,
                        "representative_point": 2.0,
                        "median_dist": 2.0,
                    },
                    "graph": {
                        "centroid": 1.0,
                        "representative_point": 1.0,
                        "median_dist": 1.0,
                    },
                    "geodesic": {
                        "centroid": 2.0,
                        "representative_point": 2.0,
                        "median_dist": 2.0,
                    },
                },
                "Place2": {
                    "euclidean": {
                        "centroid": math.sqrt(5),
                        "representative_point": math.sqrt(5),
                        "median_dist": math.sqrt(5),
                    },
                    "graph": {
                        "centroid": 2.0,
                        "representative_point": 2.0,
                        "median_dist": 2.0,
                    },
                    "geodesic": {
                        "centroid": 3.0,
                        "representative_point": 3.0,
                        "median_dist": 3.0,
                    },
                },
                "Place3": {
                    "euclidean": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                    "graph": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                    "geodesic": {
                        "centroid": 0,
                        "representative_point": 0,
                        "median_dist": 0,
                    },
                },
            },
        }

    def teardown_class(self):
        """Clean up by delete created file and directory"""
        self.fake_nav = None
        self.fake_graph = None
        self.expected_area_matrix = None
        self.expected_place_matrix = None
        for file in os.listdir(self.dir):
            if (
                file == self.file_name
                or file == f"area_distance_matrix_{self.map_name}.json"
                or file == f"place_distance_matrix_{self.map_name}.json"
            ):
                os.remove(os.path.join(self.dir, file))
        os.rmdir(self.dir)

    def test_point_in_area(self):
        """Tests point in area"""
        with pytest.raises(ValueError):
            point_in_area(map_name="test", area_id=3814, point=[0, 0, 0])
        with pytest.raises(ValueError):
            point_in_area(map_name="de_dust2", area_id=0, point=[0, 0, 0])
        with pytest.raises(ValueError):
            point_in_area(map_name="de_dust2", area_id=3814, point=[0])
        avg_x = (
            NAV["de_dust2"][152]["northWestX"] + NAV["de_dust2"][152]["southEastX"]
        ) / 2
        avg_y = (
            NAV["de_dust2"][152]["northWestY"] + NAV["de_dust2"][152]["southEastY"]
        ) / 2
        avg_z = (
            NAV["de_dust2"][152]["northWestZ"] + NAV["de_dust2"][152]["southEastZ"]
        ) / 2
        assert point_in_area(
            map_name="de_dust2", area_id=152, point=[avg_x, avg_y, avg_z]
        )
        assert not point_in_area(
            map_name="de_dust2", area_id=3814, point=[avg_x, avg_y, avg_z]
        )

    def test_find_area(self):
        """Tests find_area"""
        with pytest.raises(ValueError):
            find_closest_area(map_name="test", point=[0, 0, 0])
        with pytest.raises(ValueError):
            find_closest_area(map_name="de_dust2", point=[0, 0])
        avg_x = (
            NAV["de_dust2"][152]["northWestX"] + NAV["de_dust2"][152]["southEastX"]
        ) / 2
        avg_y = (
            NAV["de_dust2"][152]["northWestY"] + NAV["de_dust2"][152]["southEastY"]
        ) / 2
        avg_z = (
            NAV["de_dust2"][152]["northWestZ"] + NAV["de_dust2"][152]["southEastZ"]
        ) / 2
        area_found = find_closest_area(map_name="de_dust2", point=[avg_x, avg_y, avg_z])
        assert isinstance(area_found, dict)
        assert area_found["areaId"] == 152

    def test_area_distance(self):
        """Tests area distance"""
        with pytest.raises(ValueError):
            area_distance(map_name="test", area_a=152, area_b=152, dist_type="graph")
        with pytest.raises(ValueError):
            area_distance(map_name="de_dust2", area_a=0, area_b=0, dist_type="graph")
        with pytest.raises(ValueError):
            area_distance(map_name="de_dust2", area_a=152, area_b=152, dist_type="test")
        graph_dist = area_distance(
            map_name="de_dust2", area_a=152, area_b=152, dist_type="graph"
        )
        geo_dist = area_distance(
            map_name="de_dust2", area_a=152, area_b=152, dist_type="geodesic"
        )
        assert isinstance(graph_dist, dict)
        assert graph_dist["distanceType"] == "graph"
        assert graph_dist["distance"] == 0
        assert isinstance(geo_dist, dict)
        assert geo_dist["distanceType"] == "geodesic"
        assert geo_dist["distance"] == 0
        graph_dist = area_distance(
            map_name="de_dust2", area_a=8251, area_b=8773, dist_type="graph"
        )
        geo_dist = area_distance(
            map_name="de_dust2", area_a=8251, area_b=8773, dist_type="geodesic"
        )
        assert graph_dist["distance"] == float("inf")
        assert geo_dist["distance"] == float("inf")
        assert len(graph_dist["areas"]) == 0
        assert len(geo_dist["areas"]) == 0
        euc_dist = area_distance(
            map_name="de_dust2", area_a=8251, area_b=8773, dist_type="euclidean"
        )
        assert isinstance(euc_dist, dict)
        assert len(euc_dist["areas"]) == 0

    def test_point_distance(self):
        """Tests point distance"""
        with pytest.raises(ValueError):
            point_distance(
                map_name="test", point_a=[0, 0, 0], point_b=[0, 0, 0], dist_type="graph"
            )
        with pytest.raises(ValueError):
            point_distance(
                map_name="de_dust2", point_a=[0, 0], point_b=[0, 0], dist_type="graph"
            )
        with pytest.raises(ValueError):
            point_distance(
                map_name="test",
                point_a=[0, 0, 0],
                point_b=[0, 0, 0],
                dist_type="geodesic",
            )
        with pytest.raises(ValueError):
            point_distance(
                map_name="de_dust2",
                point_a=[0, 0],
                point_b=[0, 0],
                dist_type="geodesic",
            )
        assert (
            point_distance(
                map_name="de_dust2",
                point_a=[0, 0],
                point_b=[1, 1],
                dist_type="euclidean",
            )["distance"]
            == 1.4142135623730951
        )
        assert (
            point_distance(
                map_name="de_dust2",
                point_a=[0, 0],
                point_b=[1, 1],
                dist_type="manhattan",
            )["distance"]
            == 2
        )
        assert (
            point_distance(
                map_name="de_dust2",
                point_a=[0, 0],
                point_b=[1, 1],
                dist_type="canberra",
            )["distance"]
            == 2.0
        )
        assert (
            point_distance(
                map_name="de_dust2", point_a=[-1, 5], point_b=[2, 1], dist_type="cosine"
            )["distance"]
            == 0.7368825942078912
        )
        avg_x = (
            NAV["de_dust2"][152]["northWestX"] + NAV["de_dust2"][152]["southEastX"]
        ) / 2
        avg_y = (
            NAV["de_dust2"][152]["northWestY"] + NAV["de_dust2"][152]["southEastY"]
        ) / 2
        avg_z = (
            NAV["de_dust2"][152]["northWestZ"] + NAV["de_dust2"][152]["southEastZ"]
        ) / 2
        assert (
            point_distance(
                map_name="de_dust2",
                point_a=[avg_x, avg_y, avg_z],
                point_b=[avg_x, avg_y, avg_z],
                dist_type="graph",
            )["distance"]
            == 0
        )
        assert (
            point_distance(
                map_name="de_dust2",
                point_a=[avg_x, avg_y, avg_z],
                point_b=[avg_x, avg_y, avg_z],
                dist_type="geodesic",
            )["distance"]
            == 0
        )

        with pytest.raises(ValueError):
            point_distance(
                map_name="de_dust2",
                point_a=[0, 0],
                point_b=[1, 1],
                dist_type="distance_type_does_not_exist",
            )

    def test_position_token(self):
        """Tests that position token returns correct values"""
        map_name = "de_nuke"
        frame = {
            "ct": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                        "isAlive": False,
                    }
                ]
            },
            "t": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                        "isAlive": True,
                    }
                ]
            },
        }
        token = generate_position_token(map_name, frame)
        assert isinstance(token, dict)
        assert "tToken" in token
        assert "ctToken" in token
        assert "token" in token
        assert token["tToken"] == "000000000000000000100000000000"
        assert token["ctToken"] == "000000000000000000000000000000"
        assert (
            token["token"]
            == "000000000000000000000000000000000000000000000000100000000000"
        )
        frame = {
            "ct": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                        "isAlive": True,
                    }
                ]
            },
            "t": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                        "isAlive": False,
                    }
                ]
            },
        }
        token = generate_position_token(map_name, frame)
        assert isinstance(token, dict)
        assert "tToken" in token
        assert "ctToken" in token
        assert "token" in token
        assert token["tToken"] == "000000000000000000000000000000"
        assert token["ctToken"] == "000000000000000000100000000000"
        assert (
            token["token"]
            == "000000000000000000100000000000000000000000000000000000000000"
        )

        with pytest.raises(ValueError):
            generate_position_token("de_does_not_exist", frame)

        frame = {
            "ct": {"players": []},
            "t": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                        "isAlive": True,
                    }
                ]
            },
        }
        with pytest.raises(ValueError):
            generate_position_token(map_name, frame)

    def test_tree(self):
        """Tests tree"""
        my_tree = tree()
        my_tree["1"]["A"][666][("test", 42)] = "Should work"

    def test_generate_area_distance_matrix(self):
        """Tests generate_area_distance_matrix"""
        # Need to mock awpy.data.NAV to properly test this
        def default_to_regular(d):
            if isinstance(d, defaultdict):
                d = {k: default_to_regular(v) for k, v in d.items()}
            return d

        with patch("awpy.analytics.nav.NAV", self.fake_nav):
            with patch("awpy.analytics.nav.NAV_GRAPHS", self.fake_graph):
                with patch("awpy.analytics.nav.PATH", os.path.join(os.getcwd(), "")):
                    result_matrix = generate_area_distance_matrix(
                        map_name="de_mock", save=True
                    )

        assert isinstance(result_matrix, dict)
        assert os.path.exists(
            os.path.join(self.dir, "area_distance_matrix_de_mock.json")
        )

        assert self.expected_area_matrix == result_matrix
        with pytest.raises(ValueError):
            _ = generate_area_distance_matrix("de_does_not_exist")

    def test_generate_place_distance_matrix(self):
        """Tests generate_place_distance_matrix"""
        # Need to mock awpy.data.NAV to properly test this
        with patch("awpy.analytics.nav.NAV", self.fake_nav):
            with patch("awpy.analytics.nav.NAV_GRAPHS", self.fake_graph):
                with patch("awpy.analytics.nav.PATH", os.path.join(os.getcwd(), "")):
                    with patch("awpy.analytics.nav.AREA_DIST_MATRIX", {}):
                        result_matrix_1 = generate_place_distance_matrix(
                            map_name="de_mock", save=True
                        )
                    with patch(
                        "awpy.analytics.nav.AREA_DIST_MATRIX",
                        {self.map_name: self.expected_area_matrix},
                    ):
                        result_matrix_2 = generate_place_distance_matrix(
                            map_name="de_mock", save=False
                        )

        assert isinstance(result_matrix_1, dict)
        assert os.path.exists(
            os.path.join(self.dir, f"place_distance_matrix_{self.map_name}.json")
        )

        assert isinstance(result_matrix_2, dict)

        assert self.expected_place_matrix == result_matrix_1
        assert self.expected_place_matrix == result_matrix_2
        with pytest.raises(ValueError):
            _ = generate_place_distance_matrix("de_does_not_exist")

    def test_generate_centroids(self):
        """Tests generate centroids"""
        with pytest.raises(ValueError):
            generate_centroids(map_name="test")
        centroids, reps = generate_centroids("de_inferno")
        assert isinstance(centroids, dict)
        assert "Quad" in centroids
        assert centroids == {
            "CTSpawn": 2831,
            "": 80,
            "BombsiteA": 3129,
            "TRamp": 190,
            "TSpawn": 3030,
            "LowerMid": 55,
            "TopofMid": 32,
            "Quad": 124,
            "Upstairs": 1306,
            "BombsiteB": 520,
            "Banana": 791,
            "Ruins": 225,
            "Middle": 8,
            "BackAlley": 269,
            "Apartments": 1606,
            "Graveyard": 3126,
            "SecondMid": 1478,
            "Balcony": 2367,
            "Pit": 305,
            "Arch": 82,
            "Bridge": 57,
            "Underpass": 2944,
            "Library": 911,
            "Deck": 74,
            "Kitchen": 257,
        }
        assert isinstance(reps, dict)
        assert "" in reps
        assert reps == {
            "CTSpawn": 2832,
            "": 749,
            "BombsiteA": 3128,
            "TRamp": 190,
            "TSpawn": 3030,
            "LowerMid": 314,
            "TopofMid": 32,
            "Quad": 124,
            "Upstairs": 1306,
            "BombsiteB": 1968,
            "Banana": 109,
            "Ruins": 377,
            "Middle": 338,
            "BackAlley": 363,
            "Apartments": 2367,
            "Graveyard": 3126,
            "SecondMid": 730,
            "Balcony": 3050,
            "Pit": 2518,
            "Arch": 59,
            "Bridge": 57,
            "Underpass": 2946,
            "Library": 911,
            "Deck": 255,
            "Kitchen": 441,
        }

    def test_stepped_hull(self):
        """Tests stepped hull"""
        hull = stepped_hull(
            [
                (0, 0),
                (1, 0),
                (0, 1),
                (1, 1),
                (0.5, 0.5),
                (0.2, 0.2),
            ]
        )
        assert isinstance(hull, list)
        assert hull == [(0, 1), (0, 0), (1, 0), (1, 1), (0, 1)]
        assert stepped_hull([(1, 1)]) == [(1, 1)]
        assert stepped_hull([]) == []

    def test_position_state_distance(self):
        """Tests position state distance"""
        pos_state1 = np.array([[[-500, -850, 100]]])
        pos_state2 = np.array([[[-550, -100, 130]], [[1, 1, 1]]])
        with pytest.raises(ValueError):
            position_state_distance(
                "de_ancient", pos_state1, pos_state2, distance_type="euclidean"
            )

        pos_state1 = np.array([[[-500, -850, 100, 6]]])
        pos_state2 = np.array([[[-550, -100, 130, 6]]])
        with pytest.raises(ValueError):
            position_state_distance(
                "de_ancient", pos_state1, pos_state2, distance_type="euclidean"
            )

        pos_state1 = np.array([[[-500, -850, 100]]])
        pos_state2 = np.array([[[-550, -100, 130]]])
        with pytest.raises(ValueError):
            position_state_distance(
                "de_map_does_not_exist",
                pos_state1,
                pos_state2,
                distance_type="euclidean",
            )
        with pytest.raises(ValueError):
            position_state_distance(
                "de_ancient",
                pos_state1,
                pos_state2,
                distance_type="distance_type_does_not_exist",
            )
        dist = position_state_distance(
            "de_ancient", pos_state1, pos_state2, distance_type="euclidean"
        )
        assert isinstance(dist, float)
        assert round(dist, 2) == 752.26

        pos_state1 = np.array([[[-500, -850, 100], [-555, -105, 135]]])
        pos_state2 = np.array([[[-550, -100, 130], [-500, -850, 100]]])
        dist = position_state_distance(
            "de_ancient", pos_state1, pos_state2, distance_type="euclidean"
        )
        assert round(dist, 2) == 4.33

        pos_state1 = np.array([[[-500, -850, 100], [-445, -105, 135]]])
        pos_state2 = np.array([[[-550, -100, 130], [-500, -850, 100]]])
        dist = position_state_distance(
            "de_ancient", pos_state1, pos_state2, distance_type="graph"
        )
        assert isinstance(dist, float)
        assert dist == 1
        with patch("awpy.analytics.nav.AREA_DIST_MATRIX", {}):
            new_dist = position_state_distance(
                "de_ancient", pos_state1, pos_state2, distance_type="graph"
            )
            assert new_dist == dist

        pos_state1 = np.array([[[-500, -850, 100]]])
        pos_state2 = np.array([[[-550, -100, 130], [-500, -850, 100]]])
        dist = position_state_distance(
            "de_ancient", pos_state1, pos_state2, distance_type="graph"
        )
        assert isinstance(dist, float)
        assert dist == 0.0

        pos_state1 = np.array([[[-2497, -224, 200]]])
        pos_state2 = np.array([[[-1900, -1200, 100]]])
        dist = position_state_distance(
            "de_dust2", pos_state1, pos_state2, distance_type="graph"
        )
        assert isinstance(dist, float)
        assert sys.maxsize / 7 < dist < sys.maxsize / 5

    def test_token_state_distance(self):
        """Tests token state distance"""
        token_array1 = np.array(
            [
                0.0,
                2.0,
                0.0,
                2.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )
        token_array2 = np.array(
            [
                0.0,
                2.0,
                0.0,
                1.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                5.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )
        with pytest.raises(ValueError):
            token_state_distance(
                "de_map_does_not_exist",
                token_array1,
                token_array2,
                distance_type="euclidean",
            )
        with pytest.raises(ValueError):
            token_state_distance(
                "de_ancient", token_array1, token_array2, distance_type="euclidean"
            )
        token_array1 = np.array(
            [
                0.0,
                2.0,
                0.0,
                2.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )
        token_array2 = np.array(
            [
                0.0,
                2.0,
                0.0,
                1.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )
        with pytest.raises(ValueError):
            token_state_distance(
                "de_ancient", token_array1, token_array2, distance_type="euclidean"
            )
        token_array1 = np.array(
            [
                0.0,
                2.0,
                0.0,
                2.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                1.0,
                1.0,
            ]
        )
        token_array2 = np.array(
            [
                0.0,
                2.0,
                0.0,
                1.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                5.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        )
        with pytest.raises(ValueError):
            token_state_distance(
                "de_ancient",
                token_array1,
                token_array2,
                distance_type="distance_type_does_not_exist",
            )
        with pytest.raises(ValueError):
            token_state_distance(
                "de_ancient",
                token_array1,
                token_array2,
                distance_type="graph",
                reference_point="reference_point_does_not_exist",
            )
        dist = token_state_distance(
            "de_ancient", token_array1, token_array2, distance_type="graph"
        )
        assert isinstance(dist, float)
        assert round(dist, 2) == 7.10
        dist = token_state_distance(
            "de_ancient", token_array1, token_array2, distance_type="euclidean"
        )
        assert isinstance(dist, float)
        assert round(dist, 2) == 643.12
        dist = token_state_distance(
            "de_ancient", token_array1, token_array2, distance_type="geodesic"
        )
        assert isinstance(dist, float)
        assert round(dist, 2) == 817.53

        token_array1 = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=int,
        )
        token_array2 = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=int,
        )
        dist = token_state_distance(
            "de_dust2", token_array1, token_array2, distance_type="edit_distance"
        )
        assert dist == 2
        dist = token_state_distance(
            "de_dust2",
            token_array1,
            token_array2,
            distance_type="graph",
            reference_point="representative_point",
        )
        assert isinstance(dist, float)
        assert dist == 6
        dist = token_state_distance(
            "de_dust2",
            token_array1,
            token_array2,
            distance_type="euclidean",
            reference_point="representative_point",
        )
        assert isinstance(dist, float)
        assert round(dist, 2) == 336.60
        with patch("awpy.analytics.nav.PLACE_DIST_MATRIX", {}):
            new_dist = token_state_distance(
                "de_dust2",
                token_array1,
                token_array2,
                distance_type="euclidean",
                reference_point="representative_point",
            )
            assert new_dist == dist
        dist = token_state_distance(
            "de_dust2",
            token_array1,
            token_array2,
            distance_type="geodesic",
            reference_point="representative_point",
        )
        assert isinstance(dist, float)
        assert round(dist, 2) == 838.02

        token_array1 = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=int,
        )
        token_array2 = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=int,
        )
        dist = token_state_distance(
            "de_nuke", token_array1, token_array2, distance_type="edit_distance"
        )
        assert dist == 2
        dist1 = token_state_distance(
            "de_nuke", token_array1, token_array2, distance_type="geodesic"
        )
        dist2 = token_state_distance(
            "de_nuke", token_array2, token_array1, distance_type="geodesic"
        )
        assert dist1 == dist2
        dist = token_state_distance(
            "de_nuke", token_array1, token_array2, distance_type="graph"
        )
        assert isinstance(dist, float)
        assert dist == 27
        dist = token_state_distance(
            "de_nuke", token_array1, token_array2, distance_type="euclidean"
        )
        assert isinstance(dist, float)
        assert round(dist, 2) == 2272.12
        dist = token_state_distance("de_nuke", token_array1, token_array2)
        assert isinstance(dist, float)
        assert round(dist, 2) == 4031.26

        token_array1 = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=int,
        )
        token_array2 = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=int,
        )
        assert token_state_distance(
            "de_nuke", token_array1, token_array2, distance_type="euclidean"
        ) == token_state_distance(
            "de_nuke", token_array2, token_array1, distance_type="euclidean"
        )

    def test_get_array_for_frame(self):
        """Tests get_array_for_frame"""
        frame1 = {
            "ct": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "t": {"players": []},
            "isKillFrame": False,
        }
        frame2 = {
            "ct": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "t": {"players": []},
            "isKillFrame": True,
        }
        array1_expected = np.array(
            [[[0, 0, 0]], [[-814.4315185546875, -950.5277099609375, -413.96875]]]
        )
        array2_expected = np.array(
            [
                [[0, 0, 0]],
                [[-614.4315185546875, -550.5277099609375, -213.96875]],
            ]
        )
        array1_result = get_array_for_frame(frame1)
        array2_result = get_array_for_frame(frame2)
        assert np.array_equal(array1_expected, array1_result)
        assert np.array_equal(array2_expected, array2_result)

        frame1 = {
            "t": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "ct": {"players": []},
            "isKillFrame": False,
        }
        frame2 = {
            "t": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "ct": {"players": []},
            "isKillFrame": True,
        }
        array1 = np.array(
            [[[-814.4315185546875, -950.5277099609375, -413.96875]], [[0, 0, 0]]]
        )
        array2 = np.array(
            [[[-614.4315185546875, -550.5277099609375, -213.96875]], [[0, 0, 0]]]
        )
        assert np.array_equal(array1, get_array_for_frame(frame1))
        assert np.array_equal(array2, get_array_for_frame(frame2))
        frame1 = {
            "ct": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "t": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "isKillFrame": False,
        }
        frame2 = {
            "ct": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "t": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "isKillFrame": True,
        }
        array1 = np.array(
            [
                [[-814.4315185546875, -950.5277099609375, -413.96875]],
                [[-814.4315185546875, -950.5277099609375, -413.96875]],
            ]
        )
        array2 = np.array(
            [
                [[-614.4315185546875, -550.5277099609375, -213.96875]],
                [[-614.4315185546875, -550.5277099609375, -213.96875]],
            ]
        )
        assert np.array_equal(array1, get_array_for_frame(frame1))
        assert np.array_equal(array2, get_array_for_frame(frame2))

    def test_frame_distance(self):
        """Tests frame distance"""
        map_name = "de_nuke"
        frame1 = {
            "ct": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "t": {"players": []},
            "isKillFrame": False,
        }
        frame2 = {
            "ct": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "t": {"players": []},
            "isKillFrame": True,
        }
        array1 = np.array([[[-814.4315185546875, -950.5277099609375, -413.96875]]])
        array2 = np.array([[[-614.4315185546875, -550.5277099609375, -213.96875]]])
        assert frame_distance(map_name, frame1, frame2) == position_state_distance(
            map_name, array1, array2
        )
        frame1 = {
            "t": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "ct": {"players": []},
            "isKillFrame": False,
        }
        frame2 = {
            "t": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "ct": {"players": []},
            "isKillFrame": True,
        }
        array1 = np.array([[[-814.4315185546875, -950.5277099609375, -413.96875]]])
        array2 = np.array([[[-614.4315185546875, -550.5277099609375, -213.96875]]])
        assert frame_distance(map_name, frame1, frame2) == position_state_distance(
            map_name, array1, array2
        )
        frame1 = {
            "ct": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "t": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "isKillFrame": False,
        }
        frame2 = {
            "ct": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "t": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "isKillFrame": True,
        }
        array1 = np.array(
            [
                [[-814.4315185546875, -950.5277099609375, -413.96875]],
                [[-814.4315185546875, -950.5277099609375, -413.96875]],
            ]
        )
        array2 = np.array(
            [
                [[-614.4315185546875, -550.5277099609375, -213.96875]],
                [[-614.4315185546875, -550.5277099609375, -213.96875]],
            ]
        )
        assert frame_distance(map_name, frame1, frame2) == position_state_distance(
            map_name, array1, array2
        )

        frame1 = {
            "t": {
                "players": [
                    {
                        "x": -814.4315185546875,
                        "y": -950.5277099609375,
                        "z": -413.96875,
                    }
                ]
            },
            "ct": {"players": []},
            "isKillFrame": False,
        }
        frame2 = {
            "ct": {
                "players": [
                    {
                        "x": -614.4315185546875,
                        "y": -550.5277099609375,
                        "z": -213.96875,
                    }
                ]
            },
            "t": {"players": []},
            "isKillFrame": True,
        }
        with pytest.raises(ValueError):
            frame_distance(map_name, frame1, frame2)

    def test_token_distance(self):
        """Tests token distance"""
        map_name = "de_nuke"
        token1 = "000000000000000000100000000000"
        token2 = "000000000000000000000000000001"
        array1 = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=int,
        )
        array2 = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ],
            dtype=int,
        )
        assert token_distance(map_name, token1, token2) == token_state_distance(
            map_name, array1, array2
        )
