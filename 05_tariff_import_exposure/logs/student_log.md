# Student work log — Deniz Yaveroglu

_date | what you did | count | notes_

---

**2026-07-25 | Received the project tasks; cloned the repo but could not locate the “firms_to_verify.csv” file. | 60 mins | Reached out to Prof. Gao asking about the file**

---

**2026-07-26 | Read the working paper and studied assigned tasks, repo structure and data files. | 300 mins | Cloned repo**

---

**2026-07-27 | Started working on rules to apply on sample companies (used Apple in the absance of verified list) | 300 mins | notes below**

Reached out to Prof. Gao regarding the timing rule for the 10Ks. I considered the following scenarios:

- 10K for Fiscal Year Ending June 30, 2026 – This may be the most recent one available, but covers a period after the “liberation day” during when the company's sourcing strategy may have changed?
- 10K for Fiscal Year Ending June 30, 2025 – This covers the tariff announcement period, but the 10K was not public at the time the shock happened. So investors did not have this exact wording available to them when the tariff announcement happened.
- 10K for Fiscal Year Ending June 30, 2024 – This is the 10K that was publicly available when the tariff announcement happened, but may not cover any change in company strategy between July 2024 and April 2025.

---

**2026-07-28 | Prepared the abstract for the paper for ASSIP submission | 180 mins | —**

---

**2026-07-29 | Completed Task 2 | 120 mins | notes below**

Task 2 did not depend on list of firms.

Shared the abstract with Prof. Gao for his approval with a reminder to receive firms_to_verify.csv file to get started on Task 1

---

**2026-07-29 | Started to work on the presentation template | 300 mins | Focused on the slides that are not dependent on the firms to verify file**

---

**2026-07-30 | Downloaded all 10K and 20F files | 90 mins | notes below**

Received Prof. Gao's approval on the abstract and also received the firms_to_verify.csv file

Generated a code to get all the SEC url links to download the filings. Generated another code to double check that each file is the correct one

---

**2026-07-30 | Finished and coded: SKECHERS U S A INC (SKX) | 50 mins | notes below**

- Intensity High: filing says substantially all sales come from footwear made in foreign countries.
- Recorded Asia alongside China and Vietnam, because the filing says manufacturers are located primarily in Asia; country names not mentioned
- Every foreign site in the properties table seems to be a distribution center; none counted

---

**2026-07-30 | Finished and coded: MISSION PRODUCE INC (AVO) | 50 mins | notes below**

- Intensity High: no import share given, but the acreage table shows international avocado planted acreage
- UK and Canadian sites are distribution, excluded.

---

**2026-07-30 | Finished and coded: RESIDEO TECHNOLOGIES (REZI) | 40 mins | notes below**

- Goods type Both: it imports finished goods for resale and components for its own manufacturing
- Canada and the EU are named in its tariff sentence but not as places it buys from (not recorded as source countries)

---

**2026-07-30 | Finished and coded: SITEONE LANDSCAPE SUPPLY INC (SITE) | 20 mins | notes below**

- Intensity Low: the only foreign sourcing described is a single product line of imported stone.

---

**2026-07-30 | Finished and coded: COTY INC (COTY) | 50 mins | notes below**

- Reports by product line rather than geography, so there was no basis to exclude any foreign plant. All named countries counted.

---

**2026-07-30 | Finished and coded: INTERFACE INC (IFSIA) | 40 mins | notes below**

- its main supplier of vinyl tile has its plant in South Korea.

---

**2026-07-30 | Finished and coded: HAIN CELESTIAL GROUP INC (NOSH) | 40 mins | notes below**

- Tariff language 0 on direction: its only tariff risk is Canadian and EU duties on US food exports (the opposite exposure to an importer)
- Canadian plants counted, England/Germany/Austria plants excluded, using the filing's own North America vs International segment split.

---

**2026-07-30 | Finished and coded: CULLINAN THERAPEUTICS INC (CGEM) | 30 mins | notes below**

- China recorded because the filing states that it relies on third parties located there

---

**2026-07-30 | Finished and coded: RELAY THERAPEUTICS INC (RLAY) | 40 mins | notes below**

- No country recorded. Its BIOSECURE Act reference points at China, but the filing never says its CMOs are Chinese.

---

**2026-07-30 | Finished and coded: CME GROUP INC (CME) | 40 mins | notes below**

- Tariff language 0: the word appears once but in a generic forward-looking list not in the risk factors

---

**2026-07-31 | Finished and coded: STATE STREET CORP (STBK) | 60 mins | notes below**

- The word tariff never appears anywhere, but two trade-policy references citing US measures discouraging use of lower-cost jurisdictions would raise its cost base.

---

**2026-07-31 | Finished and coded: JANUS HENDERSON GROUP PLC (JHG) | 30 mins | notes below**

- No decisions- asset manager, no imports, no trade vocabulary anywhere in the filing.

---

**2026-07-31 | Finished and coded: GREENBRIER COS INC (THE) (GBX) | 40 mins | notes below**

- Europe was too vague but found Poland and Romania in the properties table.

---

**2026-07-31 | Finished and coded: XYLEM INC (XYL) | 60 mins | notes below**

- Austria, Switzerland and France are sales or administration only, not manufacturing.
- China, Mexico and Canada added; the sourcing sentence was in Item 1A

---

**2026-07-31 | Finished and coded: ALAMO GROUP INC (ALMO) | 40 mins | notes below**

- Named countries from the plant table.
- The properties table also lists an Australian plant that the summary sentence in Item 1 doesn't mention it

---

**2026-07-31 | Finished and coded: TIMKEN CO | 50 mins | notes below**

- Italy and Netherlands recorded from acquisition notes rather than the properties table, which names only China, India and Romania.
- Ticker blank in the source file; left as is

---

**2026-07-31 | Finished and coded: IMMUNOVANT INC (HSAC) | 40 mins | notes below**

- Dedicated risk factor about trade war disrupting its Asian manufacturing

---

**2026-07-31 | Finished and coded: METALLUS INC (TMST) | 40 mins | notes below**

- It is a domestic steel producer that tariffs protect. Its own filing says relaxing them would flood it with cheap imports.
- Tariff language 0: all three trade sentences are protective, none about its costs.
- Buys recycled scrap on the open market with no geography given
- Foreign property, plant and equipment of $0.4m against $522m domestic supports None decision on intensity

---

**2026-07-31 | Finished and coded: NOV INC (NOI) | 60 mins | notes below**

- Looked at the facility table plus the supply-chain sentence in Item 1A.

---

**2026-07-31 | Finished and coded: GREEN PLAINS INC (GPRE) | 30 mins | notes below**

- None despite a 10.76% industry score: corn is bought from local farmers for ten domestic plants.
- Tariff language 0: its tariff references seem to be about export retaliation and import competition

---

**2026-07-31 | Finished and coded: AMPHASTAR PHARMACEUTICLS INC (AMPH) | 30 mins | notes below**

- Kept Asia and EU alongside the named plants in China and France, because the filing says it has suppliers in those regions in addition to the two plants.

---

**2026-07-31 | Finished and coded: MARVELL TECHNOLOGY INC (MRVL) | 40 mins | notes below**

- Countries are subcontractor locations from Item 1. Its own foreign sites are all research and design facilities

---

**2026-07-31 | Finished and coded: WATERS CORP (WAT) | 50 mins | notes below**

- India added: the properties table marks Bangalore as manufacturing. Item 1 names only four countries.

---

**2026-07-31 | Finished and coded: PEPSICO INC | 60 mins | notes below**

- Its other foreign plants are assigned to foreign divisions so assumed they support local markets - kept them out
- Ticker blank in the source file; left as is.

---

**2026-08-01 | Finished and coded: PROCEPT BIOROBTCS CORP (PRCT) | 40 mins | notes below**

- Company says that it imports raw materials and components from foreign suppliers but does not name a country.
- Its UK and Netherlands mentions are logistics providers

---

**2026-08-01 | Finished and coded: WINGSTOP INC (WING) | 20 mins | notes below**

- No decisions (no trade vocabulary of any kind in the filing)

---

**2026-08-01 | Finished and coded: CINTAS CORP (CTAS) | 50 mins | notes below**

- It names foreign suppliers, calls global sourcing important to its financial performance, but never names a country.
- The properties table lists 479 facilities in 344 cities and gives no country either.

---

**2026-08-01 | Finished and coded: DUKE ENERGY CORP | 50 mins | notes below**

- A utility, so most of its 19 uses of tariff mean a regulated rate schedule. But more than half of them were about trade and mentioned in the risk factors, so it coded 1.
- Its 17.5% stake in a Saudi petrochemical joint venture is a passive investment, not sourcing
- Ticker blank in the source file; left as is.

---

**2026-08-01 | Finished and coded: HUNT (JB) TRANSPRT SVCS INC (JBHT) | 40 mins | notes below**

- Intensity Low. The freight it hauls is its service, not input
- Inputs seems like the closest available fit, but I am not fully sure

---

**2026-08-01 | Finished and coded: W P CAREY INC (CDC) | 40 mins | notes below**

- All locations seem to be tenant-occupied properties in its real-estate schedule. None of it is sourcing.

---

**2026-08-01 | Finished and coded: HOST HOTELS & RESORTS INC (MHS) | 30 mins | notes below**

- No decisions - hotel REIT, no imports.

---

**2026-08-01 | Finished and coded: UMB FINANCIAL CORP (UMSB) | 40 mins | notes below**

- Its only uses of import are sanctions compliance. No goods involved.

---

**2026-08-01 | Finished and coded: CHIMERA INVESTMENT CORP (CIM) | 30 mins | notes below**

- No decisions;  mortgage REIT, no imports.

---

**2026-08-01 | Finished and coded: EVEREST GROUP LTD (RE) | 40 mins | notes below**

- Could not find any trade related vocabulary anywhere in the filing.

---

**2026-08-01 | Finished and coded: ASANA INC (ASAN) | 20 mins | notes below**

- Its only uses of import concern transferring personal data across borders, not goods.

---

**2026-08-01 | Finished and coded: OPKO HEALTH INC (CYPH) | 40 mins | notes below**

- Its Chilean subsidiary imports into Chile, not the US so excluded. Properties table confirms Santiago is office and warehouse, not manufacturing.
- The one use of customs means local conventions, not border duties.
- Importing from four named countries but discloses no trade-policy exposure at all.

---

**2026-08-01 | Finished and coded: MISTER CAR WASH INC (MCW) | 20 mins | notes below**

- No decisions,  car washes, no imports.

---

**2026-08-01 | Finished and coded: KNIFE RIVER CORP (KNF) | 40 mins | notes below**

- None on reliance but 1 on tariff language. It has a dedicated risk factor on import tariffs, but what it describes is the price of cement and steel rising. Being exposed to the price of a tariffed commodity is not importing it, so I tried to stick to this rule consistently

---

**2026-08-01 | Finished and coded: WEBTOON ENTERTAINMENT INC (WBTN) | 20 mins | notes below**

- Its uses of import concern data transfer, not goods.

---

**2026-08-01 | Finished and coded: CHORD ENERGY CORP (OAS) | 40 mins | notes below**

- An oil producer, so three of its tariff uses are pipeline rate terms rather than trade. Still 1 on a dedicated trade-policy risk factor.

---

**2026-08-01 | Finished and coded: TELEDYNE TECHNOLOGIES INC (TDY) | 60 mins | notes below**

- Facilities in 10 foreign countries

---

**2026-08-02 | Finished and coded: GRAFTECH INTERNATIONAL LTD (EAF) | 60 mins | notes below**

- A dedicated risk factor says tariffs also raise the cost of its own raw materials.
- Brazil added; the properties table shows a real machine shop, not just an employee location. A Swiss site is a planning office and was excluded.

---

**2026-08-02 | Finished and coded: VALHI INC (LLC) | 50 mins | notes below**

- Relies on imports but could not find any quantification

---

**2026-08-02 | Finished and coded: HOME DEPOT INC (HOMD) | 80 mins | notes below**

- I debated High and Medium; High could also work, since few firms describe a global sourcing operation in this much detail without it being material.
- Countries taken from where sourcing offices are, not where staff are based
- Europe recorded as EU but a European sourcing office could be in the UK, Switzerland or Norway
- Goods type Finished, not Inputs: having a factory abroad build your own design is still buying a finished product.

---

**2026-08-02 | Finished and coded: LANDBRIDGE CO LLC (LB) | 40 mins | notes below**

- No mention of imports or foreign facilities

---

**2026-08-02 | Finished and coded: NATIONAL CINEMEDIA INC (NCMI) | 20 mins | notes below**

- Both uses of trade mean securities trading.

---

**2026-08-02 | Finished and coded: INSULET CORP (PODD) | 40 mins | notes below**

- Coding came out of the risk factors section

---

**2026-08-02 | Finished and coded: AEHR TEST SYSTEMS (AEHR) | 40 mins | notes below**

- Added Taiwan and EU, on a sentence saying it has procurement from those regions.

---

**2026-08-02 | Finished and coded: SOLARIS ENRGY INFRASTRUCTURE (SOI) | 40 mins | notes below**

- Intensity Low but it was a close call. Its main equipment supplier is 38% of total spend and the filing does not say it is foreign; the only signal was that the equipment may be subject to tariffs.
- Stays Low rather than Medium because the mention reads like a generic clause with no country and no quantification

---

**2026-08-02 | Finished and coded: CHAMPIONX CORP (APY) | 40 mins | notes below**

- Its one mention of suppliers in China is a list of competitors, in the competition section. A search for that phrase would record a source country from a sentence saying the opposite.

---

**2026-08-02 | Finished and coded: SI-BONE INC (SIBN) | 30 mins | notes below**

- Canada recorded. The filing says substantially all products are made in the United States but uses third-party manufacturers.
- The Italian site appears to be a sales office, so it was excluded.

---

**2026-08-02 | Finished and coded: INDEPENDENT BANK CORP/MI (IBCP) | 40 mins | notes below**

- Zero uses of tariff, duty, duties or customs anywhere in the filing

---

**2026-08-02 | Finished and coded: TRUPANION INC (TRUP) | 40 mins | notes below**

- Tariff language 0 on direction (its single tariff sentence is export-side)
- Its Philippines mention is contracted labor, not goods.

---

**2026-08-02 | Finished and coded: TPG RE FINANCE TRT INC (TRTX) | 40 mins | notes below**

- Its two uses of duties are contractual obligations. No mention of imports

---

**2026-08-02 | Finished and coded: AFYA LIMITED (AFYA) | 40 mins | notes below**

- Most recent annual report came after the cutoff, so used the prior year's filing
- Medial education company - no trade/import cases

---

**2026-08-03 | Finished and coded: JAYUD GLOBAL LOGISTICS LTD (JYD) | 60 mins | notes below**

- It is a customs broker, so tariffs are what it sells
- Coded None, any importing dones seems to be in China.
- Country column left empty despite the business section claiming global facilities, because the properties section mentions none
- Tariff language 1 recorded as debatable (the exposure runs through customers' cargo volumes.)

---

**2026-08-03 | Finished and coded: STELLANTIS NV (FCAU) | 40 mins | notes below**

- Some foreign plants feed the US business and counts counts as an import

---

**2026-08-03 | Finished and coded: ZIPRECRUITER INC (ZIP) | 20 mins | notes below**

- No decisions — job marketplace, no imports.

---

**2026-08-03 | Finished and coded: ONE GAS INC (OGS) | 40 mins | notes below**

- Uses tariff 32 times, every one a regulated rate schedule, with zero trade content anywhere.
- Its only mention of steel is the United Steelworkers union, not a purchased material.

---

**2026-08-03 | Finished and coded: VITESSE ENERGY INC (VTS) | 40 mins | notes below**

- No mention of imports

---

**2026-08-05 | Finished and coded: GOLD.COM INC (AMRK) | 60 mins | notes below**

- Intensity Medium: it buys finished coins from seven foreign sovereign mints for resale, but no share or figure is given, and it owns a US mint and holds a 35-year US Mint relationship.
- Goods type Finished: it does fabricate at its own US mint, but the filing never says that mint's raw material is foreign.
- Tariff language 0 (close). One tariff sentence is in the risk factors, but under a heading about revenues from business outside the US so it is about its foreign operations, not duties on the coins it brings in.

---

**2026-08-05 | Finished and coded: AMERISAFE INC (AMSF) | 20 mins | notes below**

- No decisions - workers' compensation insurer, no imports, and tariff never appears.

---

**2026-08-05 | Finished and coded: AVISTA CORP | 60 mins | notes below**

- Intensity High: filing gives a hard number: 75% of peak gas supply capacity comes from Canada.
- I debated between High and Medium; Medium could also work, because that 75% describes pipeline capacity rather than the volume actually bought.
- Goods type Both: gas resold to retail customers and burned as generation fuel.
- Ticker blank in the source file; left as is.

---

**2026-08-05 | Finished and coded: CALIFORNIA BANCRP (BCAL) | 40 mins | notes below**

- Tariff language 0 under the rule that a bank's tariff risk running through its borrowers is not its own import cost. Its risk factor is a full paragraph and names Mexico, Canada and China, but the exposure is credit quality and loan growth.
- Filed 1 April 2025, one day inside the cutoff.

---

**2026-08-05 | Finished and coded: STRATA CRITICAL MEDICAL INC (EXPC) | 40 mins | notes below**

- Filed under Blade Air Mobility (In August 2025, Blade Air Mobility, Inc. rebranded as Strata Critical Medical, Inc.)
- None on reliance but 1 on tariff language: US duties raising the price of the aircraft fuel it burns, with no importing of its own described.

---

**2026-08-05 | Finished and coded: BITDEER TECHNOLOGIES GROUP (BTDR) | 50 mins | notes below**

- It says it relies on overseas suppliers including suppliers in the United States. It is a Singapore-based bitcoin miner
- Coded None. It does run US data centers that machines must reach, but the filing never links a supply route to them and names no non-US manufacturer.
- Prior year's filing used; the latest came after the cutoff.

---

**2026-08-05 | Finished and coded: BYLINE BANCORP INC (BY) | 20 mins | notes below**

- No decisions / bank, no imports, and tariff never appears.

---

**2026-08-05 | Finished and coded: CELLDEX THERAPEUTICS INC (TCEL) | 40 mins | notes below**

- Intensity Medium: it engages contract manufacturers outside the US, with no size quantification given. Not High, it runs its own plant in Massachusetts.
- No country recorded; the filing says only outside the US.
- Tariff language 0 on direction: the only mention sits in a risk factor about commercializing products outside the United States.

---

**2026-08-05 | Finished and coded: MR COOPER GROUP INC (WAMU) | 30 mins | notes below**

- No decisions on coding - mortgage servicer, no imports, tariff not mentioned

---

**2026-08-05 | Finished and coded: CITIZENS FINANCIAL SVCS INC (CZFS) | 30 mins | notes below**

- Tariffs mentioned inside the agricultural lending risk factor, among things that could hurt farm borrowers' revenues.

---

**2026-08-05 | Finished and coded: DEFINITIVE HEALTH CORP (DH) | 40 mins | notes below**

- No decisions on coding. Healthcare data software, no goods.
- Its four duty hits are all fiduciary duty in the charter

---

**2026-08-05 | Finished and coded: EVENTBRITE INC (EB) | 20 mins | notes below**

- Tariff language 0: tariffs appear only in a list of macroeconomic conditions affecting consumer spending on events. A ticketing platform buys no goods.

---

**2026-08-05 | Finished and coded: E2OPEN PARENT HOLDINGS INC (PCPL) | 30 mins | notes below**

- Tariffs are mentioned as the product rather than the cost: its trade-management software database includes harmonized tariff codes.

---

**2026-08-05 | Finished and coded: GEOPARK LTD (GPRK) | 30 mins | notes below**

- The company explicitly says it does not directly import significant volumes from or to the United States.
- Tariff language coded 0 since it is mentioned as an overall risk to potential disruptions impacting them.
- The file I have is the FY2024 20-F, filed 2 April 2025, which is on the cutoff date rather than before it. I checked it for contamination and it is clean: it never mentions the April 2 reciprocal package anywhere, and its most recent tariff content is the January 2025 US-Colombia dispute.

---

**2026-08-05 | Finished and coded: HILLTOP HOLDINGS INC (ARC) | 40 mins | notes below**

- Tariff language 0 under the borrower rule. Its two other mentions are inputs to a downside economic scenario in the loan-loss model.

---

**2026-08-05 | Finished and coded: JACK IN THE BOX INC (FM) | 40 mins | notes below**

- Intensity Medium: the filing says some of its produce, meats and restaurant supplies are sourced from outside the United States, and ties that to a material financial-results risk.
- I debated Medium and Low; the word some reads like a hedge. I selected Medium because the filing frames it as material
- No country recorded. Mexico appears often but only as restaurant and franchise locations.

---

**2026-08-06 | Finished and coded: MIMEDX GROUP INC (MDXG) | 30 mins | notes below**

- None despite a high industry score: birth tissue comes from a US hospital donor network and is processed in Georgia.
- All its non-US references are about selling abroad and foreign approval to market, which do not count as sourcing.

---

**2026-08-06 | Finished and coded: DEFINIUM THERAPEUTICS INC (MNMD) | 50 mins | notes below**

- Manufacturing section names third parties with no geography and Item 1A says its contract manufacturers are in the United States and outside it. Also discusses needing US import permits for controlled substances.
- No country recorded. The long list of jurisdictions at p.23 is patent filings, not suppliers.
- Tariff language 0 on direction (the mention sits under risks of marketing internationally)

---

**2026-08-06 | Finished and coded: NOVAGOLD RESOURCES LTD (NG) | 30 mins | notes below**

- Importing liquefied natural gas by ship but no quantification and reads like a development project
- A British Columbia company that files a US annual report rather than a Canadian one.

---

**2026-08-06 | Finished and coded: NI HOLDINGS INC (NODK) | 20 mins | notes below**

- Tariff language 0: tariffs move crop prices, which affects its insured farmers rather than anything it buys.

---

**2026-08-06 | Finished and coded: ONESPAN INC (VDSI) | 40 mins | notes below**

- Intensity Medium: all of its Digipass hardware is built by contract manufacturers in southern China and Romania. Not High, because hardware is $58.9m of $243.2m revenue and the rest of the business is software with no goods at all.
- Recorded China and Romania but not the EU. The filing mentions the European Union only to locate Romania, which is already named
- Goods type Finished, not Both: the microprocessors it buys are shipped out to those factories, so they never enter the US.

---

**2026-08-06 | Finished and coded: PATRIA INVESTMENTS LTD (PAX) | 50 mins | notes below**

- Tariff language 0: its tariff mentions are geopolitical background and a list of risks facing the companies its funds invest in, not itself
- Prior year's filing used; the latest came after the cutoff.

---

**2026-08-06 | Finished and coded: PROTAGONIST THERAPEUTICS INC (PTGX) | 40 mins | notes below**

- Recorded EU and Asia
- Tariff language 0, all tariff mentions are about macroeconomic and capital-market conditions affecting its share price, never about the cost of what it buys.

---

**2026-08-06 | Finished and coded: REPUBLIC BANCORP INC/KY (RBCAA) | 30 mins | notes below**

- Tariff language 0: the mention is in the forward-looking list rather than the risk factors, and the filing itself calls those factors unrelated to the company's performance.

---

**2026-08-06 | Finished and coded: SIGA TECHNOLOGIES INC (SGPH) | 40 mins | notes below**

- This firm names every contract manufacturer it uses and all are US entities. Offices are New York and Oregon only.
- That said the filing never says where those US-named manufacturers actually do the work (could they be importing?)
- Tariff language 0 on direction... its tariff sentence is expressly about exporting its product to foreign government stockpiles.

---

**2026-08-06 | Finished and coded: TREACE MEDIC CNCPTS INC (TMCI) | 40 mins | notes below**

- Intensity Medium. It mentions about the risk of tariffs on imports from countries where they purchase their products but with no country, no share etc mentioned
- I actually debated Medium, Low and None; Low or None could also work, since one could argue that a generic conditional clause does not establish that the firm itself imports.
- The word tariff appears only twice in the whole filing: once in the forward-looking list (which I excluded) and once in the sentence I quoted. That sentence was under the General Risk Factors section, under a heading about unfavourable global economic conditions, not under a trade or sourcing heading.

---

**2026-08-06 | Finished and coded: UBS GROUP AG (UBS) | 40 mins | notes below**

- Tariff language 0: its tariff passages are the bank's own published economic outlook for 2025, printed inside the annual report. It is forecasting the world economy, not disclosing an exposure of its own.

---

**2026-08-06 | Finished and coded: UPSTART HOLDINGS INC (UPST) | 30 mins | notes below**

- No decisions;  lending marketplace, no goods, and tariff never appears. Its duty hits are all fiduciary.

---

**2026-08-06 | Finished and coded: UWM HOLDINGS CORP (GHIV) | 30 mins | notes below**

- Tariff language 0: only mention is in a list of federal policy actions whose effect on the housing market it lends into is described as unclear.

---

**2026-08-06 | Finished and coded: VINCI COMPASS INVEST LTD (VINP) | 50 mins | notes below**

- No decisions on coding (asset manager, no goods, and tariff never appears)
- Prior year's filing used; the latest came after the cutoff.

---

**2026-08-06 | Finished and coded: VTEX (VTEX) | 40 mins | notes below**

- Tariff language 0 on direction: its mentions are about expanding its own operations into new countries. It is also a Brazilian filer, so the trade barriers it contemplates are not US duties.

---

**2026-08-06 | Finished and coded: WAFD INC (WFSL) | 30 mins | notes below**

- Tariff language 0: tariffs cause inflation, which affects the prices its borrowers charge, which affects their profitability, which affects whether they can repay.

---

**2026-08-07 | Summarized rules and judgements that I used | 300 mins | notes below**

- Made a summary of the rules and judgements that I used over the last week when reading the files to capture in this log:

Which date did I use for filings: I reached out to Prof. Gao on this to confirm and ended deciding to use the most recent 10-K the company filed BEFORE 2 April 2025 (by filing date, not by fiscal year as I realized some of the documents filed after Liberation Date, although their fiscal year end was before the shock, were referring to the April 2 events)

Which sections did I mainly focus on: Item 1, Business; Item 1A, Risk Factors; Item 7, MD&A;Item 2, Properties (the facilities tables were useful). For a 20-F the equivalents are Item 4.B for Business, Item 3.D for Risk Factors and Item 5 for MD&A.

Field 1 - Import reliance:

- High: Either of two tests:
    - The filing says all, substantially all, or most of its products are imported or foreign-made, OR gives a percentage or dollar figure for imported goods.
    - The filing gives a hard number showing the company's own productive or sourcing assets are wholly or overwhelmingly foreign.
- Medium: The filing describes real reliance on foreign sourcing but never says how much. This ended up being the most populated level, because filings not always quantify their import reliance. For example, Home Depot describes sourcing offices in seven places and a direct import program, but does not state an import share (where I coded Medium). If I had more time, I might have looked at other resources or do a web search
- Low: Foreign sourcing is mentioned but described as minor or incidental. For example SiteOne had one product line of imported stone among thousands of products that they sell
- None: The filing describes no imported inputs or goods.

Field 2 - Finished goods or inputs:

- Inputs: bought to make something else.
- Finished goods: completed products bought for resale.
- Both: the filing plainly describes both, materially.

Field 3 - Tariff language: Do the risk factors treat tariffs or trade policy as a risk to this company? Coded 1 or 0 and followed the following rules:

- The language has to be in the risk factors, not the boilerplate or some generic cautionary statement.
- I tried to look at the direction of trade and 0 can mean “tariffs discussed, but not related to the company’s imports”
- I coded 0 for exposure through customers or borrowers. Many banks added a tariff paragraph to their filings and it was mostly about their borrowers rather than themselves. Same concept on tariff potentially impacting customer demand from a pure macroeconomics perspective.

I went back and double checked all coded entries where Tariff language was 1 where import reliance was None.

Field 4 - Source countries: For this, I ended up relying on 3 rules:

- Included the sourcing offices but excluded staff locations / offices
- Foreign plants serving foreign markets are excluded if the filing's own segment discussion mentions that
- I kept the region names (e.g. Asia), especially when no other country names were mentioned within that region

---
