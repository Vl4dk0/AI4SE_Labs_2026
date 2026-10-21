# Software requirements

Generated: 2026-10-20

Models: classification `gpt-4.1-nano`; extraction and deduplication `gpt-5-nano`; polishing `gpt-4o-mini`.

## Priority scale

Priorities use MoSCoW. A stronger priority wins when two wordings of the same requirement are merged.

- **Must** — the system is not acceptable without this. The source says shall, must, or required, or it is a stated specification requirement.
- **Should** — important, but acceptance does not depend on it.
- **Could** — do it if the schedule allows. A wish or an option.
- **Won't** — explicitly out of scope for this iteration. Recorded so it is not built and not forgotten.

**Boost.** After duplicates are merged, a requirement whose sources include a decision document, or a requirement with at least three distinct sources, is raised one level. Must stays Must. The boost is applied once, even when both conditions are true. An explicit Won't that is backed by a decision or by three sources therefore becomes a Could.

Requirements are grouped by category. Each identifier is stable for this document.

## Circulation

### REQ-001 — Count check-ins by type

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `survey_results_2009.txt`

The system must count all check-ins individually and cumulatively, including book-drop, by terminal, by patron or self-service.

### REQ-002 — Count check-outs by type

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `survey_results_2009.txt`

The system must count all check-outs individually and cumulatively: staff checkout, self checkout, staff renewal, self checkout renewal, online renewal, OPAC renewal.

### REQ-003 — In-transit items reporting with configurable days

- **Priority:** Must
- **Sources:** `conversations/conv_pines019_020_missing_intransit.eml`, `early_draft_srs_galecia.txt`

Generate a list of items in transit for more than X days (X configurable) per branch and per library system, merging transit-to and transit-from into one report for frontline staff use. The system shall generate a list of items that have been in transit for more than X days (X configurable, defaults to 7 days) per branch and per library system, and the report shall merge transit-to and transit-from data into a single report for frontline staff.

## Cataloging

### REQ-004 — Batch transfer utility and last-copy reporting

- **Priority:** Must
- **Sources:** `conversations/conv_pines018_item_transfer.eml`, `conversations/conv_pines021_item_purging.eml`, `interview_cataloging_2009-05-08.txt`

Batch transfer utility for transferring batches of items between branches, including: querying for candidate materials, saving queries for repeated use, manually selecting titles from query results, changing records of selected items to move them to a new location, generating pull lists, and mechanisms to revert items to their original location after a set period. Additionally, a last-copy reporting capability per library and per library system is provided to identify an item’s last copies and assist catalogers in editing WorldCat entries, with views that support preventing loss of rare copies within a scope.

### REQ-005 — Data specifications for management records

- **Priority:** Must
- **Sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`

The software developer shall provide complete data specifications for authority, bibliographic, order, item, hold/request records, and other management-process records to enable staff to write effective queries and build data dictionaries.

### REQ-006 — Definition of electronic activity

- **Priority:** Must
- **Sources:** `conversations/conv_pines024_inactive_patrons.eml`

Electronic activity shall include: OPAC/patron account login, online hold placements, online renewals, and access to digital resources (if integrated); these activities are tracked separately but included in determining inactivity.

### REQ-007 — Delete orphaned records and volume entries

- **Priority:** Must
- **Sources:** `interview_cataloging_2009-05-08.txt`

Provide a quick, effective method for deleting volume entries along with copy entries, as well as records that have no items attached (orphaned records), to streamline cleanup operations.

### REQ-008 — Quick delete utility for volumes and copies

- **Priority:** Must
- **Sources:** `conversations/conv_pines021_item_purging.eml`

Provide a quick effective method to delete volume entries along with their associated copy entries, and to delete records that have no items attached, as a cleanup utility.

### REQ-009 — Uncataloged materials tracking

- **Priority:** Must
- **Sources:** `interview_cataloging_2009-05-08.txt`

Cataloging staff need to track shipments of paperback books and children’s board books that arrive without individual catalog records as inventory, with quick distribution, minimal branch labor per item, and the ability to identify how the material is being used; additionally, ensure that all transactions are counted and included in circulation statistics and reports.

### REQ-010 — Authority and bibliographic data specifications

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The developer must provide complete data specifications for authority records, bibliographic records, order records, item records, hold/request records, and other records maintained or accessed by the Management Processes.

### REQ-011 — Data quality reports

- **Priority:** Should
- **Sources:** `interview_cataloging_2009-05-08.txt`

Provide data quality reports highlighting items with invalid item types, items with long call numbers, and bibliographic records with no item records to help maintain data integrity.

### REQ-012 — Printable transit labels

- **Priority:** Could
- **Sources:** `conversations/conv_pines018_item_transfer.eml`

Generate printable transit labels (e.g., barcodes) for items being transferred.

## Holds

### REQ-013 — Hold placement tracking and method counting

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `survey_results_2009.txt`

The system tracks holds and counts holds based on the method of placement, whether at the staff desk, at a public computer, or remotely. It should record all hold requests and the specific method by which each hold was placed.

### REQ-014 — Purging: batch status changes with configurable and combined criteria

- **Priority:** Must
- **Sources:** `conversations/conv_pines021_item_purging.eml`

The system should support batch status changes via a report to assist in converting items from one status to another in bulk, such as changing multiple items from missing to discard/weed at once. It must allow customizable purging criteria based on multiple conditions, configurable by staff, and support for combining criteria to form complex purge conditions.

## Patrons

### REQ-015 — Demographic statistics with anonymization (region and age ranges)

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `survey_results_2009.txt`

The system must provide demographic statistics including transactions by geographical regions and age ranges, ensuring that data is anonymized by deleting identifying patron information.

### REQ-016 — Exclude certain patron types from inactive report

- **Priority:** Must
- **Sources:** `conversations/conv_pines024_inactive_patrons.eml`

The report shall allow staff to exclude patrons based on criteria such as 'do not disturb' flags, VIP status, staff membership, or patrons who have opted out of communications.

### REQ-017 — Include mailing addresses in report

- **Priority:** Must
- **Sources:** `conversations/conv_pines024_inactive_patrons.eml`

For outreach purposes, the report output shall include current mailing addresses of inactive patrons.

### REQ-018 — Track inactive patrons with outstanding fines separately

- **Priority:** Must
- **Sources:** `conversations/conv_pines024_inactive_patrons.eml`

The system shall track patrons who are inactive but still owe fines as a separate subset for handling, such as outreach or cleanup tasks.

### REQ-019 — Financial audit trail

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system maintains a ledger of patron payments, detailing which charges payments are applied to, to facilitate reconciliation.

### REQ-020 — Inactive patrons report

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should generate a list of patrons with no circulation or electronic activity in the last configurable days, with options for configuration by system, home branch, county, etc.

### REQ-021 — Patron behavior statistics

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should produce statistics to understand and predict patron behavior and use of materials, such as average return time, renewal likelihood, and the percentage of renewals in check-outs at a branch.

### REQ-022 — Patron characteristic-based restrictions

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

Queries and reports can be limited or grouped by patron characteristics, including age range, zip code, county of residence, home branch, and preferred language.

### REQ-023 — Patron financial data linkage

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

Fines, charges, waivers, and ecommerce transactions are linked to patron and item records, allowing staff to query patron accounts with balances greater than a specified amount.

## Acquisitions

### REQ-024 — Acquisition date tracking for time-based analysis

- **Priority:** Must
- **Sources:** `conversations/conv_pines014_material_volume.eml`

The system shall track acquisition dates for items to enable volume reports that show changes over time, such as over the last 30, 60, or 90 days, and allow for historical comparisons.

### REQ-025 — Item transfer utility

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

Provide a utility for transferring batches of items between branches, including querying for candidate materials, saving queries, manually selecting titles, changing records to move to a new location, mechanisms for moving items, and reverting items to original location after a set time.

### REQ-026 — Financial reporting capabilities

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system provides financial reports including patron account balances by patron, home library, and system; fines and charges by time period and charge type; fines waived by time period and branch; and payments by time period and payment method.

## Reports

### REQ-027 — Ability to cancel running reports

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

The system shall allow staff to cancel a report that is currently running in the queue.

### REQ-028 — Aged Debt

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an Aged Debt report.

### REQ-029 — Annual # of holds placed

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an Annual # of holds placed report.

### REQ-030 — Audit report interface

- **Priority:** Must
- **Sources:** `conversations/conv_pines022_deletions.eml`

The system shall provide a report interface to query the audit table of deletions, allowing aggregation and reporting of deletions per location and per system, with options to filter by date range and staff.

### REQ-031 — Audit trail for payments

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

The system shall maintain a ledger of patron payments, including which charges payments are applied to, to facilitate reconciliation.

### REQ-032 — Audit trail for purges

- **Priority:** Must
- **Sources:** `conversations/conv_pines021_item_purging.eml`

The system must maintain an audit trail recording who purged what and when, for accountability and troubleshooting.

### REQ-033 — Bib Records Added by staff by library Count

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Bib Records Added by staff by library Count report showing additions performed by staff within the library context, as part of Bib Records Reports.

### REQ-034 — Bib Records Count

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Bib Records Count report for Bib Records, accessible to library staff as part of Bib Records Reports.

### REQ-035 — Bib Records Edited Count

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Bib Records Edited Count report for Bib Records, accessible to library staff as part of Bib Records Reports.

### REQ-036 — Bib Records missing specific MARC fields

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Bib Records missing specific MARC fields report identifying bibliographic records missing required MARC fields, as part of Bib Records Reports.

### REQ-037 — Bib Records with No Volumes attached

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Bib Records with No Volumes attached report listing bibliographic records that lack volume attachments, as part of Bib Records Reports.

### REQ-038 — Bills currently Owed by Patrons

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Bills currently Owed by Patrons report.

### REQ-039 — Board reports definition

- **Priority:** Must
- **Sources:** `email_report_features.eml`

Pre-defined board reports with basic statistics (Georgia Annual Report requirements) and activity reports showing traffic and use (checkouts, check-ins, holds placed, holds filled), cross-tabulated per terminal, branch, system, hour, age range, patron type, and patron location.

### REQ-040 — Canned reports availability

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

System shall include pre-defined canned reports across categories (Circulation, Items, Bib Records, Patrons, Bills) such as Checkout Count, Renewals Count, Items Added Count, Bib Records Count, Patron Count, Bills Currently Owed by Patrons, etc.

### REQ-041 — Canned Reports Details

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall include pre-written templates delivered with the product, capable of running by yesterday's data, last week’s, last month’s, or last year’s data, and allow running multiple canned reports together within one document.

### REQ-042 — Cataloged In House Use Count

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Cataloged In House Use Count report.

### REQ-043 — Category breakdown with customization

- **Priority:** Must
- **Sources:** `conversations/conv_pines014_material_volume.eml`

The report shall expose breakdowns by categories including total items, number of holds, number of adult fiction, number of board books, and allow other categories to be customized by library.

### REQ-044 — Compliance with accounting and auditing requirements

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

All reports and data archiving must comply with standard accounting practice and state, county, and municipal auditing requirements.

### REQ-045 — Configurable age ranges per report

- **Priority:** Must
- **Sources:** `conversations/conv_pines023_patron_characteristics.eml`

The system shall allow age ranges to be configurable per report (e.g., 0-5, 6-10, 11-15 or alternative groupings) and compute age brackets from birth_date for the report.

### REQ-046 — Configurable reporting scope levels

- **Priority:** Must
- **Sources:** `conversations/conv_pines024_inactive_patrons.eml`

The reporting feature shall allow configuring the level at which inactive patrons are determined, including System, Home Library, and County (and other levels as needed).

### REQ-047 — Data specifications and dictionaries

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

Develop complete data specifications for Authority, Bibliographic, Order, Item, Hold/Request, and other records, including data dictionaries with field names, data types, and relationships to support staff queries.

### REQ-048 — Detailed Forgive, Work, and Goods Payments Received

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Detailed Forgive, Work, and Goods Payments Received report.

### REQ-049 — Detailed Payments Received

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Detailed Payments Received report.

### REQ-050 — Detailed Voids

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Detailed Voids report.

### REQ-051 — Document optimal Reports functionality

- **Priority:** Must
- **Sources:** `meeting_minutes/meeting_2009-03-15_minutes.txt`

The Reports Working Group shall document the optimal Reports functionality within a future Evergreen release and develop a list of requirements based on that functionality, involving the group as the primary actors and assuming Evergreen as the system under consideration.

### REQ-052 — Enterprise scope and central consolidation

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

Management Processes are part of an enterprise-level Library Automation System and are consolidated at a central location, accepting input and providing services to multiple branches.

### REQ-053 — Environments and migration

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

There must be separate development, training, and production environments with a mechanism to migrate configurations between them, including export/import of templates, permission settings, and saved queries; the training environment must be safe for experimentation without risking production data.

### REQ-054 — Executive Reports Interface reports list

- **Priority:** Must
- **Sources:** `meeting_minutes/meeting_2009-03-15_minutes.txt`

The Reports Working Group shall compile a list of reports needed for an Executive Reports Interface, identifying the concrete reports and reporting needs that should be supported for the executive view within the system.

### REQ-055 — Exportable report format

- **Priority:** Must
- **Sources:** `conversations/conv_pines024_inactive_patrons.eml`

The inactive patrons output shall be exportable in a CSV format suitable for uploading to outreach systems.

### REQ-056 — Filter by Deleted Items Last Copy

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall support running a report on deleted items that were the last copy in the facility.

### REQ-057 — Fines and charges over time

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

System shall provide financial reports showing fines and charges accrued per time period (last 12 months, YTD, last month).

### REQ-058 — Fines waived by time and branch

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

System shall provide financial reports showing fines waived per time period and per library/branch.

### REQ-059 — Full administrator access

- **Priority:** Must
- **Sources:** `email_staff_login.eml`

System administrators shall have full access to all reports and permissions.

### REQ-060 — Global capacity interface for all branches

- **Priority:** Must
- **Sources:** `conversations/conv_pines015_capacity_interface.eml`

The system shall provide an interface that shows the capacity of all branches. It must include a high-level overview of all branches' capacity at once, support drilling down into individual branches, allow sorting and filtering (by region, by library type, by current load), provide trend data (growth or shrink patterns), and support exporting the data to CSV.

### REQ-061 — Group by patron characteristics

- **Priority:** Must
- **Sources:** `conversations/conv_pines023_patron_characteristics.eml`

The system shall allow queries and reports to be grouped by patron characteristics such as age range, zip code, county of residence, home branch, patron type, and preferred language, enabling the production of aggregate counts or statistics per category.

### REQ-062 — Holds and check-outs per patron/library/group/system/county

- **Priority:** Must
- **Sources:** `survey_results_2009.txt`

The system must produce a Transactions report that displays holds placed, holds filled, and check-outs per patron, per branch, per group of branches, per library system, and per county.

### REQ-063 — Holds Purchase Alert

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Holds Purchase Alert report as part of the Holds Reports.

### REQ-064 — HTML compliance

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

The system must produce standards-compliant HTML for the web-based interface, help system, and report output, ensuring compatibility with browsers and assistive technologies.

### REQ-065 — ILs data dependencies

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

Management Processes rely on data structures and functionality of an enterprise-level Library Automation System, including Acquisitions and Cataloging modules, with the reporting system reading data from the ILS without managing acquisitions or cataloging.

### REQ-066 — Inactive patrons report generation

- **Priority:** Must
- **Sources:** `conversations/conv_pines024_inactive_patrons.eml`

The system shall generate a list of patrons who have had no circulation or electronic activity in the last configurable number of days, targeting patrons across configured scopes such as System, Home Library, and County, and supporting exporting the results for outreach.

### REQ-067 — Include null values in results

- **Priority:** Must
- **Sources:** `conversations/conv_pines023_patron_characteristics.eml`

The system shall include records with null or missing values for demographic fields in reports to ensure that results are not misleading due to missing data.

### REQ-068 — IntraPINES Loans by Facility

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an IntraPINES Loans by Facility report.

### REQ-069 — IntraPINES Loans by System

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an IntraPINES Loans by System report.

### REQ-070 — IntraPINES Loans for all Facilities

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an IntraPINES Loans for all Facilities report.

### REQ-071 — IntraPINES Loans for all Systems

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an IntraPINES Loans for all Systems report.

### REQ-072 — Items In Transit by Sending Library

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an Items In Transit by Sending Library report.

### REQ-073 — Items In Transit to Destination Library

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an Items In Transit to Destination Library report.

### REQ-074 — Items Received for Holds

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an Items Received for Holds report as part of Holds Reports.

### REQ-075 — Items Sent for Holds

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an Items Sent for Holds report as part of Holds Reports.

### REQ-076 — Join patron and item data for reports

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

Financial reports shall be able to join data from patron records and item records to support integrated reporting.

### REQ-077 — Last edit date visible on reports only for edits

- **Priority:** Must
- **Sources:** `interview_cataloging_2009-05-08.txt`

Ensure that reports display the last edit date only when the item itself was edited, and exclude last circulation date; current behavior combines these dates.

### REQ-078 — Library-scoped reporting

- **Priority:** Must
- **Sources:** `conversations/conv_pines014_material_volume.eml`

The volume report shall count items for a specific library location (e.g., a given library) and support grouping by applicable categories (fiction/non-fiction, format, etc.).

### REQ-079 — Limit reports by patron characteristics

- **Priority:** Must
- **Sources:** `conversations/conv_pines023_patron_characteristics.eml`

The system shall allow queries and reports to be limited by patron characteristics (e.g., age range, zip code, county of residence, home branch, patron type, preferred language) so that the result set can be restricted to a subset of patrons for a given report.

### REQ-080 — List of Patrons by Expiration Date

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a List of Patrons by Expiration Date report listing patrons with their account expiration dates.

### REQ-081 — List of patrons by survey answer

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a List of patrons by survey answer report providing lists of patrons corresponding to each survey answer.

### REQ-082 — List of patrons who are BARRED

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a List of patrons who are BARRED, as part of Patrons Reports.

### REQ-083 — List of Patrons with inactive status

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a List of Patrons with inactive status.

### REQ-084 — List of Patrons with specific wording in notes

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a List of Patrons with specific wording in notes.

### REQ-085 — List of Staff Accounts with date of last password change and account expiration

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a list of staff accounts that includes the date of the last password change and the account expiration date.

### REQ-086 — MARC Record Fields on One Row

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall pull MARC record fields so that they appear on a single row of data in a report.

### REQ-087 — Missing and in-transit items reporting

- **Priority:** Must
- **Sources:** `interview_cataloging_2009-05-08.txt`

Provide reports that show all missing and damaged items per branch from monthly shelf readings, along with an in-transit items report for items being transferred between branches. This report should identify items in transit for more than a configurable number of days and merge transit-from and transit-to data into a single view.

### REQ-088 — Missing/damaged items report per branch

- **Priority:** Must
- **Sources:** `conversations/conv_pines019_020_missing_intransit.eml`

The system shall provide a report of missing and damaged items, broken down per branch, to support inventory audits and collection management.

### REQ-089 — Multiple output formats

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

The system shall provide multiple output formats for reports beyond current support, including additional formats beyond CSV, HTML, and Excel as applicable.

### REQ-090 — New Patron Count by Demographic

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a New Patron Count report by Demographic Category for patrons added in the prior month, as part of Patrons Reports.

### REQ-091 — NonCat In House Use Count by Month

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a NonCat In House Use Count by Month report.

### REQ-092 — Null handling

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

All NULLs and blank fields must be included in results; this behavior should be explicitly required.

### REQ-093 — On Demand Reports

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall support On Demand Reports that are pre-selected by criteria but run on demand for maintenance, collections development, and similar use cases.

### REQ-094 — OPAC performance constraint

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

The management reporting system is separate from the public catalog, and when a report is running, it must not slow down the OPAC.

### REQ-095 — Open Template Reporting

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall provide an Open Template Reporting interface with all attributes for circulation, patrons, items, bills, and bibliographic records to select from for filtering and display.

### REQ-096 — Open template/reporting interfaces

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

The system shall include Open Template Reporting and multiple interfaces (canned, on-demand, open template) as part of the reporting capabilities.

### REQ-097 — Output formats

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

Supported export and display formats include Excel, HTML, and CSV; Excel is preferred for pivot tables, CSV is the most reliable for data export, and HTML is used for web display.

### REQ-098 — Output Variability and Comparisons

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall support outputs with multiple columns, such as last month, previous month, percent differences, and last year's month, and include date selection criteria in results.

### REQ-099 — Patron Added Count by Month

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Patron Added Count by Month report showing the number of patrons added each month, as part of Patrons Reports.

### REQ-100 — Patron balances by scope

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

The system shall provide financial reports that show patron account balances by patron, by home library, and by system.

### REQ-101 — Patron Count

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Patron Count report listing the number of patrons, as part of Patrons Reports.

### REQ-102 — Patron Count by Age Demographic

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Patron Count by Age Demographic report.

### REQ-103 — Patron Count by County

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Patron Count by County report.

### REQ-104 — Patron Count by County, City, and Zip Code

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Patron Count by County, City, and Zip Code report.

### REQ-105 — Patron Count by Home Library

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Patron Count by Home Library report.

### REQ-106 — Patron Count by Profile Group

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Patron Count by Profile Group report.

### REQ-107 — Patron Count by survey answer

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Patron Count by survey answer report listing counts per survey answer.

### REQ-108 — Payments by library tracking

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

The system shall track payments by library/branch so end-of-month reports can show what payments were collected at each location.

### REQ-109 — Payments by time period and method

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

The system shall provide financial reports showing payments made per time period and per payment method (staff desk, self-check, OPAC).

### REQ-110 — Periodic report examples support

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system must support the periodic report definitions as described by the attached report examples (see Appendix A).

### REQ-111 — Process descriptions

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

Provide a thorough high-level description of major processes, including bibliographic record import/export, validation against authority sources, and standard reports.

### REQ-112 — Query selections alongside results

- **Priority:** Must
- **Sources:** `email_report_features.eml`

The system should provide query selections in addition to showing the results of those queries.

### REQ-113 — Query tool for report design

- **Priority:** Must
- **Sources:** `email_report_features.eml`

Staff should have a user-friendly interface for designing queries against all record types, with the ability to select fields to query, select values from picklists, use regular expressions from a dropdown, and apply Boolean operators.

### REQ-114 — Quick Access Interface – Email and Recurrence

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall allow entering email addresses (with an address book), editing recurring reports (selections and emails), and prioritizing reports in a queue.

### REQ-115 — Quick Access Interface – Run Options

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall provide a Quick Access Interface that allows hovering over canned report titles to show a description, selecting Run ASAP/Hourly/Daily/Weekly/Monthly/Yearly, and output in Excel, HTML, and CSV formats.

### REQ-116 — RBAC with role-based access

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

The system shall implement security groups and/or roles that allow access control for individuals, workgroups, and arbitrary staff groups, with easy permission changes by altering role assignments; defined roles include Global Admin, Local Admin, Library Manager, Staff, and Patron (indirect via OPAC).

### REQ-117 — Read-only purge candidate reports

- **Priority:** Must
- **Sources:** `conversations/conv_pines021_item_purging.eml`

The system should present reports identifying purge candidates in read-only form to prevent accidental deletions.

### REQ-118 — Real-time and historical reporting

- **Priority:** Must
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

Some reports should be real-time (e.g., overdue items today) while others are historical (e.g., bill amount on a specific date); a reporting warehouse for historical data is needed.

### REQ-119 — Report delivery via email

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

The system shall provide email delivery of scheduled or on-demand reports in addition to web-interface access and downloads.

### REQ-120 — Report queue visibility

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

The system shall implement visibility into the report queue and provide status indicators for running and pending reports.

### REQ-121 — Report queue visibility

- **Priority:** Must
- **Sources:** `email_report_features.eml`, `survey_results_2009.txt`

Patrons should be able to see where their report is in the queue, including the number of reports ahead and the submission time, with status indicators (waiting, running, completed, failed). The system must provide the ability to see where a report is in the queue.

### REQ-122 — Report scheduling with run options

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

The system shall support scheduling of reports with options to run ASAP, hourly, daily, weekly, monthly, or yearly, and allow multiple reports to be scheduled without conflict.

### REQ-123 — Report templates creation and execution

- **Priority:** Must
- **Sources:** `survey_results_2009.txt`

Staff must be able to create report templates and run them as-is or modified.

### REQ-124 — Report templates with run/modify behavior

- **Priority:** Must
- **Sources:** `email_report_features.eml`

Staff should be able to create report templates that are available to staff, templates should be runnable as-is or modified, changes must not compromise results, and staff should be able to limit which filters and display fields can be altered.

### REQ-125 — Report writer capabilities

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

The system shall provide a report writer interface that allows staff to create custom reports with drag-and-drop field selection, basic filtering and sorting, multiple output formats (CSV, HTML, Excel), and the ability to save and reuse report definitions.

### REQ-126 — Retention enforcement

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

The system shall enforce data retention policies, including retaining data for 7 years for audit purposes as required by state/local requirements.

### REQ-127 — Shelf space reporting and estimation by genre/format

- **Priority:** Must
- **Sources:** `conversations/conv_pines016_shelf_space.eml`, `early_draft_srs_galecia.txt`, `interview_cataloging_2009-05-08.txt`

The system shall estimate shelf space per genre/format by either using item dimensions as a basis or by using item count as a proxy, to produce the percentage of shelf space figures. For each genre and format of material, the system shall provide the ability to compare the percentage of total circulations, the percentage of the collection, and the percentage of total shelf space, with the report available per branch and per library system so that branch managers and system administrators can see local and system-wide standings. Additionally, shelf space reporting should present, for each genre and format, the percentage of total circulations, the percentage of the collection, and the percentage of total shelf space to aid decisions on resource allocation across libraries.

### REQ-128 — Stale Holds

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Stale Holds report for holds sitting on the hold shelf waiting for pickup for too long.

### REQ-129 — Statistics for patron behavior and materials use

- **Priority:** Must
- **Sources:** `survey_results_2009.txt`

The system must produce statistics to understand and predict patron behavior and use of materials.

### REQ-130 — Support combined filters with AND/OR

- **Priority:** Must
- **Sources:** `conversations/conv_pines023_patron_characteristics.eml`

The system shall support combining multiple demographic filters using AND or OR logic in a single report query, enabling complex constraints across patron characteristics.

### REQ-131 — Support for canned reports definitions

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system must be able to support the reporting definitions as described in the attached report examples.

### REQ-132 — Support for fine-grained reporting requirements

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system must be able to support the fine-grained reports requirements as described in Appendix B.

### REQ-133 — Survey filtering by name

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

The system shall allow filtering reports by selecting the survey name without requiring a survey ID. It must be able to filter by survey name, necessitating internal resolution of names to IDs.

### REQ-134 — Template and permissions management features

- **Priority:** Must
- **Sources:** `email_staff_login.eml`, `evergreen_reference_2009.txt`

Department heads should be able to create and modify templates. The system shall include template management and open template capabilities to support standardized reporting and reuse, with separate templates for canned, on-demand, and open-template reporting modes.

### REQ-135 — Three Interfaces

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall provide three interfaces for reporting: (a) Canned reports – generic reports set to run by the individual ASAP or recurring, (b) Noncanned or On Demand Reports – preset but editable selection criteria and display options, (c) Open Template Reporting – all attributes for circulation, items, patrons, bills, and bibliographic records to filter and display.

### REQ-136 — Transaction archive with privacy and retention

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `email_report_features.eml`

Transactions should be archived in a form that protects patron privacy as defined by State Law, while providing useful demographic statistics. The transaction archive must protect patron privacy per State Law while providing useful demographic statistics, with retention of transaction data for a specified number of years.

### REQ-137 — Transactions by Date and Workstation/Staff

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a report on transactions that occurred on a specific date/time on a specified workstation or by a specified staff member.

### REQ-138 — Transactions grouping by time and location

- **Priority:** Must
- **Sources:** `survey_results_2009.txt`

The system must allow transactions to be grouped by hour, terminal, branch, and library system.

### REQ-139 — Transfer history auditing

- **Priority:** Must
- **Sources:** `conversations/conv_pines018_item_transfer.eml`

The system shall log all item transfers for audit purposes, including details of transfers to support accountability.

### REQ-140 — Unfilled Holds

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate an Unfilled Holds report.

### REQ-141 — Value of items report

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `email_financial_reports.eml`

The system can generate a report of the value of items based on data in item records, such as the value of all long-overdue items, value of all DVDs in the children's collection, or value of the entire collection. The system shall generate a value of items report based on data in item records, with the ability to cover the entire collection or a portion.

### REQ-142 — Vendor integration interfaces

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

The system must interface with a variety of vendor websites via published APIs and/or automated transfer of standard-format data files (e.g., USMARC21, EDIFACT) to handle data from external sources for reporting. The system must be able to handle this data even if not present at every branch.

### REQ-143 — Volume reporting at point in time

- **Priority:** Must
- **Sources:** `conversations/conv_pines014_material_volume.eml`

The system shall provide the ability to report on the volume of material in a given branch at any point in time, based on new acquisitions, items on the shelf (checked in), and items out in circulation (checked out). The report should include a total volume figure for the library location.

### REQ-144 — Voter Reg Survey Responses Count by Week

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Voter Reg Survey Responses Count by Week report counting voter registration survey responses on a weekly basis.

### REQ-145 — Voter Survey Responses County by Week

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system shall generate a Voter Survey Responses County by Week report showing voter survey responses aggregated by county on a weekly basis.

### REQ-146 — Weeding and purging reports

- **Priority:** Must
- **Sources:** `interview_cataloging_2009-05-08.txt`

Deliver reports to identify items for purging based on customizable criteria (e.g., status 'missing' for more than X months; status 'discard/weed'); include the ability to perform batch changes (e.g., changing 100 items from 'missing' to 'discard/weed'), and generate the last copy report to aid WorldCat editing.

### REQ-147 — Accounting compliance for reports and archiving

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

All reports and data archiving must comply with standard accounting practice and state, county, and municipal auditing requirements.

### REQ-148 — Activity reports with cross-tabulation

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

Activity reports should indicate traffic and volume of use, displaying statistics on check-outs, check-ins, holds placed, and holds filled, and must be cross-tabulatable per terminal, per branch, per library system, per hour, per patron age range, per patron type, and per patron location.

### REQ-149 — Backroom statistics by time and type

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

Transactions can be grouped by hour, terminal, branch, and system, and can be queried by all transactions or by type of transaction (check-ins, check-outs, fines, patron registrations, etc.).

### REQ-150 — Board and executive reports

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should provide pre-defined reports for library boards and external consumers, including basic statistics like those required by state reports; activity reports should indicate traffic and volume of use.

### REQ-151 — Comprehensive transactions report

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system can generate a transactions report per patron, per library, per selected group of libraries, per system, per county, with counts of check-outs and placed holds per patron and holds subtotaled by type (active, frozen, frozen-until).

### REQ-152 — Front desk reporting permissions

- **Priority:** Should
- **Sources:** `email_staff_login.eml`

Front desk staff role should be able to run basic reports with limited filters.

### REQ-153 — In-transit report sort by due date

- **Priority:** Should
- **Sources:** `conversations/conv_pines019_020_missing_intransit.eml`

The in-transit report shall support sorting by due date to allow frontline staff to chase the oldest items first.

### REQ-154 — Material volume reporting by acquisitions, shelf, and circulation

- **Priority:** Should
- **Sources:** `interview_cataloging_2009-05-08.txt`

Generate a material volume report that summarizes quantities by acquisitions, items on shelf, and items in circulation, broken down into categories such as total items, holds, adult fiction, board books, etc.

### REQ-155 — Missing and damaged items reporting

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

Provide reports of missing and damaged items per branch.

### REQ-156 — Pre-defined board/executive reports

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should provide pre-defined reports for consumption by library boards and other external consumers, including basic statistics like those required by the Georgia Annual Report and Application for State Aid.

### REQ-157 — Query selections displayed with results

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should provide the query selections along with the results, so patrons can see what criteria were used to generate the report.

### REQ-158 — Query tool for all record types

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should provide a user-friendly interface for designing queries against all record types (bibliographic, item, patron, transaction, financial) with capabilities to select fields, values, regular expressions, and Boolean operators; administrators control staff access to tables and fields.

### REQ-159 — Report cancellation capability

- **Priority:** Should
- **Sources:** `meeting_tech_subcommittee_2009-06-30.txt`

The system should support cancellation of scheduled or running reports, requiring the system to check for cancellation signals during processing.

### REQ-160 — Report permissions and folders

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should provide distinct, fine-grained permission levels that limit who can create and clone reports, and allow administrators to create shared folders to control staff access to specific reports or ad hoc data sets.

### REQ-161 — Report queue visibility for staff

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

Staff should be able to see where their report is in the queue of reports waiting to run.

### REQ-162 — Report templates

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

System administrators should be able to create report templates available to staff, runnable as-is or modifiable; changes should not compromise accuracy, and filters/display fields control should be limited to ensure dependable output.

### REQ-163 — Report Top/Bottom Presentation

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system shall allow reports to display a top-level indication of the date selection criteria and the report name for quick reference.

### REQ-164 — Templates for PINES libraries

- **Priority:** Should
- **Sources:** `meeting_minutes/meeting_2009-03-15_minutes.txt`

Determine and create templates needed for all PINES libraries as part of the Reports functionality, ensuring reusable structures are available for library-specific reporting needs across PINES libraries.

### REQ-165 — Transfer delay alerts

- **Priority:** Could
- **Sources:** `conversations/conv_pines018_item_transfer.eml`

Notify stakeholders if an item transfer is delayed or encounters issues.

## Staff, administration, and security

### REQ-166 — Accessibility compliance

- **Priority:** Must
- **Sources:** `interview_sysadmin_2009-05-10.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

Management Processes shall be accessible with screen-reading software, screen-magnification software, and other assistive technologies (e.g., JAWS, NVDA, ZoomText) to meet Section 508 compliance mandatory for public institutions. The system must comply with Section 508 accessibility requirements, work with screen readers (JAWS, NVDA), screen magnification (ZoomText), other assistive technologies, provide alt tags, ARIA labels, semantic HTML, and generate standards-compliant HTML so that no staff member is unable to run reports.

### REQ-167 — Accessibility compliance for report interface

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

System shall implement accessibility compliance for the report interface to ensure it is usable by patrons and staff with disabilities.

### REQ-168 — Assistive technology accessibility

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

The system must be accessible with screen-reading software, screen-magnification software, and other assistive technology programs designed to increase accessibility.

### REQ-169 — Audit trail for logins

- **Priority:** Must
- **Sources:** `email_staff_login.eml`

The system must track which staff member is logged in for audit purposes, even when using card swipe as a convenience to identify the person.

### REQ-170 — Auditing deletions by location and system

- **Priority:** Must
- **Sources:** `interview_cataloging_2009-05-08.txt`

Count and track record deletions by location and by system for auditing purposes; provide counts and reasons to assist troubleshooting if items go missing.

### REQ-171 — Deletion auditing for item and patron records

- **Priority:** Must
- **Sources:** `conversations/conv_pines022_deletions.eml`

The system shall implement a database trigger to log deletions of records (e.g., item records, patron records) to an audit table, recording record_type, record_id, deleted_by, deleted_at, and location, so that deletions can be audited and counted per location and per system.

### REQ-172 — Development/training environments with export/import

- **Priority:** Must
- **Sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`

Management Processes shall provide a development and training environment with the ability to migrate configurations to a production environment, including the export/import of report templates and configurations.

### REQ-173 — Fine-grained report permissions

- **Priority:** Must
- **Sources:** `email_report_features.eml`

There should be distinct, fine-grained permission levels limiting who can create and clone reports; admins should be able to create shared folders to allow or disallow staff from running specific reports, and/or to run ad hoc reports on specific data sets.

### REQ-174 — Fine-grained report permissions

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

System shall implement fine-grained permissions for reports, including control over who can create versus run reports, and support for permissions scoped to specific users or roles.

### REQ-175 — Fine-grained report permissions

- **Priority:** Must
- **Sources:** `survey_results_2009.txt`

System must enforce fine-grained permissions controlling who can create and clone reports.

### REQ-176 — High-level process descriptions

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

The developer must provide a thorough high-level description of major processes, including bibliographic record import and export, validation of bibliographic records against internal and external authority sources, and standard reports, to aid staff understanding of data movement through the system.

### REQ-177 — Immediate reflection of payments

- **Priority:** Must
- **Sources:** `email_financial_reports.eml`

When a patron makes a payment at the front desk, the system should reflect that financial update immediately.

### REQ-178 — Permission controls

- **Priority:** Must
- **Sources:** `conversations/conv_pines018_item_transfer.eml`

Restrict transfer capabilities to designated roles (managers, administrators, transfer coordinators).

### REQ-179 — Role-based access control and RBAC administration

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `email_staff_login.eml`, `interview_sysadmin_2009-05-10.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

User rights and privileges are controlled through security groups and/or roles that allow access control for individuals, workgroups, and arbitrary staff groups. Administrators shall be able to create and manage security groups/roles and assign them to staff members without modifying individual permissions. The system shall support assigning roles to individuals, workgroups, and arbitrary staff groups to control access. Access control shall be managed through security groups and/or roles to control permissions for individuals, workgroups, and arbitrary staff groups. The system must implement a RBAC model with roles such as Patron, Staff, Local Admin, and Global Admin, managed via security groups or roles, and allow easy administration and updates to user permissions by changing role assignments.

### REQ-180 — Separate confirmation step for deletions

- **Priority:** Must
- **Sources:** `conversations/conv_pines021_item_purging.eml`

There must be a separate confirmation step before any actual deletions are performed, to ensure deliberate action and prevent unintended data loss.

### REQ-181 — Separate development/training environments with migratable configurations

- **Priority:** Must
- **Sources:** `interview_sysadmin_2009-05-10.txt`

There must be separate development/test and training environments for reporting, with migration capability to production. The system must support export/import of report templates, permission settings, and other configurations so changes can be propagated.

### REQ-182 — Shared folders for report access control

- **Priority:** Must
- **Sources:** `survey_results_2009.txt`

The system must provide shared folders to allow or disallow staff from running specific reports.

### REQ-183 — Optional streamlined login

- **Priority:** Should
- **Sources:** `email_staff_login.eml`

The streamlined login method should be optional but available for libraries with the infrastructure to support card readers.

### REQ-184 — Preview before applying changes

- **Priority:** Should
- **Sources:** `conversations/conv_pines018_item_transfer.eml`

Before executing a transfer, the system should show a preview indicating how many items would be moved and to where, allowing confirmation prior to changes.

### REQ-185 — Publicized help and guidance for reports

- **Priority:** Should
- **Sources:** `evergreen_reference_2009.txt`

The system shall include online help or guidance integrated with the report interface to assist staff in creating and configuring reports.

### REQ-186 — Staff access control to tables and fields

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

Administrators should control staff access to tables and fields under the system’s access control mechanisms.

### REQ-187 — Staff login flexibility

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should support streamlined methods of logging into terminals (e.g., swipe card or username/password) and should not require card-based login, with traditional username/password as a fallback.

### REQ-188 — Track denied deletion attempts

- **Priority:** Should
- **Sources:** `conversations/conv_pines022_deletions.eml`

The system shall track attempts to delete records that are denied, so that audits can show both successful deletions and failed deletion attempts for compliance and troubleshooting.

### REQ-189 — Undo transfer operation

- **Priority:** Should
- **Sources:** `conversations/conv_pines018_item_transfer.eml`

Provide an undo function to revert a transfer if the wrong button was pressed or changes were made in error.

## Interoperability

### REQ-190 — Browser compatibility requirements

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `interview_sysadmin_2009-05-10.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

If web-browser based, the system must be accessible through Microsoft Internet Explorer (version 6.0 and later) and Mozilla Firefox (version 2.0 and later). The system should support IE6.0+ and Firefox 2.0+ across libraries, with alignment to IE/Firefox standards.

### REQ-191 — Cross-OS compatibility

- **Priority:** Must
- **Sources:** `interview_sysadmin_2009-05-10.txt`

The reporting system must work on both Red Hat Enterprise Linux 5 and Solaris 10 SPARC environments to support the main server and disaster recovery/reporting site.

### REQ-192 — OPAC integration with reporting

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

Management processes must interact with a patron interface (OPAC); reporting must be able to query patron data produced by the OPAC for holds and circulation data. These requirements shall not constrain functionality or features of the OPAC module, and management reporting changes should not affect patron access. The reporting system should query data from the OPAC but must not modify it.

### REQ-193 — Relational database compatibility

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `interview_sysadmin_2009-05-10.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

The reporting system must integrate with PostgreSQL as a fully relational database, avoiding denormalized reporting schemas due to synchronization issues, and operate within the main relational database structure. Management Processes shall use a fully relational database back-end to ensure the reporting layer works properly with the relational structure.

### REQ-194 — Standards-compliant HTML output

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

The system shall produce standards-compliant HTML for all web output, including report display, help system, and web-based UI components.

### REQ-195 — Web browser or Windows-compatible client access

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

The system must be accessible through a web browser or a Windows-compatible client to accommodate libraries preferring browser-based access or a dedicated client for performance.

## Performance and capacity

### REQ-196 — Auto-revert mechanism

- **Priority:** Must
- **Sources:** `conversations/conv_pines018_item_transfer.eml`

A scheduled mechanism that reverts transferred items to their original location after a set period of time and can also revert based on other criteria such as item status changes or being checked out at the destination.

### REQ-197 — Background processing for performance

- **Priority:** Must
- **Sources:** `conversations/conv_pines024_inactive_patrons.eml`

The system should run the inactive patrons query as a background process and cache results to avoid slow response times for large patron databases.

### REQ-198 — Background processing for reports

- **Priority:** Must
- **Sources:** `interview_sysadmin_2009-05-10.txt`

The reporting system must be able to queue and process complex reports in the background or operate with read-only reporting replicas so that searches and reports can be processed during open hours without disrupting other system functions, including the circulation client.

### REQ-199 — Comprehensive error reporting

- **Priority:** Must
- **Sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`

The system shall provide thorough high-level error reporting and feedback and shall allow low-level query-specific feedback for Local and Global System Administrators from the front-end interface, so staff can understand failures in reports.

### REQ-200 — Consortium capacity with performance considerations

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

The system must support a library consortium with 286 locations, 17 million annual circulations, and purchasing/processing over 900,000 items per year. It is highly desirable that searches and reports can be processed during open hours without disrupting other system functions. Management Processes must support a large, multiple-system library consortium with background processing/queuing to prevent report generation from slowing the circulation client during peak hours.

### REQ-201 — Historical Reporting / Data Warehouse

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `evergreen_reference_2009.txt`

The system shall provide historical reporting via a reporting warehouse to acquire data for a given date or date range. It shall support historical reporting and provide a reporting warehouse or equivalent mechanism to store and query past data independent from production data.

### REQ-202 — Linux or Solaris server environment

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

The system must operate on a Linux or Solaris server environment. Management Processes shall operate on a Linux or Solaris server, noting that most PINES installations use Linux but some larger systems use Solaris.

### REQ-203 — OPAC performance isolation

- **Priority:** Must
- **Sources:** `interview_sysadmin_2009-05-10.txt`

The management reporting system must be decoupled from the OPAC so that large reporting queries do not constrain or slow down patrons’ access to the catalog; the OPAC remains fast and responsive.

### REQ-204 — Queue priority for important reports

- **Priority:** Must
- **Sources:** `email_report_features.eml`

The system should allow important reports to jump ahead in the queue (priority-based queuing) to support timely access to critical analytics.

### REQ-205 — Separate reporting environment

- **Priority:** Must
- **Sources:** `evergreen_reference_2009.txt`

The system shall separate reporting from production operations, providing a development/training environment with migration capability and a separate reporting database or equivalent isolation.

### REQ-206 — Transaction history retention with aggregates

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `survey_results_2009.txt`

Transaction history is maintained for a configurable number of days, with monthly and annual aggregate information retained indefinitely.

### REQ-207 — Material volume reporting

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system shall have the ability to report the volume of material in a library at any point in time, based on new acquisitions, items on the shelf, and items in circulation, with breakdowns such as total items, number of holds, and category tallies.

### REQ-208 — Real-time Reporting

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system shall support real-time reporting.

### REQ-209 — Scheduling of purging utility

- **Priority:** Should
- **Sources:** `conversations/conv_pines021_item_purging.eml`

The purging utility should be schedulable so it can run automatically, for example at the end of each year, if configured.

### REQ-210 — System capacity interface

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system should provide an interface showing the capacity of all branches.

## Other

### REQ-211 — Centralized enterprise-wide management processing with multi-location support

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

Management processes are consolidated at a central location and accept input and provide services to multiple locations. They are part of an enterprise-level Library Automation System and rely on enterprise data structures and functionality, including Acquisitions and Cataloging modules.

### REQ-212 — Enterprise data dependencies

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

Management processes rely on the data structures and functionality of an enterprise-level Library Automation System, including Acquisitions and Cataloging modules.

### REQ-213 — Error reporting and admin feedback

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

The system must provide thorough high-level error reporting and feedback, and shall allow low-level query-specific feedback for Local and Global System Administrators from the front-end interface.

The system shall provide thorough high-level error reporting and feedback, and shall allow low-level, query-specific feedback for administrators to explain why a report failed with specifics (which table, which field, type of error).

### REQ-214 — Online help system and user guidance

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`, `interview_sysadmin_2009-05-10.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

The system must provide an online, hierarchical, and cross-linked help system in HTML that describes and illustrates all system functions. The help system should be online, hierarchical, cross-linked, and searchable; staff should be able to find guidance on running reports without contacting IT.

The system shall provide an online, hierarchical, cross-linked help system in HTML that is accessible to screen readers.

### REQ-215 — OPAC non-constraint of functionality

- **Priority:** Must
- **Sources:** `early_draft_srs_galecia.txt`

These requirements must not constrain functionality or features of the Online Public Access Catalog (OPAC) module.

### REQ-216 — Deletions tracking

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system shall have the ability to count and track record deletions, such as item records and patron records, per location and per system.

### REQ-217 — Development and training environment with migration to production

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

The system must provide a development and training environment that allows for the migration of configurations to a production environment.

### REQ-218 — Item record purging utilities and reports

- **Priority:** Should
- **Sources:** `early_draft_srs_galecia.txt`

Provide a utility and reports for identifying item records to purge based on customizable criteria, such as items missing for more than a specified number of months or with a status of discard/weed. This includes a report to assist in converting items between statuses and a last-copy report for catalogers, as well as facilitating the deletion of volume and copy entries and records with no items attached.

### REQ-219 — Scope constraint on patron-facing functions

- **Priority:** Could
- **Sources:** `meeting_minutes/meeting_2009-03-15_minutes.txt`

The scope of the group’s work explicitly excludes day-to-day patron-facing functions, such as the OPAC and circulation client, and focuses on Management Processes, including reports and analysis tools used by library managers, administrators, and staff.

### REQ-220 — Uncataloged material inventory control

- **Priority:** Could
- **Sources:** `early_draft_srs_galecia.txt`

Ability to control the inventory of uncataloged material, such as paperback books and children's board books, ensuring quick distribution, minimal branch labor, and usage identification, while including this material in circulation statistics and reports.

## Blacklist

Candidates removed because they duplicated another requirement, conflicted with a stronger one, or were not a real requirement.

### Discarded — Value of items report

- **Category:** Acquisitions
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-141

The system can generate a report of the value of items based on data in item records, e.g., value of all long-overdue items, value of all DVDs in children's collection, or value of the entire collection.

This requirement was discarded as it is a duplicate of REQ-141 (Value of items report), filed under a different category. The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Item transfer utility capabilities

- **Category:** Cataloging
- **Original sources:** `interview_cataloging_2009-05-08.txt`
- **Disposition:** Duplicate of REQ-004

The system must support transferring batches of items between branches, including: a) querying for candidate materials (e.g., all items in a given section not circulated in a set period), b) saving queries for repeated monthly use, c) manually selecting titles from query results, d) changing records of selected items to move them to a new location, and e) mechanisms to revert items back to their original location after a set period.

This requirement was discarded as it is a duplicate of REQ-004 (Batch transfer utility and last-copy reporting). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Last copy report per library and per system

- **Category:** Cataloging
- **Original sources:** `conversations/conv_pines021_item_purging.eml`
- **Disposition:** Duplicate of REQ-004

The system provides a "last copy" report that identifies an item’s last copies, with views available per library and per system, so catalogers can update WorldCat entries and avoid deleting the only copy within a scope.

This requirement was discarded because it duplicates the obligation of REQ-004 (Batch transfer utility and last-copy reporting). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Last copy report with WorldCat integration

- **Category:** Cataloging
- **Original sources:** `interview_cataloging_2009-05-08.txt`
- **Disposition:** Duplicate of REQ-004

Provide a report that singles out a library system’s last copies to assist catalogers editing WorldCat entries, preventing loss of rare books; system must support this critical reporting capability.

This requirement was discarded due to its duplication of REQ-004 (Batch transfer utility and last-copy reporting). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Templates management by department heads

- **Category:** Cataloging
- **Original sources:** `email_staff_login.eml`
- **Disposition:** Duplicate of REQ-134

Department heads role should be able to create and modify templates.

This requirement was discarded because it duplicates REQ-134 (Template and permissions management features), filed under a different category. The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Check-in type counting

- **Category:** Circulation
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-001

The system counts all types of check-in individually and cumulatively (book-drop, by terminal, by user or self-service).

This requirement was discarded because it duplicates REQ-001 (Count check-ins by type). The sources were consolidated into the surviving requirement, which had a stronger priority.

### Discarded — Check-out type counting

- **Category:** Circulation
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-002

The system counts all types of check-out individually and cumulatively (staff check-out, self check-out, staff renewal, self-checkout renewal, online renewal, OPAC renewal).

This requirement was discarded as it is a duplicate of REQ-002 (Count check-outs by type). The sources were united on the surviving requirement, which was prioritized higher.

### Discarded — Batch status conversion report

- **Category:** Holds
- **Original sources:** `conversations/conv_pines021_item_purging.eml`
- **Disposition:** Duplicate of REQ-014

Cataloging staff can generate a report to assist in converting items from one status to another in batch, e.g., changing 100 items from "missing" to "discard/weed" at once.

This requirement was discarded because it duplicates REQ-014 (Purging: batch status changes with configurable and combined criteria). The sources were combined into the surviving requirement, which had a stronger priority.

### Discarded — Holds and locations tracking

- **Category:** Holds
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-013

The system counts all hold requests, including how the hold was placed (staff desk, public computer inside the library, remotely).

This requirement was discarded because it duplicates REQ-013 (Hold placement tracking and method counting). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Support combining criteria in purging

- **Category:** Holds
- **Original sources:** `conversations/conv_pines021_item_purging.eml`
- **Disposition:** Duplicate of REQ-014

The purging capability should allow combining criteria, such as an item with status "missing" for more than 6 months AND hasn't circulated in 2 years, to form complex purge conditions.

This requirement was discarded as it is a duplicate of REQ-014 (Purging: batch status changes with configurable and combined criteria). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Browser compatibility

- **Category:** Interoperability
- **Original sources:** `interview_sysadmin_2009-05-10.txt`
- **Disposition:** Duplicate of REQ-190

The system must support Microsoft Internet Explorer 6.0+ and Firefox 2.0+ because libraries are standardized on IE and some locations use Firefox, and upgrading across 200+ library computers is impractical.

This requirement was discarded as it is a duplicate of REQ-190 (Browser compatibility requirements). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Online, hierarchical help system

- **Category:** Interoperability
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-193

The system shall provide an online, hierarchical, cross-linked help system in HTML that describes and illustrates all system functions, enabling context-sensitive help within the product.

This requirement was discarded because it duplicates REQ-193 (Relational database compatibility). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — OPAC data querying for reports

- **Category:** Interoperability
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-192

Management Processes interact with a patron interface (OPAC); reporting must be able to query patron data produced by the OPAC for holds and circulation data.

This requirement was discarded as it is a duplicate of REQ-192 (OPAC integration with reporting). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — OPAC independence for reporting

- **Category:** Interoperability
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-192

These requirements shall not constrain functionality or features of the Online Public Access Catalog (OPAC) module; management reporting changes should not affect patron access.

This requirement was discarded because it duplicates REQ-192 (OPAC integration with reporting). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Relational back-end for management data

- **Category:** Interoperability
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-193

Management Processes shall use a fully relational database back-end (e.g., PostgreSQL) to ensure reporting layer works properly with the relational structure.

This requirement was discarded as it is a duplicate of REQ-193 (Relational database compatibility). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Standards-compliant HTML output

- **Category:** Interoperability
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-194

Management Processes shall produce standards-compliant HTML for all web output, including report display, help system, and web-based UI components.

This requirement was discarded as it is a duplicate of REQ-194 (Standards-compliant HTML output). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Transaction data archiving with privacy

- **Category:** Interoperability
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-136

Transactions should be archived in a form that protects patron privacy as defined by State Law, while providing useful demographic statistics.

This requirement was discarded as it is a duplicate of REQ-136 (Transaction archive with privacy and retention), filed under a different category. The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Vendor data interfaces

- **Category:** Interoperability
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate

Management Processes interface with a variety of vendor websites via published APIs and/or automated transfer of standard-format data files (e.g., USMARC21, EDIFACT) to handle data from external sources for reporting.

This requirement was discarded because it duplicates the surviving requirement (Vendor data interfaces). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Vendor data interfaces

- **Category:** Interoperability
- **Original sources:** `early_draft_srs_galecia.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-142

Management Processes interface with a variety of vendor websites, via published APIs and/or automated transfer of standard-format data files (e.g., USMARC21, EDIFACT) to handle data from external sources for reporting.

This requirement was discarded because it duplicates REQ-142 (Vendor integration interfaces), filed under a different category. The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Web browser or Windows-compatible client access

- **Category:** Interoperability
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-195

Management Processes shall be accessible through a web-browser or a Windows-compatible client to accommodate libraries preferring browser-based access or a dedicated client for performance.

This requirement was discarded as it is a duplicate of REQ-195 (Web browser or Windows-compatible client access). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Web-browser compatibility requirements

- **Category:** Interoperability
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-190

If web-browser based, the system must be accessible through Microsoft Internet Explorer (version 6.0 and later) and Mozilla Firefox (version 2.0 and later).

This requirement was discarded because it duplicates REQ-190 (Browser compatibility requirements). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Accessibility compliance

- **Category:** Other
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-166

Management Processes shall be accessible with screen-reading software, screen-magnification software, and other assistive technologies (e.g., JAWS, NVDA, ZoomText) to meet Section 508 compliance mandatory for public institutions.

This requirement was discarded because it duplicates REQ-166 (Accessibility compliance), filed under a different category. The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Enterprise library integration

- **Category:** Other
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-211

Management Processes are part of an enterprise-level Library Automation System and are consolidated at a central location, accepting input and providing services to multiple locations.

This requirement was discarded as it is a duplicate of REQ-211 (Centralized enterprise-wide management processing with multi-location support). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Enterprise system placement

- **Category:** Other
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-211

Management Processes are part of an enterprise-level Library Automation System.

This requirement was discarded because it duplicates REQ-211 (Centralized enterprise-wide management processing with multi-location support). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Help system usability

- **Category:** Other
- **Original sources:** `interview_sysadmin_2009-05-10.txt`
- **Disposition:** Duplicate of REQ-214

The help system must be online, hierarchical, cross-linked, and searchable; staff should be able to find guidance on running reports without contacting IT.

This requirement was discarded because it duplicates REQ-214 (Online help system and user guidance). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — High-level process descriptions

- **Category:** Other
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-176

The developer must provide a thorough high-level description of major processes, including bibliographic record import and export, validation of bibliographic records against internal and external authority sources, and standard reports.

This requirement was discarded because it duplicates REQ-176 (High-level process descriptions), filed under a different category. The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Demographic statistics anonymized

- **Category:** Patrons
- **Original sources:** `survey_results_2009.txt`
- **Disposition:** Duplicate of REQ-015

System must provide demographic statistics including transactions by geographical regions and age ranges, with data anonymized.

This requirement was discarded as it is a duplicate of REQ-015 (Demographic statistics with anonymization (region and age ranges)). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Select Survey Name for Filtering

- **Category:** Patrons
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-133

The system shall allow filtering reports by selecting the survey name (not requiring a survey id).

This requirement was discarded as it is a duplicate of REQ-133 (Survey filtering by name), filed under a different category. The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Large library consortium capacity

- **Category:** Performance and capacity
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-200

Management Processes must support a large, multiple-system library consortium including 286 locations, 17 million annual circulations, and purchasing/processing over 900,000 items per year, with background processing/queuing to prevent report generation from slowing the circulation client during peak hours.

This requirement was discarded because it duplicates REQ-200 (Consortium capacity with performance considerations). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Linux or Solaris server requirement

- **Category:** Performance and capacity
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-202

Management Processes shall operate on a Linux or Solaris server, as agreed by the group, noting that most PINES installations use Linux but some larger systems use Solaris.

This requirement was discarded as it is a duplicate of REQ-202 (Linux or Solaris server environment). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Relational database back-end

- **Category:** Performance and capacity
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-193

The system must use a fully relational database back-end.

This requirement was discarded as it is a duplicate of REQ-193 (Relational database compatibility), filed under a different category. The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Reports queuing visibility

- **Category:** Performance and capacity
- **Original sources:** `email_report_features.eml`
- **Disposition:** Duplicate of REQ-121

Users should be able to see where their report is in the queue, including the number of reports ahead and the submission time, with status indicators (waiting, running, completed, failed).

This requirement was discarded as it is a duplicate of REQ-121 (Report queue visibility), filed under a different category. The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Transaction history retention and aggregates

- **Category:** Performance and capacity
- **Original sources:** `survey_results_2009.txt`
- **Disposition:** Duplicate of REQ-206

System must maintain transaction history for a configurable number of days, with monthly and annual aggregates retained indefinitely.

This requirement was discarded because it duplicates REQ-206 (Transaction history retention with aggregates). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Error reporting

- **Category:** Reports
- **Original sources:** `meeting_tech_subcommittee_2009-06-30.txt`
- **Disposition:** Duplicate of REQ-213

The system shall provide thorough high-level error reporting and feedback, and shall allow low-level, query-specific feedback for administrators to explain why a report failed with specifics (which table, which field, type of error).

This requirement was discarded as it is a duplicate of REQ-213 (Error reporting and admin feedback), filed under a different category. The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Historical and warehouse-style reporting

- **Category:** Reports
- **Original sources:** `evergreen_reference_2009.txt`
- **Disposition:** Duplicate of REQ-201

System shall support historical reporting and provide a reporting warehouse or equivalent mechanism to store and query past data independent from production data.

This requirement was discarded because it duplicates REQ-201 (Historical Reporting / Data Warehouse), filed under a different category. The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — In-transit items report with configurable threshold

- **Category:** Reports
- **Original sources:** `conversations/conv_pines019_020_missing_intransit.eml`
- **Disposition:** Duplicate of REQ-003

The system shall generate a list of items that have been in transit for more than X days (X configurable, defaults to 7 days) per branch and per system, and the report shall merge transit-to and transit-from data into a single report for frontline staff.

This requirement was discarded as it is a duplicate of REQ-003 (In-transit items reporting with configurable days), filed under a different category. The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Online help system

- **Category:** Reports
- **Original sources:** `meeting_tech_subcommittee_2009-06-30.txt`
- **Disposition:** Duplicate of REQ-214

The system shall provide an online, hierarchical, cross-linked help system in HTML that is accessible to screen readers.

This requirement was discarded as it is a duplicate of REQ-214 (Online help system and user guidance), filed under a different category. The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — OPAC integration"

- **Category:** Reports
- **Original sources:** `meeting_tech_subcommittee_2009-06-30.txt`
- **Disposition:** Duplicate of REQ-192

The reporting system should query data from the OPAC (patron interface) but must not modify it.

This requirement was discarded because it duplicates REQ-192 (OPAC integration with reporting), filed under a different category. The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Relational database back-end

- **Category:** Reports
- **Original sources:** `meeting_tech_subcommittee_2009-06-30.txt`
- **Disposition:** Duplicate of REQ-193

The reporting system must use a fully relational database back-end; PostgreSQL is the current choice for PINES and the reporting system must work WITH the relational structure, not against it.

This requirement was discarded because it duplicates REQ-193 (Relational database compatibility), filed under a different category. The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Shelf space estimation method

- **Category:** Reports
- **Original sources:** `conversations/conv_pines016_shelf_space.eml`
- **Disposition:** Duplicate of REQ-127

The system shall estimate shelf space per genre/format because shelf space is not directly tracked in the database, by either using item dimensions as a basis or by using item count as a proxy, to produce the percentage of shelf space figures.

This requirement was discarded as it is a duplicate of REQ-127 (Shelf space reporting and estimation by genre/format). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Shelf space reporting by genre/format

- **Category:** Reports
- **Original sources:** `early_draft_srs_galecia.txt`
- **Disposition:** Duplicate of REQ-127

For each genre and format, the system should report the percentage of total circulations, the percentage of the collection, and the percentage of total shelf space, per library and per system.

This requirement was discarded because it duplicates REQ-127 (Shelf space reporting and estimation by genre/format). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Shelf space reporting by genre/format

- **Category:** Reports
- **Original sources:** `interview_cataloging_2009-05-08.txt`
- **Disposition:** Duplicate of REQ-127

Provide a shelf space report that, for each genre and format, shows percentage of total circulations, percentage of the collection, and percentage of total shelf space to aid decisions on resource allocation.

This requirement was discarded as it is a duplicate of REQ-127 (Shelf space reporting and estimation by genre/format). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Administrators manage roles

- **Category:** Staff, administration, and security
- **Original sources:** `email_staff_login.eml`
- **Disposition:** Duplicate of REQ-179

Administrators shall be able to create and manage security groups/roles and assign them to staff members without modifying individual permissions.

This requirement was discarded because it duplicates REQ-179 (Role-based access control and RBAC administration). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Dual login support

- **Category:** Staff, administration, and security
- **Original sources:** `email_staff_login.eml`
- **Disposition:** Duplicate of REQ-179

System shall support streamlined staff login methods (e.g., card swipe) and traditional login (individual username/password) for staff members.

This requirement was discarded as it is a duplicate of REQ-179 (Role-based access control and RBAC administration). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Non-requirement of streamlined login

- **Category:** Staff, administration, and security
- **Original sources:** `email_staff_login.eml`
- **Disposition:** Duplicate of REQ-179

The system should not require the streamlined login method; some branches may not have card reader infrastructure.

This requirement was discarded because it duplicates REQ-179 (Role-based access control and RBAC administration). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Role assignment scope

- **Category:** Staff, administration, and security
- **Original sources:** `email_staff_login.eml`
- **Disposition:** Duplicate of REQ-179

The system shall support assigning roles to individuals, workgroups, and arbitrary staff groups to control access.

This requirement was discarded as it is a duplicate of REQ-179 (Role-based access control and RBAC administration). The sources were merged into the surviving requirement, which was deemed more important.

### Discarded — Role-based access control

- **Category:** Staff, administration, and security
- **Original sources:** `email_staff_login.eml`
- **Disposition:** Duplicate of REQ-179

Access control shall be managed through security groups and/or roles to control permissions for individuals, workgroups, and arbitrary staff groups.

This requirement was discarded because it duplicates REQ-179 (Role-based access control and RBAC administration). The sources were united on the surviving requirement, which had a stronger priority.

### Discarded — Role-based access control

- **Category:** Staff, administration, and security
- **Original sources:** `interview_sysadmin_2009-05-10.txt`
- **Disposition:** Duplicate of REQ-179

The system must implement a RBAC model with roles such as Patron, Staff, Local Admin, and Global Admin, managed via security groups or roles, and allow easy administration and updates to user permissions by changing role assignments.

This requirement was discarded as it is a duplicate of REQ-179 (Role-based access control and RBAC administration). The sources were combined into the surviving requirement, which was prioritized higher.

### Discarded — Role-based access control

- **Category:** Staff, administration, and security
- **Original sources:** `meeting_minutes/meeting_2009-07-20_minutes.txt`
- **Disposition:** Duplicate of REQ-179

User rights and privileges shall be controlled through security groups and/or roles that allow access control for individuals, workgroups, and arbitrary staff groups.

This requirement was discarded because it duplicates REQ-179 (Role-based access control and RBAC administration). The sources were merged into the surviving requirement, which was deemed more important.

## Appendix: documents reviewed

Coverage loop ran 1 time(s), including the first pass. Retry budget after that pass: 2.

| Document | Type | Date | Outcome |
| --- | --- | --- | --- |
| `conversations/conv_pines014_material_volume.eml` | email | 2009-04-06 | 4 requirements. This is an email thread discussing requirements for a library volume reporting system. |
| `conversations/conv_pines015_capacity_interface.eml` | email | 2009-04-08 | 1 requirement. This is an email thread discussing the need for a system capacity interface for library branches. |
| `conversations/conv_pines016_shelf_space.eml` | email | 2009-04-13 | 1 requirement. This is an email thread discussing requirements for a shelf space usage report in a library system. |
| `conversations/conv_pines018_item_transfer.eml` | email | 2009-05-11 | 8 requirements. This is an email thread discussing requirements and design considerations for a library item transfer utility. |
| `conversations/conv_pines019_020_missing_intransit.eml` | email | 2009-04-16 | 3 requirements. This is an email thread discussing requirements for missing, damaged, and in-transit item reports in a library system. |
| `conversations/conv_pines021_item_purging.eml` | email | 2009-04-21 | 7 requirements. This is an email thread discussing requirements for library item purging reports and utilities. |
| `conversations/conv_pines022_deletions.eml` | email | 2009-04-24 | 3 requirements. This is an email thread discussing the need for tracking record deletions in a library system for auditing and accountability purposes. |
| `conversations/conv_pines023_patron_characteristics.eml` | email | 2009-04-29 | 5 requirements. A thread of emails discussing requirements for patron demographic reports in a library system. |
| `conversations/conv_pines024_inactive_patrons.eml` | email | 2009-05-05 | 8 requirements. This is an email thread discussing requirements for an inactive patrons report in a library system. |
| `early_draft_srs_galecia.txt` | specification | 2009-01-27 | 111 requirements. This is a draft software requirements specification for the management processes of an integrated library system. |
| `email_financial_reports.eml` | email | 2009-07-13 | 11 requirements. This is an email thread discussing financial reporting requirements for a library system. |
| `email_report_features.eml` | email | 2009-07-27 | 8 requirements. A series of emails discussing report features and interface requirements for a library system. |
| `email_staff_login.eml` | email | 2009-04-09 | 6 requirements. This document is an email thread discussing staff login methods and access control requirements for a library system. |
| `evergreen_reference_2009.txt` | reference | 2009-03-15 | 14 requirements. This document provides an overview of the Evergreen ILS reporting capabilities, gaps, and limitations. |
| `interview_cataloging_2009-05-08.txt` | interview | 2009-05-08 | 10 requirements. This document is an interview with a senior cataloger discussing requirements for library reporting and management tools. |
| `interview_sysadmin_2009-05-10.txt` | interview | 2009-05-10 | 9 requirements. An interview with a senior systems administrator discussing technical requirements for a library management reporting system. |
| `meeting_minutes/meeting_2009-03-15_minutes.txt` | decision | 2009-03-15 | 4 requirements. The document is minutes from the first meeting of the PINES Reports Working Group discussing their scope, mission, and next steps. |
| `meeting_minutes/meeting_2009-07-20_minutes.txt` | decision | 2009-07-20 | 15 requirements. This document is minutes from a PINES Reports Working Group meeting discussing project updates and decisions. |
| `meeting_tech_subcommittee_2009-06-30.txt` | decision | 2009-06-30 | 18 requirements. The document records the minutes of a PINES technical subcommittee meeting discussing system architecture and implementation details. |
| `survey_results_2009.txt` | survey | 2009-04-25 | 12 requirements. This document summarizes the results of a PINES staff survey on report usage and requirements. |

## Uncovered documents

Every document is covered by at least one requirement that cites it, or by an explicit reason that it states no requirement.
