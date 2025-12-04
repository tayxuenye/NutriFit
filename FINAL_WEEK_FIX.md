# Final Week Navigation Fix

## Issues Fixed

### 1. Week Calculation - Monday-Based Weeks
**Problem:** You wanted Monday-to-Sunday weeks, not current-date-based weeks.

**Solution:** Reverted to Monday-based week calculation:
```javascript
function getWeekStartDate(weekOffset = 0) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const dayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
    const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
    const monday = new Date(today);
    monday.setDate(today.getDate() + daysToMonday + (weekOffset * 7));
    return monday;
}
```

### 2. Plan Filtering - Exact Match Instead of Overlap
**Problem:** When navigating to a week (e.g., Nov 17-23), it would show plans from the next week (Nov 23-29) because the filtering used "overlaps" logic.

**Solution:** Changed to exact start date matching:
```javascript
// OLD - Overlap logic (WRONG)
const weekPlans = result.plans.filter(plan => {
    const planStart = new Date(plan.start_date);
    const planEnd = plan.end_date ? new Date(plan.end_date) : planStart;
    return (planStart <= weekEndDate && planEnd >= weekStartDate); // Any overlap
});

// NEW - Exact match (CORRECT)
const weekPlans = result.plans.filter(plan => {
    const planStart = new Date(plan.start_date);
    const planStartStr = planStart.toISOString().split('T')[0];
    return planStartStr === weekStart; // Must start on this Monday
});
```

### 3. Date Formatting - Local Timezone
**Problem:** Using `toISOString()` was converting to UTC and causing off-by-one-day errors.

**Solution:** Format dates in local timezone:
```javascript
function getWeekValue(weekOffset) {
    const weekStart = getWeekStartDate(weekOffset);
    const year = weekStart.getFullYear();
    const month = String(weekStart.getMonth() + 1).padStart(2, '0');
    const day = String(weekStart.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
```

## How It Works Now

### Week Display
- Shows Monday to Sunday of the current week
- Today is Thursday, Dec 4, 2025
- "This Week" shows: Dec 1 - Dec 7 (Monday to Sunday)

### Generate Plan
1. Click "Generate Weekly Plan"
2. Sends `start_date: 2025-12-01` (Monday)
3. Backend generates 7 days: Dec 1, 2, 3, 4, 5, 6, 7
4. Plan is saved with `start_date: 2025-12-01`

### Navigate Weeks
1. Click ← to go to previous week
2. Week selector shows: Nov 24 - Nov 30
3. `loadMealPlansForWeek()` looks for plans with `start_date === 2025-11-24`
4. Only shows plans that start exactly on Nov 24 (Monday)
5. No more showing plans from overlapping weeks!

### Come Back to Week
1. Navigate away and come back
2. Week selector still shows: Nov 24 - Nov 30
3. Loads the correct plan that starts on Nov 24
4. Displays all 7 days from Nov 24-30

## Files Modified
- `nutrifit/templates/index.html`
  - `getWeekStartDate()` - Monday-based calculation
  - `getWeekValue()` - Local timezone formatting
  - `loadMealPlansForWeek()` - Exact date matching
  - `loadWorkoutPlansForWeek()` - Exact date matching

## Testing

Server running at: http://localhost:5000

### Test Scenario 1: Generate Plan
1. Go to Meals tab
2. Check week display shows "This Week (Dec 1 - Dec 7, 2025)"
3. Click "Generate Weekly Plan"
4. Verify plan shows days: Dec 1, 2, 3, 4, 5, 6, 7 ✓

### Test Scenario 2: Navigate Weeks
1. Click ← to go to last week
2. Should show "Last Week (Nov 24 - Nov 30, 2025)"
3. If no plan exists, shows "No meal plan found"
4. Click → to go back to this week
5. Should show "This Week (Dec 1 - Dec 7, 2025)"
6. Shows the plan you generated ✓

### Test Scenario 3: Multiple Plans
1. Generate plan for "This Week" (Dec 1-7)
2. Click → to go to next week (Dec 8-14)
3. Generate plan for next week
4. Click ← to go back to this week
5. Should show the Dec 1-7 plan, NOT the Dec 8-14 plan ✓

## Key Points
- ✓ Weeks are Monday to Sunday
- ✓ Plans are generated starting from Monday
- ✓ Plans are filtered by exact Monday match
- ✓ No more showing wrong week's plans
- ✓ Navigation works correctly
