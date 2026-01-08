import sys
import os
import re
# Adjust path to include src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_to_sql.llm_generator import LLMGenerator

def test_clean_sql():
    generator = LLMGenerator()
    
    test_cases = [
        (
            "```sql\nSELECT * FROM table\n```",
            "SELECT * FROM table"
        ),
        (
            "```sqlite\nSELECT * FROM table\n```",
            "SELECT * FROM table"
        ),
        (
            "Here is the code:\n```bash\nSELECT * FROM table\n```\nHope it helps!",
            "SELECT * FROM table"
        ),
        (
            "SELECT * FROM table",
            "SELECT * FROM table"
        ),
        (
            "```\nSELECT * FROM table\n```",
            "SELECT * FROM table"
        )
    ]
    
    print("Testing clean_sql...")
    for i, (input_sql, expected) in enumerate(test_cases):
        cleaned = generator.clean_sql(input_sql)
        # Normalize whitespace for comparison
        cleaned_norm = re.sub(r'\s+', ' ', cleaned).strip()
        expected_norm = re.sub(r'\s+', ' ', expected).strip()
        
        if cleaned_norm == expected_norm:
            print(f"Case {i+1}: PASS")
        else:
            print(f"Case {i+1}: FAIL")
            print(f"  Input: {input_sql!r}")
            print(f"  Expected: {expected!r}")
            print(f"  Got: {cleaned!r}")

if __name__ == "__main__":
    test_clean_sql()
