import requests
import json
from collections import defaultdict


def statcan_get_metadata(pid: int):
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
    payload = [{"productId": pid}]
    response_json = statcan_post(url, payload)
    return _process_metadata(response_json)


def statcan_get_data(pid: int, coordinate: str, periods: int):
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromCubePidCoordAndLatestNPeriods"
    payload = [{"productId": pid, "coordinate": coordinate, "latestN": periods}]
    response_json = statcan_post(url, payload)
    return _process_data(response_json)


def statcan_post(url: str, payload):
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    r_json = r.json()
    if r_json[0]["status"] != "SUCCESS":
        raise RuntimeError("API request failed", r_json)
    return r_json[0]["object"]


def _process_data(r_json: dict):
    return {
        # "productId": r_json["productId"],
        "coordinate": r_json["coordinate"],
        "vectorId": r_json["vectorId"],
        "values": [dp["value"] for dp in r_json["vectorDataPoint"]],
        "periods": [dp["refPer"] for dp in r_json["vectorDataPoint"]],
    }


def _process_metadata(r_json: dict):
    return {
        "productId": r_json["productId"],
        "cansimId": r_json["cansimId"],
        "cubeTitleEn": r_json["cubeTitleEn"],
        "cubeStartDate": r_json["cubeStartDate"],
        "cubeEndDate": r_json["cubeEndDate"],
        "dimension": [
            {
                "position": int(dim["dimensionPositionId"]),
                "name": dim["dimensionNameEn"],
                "members": _members_map(dim["member"]),
            }
            for dim in r_json["dimension"]
        ],
    }


def _members_map(json_mems):
    members = defaultdict(lambda: {"children": []})
    for member in json_mems:
        m_id = int(member["memberId"])
        parent_id = int(member["parentMemberId"]) if member["parentMemberId"] else None
        members[m_id]["name"] = member["memberNameEn"]
        if parent_id:
            members[parent_id]["children"].append(m_id)
    return members


def _bfs(tree: dict, max_depth=2):
    root = min(tree.keys())
    ids = []
    current_level = [root]
    depth = 0
    while current_level and depth <= max_depth:
        next_level = []
        for node_id in current_level:
            node = tree[node_id]
            ids.append((depth, node_id))
            next_level.extend(node["children"])
        depth += 1
        current_level = next_level
    return ids


def main():
    cpi_table_id = 18100004
    time_periods = 13
    geo_depth = 1
    cpi_depth = 3

    metadata = statcan_get_metadata(cpi_table_id)
    metadata_file = f"data/{cpi_table_id}/metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    geography = metadata["dimension"][0]["members"]
    category = metadata["dimension"][1]["members"]

    for geo_level, geo_id in _bfs(geography, geo_depth):
        geo = geography[geo_id]
        geo_short_name = geo["name"].lower().replace(" ","_").split(",")[0]
        dataset = {
            "tableName": metadata["cubeTitleEn"],
            "tableId": cpi_table_id,
            "geography": geo["name"],
            "geoId": geo_id,
            "children": geo["children"],
            "level": geo_level,
            "data": [],
        }
        for cat_level, cat_id in _bfs(category, cpi_depth):
            cat = category[cat_id]
            coordinate = f"{geo_id}.{cat_id}.0.0.0.0.0.0.0.0"
            try:
                data = statcan_get_data(cpi_table_id, coordinate, time_periods)
            except RuntimeError as err:
                print(coordinate, err)
            else:
                data["category"] = cat["name"]
                data["catId"] = cat_id,
                data["children"] = cat["children"],
                data["level"] = cat_level
                dataset["data"].append(data)
        with open(f"data/{cpi_table_id}/{geo_short_name}.json", "w") as f:
            json.dump(dataset, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
