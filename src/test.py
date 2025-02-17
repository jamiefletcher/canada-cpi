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
        "productId": r_json["productId"],
        "coordinate": r_json["coordinate"],
        "vectorId": r_json["vectorId"],
        "values": [dp["value"] for dp in r_json["vectorDataPoint"]],
        "periods": [dp["refPer"] for dp in r_json["vectorDataPoint"]],
    }


def _process_metadata(r_json: dict):
    metadata = {}
    for field in [
        "productId",
        "cansimId",
        "cubeTitleEn",
        "cubeStartDate",
        "cubeEndDate",
    ]:
        metadata[field] = r_json[field]

    metadata["dimension"] = {}
    for d in r_json["dimension"]:
        dim_id = int(d["dimensionPositionId"])
        dim_name = d["dimensionNameEn"]
        members = {}
        for m in d["member"]:
            m_id = int(m["memberId"])
            if m_id not in members:
                members[m_id] = {"children": []}
            members[m_id].update({"name": m["memberNameEn"]})
            parent_id = int(m["parentMemberId"]) if m["parentMemberId"] else None
            if parent_id:
                if parent_id not in members:
                    members[parent_id] = {"children": []}
                members[parent_id]["children"].append(m_id)
        metadata["dimension"][dim_id] = {"name": dim_name, "members": members}
    return metadata


def main():
    cpi_table = 18100004

    metadata = statcan_get_metadata(cpi_table)
    metadata_file = f"data/{cpi_table}_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    table_name = metadata["cubeTitleEn"]
    geography = metadata["dimension"][1]["members"]
    products = metadata["dimension"][2]["members"]
    prod_root = min(products.keys())
    prod_ids = [prod_root] + products[prod_root]["children"]

    for geo_id, geo in geography.items():
        dd = []
        for prod_id in prod_ids:
            prod = products[prod_id]
            coord = f"{geo_id}.{prod_id}.0.0.0.0.0.0.0.0"
            try:
                data = statcan_get_data(pid=cpi_table, coordinate=coord, periods=12)
            except RuntimeError as err:
                print(coord, err)
            else:
                data["tableName"] = table_name
                data["geography"] = geo["name"]
                data["product"] = prod["name"]
                dd.append(data)
        with open(f"data/{cpi_table}-{geo_id}_data.json", "w") as f:
            json.dump(dd, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
