import os
from pathlib import Path

def ends_with_period(text: str) -> bool:
    """
    Check if a line of text ends with a period.
    Handles cases where the line might end with newline characters.
    
    Args:
        text: The line of text to check
        
    Returns:
        bool: True if the line ends with a period, False otherwise
    """
    stripped = text.rstrip('\n\r')
    return stripped.endswith('.')

def find_last_period_line(lines: list[str], start_idx: int, max_chars: int) -> int:
    """
    Find the last line that ends with a period within the character limit.
    
    Args:
        lines: List of lines to check
        start_idx: Starting index in the lines list
        max_chars: Maximum number of characters allowed
        
    Returns:
        int: Index of the last line ending with a period within the limit,
             or the last possible line if no period is found
    """
    current_chars = 0
    last_period_idx = None
    
    for i, line in enumerate(lines[start_idx:], start_idx):
        if current_chars + len(line) > max_chars:
            break
            
        current_chars += len(line)
        if ends_with_period(line):
            last_period_idx = i
    
    # If we found no period, return the last possible line within the limit
    if last_period_idx is None:
        # Find the last line that fits within the character limit
        i = start_idx
        chars_sum = 0
        while i < len(lines) and chars_sum + len(lines[i]) <= max_chars:
            chars_sum += len(lines[i])
            i += 1
        return i - 1
        
    return last_period_idx

def split_markdown_file(input_file: Path, max_chars: int = 5000) -> None:
    """
    Split a markdown file into multiple files, each containing up to max_chars characters
    and ending with a line that contains a period.
    
    Args:
        input_file: Path to the input markdown file
        max_chars: Maximum number of characters per output file
    """
    # Read the entire file
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Initialize variables
    current_idx = 0
    part_number = 0
    
    # Get the base filename without extension
    base_name = input_file.stem
    extension = input_file.suffix
    output_dir = input_file.parent / 'splitted'

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    while current_idx < len(lines):
        # Find the last line ending with a period within the character limit
        end_idx = find_last_period_line(lines, current_idx, max_chars)
        
        # Generate output filename with letter suffix
        suffix = chr(97 + part_number)  # 97 is ASCII for 'a'
        output_file = output_dir / f"{base_name}{suffix}{extension}"

        content = lines[current_idx:end_idx + 1]
        if any(line.strip() for line in content):
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(content)
        # Move to next part
        current_idx = end_idx + 1
        part_number += 1

def process_markdown_directory(directory: str, max_chars: int = 5000) -> None:
    """
    Process all markdown files in the specified directory.
    
    Args:
        directory: Path to the directory containing markdown files
        max_chars: Maximum number of characters per output file
    """
    dir_path = Path(directory)
    
    # Ensure the directory exists
    if not dir_path.exists():
        raise ValueError(f"Directory {directory} does not exist")
    
    # Process all markdown files
    for file_path in dir_path.glob('*.md'):
        split_markdown_file(file_path, max_chars)

if __name__ == "__main__":
    # Example usage
    #process_markdown_directory('data/LidskeJednani/markdown')
    process_markdown_directory('data/processed')