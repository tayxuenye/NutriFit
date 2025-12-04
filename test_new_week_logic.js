// Test the new week logic
console.log("Testing new week calculation logic");
console.log("Today is:", new Date().toDateString());
console.log("=" + "=".repeat(60));

// New implementation
function getWeekStartDate(weekOffset = 0) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() + (weekOffset * 7));
    return weekStart;
}

function formatWeekDisplay(weekOffset) {
    const weekStart = getWeekStartDate(weekOffset);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);

    const startStr = weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endStr = weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    if (weekOffset === 0) {
        return `This Week (${startStr} - ${endStr})`;
    } else if (weekOffset === -1) {
        return `Last Week (${startStr} - ${endStr})`;
    } else if (weekOffset === 1) {
        return `Next Week (${startStr} - ${endStr})`;
    } else {
        return `${startStr} - ${endStr}`;
    }
}

function getWeekValue(weekOffset) {
    const weekStart = getWeekStartDate(weekOffset);
    // Format as YYYY-MM-DD in local timezone (not UTC)
    const year = weekStart.getFullYear();
    const month = String(weekStart.getMonth() + 1).padStart(2, '0');
    const day = String(weekStart.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

console.log("\nWeek Display:");
console.log("-".repeat(60));
for (let offset = -1; offset <= 1; offset++) {
    console.log(`Offset ${offset}: ${formatWeekDisplay(offset)}`);
    console.log(`  API value: ${getWeekValue(offset)}`);
}

console.log("\nExpected behavior:");
console.log("-".repeat(60));
console.log("When you click 'Generate Weekly Plan' on offset 0:");
console.log(`  - It should send start_date: ${getWeekValue(0)}`);
console.log(`  - Backend will generate 7 days starting from ${getWeekValue(0)}`);
console.log(`  - Days will be: ${getWeekValue(0)} through ${new Date(new Date(getWeekValue(0)).getTime() + 6 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}`);
