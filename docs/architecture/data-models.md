# Data Models

## Company
**Purpose:** Core entity representing a UK registered company

**Key Attributes:**
- `company_number`: str - Unique 8-character identifier
- `company_name`: str - Registered company name
- `company_status`: str - Active, dissolved, liquidation, etc.
- `date_of_creation`: date - Company incorporation date
- `jurisdiction`: str - Registration jurisdiction
- `sic_codes`: List[str] - Standard Industrial Classification codes
- `registered_office_address`: Address - Official company address
- `accounts`: AccountingReference - Accounting reference dates
- `confirmation_statement`: ConfirmationStatement - Annual confirmation info

**Relationships:**
- Has many Officers
- Has many FilingHistory entries
- Has many Charges
- Has many PersonsWithSignificantControl

## Officer
**Purpose:** Represents a company director, secretary, or other officer

**Key Attributes:**
- `officer_id`: str - Unique officer identifier
- `name`: str - Officer's full name
- `officer_role`: str - Director, secretary, etc.
- `appointed_on`: date - Appointment date
- `resigned_on`: Optional[date] - Resignation date if applicable
- `date_of_birth`: PartialDate - Month/year only for privacy
- `nationality`: str - Officer's nationality
- `occupation`: str - Stated occupation
- `address`: Address - Service address

**Relationships:**
- Belongs to Company (via appointments)
- Has many Appointments across companies
- May have Disqualifications

## SearchResult
**Purpose:** Container for search operation results

**Key Attributes:**
- `items`: List[Union[Company, Officer]] - Search result items
- `total_results`: int - Total matches found
- `items_per_page`: int - Pagination size
- `start_index`: int - Starting position
- `kind`: str - Type of search results

**Relationships:**
- Contains Companies or Officers depending on search type
- Used by search_all for pagination

## Address
**Purpose:** Standardized address representation

**Key Attributes:**
- `premises`: Optional[str] - Building name/number
- `address_line_1`: str - First line of address
- `address_line_2`: Optional[str] - Second line of address
- `locality`: Optional[str] - Town/city
- `region`: Optional[str] - County/state
- `postal_code`: Optional[str] - Postcode
- `country`: Optional[str] - Country name

**Relationships:**
- Used by Company (registered office)
- Used by Officer (service address)
- Embedded in many other models

## FilingHistory
**Purpose:** Record of documents filed with Companies House

**Key Attributes:**
- `transaction_id`: str - Unique filing identifier
- `category`: str - Filing category (accounts, confirmation-statement, etc.)
- `date`: date - Filing date
- `description`: str - Filing description
- `type`: str - Specific document type
- `links`: Dict - URLs to document resources

**Relationships:**
- Belongs to Company
- May link to Document

## PersonWithSignificantControl
**Purpose:** Individual or entity with significant control over company

**Key Attributes:**
- `psc_id`: str - Unique PSC identifier
- `name`: str - PSC name
- `kind`: str - Individual, corporate entity, etc.
- `natures_of_control`: List[str] - Types of control held
- `notified_on`: date - Date notified to Companies House
- `ceased_on`: Optional[date] - Date control ceased
- `address`: Address - PSC address

**Relationships:**
- Belongs to Company
- May be linked to Officer (if director)

## RateLimitInfo
**Purpose:** Track API rate limiting status

**Key Attributes:**
- `remain`: int - Remaining requests in window
- `limit`: int - Total requests allowed
- `reset`: datetime - When limit resets
- `retry_after`: Optional[int] - Seconds to wait if rate limited

**Relationships:**
- Used by AsyncClient for retry logic
- Extracted from HTTP response headers