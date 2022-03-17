from src.helper.aec import AEC
from src.helper.general import General
from src.model.candidate import Candidate
from src.model.combination import Combination
from src.model.election import Election
from src.model.electorate import Electorate
from src.model.note import Note
from src.model.party import Party


class AuAecCandidatesV1:
    """Australia Electoral Commission candidates list (v1)."""

    def __init__(self, general: General, aec: AEC):
        self._general = general
        self._aec = aec

    def populate(
        self, original_data: dict, combination: Combination, election: Election
    ) -> None:
        """Populate the Combination with result data."""

        cat = Note.get_category_raw_info()
        senate = self._aec.get_assembly_senate(combination)
        house_reps = self._aec.get_assembly_house_reps(combination)
        ind_title = self._aec.get_party_independent_title()

        rows = original_data.get("2019federalelection-all-candidates-nat-17-05.csv")

        for row in rows:
            # nom_ty = row.get("nom_ty", "").strip()
            state_ab = row.get("state_ab", "").strip()
            div_nm = row.get("div_nm", "").strip()
            ticket = row.get("ticket", "").strip()
            ballot_position = row.get("ballot_position", "").strip()
            name_last = row.get("surname", "").strip()
            name_first = row.get("ballot_given_nm", "").strip()
            party_ballot_nm = row.get("party_ballot_nm", "").strip() or ind_title
            occupation = row.get("occupation", "").strip()

            address_1 = row.get("address_1", "").strip()
            address_2 = row.get("address_2", "").strip()
            postcode = row.get("postcode", "").strip()
            suburb = row.get("suburb", "").strip()
            address_state_ab = row.get("address_state_ab", "").strip()
            postal_address_1 = row.get("postal_address_1", "").strip()
            postal_address_2 = row.get("postal_address_2", "").strip()
            postal_suburb = row.get("postal_suburb", "").strip()
            postal_postcode = row.get("postal_postcode", "").strip()
            postal_state_ab = row.get("postal_state_ab", "").strip()

            location_address = [
                address_1,
                address_2,
                suburb,
                postcode,
                address_state_ab,
            ]
            location_address = ", ".join([i for i in location_address if i])

            post_address = [
                postal_address_1,
                postal_address_2,
                postal_suburb,
                postal_postcode,
                postal_state_ab,
            ]
            post_address = ", ".join([i for i in post_address if i])

            contact_work_ph = row.get("contact_work_ph", "").strip()
            contact_home_ph = row.get("contact_home_ph", "").strip()
            contact_fax = row.get("contact_fax", "").strip()
            contact_mobile_no = row.get("contact_mobile_no", "").strip()
            contact_email = row.get("contact_email", "").strip()

            candidate_notes = [
                Note(display="state short name", content=state_ab, category=cat),
                Note(display="occupation", content=occupation, category=cat),
                Note(display="work phone", content=contact_work_ph, category=cat),
                Note(display="home phone", content=contact_home_ph, category=cat),
                Note(display="fax", content=contact_fax, category=cat),
                Note(display="mobile phone", content=contact_mobile_no, category=cat),
                Note(display="email", content=contact_email, category=cat),
                Note(display="location", content=location_address, category=cat),
                Note(display="post", content=post_address, category=cat),
            ]
            candidate_notes = [n for n in candidate_notes if n.content]

            party = Party(
                code=self._general.party_code(election.code, party_ballot_nm),
                short_name="",
                title=party_ballot_nm,
                alt_titles=[],
                category="",
                notes=[],
                election_code=election.code,
                candidate_codes=[],
            )

            if div_nm:
                assembly = house_reps
                electorate = Electorate(
                    code=self._general.electorate_code(house_reps.code, div_nm),
                    title=div_nm,
                    ballot_codes=[],
                    notes=[],
                    election_code=election.code,
                    assembly_code=house_reps.code,
                    candidate_codes=[],
                )
            else:
                assembly = senate
                electorate = Electorate(
                    code=self._general.electorate_code(senate.code, state_ab),
                    title=state_ab,
                    ballot_codes=[],
                    notes=[],
                    election_code=election.code,
                    assembly_code=senate.code,
                    candidate_codes=[],
                )

            candidate = Candidate(
                code=self._general.candidate_code(
                    assembly.code, electorate.title, name_first, name_last
                ),
                title=self._general.candidate_title(name_first, name_last),
                name_first=name_first,
                name_last=name_last,
                notes=candidate_notes,
                election_code=election.code,
                assembly_code=assembly.code,
                electorate_code=electorate.code,
                party_code=party.code,
                ballot_code=self._general.ballot_code(assembly.code, electorate.title),
                result_codes=[],
            )

            combination.add(party)
            combination.add(electorate)
            combination.add(candidate)

        a = 1


# 'txn_nm' = {set: 1} {'2019 Federal Election'}
# 'nom_ty' = {set: 2} {'S', 'H'}
# 'state_ab' = {set: 8} {'ACT', 'SA', 'WA', 'NSW', 'VIC', 'TAS', 'NT', 'QLD'}
# 'div_nm' = {set: 152} {'Wannon', '', 'Holt', 'Fadden', 'Grayndler', 'Braddon', 'Cook', 'Berowra', 'Wentworth', 'Groom', 'Perth', 'Sturt', 'Casey', 'Cowper', 'Fremantle', 'Barker', 'Makin', 'Stirling', 'Flinders', 'Dawson', 'Leichhardt', 'Monash', 'Lingiari', 'Rankin', 'Burt', 'Reid', 'Bean', 'Forde', 'Canning', 'Eden-Monaro', 'Wright', 'Whitlam', 'Spence', 'New England', 'Gilmore', 'Goldstein', 'Blaxland', 'Dickson', 'Fowler', 'Hume', 'Durack', 'Canberra', 'Brand', 'North Sydney', 'Lyons', 'McPherson', 'Griffith', 'Werriwa', 'Boothby', 'Gorton', 'Higgins', 'Bruce', 'Barton', 'Fenner', 'Corio', 'Pearce', 'Kooyong', 'Watson', 'Blair', 'Moncrieff', 'Dobell', 'Flynn', 'Kingston', 'Franklin', 'Swan', 'Hotham', 'Maranoa', 'Parkes', 'Page', 'La Trobe', 'Hughes', 'Bradfield', 'Macarthur', 'Bowman', 'Macnamara', 'Lalor', 'Fraser', 'Calwell', 'Hindmarsh', 'Richmond', 'Oxley', 'Curtin', 'Fisher', 'Moreton', 'Hinkler', 'Jagajaga', 'Parramatta', 'Chisholm', 'Menzies', 'Deakin', 'Petrie', "O'Connor", 'Capricornia', 'Hasl...
# 'ticket' = {set: 37} {'', 'L', 'A', 'H', 'M', 'Q', 'B', 'AF', 'N', 'X', 'P', 'V', 'D', 'W', 'J', 'AE', 'AA', 'U', 'T', 'F', 'UG', 'K', 'Y', 'AG', 'Z', 'G', 'AD', 'C', 'AI', 'R', 'AC', 'AB', 'I', 'E', 'O', 'S', 'AH'}
# 'ballot_position' = {set: 14} {'9', '5', '7', '10', '2', '13', '11', '8', '3', '14', '6', '12', '1', '4'}
# 'surname' = {set: 1212} {'FEENEY', 'SNOWDON', 'LAMBERT', 'HILLAM', 'BAYLES', 'ANNING', 'KHALIL', 'HAVILAND', 'DICKS', 'MANSON', 'FOSKEY', 'LARKIN', 'WISE', "O'DOWD", 'KATTER', 'SHERRY', 'JONES', 'GIRARD', 'BUDDE', 'DEJUN', 'SHAKESPEARE', 'RISHWORTH', 'TURTON', 'RIGONI', 'KILLIN', 'HOWARTH', 'KLOOT', 'HALLIWELL', 'FRASER-ADAMS', 'PETERSON', 'VEITCH', 'BURNUM BURNUM', 'MYERS', 'TSANGARIS', 'BURGOYNE', 'CAREW-HOPKINS', 'PAULL', 'STURGEON', 'HOULT', 'DAVIS', "O'NEILL", 'WALSH', 'WILLIAMSON', 'CHEHOFF', 'NERO', 'PERSSON', 'HASLER', 'TAAFFE', 'BEAZLEY', 'COSTA', 'STRETTON', 'MUNDINE', 'FRANKLIN', 'HORTON', 'ROMANO', 'JEFFRESON', 'FRENCH', 'MULLINGS', 'BOWEN', 'CHANDLER-MATHER', 'SPAULDING', 'PTOLEMY', 'HIESLER', 'HOLLO', 'ANDREWS', 'EARLEY', 'PERRETT', 'YORK', 'HARPLEY-CARR', "O'BRIEN", 'HALL', 'KARANDREWS', 'YU', 'TABER', 'FOX', 'FAULKNER', 'HANNA', 'HINKLEY', 'McROBERT', 'CHAWLA', 'Du PREEZ', 'FARUQI', 'REED', 'ADDINK', 'KIRK', 'LEBRASSE', 'BOSI', 'KANGAS', 'SHERSON', 'PURCELL', 'WILDE', 'SCHUBACK', 'HASSELL', 'O...
# 'ballot_given_nm' = {set: 808} {'Matthew', 'Kimbra Louise', 'Gabrielle', 'Reade', 'Nicholas', 'Emily', 'Helen Lucy', 'Sinim', 'Susan', 'Sahil', 'Nicole', 'Frank', 'Sophie', 'Gregory Francis', 'Alicia', 'Nick', 'B.J.', 'Gregory John', 'Bob', 'Tania', 'Keith', 'Richelle', 'Simon Alan', 'Hussein', 'Alexander David', 'Christopher Ronald', 'Grahame', 'Sharyn', 'Nita', 'Emmeline', 'Joseph Oscar', 'Julie', 'Lachlan Andrew', 'Belinda', 'Marion', 'Wylie', 'Nola', 'Guy', 'Thomas', 'Sheila', 'Sylvie', 'Bruce', 'Ted', 'Julia', 'Amanda', 'Blake', 'Ross Thomas', 'Asher Joseph', 'Ellen', 'Virginia Anne', 'Patsy', 'Sonny', 'Morgan', 'Huw Mostyn', 'Pamela', 'Nikhil', 'Dennis', 'Kamala', 'Cameron', 'Sonia', 'Esther', 'Bryan', 'Michael John', 'Rohan', 'Brent John', 'Jillian', 'Les', 'Dustin', 'Beverley T.', 'Jasmine', 'Elizabeth', 'Perry', 'Karagh-Mae', 'Martin', 'Katie', 'Rod', 'Natasha', 'Helen', 'Garry', 'Dan', 'Terrance', 'Kevin Francis', 'Anika', 'Lyn', 'Crystal', 'Kenneth Gordon', 'Shayne Kenneth', 'Wesley Jerome', 'Nicholas And...
# 'party_ballot_nm' = {set: 64} {'', 'Reason Australia', 'VOTEFLUX.ORG | Upgrade Democracy!', 'Sustainable Australia', 'Australian Labor Party', 'Labour DLP', 'Australian Conservatives', 'Liberal National Party of Queensland', 'The Greens (VIC)', 'Help End Marijuana Prohibition (HEMP) Party', 'Democratic Labour Party', 'Health Australia Party', "FRASER ANNING'S CONSERVATIVE NATIONAL PARTY", 'The Australian Mental Health Party', 'Child Protection Party', 'Republican Party of Australia', "Australian People's Party", 'Independents For Climate Action Now', 'Australian Progressives', 'Jacqui Lambie Network', 'Liberal Democrats', 'Australia First Party', 'Australian Christians', 'Victorian Socialists', 'The Greens (WA)', 'Australian Workers Party', 'Rise Up Australia Party', 'National Party', "The Women's Party", 'The Small Business Party', 'Secular Party of Australia', 'Citizens Electoral Council', 'WESTERN AUSTRALIA PARTY', 'Shooters, Fishers and Farmers', 'Centre Alliance', 'Science Party', 'Christian Democratic Party (...
# 'occupation' = {set: 756} {'Member for Cook', 'Retired Engineer', 'Policy Officer', 'Retired Police Officer', 'Tradesperon', 'Sales Representative', 'Financial Adviser', 'Disability Support Worker', 'Magazine Director', 'Emeritus Professor', 'Self Employed/Music Teacher', 'Musician', 'Hospitality', 'Candidate', 'Airline Scheduler', 'Plumber', 'Tourism', 'High Performance Driver Trainer', 'Bookkeeper', 'Project Manager', 'Disability Support Pensioner', 'Small Business Ownr (Heavy Trns)', 'Senator for Tasmania', 'Ecologist', 'Small Business Owner', 'Learning Designer', 'Senator of Queensland', 'Qld State Secretary, CEC', 'Neurosurgeon', 'Trainer', 'Media Producer', 'Chief Of Staff', 'Retired Minister', 'Business', 'Client Service Administrator', 'Federal MP', 'Acting Talent Manager', 'Research Scientist', 'Builder-Managing Director', 'Communications Consultant', 'Cultural Advisor', 'IT Cyber Fraud Consultant', 'General Practitioner', 'Sales Manager', 'Health Consultant', 'Warehouse Team Member', 'Mariner', 'Profe...
# 'address_1' = {set: 101} {'', '68 Rowsphorn Rd', '8 Clifford Ave', '36 Herschel St', '38/43 Wickham St', '1093 Upper Logan Rd', '2658 Wickepin-Pingelly Road', 'Tumblegum', '34 Magazine Dr', '23 Hakea Rd', '10 Albert La', '13 Atley St', '19 Maquire Way', '1/241 Belmore Rd', '407 Hickmans Rd', '3 Wellington Pde', '48 Cameron St', '410 Hurse Rd', '52 Jeffries Rd', '61 George St', '87 Maryborough St', '1 Kenman Rd', '9/325 Peats Ferry Rd', '191 Walters Rd', '3388a Deakin Ave', '2 Gallipoli St', '1927 Melba Hwy', '20 Bridgwood Rd', '725 Princes Hwy', '89 Ormeau Ridge Rd', "272 O'Hea St", '20/2 Doyalson Pl', '1 Valentia St', '138 Gurwood St', '12 Lowanna Way', 'Lot 304', '18 Kurrajong St', '14 Sunset Ave', '3 Dow St', '2 Morgan St', '1 Carter Rd', '63 Bangalay Dr', '28 Templeton St', '25 Tollington Park Rd', '2/130 Head St', '6 Patricia Ct', '2964 Hundred Line Rd', '51 Cullen St', '7 Pipping Way', '299 Lapoinya Rd', '3/34 Oliva St', '30 Schofield St', '9/26 Tintern Rd', '220/158 Day St', '27 De Villiers Ave', '545 L...
# 'address_2' = {set: 2} {'', '16 Adina Rd'}
# 'postcode' = {set: 95} {'', '2135', '6084', '5098', '2340', '4815', '2110', '3381', '2216', '6532', '4208', '4350', '3584', '2640', '4721', '7140', '6152', '2747', '3775', '2000', '3127', '3677', '2120', '3754', '2210', '2570', '2077', '7300', '2010', '6111', '2148', '7250', '3350', '4871', '2087', '2650', '6316', '3051', '2067', '5290', '3500', '3044', '6162', '3205', '3824', '4670', '3340', '0822', '2044', '2680', '2350', '3666', '4879', '3040', '2565', '6076', '5633', '3188', '4287', '6102', '6308', '6149', '2478', '4209', '4740', '2745', '2444', '4570', '4280', '2767', '6707', '6004', '4212', '6018', '6395', '7030', '7325', '5068', '5008', '0810', '2480', '5112', '3825', '7253', '2131', '4673', '3181', '6230', '5267', '5223', '3186', '3460', '2607', '6015', '6148'}
# 'suburb' = {set: 98} {'', 'CHATSWOOD', 'DOONSIDE', 'WHITE GUM VALLEY', 'SPRING FARM', 'NEWINGTON', 'NEW NORFOLK', 'GRIFFITH', 'WALKERVALE', 'WANGARATTA', 'MOUNT BARNEY', 'TINTENBAR', 'WATERLOO', 'MOORE CREEK', 'ALAWA', 'EAST PINGELLY', 'WALKLEY HEIGHTS', 'CITY BEACH', 'PALM COVE', 'TEMPE', 'INGLEBURN', 'BULLSBROOK', 'THORNLEIGH', 'ASQUITH', 'DALYELLUP', 'FARRER', 'PORT MACQUARIE', 'LAKE BOGA', 'WOOLWICH', 'LOCK', 'HAMPTON EAST', 'ASHFIELD', 'SURREY HILLS', 'KELMSCOTT', 'WERRINGTON DOWNS', 'ROCKDALE', 'SYDNEY', 'LUBECK', 'WOODLANDS', 'KEITH', 'INVERGOWRIE', 'DEVON PARK', 'SURRY HILLS', 'DEVON HILLS', 'RICHMOND', 'TRAVESTON', 'WAGGA WAGGA', 'WESTWOOD', 'MANNING', 'KILLARNEY HEIGHTS', 'BUNDABERG NORTH', 'ROCKVILLE', 'PASCOE VALE SOUTH', 'MOUNT GAMBIER', 'STRATHFIELD', 'EAST PERTH', 'GEORGE TOWN', 'LAPOINYA', 'LAKELAND', 'DIXONS CREEK', 'WURRUMIYANGA', 'CLERMONT', 'NORTH MELBOURNE', 'SEDDON', 'ORMEAU HILLS', 'ALBURY', 'RIVERSIDE', 'ST JAMES', 'SYDENHAM', 'BULL CREEK', 'RIVERWOOD', 'WILLOW VALE', 'MILDURA', 'LE...
# 'address_state_ab' = {set: 9} {'', 'ACT', 'SA', 'WA', 'NSW', 'VIC', 'TAS', 'NT', 'QLD'}
# 'contact_work_ph' = {set: 228} {'', '08 9328 7222', '0472 914 541', '0413 248 193', '08 8265 3100', '08 9477 5411', '03 9781 2333', '0409 899 006', '0438 527 200', '07 4662 2715', '08 9277 1502', '07 5500 5919', '0408 034 392', '08 8586 6600', '13 0062 7545', '0411 393 503', '0490 134 827', '0419 906 393', '0448 817 163', '02 6341 1571', '08 8241 0190', '0422 403 571', '0450 068 960', '03 9674 7381', '03 9354 0544', '03 9690 2201', '03 9882 3677', '0437 580 726', '08 9272 3411', '03 9887 3890', '03 6423 1453', '03 9768 9164', '02 9633 3255', '08 8941 0003', '02 9349 6007', '07 4152 0744', '02 4991 1022', '02 9750 9088', '02 6621 4044', '08 9300 2244', '0487 010 691', '0432 682 028', '02 4326 0828', '0438 275 168', '03 7015 3054', '03 6234 5255', '07 3881 3710', '07 4922 6604', '03 5977 9082', '03 6263 3721', '03 6229 4444', '02 4947 9546', '13 0036 4232', '07 4632 4144', '0459 958 216', '08 8186 2588', '03 5243 1444', '0490 375 409', '0466 028 220', '08 8381 5352', '03 9557 4644', '0497 372 484', '07 4061 6066', '08...
# 'contact_home_ph' = {set: 43} {'', '08 8265 3100', '0459 958 216', '07 5484 6419', '08 8186 2588', '0438 371 398', '0414 015 677', '0421 175 785', '08 8269 6022', '08 8381 5352', '03 5633 1109', '08 8554 5260', '02 6341 1571', '02 9559 2070', '08 8241 0190', '0439 295 698', '0422 403 571', '08 8531 3433', '0450 068 960', '07 3232 1254', '0422 122 690', '02 6775 2588', '08 8418 6700', '0448 720 433', '02 6655 4437', '08 6162 0438', '08 8284 2422', '07 4903 1945', '0467 365 964', '08 9831 1038', '0490 555 292', '08 8376 9000', '08 9409 4517', '0467 610 761', '02 9519 4770', '07 4566 0696', '0406 390 058', '0429 034 542', '08 9446 7136', '0400 372 947', '13 0041 5449', '07 4060 2185', '0414 566 342'}
# 'postal_address_1' = {set: 335} {'', 'PO BOX 1505', 'PO Box 156', '407 Parramatta Rd', 'PO Box 3082', 'PO Box 8177', 'PO Box 264', 'PO Box 20177', 'P O Box 376', 'PO Box 888', 'PO Box 2038', 'PO Box 3412', 'PO BOX 8134', 'PO Box 4128', 'PO Box 153', '45a Steele St', 'PO Box 40', 'PO Box 2221', 'GPO Box 35', 'PO BOX 299', 'PO Box 4117', 'PO Box 6004', 'Suite 124,', '23 Hakea Rd', 'PO Box 476', 'PO Box 342', 'PO Box 756', '13 Atley St', '427 Hunter St', 'PO Box 2185', 'PO Box 227', '52 Jeffries Rd', 'PO Box 266', 'PO Box 899', 'PO Box 501', 'PO Box 733', 'PO Box 2158', 'PO Box 2246', 'Rise Up Australia', '296 Brunswick St', '695 Burke Rd', 'PO Box 417', '1927 Melba Hwy', 'Shop 6', 'GPO Box 4589', 'GPO Box 32', 'GPO Box 1402', '3A/195 Colac Rd', '69 Clara St', 'Level 6, 40 City Rd', 'PO Box 901', 'PO Box 306', 'C/O PO BOX 413', 'PO Box 452', 'PO Box 4255', 'PO Box 649', 'Rise Up Australia Party', '138 Gurwood St', 'PO Box 1156', 'PO Box 618', 'PO Box 419 Sunnybank Plaza', 'PO Box 346', 'PO Box 628', 'PO Box 288', '6 Pat...
# 'postal_address_2' = {set: 10} {'', '16 Adina Rd', 'PO Box 290', 'Singleton Plaza', 'Tintenbar via', 'Riverview Rd', '30 Star Cres', 'Queen Victoria Building', 'Innaloo Post Shop', '336 Murnong St'}
# 'postal_suburb' = {set: 303} {'', 'WAURN PONDS', 'WORRIGEE', 'CHATSWOOD', 'LAUNCESTON', 'NEWCASTLE', 'CLEVELAND', 'SPRING FARM', 'CANNONVALE', 'BUDERIM', 'BELLINGEN', 'NEW NORFOLK', 'PALMWOODS', 'BENTLEIGH', 'HORSHAM', 'PUNCHBOWL', 'ROXBURGH PARK', 'GRIFFITH', 'MURTOA', 'CAMBERWELL', 'WALKERVALE', 'CROWS NEST PRIVATE BOXES', 'BUDDINA', 'PROSPECT', 'CRAIGIEBURN', 'MOUNT BARNEY', 'SUBIACO', 'MAREEBA', 'SUCCESS', 'NOBBY BEACH', 'WARRAGUL', 'VARSITY LAKES', 'MORPHETT VALE', 'WHITTLESEA', 'MELBOURNE GPO', 'CHARTERS TOWERS', 'WATERLOO', 'SUNNYBANK HILLS', 'MAPLETON', 'HELENSVALE TOWN CENTRE', 'KINGSCOTE', 'MOORE CREEK', 'WOODANILLING', 'ALAWA', 'COBURG', 'ROCKHAMPTON', 'EAST PINGELLY', "O'CONNOR", 'BLACKWOOD', 'CROYDON', 'SOUTHBANK', 'BURPENGARY', 'SUNBURY', 'WALKLEY HEIGHTS', 'GISBORNE', 'TUGGERAH', 'CITY BEACH', 'RENMARK', 'PALM COVE', 'BELROSE', 'CAPEL SOUND', 'CASULA MALL', 'NORTH RYDE', 'TEMPE', 'BULLSBROOK', 'THORNLEIGH', 'ASQUITH', 'MILDURA SOUTH', 'FARRER', 'PORT MACQUARIE', 'MARYBOROUGH', 'LAKE BOGA', 'FITZROY ...
# 'postal_postcode' = {set: 280} {'', '6253', '6084', '5098', '2340', '4815', '7330', '4213', '3178', '2110', '2216', '2312', '0838', '2578', '2440', '0847', '4170', '4370', '4208', '6532', '4650', '4350', '3584', '6743', '3820', '2640', '2007', '4019', '2454', '5162', '4802', '4721', '6244', '2912', '4621', '1470', '1585', '4500', '7140', '5252', '6872', '6152', '4115', '3429', '3300', '2090', '4151', '4218', '4305', '2747', '5253', '3775', '6964', '4207', '3127', '3757', '6911', '4870', '3122', '2120', '3754', '2210', '4575', '4012', '2570', '4078', '2540', '2077', '7300', '1765', '2010', '6946', '2085', '5092', '7051', '5114', '6111', '3803', '2290', '5038', '7250', '2148', '2515', '1230', '2280', '4871', '6014', '6010', '3124', '3912', '4860', '2357', '6979', '4109', '4819', '4880', '3161', '6227', '4114', '6959'...
# 'contact_fax' = {set: 42} {'', '07 3839 4649', '03 5243 1666', '03 9354 0166', '03 6229 4100', '03 9848 2741', '08 8418 6701', '02 9349 8089', '08 8988 1723', '02 4926 1895', '07 3208 8744', '02 9331 2349', '02 9559 2070', '03 9887 3893', '02 9806 9642', '08 8531 2124', '08 8633 1749', '07 3879 6441', '07 3881 3755', '08 8376 7888', '02 4991 2322', '03 9768 9883', '03 9882 3773', '07 3201 5311', '02 4620 4414', '03 9727 0833', '08 8186 2688', '03 5979 3034', '02 6277 5782', '02 9832 2641', '07 5432 3188', '08 9463 6313', '08 8265 3900', '07 4061 6566', '03 5572 1141', '08 8941 0071', '03 9012 4549', '07 3899 5755', '03 5623 2509', '08 8241 0198', '08 8205 1045', '08 8284 2433'}
# 'postal_state_ab' = {set: 9} {'', 'ACT', 'SA', 'WA', 'NSW', 'VIC', 'TAS', 'NT', 'QLD'}
# 'contact_mobile_no' = {set: 530} {'', '0407 524 466', '0421 161 347', '0456 523 153', '0420 715 459', '0437 197 871', '0438 482 272', '0438 494 087', '0481 111 498', '0418 411 229', '0438 528 404', '0438 045 817', '0439 452 419', '0404 204 080', '0437 965 920', '0417 684 349', '0497 814 158', '0403 997 891', '0432 807 946', '0438 320 265', '0439 446 619', '0431 233 747', '0437 829 897', '0437 799 546', '0466 805 369', '0432 338 474', '0438 902 266', '0411 818 950', '0467 610 761', '0439 039 189', '0439 207 505', '0499 396 502', '0401 409 797', '0414 873 412', '0438 319 567', '0438 909 343', '0490 057 911', '0409 447 497', '0487 879 637', '0439 492 992', '0466 028 220', '0490 375 409', '0438 356 475', '0413 611 334', '0438 787 515', '0451 038 160', '0400 256 929', '0468 689 608', '0438 695 679', '0400 628 787', '0413 379 895', '0491 207 088', '0401 861 642', '0417 952 723', '0438 600 853', '0449 996 848', '0438 877 941', '0448 720 433', '0428 177 638', '0490 442 678', '0419 854 211', '0476 041 508', '0437 646 564', '04...
# 'contact_email' = {set: 1041} {'', 'james.williams@vic.greens.org.au', 'chris.buckman888@icloud.com', 'rebecca.byfield@aussieicon.com', 'matt.thistlethwaite.mp@aph.gov.au', 'matthew.mattowen.owen@gmail.com', 'louise.kingston@nationalswa.com', 'joeyroorankin@gmail.com', 'Paterson@unitedaustraliaparty.org.au', 'kingston@sa.greens.org.au', 'watson@nsw.greens.org.au', 'cowan@onenation.com.au', 'andrew.wilkie.mp@aph.gov.au', 'carolynthomson55@gmail.com', 'djhanna@optusnet.com.au', 'corinne.mulholland@queenslandlabor.org', 'debby.lo-dean@hotmail.com', 'eden-monaro@nswnationals.org.au', 'sara.joyce@pirateparty.org.au', 'gpautotech@outlook.com', 'bindi334@hotmail.com', 'Bruce@unitedaustraliaparty.org.au', 'vote.a.martin@gmail.com', 'christian.porter.mp@aph.gov.au', 'neil.barker@vic.greens.org.au', 'Nick.Champion.MP@aph.gov.au', 'Chifley@unitedaustraliaparty.org.au', 'darren.brollo.ajp@gmail.com', 'akavasilas@hotmail.com', 'brand@wa.greens.org.au', 'molyneux1@outlook.com', 'gilmore@nswnationals.org.au', 'miles@sa.nationals....
