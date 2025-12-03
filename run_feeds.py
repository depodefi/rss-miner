import os
import importlib.util
import sys

def run_scrapers():
    scrapers_dir = "scrapers"
    if not os.path.exists(scrapers_dir):
        print(f"Directory '{scrapers_dir}' not found.")
        return

    print(f"Looking for scrapers in {scrapers_dir}...")
    
    # List all python files in scrapers directory
    for filename in os.listdir(scrapers_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            file_path = os.path.join(scrapers_dir, filename)
            
            print(f"Running scraper: {module_name}")
            
            try:
                # Import the module dynamically
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Check if it has a generate function
                if hasattr(module, "generate") and callable(module.generate):
                    module.generate()
                    print(f"Successfully ran {module_name}")
                else:
                    print(f"Skipping {module_name}: No 'generate' function found.")
            except Exception as e:
                print(f"Error running {module_name}: {e}")
            print("-" * 20)

if __name__ == "__main__":
    run_scrapers()
