import os
import shutil
import stat
import getpass
import sys
import importlib
import subprocess

def setup_passphrase():
    secret_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.secret')
    
    print("\nPassphrase Setup")
    print("---------------")
    print("This passphrase will be used to encrypt your assignment files before committing to the repository.")
    print("IMPORTANT: You must use the same passphrase to decrypt your files when pulling from the repository.")
    print("If you lose this passphrase, you won't be able to decrypt your assignments!\n")
    
    # Check if .secret already exists and has content
    if os.path.exists(secret_file) and os.path.getsize(secret_file) > 0:
        response = input("A passphrase already exists. Do you want to change it? (y/N): ")
        if response.lower() != 'y':
            print("\nKeeping existing passphrase. Make sure you remember it!\n")
            return
        print("\nChanging passphrase - make sure you remember the new one!\n")
    
    # Get passphrase with confirmation
    while True:
        passphrase = getpass.getpass("Enter passphrase: ")
        if not passphrase:
            print("Error: Passphrase cannot be empty")
            continue
            
        confirm = getpass.getpass("Confirm passphrase: ")
        if passphrase != confirm:
            print("Error: Passphrases do not match")
            continue
            
        break
    
    # Save passphrase
    with open(secret_file, 'w') as f:
        f.write(passphrase)
    print("\nPassphrase saved successfully")
    print("Remember this passphrase - you'll need it to decrypt your assignments later!")

def inject_python_command(hook_path, python_cmd):
    """Inject Python command at the start of the hook file"""
    with open(hook_path, 'r') as f:
        content = f.read()
    
    # Add Python command definition after shebang
    modified = content.replace(
        "#!/bin/bash\n\nPYTHON=python3",
        f"#!/bin/bash\n\nPYTHON='{python_cmd}'"
    )
    
    with open(hook_path, 'w') as f:
        f.write(modified)

def install_hooks(python_cmd):
    # Get the root directory (where .git is)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hooks_dir = os.path.join(root_dir, '.git', 'hooks')
    source_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Hooks to install
    hooks = ['pre-commit', 'post-checkout']
    
    for hook in hooks:
        src = os.path.join(source_dir, hook)
        dst = os.path.join(hooks_dir, hook)
        
        # Copy the hook file
        print(f"Installing {hook} hook...")
        shutil.copy2(src, dst)
        
        # Inject Python command
        inject_python_command(dst, python_cmd)
        
        # Make it executable (equivalent to chmod +x)
        st = os.stat(dst)
        os.chmod(dst, st.st_mode | stat.S_IEXEC)
        
        print(f"Successfully installed {hook} hook")

def trigger_checkout():
    try:
        # Get current branch/commit
        current = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        print("\nDecrypting files...")
        # Checkout to same location to trigger post-checkout hook
        subprocess.check_call(['git', 'checkout', current])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to decrypt files: {str(e)}")
    except Exception as e:
        print(f"Warning: Unexpected error during decryption: {str(e)}")

def get_python_command():
    default_cmd = sys.executable # gets ${which python3}
    
    print("\nPython Command Setup")
    print("--------------------")
    print("Please specify the command to run Python on your system.")
    print("Common values: 'python', 'python3', '/path/to/python3'")
    print(f"Default Python: {default_cmd}\n")
    
    while True:
        cmd = input("Enter Python command (leave empty to choose default): ").strip()
        if not cmd:
            cmd = default_cmd
            
        try:
            # Test the command
            version = subprocess.check_output([cmd, '--version']).decode().strip()
            print(f"Detected: {version}")
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Error: Unable to run Python using '{cmd}'")
            retry = input("Try another command? (Y/n): ")
            if retry.lower() == 'n':
                print(f"Using default command: {default_cmd}")
                return default_cmd

def check_dependencies(python_cmd):
    """
    Checks dependencies existence before installing it again unnecessarily.
    """
    dependencies = ["cryptography"]
    uninstalled_dependency = []
    for dependency in dependencies:
        try:
            # Tries to import it, if fails, will get it installed later
            importlib.import_module(dependency)
        except ImportError:
            print(f"Dependency {dependency} is not installed.")
            uninstalled_dependency.append(dependency)

    return uninstalled_dependency

def install_dependencies(pip_cmd):
    """Install required Python dependencies"""
    uninstalled_dependency = check_dependencies(pip_cmd)

    if not len(uninstalled_dependency) > 0:
        print("All dependencies are pre-installed. Good to go!")
        return
    print("\nInstalling required dependencies...")

    for dependency in uninstalled_dependency:
        try:
            subprocess.check_call([pip_cmd, 'install', dependency])
            print(f"Successfully installed {dependency}")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install dependencies: {str(e)}")
            print(f"Please manually install the {dependency} module using pip")
        except Exception as e:
            print(f"Warning: Unexpected error during dependency installation: {str(e)}")
            print(f"Please manually install the {dependency} module using pip")

def create_virtualenv(venv_path):
    """Create a virtual environment"""
    if not os.path.exists(venv_path):
        print("\nCreating virtual environment...")
        subprocess.check_call([sys.executable, '-m', 'venv', venv_path])
        print("Virtual environment created successfully")
    else:
        print("Virtual environment already exists")

def which_shell():
    """Detect the user's shell and return the appropriate profile file"""
    shell = os.environ.get('SHELL', '')
    if "fish" not in shell:
        return os.path.expanduser(f'~/.{shell}rc')
    else:
        return os.path.expanduser('~/.config/fish/config.fish')

def update_shell_profile(venv_path):
    """Update shell profile to source the virtual environment automatically"""
    try:
        shell_profile = which_shell()
        activate_script = os.path.join(venv_path, 'bin', 'activate')

        with open(shell_profile, 'a') as f:
            f.write(f'\n# Activate virtual environment\nsource {activate_script}\n')

        print(f"Updated {shell_profile} to source the virtual environment automatically")
    except ValueError as e:
        print(str(e))

if __name__ == "__main__":
    try:
        print("\nSaveMyAss Setup")
        print("===============")
        setup_passphrase()
        python_cmd = get_python_command()
        venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv')
        create_virtualenv(venv_path)
        update_shell_profile(venv_path)
        
        # Use the python and pip from the virtual environment
        venv_python = os.path.join(venv_path, 'bin', 'python')
        venv_pip = os.path.join(venv_path, 'bin', 'pip')
        
        install_dependencies(venv_pip)
        install_hooks(venv_python)
        trigger_checkout()
        print("\nSetup completed successfully!")
    except Exception as e:
        print(f"\nError during setup: {str(e)}")
