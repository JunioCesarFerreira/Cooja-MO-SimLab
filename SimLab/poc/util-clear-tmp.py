import os

def delete_files_in_directories(directories: list[str]):
    for directory in directories:
        if not os.path.isdir(directory):
            print(f"Directory not found: {directory}")
            continue
        for filename in os.listdir(directory):
            full_path = os.path.join(directory, filename)
            if os.path.isfile(full_path):
                try:
                    os.remove(full_path)
                    print(f"Deleted file: {full_path}")
                except Exception as e:
                    print(f"Error deleting {full_path}: {e}")

# Example usage
directories_to_clean = [
    "./tmp",
    "./logs"
]

delete_files_in_directories(directories_to_clean)
