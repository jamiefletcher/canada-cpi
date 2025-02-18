# canada-cpi
The Consumer Price Index (CPI) is an indicator of changes in consumer prices experienced by Canadians. It is calculated monthly and compares the cost of a fixed basket of goods and services purchased by consumers. The index values are relative to a reference period (currently the year 2002) for which the CPI equals 100.

[Statistics Canada - Consumer Price Index (CPI)](https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&SDDS=2301)

## Accessing StatCan Data via REST API
StatCan provides a RESTful API called the Web Data Service that can be used to access their datasets. They supply a [detailed user guide](https://www.statcan.gc.ca/en/developers/wds/user-guide) but, in short, two identifiers are needed to access StatCan data via the API:
- A **product identification number** (PID) is an integer that uniquely identifies the table. This value is usually easy to find via the [StatCan website](https://www150.statcan.gc.ca/n1/en/type/data). For example, the PID for the CPI table is `18100004`.
- A **coordinate** is a string representing the dotted concatenation of the member ID values for each table dimension. Regardless of the number of actual table dimensions, the coordinate is always zero-padded out to 10 dimensions. For example, the CPI table has two dimensions `geography` and `product_group` (i.e. basket/CPI category) so the coordinate `23.3.0.0.0.0.0.0.0.0` corresponds to the *Food* basket `product_group=3` for *Alberta* `geography=23`.

### Procedure
1. Given `pid` identifying the table of interest, gather the full metadata for that table by making a POST request to the `https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata` endpoint with `[{"productId": pid}]` as the payload.
2. The metadata is verbose but we are interested in the `dimension` list object. For each dimension, take note of:
- `dimensionNameEn` and/or `dimensionNameFr`
- `dimensionPositionId` which specifies the dimension's index position within the coordinate
- `member` which contains the unique values for that dimension
3. Use the member and position information for each dimension to construct a valid coordinate for the data of interest. Next, make a POST request to the `https://www150.statcan.gc.ca/t1/wds/rest/getDataFromCubePidCoordAndLatestNPeriods` endpoint with `[{"productId": pid, "coordinate": coordinate, "latestN": periods}]`. This will return a timeseries for the most recent *N* `periods`. CPI is computed monthly, so setting `periods=12` gives 1 year of data.

## Details of CPI Dataset

