from flask import Flask
from flask import render_template
from flask import abort, redirect, url_for
import subprocess

##################
# TODO
# - check in to GIT for easy deployment to berry
# - test the app on berry with venv and quick flask test locally
# - deploy with gunicorn or similar 

LOCKED_PORT = 5555

#iptables -A INPUT -p tcp --dport 22 -s 192.168.0.0/16 -j ACCEPT
#iptables -A INPUT -p tcp --dport 22 -s 127.0.0.0/8 -j ACCEPT
#iptables -A INPUT -p tcp --dport 22 -j DROP

app = Flask(__name__)

# check if the port is locked by the iptables firewall
# returns True if the port is locked, False otherwise
# simply looks for the port number with DROP at the end
def is_port_locked(port_num):
    app.logger.info(f"checking if port {port_num} is locked...")
    res = subprocess.run(["/usr/bin/sudo", "iptables", "-S"], capture_output=True, text=True)
    rules = []
    if (res.stdout is not None):
        rules = res.stdout.split("\n")
        # remove the empty string at the end
        if len(rules[len(rules)-1]) == 0:
            rules.pop()
        for rule in rules:
            if str(port_num) in rule and "DROP" in rule:
                app.logger.info(f"port {port_num} is locked")
                return True, rules
    app.logger.info(f"port {port_num} is not locked")
    return False, rules


# lock the port using iptables
# returns True if the port was successfully locked, False otherwise
def lock_port(port_num):
    app.logger.info(f"locking port {port_num}...")
    res = subprocess.run(["/usr/bin/sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(port_num), "-s", "192.168.0.0/16", "-j", "ACCEPT"], capture_output=True, text=True)
    res = subprocess.run(["/usr/bin/sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(port_num), "-s", "127.0.0.0/8", "-j", "ACCEPT"], capture_output=True, text=True)
    res = subprocess.run(["/usr/bin/sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(port_num), "-j", "DROP"], capture_output=True, text=True)
    app.logger.info(res.stdout)
    if len(res.stderr) > 0:
        app.logger.error(res.stderr)
    return res.returncode == 0


# unlock the port using iptables
# returns True if the port was successfully unlocked, False otherwise
def unlock_port(port_num):
    app.logger.info(f"unlocking port {port_num}...")
    res = subprocess.run(["/usr/bin/sudo", "iptables", "-D", "INPUT", "-p", "tcp", "--dport", str(port_num), "-s", "192.168.0.0/16", "-j", "ACCEPT"], capture_output=True, text=True)
    res = subprocess.run(["/usr/bin/sudo", "iptables", "-D", "INPUT", "-p", "tcp", "--dport", str(port_num), "-s", "127.0.0.0/8", "-j", "ACCEPT"], capture_output=True, text=True)
    res = subprocess.run(["/usr/bin/sudo", "iptables", "-D", "INPUT", "-p", "tcp", "--dport", str(port_num), "-j", "DROP"], capture_output=True, text=True)
    app.logger.info(res.stdout)
    if len(res.stderr) > 0:
        app.logger.error(res.stderr)
    return res.returncode == 0


@app.route("/")
def root_page():
    return render_template('index.html')


@app.route("/check")
def check_gate():
    app.logger.info("checking gate status...")
    is_locked, rules = is_port_locked(LOCKED_PORT)
    app.logger.info(f"the gate is {'locked' if is_locked else 'unlocked'}")
    return render_template('check.html', is_locked=is_locked, rules=rules)


@app.route('/open')
def open_gate():
    app.logger.info("opening gate...")
    success = unlock_port(LOCKED_PORT)
    app.logger.info(f"the gate was {'opened' if success else 'NOT opened'}")
    return redirect(url_for('check_gate'))


@app.route('/close')
def close_gate():
    app.logger.info("closing gate...")
    success = lock_port(LOCKED_PORT)
    app.logger.info(f"the gate was {'closed' if success else 'NOT closed'}")
    return redirect(url_for('check_gate'))
