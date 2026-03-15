"""Path関連のユーティリティ関数"""

import math
import time

import requests

from commons.redis_client import cache_get_json, cache_set_json

DOMAIN_URL = "https://cyberjapandata.gsi.go.jp/xyz/dem/"
DEFAULT_ZOOM = 14


def fetch_dem_data(z: int, x: int, y: int) -> dict | None:
    """
    指定されたz/x/y座標のDEMデータを取得（Redisキャッシュ対応）

    Args:
        z: ズームレベル
        x: X座標
        y: Y座標

    Returns:
        dict: (i, j) -> elevation のマッピング
        None: エラー時
    """
    cache_key = f"dem:{z}:{x}:{y}"

    # Redisキャッシュから読み込み
    cached = cache_get_json(cache_key)
    if cached is not None:
        # JSON キーは文字列 "i_j" 形式 → タプル (i, j) に復元
        return {tuple(int(v) for v in k.split("_")): val for k, val in cached.items()}

    url = f"{DOMAIN_URL}{z}/{x}/{y}.txt"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        time.sleep(0.5)  # Rate limiting to avoid overwhelming the API

        # カンマ区切りデータをパース
        lines = response.text.strip().split("\n")
        data = [line.split(",") for line in lines]
        data = [[float(value) if value != "e" else 0 for value in line] for line in data]
        res = {}
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                res[(i, j)] = value

        # Redisにキャッシュを保存（キーを "i_j" 文字列に変換）
        json_data = {f"{i}_{j}": val for (i, j), val in res.items()}
        cache_set_json(cache_key, json_data)

        return res
    except requests.exceptions.RequestException:
        return None


def calc_delta_x(z: int) -> float:
    """ズームレベルzにおける1ピクセルの経度差"""
    return 360 / (2**z * 256)


def calc_delta_y(z: int, lat: float) -> float:
    """ズームレベルzにおける1ピクセルの緯度差"""
    rad = math.radians(lat)
    return 360 * math.cos(rad) / (2**z * 256)


def x_from_lon(lon_deg: float, z: int) -> int:
    """
    経度からタイルのx座標を計算

    Args:
        lon_deg: 経度（度）
        z: ズームレベル

    Returns:
        int: タイルのx座標
    """
    val = (lon_deg + 180) / 360
    return math.floor(val * (2**z))


def y_from_lat(lat_deg: float, z: int) -> int:
    """
    緯度からタイルのy座標を計算

    Args:
        lat_deg: 緯度（度）
        z: ズームレベル

    Returns:
        int: タイルのy座標
    """
    rad = math.radians(lat_deg)
    val = 1 - (math.log(math.tan(rad) + 1 / math.cos(rad)) / math.pi)
    return math.floor(val * (2 ** (z - 1)))


def lon_from_x(x: int, z: int) -> float:
    """
    タイルのx座標から経度を計算

    Args:
        x: タイルのx座標
        z: ズームレベル

    Returns:
        float: 経度（度）
    """
    return (x / (2**z)) * 360 - 180


def lat_from_y(y: int, z: int) -> float:
    """
    タイルのy座標から緯度を計算

    Args:
        y: タイルのy座標
        z: ズームレベル

    Returns:
        float: 緯度（度）
    """
    n = math.pi * (1 - 2 * y / (2**z))
    return math.degrees(math.atan(math.sinh(n)))


def fetch_all_dem_data_from_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    z: int = DEFAULT_ZOOM,
) -> dict:
    """
    指定された経度緯度の範囲のDEMデータを取得

    Args:
        min_lon: 最小経度
        min_lat: 最小緯度
        max_lon: 最大経度
        max_lat: 最大緯度
        z: ズームレベル（デフォルト: 14）

    Returns:
        dict: (x, y) -> {(i, j) -> elevation} のマッピング
    """
    x_min = int(x_from_lon(min_lon, z))
    y_min = int(y_from_lat(max_lat, z))
    x_max = math.ceil(x_from_lon(max_lon, z))
    y_max = math.ceil(y_from_lat(min_lat, z))

    dem_data = {}
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            data = fetch_dem_data(z, x, y)
            if data:
                dem_data[(x, y)] = data

    return dem_data


def get_nearest_elevation(lat: float, lon: float, dem_data: dict, z: int = DEFAULT_ZOOM) -> float:
    """
    指定した座標に最も近い標高データを取得

    Args:
        lat: 緯度
        lon: 経度
        dem_data: DEMデータ
        z: ズームレベル

    Returns:
        float: 標高（メートル）
    """
    base_x = int(x_from_lon(lon, z))
    base_y = math.ceil(y_from_lat(lat, z))

    if (base_x, base_y) in dem_data:
        data = dem_data[(base_x, base_y)]
        x_diff = lon - lon_from_x(base_x, z)
        y_diff = lat_from_y(base_y, z) - lat
        delta_x = calc_delta_x(z)
        delta_y = calc_delta_y(z, lat)
        i = int(x_diff / delta_x)
        j = int(y_diff / delta_y)

        if 0 <= i < 256 and 0 <= j < 256:
            return data.get((j, i), 0)

    return 0
