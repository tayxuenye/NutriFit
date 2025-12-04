# Implementation Plan

## Overview
This implementation plan outlines the tasks needed to build the LLM-Based Conversational Plan Generation feature with save functionality.

- [x] 1. Create Plan Parser Module
  - Create `nutrifit/parsers/plan_parser.py` with PlanParser class
  - Implement regex patterns for meal and exercise extraction
  - Implement `parse_meal_plan()` method
  - Implement `parse_workout_plan()` method
  - Add nutritional estimation logic
  - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - **Status**: ✅ Complete - All 8 tests passing

- [x] 2. Enhance Chatbot Engine with LLM Plan Generation
  - Add `generate_llm_meal_plan()` method to ChatbotEngine
  - Add `generate_llm_workout_plan()` method to ChatbotEngine
  - Create meal plan prompt template with user profile injection
  - Create workout plan prompt template with user profile injection
  - Add `store_generated_plan()` method for context management
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 7.1, 7.2, 7.3, 7.4_

- [x] 3. Update Intent Detection for LLM Mode
  - Modify `_handle_meal_plan_request()` to use LLM generation
  - Modify `_handle_workout_plan_request()` to use LLM generation
  - Add flag to toggle between LLM and structured generation
  - Ensure requirements extraction still works (calories, macros, etc.)
  - _Requirements: 1.1, 2.1, 7.1, 7.2, 7.3_

- [x] 4. Add Save Plan API Endpoint
  - Create `/api/chatbot/save-plan` POST endpoint
  - Implement plan retrieval from context by ID
  - Integrate PlanParser to convert text to structured data
  - Save parsed plan to storage using existing storage manager
  - Return success response with saved plan ID
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 8.1, 8.2_

- [x] 5. Enhance Chat Response Format
  - Modify chatbot response to include plan metadata (plan_id, plan_type)
  - Update response JSON structure to support action buttons
  - Add plan identification in conversation context
  - _Requirements: 3.1, 3.2, 3.3, 4.5_

- [x] 6. Add Save Button UI Component
  - Create CSS styles for save plan buttons
  - Implement `createSaveButton()` JavaScript function
  - Add button states (default, saving, saved)
  - Style buttons to match existing UI theme
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 7. Implement Save Plan JavaScript Function
  - Create `savePlanToDashboard()` function
  - Make API call to `/api/chatbot/save-plan`
  - Handle loading state during save
  - Update button state on success/failure
  - Show confirmation toast notification
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8. Update Message Rendering to Include Buttons
  - Modify `formatMessage()` to detect plan responses
  - Inject save buttons after plan content
  - Ensure buttons are only shown for unsaved plans
  - Handle button visibility after save
  - _Requirements: 3.1, 3.2, 3.4, 4.5_

- [x] 9. Add Plan Regeneration Feature
  - Create "Regenerate" button alongside save button
  - Implement `regeneratePlan()` JavaScript function
  - Resend request with modification context
  - Replace old plan with new one in chat
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Integrate Saved Plans with Dashboard
  - Ensure saved plans appear in Meal Plans panel
  - Ensure saved plans appear in Workout Plans panel
  - Add "Source: AI Chat" indicator to saved plans
  - Test plan display and interaction in dashboard
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 11. Add Error Handling and Fallbacks
  - Handle LLM generation failures gracefully
  - Implement fallback to structured generation
  - Handle parsing failures with user notification
  - Add retry logic for transient failures
  - Log errors for debugging
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 12. Add Helpful Prompts and Examples
  - Update welcome message with LLM plan examples
  - Add help text for meal plan requests
  - Add help text for workout plan requests
  - Implement clarifying questions for ambiguous requests
  - Add modification instructions in plan responses
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 13. Write Unit Tests for Plan Parser
  - Test meal plan parsing with various formats
  - Test workout plan parsing with various formats
  - Test regex pattern matching
  - Test nutritional estimation
  - Test error handling for malformed input
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 14. Write Integration Tests
  - Test end-to-end meal plan generation and save
  - Test end-to-end workout plan generation and save
  - Test plan regeneration flow
  - Test error scenarios
  - Test UI button interactions
  - _Requirements: All_

- [ ] 15. Update Documentation
  - Document new API endpoints
  - Document PlanParser usage
  - Add user guide for conversational planning
  - Update README with new feature description
  - _Requirements: All_

## Notes

- **LLM Dependency**: This feature requires Ollama to be running with Llama model
- **Parsing Accuracy**: Initial parsing may not be 100% accurate; users can edit plans in dashboard
- **Performance**: LLM generation takes 2-10 seconds; UI should show loading state
- **Backward Compatibility**: Keep existing structured plan generation as fallback
- **Testing**: Extensive testing needed for various LLM output formats

## Estimated Effort

- **Total Tasks**: 15 main tasks
- **Estimated Time**: 3-5 days for full implementation
- **Priority**: High (user-requested feature)
- **Dependencies**: Ollama must be installed and running

## Success Criteria

- ✅ Users can generate meal plans through natural conversation
- ✅ Users can generate workout plans through natural conversation
- ✅ Save buttons appear after plan generation
- ✅ Clicking save adds plans to dashboard
- ✅ Plans can be regenerated through conversation
- ✅ Error handling works gracefully
- ✅ All tests pass
