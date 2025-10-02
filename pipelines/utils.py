import importlib
from collections.abc import Iterable

import pandas as pd


def name_from_class(obj):
    """
    Get the fully qualified dot-notation string name for an object or class
    """
    if not hasattr(obj, "__qualname__") or not hasattr(obj, "__module__"):
        # o is not a class, so we need to get the class from the object
        obj = obj.__class__
    module = "" if obj.__module__ in (None, str.__module__) else obj.__module__ + "."
    return module + obj.__qualname__


def class_from_name(full_name):
    """
    Load a class from a dot-notation string name
    """
    try:
        module_name, class_name = full_name.rsplit(".", 1)
    except ValueError as e:
        raise ValueError(f"Can't extract separate module and class names from '{full_name}'") from e
    # load the module, will raise ImportError if module cannot be loaded
    m = importlib.import_module(module_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


def get_index(search_text: str | list[str], data: pd.Series, offset: int = 0) -> int | None:
    """
    Return the index of the first value in a Series that matches the text, or None if there is no match.

    Note that the search is case-insensitive.

    The text to search for can be a string or a list of strings, in which case the function
    returns the first cell that matches any of the supplied strings.
    """
    # Make sure we have an iterable that we can pass to `.isin()`
    if isinstance(search_text, str) or not isinstance(search_text, Iterable):
        search_text = [str(search_text)]
    # Make sure that the search terms are lowercase and stripped of leading/trailing whitespace
    search_text = [str(search_term).lower().strip() for search_term in search_text]
    # Convert the Series to a set of True/False values based on whether they match one of the
    # search_text values.
    matches = data.str.lower().str.strip().isin(search_text)
    # If we don't find a match, return None
    if not matches.any():
        return None
    # Use idxmax to return the index of the first match.
    # This works because in Pandas True > False, so idxmax() returns the index of the first True.
    result = matches.idxmax()
    # Offset the index if necessary
    if offset:
        result = data.index[data.index.get_loc(result) + offset]
    return result


def get_sample_data(df: pd.DataFrame, rows: list[int], max_columns: int = 10) -> pd.DataFrame:
    """
    Get a sample of the data to include in an error message.

    The BSS contains many columns, and including all of them in an error
    message makes the message unreadable, so return the first and last columns
    up to the specified number of columns.
    """
    # Use replace/dropna/fillna so that the sample only includes the columns that have data
    sample_data = df.loc[rows].replace("", pd.NA).dropna(axis="columns", subset=rows[-1]).fillna("")
    # Don't show more than max_columns in the error message, to make the message more readable
    leading_cols = max_columns // 2
    if sample_data.shape[1] > max_columns:
        sample_data = pd.concat(
            [
                sample_data.iloc[:, :leading_cols],
                # Add a column of "..." to indicate that there are more columns
                pd.DataFrame(["..."] * sample_data.shape[0], columns=["..."], index=sample_data.index),
                sample_data.iloc[:, (leading_cols + 1 - max_columns) :],
            ],
            axis="columns",
        )
    return sample_data


def prepare_lookup(data: str | list[str] | pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    Prepare a Series or DataFrame for lookup operations by converting to lowercase strings and stripping whitespace.
    """
    if isinstance(data, str):
        result = pd.DataFrame([data])
    elif isinstance(data, (list, pd.Series)):
        result = pd.DataFrame(data)
    else:
        # Handle unexpected types (like int, float)
        result = pd.DataFrame([str(data)])

    result = result.map(str).map(str.strip).map(str.lower).replace(r"\s+", " ", regex=True)
    if isinstance(data, str) or (not isinstance(data, (list, pd.Series))):
        return result.iloc[0, 0]
    elif isinstance(data, (list, pd.Series)):
        return result.iloc[:, 0]
    return result


def verbose_pivot(df: pd.DataFrame, values: str | list[str], index: str | list[str], columns: str | list[str]):
    """
    Pivot a DataFrame, or log a detailed exception in the event of a failure

    Failures are typically caused by duplicate entries in the index.
    """
    # Make sure index and columns are lists so we can concatenate them in the error handler, if needed.
    if isinstance(index, str):
        index = [index]
    if isinstance(columns, str):
        columns = [columns]
    try:
        return pd.pivot(df, values=values, index=index, columns=columns).reset_index()
    except ValueError as e:
        # Need to fillna, otherwise the groupby returns an empty dataframe
        duplicates = df.fillna("").groupby(index + columns).size().reset_index(name="count")

        # Filter for the entries that appear more than once, i.e., duplicates
        duplicates = duplicates[duplicates["count"] > 1]

        error_df = pd.merge(df.fillna(""), duplicates[index + columns], on=index + columns)

        raise ValueError(str(e) + "\n" + error_df.to_markdown()) from e
