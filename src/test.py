import requests
import json

def statcan_get_metadata(pid: int):
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
    payload = [{"productId": pid}]
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    r_json = r.json()
    metadata = {}
    if r_json[0]["status"] == "SUCCESS":
        for field in ["productId", "cansimId", "cubeTitleEn", "cubeStartDate", "cubeEndDate"]:
            metadata[field] = r_json[0]["object"][field]

        metadata["dimension"] = []
        for d in r_json[0]["object"]["dimension"]:
            dim = {d_field: d[d_field] for d_field in ["dimensionNameEn", "dimensionPositionId"]}
            dim["member"] = []
            for m in d["member"]:
                mem = {m_field: m[m_field] for m_field in ["memberId", "parentMemberId", "memberNameEn", "geoLevel", "vintage"]}
                dim["member"].append(mem)
            metadata["dimension"].append(dim)
            
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
    
    metadata = statcan_get_metadata(pid=cpi_pid)
    with open(f"data/{cpi_pid}_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    
    # for d in metadata["dimension"]:
    #     print(d["dimensionNameEn"])
    #     mems = [(m["memberId"], m["parentMemberId"], m["memberNameEn"]) for m in d["member"]]
    #     print(mems)

    # statcan_get_data(pid=18100004, coordinate="2.2.0.0.0.0.0.0.0.0", periods=12)


if __name__ == "__main__":
    main()
