Feature: HTMX Interactions
    As a user
    I want to use HTMX to load content dynamically
    So that I can have a smooth user experience

    Scenario: Load items via HTMX
        Given The item list contains "Item 1"
        When I request items with HTMX headers
        Then I should receive an HTML fragment
        And the fragment should contain item data

    Scenario: Create item via HTMX
        Given The item list contains "Item 1"
        When I submit "Item 2" via HTMX
        Then I should receive the "Item 2" HTML
        And an event should be published
