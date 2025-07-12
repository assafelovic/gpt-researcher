from __future__ import annotations

import tkinter as tk

from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
import pandas as pd

from llm_fallbacks.core import get_litellm_model_specs

if TYPE_CHECKING:
    from typing_extensions import Literal

    FilterMethod = Literal[
        "value",
        "regex",
        "quantile",
        "outlier",
        "boolean",
        "string",
        "null",
        "topn",
        "group",
        "custom",
        "range",
        "categorical",
        "time",
        "correlation",
        "variance",
    ]

    ModelCategory = Literal[
        # Model Modes
        "chat",
        "completion",
        "embedding",
        "image_generation",
        "audio_transcription",
        "audio_speech",
        "moderation",
        "moderations",
        "rerank",
        # Model Capabilities
        "vision",
        "audio_input",
        "audio_output",
        "image_input",
        "embedding_image_input",
        "pdf_input",
        "system_messages",
        "function_calling",
        "parallel_function_calling",
        "tool_choice",
        "response_schema",
        "prompt_caching",
        "assistant_prefill",
    ]
else:
    ModelCategory = str
    FilterMethod = str
    Literal = str


def filter_model_specs(
    method: FilterMethod,
    columns: list[str] | str | None = None,
    *,
    # Value filtering
    comparison: Literal[">", "<", ">=", "<=", "==", "!="] | None = None,  # noqa: F722
    value: Any = None,
    # Regex
    pattern: str | None = None,
    # Quantile
    quantile: float | None = None,
    # Outlier
    zscore_threshold: float | None = None,
    iqr_threshold: float | None = None,
    # Boolean
    condition: Callable[[pd.Series], pd.Series] | None = None,
    # String
    contains: str | None = None,
    startswith: str | None = None,
    endswith: str | None = None,
    # Null
    include_nulls: bool = False,
    # TopN
    n: int | None = None,
    ascending: bool = False,
    # Group
    groupby: str | None = None,
    agg_func: str | Callable[[pd.Series], pd.Series] | None = None,
    # Custom
    custom_func: Callable[[pd.DataFrame], pd.DataFrame] | None = None,
    # Range
    start: Any = None,
    end: Any = None,
    # Categorical
    categories: list[ModelCategory] | None = None,
    # Correlation
    target_column: str | None = None,
    correlation_threshold: float | None = None,
    # Variance
    variance_threshold: float | None = None,
    # Common
    as_dict: bool = True,
) -> Any:
    """Flexibly filter and transform LiteLLM model specifications.

    Args:
        method: The filtering method to use
        columns: Column(s) to filter on
        comparison: Comparison operator for value filtering
        value: Value to compare against
        pattern: Regex pattern for matching
        quantile: Quantile threshold (0-1)
        zscore_threshold: Z-score threshold for outlier detection
        iqr_threshold: IQR threshold for outlier detection
        condition: Custom boolean condition function
        contains: String to check for containment
        startswith: String to check for prefix
        endswith: String to check for suffix
        include_nulls: Whether to include null values
        n: Number of top/bottom items to select
        ascending: Sort order for top-n selection
        groupby: Column to group by
        agg_func: Aggregation function for groupby
        custom_func: Custom filtering function
        start: Start value for range
        end: End value for range
        categories: List of categories to filter by
        target_column: Target column for correlation
        correlation_threshold: Minimum correlation coefficient
        variance_threshold: Minimum variance threshold
        as_dict: Return as dict if True, DataFrame if False

    Returns:
        Filtered model specifications as either dict or DataFrame
    """
    df = pd.DataFrame(get_litellm_model_specs())

    if columns is None:
        columns = df.columns.tolist()
    elif isinstance(columns, str):
        columns = [columns]

    if method == "value" and comparison and value is not None:
        ops = {
            ">": np.greater,
            "<": np.less,
            ">=": np.greater_equal,
            "<=": np.less_equal,
            "==": np.equal,
            "!=": np.not_equal,
        }
        df = df[ops[comparison](df[columns[0]].convert_dtypes(), value)]

    elif method == "regex" and pattern and len(columns) > 0:
        df = df[df[columns[0]].astype(str).str.match(pattern, na=False)]

    elif method == "quantile" and quantile is not None and len(columns) > 0:
        threshold = df[columns[0]].quantile(quantile)
        df = df[df[columns[0]] >= threshold]

    elif method == "outlier" and len(columns) > 0:
        if zscore_threshold:
            z_scores = np.abs((df[columns[0]] - df[columns[0]].mean()) / df[columns[0]].std())
            df = df[z_scores < zscore_threshold]
        elif iqr_threshold:
            q1 = df[columns[0]].quantile(0.25)
            q3 = df[columns[0]].quantile(0.75)
            iqr = q3 - q1
            df = df[
                ~(
                    (df[columns[0]] < (q1 - iqr_threshold * iqr))
                    | (df[columns[0]] > (q3 + iqr_threshold * iqr))
                )
            ]

    elif method == "boolean" and condition and len(columns) > 0:
        df = df[condition(df[columns[0]])]

    elif method == "string" and len(columns) > 0:
        if contains:
            df = df[df[columns[0]].astype(str).str.contains(contains, na=False)]
        elif startswith:
            df = df[df[columns[0]].astype(str).str.startswith(startswith, na=False)]
        elif endswith:
            df = df[df[columns[0]].astype(str).str.endswith(endswith, na=False)]

    elif method == "null" and len(columns) > 0:
        if include_nulls:
            df = df[df[columns[0]].isnull()]
        else:
            df = df[df[columns[0]].notnull()]

    elif method == "topn" and n and len(columns) > 0:
        df = df.nlargest(n, columns[0]) if not ascending else df.nsmallest(n, columns[0])

    elif method == "group" and groupby and agg_func:
        df = df.groupby(groupby).agg(agg_func)

    elif method == "custom" and custom_func:
        df = custom_func(df)

    elif method == "range" and start is not None and end is not None and len(columns) > 0:
        df = df[(df[columns[0]] >= start) & (df[columns[0]] <= end)]

    elif method == "categorical" and categories and len(columns) > 0:
        df = df[df[columns[0]].isin(categories)]

    elif method == "correlation" and target_column and correlation_threshold:
        correlations = df.corr()[target_column].abs()
        highly_correlated = correlations[correlations > correlation_threshold].index
        df = df[highly_correlated]

    elif method == "variance" and variance_threshold and len(columns) > 0:
        numeric_df = df[columns[0]].convert_dtypes()
        if pd.api.types.is_numeric_dtype(numeric_df):
            variance = numeric_df.astype(float).var()
            if isinstance(variance, (int, float)):
                df = df[variance > variance_threshold]

    if as_dict:
        return df.to_dict(orient="index")  # pyright: ignore[reportCallIssue]
    return df


class ModelSpecsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LiteLLM Model Specifications Explorer")
        self.geometry("1200x800")

        # DataFrame with all model specs
        self.df: pd.DataFrame = pd.DataFrame(get_litellm_model_specs())
        self.current_view: pd.DataFrame = self.df.copy()

        # Create main layout
        self.setup_ui()

    def setup_ui(self):
        # Filter Frame
        filter_frame = ttk.LabelFrame(self, text="Filters")
        filter_frame.pack(padx=10, pady=10, fill="x")

        # Method Selection
        ttk.Label(filter_frame, text="Filter Method:").grid(row=0, column=0)
        self.method_var: tk.StringVar = tk.StringVar(value="value")
        method_dropdown = ttk.Combobox(
            filter_frame, textvariable=self.method_var, values=list(FilterMethod.__args__)
        )
        method_dropdown.grid(row=0, column=1)

        # Column Selection
        ttk.Label(filter_frame, text="Column:").grid(row=0, column=2)
        self.column_var: tk.StringVar = tk.StringVar()
        column_dropdown = ttk.Combobox(
            filter_frame, textvariable=self.column_var, values=list(self.df.columns)
        )
        column_dropdown.grid(row=0, column=3)

        # Value Input
        ttk.Label(filter_frame, text="Value/Condition:").grid(row=0, column=4)
        self.value_entry: ttk.Entry = ttk.Entry(filter_frame)
        self.value_entry.grid(row=0, column=5)

        # Filter Button
        ttk.Button(filter_frame, text="Apply Filter", command=self.apply_filter).grid(
            row=0, column=6
        )

        # Treeview for displaying results
        self.tree: ttk.Treeview = ttk.Treeview(self, columns=list(self.df.columns), show="headings")
        for col in self.df.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c, False))
            self.tree.column(col, width=100)
        self.tree.pack(padx=10, pady=10, expand=True, fill="both")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Initial population of treeview
        self.populate_treeview(self.df)

    def apply_filter(self):
        try:
            method = self.method_var.get()
            column = self.column_var.get()
            value = self.value_entry.get()

            # Dynamic filtering based on method
            if method == "value":
                filtered_data = filter_model_specs(
                    method="value", columns=column, comparison="<=", value=float(value)
                )
            elif method == "topn":
                filtered_data = filter_model_specs(method="topn", columns=column, n=int(value))
            elif method == "regex":
                filtered_data = filter_model_specs(method="regex", columns=column, pattern=value)
            else:
                # For more complex methods, you might want to add more sophisticated parsing
                messagebox.showinfo("Info", f"Method {method} requires more complex input")
                return

            # Convert filtered data to DataFrame
            if isinstance(filtered_data, dict):
                filtered_df = pd.DataFrame.from_dict(filtered_data, orient="index")
            else:
                filtered_df = filtered_data

            self.populate_treeview(filtered_df)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def populate_treeview(self, df: pd.DataFrame):
        # Clear existing items
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Insert new items
        for _index, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))

    def sort_column(self, col: str, reverse: bool):
        # Sort the treeview by the selected column
        children = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            children.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            children.sort(key=lambda t: t[0], reverse=reverse)

        for index, (_val, k) in enumerate(children):
            self.tree.move(k, "", index)

        # Toggle sort direction
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))


# Create and run the application
def main():
    app = ModelSpecsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
