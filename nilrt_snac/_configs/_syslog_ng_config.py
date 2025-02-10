import argparse
import subprocess

from nilrt_snac import logger
from nilrt_snac._configs._base_config import _BaseConfig
from nilrt_snac.opkg import opkg_helper

def _cmd(*args: str):
    "Syntactic sugar for running shell commands."
    subprocess.run(args, check=True)

def format_syslog_ng_config() -> str:
    return (
        "@version: 4.6\n"
        "@include \"scl.conf\"\n\n"
        "source s_sys {\n"
        "    system();\n"
        "    internal();\n"
        "};\n\n"
        "destination d_mesg {\n"
        "    file(\"/var/log/messages\");\n"
        "};\n\n"
        "log {\n"
        "    source(s_sys);\n"
        "    destination(d_mesg);\n"
        "};\n"
    )

class _SyslogConfig(_BaseConfig):
    def __init__(self):
        self._opkg_helper = opkg_helper

    def configure(self, args: argparse.Namespace) -> None:
        print("Configuring syslog-ng...")
        dry_run: bool = args.dry_run


        # Check if syslog-ng is already installed
        if not self._opkg_helper.is_installed("syslog-ng"):
            self._opkg_helper.install("syslog-ng")


        if not dry_run:
            # Enable persistent storage
            _cmd('nirtcfg', '--set', 'section=SystemSettings,token=PersistentLogs.enabled,value="True"')

            # Setup template syslog-ng configuration
            syslog_conf_path = '/etc/syslog-ng/syslog-ng.conf'
            syslog_conf_template = format_syslog_ng_config()
            with open(syslog_conf_path, "w") as file:
                file.write(syslog_conf_template)
                
            # Restart syslog-ng service
            _cmd('/etc/init.d/syslog', 'restart')

      

    def verify(self, args: argparse.Namespace) -> bool:
        print("Verifying syslog-ng configuration...")
        valid: bool = True


        # Check if syslog-ng is setup to log in /var/log
        test_message = "Test log entry for verification"
        result_command = f'grep "{test_message}" /var/log/messages'
        try:
            # Generate a test log entry
            _cmd("logger", test_message)

            result = subprocess.run(
                result_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            last_entry = result.stdout.strip().split('\n')[-1]
            if test_message not in last_entry:
                logger.error(f"ERROR: Failed logging verification.")
                valid = False
        except:
            logger.error(f"ERROR: Failed logging verification.")
            valid = False
    
      

        return valid