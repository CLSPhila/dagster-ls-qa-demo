from dagster import Definitions
from ls_qa_demo.example_asset import example_asset
from ls_qa_demo.case_error_assets import case_error_asset
from ls_qa_demo.email_admin_about_errors import email_to_admin



# Here's where you add assets and jobs so Dagster can find them.
defs = Definitions(
        assets = [example_asset, case_error_asset],
        jobs = [email_to_admin])


