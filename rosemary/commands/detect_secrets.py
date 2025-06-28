import click
import subprocess
import os
import json

# https://github.com/Yelp/detect-secrets
@click.command('detect_secrets', help="Runs detect-secrets to check if there are any plaintext secret in the source code. By default it only checks tracked files.")
@click.argument('specified_path', required=False)
@click.option('--all_files', is_flag=True, help="Scans all files.")
@click.option('--baseline', is_flag=True, help="Use baseline file")
@click.option('--add_to_baseline', is_flag=True, help="Adds all detected secrets to baseline file to don't show them as secrets.")
def detect_secrets(specified_path, all_files, baseline, add_to_baseline):
    if specified_path:
        base_path = specified_path
    else:
        base_path = os.path.join(os.getenv('WORKING_DIR', ''))
    if not os.path.exists(base_path):
        relative_base_path = './'+base_path
        if not os.path.exists(relative_base_path):
            click.echo(click.style(f"Paths '{base_path}' and '{relative_base_path}' does not exist.", fg='red'))
            exit(1)
        base_path = relative_base_path
    
    click.echo(f"Running detect-secrets for the path '{base_path}'")
    test_path = base_path
    baseline_file = os.path.join(test_path, '.secrets.baseline')
    
    detect_secrets_cmd = ['detect-secrets', '-C', test_path, 'scan', '--exclude-files', baseline_file]
    if all_files:
        detect_secrets_cmd.extend(['--all-files'])
        
    if baseline:
        if os.path.exists(baseline_file):
            detect_secrets_cmd.extend(['--baseline',baseline_file])
        else:
            click.echo(click.style(f"Baseline file '{baseline_file}' does not exists. You should run --add_to_baseline first", fg='red'))
            exit(1)
    try:
        if add_to_baseline:
            file = open(baseline_file,"w")
            subprocess.run(detect_secrets_cmd, stdout=file)
            file.close()
            click.echo(click.style(f"Done! You may now run 'rosemary detect_secrets --all_files --baseline' to inspect secrets. Baseline is updated automatically" , fg='green')) 
            click.echo(click.style(f"You shouldn't need to run this command again" , fg='red')) 
            click.echo(click.style(f"You can also just delete the secrets leaked or run 'detect-secrets audit {baseline_file}' to discard false positives", fg='green'))
            return
        
        if baseline:
            subprocess.run(detect_secrets_cmd)
            file = open(baseline_file,"r")
            output = file.read()
            
            file.close()
        else:
            output = subprocess.run(detect_secrets_cmd, capture_output=True, check=True, text=True).stdout
        
        output = json.loads(output)
        secrets = output["results"]
        if secrets == {}:
            click.echo(click.style("No secrets found!", fg='green'))
            exit(0)
        else:
            
            contains_secrets = False
            for file in secrets:
                line = secrets[file][0]["line_number"]
                secret = secrets[file][0]["hashed_secret"]
                
                is_secret = True
                if "is_secret" in secrets[file][0]:
                    is_secret = secrets[file][0]["is_secret"]
                    
                if is_secret:
                    contains_secrets = True
                    click.echo(click.style(f"File {file} in line {line}", fg='yellow'))
                    click.echo(click.style(f"\tHashed secret(not displayed for security) {secret}", fg='red'))
            if contains_secrets:
                click.echo(click.style("########## Secrets found! ##########", fg='red'))
                if baseline:
                    click.echo(click.style(f"You may now run 'detect-secrets audit {baseline_file}' to discard false positives", fg='green'))
                    click.echo(click.style(f"If the secrets listed are not false positives you can remove them by editing the listed lines and rerunning this command", fg='red'))
                exit(1)
            else:
                click.echo(click.style("########## All secrets are managed ##########", fg='green'))
                exit(0)
            
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error running detect_secrets: {e}", fg='red'))