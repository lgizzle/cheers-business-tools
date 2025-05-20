import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import shutil
from pathlib import Path

class APReportProcessor:
    """
    Python implementation of the AP Weekly Report Generator.
    Processes AP Aging reports and generates formatted weekly payment reports.
    """
    # Constants for sheet names
    SHEET_RAW_DATA = "RawData"
    SHEET_WEEKLY_BILL = "WeeklyBill"
    SHEET_VENDOR_SUBTOTALS = "VendorSubtotals"
    SHEET_WEEKLY_SUMMARY = "WeeklySummary"

    def __init__(self, file_path):
        """Initialize the processor with the source file path."""
        self.file_path = file_path
        self.source_date = None
        self.next_monday = None
        self.output_file = None

    def generate_report(self):
        """Main method to generate the AP weekly report."""
        try:
            # Create a backup of the original file
            self._create_backup()

            # Load the source data
            self.src_wb = pd.ExcelFile(self.file_path)

            # Find and load the raw data sheet
            self._find_source_sheet()

            # Calculate next Monday based on source date
            self._calculate_next_monday()

            # Create weekly bill report
            weekly_bill_df = self._create_weekly_bill()

            # Insert subtotals by week
            weekly_bill_df = self._insert_subtotals(weekly_bill_df)

            # Create vendor subtotals
            vendor_subtotals_df = self._create_vendor_subtotals(weekly_bill_df)

            # Create weekly summary
            weekly_summary_df = self._create_weekly_summary(weekly_bill_df)

            # Save the complete report
            return self._save_report_as(weekly_bill_df, vendor_subtotals_df, weekly_summary_df)

        except Exception as e:
            print(f"ERROR IN GENERATE_REPORT: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Error generating report: {str(e)}")

    def _create_backup(self):
        """Creates a backup of the source file."""
        src_path = Path(self.file_path)
        backup_folder = src_path.parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{src_path.stem}_Backup_{timestamp}{src_path.suffix}"
        backup_path = backup_folder / backup_name

        try:
            shutil.copy2(self.file_path, backup_path)
            print(f"Backup created at: {backup_path}")
        except Exception as e:
            print(f"Warning: Could not create backup. {str(e)}")

    def _find_source_sheet(self):
        """Finds the appropriate source sheet in the workbook."""
        # Check if RawData sheet exists
        if self.SHEET_RAW_DATA in self.src_wb.sheet_names:
            self.src_sheet = self.SHEET_RAW_DATA
        else:
            # Try to find a sheet with "aging detail report" in the first few rows
            found = False
            for sheet in self.src_wb.sheet_names:
                df = pd.read_excel(self.src_wb, sheet_name=sheet, nrows=5)  # Read up to 5 rows to find header
                sheet_found = False
                for _, row in df.iterrows():
                    for val in row:
                        if isinstance(val, str) and "aging detail report" in val.lower():
                            self.src_sheet = sheet
                            found = True
                            sheet_found = True
                            break
                    if sheet_found:
                        break
                if sheet_found:
                    break

            # If no matching sheet found, use the first sheet
            if not found:
                self.src_sheet = self.src_wb.sheet_names[0]

        print(f"Selected source sheet: {self.src_sheet}")

        # Let's check both ways - first try reading file with both header options and print columns
        # Try reading with headers in row 5 (index 4)
        try:
            df_header4 = pd.read_excel(self.src_wb, sheet_name=self.src_sheet, header=4)
            print(f"Header row 5 (index 4) columns: {df_header4.columns.tolist()}")

            # Debug print the first few rows to see the content
            print("\nSample rows with header row 5:")
            print(df_header4.head(2))
        except Exception as e:
            print(f"Error reading with header=4: {str(e)}")

        # Try reading with first row header
        try:
            df_header0 = pd.read_excel(self.src_wb, sheet_name=self.src_sheet)
            print(f"Header row 1 (index 0) columns: {df_header0.columns.tolist()}")

            # Debug print the first few rows to see the content
            print("\nSample rows with header row 1:")
            print(df_header0.head(2))
        except Exception as e:
            print(f"Error reading with header=0: {str(e)}")

        # First check if the data has headers in row 5 (typical for AP Aging reports)
        try:
            # Try reading with headers in row 5 (index 4)
            self.src_data = pd.read_excel(self.src_wb, sheet_name=self.src_sheet, header=4)

            # Check if we have expected columns (due date, amount, etc.)
            has_header = False
            print("\nChecking for expected columns with header=4...")
            for col in self.src_data.columns:
                col_str = str(col).lower()
                print(f"Column: '{col}', Lower: '{col_str}'")
                if "due date" in col_str or "amount" in col_str:
                    has_header = True
                    print(f"Found expected column: {col}")

            if not has_header:
                print("No expected columns found with header=4, trying with header=0...")
                # If headers weren't found in row 5, try with headers in row 1
                self.src_data = pd.read_excel(self.src_wb, sheet_name=self.src_sheet)
                print(f"Columns with header=0: {self.src_data.columns.tolist()}")
        except Exception as e:
            print(f"Exception during header detection: {str(e)}")
            # Fall back to standard header (first row)
            self.src_data = pd.read_excel(self.src_wb, sheet_name=self.src_sheet)
            print(f"Fallback to header=0, columns: {self.src_data.columns.tolist()}")

        # Print the final columns we're using
        print(f"\nFinal column set: {self.src_data.columns.tolist()}")

        # Extract source date from the report (typically in cell A3)
        self._get_source_date()

    def _get_source_date(self):
        """Extract the source date from the AP Aging report."""
        try:
            # Read the original Excel file to get cell A3 value
            date_df = pd.read_excel(self.src_wb, sheet_name=self.src_sheet, header=None, nrows=5)

            # Get value from A3 (or equivalent first few rows)
            date_text = None
            for i in range(min(5, date_df.shape[0])):
                val = date_df.iloc[i, 0]
                if isinstance(val, str) and "as of" in val.lower():
                    date_text = val
                    break

            # Parse the date from "As of May 1, 2025" format
            if date_text:
                date_text = re.sub(r'(?i)as\s+of\s+', '', date_text).strip()
                try:
                    self.source_date = pd.to_datetime(date_text)
                except:
                    self.source_date = datetime.now().date()
            else:
                self.source_date = datetime.now().date()
        except:
            # Default to today if can't find or parse the date
            self.source_date = datetime.now().date()

    def _get_next_monday(self, start_date=None):
        """Calculate the next Monday from a given date."""
        if start_date is None:
            start_date = datetime.now().date()

        # Convert string or timestamp to date if needed
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).date()
        elif hasattr(start_date, 'date') and callable(getattr(start_date, 'date')):
            start_date = start_date.date()

        # Calculate days until next Monday (0 = Monday, 1 = Tuesday, etc.)
        days_ahead = 0 - start_date.weekday()
        if days_ahead <= 0:  # Target is today or in the past
            days_ahead += 7

        return start_date + timedelta(days=days_ahead)

    def _calculate_next_monday(self):
        """Calculate the next Monday based on the source data date."""
        self.next_monday = self._get_next_monday(self.source_date)
        print(f"Source data date: {self.source_date}")
        print(f"Next Monday calculated as: {self.next_monday}")

    def _create_weekly_bill(self):
        """
        Creates the WeeklyBill sheet by cleaning up the source data,
        removing headers, footers, non-bill rows, and specific columns.
        """
        # Copy the source data
        df = self.src_data.copy()

        # Filter to keep only "Bill" transaction types
        transaction_type_col = None
        for col in df.columns:
            col_str = str(col).lower()
            print(f"Looking for transaction type in: '{col}' (lower: '{col_str}')")
            if "transaction type" in col_str:
                transaction_type_col = col
                print(f"Found transaction type column: {col}")
                break

        if transaction_type_col:
            df = df[df[transaction_type_col].str.contains('Bill', case=False, na=False)].reset_index(drop=True)
            print(f"Filtered to {len(df)} 'Bill' transactions")
        else:
            print("No transaction type column found for filtering")

        # Delete specific columns if they exist
        columns_to_delete = []
        for col in df.columns:
            if isinstance(col, str):
                col_lower = str(col).lower()
                if "transaction type" in col_lower or "past due" in col_lower or "open balance" in col_lower:
                    columns_to_delete.append(col)

        if columns_to_delete:
            df = df.drop(columns=columns_to_delete)
            print(f"Deleted columns: {columns_to_delete}")

        print(f"Weekly bill columns after cleanup: {df.columns.tolist()}")
        return df

    def _insert_subtotals(self, df):
        """
        Calculates and adds subtotal rows by week, with dates
        formatted as mm/dd/yyyy.
        """
        # Find the due date and amount columns
        due_col = None
        amt_col = None

        print("\nLooking for 'Due Date' and 'Amount' columns in:")
        for col in df.columns:
            col_str = str(col).lower()
            print(f"Column: '{col}', Lower: '{col_str}'")
            if "due date" in col_str:
                due_col = col
                print(f"Found due date column: {col}")
            elif "amount" in col_str:
                amt_col = col
                print(f"Found amount column: {col}")

        if not due_col or not amt_col:
            error_msg = f"Could not find 'Due Date' or 'Amount' columns. Available columns: {df.columns.tolist()}"
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)

        # Convert due date column to datetime
        df[due_col] = pd.to_datetime(df[due_col], errors='coerce')

        # Make a copy of the dataframe to work with
        result_df = []

        # Convert next_monday to pandas Timestamp for proper comparison
        report_first_monday = pd.Timestamp(self.next_monday)
        print(f"report_first_monday type: {type(report_first_monday)}, value: {report_first_monday}")

        # Process items before first Monday (Remainder of current week)
        remainder_filter = df[due_col] < report_first_monday
        remainder_items = df[remainder_filter].copy()
        if len(remainder_items) > 0:
            print(f"Found {len(remainder_items)} items for remainder of current week")
            week_total = remainder_items[amt_col].sum()
            result_df.append(remainder_items)

            # Add subtotal row for remainder of week
            subtotal_row = pd.DataFrame({
                df.columns[0]: [f"TOTAL FOR CURRENT WEEK: UP TO {report_first_monday.strftime('%m/%d/%Y')}"],
                amt_col: [week_total]
            })
            for col in df.columns:
                if col != df.columns[0] and col != amt_col:
                    subtotal_row[col] = None
            result_df.append(subtotal_row)

        # Process subsequent weeks (4 weeks after first Monday)
        for i in range(1, 5):
            week_start = report_first_monday + pd.Timedelta(days=(i-1)*7)
            week_end = report_first_monday + pd.Timedelta(days=i*7) - pd.Timedelta(days=1)
            next_monday = report_first_monday + pd.Timedelta(days=i*7)

            # Items due this week
            week_filter = (df[due_col] >= week_start) & (df[due_col] < next_monday)
            week_items = df[week_filter].copy()

            if len(week_items) > 0:
                print(f"Found {len(week_items)} items for date range {week_start.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}")
                week_total = week_items[amt_col].sum()
                result_df.append(week_items)

                # Add subtotal row for this week
                subtotal_row = pd.DataFrame({
                    df.columns[0]: [f"TOTAL FOR {week_start.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}"],
                    amt_col: [week_total]
                })
                for col in df.columns:
                    if col != df.columns[0] and col != amt_col:
                        subtotal_row[col] = None
                result_df.append(subtotal_row)

        # Add total for any remaining items after 4 weeks
        fifth_monday = report_first_monday + pd.Timedelta(days=4*7)
        remaining_filter = df[due_col] >= fifth_monday
        remaining_items = df[remaining_filter].copy()
        if len(remaining_items) > 0:
            print(f"Found {len(remaining_items)} items for dates after {fifth_monday.strftime('%m/%d/%Y')}")
            remaining_total = remaining_items[amt_col].sum()
            result_df.append(remaining_items)

            # Add subtotal row for remaining items
            subtotal_row = pd.DataFrame({
                df.columns[0]: [f"TOTAL FOR AFTER {fifth_monday.strftime('%m/%d/%Y')}"],
                amt_col: [remaining_total]
            })
            for col in df.columns:
                if col != df.columns[0] and col != amt_col:
                    subtotal_row[col] = None
            result_df.append(subtotal_row)

        # Combine all parts into a single DataFrame
        if len(result_df) > 0:
            combined_df = pd.concat(result_df, ignore_index=True)
            return combined_df
        else:
            return df

    def _create_vendor_subtotals(self, weekly_bill_df):
        """
        Creates the VendorSubtotals sheet with vendor totals by week.
        """
        # Find the vendor, due date, and amount columns
        vendor_col = None
        due_col = None
        amt_col = None

        # Print all available columns for debugging
        print(f"Available columns for vendor detection: {weekly_bill_df.columns.tolist()}")

        # First look for vendor column with more flexible matching
        for col in weekly_bill_df.columns:
            col_str = str(col).lower()
            print(f"Checking column: '{col}' (lower: '{col_str}')")
            # More flexible vendor matching - look for any column with "vendor" in the name
            if "vendor" in col_str:
                vendor_col = col
                print(f"Found vendor column: {col}")
                if "display" in col_str and "name" in col_str:
                    # This is the ideal match, so break immediately
                    break

            if "due date" in col_str or "due" in col_str:
                due_col = col
                print(f"Found due date column: {col}")

            if "amount" in col_str:
                amt_col = col
                print(f"Found amount column: {col}")

        # Fallback: if no vendor column found with "vendor" in name, use the first text column
        if not vendor_col:
            print("No vendor column found with 'vendor' in name, trying to find first text column")
            for col in weekly_bill_df.columns:
                # Get sample values to check if it might be a text column
                sample_values = weekly_bill_df[col].dropna().head(5)
                if len(sample_values) > 0 and all(isinstance(val, str) for val in sample_values):
                    vendor_col = col
                    print(f"Using text column as vendor: {col}")
                    break

        if not vendor_col:
            # Last resort: just use the first column
            vendor_col = weekly_bill_df.columns[0]
            print(f"Using first column as vendor: {vendor_col}")

        # If due_col and amt_col are still not found, try simpler matching
        if not due_col:
            for col in weekly_bill_df.columns:
                if "due" in str(col).lower():
                    due_col = col
                    print(f"Found due date column (simplified search): {col}")
                    break

        if not amt_col:
            for col in weekly_bill_df.columns:
                if "amount" in str(col).lower() or "amt" in str(col).lower():
                    amt_col = col
                    print(f"Found amount column (simplified search): {col}")
                    break
                # Try to identify amount column by numeric values
                elif weekly_bill_df[col].dtype in [np.float64, np.int64]:
                    amt_col = col
                    print(f"Using numeric column as amount: {col}")
                    break

        print(f"Using columns: Vendor={vendor_col}, Due date={due_col}, Amount={amt_col}")

        # Double check that we found all required columns
        if not vendor_col:
            print("WARNING: No vendor column found, using first column")
            vendor_col = weekly_bill_df.columns[0]

        if not due_col:
            print("WARNING: No due date column found, continuing without it")
            # This isn't strictly required for vendor subtotals
            due_col = vendor_col  # Set to something non-None to pass the check

        if not amt_col:
            print("WARNING: No amount column found, cannot continue")
            return pd.DataFrame(columns=['VENDOR', '# OF BILLS', 'TOTAL AMOUNT', '% OF WEEK'])

        # Print the subtotal structure for debugging
        print("\nAnalyzing subtotal structure:")
        # Extract subtotal rows to identify week boundaries
        subtotal_filter = weekly_bill_df[weekly_bill_df.columns[0]].str.contains('TOTAL FOR', case=False, na=False)
        subtotal_rows = weekly_bill_df[subtotal_filter].copy()

        for i, row in subtotal_rows.iterrows():
            print(f"Subtotal at row {i}: {row[weekly_bill_df.columns[0]]}")

        if len(subtotal_rows) == 0:
            print("Warning: No subtotal rows found. Returning empty vendor subtotal sheet.")
            return pd.DataFrame(columns=['VENDOR', '# OF BILLS', 'TOTAL AMOUNT', '% OF WEEK'])

        # Initialize result DataFrame for VendorSubtotals
        vendor_subtotals = []

        # Add header
        vendor_subtotals.append(pd.DataFrame({
            'HEADER': ['Vendor Subtotals by Week', f"Report for data as of: {self.source_date.strftime('%m/%d/%Y')}"]
        }))

        # Process each week - we'll do this by analyzing the data between subtotal rows
        week_boundaries = subtotal_rows.index.tolist()
        print(f"Week boundaries at rows: {week_boundaries}")

        # Add index 0 as the first boundary and len(weekly_bill_df) as the last
        all_boundaries = [0] + week_boundaries + [len(weekly_bill_df)]

        # Process each section (week)
        for i in range(len(week_boundaries)):
            # Get the title from the subtotal row
            week_title = weekly_bill_df.iloc[week_boundaries[i], 0]
            if "TOTAL FOR" in week_title:
                week_title = week_title.replace("TOTAL FOR", "").strip()

            print(f"Processing section: {week_title}")

            # Get the start and end indices for this section
            start_idx = all_boundaries[i]  # Start from the previous boundary
            end_idx = week_boundaries[i]   # End at this subtotal row

            # Skip if there are no data rows in this section
            if end_idx <= start_idx:
                print(f"  Skipping empty section {i+1}")
                continue

            # Extract data rows only (no subtotal rows)
            mask = ~weekly_bill_df.iloc[start_idx:end_idx][weekly_bill_df.columns[0]].str.contains('TOTAL FOR', case=False, na=False)
            week_data = weekly_bill_df.iloc[start_idx:end_idx][mask].copy()

            if len(week_data) == 0:
                print(f"  No items in section {i+1}")
                continue

            print(f"  Found {len(week_data)} items in section {i+1}")

            # Process this week's data
            try:
                # Group by vendor and sum amounts
                vendor_totals = week_data.groupby(vendor_col)[amt_col].agg(['count', 'sum']).reset_index()
                vendor_totals.columns = ['VENDOR', '# OF BILLS', 'TOTAL AMOUNT']

                # Calculate percentage of week
                week_total = vendor_totals['TOTAL AMOUNT'].sum()
                if week_total > 0:  # Avoid division by zero
                    vendor_totals['% OF WEEK'] = vendor_totals['TOTAL AMOUNT'] / week_total
                else:
                    vendor_totals['% OF WEEK'] = 0.0

                # Sort by amount descending
                vendor_totals = vendor_totals.sort_values('TOTAL AMOUNT', ascending=False)

                # Add week title and headers
                result = [
                    pd.DataFrame({'WEEK': [week_title]}),
                    pd.DataFrame({
                        'VENDOR': ['VENDOR'],
                        '# OF BILLS': ['# OF BILLS'],
                        'TOTAL AMOUNT': ['TOTAL AMOUNT'],
                        '% OF WEEK': ['% OF WEEK']
                    }),
                    vendor_totals,
                    pd.DataFrame({
                        'VENDOR': ['WEEK TOTAL'],
                        '# OF BILLS': [vendor_totals['# OF BILLS'].sum()],
                        'TOTAL AMOUNT': [week_total],
                        '% OF WEEK': [1.0]
                    }),
                    pd.DataFrame({'SPACER': ['']}),  # blank row between weeks
                ]
                section_result = pd.concat(result, ignore_index=True)
                vendor_subtotals.append(section_result)
                print(f"  Added section with {len(section_result)} rows")
            except Exception as e:
                print(f"Error processing section {i+1}: {str(e)}")

        # Calculate grand total across all weeks
        grand_total = 0
        total_bills = 0
        try:
            for frame in vendor_subtotals:
                if 'VENDOR' in frame.columns and 'TOTAL AMOUNT' in frame.columns:
                    week_total_rows = frame.loc[frame['VENDOR'] == 'WEEK TOTAL', 'TOTAL AMOUNT']
                    week_bills_rows = frame.loc[frame['VENDOR'] == 'WEEK TOTAL', '# OF BILLS']
                    if not week_total_rows.empty:
                        grand_total += week_total_rows.iloc[0]
                    if not week_bills_rows.empty:
                        total_bills += week_bills_rows.iloc[0]
        except Exception as e:
            print(f"Error calculating grand total: {str(e)}")

        # Add grand total row
        vendor_subtotals.append(pd.DataFrame({
            'VENDOR': ['ALL WEEKS TOTAL'],
            '# OF BILLS': [total_bills],
            'TOTAL AMOUNT': [grand_total],
            '% OF WEEK': [1.0]
        }))

        # Combine all parts
        if len(vendor_subtotals) > 0:
            try:
                result_df = pd.concat(vendor_subtotals, ignore_index=True)
                return result_df
            except Exception as e:
                print(f"Error combining vendor subtotals: {str(e)}")
                # Return a basic DataFrame if concatenation fails
                return pd.DataFrame({
                    'VENDOR': ['Error creating vendor subtotals'],
                    '# OF BILLS': [0],
                    'TOTAL AMOUNT': [0],
                    '% OF WEEK': [0]
                })
        else:
            # Return an empty DataFrame with expected columns if no data
            return pd.DataFrame(columns=['VENDOR', '# OF BILLS', 'TOTAL AMOUNT', '% OF WEEK'])

    def _create_weekly_summary(self, weekly_bill_df):
        """
        Creates the WeeklySummary sheet with totals by week.
        """
        # Find the amount column
        amt_col = None
        for col in weekly_bill_df.columns:
            if isinstance(col, str) and 'amount' in str(col).lower():
                amt_col = col
                break

        if not amt_col:
            raise ValueError("Could not find 'Amount' column in WeeklyBill data")

        # Initialize summary DataFrame
        summary = [
            pd.DataFrame({
                'TITLE': ['Weekly Payment Summary', f"Report for data as of: {self.source_date.strftime('%m/%d/%Y')}"]
            }),
            pd.DataFrame({
                'PAYMENT PERIOD': ['PAYMENT PERIOD'],
                'TOTAL AMOUNT': ['TOTAL AMOUNT'],
                '# OF INVOICES': ['# OF INVOICES']
            })
        ]

        # Extract week subtotals
        subtotal_filter = weekly_bill_df[weekly_bill_df.columns[0]].str.contains('TOTAL FOR', case=False, na=False)
        subtotal_rows = weekly_bill_df[subtotal_filter].copy()

        # Process each week subtotal
        week_data = []
        grand_total = 0
        total_invoices = 0

        # Helper to count invoices in a week
        def count_invoices(start_idx, end_idx):
            if start_idx >= end_idx:
                return 0
            week_df = weekly_bill_df.iloc[start_idx:end_idx].copy()
            no_total_filter = ~week_df[weekly_bill_df.columns[0]].str.contains('TOTAL FOR', case=False, na=False)
            return len(week_df[no_total_filter])

        # Process each subtotal row
        subtotal_indices = subtotal_rows.index.tolist()
        for i, idx in enumerate(subtotal_indices):
            row = weekly_bill_df.iloc[idx]
            week_text = re.sub(r'(?i)TOTAL FOR ', '', str(row[weekly_bill_df.columns[0]]))
            week_total = row[amt_col]

            # Count invoices in this section
            start_idx = 0 if i == 0 else subtotal_indices[i-1] + 1
            invoice_count = count_invoices(start_idx, idx)

            week_data.append({
                'PAYMENT PERIOD': week_text,
                'TOTAL AMOUNT': week_total,
                '# OF INVOICES': invoice_count
            })

            grand_total += week_total
            total_invoices += invoice_count

        # Add week data
        if len(week_data) > 0:
            summary.append(pd.DataFrame(week_data))

        # Add grand total
        summary.append(pd.DataFrame({
            'PAYMENT PERIOD': ['TOTAL PAYMENTS'],
            'TOTAL AMOUNT': [grand_total],
            '# OF INVOICES': [total_invoices]
        }))

        # Combine all parts
        if len(summary) > 0:
            result_df = pd.concat(summary, ignore_index=True)
            return result_df
        else:
            # Return an empty DataFrame with expected columns if no data
            return pd.DataFrame(columns=['PAYMENT PERIOD', 'TOTAL AMOUNT', '# OF INVOICES'])

    def _save_report_as(self, weekly_bill_df, vendor_subtotals_df, weekly_summary_df):
        """Save the processed report with enhanced formatting using xlsxwriter."""
        # Create output filename with source date
        output_filename = f"Upcoming Bills Report {self.source_date.strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join('reports', output_filename)

        # Create Excel writer with xlsxwriter engine
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Write each sheet
            self._write_weekly_summary(writer, weekly_summary_df)
            self._write_weekly_bill(writer, weekly_bill_df)
            self._write_vendor_subtotals(writer, vendor_subtotals_df)
            self._write_raw_data(writer, self.src_data)

        print(f"Report saved as: {output_path}")
        return output_path

    def _write_weekly_summary(self, writer, df):
        """Format and write the weekly summary sheet."""
        # Write data
        df.to_excel(writer, sheet_name=self.SHEET_WEEKLY_SUMMARY, index=False)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[self.SHEET_WEEKLY_SUMMARY]

        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'align': 'center'
        })

        money_format = workbook.add_format({
            'num_format': '$#,##0.00',
            'align': 'right'
        })

        total_format = workbook.add_format({
            'bold': True,
            'num_format': '$#,##0.00',
            'align': 'right',
            'top': 2
        })

        # Find amount and period columns
        amount_col = None
        period_col = None

        for i, col in enumerate(df.columns):
            col_str = str(col).lower()
            if "amount" in col_str or "total" in col_str:
                amount_col = i
            elif "period" in col_str or "payment" in col_str:
                period_col = i

        # Apply column formatting
        worksheet.set_column('A:A', 30)  # Payment period
        worksheet.set_column('B:B', 15, money_format)  # Total amount
        worksheet.set_column('C:C', 15)  # Number of invoices

        # Find the row where the actual data starts (after headers)
        data_start_row = 0
        for i, row in df.iterrows():
            if 'PAYMENT PERIOD' in str(row.iloc[0]):
                data_start_row = i + 1
                break

        # Find total row
        total_row = None
        for i, row in df.iterrows():
            if 'TOTAL PAYMENTS' in str(row.iloc[0]):
                total_row = i
                break

        # Apply formatting to all cells with amounts
        if amount_col is not None:
            for i in range(len(df)):
                try:
                    val = df.iloc[i, amount_col] if amount_col < df.shape[1] else None
                    if pd.notna(val) and isinstance(val, (int, float)):
                        # For regular rows or header rows
                        if total_row is not None and i == total_row:
                            # Use total format for the total row
                            worksheet.write(i+1, amount_col, val, total_format)
                        elif i >= data_start_row:
                            # Regular data rows
                            worksheet.write(i+1, amount_col, val, money_format)
                except (IndexError, KeyError):
                    pass

        # Apply formatting to data rows
        if total_row is not None:
            # Format the total row
            worksheet.write(total_row+1, 0, 'TOTAL PAYMENTS', workbook.add_format({'bold': True}))
            # Total amount already formatted above
            worksheet.write(total_row+1, 2, df.iloc[total_row, 2], workbook.add_format({'bold': True}))

        # Set optimal column widths based on content
        self._set_column_widths(worksheet, df)

    def _write_weekly_bill(self, writer, df):
        """Format and write the weekly bill sheet with enhanced formatting."""
        # Find due date and amount columns
        due_col = None
        amt_col = None
        vendor_col = None
        date_col = None

        for i, col in enumerate(df.columns):
            col_str = str(col).lower()
            if "due date" in col_str or "due" in col_str:
                due_col = i
            elif "amount" in col_str:
                amt_col = i
            elif "vendor" in col_str:
                vendor_col = i
            elif col_str == "date":
                date_col = i

        # If columns weren't found, use defaults
        if due_col is None and len(df.columns) > 4:
            due_col = 4  # Typical position for due date
        if amt_col is None and len(df.columns) > 5:
            amt_col = 5  # Typical position for amount
        if vendor_col is None and len(df.columns) > 3:
            vendor_col = 3  # Typical position for vendor

        # Write data to Excel
        df.to_excel(writer, sheet_name=self.SHEET_WEEKLY_BILL, index=False)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[self.SHEET_WEEKLY_BILL]

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1
        })

        date_format = workbook.add_format({
            'num_format': 'mm/dd/yyyy',  # Date format without time
        })

        money_format = workbook.add_format({
            'num_format': '$#,##0.00'
        })

        subtotal_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F2F2F2',
            'num_format': '$#,##0.00',
            'top': 1,
            'bottom': 1
        })

        # Apply column formatting
        if due_col is not None:
            worksheet.set_column(due_col, due_col, 12, date_format)
        if amt_col is not None:
            worksheet.set_column(amt_col, amt_col, 15, money_format)
        if vendor_col is not None:
            worksheet.set_column(vendor_col, vendor_col, 25)
        if date_col is not None:
            worksheet.set_column(date_col, date_col, 12, date_format)

        # Apply money format to all amount cells (including data rows)
        if amt_col is not None:
            for i in range(1, len(df)+1):  # Skip header row (0)
                try:
                    val = df.iloc[i-1, amt_col] if i-1 < len(df) else None
                    if pd.notna(val) and isinstance(val, (int, float)):
                        if 'TOTAL FOR' in str(df.iloc[i-1, 0]):
                            # Use subtotal format for total rows
                            worksheet.write(i, amt_col, val, subtotal_format)
                        else:
                            # Use standard money format for regular rows
                            worksheet.write(i, amt_col, val, money_format)
                except (IndexError, KeyError):
                    pass

        # Apply date format to all date cells
        if date_col is not None:
            for i in range(1, len(df)+1):
                try:
                    val = df.iloc[i-1, date_col] if i-1 < len(df) else None
                    if pd.notna(val) and not ('TOTAL FOR' in str(df.iloc[i-1, 0])):
                        worksheet.write(i, date_col, val, date_format)
                except (IndexError, KeyError):
                    pass

        # Apply formatting to subtotal rows
        for i in range(len(df)):
            if 'TOTAL FOR' in str(df.iloc[i, 0]):
                # Format the entire subtotal row
                for j in range(len(df.columns)):
                    cell_value = df.iloc[i, j]
                    if j != amt_col and j == 0:  # Skip amount column as it's handled above
                        # First column (description) with subtotal format
                        worksheet.write(i+1, j, cell_value, workbook.add_format({
                            'bold': True,
                            'bg_color': '#F2F2F2',
                            'top': 1,
                            'bottom': 1
                        }))

        # Apply date format to all due date cells
        if due_col is not None:
            for i in range(1, len(df)+1):  # Skip header row
                try:
                    val = df.iloc[i-1, due_col] if i-1 < len(df) else None
                    if pd.notna(val) and not ('TOTAL FOR' in str(df.iloc[i-1, 0])):
                        worksheet.write(i, due_col, val, date_format)
                except (IndexError, KeyError):
                    pass

        # Add conditional formatting to highlight upcoming and overdue payments
        if due_col is not None:
            # Highlight bills due within 7 days in yellow
            worksheet.conditional_format(1, 0, len(df), len(df.columns)-1, {
                'type': 'formula',
                'criteria': f'=AND(ISNUMBER(INDIRECT("${chr(65+due_col)}"&ROW())),INDIRECT("${chr(65+due_col)}"&ROW())<=TODAY()+7,INDIRECT("${chr(65+due_col)}"&ROW())>=TODAY())',
                'format': workbook.add_format({'bg_color': '#FFF2CC'})
            })

            # Highlight overdue bills in red
            worksheet.conditional_format(1, 0, len(df), len(df.columns)-1, {
                'type': 'formula',
                'criteria': f'=AND(ISNUMBER(INDIRECT("${chr(65+due_col)}"&ROW())),INDIRECT("${chr(65+due_col)}"&ROW())<TODAY())',
                'format': workbook.add_format({'bg_color': '#F4CCCC'})
            })

        # Set optimal column widths
        self._set_column_widths(worksheet, df)

        # Freeze panes at B2 to keep headers and row labels visible
        worksheet.freeze_panes(1, 1)

    def _write_vendor_subtotals(self, writer, df):
        """Format and write the vendor subtotals sheet."""
        # Write data to Excel
        df.to_excel(writer, sheet_name=self.SHEET_VENDOR_SUBTOTALS, index=False)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[self.SHEET_VENDOR_SUBTOTALS]

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E2EFDA',
            'border': 1
        })

        money_format = workbook.add_format({
            'num_format': '$#,##0.00'
        })

        percent_format = workbook.add_format({
            'num_format': '0.0%'  # Proper percentage format
        })

        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F2F2F2',
            'num_format': '$#,##0.00',
            'top': 1,
            'bottom': 1
        })

        # Find column indices for special formatting
        total_col = None
        percent_col = None
        vendor_col = None
        bills_col = None

        for i, col in enumerate(df.columns):
            col_str = str(col).lower() if not pd.isna(col) else ""
            if 'total amount' in col_str:
                total_col = i
            elif '% of week' in col_str:
                percent_col = i
            elif 'vendor' in col_str:
                vendor_col = i
            elif '# of bills' in col_str or 'bills' in col_str:
                bills_col = i

        # Apply column formatting
        if total_col is not None:
            worksheet.set_column(total_col, total_col, 15, money_format)
        if percent_col is not None:
            worksheet.set_column(percent_col, percent_col, 10, percent_format)
        if vendor_col is not None:
            worksheet.set_column(vendor_col, vendor_col, 25)
        if bills_col is not None:
            worksheet.set_column(bills_col, bills_col, 10)

        # Apply formatting to all rows
        for i in range(len(df)):
            try:
                # Total amount formatting for all rows
                if total_col is not None and i < len(df):
                    val = df.iloc[i, total_col] if total_col < df.shape[1] else None
                    if pd.notna(val) and isinstance(val, (int, float)):
                        worksheet.write(i+1, total_col, val, money_format)

                # Percentage formatting for all rows
                if percent_col is not None and i < len(df):
                    val = df.iloc[i, percent_col] if percent_col < df.shape[1] else None
                    if pd.notna(val) and isinstance(val, (int, float)):
                        worksheet.write(i+1, percent_col, val, percent_format)
            except (IndexError, KeyError):
                pass

        # Format week title and total rows
        for i in range(len(df)):
            # Identify row types
            cell_val = str(df.iloc[i, 0]) if len(df.columns) > 0 and i < len(df) else ''

            if 'WEEK TOTAL' in cell_val or (len(df.columns) > 1 and 'WEEK TOTAL' in str(df.iloc[i, 1])):
                # Week total row
                for j in range(len(df.columns)):
                    if j < df.shape[1]:  # Make sure column exists
                        try:
                            cell_value = df.iloc[i, j]
                            if pd.notna(cell_value):
                                if j == total_col:
                                    worksheet.write(i+1, j, cell_value, total_format)
                                else:
                                    worksheet.write(i+1, j, cell_value, workbook.add_format({
                                        'bold': True,
                                        'bg_color': '#F2F2F2'
                                    }))
                        except IndexError:
                            pass

            elif 'GRAND TOTAL' in cell_val:
                # Grand total row
                worksheet.write(i+1, 0, cell_val, workbook.add_format({'bold': True, 'bg_color': '#D9E1F2'}))
                if len(df.columns) > 1 and i < len(df):
                    worksheet.write(i+1, 1, df.iloc[i, 1], workbook.add_format({
                        'bold': True,
                        'bg_color': '#D9E1F2',
                        'num_format': '$#,##0.00'
                    }))

        # Set column widths
        self._set_column_widths(worksheet, df)

    def _write_raw_data(self, writer, df):
        """Write the raw data sheet with basic formatting."""
        # Write data to Excel
        df.to_excel(writer, sheet_name=self.SHEET_RAW_DATA, index=False)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[self.SHEET_RAW_DATA]

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9D9D9',
            'border': 1
        })

        date_format = workbook.add_format({
            'num_format': 'mm/dd/yyyy'  # Date format without time
        })

        money_format = workbook.add_format({
            'num_format': '$#,##0.00'
        })

        # Format the headers
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Apply column formatting for dates and amounts
        for i, col in enumerate(df.columns):
            col_str = str(col).lower()
            if "date" in col_str:
                worksheet.set_column(i, i, 12, date_format)

                # Also format each cell in date columns
                for row_idx in range(1, len(df)+1):
                    try:
                        val = df.iloc[row_idx-1, i]
                        if pd.notna(val):
                            worksheet.write(row_idx, i, val, date_format)
                    except (IndexError, KeyError):
                        pass

            elif "amount" in col_str or "balance" in col_str:
                worksheet.set_column(i, i, 15, money_format)

                # Also format each cell in amount columns
                for row_idx in range(1, len(df)+1):
                    try:
                        val = df.iloc[row_idx-1, i]
                        if pd.notna(val) and isinstance(val, (int, float)):
                            worksheet.write(row_idx, i, val, money_format)
                    except (IndexError, KeyError):
                        pass
            else:
                # Default width for other columns
                worksheet.set_column(i, i, 15)

        # Freeze the top row
        worksheet.freeze_panes(1, 0)

        # Set column widths
        self._set_column_widths(worksheet, df)

    def _set_column_widths(self, worksheet, df):
        """Calculate and set optimal column widths based on data."""
        # Iterate through each column
        for i, col in enumerate(df.columns):
            # Start with header width
            max_width = len(str(col)) + 2

            # Check width needed for data
            for j in range(min(len(df), 1000)):  # Limit to first 1000 rows for performance
                if j < len(df):
                    cell_value = str(df.iloc[j, i]) if i < df.shape[1] and pd.notna(df.iloc[j, i]) else ''
                    max_width = max(max_width, len(cell_value) + 2)

            # Set column width with a maximum reasonable width
            worksheet.set_column(i, i, min(max_width, 50))
