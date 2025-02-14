import requests
import json

def statcan_get_metadata(pid: int, save_file = ""):
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
    payload = [{"productId": pid}]
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    r_json = r.json()    
    if r_json[0]["status"] == "SUCCESS":
        metadata = _process_metadata(r_json)
    if save_file:
        with open(save_file, "w") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
    return metadata

def _process_metadata(r_json: dict):
    metadata = {}
    for field in ["productId", "cansimId", "cubeTitleEn", "cubeStartDate", "cubeEndDate"]:
        metadata[field] = r_json[0]["object"][field]

    metadata["dimension"] = {}
    for d in r_json[0]["object"]["dimension"]:
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

def statcan_get_data(pid: int, coordinate: str, periods: int):
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromCubePidCoordAndLatestNPeriods"
    payload = [{"productId": pid, "coordinate": coordinate, "latestN": periods}]
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    r_json = r.json()
    print(r_json)


def main():
    cpi_pid = 18100004
    
    metadata = statcan_get_metadata(
        pid=cpi_pid, save_file=f"data/{cpi_pid}_metadata.json"
    )

    print(metadata)

    
    # for d in metadata["dimension"]:
    #     print(d["dimensionNameEn"])
    #     mems = [(m["memberId"], m["parentMemberId"], m["memberNameEn"]) for m in d["member"]]
    #     print(mems)

    # statcan_get_data(pid=18100004, coordinate="2.2.0.0.0.0.0.0.0.0", periods=12)


if __name__ == "__main__":
    main()
