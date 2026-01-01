import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from text_to_sql.config_loader import ConfigLoader, GLOBAL_CONFIG
    print("Import successful")
    print(f"Config: {GLOBAL_CONFIG}")
    
    loader = ConfigLoader()
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.modules['text_to_sql.config_loader'].__file__))))
    print(f"Calculated Base Dir: {base_dir}")
    print(f"Expected Config Path: {os.path.join(base_dir, 'config', 'llm_config.yaml')}")
    print(f"Exists? {os.path.exists(os.path.join(base_dir, 'config', 'llm_config.yaml'))}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
