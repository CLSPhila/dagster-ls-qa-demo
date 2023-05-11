** Work in progress. Feedback appreciated! **

# Orchestrating Case Management Quality Assurance



## The payoff

At Community Legal Services, we rely heavily on our case management system, LegalServer, to collect data for reporting on our work to funders. We collect a lot of data. There are hundreds of different fields on thousands of cases, people, and other kinds of entities. And we have an ever-growing list of rules to ensure the quality of that data: cases that close as brief advice shouldn't also record that the case involved litigation in a state court; cases that are funded by certain projects need to have certain data fields filled in. And so on. There are a few dozen of these rules now, and the list is always growing.

We need to be able to:
1. Identify all the errors
2. Inform case handlers and management about errors.

With so many different rules to enforce, this might be an arduous process. It would require a time-intesive process of paging through case files to spot errors and write emails about them. A manual process like this is _boring._ Worse, a manual process is very error prone. My eyes start swimming after trying to click through too many nearly-identical forms and tiny multiple-choice dropdown boxes. LegalServer helps us collect bulk data into tabular reports, and that helps. But we're still stuck reading through the reports and crafting emails to staff to give instructions about which cases they need to fix, and how. 

There's a better way! At CLS, we're now using a process that makes it much easier to review any number of quality assurance errors and then alert staff about fixing them. With the click of a single button, we can tell **Dagster** to download dozens of quality assurance reports from the case management sytem. And for each report, Dagster will send emails to managers and case handlers, alerting staff to the errors they need to fix. Emails identify each case with an issue that needs fixing, and they include instructions and hyperlinks to make it quick for staff to address problems. I am able to send 150 emails at once, each one customized with instructions for the case handler and links to the cases that each case handler needs to fix.

One button click. Dozens of QA reports. Potentially hundreds of customized emails to case handlers. And adding new quality assurance checks is now just the work of a few minutes. If you've been doing this work manually, this new approach feels ... powerful.

How's it work? Read on.

The rest of this discussion is very techy, with lots of Python code. If the code is little _too_ obscure for where you're at right now, but you're still interested in this concept, don't hesitate to reach out to talk about how this approach to solving QA needs might help you, even if this specific solution doesn't work for you.

## Setting up QA with Dagster

We are using an open source software tool called **Dagster** to run this quality assurance system. At a very high level, Dagster is software for orchestrating computations on data. It is built to help organizations manage complicated data operations such as moving data from a live database to an analytics-focused data warehouse or combining data from multiple sources. And its also great at running little bits of Python to download some data and send emails about what got downloaded. That's what we're doing here.

### Set up LegalServer QA reports
The most important pieces of this process are the quality assurance reports in LegalServer. Dagster is very capable, but there would be ways to replace it. The quality assurance reports in LegalServer are the absolutely essential part of the system.

Here's what I recommend for designing QA reports that will work well with Dagster. 

1. Create lots of reports that each identify one single data error. 

2. Add just the bare minimum set of columns. Try to avoid including identifiable client information; instead, try to just use Case IDs and other non-identifable fields. This is a "defense-in-depth" strategy for protecting confidential information.

3. Configure the filters so that each row in the report identifies one case that has the error the report is about. 

For example, to set up a quality assurance check that all closed cases have a field called "Special District" filled in, add only the columns 'Case/Matter ID#', 'Disposition', and the 'Special District'.  And create a filter to select only cases where 'Disposition' is closed and 'Special District'  is null or empty. If you want to have Dagster email the case handler, add a column with the email address of the Primary Assignment.  

4. Enable the External API for each report.

If you're not sure how, check out https://help.legalserver.org/article/1751-reports-api.

### Emails

If you're sending emails with this system, I've used Sendgrid, but that's not the only option. So however you plan to send emails, make sure you've set up the right accounts and have the libraries and api keys you need.

### Sample Code

I've set up a starter code repository to hopefully make it easier to get going. Download the code at  https://github.com/CLSPhila/dagster-ls-qa-demo for the starter project.

You'll also need the Python library for collecting LegalServer report by API, which is available here: https://github.com/CLSPhila/ls_report_agent. The demo project assumes this code is in a directory right next to the demo project. So download that code as well.

### Set up Dagster

Dagster is a paid service, and it has a free, open source version that you can run  on your local computer. I think paying to use the hosted service is worth it for what we're doing, but for now we'll do everything locally. If you're not used to writing code and figuring out installing dependencies and so on, this part is definitely a pain. But bear with me; getting through this part opens a world of capabilities!

Everything in Dagster happens in Python, so you'll need Python installed. And you'll want a good text editor. VSCode is very popular, and there are lots of others. You can download Python here: https://www.python.org/downloads/ and VSCode here: https://code.visualstudio.com/. 

Once you've got Python set up, install the `Poetry` package manger. https://python-poetry.org/docs/. You can use python's default package manager, `pip` if you prefer, but I've set up a demo project to help you get started, and that project uses `Poetry.`  

Dagster has instructions for creating a new dagster project. https://docs.dagster.io/getting-started/create-new-project. But lets keep things even simpler. I've created a demo project that you can just download from here: ______- 

Download that project (or use `git` to clone it, if you're familiar with that.) And install with `poetry intall`. 

Run `poetry shell` to activate the `Poetry` environment and `dagster dev -m ls`

Now you can navigate in your browser to "localhost:3000" and see Dagster's web interface. And you'll see an example `asset`.


### Create Assets

An `Asset` is how we describe some chunk of data with Dagster. An `Asset` is essentially a Python function that returns some kind of data. This is an Asset that describes a list of a few numbers:

```python
from dagster import asset


@asset
def my_data():
	return [1,2,3,4]
```

Dagster's main job is knowing how to run these `assets` to collect the data they describe. (Dagster calls this 'materializing' an `asset`. Dagster then stores that data somewhere. Where it stores the data depends on something called an `IOManager`. The default is just to store the data in the local file system, so that's all we're doing here. This `asset` will store the list `[1,2,3,4]` to a file in a local directory on your computer.

We are going to create an `Asset` for each of the quality assurance reports we want to monitor. Each `Asset` is basically the same. We're using the library `ls_report_agent`, which helps collect LegalServer reports to make downloading a single report a quick operation.

```python
@asset()
def case_error_asset() -> Output:
	instructions = "To fix this error, make sure X is really Y, and fix the recorded data."
	long_description =  "We can't have values of X in these cases."
	url_for_fixing = "https://mylegalserver.legalserver.org/matter/form123"
	to_emails = ["admin@legalservicesorg.example"]
	email_key = "Email"

    agent = ReportAgent(BearerToken(os.environ["API_TOKEN"]), env_var_url)
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
```

We create a `ReportAgent` and then use it download a report from LegalServer in a tabular format called a pandas dataframe.  We wrap the results in a `CaseErrors` object. This object helps us keep the data from our report together with metadata about the error, such as instructions for fixing the error and a list of who should get emails about the error. It doesn't do anything besides hold together a collection of related values.

We wrap that in an `Output`  object, which is a Dagster helper that lets us add metadata. This way, in the Dagster web interface, we'll actually see a plot of the number of case errors for this report, for ever time we've run this asset! 

Note that we're storing the `API_TOKEN`, the LegalServer credentials for our Reports API as an environment variable. 

Also, in this example, `env_var_url` is a placeholder for the actual url of your report (with the report's api key parameter). I recommend against storing that directly in the code, and instead use another environment variable for that.

And with this, we can 'materialize' this asset in the web interface, and Dagster will run this code and download the report data.

### Factories

You could make a whole lot of these asset functions. They'll each be pretty much identical. We can avoid a lot of that repetition by making a new function that _creates_ asset functions. This is some funky higher-order functional programming, but all we need to know is that there's a factory in `factories.py`  called `make_case_error_asset`. Instead of writing lots of nearly-identical asset functions that differ only in the report's url, the instructions, the list of emails, you can just write:

```python
language_missing = make_case_error_asset(
        "language_missing", # dagster's name for the asset
         "language is missing for these cases", # description for users
         "URL_language_missing", # Environment variable with url for report
         "Please make sure language is selected for the these cases", #instructions
         "matter/url/for/case", # url stub will have the case-id appended at the end.
         "admin@myorg.example", # address that should hear about _all_ the errors.
         "Email", # column name in the report with the case handler's email address.
         )

```

Its easier to write variations of this thirty times instead of the full asset definition for every qa report.  Oof.

There may still be reports you need to write a full asset definition for. For example if you need to do filtering calculations that LegalServer cannot do, such as making sure the values of two columns are equal to each other. 

For the sake of clarity, and to make the next step easier its a good idea to put all these case error assets in one python file: `case_error_assets.py`. 

### Jobs and Ops

With these assets configured, you can use the Dagster web interface to download all these reports. To actually send emails about these reports, we'll need to create a `Job` and some `Ops` in Dagster. 

A `Job` is also a Python function that has the special `@job` symbol (called a "decorator") at the top. We can tell a job to collect a bunch of assets and then pass the results of each asset to a bunch of `Op`s.

An `Op` is a generic chunk of computation. We'll create `ops` that take one of our `CaseError` objects and send emails based on those `CaseError`s. 

The `Job` we'll use gathers all the case error assets we made in the last step. Then we'll use another Factory function to create an `op` for each asset. This op will send an email to whoever is identified in the `to_emails` list of the `CaseErrors` object.

The `Job` looks like this:

```python
@job(resource_defs=emailing_resources)
def email_to_admin():    
    """
    Email the stored case error reports to admins only.
    """
    errs_list = [(asset_key, asset.to_source_asset()) for asset_key, asset in ls_qa.assets_case_errors.__dict__.items() if isinstance(asset, AssetsDefinition)]

    for _, err in errs_list:
        make_send_case_error_email(     ■ Argument missing for parameter "errs"                           
                name=f"send_email_re_{err.description or 'not_described'}")(err)
```

That `make_send_case_error_email` is a factory that makes an `op` for each one of the case error assets in `errs_list`. 

### Definitions

Dagster doesn't find all these assets and jobs and ops by itself. You need to add them to a `Definitions` object in the `__init__.py` file of your code folder.  

Definitions looks like this:

```python
defs = Definitions(
        assets = [example_asset, case_error_asset],
        jobs = [email_to_admin])
```

### Running it, finally

Run your code in Dagster's web interface with 

```bash
dagster dev -m ls_qa_demo
```

Visit `localhost:3000` in your browser. You'll see a panel listing your jobs and links to see your assets and a history of runs you've done. 

You need to 'materialize', or run, the assets first, so click over to your assets, and click "Materialize". Then click your job and click the Launchpad to run it. You'll have to set any config variables that are missing in the Launchpad. Use the 'Scaffold' button to have Dagster create an empty config file for you to fill in. Enjoy all the emails about case errors!

### Adding emails to users

Use another `Job` to send emails to case handlers. You can write a `Job` that groups Case Error tables by the assigned advocate, and then sends each grouped table to an `Op` that will send an email. 

## Next Steps

Collecting case errors and alerting users is a huge win for us. It took some work to set all this up, but now that its set up, all that is left for checking case errors is clicking 'Run Job.' But this is still only scratching the surface of what we can do with Dagster.

We can have Dagster run jobs and collect assets on schedules. Instead of manually running these error report jobs, we might have them run weekly, automatically, so case handlers will get reminders to fix issues more regularly. (and have fewer to fix at once!)

We can also use Dagster to generate other kinds of reports. A Dagster job could collect LegalServer data and prepare cross-tabulations for reports for funders.

And Dagster opens doors to powerful analytics. A Dagster job, running on a schedule, could monitor new cases for trends or unusual events, using 'anomaly detection' techniques. We can also use Dagster to combine multiple data sources into one easier-to-understand collection, such as combining phone and case data. 

With automating case error checking, we've accomplished a lot. Even better, we've found a plaform for a wide range of new practices to improve our legal services!

## Alternatives to Dagster

All this focus on Dagster hides an important point. Dagster is not the only way to accomplish what we're doing here. Conceptually, we're writing chunks of code that do small things to bits of data and then using some piece of software to run those chunks of code. Dagster provides a very helpful interface for this. But there are other ways to accomplish our underlying goals here. We might __examples__. Dagster is great software, but the more powerful gain is the practice of doing data orchestration in some way.
