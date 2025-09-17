# Quickstart Guide: Portfolio List View Toggle

## Overview
This quickstart guide demonstrates how to use and test the portfolio list view toggle feature, which allows users to switch between tile view (card layout) and table view (tabular layout) for their portfolio lists.

## User Journey Walkthrough

### 1. Initial Page Load
**Expected Behavior**:
- User lands on `/portfolios` page
- Default view shows portfolios in tile/card format (existing behavior)
- View toggle control visible in page header area
- Toggle shows "Tiles" mode as selected

**Visual Indicators**:
- Grid layout with portfolio cards
- Toggle button group with "Tiles" highlighted
- All existing functionality (search, sort, filters) remains available

### 2. Switch to Table View
**User Action**: Click "Table" button in view toggle
**Expected Behavior**:
- Smooth transition animation (< 300ms)
- Portfolio data reflows into tabular layout
- Column headers appear with sortable indicators
- All portfolio information remains visible in table cells
- User preference automatically saved to localStorage

**Table Layout**:
```
| Portfolio Name | Total Value | Daily Change | Unrealized P&L | Created | Last Updated | Actions |
|----------------|-------------|--------------|----------------|---------|--------------|---------|
| Tech Portfolio | $125,432.50 | +$2,341 (+1.9%) | +$15,234 (+13.4%) | 2024-01-15 | 2 min ago | [View][Trade][Delete] |
| Growth Fund    | $89,765.21  | -$543 (-0.6%)   | -$2,134 (-2.3%)   | 2024-02-20 | 5 min ago | [View][Trade][Delete] |
```

### 3. Table Interaction Testing
**Column Sorting**:
- Click any sortable column header → Data sorts ascending
- Click same header again → Data sorts descending
- Sort indicator (arrow) updates to show current direction
- Existing search and filter state preserved during sort

**Responsive Behavior**:
- Mobile (< 768px): Table scrolls horizontally, priority columns visible
- Tablet (768px - 1024px): Reduced columns shown, action buttons may stack
- Desktop (> 1024px): Full table with all columns visible

**Row Actions**:
- "View" button → Navigate to portfolio detail page
- "Trade" button → Navigate to add transaction page
- "Delete" button → Show delete confirmation modal
- Row click (outside buttons) → Navigate to portfolio detail page

### 4. Switch Back to Tiles View
**User Action**: Click "Tiles" button in view toggle
**Expected Behavior**:
- Smooth transition back to card layout
- All portfolio cards display with full information
- Grid responsive behavior resumes
- User preference persists (reload page shows tiles mode)

### 5. Persistence Testing
**Test Steps**:
1. Set view to "Table" mode
2. Refresh page or navigate away and back
3. **Expected**: Page loads in table mode (preference remembered)
4. Switch to "Tiles" mode
5. Refresh page
6. **Expected**: Page loads in tiles mode

## Testing Scenarios

### Functional Testing
```bash
# Test Case 1: Basic Toggle Functionality
Given I am on the portfolios page
When I click the "Table" toggle button
Then the view changes to table layout
And the toggle shows "Table" as selected
And my preference is saved

# Test Case 2: Data Integrity
Given I have portfolios with various metrics
When I switch between tile and table views
Then all portfolio information is displayed correctly
And no data is lost or truncated
And formatting remains consistent

# Test Case 3: Sorting Integration
Given I am in table view
When I click a column header to sort
Then the data sorts correctly
And existing search filters remain applied
And the sort state persists when switching views

# Test Case 4: Responsive Design
Given I am on a mobile device
When I view the table layout
Then the table scrolls horizontally
And priority columns are visible
And action buttons remain accessible

# Test Case 5: Accessibility
Given I am using keyboard navigation
When I focus on the view toggle
Then I can use arrow keys or tab to navigate
And screen readers announce the current view mode
And table headers are properly associated with data cells
```

### Performance Testing
```bash
# Test Case 6: Large Portfolio Lists
Given I have 50+ portfolios
When I switch between view modes
Then the transition completes in < 500ms
And the page remains responsive
And memory usage stays reasonable

# Test Case 7: Repeated Toggling
Given I rapidly switch between views
When I toggle 10+ times quickly
Then the UI remains stable
And preferences save correctly
And no memory leaks occur
```

### Edge Case Testing
```bash
# Test Case 8: Empty State
Given I have no portfolios
When I toggle between view modes
Then appropriate empty state messages appear
And the toggle functionality still works
And create portfolio buttons remain accessible

# Test Case 9: Loading State
Given portfolios are loading from API
When I toggle view modes during loading
Then loading indicators display correctly
And the toggle is disabled during load
And the view switch completes after data loads

# Test Case 10: Error State
Given there is an API error loading portfolios
When I toggle view modes
Then error messages display in both views
And the toggle remains functional
And retry actions work from both views
```

## Quick Validation Checklist

### Before Release
- [ ] Toggle button displays correctly in page header
- [ ] Default view is tiles mode for new users
- [ ] Table view shows all portfolio data fields
- [ ] Column sorting works in table view
- [ ] Search and filters work in both views
- [ ] Responsive design functions on mobile/tablet
- [ ] User preferences persist across sessions
- [ ] Loading states display correctly in both views
- [ ] Empty states show appropriate messages
- [ ] Error handling works consistently
- [ ] Accessibility features function properly
- [ ] Performance meets requirements (< 500ms transitions)

### User Acceptance
- [ ] Non-technical users can easily understand the toggle
- [ ] Table view provides better comparison capabilities
- [ ] Tile view preserves visual appeal and readability
- [ ] Mobile experience remains usable
- [ ] Feature integrates seamlessly with existing workflow
- [ ] No regression in existing portfolio management features

## Development Quick Reference

### Key Files to Validate
- `/frontend/src/app/portfolios/page.tsx` - Main portfolio page with toggle
- `/frontend/src/components/Portfolio/ViewToggle.tsx` - Toggle component
- `/frontend/src/components/Portfolio/PortfolioTable.tsx` - Table view component
- `/frontend/src/hooks/usePortfolioView.ts` - View state management
- Tests in `/frontend/src/__tests__/components/Portfolio/`

### Local Storage Schema
```javascript
// Check in browser dev tools: Application > Local Storage
{
  "portfolio-view-preferences": {
    "viewMode": "table",
    "timestamp": 1694876543210,
    "version": "1.0.0"
  }
}
```

### CSS Classes to Verify
- View toggle: `.view-toggle-container`, `.view-toggle-button`
- Table: `.portfolio-table`, `.portfolio-table-row`
- Responsive: `.mobile-scroll`, `.tablet-columns`
- Transitions: `.view-transition`, `.fade-in`, `.slide-up`

This quickstart provides a comprehensive testing and validation framework for the portfolio list view toggle feature.