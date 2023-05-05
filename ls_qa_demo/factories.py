from dagster import asset, Output, op, In, Nothing, Out
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import List
import pandas as pd
from ls_report_agent import ReportAgent, BearerToken
import os
from ls_qa_demo.types import CaseErrors


def create_caseid_link(site_root, url_for_fixing):
    """
    A method for making an html hyperlink to your legalserver site.
    """
    url_template= '''<a href="{site_root}/{url_for_fixing}{partial_caseid}" target="_blank">{full_caseid}</a>'''.format(full_caseid=caseid, partial_caseid=caseid[3:], site_root=site_root, 
            url_for_fixing=url_for_fixing)
    return url_template

def make_case_error_asset(
        asset_description: str,
        long_description: str,
        env_var_url: str,
        instructions: str,
        url_for_fixing: str,
        to_emails: List[str],
        email_key: str | None = None,
        ):
    """
    Create an asset that represents a certain type case error. 

    For example, if cases are not supposed to have Field A be equal X if Field B is equal to Y, we'll have a legalserver report identifiying those cases. This asset will collect that report, and wrap in context that will explain who should be notified about the error (either just admins, or both admins and the value of some column in the report, like the case handler's email), and how to fix the error.

    """


    @asset(
            name=asset_description, group_name="case_errors",
            description=asset_description, 
            io_manager_key="case_errors_manager")
    def case_error_asset() -> Output:
        agent = ReportAgent(BearerToken(os.environ.get("API_TOKEN","")), os.environ.get(env_var_url,"") + "&display_hidden_columns=false")
        rpt : pd.DataFrame = agent.get_report(format='pandas')
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
    return case_error_asset 

def make_case_error_op(
        op_description: str,
        long_description: str,
        env_var_url: str,
        instructions: str,
        url_for_fixing: str,
        to_emails: List[str],
        email_key: str | None = None,
        ):
    """
    Create an operator function that collects case errors from LegalServer.
    """

    @op(name=op_description, description=op_description, out=Out(io_manager_key="case_errors_manager"))
    def case_error_op() -> Output:
        agent = ReportAgent(BearerToken(os.environ.get("API_TOKEN","")), os.environ.get(env_var_url,"") + "&display_hidden_columns=false")
        rpt : pd.DataFrame = agent.get_report(format='pandas')
        return Output(
                value=CaseErrors(
                    rpt,
                    long_description,
                    instructions,
                    url_for_fixing,
                    to_emails,
                    email_key,
                    ),
                metadata={
                    "num_errors":rpt.shape[0],
                    "description":long_description,
                    }
                )
    return case_error_op 





def make_send_case_error_email(
    name="send_case_error_email",
    ins=None
):
    """
    Second-order function that create an op function for sending an email. 


    TODO this should probably use send_case_error_email from ls_qa.common, rather 
    than reproducing a lot of the logic from there.

    Args:
        name (str): The name of the new op.

    Returns:
        function: The new op.
    """

    @op(
            name=name, 
            # not with config schema, because that makes separate configs per op.
            #config_schema={"really_send_emails": bool, "email_to_advocate": bool},
            # https://docs.dagster.io/concepts/configuration/config-schema#passing-configuration-to-multiple-ops-in-a-job
            required_resource_keys={"really_send_emails"},
            ins=ins or {"start": In(Nothing)})
    def send_case_error_email(context, errs: CaseErrors) -> None:
        """
        Send an email with a table of case errors

        Send to Addresses in the to_emails property of
        a CaseErrors object.
    
        Args:
            errs: CaseErrors container of case errors.
        """
    
        
        if context.resources.really_send_emails is False:
            context.log.info("Not really sending emails!")
            return

        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_KEY')) 
        from_email = Email(os.environ.get('EMAIL_FROM'))  # Change to your verified sender
        to_emails = [To(addr) for addr in errs.to_emails]  # Change to your recipient
        subject = errs.description
        instructions = "<div> " + errs.instructions + "</div>"
        tbl = errs.df.copy()
        try:
            tbl["Case_Matter_Case_ID_"] = tbl["Case_Matter_Case_ID_"].apply(create_caseid_link, args=(os.environ.get('LS_SITE_ROOT'), errs.url_for_fixing))
        except:
            try:
                tbl["Matter_Case_ID_"] = tbl["Matter_Case_ID_"].apply(create_caseid_link, args=(os.environ.get('LS_SITE_ROOT'), errs.url_for_fixing))
            except:
                context.log.error("Case_Matter_Case ID_ and Matter_Case_ID_ columns missing for table: %s", errs.description)
        
        if tbl.shape[0] > 0:
            if "Database_ID" in tbl.columns:
                tbl.drop(["Database_ID"],axis="columns",inplace=True)
            if "ID" in tbl.columns:
                tbl.drop(["ID"],axis="columns", inplace=True)
            if "Date_Open_Range" in tbl.columns:
                tbl.drop(["Date_Open_Range"], axis="columns", inplace=True)
            if "Is_Test_Case" in tbl.columns:
                tbl.drop(["Is_Test_Case"], axis="columns",inplace=True)
            content = Content("text/html", "<div><b>" + instructions + "</b></div>" + tbl.to_html(index=False, escape=False))
        else:
            content = Content("text/html", "<div><b> No errors! </b></div>")
    
        mail = Mail(from_email, to_emails, subject, content)
    
   
        # Get a JSON-ready representation of the Mail object
        mail_json = mail.get()
        
        # Send an HTTP POST request to /mail/send
        response = sg.client.mail.send.post(request_body=mail_json)
        context.log.info(response.status_code)
        
    
    return send_case_error_email 


