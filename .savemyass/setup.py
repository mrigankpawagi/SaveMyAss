import os
import shutil
import stat
import getpass
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

def install_hooks():
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
        
        # Make it executable (equivalent to chmod +x)
        st = os.stat(dst)
        os.chmod(dst, st.st_mode | stat.S_IEXEC)
        
        print(f"Successfully installed {hook} hook")

def trigger_checkout():
    try:
        # Get current branch/commit
        current = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        print(f"\nDecrypting files...")
        # Checkout to same location to trigger post-checkout hook
        subprocess.check_call(['git', 'checkout', current])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to decrypt files: {str(e)}")
    except Exception as e:
        print(f"Warning: Unexpected error during decryption: {str(e)}")

if __name__ == "__main__":
    try:
        print("\nSaveMyAss Setup")
        print("===============")
        setup_passphrase()
        install_hooks()
        trigger_checkout()
        print("\nSetup completed successfully!")
    except Exception as e:
        print(f"\nError during setup: {str(e)}")
