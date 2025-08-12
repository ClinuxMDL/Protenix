import argparse
import os
import subprocess
import sys
from datetime import datetime

# The list of PDB IDs required for the hackathon.
PDB_ID_LIST_STR = '1I5H 1I8H 1I5D 1IH0 1IMX 1II5 1J5I 1JMQ 1JM4 1JQD 1JD0 1JET 1JIJ 1K4G 1KMV 1KLL 1K27 1KM3 1KF6 1L2Z 1LB6 1LBK 1LKE 1LXF 1M48 1M6P 1M51 1ME3 1MV0 1N5Z 1MS0 1N8U 1MWT 1ME7 1NHZ 1NW7 1NJ1 1NU8 1OAI 1OE7 1OJ5 1ORK 1OLS 1OW4 1PDQ 1PPX 1OYN 1PQ6 1PWP 1Q1Y 1Q8T 1QCA 1QFS 1R6N 1QXW 1R2B 1S5Q 1RO7 1SO2 1T7D 1T08 1T13 1UTC 1UOU 1UY7 1UWH 1VEA 1W80 1WN6 1W6J 1W96 1XKK 1XWS 1XOE 1XXE 1Y98 1YHM 1YBG 1YY6 1Z6F 1ZH7 1Z9H 1ZUB 2A25 2B7A 2B9A 2C92 2QIC 2RR4 2V83 3E3U 3G5K 3HV8 3LL8 4D3H 4DN0 4J8T'
REQUIRED_PDB_IDS = set(PDB_ID_LIST_STR.split())
REQUIRED_CIF_COUNT_PER_PDB = 100
MAX_UPLOADS = 20

# TOS credentials and endpoint configuration.
TOS_CREDENTIALS = [
    "-i", os.environ.get("VOLC_AK", None),
    "-k", os.environ.get("VOLC_SK", None),
    "-e=https://tos-cn-beijing.ivolces.com",
    "-re=cn-beijing"
]

def run_command(command):
    """Runs a shell command and returns its output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        raise

def run_command_with_realtime_output(command):
    """Runs a shell command and prints its output in real-time."""
    try:
        # Using shell=True to handle the '*' in the command path.
        # The command is constructed internally, so it's safe.
        subprocess.run(" ".join(command), check=True, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        raise

def validate_result_path(result_path):
    """
    Validates the structure and content of the result path.
    """
    print(f"Validating result path: {result_path}")
    if not os.path.isdir(result_path):
        raise ValueError(f"Result path '{result_path}' is not a valid directory.")

    present_pdbs = {d for d in os.listdir(result_path) if os.path.isdir(os.path.join(result_path, d))}
    
    missing_pdbs = REQUIRED_PDB_IDS - present_pdbs
    if missing_pdbs:
        raise ValueError(f"Validation failed: Missing PDB ID directories: {', '.join(sorted(list(missing_pdbs)))}")

    for pdb_id in REQUIRED_PDB_IDS:
        pdb_path = os.path.join(result_path, pdb_id)
        cif_files_count = 0
        for root, _, files in os.walk(pdb_path):
            for file in files:
                if file.endswith('.cif'):
                    cif_files_count += 1
        
        if cif_files_count != REQUIRED_CIF_COUNT_PER_PDB:
            raise ValueError(f"Validation failed for PDB ID '{pdb_id}': Found {cif_files_count} .cif files, but {REQUIRED_CIF_COUNT_PER_PDB} are required.")

    print("Result path validation successful.")

def get_uploaded_count(username):
    """
    Checks the number of previous uploads for the user.
    """
    print(f"Checking previous uploads for user: {username}")
    tos_path = f"tos://vhackathon-result/{username}/"
    command = ["tosutil", "ls", "-s", "-d"] + TOS_CREDENTIALS + [tos_path]
    
    try:
        output = run_command(command)
        # The output of `tosutil ls -s -d` on a non-existent or empty directory still returns exit code 0.
        # We need to parse the output to count the folders.
        folder_count = 0
        for line in output.splitlines():
            # Folders are listed starting with the bucket path.
            if line.startswith(tos_path) and line.endswith('/'):
                # Exclude the base user directory itself from the count.
                if line.strip() != tos_path:
                    folder_count += 1
        print(f"Found {folder_count} previous uploads.")
        return folder_count
    except subprocess.CalledProcessError:
        # If the user's directory doesn't exist, tosutil might error, which means 0 uploads.
        # However, based on observation, it exits 0. This is a safeguard.
        print("Could not list user directory, assuming 0 uploads.")
        return 0


def upload_results(username, result_path, rank):
    """
    Uploads the result directory and a completion marker to TOS.
    """
    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    target_base_path = f"tos://vhackathon-result/{username}/{rank}_{time_stamp}"
    
    # 1. Upload the results directory
    print(f"Uploading result directory to {target_base_path}...")
    # Append '/*' to the source path to copy the contents of the directory, not the directory itself.
    source_path_for_upload = result_path
    upload_dir_command = ["tosutil", "cp", "-u", "-r", "-j=10", "-p=10"] + TOS_CREDENTIALS + [f"'{source_path_for_upload}'", target_base_path]
    run_command_with_realtime_output(upload_dir_command)
    print("Result directory upload complete.")

    # 2. Create and upload the 'upload_finished' marker file
    finished_file_path = "/tmp/upload_finished"
    with open(finished_file_path, "w") as f:
        pass # Create an empty file
    
    target_marker_path = f"{target_base_path}/upload_finished"
    print(f"Uploading completion marker to {target_marker_path}...")
    upload_marker_command = ["tosutil", "cp", "-u", "-j=10", "-p=10"] + TOS_CREDENTIALS + [finished_file_path, target_marker_path]
    run_command(upload_marker_command)
    print("Completion marker upload complete.")
    
    os.remove(finished_file_path)


def main():
    """Main function to orchestrate the validation and upload process."""
    parser = argparse.ArgumentParser(description="Validate and upload hackathon results.")
    parser.add_argument("--username", type=str, help="Your username for the hackathon.")
    parser.add_argument("--result_path", type=str, help="Path to your results directory.")
    args = parser.parse_args()

    try:
        # 1. Validate result format
        validate_result_path(args.result_path)

        # 2. Validate upload count
        uploaded_count = get_uploaded_count(args.username)
        if uploaded_count >= MAX_UPLOADS:
            raise RuntimeError(f"Upload failed: You have already used all {MAX_UPLOADS} of your upload attempts.")
        
        result_rank = uploaded_count + 1
        remaining_attempts = MAX_UPLOADS - result_rank

        print(f"Upload check passed. This will be your submission #{result_rank}.")
        print(f"You will have {remaining_attempts} attempts remaining after this.")

        # 3. Upload results
        upload_results(args.username, args.result_path, result_rank)

        print("\n--- Upload Successful! ---")
        print(f"Username: {args.username}")
        print(f"Submission Rank: {result_rank}")
        print(f"Remaining Uploads: {remaining_attempts}")
        print("--------------------------")

    except (ValueError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"\n--- An error occurred ---", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        print("--------------------------", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
