Feature: Live Updates
    As a user
    I want to receive live updates
    So that I can see changes in real-time

    Scenario: Receive update via long-polling
        Given I am connected to the updates endpoint
        When a new item is created
        Then I should receive the update notification
        And the notification should contain the item data

    Scenario: Long-polling timeout
        When I connect to updates with a short timeout
        Then I should receive a timeout response