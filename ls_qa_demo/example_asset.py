from dagster import asset


@asset
def example_asset():
    return [5,4,3,2,1]
