# Week Navigation Bug Fix

## Issues Fixed

### 1. Missing Variable Declaration
**Problem:** The `currentDisplayedMealPlanId` variable was referenced but never declared, causing JavaScript errors.

**Solution:** Added the variable declaration:
```javascript
let currentDisplayedMealPlanId = null; // Track which plan is currently displayed
```

### 2. Auto-Week Adjustment on Generate
**Problem:** When clicking "Generate Weekly Plan", the week selector would automatically jump to match the generated plan's start date, which was confusing for users.

**Solution:** Removed the auto-adjustment code that was changing `currentMealWeek` after plan generation. Now the week selector stays on the user's selected week.

### 3. Week Navigation Conflict
**Problem:** When using the previous/next week buttons, the `loadMealPlansForWeek` function would call `loadMealPlan` with `autoAdjustWeek=true`, causing the week selector to jump back.

**Solution:** Changed `loadMealPlansForWeek` to call `loadMealPlan(weekPlans[0].id, false)` to prevent auto-adjustment when navigating weeks.

### 4. Console Warning about Form Labels
**Problem:** Hidden input fields for week selectors didn't have labels, causing accessibility warnings.

**Solution:** Added `aria-label` attributes to both hidden inputs:
```html
<input type="hidden" id="mealWeekSelector" value="" aria-label="Selected week start date">
<input type="hidden" id="workoutWeekSelector" value="" aria-label="Selected week start date">
```

### 5. Meal Edit Week Jump
**Problem:** When editing a meal, the plan would reload and potentially adjust the week selector.

**Solution:** Changed `saveMealEdit` to call `loadMealPlan(planId, false)` to prevent week adjustment after edits.

## How Week Navigation Now Works

1. **Previous/Next Buttons**: Click ← or → to navigate between weeks. The display updates and shows plans for that week.

2. **Generate Plan**: Generates a plan for the currently selected week without jumping the week selector.

3. **Click Saved Plan**: Clicking a saved plan from the list will auto-adjust the week selector to show that plan's week (this is intentional for better UX).

4. **Edit Meal**: Editing a meal keeps you on the same week.

## Testing

The server is running at http://localhost:5000

Test the following:
1. Navigate to Meals tab
2. Click the ← and → buttons to change weeks
3. Generate a plan for a specific week
4. Verify the week selector doesn't jump unexpectedly
5. Edit a meal and verify you stay on the same week

## Files Modified

- `nutrifit/templates/index.html` - Fixed JavaScript functions and HTML attributes
