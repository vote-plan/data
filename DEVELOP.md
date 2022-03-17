# Development

There are three directories:

- `raw` contains the original data files in subdirectories
- `ready` contains the data fiels used by the web app
- `src` contains the Python source code used to process the raw data into ready data

## Data Structure

This data structure aims to store election information in a generic way.

The top-level is the `combination` model, which contains lists of all the other models.

- assembly: A chamber or house of a political institution.
- ballot: The definition for a ballot paper used in an election.
- candidate: One of the people running for a position in an assembly.
- election: An event held to elect one person for each seat in each assembly.
- electorate: People who live in this geographical area vote for candidates in one or more assemblies.
- party: A group of candidates in an election.
- results: One entry in the process of determining the candidate elected to a seat.

Each model has a code, which must be unique across *all models* in *all elections*.

Models refer to other models using the code.

## Data Sources

- At most 9 years old (currently 2022 - 2013)

### Australia

- Australian Bureau of Statistics [Regional population](https://www.abs.gov.au/statistics/people/population/regional-population)
    - file: `raw\shared\32180DS0003_2010-20.xls`
    - saved sheets into .csv or .tsv files

#### Federal Elections

- Australian Electoral Commission [results page](https://results.aec.gov.au/)
    - from media feed (Standard granularity, verbose feed, most recent)
    - from tally room page
        - house of reps:
            - National list of candidates
            - Political parties
            - Distribution of preferences by candidate by division
            - Enrolment by state
            - Enrolment by division
            - Informal votes by state
            - Informal votes by division
            - Turnout by state
            - Turnout by division
        - senate:
            - National list of candidates
            - Political parties
            - Senate distribution of preferences
            - Enrolment by state
            - Enrolment by division
            - Informal votes by state
            - Informal votes by division
            - Turnout by state
            - Turnout by division
            - Votes by state
            - Votes by division
    - federal elections
        - 2019: ftp://mediafeedarchive.aec.gov.au/24310   https://results.aec.gov.au/24310/Website/HouseDefault-24310.htm
            - aec-mediafeed-Standard-Verbose-24310-20190729153147.zip
        - 2016: ftp://mediafeedarchive.aec.gov.au/20499   https://results.aec.gov.au/20499/Website/HouseDefault-20499.htm
        - 2013: ftp://mediafeedarchive.aec.gov.au/17496   https://results.aec.gov.au/17496/Website/Default.htm
    - federal by-elections
        - 2020 Groom by-election: ftp://mediafeedarchive.aec.gov.au/25881   https://results.aec.gov.au/25881/Website/HouseDivisionPage-25881-164.htm
        - 2020 Eden-Monaro by-election: ftp://mediafeedarchive.aec.gov.au/25820  https://results.aec.gov.au/25820/Website/HouseDivisionPage-25820-117.htm
        - 2018 Wentworth by-election: ftp://mediafeedarchive.aec.gov.au/22844  https://results.aec.gov.au/22844/Website/HouseDivisionPage-22844-152.htm
        - 2018 Perth by-election: ftp://mediafeedarchive.aec.gov.au/22696  https://results.aec.gov.au/22696/Website/HouseDivisionPage-22696-245.htm
        - 2018 Mayo by-election: ftp://mediafeedarchive.aec.gov.au/22695  https://results.aec.gov.au/22695/Website/HouseDivisionPage-22695-188.htm
        - 2018 Longman by-election: ftp://mediafeedarchive.aec.gov.au/22694   https://results.aec.gov.au/22694/Website/HouseDivisionPage-22694-302.htm
        - 2018 Fremantle by-election: ftp://mediafeedarchive.aec.gov.au/22693   https://results.aec.gov.au/22693/Website/HouseDivisionPage-22693-240.htm
        - 2018 Braddon by-election: ftp://mediafeedarchive.aec.gov.au/22692   https://results.aec.gov.au/22692/Website/HouseDivisionPage-22692-193.htm
        - 2018 Batman by-election: ftp://mediafeedarchive.aec.gov.au/21751   https://results.aec.gov.au/21751/Website/HouseDivisionPage-21751-199.htm
        - 2017 Bennelong by-election: ftp://mediafeedarchive.aec.gov.au/21379   https://results.aec.gov.au/21379/Website/HouseDivisionPage-21379-105.htm
        - 2017 New England by-election: ftp://mediafeedarchive.aec.gov.au/21364   https://results.aec.gov.au/21364/Website/HouseDivisionPage-21364-135.htm
        - 2015 North Sydney by-election: ftp://mediafeedarchive.aec.gov.au/19402   https://results.aec.gov.au/19402/Website/Default.htm
        - 2015 Canning by-election: ftp://mediafeedarchive.aec.gov.au/18126   https://results.aec.gov.au/18126/Website/Default.htm
        - 2014 WA Senate election: ftp://mediafeedarchive.aec.gov.au/17875   https://results.aec.gov.au/17875/Website/Default.htm
        - 2014 Griffith by-election: ftp://mediafeedarchive.aec.gov.au/17552   https://results.aec.gov.au/17552/Website/Default.htm
