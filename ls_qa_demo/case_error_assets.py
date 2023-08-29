from ls_qa_demo.factories import make_case_error_asset
from ls_qa_demo.types import CaseErrors
from dagster import asset, Output
import os
from ls_report_agent import ReportAgent, BearerToken

import pandas as pd

@asset()
def case_error_asset() -> Output:
    """
    Comments to explain something about the error.
    """
    # env var url should be an environment varialbe
    env_var_url = os.environ.get("THIS_REPORT_URL","")
    instructions = "To fix this error, just change X to Y."
    long_description =  "We can't have values of X in these cases."
    url_for_fixing = "https://mylegalserver.legalserver.example.com/matter/form123"
    to_emails = ["admin@legalservicesorg.example"]
    email_key = "Email"

    agent = ReportAgent(BearerToken(os.environ.get("API_TOKEN","")), env_var_url)
    
    # we're faking the report in this example
    #rpt : pd.DataFrame = agent.get_report(format='pandas')
    rpt = pd.DataFrame.from_dict({"case_id":["23","34"],"important_field":["X","X"]})
    return Output(
            value=CaseErrors(
                 rpt,
                 long_description,
                 instructions,
                 url_for_fixing,
                 to_emails,
                 email_key),
            metadata={
                 "num_errors":rpt.shape[0],
                 "description":long_description,
                 }
            )
