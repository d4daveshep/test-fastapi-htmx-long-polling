Feature: HTMX Interactions
    As a user
    I want to use HTMX to load content dynamically
    So that I can have a smooth user experience

    Scenario: Load items via HTMX
        When I request items with HTMX headers
        Then I should receive an HTML fragment
        And the fragment should contain item data

    Scenario: Create item via HTMX
        When I submit a new item via HTMX
        Then I should receive the new item HTML
        And an event should be published