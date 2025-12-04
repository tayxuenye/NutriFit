# Week Synchronization Fix

## Problem
The week navigation was using Monday-based weeks instead of current-date-based weeks. This caused:
1. When on Dec 3 (Wednesday), "This Week" showed Dec 1-7 (Monday to Sunday) instead of Dec 3-9
2. Generating a plan would create it for Nov 30-Dec 6 instead of Dec 3-9
3. The displayed week didn't match what was being generated

## Root Cause
The `getWeekStartDate()` function was calculating the Monday of the current week:
```javascript
// OLD - Monday-based
const dayOfWeek = today.getDay();
const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
const monday = new Date(today);
monday.setDate(today.getDate() + daysToMonday + (weekOffset * 7));
```

## Solution
Changed to use the current date as the week start:
```javascript
// NEW - Current date-based
const weekStart = new Date(today);
weekStart.setDate(today.getDate() + (weekOffset * 7));
```

## Changes Made

### 1. Updated `getWeekStartDate()` Function
- Now returns today's date + (weekOffset * 7 days)
- No longer calculates Monday

### 2. Updated `formatWeekDisplay()` Function
- Changed variable names from `monday`/`sunday` to `weekStart`/`weekEnd`
- Logic remains the same (7-day range)

### 3. Updated `getWeekValue()` Function
- Fixed timezone issue by formatting date in local timezone instead of UTC
- Prevents off-by-one-day errors

### 4. Updated `loadMealPlan()` Week Calculation
- Simplified the week offset calculation
- No longer tries to find "Monday of the week"
- Directly calculates day difference and converts to week offset

## Testing Results

Today: Wednesday, December 3, 2025

### Before Fix:
- This Week: Dec 1 - Dec 7 (Monday-based)
- API sends: 2025-12-01
- Backend generates: Nov 30 - Dec 6 (due to timezone issues)

### After Fix:
- This Week: Dec 3 - Dec 9 (Current date-based)
- API sends: 2025-12-03
- Backend generates: Dec 3 - Dec 9 ✓

## How It Works Now

1. **Week Display**: Shows 7 days starting from today (or offset days)
   - Offset -1: 7 days ago to 1 day ago
   - Offset 0: Today to 6 days from now
   - Offset 1: 7 days from now to 13 days from now

2. **Generate Plan**: Sends the exact start date shown in the display

3. **Backend**: Generates 7 days starting from the received date

4. **Display**: Shows all 7 days from the plan

## Files Modified
- `nutrifit/templates/index.html` - Updated week calculation functions

## Server
Running at http://localhost:5000

## Test It
1. Go to Meals tab
2. Check "This Week" display - should show Dec 3 - Dec 9
3. Click "Generate Weekly Plan"
4. Verify it generates for Dec 3 - Dec 9
5. Verify all 7 days are displayed (Dec 3, 4, 5, 6, 7, 8, 9)
6. Click ← to go to last week - should show Nov 26 - Dec 2
7. Click → twice to go to next week - should show Dec 10 - Dec 16
