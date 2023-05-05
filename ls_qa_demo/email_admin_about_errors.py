from dagster import job, AssetsDefinition, make_values_resource
import ls_qa_demo
from ls_qa_demo.factories import make_send_case_error_email
"""
Module for the job "Emailing admins about case error alerts"
"""

all_case_error_assets = [asset for _, asset in ls_qa_demo.case_error_assets.__dict__.items() if isinstance(asset, AssetsDefinition)]


# These 'Resources' make it easier to toggle sending emails on an off. 
# You might want to not actually send emails while testing things. This 
# creates a runtime configuration option to turn emailing on or off.
emailing_resources = dict()
emailing_resources = dict()
emailing_resources.update({
    "really_send_emails":make_values_resource()
})


@job(resource_defs=emailing_resources)
def email_to_admin():    
    """
    Email the stored case error reports to admins only.
    """
    errs_list = [(asset_key, asset.to_source_asset()) for asset_key, asset in ls_qa_demo.case_error_assets.__dict__.items() if isinstance(asset, AssetsDefinition)]

    for asset_key, err in errs_list:
        make_send_case_error_email(                       
                name=f"send_email_re_{asset_key or 'not_described'}")(err)
