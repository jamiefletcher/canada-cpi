import requests
import json


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
    members = {}
    for member in json_mems:
        m_id = int(member["memberId"])
        parent_id = int(member["parentMemberId"]) if member["parentMemberId"] else None
        if m_id not in members:
            members[m_id] = {"children": []}
        members[m_id]["name"] = member["memberNameEn"]
        if parent_id:
            if parent_id not in members:
                members[parent_id] = {"children": []}
            members[parent_id]["children"].append(m_id)
    return members


def main():
    cpi_table_id = 18100004

    metadata = statcan_get_metadata(cpi_table_id)
    metadata_file = f"data/{cpi_table_id}_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    geography = metadata["dimension"][0]["members"]
    category = metadata["dimension"][1]["members"]
    cat_root = min(category.keys())
    cat_ids = [cat_root] + category[cat_root]["children"]

    for geo_id, geo in geography.items():
        dataset = {
            "tableName": metadata["cubeTitleEn"],
            "tableId": cpi_table_id,
            "geography": geo["name"],
            "data": [],
        }
        for c_id in cat_ids:
            cat = category[c_id]
            coord = f"{geo_id}.{c_id}.0.0.0.0.0.0.0.0"
            try:
                data = statcan_get_data(pid=cpi_table_id, coordinate=coord, periods=12)
            except RuntimeError as err:
                print(coord, err)
            else:
                data["category"] = cat["name"]
                dataset["data"].append(data)
        with open(f"data/{cpi_table_id}-{geo_id}_data.json", "w") as f:
            json.dump(dataset, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
