import requests
import json


def statcan_get_metadata(pid: int):
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
    payload = [{"productId": pid}]
    response_json = statcan_get(url, payload)
    return _process_metadata(response_json)


def statcan_get_data(pid: int, coordinate: str, periods: int):
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromCubePidCoordAndLatestNPeriods"
    payload = [{"productId": pid, "coordinate": coordinate, "latestN": periods}]
    response_json = statcan_get(url, payload)
    return _process_data(response_json)


def statcan_get(url: str, payload):
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    r_json = r.json()    
    if r_json[0]["status"] != "SUCCESS":
        raise RuntimeError("API request failed", r_json)
    return r_json[0]["object"]


def _process_data(r_json: dict):
    data = {"values": []}
    for field in ["productId", "coordinate", "vectorId"]:
        data[field] = r_json[field]
    for dp in r_json["vectorDataPoint"]:
        data["values"].append((dp["refPer"], dp["value"]))
    return data


def _process_metadata(r_json: dict):
    metadata = {}
    for field in ["productId", "cansimId", "cubeTitleEn", "cubeStartDate", "cubeEndDate"]:
        metadata[field] = r_json[field]

    metadata["dimension"] = {}
    for d in r_json["dimension"]:
        dim_id = int(d["dimensionPositionId"])
        dim_name = d["dimensionNameEn"]
        members = {}
        for m in d["member"]:
            m_id = int(m["memberId"])
            if m_id not in members:
                members[m_id] = {"children" : []}
            members[m_id].update({"name" : m["memberNameEn"]})
            parent_id = int(m["parentMemberId"]) if m["parentMemberId"] else None
            if parent_id:
                if parent_id not in members:
                    members[parent_id] = {"children" : []}
                members[parent_id]["children"].append(m_id)
        metadata["dimension"][dim_id] = {
            "name" : dim_name, 
            "members" : members
        }
    return metadata


def main():
    cpi_pid = 18100004
    metadata_file = f"data/{cpi_pid}_metadata.json"
    data_file = f"data/{cpi_pid}_data.json"
    
    metadata = statcan_get_metadata(cpi_pid)
    # with open(metadata_file, "w") as f:
    #     json.dump(metadata, f, indent=4, ensure_ascii=False)

    table_name = metadata["cubeTitleEn"]
    geography = metadata["dimension"][1]["members"]
    geo_map = {geo_id: geo["name"] for geo_id, geo in geography.items()}
    print(geo_map)

    for geo_id, geo in geography.items():
        coord = f"{geo_id}.2.0.0.0.0.0.0.0.0"
        data = statcan_get_data(pid=cpi_pid, coordinate=coord, periods=12)
        data["tableName"] = table_name
        data["geography"] = geo["name"]
        with open(f"data/{cpi_pid}_geo-{geo_id}_data.json", "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    products = metadata["dimension"][2]["members"]
    cpi_root = min(products.keys())
    prod_map = {prod_id: products[prod_id]["name"] for prod_id in products[cpi_root]["children"]}
    # print(prod_map)
    

    # data = statcan_get_data(pid=cpi_pid, coordinate="2.2.0.0.0.0.0.0.0.0", periods=12)
    # with open(data_file, "w") as f:
    #     json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
