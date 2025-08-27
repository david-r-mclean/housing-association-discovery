"""
Fix existing generated files with encoding issues
"""

import os
import glob

def fix_file_encoding(file_path):
    """Fix encoding issues in a file"""
    try:
        # Read the file with error handling
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Replace problematic Unicode characters
        replacements = {
            '\u2191': '^',  # Up arrow
            '\u2192': '->',  # Right arrow
            '\u2193': 'v',   # Down arrow
            '\u2190': '<-',  # Left arrow
            '\u2022': '*',   # Bullet point
            '\u2013': '-',   # En dash
            '\u2014': '--',  # Em dash
            '\u201c': '"',   # Left double quote
            '\u201d': '"',   # Right double quote
            '\u2018': "'",   # Left single quote
            '\u2019': "'",   # Right single quote
        }
        
        cleaned_content = content
        for unicode_char, replacement in replacements.items():
            cleaned_content = cleaned_content.replace(unicode_char, replacement)
        
        # Write back the cleaned content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"✅ Fixed: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all generated files"""
    print("🔧 Fixing Generated Files...")
    print("=" * 40)
    
    # Find all generated files
    patterns = [
        "generated_files/*.py",
        "generated_files/*.js",
        "generated_files/*.html",
        "generated_files/*.css",
        "generated_files/*.md",
        "generated_files/*.txt"
    ]
    
    fixed_count = 0
    total_count = 0
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            total_count += 1
            if fix_file_encoding(file_path):
                fixed_count += 1
    
    print(f"\n📊 Results:")
    print(f"   Total files: {total_count}")
    print(f"   Fixed files: {fixed_count}")
    print(f"   Success rate: {(fixed_count/total_count*100):.1f}%" if total_count > 0 else "   No files found")

if __name__ == "__main__":
    main()