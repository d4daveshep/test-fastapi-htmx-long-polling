Feature: Homepage
    As a user
    I want to visit the homepage
    So that I can see the welcome message

    Scenario: User visits homepage
        When I visit the home page
        Then I should see the welcome message
        And the page should have the correct title