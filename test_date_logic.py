#!/usr/bin/env python3
"""Test script to understand the week date logic"""

from datetime import datetime, timedelta

def get_monday_based_week(week_offset=0):
    """Current implementation - Monday-based weeks"""
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    day_of_week = today.weekday()  # Monday = 0, Sunday = 6
    days_to_monday = -day_of_week
    monday = today + timedelta(days=days_to_monday + (week_offset * 7))
    sunday = monday + timedelta(days=6)
    return monday, sunday

def get_current_date_week(week_offset=0):
    """New implementation - Current date-based weeks"""
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    week_start = today + timedelta(days=(week_offset * 7))
    week_end = week_start + timedelta(days=6)
    return week_start, week_end

# Test with today's date
print("=" * 60)
print(f"Today is: {datetime.now().strftime('%A, %B %d, %Y')}")
print("=" * 60)

print("\n1. MONDAY-BASED WEEKS (Current Implementation):")
print("-" * 60)
for offset in [-1, 0, 1]:
    start, end = get_monday_based_week(offset)
    label = "Last Week" if offset == -1 else "This Week" if offset == 0 else "Next Week"
    print(f"{label:12} (offset={offset:2}): {start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}")

print("\n2. CURRENT DATE-BASED WEEKS (What you want):")
print("-" * 60)
for offset in [-1, 0, 1]:
    start, end = get_current_date_week(offset)
    label = "Last Week" if offset == -1 else "This Week" if offset == 0 else "Next Week"
    print(f"{label:12} (offset={offset:2}): {start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}")

print("\n3. COMPARISON:")
print("-" * 60)
monday_start, monday_end = get_monday_based_week(0)
current_start, current_end = get_current_date_week(0)
print(f"Monday-based 'This Week':  {monday_start.strftime('%b %d')} - {monday_end.strftime('%b %d, %Y')}")
print(f"Current date 'This Week':  {current_start.strftime('%b %d')} - {current_end.strftime('%b %d, %Y')}")
print(f"\nDifference: {(current_start - monday_start).days} days")
