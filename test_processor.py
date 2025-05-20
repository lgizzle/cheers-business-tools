from report_processor import APReportProcessor
import os

def main():
    # Path to the example file
    file_path = os.path.join('uploads', 'Victory Spirits LLC dba Cheers Liquor Mart_A_P Aging Detail Report-2.xlsx')

    # Make sure the file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print(f"Processing file: {file_path}")

    # Create processor instance
    processor = APReportProcessor(file_path)

    try:
        # Process the file
        output_file = processor.generate_report()
        print(f"Success! Report generated: {output_file}")
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
