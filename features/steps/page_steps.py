# ============================================================================
# features/steps/page_steps.py - Homepage Steps
# ============================================================================
from pytest_bdd import scenarios, given, when, then, parsers
from bs4 import BeautifulSoup

scenarios('../homepage.feature')

@when('I visit the home page')
def visit_home(sync_client, context):
    context['response'] = sync_client.get("/")

@then('I should see the welcome message')
def check_welcome(context):
    assert context['response'].status_code == 200
    soup = BeautifulSoup(context['response'].text, 'html.parser')
    assert "Welcome" in soup.text

@then('the page should have the correct title')
def check_title(context):
    soup = BeautifulSoup(context['response'].text, 'html.parser')
    title = soup.find('title')
    assert title is not None
    assert "Welcome to Live Updates" in title.text