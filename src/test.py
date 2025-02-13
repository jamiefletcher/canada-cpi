import requests


def statcan_get_metadata(pid: int):
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
    payload = [{"productId": pid}]
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    r_json = r.json()
    metadata = {}
    if r_json[0]["status"] == "SUCCESS":
        for field in ["productId", "cansimId", "cubeTitleEn", "cubeStartDate", "cubeEndDate", "dimension"]:
            metadata[field] = r_json[0]["object"][field]
    return metadata


def main():
    metadata = statcan_get_metadata(pid=18100004)
    for dim in metadata["dimension"]:
        print(dim["dimensionNameEn"], "# members:", len(dim["member"]))
        # for member in dim["member"]:
        #     print("  ", member["memberId"], member["memberNameEn"])


if __name__ == "__main__":
    main()
