import pandas as pd
from typing import List

class CaseErrors:
    def __init__(self, df: pd.DataFrame, description: str, instructions: str, url_for_fixing: str, to_emails: List[str], email_key: str | None)-> None:
        """
        Container wrapping case errors.


        Args:
            df: Data of case errors
            description: what is the error
            instructions: how to fix
            url_for_fixing: part of url to LegalServer, link to a form that user should use to correct issue.
            to_emails: list of email addresses to send to.
            email_key: Key in the df of a column that has other email addresses to group by and mail to.
        """
        self.df = df
        self.description = description
        self.instructions = instructions
        self.url_for_fixing = url_for_fixing
        self.to_emails = to_emails
        self.email_key = email_key


