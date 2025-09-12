# Feature Specification: Multi-Portfolio Performance Dashboard with Email Transaction Processing

**Feature Branch**: `001-portfolio-performance-dashboard`  
**Created**: 2025-09-12  
**Status**: Draft  
**Input**: User description: "Portfolio performance dashboard with interactive charts showing asset allocation, performance metrics, and historical data visualization + email monitoring for broker transaction receipts"

## Execution Flow (main)

```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines

- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

When creating this spec from a user prompt:

1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

As an investor managing multiple share portfolios with collaborative access, I need a secure intelligent portfolio management system with user authentication and permission management that uses extensible agentic workflows powered by configurable AI providers (internal like Ollama or external like OpenAI) to automatically track my transactions from broker emails, monitor dividend payments, update daily closing prices, discover and archive relevant news articles, analyze stock data to provide buy/sell/hold recommendations, perform portfolio-level analysis for rebalancing and risk management, and provide comprehensive performance dashboards with annual financial reporting and API access, so I can have my portfolios automatically maintained with complete income and capital gains data plus AI-powered investment insights and portfolio optimization recommendations for informed decision-making while allowing trusted users to collaborate on portfolio management.

### Acceptance Scenarios

1. **Given** I am a new user, **When** I access the application, **Then** I can create an account and log in securely to access my portfolio dashboard
2. **Given** I am logged in, **When** I access my account settings, **Then** I can manage my profile, email configurations, and generate API keys for third-party access
3. **Given** I am logged in, **When** I receive a broker transaction email, **Then** the system monitors my inbox and automatically extracts transaction details to update my relevant portfolio
4. **Given** I have multiple share portfolios, **When** I access the dashboard, **Then** I see an overview of all my portfolios with their total values and performance metrics
5. **Given** I select a specific portfolio, **When** I view its details, **Then** I see interactive charts showing asset allocation and individual stock performance with rise/fall indicators for each stock
6. **Given** I want to verify transactions, **When** I view transaction history, **Then** I can see all automatically processed transactions with their source emails
7. **Given** it's after market close, **When** the daily price update runs, **Then** all stock positions are updated with current closing prices and portfolio values recalculated
8. **Given** I want to compare portfolios, **When** I select multiple portfolios, **Then** I can view comparative performance metrics side by side
9. **Given** I have historical data, **When** I interact with time-series charts, **Then** I can filter by date ranges and see portfolio value changes over time
10. **Given** individual stocks in my portfolio have price changes, **When** I view the portfolio summary, **Then** I can see how each stock's gain/loss contributes to the overall portfolio performance
11. **Given** I receive dividend payments, **When** the system detects dividend notifications, **Then** it automatically records the dividend income against the relevant stock and portfolio
12. **Given** I want to view my annual performance, **When** I access the financial year report, **Then** I see total income from dividends, capital gains/losses, and overall portfolio performance for tax reporting
13. **Given** relevant news exists for my portfolio stocks, **When** the daily price update runs, **Then** the system discovers, downloads, and archives news articles in paperless-ngx with intelligent tagging
14. **Given** I view a specific stock in the UI, **When** I access its details, **Then** I can see linked news articles and documents from paperless-ngx related to that stock
15. **Given** I access the portfolio dashboard from any device, **When** I view the interface, **Then** I see a clean, modern design that adapts responsively to my screen size
16. **Given** I interact with charts and data visualizations, **When** I hover, click, or scroll, **Then** the interface responds dynamically with smooth animations and real-time updates
17. **Given** I am a developer or third-party integrator, **When** I access the API documentation, **Then** I can find well-documented RESTful endpoints for all portfolio management operations
18. **Given** I want to integrate with external systems, **When** I make API requests with my generated API key, **Then** I receive standardized JSON responses with proper HTTP status codes and error handling
19. **Given** a stock in my portfolio has a corporate action like a split or trading halt, **When** the system detects this status change, **Then** it automatically updates the stock information and notifies me of the action
20. **Given** I view my portfolio, **When** any stocks have special status conditions, **Then** I can see clear indicators showing trading halts, splits, or other corporate actions
21. **Given** the intelligent agent has analyzed my stocks, **When** I view stock details, **Then** I see AI-generated buy/sell/hold recommendations with reasoning based on news and financial analysis
22. **Given** I want investment guidance, **When** I access the recommendations dashboard, **Then** I can view all current AI recommendations across my portfolio with confidence scores and analysis summaries
23. **Given** my portfolio has been analyzed at regular intervals, **When** I view the portfolio analysis report, **Then** I see sector allocation analysis, risk metrics, and rebalancing recommendations
24. **Given** the portfolio manager detects sector overconcentration or risk imbalances, **When** I access risk management recommendations, **Then** I receive specific suggestions for portfolio rebalancing and diversification strategies
25. **Given** I want to customize my portfolio analysis, **When** I access the portfolio settings interface, **Then** I can define target sector allocations, risk tolerance levels, and rebalancing thresholds through the UI
26. **Given** I have configured my rebalancing parameters, **When** the system performs portfolio analysis, **Then** it uses my custom settings to generate personalized rebalancing recommendations
27. **Given** I am a portfolio owner, **When** I want to share access with other users, **Then** I can invite users and assign them specific permission levels (view-only, edit, or admin) for my portfolio
28. **Given** I have been granted access to a shared portfolio, **When** I log in, **Then** I can view and interact with the portfolio according to my assigned permission level
29. **Given** I am an administrator, **When** I access AI provider settings, **Then** I can configure and switch between different AI providers (Ollama, OpenAI, etc.) and manage their API configurations
30. **Given** the system uses agentic workflows for automation, **When** I view workflow status, **Then** I can see the current AI provider being used and the status of automated analysis tasks
31. **Given** an agentic workflow encounters an error, **When** the failure is detected early, **Then** the system fails gracefully without affecting other portfolio functions and provides clear error reporting
32. **Given** AI systems are generating analysis or recommendations, **When** the system detects potential hallucinations or false data, **Then** it implements validation checks and flags questionable results for human review
33. **Given** I am an administrator or auditor, **When** I need to review system activity, **Then** I can access comprehensive logs and audit trails showing all user actions, system processes, and data modifications
34. **Given** a security incident or compliance review occurs, **When** investigators examine the audit trail, **Then** they can trace all actions back to specific users, timestamps, and system components with complete accountability
35. **Given** I need to evaluate portfolio performance, **When** I access performance reports, **Then** I can view industry-standardized metrics including Sharpe ratio, alpha, beta, maximum drawdown, and other recognized performance indicators
36. **Given** I want to benchmark my portfolio, **When** I generate performance reports, **Then** I can compare my portfolio against relevant market indices and peer portfolios using standardized metrics
37. **Given** I want to monitor potential investment opportunities, **When** I create a watchlist, **Then** I can add stocks to track their performance, news, and AI recommendations without purchasing them
38. **Given** I have stocks on my watchlist, **When** I view the watchlist dashboard, **Then** I see price movements, news alerts, and AI buy/sell signals for all monitored stocks
39. **Given** a remote service (price data, AI provider, news source) times out, **When** the system detects the timeout, **Then** it implements exponential backoff retry mechanisms before failing gracefully
40. **Given** a broker email cannot be parsed automatically, **When** the parsing fails, **Then** the system flags the email for human intervention and notifies the user for manual review and processing
41. **Given** a PDF document (statements, trade confirmations, reports) cannot be parsed automatically, **When** the parsing fails, **Then** the system flags the document for human intervention and provides tools for manual data extraction
42. **Given** duplicate transactions are detected from multiple sources, **When** the system processes them, **Then** it resolves duplicates using the latest timestamp and maintains a complete history of all received transactions for human review
43. **Given** a workflow is processing data (transactions, analysis, updates), **When** any step in the workflow fails, **Then** the system prevents partial data commits, rolls back to the previous consistent state, and alerts humans of the failure for intervention

### Edge Cases

- What happens when an email cannot be parsed or contains ambiguous transaction information? (System flags for human intervention)
- How are flagged emails prioritized when multiple parsing failures occur simultaneously?
- What interface do users have for manually processing flagged emails?
- How does the system learn from manual corrections to improve future parsing accuracy?
- What happens to portfolio data when flagged emails remain unprocessed for extended periods?
- How does the system handle PDF documents with poor scan quality or corrupted text?
- What happens when PDF documents contain mixed content types (text, tables, images)?
- How are scanned PDF documents processed differently from text-based PDFs?
- What tools are provided for manual PDF data extraction when automatic parsing fails?
- How does the system prioritize PDF document processing failures alongside email failures?
- How does the system determine which transactions are duplicates across different sources (email, PDF, manual entry)?
- What happens when duplicate transactions have different details but similar timestamps?
- How is the transaction history interface organized for human review of duplicate resolution decisions?
- How does the system handle transaction corrections that arrive after duplicates have been resolved?
- What criteria are used beyond timestamp for duplicate transaction identification?
- How does the system handle rollback scenarios when workflows fail partway through complex multi-step operations?
- What happens when database transactions conflict during concurrent workflow executions?
- How are workflow rollbacks managed when external systems have already been updated?
- What alerting mechanisms notify humans when workflows fail and require intervention?
- How does the system handle scenarios where confidence calculations return conflicting high and low confidence values for the same analysis?
- What happens when confidence calculation factors are missing or unavailable for certain data points?
- How does the system explain confidence calculations when multiple AI providers contribute different confidence levels?
- What fallback mechanisms exist when confidence explanation systems themselves fail?
- How are confidence thresholds adjusted when validation factors become unreliable or outdated?
- How does the system prioritize workflow failure alerts when multiple failures occur simultaneously?
- How does the system handle duplicate transaction emails or corrections from brokers?
- What occurs when the email format from a broker changes?
- How are failed email parsing attempts logged and handled?
- What happens when portfolio data is empty or unavailable?
- How does the system handle missing historical data for certain time periods?
- What occurs when stock values are negative or show extreme volatility?
- How are very small stock positions (< 1%) displayed in charts?
- What happens when a user has no portfolios or a portfolio has no stocks?
- How does the system handle emails from unknown or new brokers?
- What happens when daily price data is unavailable or delayed?
- How are market holidays and weekends handled for price updates?
- What occurs when a stock symbol is delisted or no longer tradeable?
- How are dividend reinvestments handled and tracked?
- What happens when dividend amounts are corrected or reversed by the broker?
- How does the system handle international dividends with currency conversion?
- What occurs when financial year dates vary by jurisdiction?
- How does the system handle duplicate news articles or similar content?
- What happens when paperless-ngx is unavailable or connection fails?
- How are news articles filtered for relevance to specific stocks?
- What occurs when news sources change format or become unavailable?
- How does the system handle news in different languages or from international sources?
- How does the API handle authentication and authorization for different user roles?
- What happens when API rate limits are exceeded?
- How are API versioning and backward compatibility managed?
- What occurs when the API encounters invalid or malformed requests?
- How does the system handle failed login attempts and account lockouts?
- What happens when a user forgets their password or needs account recovery?
- How are inactive user sessions and API keys managed?
- What occurs when multiple users attempt to access the same email account for transaction parsing?
- How does the system handle stock splits and adjust historical data and position quantities?
- What happens when a stock is halted for extended periods or permanently delisted?
- How are complex corporate actions like mergers or spin-offs handled?
- What occurs when corporate action data is delayed or incorrect?
- How does the AI agent handle conflicting signals from news sentiment and financial metrics?
- What happens when the AI analysis service is unavailable or produces errors?
- How are AI recommendation confidence scores calculated and validated?
- What occurs when financial data is incomplete or outdated for analysis?
- How does the system handle liability and disclaimers for AI-generated investment advice?
- How does the portfolio analyzer handle portfolios with insufficient diversification?
- What happens when sector classifications change or stocks move between sectors?
- How are industry-standard portfolio analysis intervals configured and managed?
- What occurs when rebalancing recommendations conflict with recent user transactions?
- How does the system handle risk tolerance preferences and custom risk parameters?
- What happens when multiple users with edit permissions make conflicting changes to portfolio settings?
- How are user permissions managed when the portfolio owner account is deactivated?
- What occurs when a user loses access permissions while actively using the portfolio?
- How does the system handle invitation conflicts when inviting existing users to portfolios?
- How are audit trails maintained for multi-user portfolio modifications?
- What happens when the configured AI provider becomes unavailable or rate-limited?
- How does the system handle switching between AI providers with different API formats?
- What occurs when agentic workflows fail or produce conflicting results from different providers?
- How are AI provider costs and usage monitored and managed?
- How does the system handle different AI model capabilities and limitations across providers?
- What happens when workflow timeouts occur during critical analysis periods?
- How does the system recover when circuit breakers are triggered due to workflow failures?
- How are partial workflow failures handled without corrupting data integrity?
- How does the system detect and handle AI hallucinations in financial data analysis?
- What happens when AI-generated stock recommendations contradict factual market data?
- How are confidence scores validated to prevent overconfident false recommendations?
- What validation mechanisms prevent AI from generating non-existent stock symbols or companies?
- How does the system handle conflicting information between AI analysis and verified data sources?
- How are sensitive audit logs protected from unauthorized access or tampering?
- What happens when logging systems become unavailable or storage reaches capacity?
- How does the system handle log retention policies and automatic archiving?
- How are audit trails maintained during system upgrades or maintenance windows?
- What logging mechanisms exist for tracking cross-system integrations and external API calls?
- How does the system handle performance metric calculations when historical data is incomplete?
- What happens when benchmark indices are unavailable or delisted?
- How are performance metrics adjusted for different time zones and market holidays?
- How does the system handle performance calculations for portfolios with frequent rebalancing?
- What standardization is used when comparing portfolios with different base currencies?
- How does the system handle duplicate stocks being added to multiple watchlists?
- What happens when watchlist stocks are delisted or cease trading?
- How are watchlist alerts managed when users have many monitored stocks?
- How does the system handle watchlist performance when market data feeds are unavailable?
- What limits exist on the number of stocks that can be added to watchlists?
- How does the system handle cascading timeouts when multiple remote services are unavailable?
- What happens when backoff retry attempts exceed maximum retry limits?
- How are timeout thresholds adjusted for different types of remote services?
- How does the system prioritize retry attempts when multiple services are timing out simultaneously?
- What fallback mechanisms exist when all retry attempts fail for critical services?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide secure user registration and login functionality
- **FR-002**: System MUST implement password security requirements and validation
- **FR-003**: System MUST provide user profile management including email configuration
- **FR-004**: System MUST allow users to generate, manage, and revoke API keys through account settings
- **FR-005**: System MUST implement session management with configurable timeout periods
- **FR-006**: System MUST provide password reset and account recovery functionality
- **FR-007**: System MUST ensure data isolation and permission-based access to portfolios and data
- **FR-008**: System MUST support multiple users accessing a single portfolio with different permission levels
- **FR-009**: System MUST provide portfolio sharing functionality with user invitation system
- **FR-010**: System MUST implement role-based permissions (owner, admin, edit, view-only) for portfolio access
- **FR-011**: System MUST maintain audit trails for all multi-user portfolio modifications and access
- **FR-012**: System MUST handle permission conflicts and provide clear access control hierarchy
- **FR-013**: System MUST implement extensible agentic workflows for automation and data analysis tasks
- **FR-014**: System MUST provide a well-defined interface for AI providers with standardized request/response formats
- **FR-015**: System MUST support internal AI models (Ollama) and external AI services (OpenAI, Anthropic, etc.)
- **FR-016**: System MUST allow dynamic switching between AI providers through configuration
- **FR-017**: System MUST implement fallback mechanisms when primary AI providers are unavailable
- **FR-018**: System MUST track AI provider usage, costs, and performance metrics
- **FR-019**: System MUST provide administrative interface for managing AI provider configurations
- **FR-020**: System MUST implement early detection of workflow failures with timeout and health checks
- **FR-021**: System MUST fail gracefully when workflows encounter errors, maintaining system stability
- **FR-022**: System MUST provide detailed logging and alerting for workflow failures and recovery actions
- **FR-023**: System MUST implement circuit breaker patterns to prevent cascading workflow failures
- **FR-024**: System MUST implement hallucination detection mechanisms to identify potentially false AI-generated content
- **FR-025**: System MUST validate AI-generated stock symbols, company names, and financial data against authoritative sources
- **FR-026**: System MUST cross-reference AI recommendations with factual market data and flag inconsistencies
- **FR-027**: System MUST implement confidence score validation to prevent overconfident false recommendations
- **FR-028**: System MUST require human review for AI-generated content flagged as potentially inaccurate
- **FR-029**: System MUST maintain a blacklist of known hallucination patterns and filter AI outputs accordingly
- **FR-030**: System MUST provide transparency indicators showing which data is AI-generated vs. factual
- **FR-031**: System MUST implement comprehensive logging for all user actions, system processes, and data modifications
- **FR-032**: System MUST maintain detailed audit trails with user identification, timestamps, IP addresses, and action details
- **FR-033**: System MUST log all API requests and responses with request/response payloads and status codes
- **FR-034**: System MUST provide tamper-proof audit logs with cryptographic integrity protection
- **FR-035**: System MUST implement configurable log retention policies with automated archiving and purging
- **FR-036**: System MUST enable real-time log monitoring with alerting for security and compliance violations
- **FR-037**: System MUST provide audit log search and filtering capabilities for investigation and compliance reporting
- **FR-038**: System MUST maintain audit trails during system maintenance, upgrades, and failover scenarios
- **FR-039**: System MUST calculate and report industry-standardized performance metrics including Sharpe ratio, alpha, beta, and information ratio
- **FR-040**: System MUST provide risk-adjusted performance metrics including maximum drawdown, volatility, and Value at Risk (VaR)
- **FR-041**: System MUST support benchmark comparisons against market indices (S&P 500, NASDAQ, sector indices)
- **FR-042**: System MUST calculate time-weighted and money-weighted returns following industry standards (GIPS compliance)
- **FR-043**: System MUST provide performance attribution analysis breaking down returns by asset allocation and security selection
- **FR-044**: System MUST generate standardized performance reports for different time periods (1M, 3M, 6M, 1Y, 3Y, 5Y, inception)
- **FR-045**: System MUST handle multi-currency portfolio performance calculations with appropriate currency hedging adjustments
- **FR-046**: System MUST provide peer group comparisons and percentile rankings for portfolio performance
- **FR-047**: System MUST provide watchlist functionality for tracking potential stocks without purchasing them
- **FR-048**: System MUST allow users to create, manage, and organize multiple watchlists with custom names
- **FR-049**: System MUST apply all analysis features (price tracking, news monitoring, AI recommendations) to watchlist stocks
- **FR-050**: System MUST provide watchlist-specific dashboards showing price movements, alerts, and signals for monitored stocks
- **FR-051**: System MUST enable easy transfer of stocks from watchlists to actual portfolio purchases
- **FR-052**: System MUST support watchlist alerts and notifications for significant price movements or news events
- **FR-053**: System MUST allow watchlist sharing between users with appropriate permission controls
- **FR-054**: System MUST implement configurable timeout thresholds for all remote service calls
- **FR-055**: System MUST implement exponential backoff retry mechanisms with jitter to prevent thundering herd problems
- **FR-056**: System MUST provide different retry strategies for different types of remote services (critical vs. non-critical)
- **FR-057**: System MUST implement maximum retry limits to prevent infinite retry loops
- **FR-058**: System MUST log all timeout events and retry attempts for monitoring and debugging
- **FR-059**: System MUST provide fallback mechanisms when remote services become persistently unavailable
- **FR-060**: System MUST implement request queuing and rate limiting to prevent overwhelming recovering services
- **FR-061**: System MUST flag unparseable emails for human intervention when automatic parsing fails
- **FR-062**: System MUST provide notifications to users when emails require manual review and processing
- **FR-063**: System MUST provide a user interface for manually reviewing and processing flagged emails
- **FR-064**: System MUST allow users to correct parsing errors and manually extract transaction data
- **FR-065**: System MUST learn from manual corrections to improve future email parsing accuracy
- **FR-066**: System MUST maintain a queue of flagged emails with priority levels and aging information
- **FR-067**: System MUST flag unparseable PDF documents for human intervention when automatic parsing fails
- **FR-068**: System MUST provide OCR capabilities for processing scanned PDF documents
- **FR-069**: System MUST provide tools for manual PDF data extraction including table recognition and text selection
- **FR-070**: System MUST handle mixed content PDFs with text, tables, and image-based data
- **FR-071**: System MUST learn from manual PDF corrections to improve future document parsing accuracy
- **FR-072**: System MUST maintain a unified queue for both email and PDF document review tasks
- **FR-073**: System MUST detect duplicate transactions across all input sources (email, PDF, manual entry)
- **FR-074**: System MUST resolve duplicate transactions by prioritizing the latest timestamp when duplicates are identified
- **FR-075**: System MUST maintain complete history of all received transactions including duplicates and rejected entries
- **FR-076**: System MUST provide transaction history interface for human review of duplicate resolution decisions
- **FR-077**: System MUST allow manual override of automatic duplicate resolution when human intervention is required
- **FR-078**: System MUST track transaction source metadata (email, PDF document, manual entry) for audit purposes
- **FR-079**: System MUST implement atomic transaction processing to prevent partial data commits during workflow execution
- **FR-080**: System MUST provide rollback mechanisms to restore previous consistent state when workflows fail
- **FR-081**: System MUST ensure all data modifications within a workflow are committed as a single atomic operation
- **FR-082**: System MUST alert humans immediately when workflow failures require manual intervention
- **FR-083**: System MUST maintain workflow state consistency across database, external services, and file systems
- **FR-084**: System MUST implement distributed transaction coordination for workflows spanning multiple systems
- **FR-085**: System MUST provide workflow failure recovery interfaces for human intervention and restart capabilities
- **FR-086**: System MUST calculate confidence scores based on multiple validation factors including data source reliability, model accuracy metrics, historical prediction performance, and data freshness
- **FR-087**: System MUST prevent over-confidence by applying confidence penalties when insufficient data points or validation factors are available
- **FR-088**: System MUST provide detailed explanations for confidence calculations including contributing factors, data sources used, and reasoning methodology when requested by users
- **FR-013**: System MUST monitor designated email inbox/folders for broker transaction receipts
- **FR-014**: System MUST parse transaction emails to extract stock symbol, quantity, price, transaction type (buy/sell), and date
- **FR-015**: System MUST automatically update relevant portfolios with parsed transaction data
- **FR-016**: System MUST assign transactions to portfolios based on broker account configuration and mapping rules
- **FR-012**: System MUST provide transaction verification interface showing parsed data and source emails
- **FR-013**: System MUST authenticate with email providers using OAuth for secure email access
- **FR-014**: System MUST support Westpac broker email formats initially and implement generic heuristics for metadata extraction to support additional brokers
- **FR-015**: System MUST schedule and execute daily price updates for all stocks in portfolios
- **FR-091**: System MUST implement adapter pattern to easily add new data providers and web scrapers for obtaining stock prices and financial data
- **FR-017**: System MUST recalculate portfolio values and performance metrics after price updates
- **FR-018**: System MUST monitor and track stock status changes including trading halts, suspensions, and delistings
- **FR-019**: System MUST detect and process corporate actions including stock splits, mergers, and spin-offs
- **FR-020**: System MUST automatically adjust position quantities and historical data for stock splits
- **FR-021**: System MUST provide notifications and alerts for significant corporate actions affecting user holdings
- **FR-022**: System MUST display stock status indicators in the portfolio and stock detail views
- **FR-023**: System MUST discover relevant news articles for each stock during daily price updates
- **FR-024**: System MUST implement an intelligent agent to analyze stock news and financial data
- **FR-025**: System MUST generate buy/sell/hold recommendations with confidence scores and reasoning
- **FR-026**: System MUST analyze news sentiment and correlate with financial metrics for recommendations
- **FR-027**: System MUST provide a recommendations dashboard showing all AI analysis results
- **FR-028**: System MUST include appropriate disclaimers and risk warnings for AI-generated advice
- **FR-029**: System MUST track recommendation accuracy and performance over time
- **FR-030**: System MUST provide AI-generated investment recommendations only (no automated trading functionality)
- **FR-031**: System MUST perform portfolio-level analysis at regular intervals using industry-standard methodologies
- **FR-032**: System MUST analyze sector allocation and identify overconcentration risks
- **FR-033**: System MUST calculate portfolio risk metrics including beta, volatility, and diversification ratios
- **FR-034**: System MUST generate rebalancing recommendations based on target allocations and risk parameters
- **FR-035**: System MUST provide risk management strategies including stop-loss and position sizing recommendations
- **FR-036**: System MUST support industry-recommended analysis intervals including monthly performance reviews, quarterly rebalancing assessments, and annual comprehensive portfolio analysis
- **FR-037**: System MUST allow users to set risk tolerance preferences and custom portfolio targets
- **FR-038**: System MUST track portfolio performance against benchmarks and risk-adjusted returns
- **FR-039**: System MUST provide a user interface for defining target sector allocations and weightings
- **FR-040**: System MUST allow users to configure rebalancing thresholds and trigger conditions through the UI
- **FR-041**: System MUST provide UI controls for setting portfolio analysis intervals and scheduling
- **FR-042**: System MUST enable users to define custom risk parameters and tolerance levels in the interface
- **FR-043**: System MUST allow users to save and manage multiple portfolio configuration profiles
- **FR-044**: System MUST provide visual tools for setting target allocations using charts and sliders
- **FR-019**: System MUST download and archive news articles in paperless-ngx with intelligent tagging
- **FR-013**: System MUST integrate with paperless-ngx API for document storage and retrieval
- **FR-014**: System MUST intelligently tag news articles with stock symbols, company names, and content categories
- **FR-015**: System MUST filter news for relevance using configurable criteria including stock price impact, company mentions, and sector relevance
- **FR-016**: System MUST run daily updates in the timezone of the relevant market, but typically use local system time for most operations
- **FR-017**: System MUST detect and parse dividend payment notifications from broker emails
- **FR-018**: System MUST automatically record dividend payments with date, amount, stock symbol, and tax details
- **FR-019**: System MUST track dividend reinvestments as new stock purchases
- **FR-020**: System MUST generate annual financial reports showing total dividend income and capital gains/losses
- **FR-021**: System MUST support Australian tax year (July 1 - June 30) for financial reporting periods
- **FR-022**: System MUST display a list of all user portfolios with summary information (name, total value, daily change)
- **FR-023**: System MUST allow users to select and drill down into individual portfolio details
- **FR-024**: System MUST display current stock allocation within each portfolio using interactive visual charts
- **FR-025**: System MUST show performance metrics including total return, annualized return, maximum drawdown, and dividend yield, with extensible design to easily add new metrics later
- **FR-026**: Users MUST be able to view historical performance data over selectable time periods
- **FR-027**: System MUST provide interactive charts that allow users to hover, zoom, and filter data
- **FR-028**: System MUST calculate and display percentage allocations for each stock within portfolios
- **FR-029**: System MUST show both absolute values and percentage changes in performance metrics
- **FR-030**: System MUST display visual indicators (green/red arrows or colors) for individual stock price rises and falls
- **FR-031**: System MUST show each stock's contribution to overall portfolio gain/loss in absolute and percentage terms
- **FR-032**: System MUST calculate and display daily, weekly, and cumulative price changes for each stock position
- **FR-033**: System MUST enable comparison view between multiple portfolios
- **FR-034**: System MUST display dividend income summary for each portfolio and overall
- **FR-035**: System MUST provide annual tax reporting with total income, capital gains, and losses breakdown
- **FR-036**: System MUST display linked news articles and documents from paperless-ngx in the stock detail view
- **FR-037**: System MUST provide clickable links to view full news articles in paperless-ngx
- **FR-038**: System MUST show news article summaries with publication dates and sources in the UI
- **FR-039**: System MUST log parsing failures and provide manual correction interface
- **FR-040**: Portfolio owners MUST have full control over their portfolios and MUST be able to assign permissions to other users via email addresses including read-only, edit, admin, or owner access levels
- **FR-089**: System MUST update stock prices and news data daily after market close
- **FR-090**: System MUST check email inbox every 15 minutes by default with configurable interval settings
- **FR-041**: System MUST implement MVP permission model with three levels: read-only (view only), read-write (make changes), and none (cannot view)
- **FR-042**: System MUST allow users to select performance display periods from a dropdown menu with configurable default setting
- **FR-043**: System MUST use ASX news sources and web scraper initially for news data collection
- **FR-044**: System MUST provide a clean, modern user interface with minimal visual clutter
- **FR-045**: System MUST be fully responsive and adapt to desktop, tablet, and mobile screen sizes
- **FR-046**: System MUST provide dynamic interactions with smooth animations and transitions
- **FR-047**: System MUST load data and update charts in real-time without full page refreshes
- **FR-048**: System MUST maintain consistent design and look-and-feel across all pages and components
- **FR-050**: System MUST provide a comprehensive RESTful API for all portfolio management operations
- **FR-051**: System MUST generate and maintain complete API documentation with endpoints, parameters, and examples
- **FR-052**: System MUST implement proper HTTP status codes and standardized error responses
- **FR-053**: System MUST support JSON request and response formats for all API endpoints
- **FR-054**: System MUST implement API authentication using API keys with plans to evaluate additional mechanisms (JWT, OAuth) in future releases
- **FR-055**: System MUST provide API endpoints for CRUD operations on portfolios, stocks, transactions, and dividends
- **FR-056**: System MUST include API endpoints for retrieving performance metrics and historical data
- **FR-057**: System MUST implement API rate limiting and usage monitoring
- **FR-058**: System MUST support API versioning for backward compatibility
- **FR-059**: System MUST provide API endpoints for accessing linked news articles and documents

### Key Entities *(include if feature involves data)*

- **Portfolio**: Represents a collection of share investments with name, total value, creation date, performance history, and multi-user access permissions
- **Watchlist**: Collection of stocks being monitored for potential investment without actual ownership
- **Watchlist Item**: Individual stock entry in a watchlist with tracking preferences and alert settings
- **Transaction**: Individual buy/sell record with stock symbol, quantity, price, date, type, source reference, and duplicate resolution status
- **Transaction History**: Complete record of all received transactions including duplicates, rejections, and resolution decisions
- **Duplicate Detector**: Component that identifies potential duplicate transactions across all input sources
- **Transaction Source**: Metadata tracking the origin of transactions (email, PDF, manual entry) with timestamps and references
- **Dividend Payment**: Individual dividend record with stock symbol, payment date, amount, tax details, and source email reference
- **Stock**: Individual share holding with symbol, company name, quantity, current price, historical price data, dividend history, status indicators, corporate actions history, and linked news articles
- **Corporate Action**: Record of stock splits, mergers, spin-offs, or other actions affecting stock holdings
- **Stock Status**: Current trading status including active, halted, suspended, or delisted conditions
- **Email Processor**: Component that monitors inbox, parses broker emails, extracts transaction data, and flags unparseable emails for human intervention
- **Email Review Queue**: System for managing flagged emails that require manual review and processing
- **Parsing Failure Handler**: Component that detects parsing failures and routes emails and documents to human intervention workflows
- **PDF Processor**: Component that handles PDF document parsing, OCR, and table extraction with failure detection
- **Document Review Queue**: Unified system for managing both email and PDF document review tasks
- **OCR Engine**: Service for processing scanned PDF documents and extracting text from images
- **Price Updater**: Scheduled service that fetches daily closing prices and recalculates portfolio values
- **News Tracker**: Service that discovers, filters, and downloads relevant news articles for portfolio stocks
- **News Article**: Individual news item with title, content, source, publication date, and associated stock symbols
- **AI Analysis Agent**: Intelligent service that uses agentic workflows to analyze news sentiment and financial data to generate investment recommendations
- **Agentic Workflow**: Automated process that orchestrates multiple AI tasks for portfolio analysis, data processing, and decision-making
- **AI Provider Interface**: Standardized interface for connecting to internal (Ollama) and external (OpenAI, Anthropic) AI services
- **Workflow Engine**: Service that manages, monitors, and executes agentic workflows with atomic transaction processing, failure detection, and recovery
- **Transaction Manager**: Component that ensures atomic operations and manages rollback scenarios for workflow failures
- **Workflow State Manager**: System that maintains consistent state across all workflow operations and external system interactions
- **Failure Alert System**: Component that immediately notifies humans when workflows fail and require manual intervention
- **Retry Manager**: Component that handles timeout detection, exponential backoff, and retry logic for remote service calls
- **Service Circuit Breaker**: Mechanism that prevents cascading failures by temporarily disabling calls to failing remote services
- **Confidence Calculator**: Component that computes reliability scores for AI analyses based on multiple validation factors
- **Confidence Factor**: Individual metric used in confidence calculations such as data source reliability, model accuracy, or data freshness
- **Confidence Explanation Engine**: System that provides detailed reasoning for confidence calculations including contributing factors and methodology
- **Request Queue**: System for managing and prioritizing retry attempts to remote services during recovery
- **Hallucination Detector**: Service that validates AI-generated content against factual data sources
- **Content Validator**: Component that cross-references AI outputs with authoritative financial and market data
- **Human Review Queue**: System for flagging and managing AI-generated content requiring human verification
- **Audit Trail**: Comprehensive log record of all system activities with tamper-proof integrity protection
- **Log Entry**: Individual audit record containing user, timestamp, action, IP address, and contextual data
- **Audit Logger**: Service responsible for capturing, storing, and managing all system audit information
- **Compliance Monitor**: Component that tracks and alerts on security and regulatory compliance violations
- **Investment Recommendation**: AI-generated buy/sell/hold signal with confidence score, reasoning, and analysis timestamp
- **Financial Analysis**: Processed financial metrics and ratios used by the AI agent for recommendation generation
- **Portfolio Analyzer**: Service that performs comprehensive portfolio-level analysis and risk assessment
- **Sector Analysis**: Analysis of portfolio sector allocation and concentration risks
- **Risk Metrics**: Calculated portfolio risk measures including beta, volatility, Sharpe ratio, and diversification metrics
- **Rebalancing Recommendation**: AI-generated suggestions for portfolio optimization and risk management
- **Risk Management Strategy**: Specific recommendations for stop-loss levels, position sizing, and diversification
- **Portfolio Configuration**: User-defined settings for target allocations, risk parameters, and analysis preferences
- **Rebalancing Profile**: Saved configuration template with target allocations and rebalancing thresholds
- **Risk Tolerance Setting**: User-defined risk parameters and tolerance levels for portfolio analysis
- **Paperless-NGX Integration**: Component that handles document storage, retrieval, and tagging in paperless-ngx
- **Performance Metric**: Industry-standardized calculated values including Sharpe ratio, alpha, beta, maximum drawdown, and other recognized indicators
- **Benchmark Index**: Reference market index used for performance comparison and attribution analysis
- **Performance Report**: Standardized report containing GIPS-compliant performance metrics and comparative analysis
- **Risk Metric**: Calculated risk measures including volatility, Value at Risk (VaR), and drawdown statistics
- **Performance Attribution**: Analysis breaking down portfolio returns by asset allocation and security selection contributions
- **Historical Data Point**: Time-stamped portfolio or stock value used for trend analysis and charting
- **User**: Authenticated account holder with profile, email configuration, portfolio ownership, and API key management
- **User Session**: Active login session with timeout and security tracking
- **API Key**: Generated authentication token for API access with permissions and expiration
- **Portfolio Permission**: User access rights to a specific portfolio (owner, admin, edit, view-only)
- **Portfolio Share**: Invitation and access management for multi-user portfolio collaboration
- **Access Audit Log**: Record of user actions and permission changes for portfolio security tracking
- **Broker Configuration**: Settings for parsing specific broker email formats and rules
- **Annual Financial Report**: Comprehensive yearly summary including dividend income, capital gains/losses, and tax information
- **API Endpoint**: RESTful service interface with defined routes, methods, and response schemas
- **API Documentation**: Comprehensive documentation including endpoint specifications, examples, and authentication details

---

## Review & Acceptance Checklist

*GATE: Automated checks run during main() execution*

### Content Quality

- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness

- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status

*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed

---